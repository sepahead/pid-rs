//! End-to-end diagnostic and curated analytic checks for the experimental continuous stack.
//!
//! # Method provenance and availability
//!
//! **PROJECT-DEFINED DIAGNOSTIC PROGRAM.** `exp0` composes published estimators, analytic
//! Gaussian references, geometry summaries, and optional resampling into scoped machine-readable
//! findings. It is available as the `exp0` binary with `experimental-all`. It is not a published
//! estimator or a generic hypothesis test: the default high-dimensional sweep is diagnostic, and
//! the strict gate applies only to its curated analytic band.
//!
//! Method catalog: validation.exp0

use pid_core::diagnostics::{
    average_degree_of_redundancy, average_degree_of_vulnerability, distance_concentration_stats,
    intrinsic_dimension_levina_bickel, sampled_four_point_delta_summary,
    DistanceConcentrationConfig, HyperbolicityConfig, IntrinsicDimConfig,
    NormalizedInvariantReport, NormalizedInvariantStatus, SampledFourPointDeltaSummary,
};
use pid_core::experimental::continuous::raw_scalars::{
    co_information_pairwise, isx_redundancy, ksg_mi, ksg_mi_concat_xy,
};
use pid_core::experimental::continuous::{IsxConfig, IsxMethod, Pid2Estimate, Pid2Result};
use pid_core::experimental::pipelines::{
    bootstrap_rows_stats, permutation_rows_pvalue, BlockLengthSelection, BootstrapConfig,
    ResamplingValidityDeclaration, RowBootstrapStat, RowPermutationStat, RowResampleScheme,
    StatisticCallbackDeclaration,
};
use pid_core::stable::continuous::{
    ksg_resource_estimate, KsgConfig, NegativeHandling, SupportContract,
};
use pid_core::stable::preprocessing::{
    ConstantColumnPolicy, HashProjector, PcaProjector, Standardizer,
};
use pid_core::{concat_horiz, MatRef, Metric, PidError, ResourceEstimate};
use pid_runlog::{RunLogEvent, RunLogWriter, RunStatus, RUN_LOG_SCHEMA_VERSION};
use serde_json::json;
use std::collections::BTreeMap;
use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

#[derive(Debug, Clone)]
struct Args {
    csv: bool,
    seeds: usize,
    strict_gate: bool,
    strict_band: bool,
    summary_json: Option<String>,
    runlog: Option<String>,
    uncertainty: UncertaintyConfig,
}

/// Machine-readable state for an optional scientific computation.
///
/// `Abstained` never carries a value. `NotRequested` is distinct from abstention because no
/// computation was attempted. This boundary prevents output adapters from manufacturing numeric
/// sentinels for unavailable results.
#[derive(Debug, Clone, Copy, PartialEq)]
enum ScientificOutcome<T> {
    NotRequested,
    Produced(T),
    Abstained { reason: AbstentionReason },
}

impl<T> ScientificOutcome<T> {
    fn status(&self) -> &'static str {
        match self {
            Self::NotRequested => "not_requested",
            Self::Produced(_) => "produced",
            Self::Abstained { .. } => "abstained",
        }
    }

    fn status_code(&self) -> usize {
        match self {
            Self::NotRequested => 0,
            Self::Produced(_) => 1,
            Self::Abstained { .. } => 2,
        }
    }

    fn abstention_reason(&self) -> Option<AbstentionReason> {
        match self {
            Self::Abstained { reason } => Some(*reason),
            Self::NotRequested | Self::Produced(_) => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum AbstentionReason {
    AmbiguousKthNeighborShell,
    ObservedContinuousSampleIncompatibility,
    NumericalInstability,
    EmptyTerms,
    NonFiniteInput,
    NonPositiveDenominator,
    DenominatorBelowPolicyThreshold,
    NumericallyUnrepresentable,
    ZeroDiameter,
    IncompleteResamplingDistribution,
}

impl AbstentionReason {
    fn as_str(self) -> &'static str {
        match self {
            Self::AmbiguousKthNeighborShell => "ambiguous_kth_neighbor_shell",
            Self::ObservedContinuousSampleIncompatibility => {
                "observed_continuous_sample_incompatibility"
            }
            Self::NumericalInstability => "numerical_instability",
            Self::EmptyTerms => "empty_terms",
            Self::NonFiniteInput => "non_finite_input",
            Self::NonPositiveDenominator => "non_positive_denominator",
            Self::DenominatorBelowPolicyThreshold => "denominator_below_policy_threshold",
            Self::NumericallyUnrepresentable => "numerically_unrepresentable",
            Self::ZeroDiameter => "zero_diameter",
            Self::IncompleteResamplingDistribution => "incomplete_resampling_distribution",
        }
    }
}

fn diagnostic_outcome<T>(
    result: pid_core::PidResult<T>,
) -> Result<ScientificOutcome<T>, Exp0Error> {
    match result {
        Ok(value) => Ok(ScientificOutcome::Produced(value)),
        Err(PidError::AmbiguousKthNeighborShell { .. }) => Ok(ScientificOutcome::Abstained {
            reason: AbstentionReason::AmbiguousKthNeighborShell,
        }),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. }) => {
            Ok(ScientificOutcome::Abstained {
                reason: AbstentionReason::ObservedContinuousSampleIncompatibility,
            })
        }
        Err(PidError::NumericalInstability { .. }) => Ok(ScientificOutcome::Abstained {
            reason: AbstentionReason::NumericalInstability,
        }),
        Err(error) => Err(Exp0Error::Pid(error)),
    }
}

fn finite_diagnostic_scalar(
    result: pid_core::PidResult<f64>,
    context: &'static str,
) -> Result<ScientificOutcome<f64>, Exp0Error> {
    finite_mapped_outcome(diagnostic_outcome(result)?, |value| value, context)
}

fn finite_mapped_outcome<T>(
    outcome: ScientificOutcome<T>,
    transform: impl FnOnce(T) -> f64,
    context: &'static str,
) -> Result<ScientificOutcome<f64>, Exp0Error> {
    match outcome {
        ScientificOutcome::Produced(value) => {
            let value = transform(value);
            if !value.is_finite() {
                return Err(Exp0Error::Pid(PidError::NumericalInstability { context }));
            }
            Ok(ScientificOutcome::Produced(value))
        }
        ScientificOutcome::Abstained { reason } => Ok(ScientificOutcome::Abstained { reason }),
        ScientificOutcome::NotRequested => Ok(ScientificOutcome::NotRequested),
    }
}

fn optional_scalar_estimate_outcome(
    result: pid_core::PidResult<f64>,
) -> pid_core::PidResult<ScientificOutcome<f64>> {
    match result {
        Ok(value) if value.is_finite() => Ok(ScientificOutcome::Produced(value)),
        Ok(_) => Err(PidError::NumericalInstability {
            context: "exp0 optional estimate: produced value was non-finite",
        }),
        Err(PidError::AmbiguousKthNeighborShell { .. }) => Ok(ScientificOutcome::Abstained {
            reason: AbstentionReason::AmbiguousKthNeighborShell,
        }),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. }) => {
            Ok(ScientificOutcome::Abstained {
                reason: AbstentionReason::ObservedContinuousSampleIncompatibility,
            })
        }
        Err(PidError::NumericalInstability { .. }) => Ok(ScientificOutcome::Abstained {
            reason: AbstentionReason::NumericalInstability,
        }),
        Err(error) => Err(error),
    }
}

fn normalized_invariant_outcome(
    report: &NormalizedInvariantReport,
) -> pid_core::PidResult<ScientificOutcome<f64>> {
    let reason = match report.status {
        NormalizedInvariantStatus::Defined => {
            let value = report.value.ok_or(PidError::NumericalInstability {
                context: "exp0 normalized invariant: Defined status without a value",
            })?;
            if !value.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "exp0 normalized invariant: Defined status with non-finite value",
                });
            }
            return Ok(ScientificOutcome::Produced(value));
        }
        NormalizedInvariantStatus::EmptyTerms => AbstentionReason::EmptyTerms,
        NormalizedInvariantStatus::NonFiniteInput => AbstentionReason::NonFiniteInput,
        NormalizedInvariantStatus::NonPositiveDenominator => {
            AbstentionReason::NonPositiveDenominator
        }
        NormalizedInvariantStatus::DenominatorBelowPolicyThreshold => {
            AbstentionReason::DenominatorBelowPolicyThreshold
        }
        NormalizedInvariantStatus::NumericallyUnrepresentable => {
            AbstentionReason::NumericallyUnrepresentable
        }
        _ => {
            return Err(PidError::NumericalInstability {
                context: "exp0 normalized invariant: unrecognized report status",
            });
        }
    };
    if report.value.is_some() {
        return Err(PidError::NumericalInstability {
            context: "exp0 normalized invariant: unavailable status carried a value",
        });
    }
    Ok(ScientificOutcome::Abstained { reason })
}

/// Opt-in uncertainty-quantification configuration for the Exp0 gate.
///
/// Both `n_boot` and `n_perm` default to 0 (disabled), which keeps uncertainty
/// computations and per-estimate uncertainty events absent from the default run. When enabled, the
/// runner adds block-subsample diagnostic quantiles without repeated row indices and single-source
/// permutation p-values on the d=`uncertainty_dim` cases and folds preregistered
/// ground-truth checks into the scoped MI/coherence verdict.
#[derive(Debug, Clone, Copy)]
struct UncertaintyConfig {
    /// Number of block-subsample resamples (0 disables diagnostic quantiles).
    n_boot: usize,
    /// Number of permutations for single-source null tests (0 disables them).
    n_perm: usize,
    /// Moving-block length for the resamplers (1 = i.i.d., correct for these
    /// non-temporal synthetic scenarios).
    block_size: usize,
    /// Tail probability for diagnostic quantiles and permutation decisions.
    alpha: f64,
    /// Base seed for the resamplers (kept separate from the data seeds).
    seed: u64,
}

impl UncertaintyConfig {
    fn enabled(&self) -> bool {
        self.n_boot > 0 || self.n_perm > 0
    }
}

impl Default for UncertaintyConfig {
    fn default() -> Self {
        Self {
            n_boot: 0,
            n_perm: 0,
            block_size: 1,
            alpha: 0.05,
            seed: 0xC0FFEE,
        }
    }
}

#[derive(Debug, Clone, Copy)]
struct CaseCommon<'a> {
    csv: bool,
    n: usize,
    ksg_cfg: &'a KsgConfig,
    hash_project_to: Option<usize>,
}

#[derive(Debug, Clone, Copy)]
struct CaseSpec<'a> {
    name: &'a str,
    d: usize,
    seed: u64,
}

#[derive(Debug, Clone, Copy)]
struct Exp0RunConfig<'a> {
    n: usize,
    k: usize,
    dims: &'a [usize],
    seeds: &'a [u64],
    hash_project_to: Option<usize>,
    uncertainty: UncertaintyConfig,
}

#[derive(Debug)]
enum Exp0Error {
    Pid(pid_core::PidError),
    Io(io::Error),
    RunLog(anyhow::Error),
    StrictGate(String),
    Config(String),
}

impl From<pid_core::PidError> for Exp0Error {
    fn from(value: pid_core::PidError) -> Self {
        Self::Pid(value)
    }
}

impl From<io::Error> for Exp0Error {
    fn from(value: io::Error) -> Self {
        Self::Io(value)
    }
}

impl From<anyhow::Error> for Exp0Error {
    fn from(value: anyhow::Error) -> Self {
        Self::RunLog(value)
    }
}

fn main() {
    let args = match parse_args() {
        Ok(Some(a)) => a,
        Ok(None) => {
            let mut out = io::BufWriter::new(io::stdout());
            if let Err(e) = print_usage(&mut out) {
                // If someone does `exp0 --help | head`, avoid panicking.
                if e.kind() == io::ErrorKind::BrokenPipe {
                    return;
                }
                eprintln!("exp0: failed to write help: {e}");
            }
            return;
        }
        Err(msg) => {
            eprintln!("exp0: {msg}");
            eprintln!();
            let mut out = io::BufWriter::new(io::stderr());
            let _ = print_usage(&mut out);
            std::process::exit(2);
        }
    };

    let mut out = io::BufWriter::new(io::stdout());
    if let Err(err) = run(&mut out, args) {
        match err {
            Exp0Error::Io(e) if e.kind() == io::ErrorKind::BrokenPipe => (),
            Exp0Error::Pid(e) => {
                eprintln!("exp0: estimator error: {e}");
                std::process::exit(1);
            }
            Exp0Error::Io(e) => {
                eprintln!("exp0: IO error: {e}");
                std::process::exit(1);
            }
            Exp0Error::RunLog(e) => {
                eprintln!("exp0: run-log error: {e}");
                std::process::exit(1);
            }
            Exp0Error::StrictGate(status) => {
                eprintln!(
                    "exp0: --strict-gate: curated analytic MI recovery verdict is {status}, expected GO"
                );
                std::process::exit(3);
            }
            Exp0Error::Config(msg) => {
                eprintln!("exp0: {msg}");
                std::process::exit(2);
            }
        }
    }
}

fn parse_args() -> Result<Option<Args>, String> {
    let mut csv = false;
    let mut seeds = 3usize;
    let mut strict_gate = false;
    let mut strict_band = false;
    let mut summary_json = None;
    let mut runlog = None;
    let mut uncertainty = UncertaintyConfig::default();
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--csv" => csv = true,
            "--strict-gate" => strict_gate = true,
            "--strict-band" => strict_band = true,
            "--seeds" => {
                let raw = args
                    .next()
                    .ok_or_else(|| "--seeds requires a positive integer".to_string())?;
                seeds = raw
                    .parse::<usize>()
                    .map_err(|_| "--seeds requires a positive integer".to_string())?;
                if seeds == 0 {
                    return Err("--seeds requires a positive integer".to_string());
                }
            }
            "--summary-json" => {
                summary_json = Some(
                    args.next()
                        .ok_or_else(|| "--summary-json requires a path".to_string())?,
                );
            }
            "--runlog" => {
                runlog = Some(
                    args.next()
                        .ok_or_else(|| "--runlog requires a path".to_string())?,
                );
            }
            "--bootstrap" => {
                let raw = args
                    .next()
                    .ok_or_else(|| "--bootstrap requires a non-negative integer".to_string())?;
                uncertainty.n_boot = raw
                    .parse::<usize>()
                    .map_err(|_| "--bootstrap requires a non-negative integer".to_string())?;
            }
            "--permutation" => {
                let raw = args
                    .next()
                    .ok_or_else(|| "--permutation requires a non-negative integer".to_string())?;
                uncertainty.n_perm = raw
                    .parse::<usize>()
                    .map_err(|_| "--permutation requires a non-negative integer".to_string())?;
            }
            "--block-size" => {
                let raw = args
                    .next()
                    .ok_or_else(|| "--block-size requires a positive integer".to_string())?;
                uncertainty.block_size = raw
                    .parse::<usize>()
                    .map_err(|_| "--block-size requires a positive integer".to_string())?;
                if uncertainty.block_size == 0 {
                    return Err("--block-size requires a positive integer".to_string());
                }
            }
            "--alpha" => {
                let raw = args
                    .next()
                    .ok_or_else(|| "--alpha requires a float in (0,1)".to_string())?;
                uncertainty.alpha = raw
                    .parse::<f64>()
                    .map_err(|_| "--alpha requires a float in (0,1)".to_string())?;
                if !(uncertainty.alpha > 0.0 && uncertainty.alpha < 1.0) {
                    return Err("--alpha requires a float in (0,1)".to_string());
                }
            }
            "--help" | "-h" => return Ok(None),
            other => return Err(format!("unknown argument: {other}")),
        }
    }
    Ok(Some(Args {
        csv,
        seeds,
        strict_gate,
        strict_band,
        summary_json,
        runlog,
        uncertainty,
    }))
}

fn normalized_absolute_path(path: &Path) -> io::Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()?.join(path)
    };
    let mut normalized = PathBuf::new();
    for component in absolute.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                normalized.pop();
            }
            _ => normalized.push(component.as_os_str()),
        }
    }
    Ok(normalized)
}

fn resolved_artifact_destination(path: &Path) -> io::Result<PathBuf> {
    const MAX_SYMLINK_EXPANSIONS: usize = 40;

    let mut pending = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()?.join(path)
    };
    let mut followed_symlinks = 0usize;

    loop {
        let mut resolved = PathBuf::new();
        let mut missing_depth = 0usize;
        let mut components = pending.components();
        let mut restart = None;

        while let Some(component) = components.next() {
            match component {
                Component::CurDir => {}
                Component::ParentDir => {
                    resolved.pop();
                    missing_depth = missing_depth.saturating_sub(1);
                }
                Component::Prefix(_) | Component::RootDir => {
                    resolved.push(component.as_os_str());
                    missing_depth = 0;
                }
                Component::Normal(part) if missing_depth > 0 => {
                    resolved.push(part);
                    missing_depth = missing_depth.saturating_add(1);
                }
                Component::Normal(part) => {
                    let candidate = resolved.join(part);
                    match std::fs::symlink_metadata(&candidate) {
                        Ok(metadata) if metadata.file_type().is_symlink() => {
                            followed_symlinks = followed_symlinks.saturating_add(1);
                            if followed_symlinks > MAX_SYMLINK_EXPANSIONS {
                                return Err(io::Error::new(
                                    io::ErrorKind::InvalidInput,
                                    "too many symbolic links while resolving artifact path",
                                ));
                            }
                            let target = std::fs::read_link(&candidate)?;
                            let mut next = if target.is_absolute() {
                                target
                            } else {
                                resolved.join(target)
                            };
                            for remaining in components {
                                next.push(remaining.as_os_str());
                            }
                            restart = Some(next);
                            break;
                        }
                        // Canonicalizing every existing non-symlink component also resolves
                        // platform aliases that are not reported as ordinary symbolic links
                        // (for example Windows junctions) and normalizes case on
                        // case-insensitive filesystems. This matters when only the final child is
                        // missing, because `same_file` cannot compare that child later.
                        Ok(_) => resolved = std::fs::canonicalize(candidate)?,
                        Err(error) if error.kind() == io::ErrorKind::NotFound => {
                            resolved = candidate;
                            missing_depth = 1;
                        }
                        Err(error) => return Err(error),
                    }
                }
            }
        }

        if let Some(next) = restart {
            pending = next;
        } else {
            return normalized_absolute_path(&resolved);
        }
    }
}

fn nearest_existing_artifact_directory(path: &Path) -> io::Result<PathBuf> {
    let mut candidate = path.parent().unwrap_or(path);
    loop {
        match std::fs::metadata(candidate) {
            Ok(metadata) if metadata.is_dir() => return std::fs::canonicalize(candidate),
            Ok(_) => {
                return Err(io::Error::new(
                    io::ErrorKind::NotADirectory,
                    format!(
                        "artifact path ancestor is not a directory: {}",
                        candidate.display()
                    ),
                ));
            }
            Err(error) if error.kind() == io::ErrorKind::NotFound => {
                candidate = candidate.parent().ok_or_else(|| {
                    io::Error::new(
                        io::ErrorKind::NotFound,
                        "artifact path has no existing ancestor directory",
                    )
                })?;
            }
            Err(error) => return Err(error),
        }
    }
}

fn filesystem_is_case_insensitive(directory: &Path) -> io::Result<bool> {
    static NEXT_PROBE: AtomicU64 = AtomicU64::new(0);
    const MAX_PROBE_ATTEMPTS: usize = 32;

    for _ in 0..MAX_PROBE_ATTEMPTS {
        let sequence = NEXT_PROBE.fetch_add(1, Ordering::Relaxed);
        let lower = directory.join(format!(
            ".pid-rs-case-probe-{}-{sequence}-lower",
            std::process::id()
        ));
        let upper = directory.join(format!(
            ".PID-RS-CASE-PROBE-{}-{sequence}-LOWER",
            std::process::id()
        ));
        match OpenOptions::new().write(true).create_new(true).open(&lower) {
            Ok(file) => {
                drop(file);
                let alias_result = match same_file::is_same_file(&lower, &upper) {
                    Ok(matches) => Ok(matches),
                    Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(false),
                    Err(error) => Err(error),
                };
                let cleanup_result = std::fs::remove_file(&lower);
                cleanup_result?;
                return alias_result;
            }
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(error) => return Err(error),
        }
    }

    Err(io::Error::new(
        io::ErrorKind::AlreadyExists,
        "could not allocate a unique filesystem case-sensitivity probe",
    ))
}

fn missing_case_only_artifact_paths_alias(left: &Path, right: &Path) -> io::Result<bool> {
    if !left.as_os_str().eq_ignore_ascii_case(right.as_os_str()) {
        return Ok(false);
    }

    let left_directory = nearest_existing_artifact_directory(left)?;
    let right_directory = nearest_existing_artifact_directory(right)?;
    if !same_file::is_same_file(&left_directory, &right_directory)? {
        return Ok(false);
    }

    filesystem_is_case_insensitive(&left_directory)
}

fn artifact_paths_alias(left: &Path, right: &Path) -> io::Result<bool> {
    let resolved_left = resolved_artifact_destination(left)?;
    let resolved_right = resolved_artifact_destination(right)?;
    if resolved_left == resolved_right {
        return Ok(true);
    }
    match same_file::is_same_file(left, right) {
        Ok(true) => Ok(true),
        Ok(false) => missing_case_only_artifact_paths_alias(&resolved_left, &resolved_right),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            missing_case_only_artifact_paths_alias(&resolved_left, &resolved_right)
        }
        Err(error) => Err(error),
    }
}

fn validate_artifact_paths(args: &Args) -> Result<(), Exp0Error> {
    if let (Some(summary), Some(runlog)) = (&args.summary_json, &args.runlog) {
        if artifact_paths_alias(Path::new(summary), Path::new(runlog))? {
            return Err(Exp0Error::Config(
                "--summary-json and --runlog must refer to distinct files".to_string(),
            ));
        }
    }
    Ok(())
}

fn print_usage(out: &mut dyn Write) -> io::Result<()> {
    writeln!(
        out,
        "Usage: exp0 [--csv] [--seeds N] [--summary-json PATH] [--runlog PATH]"
    )?;
    writeln!(
        out,
        "            [--bootstrap N] [--permutation N] [--block-size N] [--alpha F]"
    )?;
    writeln!(out, "            [--strict-band] [--strict-gate]")?;
    writeln!(out)?;
    writeln!(
        out,
        "  --csv   Emit machine-readable CSV (blank-line-separated labeled tables, each with its own header)."
    )?;
    writeln!(
        out,
        "  --seeds N   Run N deterministic seeds per case (default: 3)."
    )?;
    writeln!(
        out,
        "  --summary-json PATH   Write gate summary metadata as JSON."
    )?;
    writeln!(
        out,
        "  --runlog PATH   Write canonical run-log events for the Exp0 summary."
    )?;
    writeln!(
        out,
        "  --bootstrap N   Duplicate-free subsample diagnostics (N resamples) on the d={UNCERTAINTY_DIM} cases."
    )?;
    writeln!(
        out,
        "  --permutation N   Single-source permutation null tests (N permutations) on the d={UNCERTAINTY_DIM} cases."
    )?;
    writeln!(
        out,
        "  --block-size N   Moving-block length for resamplers (default: 1 = i.i.d.)."
    )?;
    writeln!(
        out,
        "  --alpha F   Tail probability for diagnostic quantiles / permutation decisions (default: 0.05)."
    )?;
    writeln!(
        out,
        "  --strict-band   Also run the curated band (analytic d=1 Gaussian MI gate at n={STRICT_BAND_GATE_N},"
    )?;
    writeln!(
        out,
        "                  plus an informational d<=8 scenario diagnostic sweep)."
    )?;
    writeln!(
        out,
        "  --strict-gate   Exit with code 3 unless analytic MI recovery is GO. Enforced on the curated"
    )?;
    writeln!(
        out,
        "                  low-dimension band (implies --strict-band), NOT the default high-d sweep,"
    )?;
    writeln!(
        out,
        "                  whose MI/coherence NO-GO or geometry PIVOT findings are informative."
    )?;
    writeln!(out, "  -h, --help   Show this help.")?;
    Ok(())
}

fn make_seeds(n: usize) -> Result<Vec<u64>, Exp0Error> {
    let mut seeds = Vec::new();
    seeds.try_reserve_exact(n).map_err(|_| {
        Exp0Error::Config("--seeds is too large to allocate the requested seed schedule".into())
    })?;
    seeds.extend((0..n).map(|i| 42u64.wrapping_add((i as u64).wrapping_mul(1_000_003))));
    Ok(seeds)
}

/// Ambient dimension at which uncertainty quantification (bootstrap/permutation)
/// is run. The smallest dimension is the regime where continuous kNN estimation is
/// most plausible; running UQ there gives the gate its best chance of healthy
/// recovery, so a failure here is a strong NO-GO signal rather than an expected
/// curse-of-dimensionality artefact.
const UNCERTAINTY_DIM: usize = 10;

// ---------------------------------------------------------------------------
// Curated strict band (--strict-band / --strict-gate target)
// ---------------------------------------------------------------------------
//
// The DEFAULT sweep deliberately runs to dimension 256 at n=500, entering regimes
// where continuous kNN MI is known to break down (Kraskov 2004 §III; Gao 2015): a
// MI/coherence NO-GO or descriptive geometry PIVOT findings on the full default sweep are
// expected, informative outcomes, not build failures (see AGENTS.md "exp0 is a diagnostic
// gate"). The default sweep must therefore never be the target of a hard pass/fail gate.
//
// `--strict-gate` instead enforces GO on a CURATED BAND where GO is legitimately
// expected AND is checked against an ANALYTIC closed form (not against the estimator's
// own output — AGENTS.md: "a numerical result must be justified by an analytic closed
// form or a cited paper, NEVER tuned to match the estimator").
//
// WHAT THE GATE CHECKS: a small grid of jointly-GAUSSIAN systems at d=1 (pure signal, no
// noise dimensions) and n=4000 (STRICT_BAND_GATE_N — the sample size pinned by this finite
// analytic regression; the NON-gating scenario diagnostic still runs at
// n=STRICT_BAND_N=500). The pass/fail items are the three MEASURE-INDEPENDENT mutual
// information terms I(S1;T), I(S2;T), I(S1,S2;T), each compared to its Cover–Thomas
// Gaussian closed form within the scale-aware tolerance used elsewhere in the gate. GO ⇔
// every MI term across the grid is within tolerance. These terms have closed-form analytic
// references and do not depend on which redundancy MEASURE is chosen. Passing this finite grid
// is regression evidence, not a general validation claim for KSG.
//
// WHY NOT GATE ON THE FOUR SYNTHETIC SCENARIOS AT d<=8: empirically they are NOT a GO
// regime because `redundant_copy`/`unique_s1` carry very high MI; KSG underestimates the JOINT
//     (concatenated-source) MI relative to a marginal, tripping the monotonicity counter
//     — the well-known KSG joint-space bias under strong dependence (Kraskov 2004 §III;
//     Gao 2015). The d-1 pure-noise source coordinates also dominate the Chebyshev
//     neighbour structure and collapse the estimate.
// `independent_additive` has positive shared-exclusions redundancy; Exp0 reports that estimate but
// never compares it to a zero-redundancy target and never folds it into any verdict.
// Gating GO on those would require loosening the checks, which the conventions forbid. The
// scenarios are still RUN at d in STRICT_BAND_DIAG_DIMS as an INFORMATIONAL diagnostic
// (printed, NOT gated) so the documented d<=8 sweep is exercised and the findings surfaced.
const STRICT_BAND_N: usize = 500;
/// Sample size for the ANALYTIC d=1 Gaussian gate. Larger than `STRICT_BAND_N` because the gate
/// asserts recovery of the closed-form MI terms within the scale-aware noise floor (0.05 nats),
/// which requires a larger sample in this deterministic regression: at n=500 the observed
/// finite-sample discrepancy (~0.06 nats at moderate MI) sits right at that floor, whereas
/// n=4000 satisfies the committed Gaussian grid used here and in
/// tests/gaussian_pid_atoms.rs. This is a scoped test-design choice, not a population-level KSG
/// guarantee; the tolerance is not loosened to accommodate the smaller-sample discrepancy.
const STRICT_BAND_GATE_N: usize = 4000;
/// Informational (NON-gating) low-dimension scenario sweep run alongside the analytic gate so
/// the documented d<=8 scenarios are still exercised and their estimator-hostility surfaced.
const STRICT_BAND_DIAG_DIMS: [usize; 3] = [2, 4, 8];
const STRICT_BAND_SEEDS: usize = 3;
/// The d=1 jointly-Gaussian gate grid as `(a, b, c)` coefficients of `T = a*S1 + b*S2 + c*Z`,
/// with S1,S2,Z ~ N(0,1) independent. Moderate MI keeps every term inside KSG's accurate
/// regime; the mix spans redundant-leaning (a==b), unique-leaning (a > b), and balanced cases
/// so the gate is non-trivial. See `gaussian_mi_truth` for the closed-form MI terms.
const STRICT_BAND_GAUSS_GRID: [(f64, f64, f64); 3] =
    [(1.0, 1.0, 1.0), (1.0, 0.3, 1.0), (0.7, 0.7, 1.0)];

/// The four synthetic scenarios, with their preregistered ground-truth marginal
/// informativeness. A source is "marginally informative" iff `I(source; T) > 0` in
/// the data-generating process — independent of any estimator.
///
/// This table is the falsifiable contract the permutation null tests check:
/// the KSG-based permutation test must call a source significant iff that source
/// is marginally informative by construction.
const SCENARIOS: [&str; 4] = [
    "independent_additive",
    "redundant_copy",
    "unique_s1",
    "xor_like",
];

/// Returns `(s1_informative, s2_informative)` ground truth for a scenario.
fn marginal_truth(scenario: &str) -> (bool, bool) {
    match scenario {
        // T = s1[0] + s2[0] + noise → both sources marginally informative.
        "independent_additive" => (true, true),
        // s1[0], s2[0] are noisy copies of T → both marginally informative.
        "redundant_copy" => (true, true),
        // T = s1[0] + noise → only s1 marginally informative.
        "unique_s1" => (true, false),
        // T = sign(s1[0]*s2[0]) → neither source marginally informative (synergy only).
        "xor_like" => (false, false),
        _ => unreachable!("unknown scenario: {scenario}"),
    }
}

/// Per-scenario uncertainty result at `UNCERTAINTY_DIM`.
#[derive(Debug, Clone)]
struct ScenarioUncertainty {
    name: &'static str,
    /// Raw m-sample quantiles for [I(S1;T), I(S2;T), I(S1,S2;T)].
    boot: ScientificOutcome<BootMiTriple>,
    /// Shuffle-S1 / statistic I(S1;T) result.
    perm_s1: ScientificOutcome<PermutationDiagnostic>,
    /// Shuffle-S2 / statistic I(S2;T) result.
    perm_s2: ScientificOutcome<PermutationDiagnostic>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct PermutationDiagnostic {
    tail_fraction: f64,
    n_valid: usize,
}

/// Coherent subsample diagnostic quantiles for the three measure-independent MI terms.
///
/// Shared-exclusions redundancy is deliberately excluded: an atom failure must never contaminate
/// the independently scoped MI/coherence verdict.
#[derive(Debug, Clone, Copy)]
struct BootMiTriple {
    i1: QuantileTriple,
    i2: QuantileTriple,
    i12: QuantileTriple,
}

#[derive(Debug, Clone, Copy)]
struct QuantileTriple {
    point: f64,
    quantile_low: f64,
    quantile_high: f64,
    n_valid: usize,
}

impl QuantileTriple {
    fn from_stat(stat: &RowBootstrapStat) -> Result<Self, Exp0Error> {
        let values = [
            stat.point_estimate,
            stat.percentile_lower,
            stat.percentile_upper,
        ];
        if values.iter().any(|value| !value.is_finite()) {
            return Err(Exp0Error::Pid(PidError::NumericalInstability {
                context: "exp0 uncertainty: produced quantile summary was non-finite",
            }));
        }
        Ok(Self {
            point: stat.point_estimate,
            quantile_low: stat.percentile_lower,
            quantile_high: stat.percentile_upper,
            n_valid: stat.n_valid,
        })
    }
}

/// Aggregate uncertainty summary across scenarios, with the derived gate checks.
#[derive(Debug, Clone, Default)]
struct UncertaintySummary {
    enabled: bool,
    n_boot: usize,
    n_perm: usize,
    block_size: usize,
    subsample_len: Option<usize>,
    alpha: f64,
    seed: u64,
    scenarios: Vec<ScenarioUncertainty>,
    /// Number of preregistered permutation marginal-significance checks performed.
    permutation_checks: usize,
    /// Number of those checks where the estimator agreed with ground truth.
    permutation_agreements: usize,
    /// Scenarios whose coherent bootstrap distribution was invalidated by any failed/non-finite
    /// resample (an estimator-instability signal at the most favourable dimension).
    bootstrap_instabilities: usize,
}

/// The measure-independent MI statistic vector used for subsample diagnostics:
/// `[I(S1;T), I(S2;T), I(S1,S2;T)]`.
fn uncertainty_stat_vec(mats: &[MatRef<'_>], ksg_cfg: &KsgConfig) -> pid_core::PidResult<Vec<f64>> {
    let s1 = mats[0];
    let s2 = mats[1];
    let t = mats[2];
    let i1 = ksg_mi(s1, t, ksg_cfg)?;
    let i2 = ksg_mi(s2, t, ksg_cfg)?;
    let i12 = ksg_mi_concat_xy(s1, s2, t, ksg_cfg)?;
    Ok(vec![i1, i2, i12])
}

fn uncertainty_callback_declaration(
    mats: &[MatRef<'_>; 3],
) -> pid_core::PidResult<StatisticCallbackDeclaration> {
    let base = ksg_resource_estimate(mats[0], mats[2])?;
    // Three neighbor-derived calls are made; the joined-source call retains more scratch than one
    // marginal KSG call, so charge a conservative eightfold peak/work envelope rather than
    // pretending the callback is free.
    let scale = 8_u128;
    let mut per_call = ResourceEstimate::ZERO;
    per_call.estimated_bytes =
        base.estimated_bytes
            .checked_mul(scale)
            .ok_or(PidError::SizeOverflow {
                operation: "exp0 uncertainty callback",
            })?;
    per_call.pairwise_distances =
        base.pairwise_distances
            .checked_mul(4)
            .ok_or(PidError::SizeOverflow {
                operation: "exp0 uncertainty callback",
            })?;
    per_call.operations_hint =
        base.operations_hint
            .checked_mul(scale)
            .ok_or(PidError::SizeOverflow {
                operation: "exp0 uncertainty callback",
            })?;
    StatisticCallbackDeclaration::vector(3, per_call)
}

fn permutation_callback_declaration(
    source: MatRef<'_>,
    target: MatRef<'_>,
) -> pid_core::PidResult<StatisticCallbackDeclaration> {
    StatisticCallbackDeclaration::vector(1, ksg_resource_estimate(source, target)?)
}

/// Retain a coherent resampling result, or convert a numerical draw failure into one explicit
/// Exp0 gate violation. Configuration/programming errors still abort the run.
fn retain_resampling_or_count_instability<T>(
    result: pid_core::PidResult<T>,
    instabilities: &mut usize,
) -> Result<ScientificOutcome<T>, Exp0Error> {
    match result {
        Ok(value) => Ok(ScientificOutcome::Produced(value)),
        Err(PidError::NumericalInstability { .. }) => {
            *instabilities = instabilities.checked_add(1).ok_or_else(|| {
                Exp0Error::Config("bootstrap-instability counter overflow".to_string())
            })?;
            Ok(ScientificOutcome::Abstained {
                reason: AbstentionReason::NumericalInstability,
            })
        }
        Err(error) => Err(Exp0Error::Pid(error)),
    }
}

fn permutation_outcome(
    result: pid_core::PidResult<RowPermutationStat>,
) -> Result<ScientificOutcome<PermutationDiagnostic>, Exp0Error> {
    match result {
        Ok(result) => match result.tail_fraction {
            Some(tail_fraction) if tail_fraction.is_finite() => {
                Ok(ScientificOutcome::Produced(PermutationDiagnostic {
                    tail_fraction,
                    n_valid: result.n_valid,
                }))
            }
            Some(_) => Err(Exp0Error::Pid(PidError::NumericalInstability {
                context: "exp0 uncertainty: produced permutation tail was non-finite",
            })),
            None => Ok(ScientificOutcome::Abstained {
                reason: AbstentionReason::IncompleteResamplingDistribution,
            }),
        },
        Err(PidError::NumericalInstability { .. }) => Ok(ScientificOutcome::Abstained {
            reason: AbstentionReason::NumericalInstability,
        }),
        Err(error) => Err(Exp0Error::Pid(error)),
    }
}

/// Compute opt-in uncertainty quantification for all scenarios at `UNCERTAINTY_DIM`.
///
/// Determinism: uses a single fixed data seed (`make_seeds(1)?[0]`) and the
/// resampler seed from `cfg`, so output is reproducible and runtime is bounded
/// independent of `--seeds`.
fn compute_uncertainty(
    n: usize,
    ksg_cfg: &KsgConfig,
    cfg: UncertaintyConfig,
) -> Result<UncertaintySummary, Exp0Error> {
    let data_seed = make_seeds(1)?[0];
    let noise_std = 0.05;
    let d = UNCERTAINTY_DIM;
    let subsample_len = if cfg.n_boot > 0 {
        // The subsample spans half the rows in whole blocks, so a block larger than n/2 leaves
        // zero whole blocks and surfaces an opaque downstream estimator error. This setting is
        // irrelevant to permutation-only runs and is therefore validated only when requested.
        if cfg.block_size > n / 2 {
            return Err(Exp0Error::Config(format!(
                "--block-size must be <= n/2 (= {}) so the subsample spans at least one whole block",
                n / 2
            )));
        }
        // Half the rows, in whole random-origin circular blocks. The resulting raw m-sample
        // quantiles avoid duplicate-row kNN artifacts, but are not calibrated confidence
        // intervals for the full n-row estimate.
        Some(((n / 2) / cfg.block_size) * cfg.block_size)
    } else {
        None
    };

    let mut summary = UncertaintySummary {
        enabled: true,
        n_boot: cfg.n_boot,
        n_perm: cfg.n_perm,
        block_size: cfg.block_size,
        subsample_len,
        alpha: cfg.alpha,
        seed: cfg.seed,
        ..Default::default()
    };

    for &name in &SCENARIOS {
        let (s1, s2, t) = match name {
            "independent_additive" => gen_independent_additive(n, d, noise_std, data_seed),
            "redundant_copy" => gen_redundant_copy(n, d, noise_std, data_seed),
            "unique_s1" => gen_unique_s1(n, d, noise_std, data_seed),
            "xor_like" => gen_xor_like(n, d, noise_std, data_seed),
            _ => unreachable!(),
        };
        let s1 = MatRef::new(&s1, n, d)?;
        let s2 = MatRef::new(&s2, n, d)?;
        let t = MatRef::new(&t, n, 1)?;
        let (s1z, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error)?;
        let (s2z, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error)?;
        let (tz, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error)?;
        let mats: [MatRef<'_>; 3] = [s1z.as_ref(), s2z.as_ref(), tz.as_ref()];

        let mut scen = ScenarioUncertainty {
            name,
            boot: ScientificOutcome::NotRequested,
            perm_s1: ScientificOutcome::NotRequested,
            perm_s2: ScientificOutcome::NotRequested,
        };

        if cfg.n_boot > 0 {
            let boot_cfg = BootstrapConfig::new(
                cfg.n_boot,
                cfg.block_size,
                cfg.seed,
                cfg.alpha,
                ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
            )?;
            let scheme = RowResampleScheme::Subsample {
                subsample_len: subsample_len.ok_or_else(|| {
                    Exp0Error::Config(
                        "bootstrap was requested without a computed subsample length".to_string(),
                    )
                })?,
            };
            match retain_resampling_or_count_instability(
                bootstrap_rows_stats(
                    &mats,
                    &boot_cfg,
                    scheme,
                    uncertainty_callback_declaration(&mats)?,
                    |m| uncertainty_stat_vec(m, ksg_cfg),
                ),
                &mut summary.bootstrap_instabilities,
            )? {
                ScientificOutcome::Produced(res) => {
                    if let Some(stats) = res.stats {
                        if stats.len() != 3 {
                            return Err(Exp0Error::Pid(PidError::ShapeMismatch {
                                context: "exp0 uncertainty bootstrap statistics",
                                expected_len: 3,
                                actual_len: stats.len(),
                            }));
                        }
                        scen.boot = ScientificOutcome::Produced(BootMiTriple {
                            i1: QuantileTriple::from_stat(&stats[0])?,
                            i2: QuantileTriple::from_stat(&stats[1])?,
                            i12: QuantileTriple::from_stat(&stats[2])?,
                        });
                    } else {
                        summary.bootstrap_instabilities = summary
                            .bootstrap_instabilities
                            .checked_add(1)
                            .ok_or_else(|| {
                                Exp0Error::Config(
                                    "bootstrap-instability counter overflow".to_string(),
                                )
                            })?;
                        scen.boot = ScientificOutcome::Abstained {
                            reason: AbstentionReason::IncompleteResamplingDistribution,
                        };
                    }
                }
                ScientificOutcome::Abstained { reason } => {
                    scen.boot = ScientificOutcome::Abstained { reason };
                }
                ScientificOutcome::NotRequested => {
                    return Err(Exp0Error::Pid(PidError::NumericalInstability {
                        context: "exp0 uncertainty: attempted bootstrap became not-requested",
                    }));
                }
            }
        }

        if cfg.n_perm > 0 {
            // Shuffle S1 (index 0); statistic = I(S1;T).
            let perm_s1 = permutation_outcome(permutation_rows_pvalue(
                &mats,
                0,
                cfg.n_perm,
                cfg.seed,
                permutation_callback_declaration(mats[0], mats[2])?,
                |m| ksg_mi(m[0], m[2], ksg_cfg),
            ))?;
            // Shuffle S2 (index 1); statistic = I(S2;T).
            let perm_s2 = permutation_outcome(permutation_rows_pvalue(
                &mats,
                1,
                cfg.n_perm,
                cfg.seed.wrapping_add(1),
                permutation_callback_declaration(mats[1], mats[2])?,
                |m| ksg_mi(m[1], m[2], ksg_cfg),
            ))?;

            let (truth_s1, truth_s2) = marginal_truth(name);
            // A check "agrees" iff the significance decision matches ground truth.
            for (result, truth) in [(perm_s1, truth_s1), (perm_s2, truth_s2)] {
                summary.permutation_checks += 1;
                // A failed transform invalidates the complete permutation distribution. Record
                // that unavailable test as a gate non-agreement; it cannot confirm either truth
                // value, but should not abort the rest of the diagnostic run.
                if let ScientificOutcome::Produced(result) = result {
                    let significant = result.tail_fraction < cfg.alpha;
                    if significant == truth {
                        summary.permutation_agreements += 1;
                    }
                }
            }
            scen.perm_s1 = perm_s1;
            scen.perm_s2 = perm_s2;
        }

        summary.scenarios.push(scen);
    }

    Ok(summary)
}

#[allow(clippy::too_many_arguments)]
fn write_summary_json(
    path: &str,
    gates: &GateSummary,
    n: usize,
    k: usize,
    dims: &[usize],
    seeds: &[u64],
    hash_project_to: Option<usize>,
    uncertainty: Option<&UncertaintySummary>,
    strict_band: Option<&GateSummary>,
    strict_gate_enforced: bool,
) -> Result<(), Exp0Error> {
    if let Some(parent) = std::path::Path::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let config_hash = config_hash(n, k, dims, seeds, hash_project_to);
    let mut summary = gate_summary_json(gates);
    let fields = summary.as_object_mut().ok_or_else(|| {
        Exp0Error::Config("internal gate summary was not a JSON object".to_string())
    })?;
    // Named to be unconfusable with the run log's SHA-256 `config_hash`: this is a compact
    // FNV-1a-style fold over the numeric parameters only.
    fields.insert(
        "param_fingerprint_fnv64".to_string(),
        json!(format!("{config_hash:016x}")),
    );
    fields.insert("n".to_string(), json!(n));
    fields.insert("k".to_string(), json!(k));
    fields.insert("dims".to_string(), json!(dims));
    fields.insert("seeds".to_string(), json!(seeds));
    fields.insert("hash_project_to".to_string(), json!(hash_project_to));
    fields.insert("default_sweep_status".to_string(), json!(gates.status()));
    let (effective_status, effective_scope) =
        effective_status_and_scope(gates, strict_band, strict_gate_enforced);
    fields.insert("status".to_string(), json!(effective_status));
    fields.insert("status_scope".to_string(), json!(effective_scope.as_str()));
    if let Some(uncertainty) = uncertainty {
        fields.insert("uncertainty".to_string(), uncertainty_json(uncertainty)?);
    }
    if let Some(strict_band) = strict_band {
        fields.insert("strict_band".to_string(), gate_summary_json(strict_band));
        fields.insert(
            "strict_gate_enforced".to_string(),
            json!(strict_gate_enforced),
        );
        fields.insert(
            "strict_gate_passed".to_string(),
            json!(strict_gate_enforced.then(|| strict_band.verdict() == GateVerdict::Go)),
        );
    }

    let mut file = File::create(path)?;
    serde_json::to_writer_pretty(&mut file, &summary).map_err(|error| {
        Exp0Error::Config(format!("failed to serialize Exp0 summary JSON: {error}"))
    })?;
    writeln!(file)?;
    Ok(())
}

fn gate_summary_json(gates: &GateSummary) -> serde_json::Value {
    let mut fields = serde_json::Map::new();
    fields.insert("verdict_scope".to_string(), json!(gates.scope.as_str()));
    fields.insert("case_results".to_string(), json!(gates.case_results));
    fields.insert("status".to_string(), json!(gates.status()));
    fields.insert(
        gates.scope.verdict_field().to_string(),
        json!(gates.status()),
    );
    match gates.scope {
        GateScope::HighDimensionalMiCoherence => {
            fields.insert(
                "monotonicity_violations".to_string(),
                json!(gates.monotonicity_violations),
            );
            fields.insert(
                "normalized_invariant_violations".to_string(),
                json!(gates.normalized_invariant_violations),
            );
            fields.insert(
                "geometry_warnings".to_string(),
                json!(gates.geometry_warnings),
            );
            fields.insert(
                "geometry_abstentions".to_string(),
                json!(gates.geometry_abstentions),
            );
            fields.insert(
                "geometry_disposition".to_string(),
                json!(gates.geometry_disposition().as_str()),
            );
        }
        GateScope::CuratedAnalyticMiRecovery => {
            fields.insert(
                "analytic_mi_recovery_failures".to_string(),
                json!(gates.analytic_mi_recovery_failures),
            );
        }
    }
    fields.insert(
        "atom_validation".to_string(),
        json!({
            "measure": {
                "status": ATOM_MEASURE_VALIDATION_STATUS,
                "reason": ATOM_MEASURE_VALIDATION_REASON,
            },
            "estimator": {
                "status": ATOM_ESTIMATOR_VALIDATION_STATUS,
                "reason": ATOM_ESTIMATOR_VALIDATION_REASON,
            },
        }),
    );
    serde_json::Value::Object(fields)
}

fn effective_status_and_scope(
    gates: &GateSummary,
    strict_band: Option<&GateSummary>,
    strict_gate_enforced: bool,
) -> (&'static str, GateScope) {
    if strict_gate_enforced {
        strict_band.map_or(("NO-GO", GateScope::CuratedAnalyticMiRecovery), |band| {
            (band.status(), band.scope)
        })
    } else {
        (gates.status(), gates.scope)
    }
}

/// Build the JSON value describing an uncertainty run (used by the summary JSON and
/// as the structured payload for run-log evaluation events).
fn uncertainty_json(u: &UncertaintySummary) -> Result<serde_json::Value, Exp0Error> {
    let scenarios: Result<Vec<serde_json::Value>, Exp0Error> = u
        .scenarios
        .iter()
        .map(|s| {
            let (truth_s1, truth_s2) = marginal_truth(s.name);
            Ok(json!({
                "name": s.name,
                "truth_s1_informative": truth_s1,
                "truth_s2_informative": truth_s2,
                "perm_s1": permutation_diagnostic_json(&s.perm_s1)?,
                "perm_s2": permutation_diagnostic_json(&s.perm_s2)?,
                "bootstrap": bootstrap_diagnostic_json(&s.boot)?,
            }))
        })
        .collect();
    let bootstrap_config = match u.subsample_len {
        Some(subsample_len) => json!({
            "status": "requested",
            "block_size": u.block_size,
            "subsample_len": subsample_len,
            "subsample_scheme": "fixed_grid_blocks_without_replacement",
            "subsample_interpretation": "raw_m_sample_quantiles_not_n_sample_confidence_intervals",
        }),
        None => json!({"status": "not_requested"}),
    };
    Ok(json!({
        "dim": UNCERTAINTY_DIM,
        "n_boot": u.n_boot,
        "n_perm": u.n_perm,
        "alpha": u.alpha,
        "seed": u.seed,
        "bootstrap_config": bootstrap_config,
        "permutation_config": {
            "status": if u.n_perm > 0 { "requested" } else { "not_requested" },
            "n_perm": u.n_perm,
        },
        "permutation_checks": u.permutation_checks,
        "permutation_agreements": u.permutation_agreements,
        "bootstrap_instabilities": u.bootstrap_instabilities,
        "scenarios": scenarios?,
    }))
}

fn quantile_json(c: &QuantileTriple) -> Result<serde_json::Value, Exp0Error> {
    if [c.point, c.quantile_low, c.quantile_high]
        .iter()
        .any(|value| !value.is_finite())
    {
        return Err(Exp0Error::Pid(PidError::NumericalInstability {
            context: "exp0 uncertainty JSON: produced quantile was non-finite",
        }));
    }
    Ok(json!({
        "point": c.point,
        "quantile_low": c.quantile_low,
        "quantile_high": c.quantile_high,
        "n_valid": c.n_valid,
    }))
}

fn permutation_diagnostic_json(
    outcome: &ScientificOutcome<PermutationDiagnostic>,
) -> Result<serde_json::Value, Exp0Error> {
    match outcome {
        ScientificOutcome::NotRequested => Ok(json!({"status": "not_requested"})),
        ScientificOutcome::Abstained { reason } => {
            Ok(json!({"status": "abstained", "reason": reason.as_str()}))
        }
        ScientificOutcome::Produced(result) => {
            if !result.tail_fraction.is_finite() {
                return Err(Exp0Error::Pid(PidError::NumericalInstability {
                    context: "exp0 uncertainty JSON: produced permutation tail was non-finite",
                }));
            }
            Ok(json!({
                "status": "produced",
                "tail_fraction": result.tail_fraction,
                "n_valid": result.n_valid,
            }))
        }
    }
}

fn bootstrap_diagnostic_json(
    outcome: &ScientificOutcome<BootMiTriple>,
) -> Result<serde_json::Value, Exp0Error> {
    match outcome {
        ScientificOutcome::NotRequested => Ok(json!({"status": "not_requested"})),
        ScientificOutcome::Abstained { reason } => {
            Ok(json!({"status": "abstained", "reason": reason.as_str()}))
        }
        ScientificOutcome::Produced(result) => Ok(json!({
            "status": "produced",
            "i1": quantile_json(&result.i1)?,
            "i2": quantile_json(&result.i2)?,
            "i12": quantile_json(&result.i12)?,
        })),
    }
}

fn write_exp0_runlog(
    path: &str,
    summary_json_path: Option<&str>,
    gates: &GateSummary,
    config: Exp0RunConfig<'_>,
    uncertainty: Option<&UncertaintySummary>,
    strict_band: Option<&GateSummary>,
    strict_gate_enforced: bool,
) -> Result<(), Exp0Error> {
    match uncertainty {
        Some(summary)
            if summary.enabled != config.uncertainty.enabled()
                || summary.n_boot != config.uncertainty.n_boot
                || summary.n_perm != config.uncertainty.n_perm
                || summary.block_size != config.uncertainty.block_size
                || summary.alpha.to_bits() != config.uncertainty.alpha.to_bits()
                || summary.seed != config.uncertainty.seed =>
        {
            return Err(Exp0Error::Config(
                "uncertainty summary does not match the recorded run configuration".to_string(),
            ));
        }
        Some(_) if !config.uncertainty.enabled() => {
            return Err(Exp0Error::Config(
                "uncertainty output was supplied for a disabled run configuration".to_string(),
            ));
        }
        None if config.uncertainty.enabled() => {
            return Err(Exp0Error::Config(
                "enabled uncertainty configuration is missing its output summary".to_string(),
            ));
        }
        Some(_) | None => {}
    }
    if let Some(parent) = std::path::Path::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let config_json = json!({
        "experiment": "exp0",
        "n": config.n,
        "k": config.k,
        "dims": config.dims,
        "seeds": config.seeds,
        "hash_project_to": config.hash_project_to,
        "strict_band_requested": strict_band.is_some(),
        "strict_gate_enforced": strict_gate_enforced,
        "uncertainty": {
            "enabled": config.uncertainty.enabled(),
            "n_boot": config.uncertainty.n_boot,
            "n_perm": config.uncertainty.n_perm,
            "block_size": config.uncertainty.block_size,
            "alpha": config.uncertainty.alpha,
            "seed": config.uncertainty.seed,
            "subsample_scheme": if config.uncertainty.n_boot > 0 {
                Some("fixed_grid_blocks_without_replacement")
            } else {
                None
            },
            "subsample_len": uncertainty.and_then(|summary| summary.subsample_len),
        },
        "continuous_estimator_contract": {
            "support": "assume_regular_full_dimensional",
            "metric": "chebyshev_linf",
            "negative_handling": "allow",
            "tie_epsilon": 0.0,
            "ksg_status": "restricted_domain",
            "isx_methods": {
                "primary": {
                    "method": "ehrlich_ksg",
                    "status": "experimental_restricted_domain",
                },
                "diagnostic_baselines": [
                    {"method": "local_min_ksg", "status": "experimental_baseline"},
                    {"method": "disjunction_from_local_mi", "status": "experimental_baseline"},
                ],
            },
        },
        "preprocessing_provenance": {
            "baseline": "fit_and_apply_per_case_standardization",
            "projection_variants": ["seeded_countsketch_sources_only", "pca_sources_only"],
            "observation_noise": "scenario_generator_only_no_posthoc_jitter",
        },
        // The historic key is retained for run-log continuity, but its value is now pid-core's
        // typed software identity. It deliberately changes `config_hash` across captured build
        // contexts and is neither an executable attestation nor scientific-result provenance.
        "build_provenance": pid_core::software_identity(),
    });
    let config_hash = pid_runlog::canonical_json_hash_v2(&config_json)?;
    let strict_gate_failed = strict_gate_enforced
        && strict_band
            .map(|band| band.status() != "GO")
            .unwrap_or(true);
    let (reported_status, reported_scope) =
        effective_status_and_scope(gates, strict_band, strict_gate_enforced);
    let mut run_metadata = [
        ("source".to_string(), "pid-core-exp0".to_string()),
        ("status".to_string(), reported_status.to_string()),
        (
            "status_scope".to_string(),
            reported_scope.as_str().to_string(),
        ),
        (
            "default_sweep_status".to_string(),
            gates.status().to_string(),
        ),
        (
            "strict_gate_enforced".to_string(),
            strict_gate_enforced.to_string(),
        ),
    ]
    .into_iter()
    .collect::<std::collections::BTreeMap<_, _>>();
    run_metadata.insert(
        "verdict_scope".to_string(),
        gates.scope.as_str().to_string(),
    );
    run_metadata.insert(
        gates.scope.verdict_field().to_string(),
        gates.status().to_string(),
    );
    run_metadata.insert(
        "atom_measure_validation".to_string(),
        ATOM_MEASURE_VALIDATION_STATUS.to_string(),
    );
    run_metadata.insert(
        "atom_estimator_validation".to_string(),
        ATOM_ESTIMATOR_VALIDATION_STATUS.to_string(),
    );
    if let Some(band) = strict_band {
        run_metadata.insert("strict_band_status".to_string(), band.status().to_string());
        run_metadata.insert(
            "strict_band_scope".to_string(),
            band.scope.as_str().to_string(),
        );
    }
    let mut writer = RunLogWriter::create(path)?;
    writer.append(&RunLogEvent::RunStarted {
        schema_version: RUN_LOG_SCHEMA_VERSION,
        run_id: "exp0-rust-quick-run".to_string(),
        timestamp_ns: 0,
        config_hash: config_hash.clone(),
        metadata: run_metadata,
    })?;
    writer.append(&RunLogEvent::ConfigLogged {
        timestamp_ns: 0,
        config_hash,
        config: config_json,
    })?;
    let default_metric_count = write_exp0_metric_events(&mut writer, gates, "exp0", 0, 1)?;
    let mut next_step = default_metric_count as u64;
    let mut next_timestamp = next_step + 1;
    if let Some(u) = uncertainty {
        write_exp0_uncertainty_events(&mut writer, u, next_step, next_timestamp)?;
        next_step += 1;
        next_timestamp += 1;
    }
    if let Some(band) = strict_band {
        let strict_metric_count = write_exp0_metric_events(
            &mut writer,
            band,
            "exp0.strict_band",
            next_step,
            next_timestamp,
        )?;
        next_step += strict_metric_count as u64;
        next_timestamp += strict_metric_count as u64;
    }
    if let Some(summary_path) = summary_json_path {
        let mut artifact_metadata = [
            (
                "default_sweep_status".to_string(),
                gates.status().to_string(),
            ),
            ("status".to_string(), reported_status.to_string()),
            (
                "status_scope".to_string(),
                reported_scope.as_str().to_string(),
            ),
            (
                "verdict_scope".to_string(),
                gates.scope.as_str().to_string(),
            ),
            (
                gates.scope.verdict_field().to_string(),
                gates.status().to_string(),
            ),
            (
                "atom_measure_validation".to_string(),
                ATOM_MEASURE_VALIDATION_STATUS.to_string(),
            ),
            (
                "atom_estimator_validation".to_string(),
                ATOM_ESTIMATOR_VALIDATION_STATUS.to_string(),
            ),
        ]
        .into_iter()
        .collect::<std::collections::BTreeMap<_, _>>();
        if let Some(band) = strict_band {
            artifact_metadata.insert(
                band.scope.verdict_field().to_string(),
                band.status().to_string(),
            );
        }
        writer.append(&RunLogEvent::ArtifactLogged {
            timestamp_ns: next_timestamp,
            name: "exp0_summary_json".to_string(),
            kind: "summary_json".to_string(),
            uri: summary_path.to_string(),
            sha256: Some(pid_runlog::sha256_file(summary_path)?),
            metadata: artifact_metadata,
        })?;
        next_timestamp += 1;
    }
    if gates.status() != "GO" {
        writer.append(&RunLogEvent::ErrorLogged {
            step: Some(next_step),
            timestamp_ns: next_timestamp,
            message: format!(
                "Experiment 0 {} verdict: {}",
                gates.scope.as_str(),
                gates.status()
            ),
            recoverable: true,
        })?;
        next_step += 1;
        next_timestamp += 1;
    }
    if strict_gate_failed {
        writer.append(&RunLogEvent::ErrorLogged {
            step: Some(next_step),
            timestamp_ns: next_timestamp,
            message: format!("Experiment 0 strict gate status: {reported_status}"),
            recoverable: false,
        })?;
        next_timestamp += 1;
    }
    let run_status = if strict_gate_failed {
        RunStatus::Failed
    } else {
        RunStatus::Succeeded
    };
    let message = strict_band.map_or_else(
        || {
            format!(
                "Exp0 {} verdict: {}; atom measure validation: {}; atom estimator validation: {}",
                gates.scope.as_str(),
                gates.status(),
                ATOM_MEASURE_VALIDATION_STATUS,
                ATOM_ESTIMATOR_VALIDATION_STATUS,
            )
        },
        |band| {
            format!(
                "Exp0 {} verdict: {}; {} verdict: {}; strict gate enforced: {strict_gate_enforced}; atom measure validation: {}; atom estimator validation: {}",
                gates.scope.as_str(),
                gates.status(),
                band.scope.as_str(),
                band.status(),
                ATOM_MEASURE_VALIDATION_STATUS,
                ATOM_ESTIMATOR_VALIDATION_STATUS,
            )
        },
    );
    writer.append(&RunLogEvent::RunEnded {
        run_id: "exp0-rust-quick-run".to_string(),
        timestamp_ns: next_timestamp,
        status: run_status,
        message: Some(message),
    })?;
    writer.flush()?;
    Ok(())
}

fn write_exp0_metric_events<W: Write>(
    writer: &mut RunLogWriter<W>,
    gates: &GateSummary,
    name_prefix: &str,
    step_start: u64,
    timestamp_start: u64,
) -> Result<usize, Exp0Error> {
    let metrics = match gates.scope {
        GateScope::HighDimensionalMiCoherence => vec![
            ("case_results", gates.case_results),
            ("monotonicity_violations", gates.monotonicity_violations),
            (
                "normalized_invariant_violations",
                gates.normalized_invariant_violations,
            ),
            ("geometry_warnings", gates.geometry_warnings),
            ("geometry_abstentions", gates.geometry_abstentions),
            ("mi_coherence_verdict_code", gates.status_code()),
        ],
        GateScope::CuratedAnalyticMiRecovery => vec![
            ("case_results", gates.case_results),
            (
                "analytic_mi_recovery_failures",
                gates.analytic_mi_recovery_failures,
            ),
            ("analytic_mi_recovery_verdict_code", gates.status_code()),
        ],
    };
    let metric_count = metrics.len();
    for (idx, (suffix, value)) in metrics.into_iter().enumerate() {
        writer.append(&RunLogEvent::PidMetric {
            step: step_start + idx as u64,
            timestamp_ns: timestamp_start + idx as u64,
            name: format!("{name_prefix}.{suffix}"),
            value: value as f64,
            metadata: [
                (
                    "verdict_scope".to_string(),
                    gates.scope.as_str().to_string(),
                ),
                (
                    gates.scope.verdict_field().to_string(),
                    gates.status().to_string(),
                ),
            ]
            .into_iter()
            .collect(),
        })?;
    }
    Ok(metric_count)
}

/// Emit uncertainty results as `EvaluationMetric` events (kept distinct from the
/// `PidMetric` gate events so their family remains distinct). The caller assigns a shared
/// step/timestamp after the preceding scoped gate metrics, keeping the stream ordered when a
/// strict-band block follows.
/// Every optional computation emits a typed status event. Produced computations additionally emit
/// their numeric estimates; any non-finite value incorrectly marked produced aborts export.
fn write_exp0_uncertainty_events<W: Write>(
    writer: &mut RunLogWriter<W>,
    u: &UncertaintySummary,
    step: u64,
    timestamp_ns: u64,
) -> Result<(), Exp0Error> {
    let base_meta = || -> BTreeMap<String, String> {
        [("kind".to_string(), "uncertainty".to_string())]
            .into_iter()
            .collect()
    };
    let emit = |writer: &mut RunLogWriter<W>,
                name: String,
                value: f64,
                extra: BTreeMap<String, String>|
     -> Result<(), Exp0Error> {
        if !value.is_finite() {
            return Err(Exp0Error::Pid(PidError::NumericalInstability {
                context: "exp0 run-log: attempted to emit a non-finite evaluation metric",
            }));
        }
        let mut metadata = base_meta();
        metadata.extend(extra);
        writer.append(&RunLogEvent::EvaluationMetric {
            step,
            timestamp_ns,
            name,
            value,
            metadata,
        })?;
        Ok(())
    };

    emit(
        writer,
        "exp0.uncertainty.permutation_checks".to_string(),
        u.permutation_checks as f64,
        BTreeMap::new(),
    )?;
    emit(
        writer,
        "exp0.uncertainty.permutation_agreements".to_string(),
        u.permutation_agreements as f64,
        BTreeMap::new(),
    )?;
    emit(
        writer,
        "exp0.uncertainty.bootstrap_instabilities".to_string(),
        u.bootstrap_instabilities as f64,
        BTreeMap::new(),
    )?;
    if let Some(subsample_len) = u.subsample_len {
        emit(
            writer,
            "exp0.uncertainty.subsample_len".to_string(),
            subsample_len as f64,
            BTreeMap::new(),
        )?;
    }

    for s in &u.scenarios {
        let (truth_s1, truth_s2) = marginal_truth(s.name);
        for (suffix, outcome, truth) in [
            ("perm_s1", &s.perm_s1, truth_s1),
            ("perm_s2", &s.perm_s2, truth_s2),
        ] {
            let mut metadata = scientific_outcome_metadata(outcome);
            metadata.insert("truth_informative".to_string(), truth.to_string());
            if let ScientificOutcome::Produced(result) = outcome {
                metadata.insert("n_valid".to_string(), result.n_valid.to_string());
            }
            emit(
                writer,
                format!("exp0.uncertainty.{}.{suffix}_status_code", s.name),
                outcome.status_code() as f64,
                metadata.clone(),
            )?;
            if let ScientificOutcome::Produced(result) = outcome {
                emit(
                    writer,
                    format!("exp0.uncertainty.{}.{suffix}_p", s.name),
                    result.tail_fraction,
                    metadata,
                )?;
            }
        }
        let bootstrap_metadata = scientific_outcome_metadata(&s.boot);
        emit(
            writer,
            format!("exp0.uncertainty.{}.bootstrap_status_code", s.name),
            s.boot.status_code() as f64,
            bootstrap_metadata.clone(),
        )?;
        if let ScientificOutcome::Produced(b) = &s.boot {
            for (suffix, triple) in [("i1", &b.i1), ("i2", &b.i2), ("i12", &b.i12)] {
                for (value_name, value) in [
                    ("point", triple.point),
                    ("quantile_low", triple.quantile_low),
                    ("quantile_high", triple.quantile_high),
                ] {
                    let mut metadata = bootstrap_metadata.clone();
                    metadata.insert("n_valid".to_string(), triple.n_valid.to_string());
                    emit(
                        writer,
                        format!("exp0.uncertainty.{}.{}_{}", s.name, suffix, value_name),
                        value,
                        metadata,
                    )?;
                }
            }
        }
    }
    Ok(())
}

fn scientific_outcome_metadata<T>(outcome: &ScientificOutcome<T>) -> BTreeMap<String, String> {
    let mut metadata = BTreeMap::from([("status".to_string(), outcome.status().to_string())]);
    if let Some(reason) = outcome.abstention_reason() {
        metadata.insert("reason".to_string(), reason.as_str().to_string());
    }
    metadata
}

fn config_hash(
    n: usize,
    k: usize,
    dims: &[usize],
    seeds: &[u64],
    hash_project_to: Option<usize>,
) -> u64 {
    let mut h = 0xcbf2_9ce4_8422_2325u64;
    mix_u64(&mut h, n as u64);
    mix_u64(&mut h, k as u64);
    mix_u64(&mut h, dims.len() as u64);
    for &d in dims {
        mix_u64(&mut h, d as u64);
    }
    mix_u64(&mut h, seeds.len() as u64);
    for &seed in seeds {
        mix_u64(&mut h, seed);
    }
    mix_u64(&mut h, hash_project_to.map_or(u64::MAX, |v| v as u64));
    h
}

fn mix_u64(h: &mut u64, value: u64) {
    for byte in value.to_le_bytes() {
        *h ^= byte as u64;
        *h = h.wrapping_mul(0x0000_0100_0000_01B3);
    }
}

fn run(out: &mut dyn Write, args: Args) -> Result<(), Exp0Error> {
    // Minimal Experiment 0 runner (Rust-side).
    //
    // This is intentionally small and brute-force; it exists to exercise the estimators end-to-end
    // on synthetic systems and to provide a place to iterate while building the full harness.

    validate_artifact_paths(&args)?;

    let n = 500usize;
    let k = 3usize;
    let dims = [10usize, 64, 256];
    let hash_project_to = Some(64usize);
    let seeds = make_seeds(args.seeds)?;

    // `Allow`, not `ClampToZero`: these MI terms feed the inclusion–exclusion synergy atom
    // (`syn_ehrlich = I12 - I1 - I2 + Red`), the co-information, and r̄/v̄ — the AGENTS.md
    // convention forbids clamping a term before a subtraction (it breaks the PID identity and
    // silently biases the diagnostics in the high-d breakdown regimes this sweep exists to
    // expose). Negative marginal-MI estimates are honest estimator output, not errors.
    let ksg_cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(k)
        .with_metric(Metric::Chebyshev)
        .with_tie_epsilon(0.0)
        .with_negative_handling(NegativeHandling::Allow)
        .with_support_contract(SupportContract::assume_regular_full_dimensional());

    if args.csv {
        write_case_csv_header(out)?;
    } else {
        writeln!(out, "Experiment 0 (Rust quick run)")?;
        writeln!(out, "n={n}, k={k}, dims={dims:?}, seeds={seeds:?}")?;
        writeln!(
            out,
            "project_to={hash_project_to:?} (projection baselines: hash + PCA; S1,S2 only)"
        )?;
        writeln!(out)?;
    }

    let mut gates = GateSummary::default();

    let common = CaseCommon {
        csv: args.csv,
        n,
        ksg_cfg: &ksg_cfg,
        hash_project_to,
    };
    for d in dims {
        for &seed in &seeds {
            for name in [
                "independent_additive",
                "redundant_copy",
                "unique_s1",
                "xor_like",
            ] {
                let res = run_case(out, common, CaseSpec { name, d, seed })?;
                gates.observe_case(name, res.metrics, res.diag);
            }
            if !common.csv {
                writeln!(out)?;
            }
        }
        if !common.csv {
            writeln!(out)?;
        }
    }

    if common.csv {
        writeln!(out)?;
        write_gaussian_csv_header(out)?;
    }
    run_gaussian_channel_strong_dependence_sweep(out, common.csv, 900, &ksg_cfg, 0x51A7_2026)?;

    // Opt-in uncertainty quantification at the most favourable dimension.
    let uncertainty = if args.uncertainty.enabled() {
        let u = compute_uncertainty(n, &ksg_cfg, args.uncertainty)?;
        gates.observe_uncertainty(&u);
        Some(u)
    } else {
        None
    };

    if args.csv {
        if let Some(u) = uncertainty.as_ref() {
            write_uncertainty_csv(out, u)?;
        }
        write_gate_csv_summary(out, &gates)?;
    } else {
        if let Some(u) = uncertainty.as_ref() {
            print_uncertainty(out, u)?;
        }
        writeln!(out, "--- Experiment 0 Summary ---")?;
        gates.print(out)?;
    }

    // Curated low-dimension band. Run it before finalizing artifacts so strict-gate failures are
    // recorded in those artifacts rather than leaving a false successful run behind.
    let run_band = args.strict_band || args.strict_gate;
    let strict_band = if run_band {
        let band = run_strict_band(out, args.csv, &ksg_cfg)?;
        if !args.csv {
            writeln!(out, "--- Strict Band Summary (curated low-d) ---")?;
            band.print(out)?;
        }
        Some(band)
    } else {
        None
    };

    if let Some(path) = args.summary_json.as_deref() {
        write_summary_json(
            path,
            &gates,
            n,
            k,
            &dims,
            &seeds,
            hash_project_to,
            uncertainty.as_ref(),
            strict_band.as_ref(),
            args.strict_gate,
        )?;
    }
    if let Some(path) = args.runlog.as_deref() {
        write_exp0_runlog(
            path,
            args.summary_json.as_deref(),
            &gates,
            Exp0RunConfig {
                n,
                k,
                dims: &dims,
                seeds: &seeds,
                hash_project_to,
                uncertainty: args.uncertainty,
            },
            uncertainty.as_ref(),
            strict_band.as_ref(),
            args.strict_gate,
        )?;
    }

    if args.strict_gate
        && strict_band
            .as_ref()
            .is_none_or(|band| band.verdict() != GateVerdict::Go)
    {
        return Err(Exp0Error::StrictGate(
            strict_band
                .as_ref()
                .map_or("NO-GO", |band| band.status())
                .to_string(),
        ));
    }

    Ok(())
}

/// Compute the curated band's GATING summary: the analytic d=1 Gaussian grid
/// (`STRICT_BAND_GAUSS_GRID` at `STRICT_BAND_GATE_N`). This is the only sweep `--strict-gate`
/// is allowed to enforce GO on, because (a) GO is legitimately expected there — d=1, moderate
/// MI is a curated, analytically checked low-dimensional regime — and (b) the pass/fail items (the
/// three
/// measure-independent MI terms) are checked against a closed-form analytic ground truth, not
/// the estimator's own output (see the `STRICT_BAND_*` rationale block). Kept cheap and separate
/// from the informational diagnostic so the gate can be unit-tested without the slow geometry pass.
fn strict_band_gate(
    out: &mut dyn Write,
    csv: bool,
    ksg_cfg: &KsgConfig,
) -> Result<GateSummary, Exp0Error> {
    let gate_n = STRICT_BAND_GATE_N;
    if !csv {
        writeln!(out)?;
        writeln!(
            out,
            "Strict band GATE (analytic d=1 Gaussian MI, n={gate_n}): MI terms vs Cover-Thomas closed form"
        )?;
    } else {
        // Labeled CSV table for the gating band, blank-line separated from the previous
        // table so the machine-readable stream stays parseable.
        writeln!(out)?;
        writeln!(
            out,
            "system,a,b,c,d,n,i1_hat,i1_true,i2_hat,i2_true,i12_hat,i12_true,mi_passes,mi_checks"
        )?;
    }
    let mut band = GateSummary::curated_analytic_mi();
    let mut seed = 0x6A55_1A20_u64;
    for &(a, b, c) in &STRICT_BAND_GAUSS_GRID {
        let check = run_gaussian_mi_check(out, csv, gate_n, ksg_cfg, a, b, c, seed)?;
        band.observe_gaussian_mi_check(&check);
        seed = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    }
    if csv {
        writeln!(out)?;
        writeln!(
            out,
            "verdict_scope,analytic_mi_recovery_verdict,atom_measure_validation_status,atom_measure_validation_reason,atom_estimator_validation_status,atom_estimator_validation_reason"
        )?;
        writeln!(
            out,
            "{},{},{},{},{},{}",
            band.scope.as_str(),
            band.status(),
            ATOM_MEASURE_VALIDATION_STATUS,
            ATOM_MEASURE_VALIDATION_REASON,
            ATOM_ESTIMATOR_VALIDATION_STATUS,
            ATOM_ESTIMATOR_VALIDATION_REASON,
        )?;
    }
    Ok(band)
}

/// Run the curated band and return the GATING summary, then also run the four synthetic
/// scenarios at `STRICT_BAND_DIAG_DIMS` as an INFORMATIONAL diagnostic: their gate counters
/// are printed, NOT folded into the returned (gating) summary, because they are a known non-GO
/// regime (documented findings, not regressions — see the `STRICT_BAND_*` rationale block).
fn run_strict_band(
    out: &mut dyn Write,
    csv: bool,
    ksg_cfg: &KsgConfig,
) -> Result<GateSummary, Exp0Error> {
    // --- Gating: analytic d=1 Gaussian grid (GO legitimately expected) ---
    let band = strict_band_gate(out, csv, ksg_cfg)?;

    // --- Informational (NON-gating) low-dimension scenario diagnostic ---
    let seeds = make_seeds(STRICT_BAND_SEEDS)?;
    if !csv {
        writeln!(out)?;
        writeln!(
            out,
            "Strict band DIAGNOSTIC (non-gating): four scenarios, dims={STRICT_BAND_DIAG_DIMS:?}, seeds={seeds:?}"
        )?;
    } else {
        // Re-emit the case header before the diagnostic rows so the stream stays parseable after
        // the band table above as the typed schema evolves.
        writeln!(out)?;
        write_case_csv_header(out)?;
    }
    let mut diag_summary = GateSummary::default();
    // No projection baselines: dims are already small and < the default hash_project_to.
    let common = CaseCommon {
        csv,
        n: STRICT_BAND_N,
        ksg_cfg,
        hash_project_to: None,
    };
    for d in STRICT_BAND_DIAG_DIMS {
        for &seed in &seeds {
            for name in [
                "independent_additive",
                "redundant_copy",
                "unique_s1",
                "xor_like",
            ] {
                let res = run_case(out, common, CaseSpec { name, d, seed })?;
                diag_summary.observe_case(name, res.metrics, res.diag);
            }
            if !csv {
                writeln!(out)?;
            }
        }
    }
    if !csv {
        writeln!(
            out,
            "  [diagnostic only, NOT gated] scenario verdict={} (known non-GO regime: see STRICT_BAND rationale)",
            diag_summary.status()
        )?;
        writeln!(
            out,
            "  [diagnostic only] monotonicity_violations={} normalized_invariant_violations={} geometry_warnings={} geometry_abstentions={}",
            diag_summary.monotonicity_violations,
            diag_summary.normalized_invariant_violations,
            diag_summary.geometry_warnings,
            diag_summary.geometry_abstentions,
        )?;
    }

    Ok(band)
}

/// Human-readable uncertainty report.
fn print_uncertainty(out: &mut dyn Write, u: &UncertaintySummary) -> io::Result<()> {
    writeln!(out)?;
    writeln!(
        out,
        "--- Uncertainty Diagnostics (d={UNCERTAINTY_DIM}, n_boot={}, n_perm={}, alpha={}, seed={}) ---",
        u.n_boot, u.n_perm, u.alpha, u.seed
    )?;
    if let Some(subsample_len) = u.subsample_len {
        writeln!(
            out,
            "Bootstrap block={}; subsample={subsample_len}. Subsampling uses distinct random-origin circular blocks, so it introduces no repeated row indices (original ties remain possible) and no fixed tail is permanently excluded. Reported ranges are raw m-sample quantiles, not calibrated n-sample confidence intervals.",
            u.block_size
        )?;
    } else {
        writeln!(out, "Bootstrap configuration: status=not_requested")?;
    }
    for s in &u.scenarios {
        let (truth_s1, truth_s2) = marginal_truth(s.name);
        writeln!(
            out,
            "  {:>22}: truth(S1 info={truth_s1}, S2 info={truth_s2})",
            s.name
        )?;
        match s.boot {
            ScientificOutcome::Produced(b) => {
                writeln!(
                    out,
                    "{:>26}  bootstrap status=produced I1 q=[{:.3},{:.3}] I2 q=[{:.3},{:.3}] I12 q=[{:.3},{:.3}] (valid I12: {}/{})",
                    "",
                    b.i1.quantile_low, b.i1.quantile_high,
                    b.i2.quantile_low, b.i2.quantile_high,
                    b.i12.quantile_low, b.i12.quantile_high,
                    b.i12.n_valid, u.n_boot,
                )?;
            }
            ScientificOutcome::Abstained { reason } => {
                writeln!(
                    out,
                    "{:>26}  bootstrap status=abstained reason={}",
                    "",
                    reason.as_str()
                )?;
            }
            ScientificOutcome::NotRequested => {
                writeln!(out, "{:>26}  bootstrap status=not_requested", "")?;
            }
        }
        for (label, outcome, truth) in [("S1", s.perm_s1, truth_s1), ("S2", s.perm_s2, truth_s2)] {
            match outcome {
                ScientificOutcome::Produced(result) => {
                    let agreement = if (result.tail_fraction < u.alpha) == truth {
                        "agreement"
                    } else {
                        "disagreement"
                    };
                    writeln!(
                        out,
                        "{:>26}  permutation {label} status=produced tail_fraction={:.4} n_valid={} {agreement}",
                        "", result.tail_fraction, result.n_valid
                    )?;
                }
                ScientificOutcome::Abstained { reason } => {
                    writeln!(
                        out,
                        "{:>26}  permutation {label} status=abstained reason={}",
                        "",
                        reason.as_str()
                    )?;
                }
                ScientificOutcome::NotRequested => {
                    writeln!(out, "{:>26}  permutation {label} status=not_requested", "")?;
                }
            }
        }
    }
    writeln!(
        out,
        "  permutation agreements: {}/{}; bootstrap instabilities: {}",
        u.permutation_agreements, u.permutation_checks, u.bootstrap_instabilities
    )?;
    Ok(())
}

fn write_uncertainty_csv(out: &mut dyn Write, u: &UncertaintySummary) -> Result<(), Exp0Error> {
    const COLUMNS: [&str; 10] = [
        "scenario",
        "diagnostic",
        "status",
        "reason",
        "point",
        "quantile_low",
        "quantile_high",
        "tail_fraction",
        "n_valid",
        "truth_informative",
    ];
    writeln!(out)?;
    writeln!(out, "{}", COLUMNS.join(","))?;
    for scenario in &u.scenarios {
        match scenario.boot {
            ScientificOutcome::Produced(boot) => {
                for (name, triple) in [
                    ("bootstrap_i1", boot.i1),
                    ("bootstrap_i2", boot.i2),
                    ("bootstrap_i12", boot.i12),
                ] {
                    write_uncertainty_csv_record(
                        out,
                        [
                            scenario.name.to_string(),
                            name.to_string(),
                            "produced".to_string(),
                            String::new(),
                            finite_csv_scalar("uncertainty point", triple.point)?,
                            finite_csv_scalar("uncertainty lower quantile", triple.quantile_low)?,
                            finite_csv_scalar("uncertainty upper quantile", triple.quantile_high)?,
                            String::new(),
                            triple.n_valid.to_string(),
                            String::new(),
                        ],
                    )?;
                }
            }
            ScientificOutcome::Abstained { reason } => {
                write_uncertainty_csv_record(
                    out,
                    [
                        scenario.name.to_string(),
                        "bootstrap_all".to_string(),
                        "abstained".to_string(),
                        reason.as_str().to_string(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                    ],
                )?;
            }
            ScientificOutcome::NotRequested => {
                write_uncertainty_csv_record(
                    out,
                    [
                        scenario.name.to_string(),
                        "bootstrap_all".to_string(),
                        "not_requested".to_string(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                        String::new(),
                    ],
                )?;
            }
        }
        let (truth_s1, truth_s2) = marginal_truth(scenario.name);
        for (name, outcome, truth) in [
            ("permutation_s1", scenario.perm_s1, truth_s1),
            ("permutation_s2", scenario.perm_s2, truth_s2),
        ] {
            match outcome {
                ScientificOutcome::Produced(result) => {
                    write_uncertainty_csv_record(
                        out,
                        [
                            scenario.name.to_string(),
                            name.to_string(),
                            "produced".to_string(),
                            String::new(),
                            String::new(),
                            String::new(),
                            String::new(),
                            finite_csv_scalar(
                                "uncertainty permutation tail fraction",
                                result.tail_fraction,
                            )?,
                            result.n_valid.to_string(),
                            truth.to_string(),
                        ],
                    )?;
                }
                ScientificOutcome::Abstained { reason } => {
                    write_uncertainty_csv_record(
                        out,
                        [
                            scenario.name.to_string(),
                            name.to_string(),
                            "abstained".to_string(),
                            reason.as_str().to_string(),
                            String::new(),
                            String::new(),
                            String::new(),
                            String::new(),
                            String::new(),
                            truth.to_string(),
                        ],
                    )?;
                }
                ScientificOutcome::NotRequested => {
                    write_uncertainty_csv_record(
                        out,
                        [
                            scenario.name.to_string(),
                            name.to_string(),
                            "not_requested".to_string(),
                            String::new(),
                            String::new(),
                            String::new(),
                            String::new(),
                            String::new(),
                            String::new(),
                            truth.to_string(),
                        ],
                    )?;
                }
            }
        }
    }
    Ok(())
}

fn write_uncertainty_csv_record(
    out: &mut dyn Write,
    fields: [String; 10],
) -> Result<(), Exp0Error> {
    writeln!(out, "{}", fields.join(","))?;
    Ok(())
}

fn run_case(
    out: &mut dyn Write,
    common: CaseCommon<'_>,
    spec: CaseSpec<'_>,
) -> Result<CaseResult, Exp0Error> {
    let noise_std = 0.05;
    let n = common.n;
    let d = spec.d;
    let seed = spec.seed;
    let (s1, s2, t) = match spec.name {
        "independent_additive" => gen_independent_additive(n, d, noise_std, seed),
        "redundant_copy" => gen_redundant_copy(n, d, noise_std, seed),
        "unique_s1" => gen_unique_s1(n, d, noise_std, seed),
        "xor_like" => gen_xor_like(n, d, noise_std, seed),
        _ => unreachable!("unknown case: {}", spec.name),
    };

    let s1 = MatRef::new(&s1, n, d)?;
    let s2 = MatRef::new(&s2, n, d)?;
    let t = MatRef::new(&t, n, 1)?;

    let (s1z, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error)?;
    let (s2z, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error)?;
    let (tz, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error)?;

    let baseline = compute_metrics(s1z.as_ref(), s2z.as_ref(), tz.as_ref(), common.ksg_cfg)?;
    let diag = compute_diagnostics(
        s1z.as_ref(),
        s2z.as_ref(),
        tz.as_ref(),
        common.ksg_cfg.metric,
    )?;

    if common.csv {
        write_case_csv_row(
            out,
            common.ksg_cfg,
            CaseCsvRow {
                name: spec.name,
                seed: spec.seed,
                projection: ProjectionMethod::None,
                d,
                n,
                project_to: None,
                metrics: baseline,
                diag,
            },
        )?;
    } else {
        print_metrics(out, spec.name, d, spec.seed, baseline)?;
        print_intrinsic_dims(out, diag)?;
    }

    if let Some(dout) = common.hash_project_to {
        if d > dout {
            let p1 = HashProjector::new(d, dout, 0xA11CE_u64 ^ seed)?;
            let p2 = HashProjector::new(d, dout, 0xB22CE_u64 ^ seed)?;

            let s1p = p1.transform(s1z.as_ref())?;
            let s2p = p2.transform(s2z.as_ref())?;

            let s1p = standardize_projected_sample(s1p.as_ref())?;
            let s2p = standardize_projected_sample(s2p.as_ref())?;

            let case_name = format!("{}_hashproj", spec.name);
            report_projection_outcome(
                out,
                common,
                &case_name,
                ProjectionMethod::Hash,
                dout,
                spec.seed,
                s1p.as_ref(),
                s2p.as_ref(),
                tz.as_ref(),
            )?;

            // PCA projection baseline (deterministic; no external deps).
            let (s1p, _) = PcaProjector::fit_transform(s1z.as_ref(), dout)?;
            let (s2p, _) = PcaProjector::fit_transform(s2z.as_ref(), dout)?;

            let s1p = standardize_projected_sample(s1p.as_ref())?;
            let s2p = standardize_projected_sample(s2p.as_ref())?;

            let case_name = format!("{}_pca", spec.name);
            report_projection_outcome(
                out,
                common,
                &case_name,
                ProjectionMethod::Pca,
                dout,
                spec.seed,
                s1p.as_ref(),
                s2p.as_ref(),
                tz.as_ref(),
            )?;
        }
    }
    Ok(CaseResult {
        metrics: baseline,
        diag,
    })
}

/// Re-standardize a projected sample without hiding rank loss.
///
/// Empty CountSketch buckets and constant PCA scores remain explicit zero coordinates so the
/// downstream continuous-support preflight can report and skip the singular projection. Dropping
/// a data- or seed-dependent coordinate here would silently redefine the requested projection.
fn standardize_projected_sample(x: MatRef<'_>) -> pid_core::PidResult<pid_core::MatOwned> {
    let (standardized, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Zero)?;
    Ok(standardized)
}

fn projection_metrics_outcome(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    cfg: &KsgConfig,
) -> Result<ScientificOutcome<Metrics>, Exp0Error> {
    diagnostic_outcome(compute_metrics(s1, s2, target, cfg))
}

#[allow(clippy::too_many_arguments)]
fn report_projection_outcome(
    out: &mut dyn Write,
    common: CaseCommon<'_>,
    case_name: &str,
    projection: ProjectionMethod,
    d: usize,
    seed: u64,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
) -> Result<(), Exp0Error> {
    match projection_metrics_outcome(s1, s2, target, common.ksg_cfg)? {
        ScientificOutcome::Produced(metrics) => {
            let diag = compute_diagnostics(s1, s2, target, common.ksg_cfg.metric)?;
            if common.csv {
                write_case_csv_row(
                    out,
                    common.ksg_cfg,
                    CaseCsvRow {
                        name: case_name,
                        seed,
                        projection,
                        d,
                        n: common.n,
                        project_to: Some(d),
                        metrics,
                        diag,
                    },
                )?;
            } else {
                print_metrics(out, case_name, d, seed, metrics)?;
                print_intrinsic_dims(out, diag)?;
            }
        }
        ScientificOutcome::Abstained { reason } => {
            if common.csv {
                write_case_csv_abstention_row(
                    out,
                    common.ksg_cfg,
                    CaseCsvAbstentionRow {
                        name: case_name,
                        seed,
                        projection,
                        d,
                        n: common.n,
                        project_to: Some(d),
                        reason,
                    },
                )?;
            } else {
                writeln!(
                    out,
                    "{case_name}: status=abstained reason={}",
                    reason.as_str()
                )?;
            }
        }
        ScientificOutcome::NotRequested => {
            return Err(Exp0Error::Pid(PidError::NumericalInstability {
                context: "exp0 projection: attempted estimate became not-requested",
            }));
        }
    }
    Ok(())
}

struct CaseResult {
    metrics: Metrics,
    diag: Diagnostics,
}

#[derive(Debug, Clone, Copy)]
struct Diagnostics {
    id_s1: ScientificOutcome<f64>,
    id_s2: ScientificOutcome<f64>,
    id_t: ScientificOutcome<f64>,
    id_s12: ScientificOutcome<f64>,

    dc_cv_s1: ScientificOutcome<f64>,
    dc_nnr_s1: ScientificOutcome<f64>,
    dc_cv_s2: ScientificOutcome<f64>,
    dc_nnr_s2: ScientificOutcome<f64>,
    dc_cv_s12: ScientificOutcome<f64>,
    dc_nnr_s12: ScientificOutcome<f64>,

    four_point_delta_mean_s1: ScientificOutcome<f64>,
    four_point_delta_mean_s2: ScientificOutcome<f64>,
    four_point_delta_mean_s12: ScientificOutcome<f64>,
    four_point_delta_mean_t: ScientificOutcome<f64>,

    four_point_delta_normalized_mean_s1: ScientificOutcome<f64>,
    four_point_delta_normalized_mean_s2: ScientificOutcome<f64>,
    four_point_delta_normalized_mean_s12: ScientificOutcome<f64>,
    four_point_delta_normalized_mean_t: ScientificOutcome<f64>,
}

fn compute_diagnostics(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    metric: Metric,
) -> Result<Diagnostics, Exp0Error> {
    let cfg = IntrinsicDimConfig::default().with_k(10).with_metric(metric);

    let s12 = concat_horiz(s1, s2)?;
    let id_s1 = finite_diagnostic_scalar(
        intrinsic_dimension_levina_bickel(s1, &cfg),
        "exp0 intrinsic dimension S1 was non-finite",
    )?;
    let id_s2 = finite_diagnostic_scalar(
        intrinsic_dimension_levina_bickel(s2, &cfg),
        "exp0 intrinsic dimension S2 was non-finite",
    )?;
    let id_t = finite_diagnostic_scalar(
        intrinsic_dimension_levina_bickel(t, &cfg),
        "exp0 intrinsic dimension target was non-finite",
    )?;
    let id_s12 = finite_diagnostic_scalar(
        intrinsic_dimension_levina_bickel(s12.as_ref(), &cfg),
        "exp0 intrinsic dimension joint source was non-finite",
    )?;

    let dcfg = DistanceConcentrationConfig::default().with_metric(metric);
    let ds1 = diagnostic_outcome(distance_concentration_stats(s1, &dcfg))?;
    let ds2 = diagnostic_outcome(distance_concentration_stats(s2, &dcfg))?;
    let ds12 = diagnostic_outcome(distance_concentration_stats(s12.as_ref(), &dcfg))?;
    let hcfg = HyperbolicityConfig::default()
        .with_n_samples(500)
        .with_metric(metric)
        .with_seed(42);
    let delta_s1 = diagnostic_outcome(sampled_four_point_delta_summary(s1, &hcfg))?;
    let delta_s2 = diagnostic_outcome(sampled_four_point_delta_summary(s2, &hcfg))?;
    let delta_t = diagnostic_outcome(sampled_four_point_delta_summary(t, &hcfg))?;
    let delta_s12 = diagnostic_outcome(sampled_four_point_delta_summary(s12.as_ref(), &hcfg))?;

    Ok(Diagnostics {
        id_s1,
        id_s2,
        id_t,
        id_s12,
        dc_cv_s1: finite_mapped_outcome(
            ds1,
            |summary| summary.pairwise_cv,
            "exp0 S1 distance-concentration CV was non-finite",
        )?,
        dc_nnr_s1: finite_mapped_outcome(
            ds1,
            |summary| summary.nn_over_pairwise_mean,
            "exp0 S1 nearest-neighbor ratio was non-finite",
        )?,
        dc_cv_s2: finite_mapped_outcome(
            ds2,
            |summary| summary.pairwise_cv,
            "exp0 S2 distance-concentration CV was non-finite",
        )?,
        dc_nnr_s2: finite_mapped_outcome(
            ds2,
            |summary| summary.nn_over_pairwise_mean,
            "exp0 S2 nearest-neighbor ratio was non-finite",
        )?,
        dc_cv_s12: finite_mapped_outcome(
            ds12,
            |summary| summary.pairwise_cv,
            "exp0 joint-source distance-concentration CV was non-finite",
        )?,
        dc_nnr_s12: finite_mapped_outcome(
            ds12,
            |summary| summary.nn_over_pairwise_mean,
            "exp0 joint-source nearest-neighbor ratio was non-finite",
        )?,
        four_point_delta_mean_s1: finite_mapped_outcome(
            delta_s1,
            |summary| summary.mean,
            "exp0 S1 sampled four-point mean was non-finite",
        )?,
        four_point_delta_mean_s2: finite_mapped_outcome(
            delta_s2,
            |summary| summary.mean,
            "exp0 S2 sampled four-point mean was non-finite",
        )?,
        four_point_delta_mean_s12: finite_mapped_outcome(
            delta_s12,
            |summary| summary.mean,
            "exp0 joint-source sampled four-point mean was non-finite",
        )?,
        four_point_delta_mean_t: finite_mapped_outcome(
            delta_t,
            |summary| summary.mean,
            "exp0 target sampled four-point mean was non-finite",
        )?,
        four_point_delta_normalized_mean_s1: normalized_four_point_delta(
            delta_s1,
            "exp0 S1 normalized four-point mean was non-finite",
        )?,
        four_point_delta_normalized_mean_s2: normalized_four_point_delta(
            delta_s2,
            "exp0 S2 normalized four-point mean was non-finite",
        )?,
        four_point_delta_normalized_mean_s12: normalized_four_point_delta(
            delta_s12,
            "exp0 joint-source normalized four-point mean was non-finite",
        )?,
        four_point_delta_normalized_mean_t: normalized_four_point_delta(
            delta_t,
            "exp0 target normalized four-point mean was non-finite",
        )?,
    })
}

fn normalized_four_point_delta(
    outcome: ScientificOutcome<SampledFourPointDeltaSummary>,
    context: &'static str,
) -> Result<ScientificOutcome<f64>, Exp0Error> {
    match outcome {
        ScientificOutcome::Produced(summary) => match summary.normalized_mean {
            Some(value) if value.is_finite() => Ok(ScientificOutcome::Produced(value)),
            Some(_) => Err(Exp0Error::Pid(PidError::NumericalInstability { context })),
            None => Ok(ScientificOutcome::Abstained {
                reason: AbstentionReason::ZeroDiameter,
            }),
        },
        ScientificOutcome::Abstained { reason } => Ok(ScientificOutcome::Abstained { reason }),
        ScientificOutcome::NotRequested => Ok(ScientificOutcome::NotRequested),
    }
}

fn print_intrinsic_dims(out: &mut dyn Write, d: Diagnostics) -> io::Result<()> {
    let scalar = |outcome: ScientificOutcome<f64>, precision: usize| match outcome {
        ScientificOutcome::Produced(value) => format!("{value:.precision$}"),
        ScientificOutcome::Abstained { reason } => {
            format!("abstained({})", reason.as_str())
        }
        ScientificOutcome::NotRequested => "not_requested".to_string(),
    };
    writeln!(
        out,
        "{:>20} {:>7} | ID(s1)={} ID(s2)={} ID(t)={} ID(s1,s2)={}",
        "",
        "",
        scalar(d.id_s1, 2),
        scalar(d.id_s2, 2),
        scalar(d.id_t, 2),
        scalar(d.id_s12, 2),
    )?;
    writeln!(
        out,
        "{:>20} {:>7} | DCcv(s1)={} nn/mean={} | DCcv(s2)={} nn/mean={} | DCcv(s1,s2)={} nn/mean={}",
        "",
        "",
        scalar(d.dc_cv_s1, 3),
        scalar(d.dc_nnr_s1, 3),
        scalar(d.dc_cv_s2, 3),
        scalar(d.dc_nnr_s2, 3),
        scalar(d.dc_cv_s12, 3),
        scalar(d.dc_nnr_s12, 3),
    )?;

    writeln!(
        out,
        "{:>20} {:>7} | sampled_4pt_delta_rel(s1)={} | (s2)={} | (s1,s2)={} | (t)={}",
        "",
        "",
        scalar(d.four_point_delta_normalized_mean_s1, 3),
        scalar(d.four_point_delta_normalized_mean_s2, 3),
        scalar(d.four_point_delta_normalized_mean_s12, 3),
        scalar(d.four_point_delta_normalized_mean_t, 3),
    )?;
    Ok(())
}

fn run_gaussian_channel_strong_dependence_sweep(
    out: &mut dyn Write,
    csv: bool,
    n: usize,
    ksg_cfg: &KsgConfig,
    seed: u64,
) -> Result<(), Exp0Error> {
    // Strong-dependence sweep (separate axis from "high d"):
    // X ~ N(0,1), Y = X + σN, N~N(0,1), so analytic MI is:
    // I(X;Y) = 0.5 ln(1 + 1/σ²).
    let sigmas = [1.0, 0.3, 0.1, 0.03, 0.01];

    let mut rng = Rng64::new(seed);
    let mut x = Vec::with_capacity(n);
    let mut noise = Vec::with_capacity(n);
    for _ in 0..n {
        x.push(rng.normal());
        noise.push(rng.normal());
    }

    let xref = MatRef::new(&x, n, 1)?;
    let (xstd, _) = Standardizer::fit_transform(xref, ConstantColumnPolicy::Error)?;

    if !csv {
        writeln!(out, "Strong-dependence sweep (Gaussian channel, 1D)")?;
        writeln!(out, "n={n}, k={}, metric={:?}", ksg_cfg.k, ksg_cfg.metric)?;
    }
    for &sigma in &sigmas {
        let mut y = Vec::with_capacity(n);
        for (&xi, &ni) in x.iter().zip(noise.iter()) {
            y.push(xi + sigma * ni);
        }

        let yref = MatRef::new(&y, n, 1)?;
        let (ystd, _) = Standardizer::fit_transform(yref, ConstantColumnPolicy::Error)?;

        let mi_hat = ksg_mi(xstd.as_ref(), ystd.as_ref(), ksg_cfg)?;
        let mi_true = gaussian_channel_mi(sigma);
        if csv {
            write_gaussian_csv_row(out, sigma, n, ksg_cfg, mi_hat, mi_true)?;
        } else {
            writeln!(
                out,
                "  sigma={:<7.3}  MI_hat={:>8.3}  MI_true={:>8.3}  err={:>8.3}",
                sigma,
                mi_hat,
                mi_true,
                mi_hat - mi_true
            )?;
        }
    }
    if !csv {
        writeln!(out)?;
    }
    Ok(())
}

fn gaussian_channel_mi(sigma: f64) -> f64 {
    debug_assert!(sigma.is_finite());
    debug_assert!(sigma > 0.0);
    0.5 * (1.0 + 1.0 / (sigma * sigma)).ln()
}

// ---------------------------------------------------------------------------
// Analytic Gaussian MI ground truth
// ---------------------------------------------------------------------------
//
// System (jointly Gaussian, with closed-form MI terms used by this gate):
//   S1, S2 ~ N(0,1) independent (unit variance, uncorrelated),
//   T = a*S1[0] + b*S2[0] + c*Z,  Z ~ N(0,1) independent.
// Only the first coordinate of each source carries signal; the remaining d-1
// coordinates are independent N(0,1) noise (so the band exercises multivariate
// sources without changing the analytic MI, which depends only on the signal
// coordinate). Because (S1,S2,T) is jointly Gaussian and S1 ⟂ S2:
//
//   Var(T)            = a^2 + b^2 + c^2
//   Var(T | S1,S2)    = c^2
//   I(S1,S2; T) = 0.5 * ln(Var(T) / Var(T|S1,S2)) = 0.5 * ln((a^2+b^2+c^2)/c^2)
//   I(S1; T)    = 0.5 * ln(Var(T) / Var(T|S1))    = 0.5 * ln((a^2+b^2+c^2)/(b^2+c^2))
//   I(S2; T)    = 0.5 * ln((a^2+b^2+c^2)/(a^2+c^2))
// (Cover & Thomas, "Elements of Information Theory", §8.5: differential entropy
// of a Gaussian; conditional variances from the standard Gaussian regression.)
//
// This closed form adjudicates only the three measure-independent MI terms. It is not a
// shared-exclusions atom oracle, so Exp0 keeps atom-measure and atom-estimator validation separate
// and explicitly unadjudicated/blocked.
#[derive(Debug, Clone, Copy)]
struct GaussianMiTruth {
    i1: f64,
    i2: f64,
    i12: f64,
}

/// Closed-form MI terms for the jointly-Gaussian system `T = a*S1[0] + b*S2[0] + c*Z`.
/// All values are in nats.
fn gaussian_mi_truth(a: f64, b: f64, c: f64) -> GaussianMiTruth {
    let var_t = a * a + b * b + c * c;
    let i12 = 0.5 * (var_t / (c * c)).ln();
    let i1 = 0.5 * (var_t / (b * b + c * c)).ln();
    let i2 = 0.5 * (var_t / (a * a + c * c)).ln();
    GaussianMiTruth { i1, i2, i12 }
}

/// Generate the jointly-Gaussian MI-check system into `(s1, s2, t)` row-major buffers.
/// Signal lives only in coordinate 0; coordinates 1..d are independent N(0,1) noise.
fn gen_gaussian_mi_system(
    n: usize,
    d: usize,
    a: f64,
    b: f64,
    c: f64,
    seed: u64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = Rng64::new(seed);
    let mut s1 = vec![0.0; n * d];
    let mut s2 = vec![0.0; n * d];
    let mut t = vec![0.0; n];
    for i in 0..n {
        for j in 0..d {
            s1[i * d + j] = rng.normal();
            s2[i * d + j] = rng.normal();
        }
        t[i] = a * s1[i * d] + b * s2[i * d] + c * rng.normal();
    }
    (s1, s2, t)
}

/// Result of the analytic Gaussian MI accuracy check.
#[derive(Debug, Clone, Copy)]
struct GaussianMiCheck {
    /// Number of MI-term comparisons performed (measure-independent ground truth).
    mi_checks: usize,
    /// Number of those within the scale-aware tolerance.
    mi_passes: usize,
}

/// Run the analytic Gaussian MI accuracy check and compare all three MI terms against the
/// Cover–Thomas closed form. No atom oracle runs here.
#[allow(clippy::too_many_arguments)]
fn run_gaussian_mi_check(
    out: &mut dyn Write,
    csv: bool,
    n: usize,
    ksg_cfg: &KsgConfig,
    a: f64,
    b: f64,
    c: f64,
    seed: u64,
) -> Result<GaussianMiCheck, Exp0Error> {
    // d=1: pure signal, no noise dimensions to dilute the Chebyshev neighbour structure.
    // This is a curated, analytically checked low-dimensional regime, so the closed-form MI terms
    // are recovered within tolerance and GO is legitimately attainable.
    let d = 1usize;
    let truth = gaussian_mi_truth(a, b, c);

    let (s1, s2, t) = gen_gaussian_mi_system(n, d, a, b, c, seed);
    let s1 = MatRef::new(&s1, n, d)?;
    let s2 = MatRef::new(&s2, n, d)?;
    let t = MatRef::new(&t, n, 1)?;
    let (s1z, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error)?;
    let (s2z, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error)?;
    let (tz, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error)?;

    // Estimate only what the gate and report need: the three measure-independent MI terms.
    // Computing these directly, rather than via `compute_metrics`, avoids all redundancy methods
    // and keeps the n=4000 gate (and its unit test) cheap. All terms use the same KSG config with
    // `NegativeHandling::Allow`.
    let i1 = ksg_mi(s1z.as_ref(), tz.as_ref(), ksg_cfg)?;
    let i2 = ksg_mi(s2z.as_ref(), tz.as_ref(), ksg_cfg)?;
    let i12 = ksg_mi_concat_xy(s1z.as_ref(), s2z.as_ref(), tz.as_ref(), ksg_cfg)?;

    // Compare the measure-independent MI terms with a scale-aware tolerance (the same
    // noise model used elsewhere in the gate); these are the quantitative pass/fail items.
    let mut mi_checks = 0usize;
    let mut mi_passes = 0usize;
    for (hat, truth_val) in [(i1, truth.i1), (i2, truth.i2), (i12, truth.i12)] {
        mi_checks += 1;
        if (hat - truth_val).abs() <= estimate_tol(truth_val) {
            mi_passes += 1;
        }
    }

    if csv {
        // Row of the gating band's labeled CSV table (header written by `strict_band_gate`):
        // the only enforced gate's measured-vs-analytic MI terms must appear in the
        // machine-readable output, not just the human-readable report.
        writeln!(
            out,
            "band_gauss_d1,{a},{b},{c},{d},{n},{i1:.6},{:.6},{i2:.6},{:.6},{i12:.6},{:.6},{mi_passes},{mi_checks}",
            truth.i1, truth.i2, truth.i12
        )?;
    }

    if !csv {
        writeln!(
            out,
            "Gaussian MI check (system T = {a}*S1 + {b}*S2 + {c}*Z, d={d}, n={n})"
        )?;
        writeln!(
            out,
            "  MI terms (nats): I1 hat/true = {:.3}/{:.3}  I2 = {:.3}/{:.3}  I12 = {:.3}/{:.3}  [{}/{} within tol]",
            i1, truth.i1, i2, truth.i2, i12, truth.i12, mi_passes, mi_checks
        )?;
        writeln!(
            out,
            "  Atom validation: measure={ATOM_MEASURE_VALIDATION_STATUS} estimator={ATOM_ESTIMATOR_VALIDATION_STATUS}"
        )?;
    }

    Ok(GaussianMiCheck {
        mi_checks,
        mi_passes,
    })
}

#[derive(Clone, Copy)]
struct Metrics {
    mi_s1_t: f64,
    mi_s2_t: f64,
    mi_s1s2_t: f64,
    ci: f64,
    r_bar: ScientificOutcome<f64>,
    v_bar: ScientificOutcome<f64>,
    red_ehrlich: ScientificOutcome<f64>,
    red_local_min: ScientificOutcome<f64>,
    red_disjunction: ScientificOutcome<f64>,
    syn_ehrlich: ScientificOutcome<f64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum GateScope {
    HighDimensionalMiCoherence,
    CuratedAnalyticMiRecovery,
}

impl GateScope {
    fn as_str(self) -> &'static str {
        match self {
            Self::HighDimensionalMiCoherence => "high_dimensional_mi_coherence",
            Self::CuratedAnalyticMiRecovery => "curated_analytic_mi_recovery",
        }
    }

    fn verdict_field(self) -> &'static str {
        match self {
            Self::HighDimensionalMiCoherence => "mi_coherence_verdict",
            Self::CuratedAnalyticMiRecovery => "analytic_mi_recovery_verdict",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum GateVerdict {
    Go,
    Pivot,
    NoGo,
}

impl GateVerdict {
    fn as_str(self) -> &'static str {
        match self {
            Self::Go => "GO",
            Self::Pivot => "PIVOT",
            Self::NoGo => "NO-GO",
        }
    }

    fn code(self) -> usize {
        match self {
            Self::Go => 0,
            Self::Pivot => 1,
            Self::NoGo => 2,
        }
    }
}

const ATOM_MEASURE_VALIDATION_STATUS: &str = "not_adjudicated";
const ATOM_MEASURE_VALIDATION_REASON: &str = "no_matching_shared_exclusions_measure_oracle_ran";
const ATOM_ESTIMATOR_VALIDATION_STATUS: &str = "blocked";
const ATOM_ESTIMATOR_VALIDATION_REASON: &str =
    "measure_validation_not_adjudicated_and_application_validation_not_established";

#[derive(Debug, Clone)]
struct GateSummary {
    scope: GateScope,
    case_results: usize,
    monotonicity_violations: usize,
    normalized_invariant_violations: usize,
    analytic_mi_recovery_failures: usize,
    geometry_warnings: usize,
    geometry_abstentions: usize,
    // Uncertainty-quantification contribution (all zero / false when UQ disabled,
    // which keeps the default verdict and metric counts unchanged).
    uncertainty_enabled: bool,
    permutation_checks: usize,
    permutation_agreements: usize,
    bootstrap_instabilities: usize,
}

impl Default for GateSummary {
    fn default() -> Self {
        Self::high_dimensional()
    }
}

impl GateSummary {
    fn high_dimensional() -> Self {
        Self {
            scope: GateScope::HighDimensionalMiCoherence,
            case_results: 0,
            monotonicity_violations: 0,
            normalized_invariant_violations: 0,
            analytic_mi_recovery_failures: 0,
            geometry_warnings: 0,
            geometry_abstentions: 0,
            uncertainty_enabled: false,
            permutation_checks: 0,
            permutation_agreements: 0,
            bootstrap_instabilities: 0,
        }
    }

    fn curated_analytic_mi() -> Self {
        Self {
            scope: GateScope::CuratedAnalyticMiRecovery,
            ..Self::high_dimensional()
        }
    }

    fn observe_case(&mut self, name: &str, metrics: Metrics, diag: Diagnostics) {
        self.case_results += 1;

        // Monotonicity of MI under adding a source: I(S1,S2;T) >= I(Si;T). For the
        // joint-vs-marginal case this IS the conditional-MI nonnegativity condition
        // (I(S1;T|S2) = I(S1,S2;T) - I(S2;T) >= 0 ⇔ I(S1,S2;T) >= I(S2;T)), so a
        // separate "CMI nonnegativity" counter would be identical by construction —
        // it is reported once, here.
        //
        // These are NOISY kNN estimates (SE ~0.01–0.05 nats), not exact identities, so we
        // compare with a scale-aware tolerance: an exact-equality tolerance (1e-9) counts
        // pure estimator noise as a violation on essentially every case.
        if metrics.mi_s1s2_t + estimate_tol(metrics.mi_s1_t) < metrics.mi_s1_t {
            self.monotonicity_violations += 1;
        }
        if metrics.mi_s1s2_t + estimate_tol(metrics.mi_s2_t) < metrics.mi_s2_t {
            self.monotonicity_violations += 1;
        }

        // r̄/v̄ are ratios with the joint MI as denominator. At the estimator noise floor
        // (e.g. a null system where all three MI estimates are near zero) they are explicitly
        // undefined, not floating-point sentinels, and do not count as bound violations.
        // Only test the [0,2] bound when the joint MI is resolvable, and with the same
        // scale-aware tolerance. For n=2, v̄ = 2 − r̄, so the two checks are equivalent.
        const INVARIANT_MI_FLOOR: f64 = 0.05;
        if metrics.mi_s1s2_t >= INVARIANT_MI_FLOOR {
            match (metrics.r_bar, metrics.v_bar) {
                (ScientificOutcome::Produced(r_bar), ScientificOutcome::Produced(v_bar))
                    if bounded_degree(r_bar, 0.0, 2.0, estimate_tol(r_bar))
                        && bounded_degree(v_bar, 0.0, 2.0, estimate_tol(v_bar)) => {}
                _ => self.normalized_invariant_violations += 1,
            }
        }

        if name == "independent_additive" {
            let (id_warning, id_abstained) = geometry_check(diag.id_s1, |value| value > 20.0);
            let (dc_warning, dc_abstained) = geometry_check(diag.dc_cv_s1, |value| value < 0.1);
            let (delta_warning, delta_abstained) =
                geometry_check(diag.four_point_delta_normalized_mean_s1, |value| {
                    value < 0.1
                });
            if id_warning || dc_warning || delta_warning {
                self.geometry_warnings += 1;
            }
            if id_abstained || dc_abstained || delta_abstained {
                self.geometry_abstentions += 1;
            }
        }
    }

    /// Fold the analytic Gaussian MI-term check into the gate. Each system counts as a
    /// case result; each MI term that disagrees with its Cover–Thomas closed form beyond the
    /// scale-aware tolerance counts as an invariant violation, so a quantitative analytic
    /// disagreement blocks GO on the curated band. (Only the measure-independent MI terms are
    /// gated; atom validation is a separate, explicitly unadjudicated status.)
    fn observe_gaussian_mi_check(&mut self, c: &GaussianMiCheck) {
        self.case_results += 1;
        self.analytic_mi_recovery_failures += c.mi_checks - c.mi_passes;
    }

    /// Absorb the derived gate checks from an opt-in uncertainty run.
    fn observe_uncertainty(&mut self, u: &UncertaintySummary) {
        self.uncertainty_enabled = u.enabled;
        self.permutation_checks = u.permutation_checks;
        self.permutation_agreements = u.permutation_agreements;
        self.bootstrap_instabilities = u.bootstrap_instabilities;
    }

    /// Total uncertainty-side violations: permutation disagreements with the
    /// preregistered ground-truth marginal-significance table, plus MI-vector
    /// bootstrap instabilities at the most favourable dimension. Zero when UQ
    /// is disabled.
    fn uncertainty_violations(&self) -> usize {
        let perm_disagreements = self.permutation_checks - self.permutation_agreements;
        perm_disagreements + self.bootstrap_instabilities
    }

    fn verdict(&self) -> GateVerdict {
        if self.case_results == 0 {
            return GateVerdict::NoGo;
        }
        match self.scope {
            GateScope::CuratedAnalyticMiRecovery => {
                if self.analytic_mi_recovery_failures == 0 {
                    GateVerdict::Go
                } else {
                    GateVerdict::NoGo
                }
            }
            GateScope::HighDimensionalMiCoherence => {
                if self.monotonicity_violations > 0
                    || self.normalized_invariant_violations > 0
                    || self.uncertainty_violations() > 0
                {
                    GateVerdict::NoGo
                } else {
                    GateVerdict::Go
                }
            }
        }
    }

    /// Descriptive geometry triage, deliberately separate from the scientific MI verdict.
    /// Uncalibrated geometry heuristics may motivate review but cannot establish estimator
    /// validity or failure (`grandplan.md` §7.9).
    fn geometry_disposition(&self) -> GateVerdict {
        if self.geometry_warnings > 0 || self.geometry_abstentions > 0 {
            GateVerdict::Pivot
        } else {
            GateVerdict::Go
        }
    }

    fn status(&self) -> &'static str {
        self.verdict().as_str()
    }

    fn status_code(&self) -> usize {
        self.verdict().code()
    }

    fn print(&self, out: &mut dyn Write) -> io::Result<()> {
        writeln!(out, "Verdict Scope: {}", self.scope.as_str())?;
        writeln!(out, "Case Results: {}", self.case_results)?;
        match self.scope {
            GateScope::HighDimensionalMiCoherence => {
                writeln!(out, "Geometry Warnings: {}", self.geometry_warnings)?;
                writeln!(out, "Geometry Abstentions: {}", self.geometry_abstentions)?;
                writeln!(
                    out,
                    "Geometry Disposition (descriptive, non-gating): {}",
                    self.geometry_disposition().as_str()
                )?;
                writeln!(
                    out,
                    "Monotonicity Violations (= CMI nonnegativity): {}",
                    self.monotonicity_violations
                )?;
                writeln!(
                    out,
                    "Normalized Invariant Bound Violations: {}",
                    self.normalized_invariant_violations
                )?;
                if self.uncertainty_enabled {
                    writeln!(
                        out,
                        "Permutation Marginal-Significance Agreements: {}/{}",
                        self.permutation_agreements, self.permutation_checks
                    )?;
                    writeln!(
                        out,
                        "Bootstrap MI-Vector Instabilities: {}",
                        self.bootstrap_instabilities
                    )?;
                }
                writeln!(out, "MI/Coherence Verdict: {}", self.status())?
            }
            GateScope::CuratedAnalyticMiRecovery => {
                writeln!(
                    out,
                    "Analytic MI Recovery Failures: {}",
                    self.analytic_mi_recovery_failures
                )?;
                writeln!(out, "Analytic MI Recovery Verdict: {}", self.status())?
            }
        }
        writeln!(
            out,
            "Atom Measure Validation: {ATOM_MEASURE_VALIDATION_STATUS} reason={ATOM_MEASURE_VALIDATION_REASON}"
        )?;
        writeln!(
            out,
            "Atom Estimator Validation: {ATOM_ESTIMATOR_VALIDATION_STATUS} reason={ATOM_ESTIMATOR_VALIDATION_REASON}"
        )?;
        Ok(())
    }
}

fn geometry_check(
    outcome: ScientificOutcome<f64>,
    warns: impl FnOnce(f64) -> bool,
) -> (bool, bool) {
    match outcome {
        ScientificOutcome::Produced(value) => (warns(value), false),
        ScientificOutcome::Abstained { .. } | ScientificOutcome::NotRequested => (false, true),
    }
}

fn write_gate_csv_summary(out: &mut dyn Write, gates: &GateSummary) -> io::Result<()> {
    writeln!(out)?;
    match gates.scope {
        GateScope::HighDimensionalMiCoherence => {
            writeln!(
                out,
                "verdict_scope,mi_coherence_verdict,case_results,monotonicity_violations,normalized_invariant_violations,geometry_warnings,geometry_abstentions,geometry_disposition,atom_measure_validation_status,atom_measure_validation_reason,atom_estimator_validation_status,atom_estimator_validation_reason"
            )?;
            writeln!(
                out,
                "{},{},{},{},{},{},{},{},{},{},{},{}",
                gates.scope.as_str(),
                gates.status(),
                gates.case_results,
                gates.monotonicity_violations,
                gates.normalized_invariant_violations,
                gates.geometry_warnings,
                gates.geometry_abstentions,
                gates.geometry_disposition().as_str(),
                ATOM_MEASURE_VALIDATION_STATUS,
                ATOM_MEASURE_VALIDATION_REASON,
                ATOM_ESTIMATOR_VALIDATION_STATUS,
                ATOM_ESTIMATOR_VALIDATION_REASON,
            )
        }
        GateScope::CuratedAnalyticMiRecovery => {
            writeln!(
                out,
                "verdict_scope,analytic_mi_recovery_verdict,case_results,analytic_mi_recovery_failures,atom_measure_validation_status,atom_measure_validation_reason,atom_estimator_validation_status,atom_estimator_validation_reason"
            )?;
            writeln!(
                out,
                "{},{},{},{},{},{},{},{}",
                gates.scope.as_str(),
                gates.status(),
                gates.case_results,
                gates.analytic_mi_recovery_failures,
                ATOM_MEASURE_VALIDATION_STATUS,
                ATOM_MEASURE_VALIDATION_REASON,
                ATOM_ESTIMATOR_VALIDATION_STATUS,
                ATOM_ESTIMATOR_VALIDATION_REASON,
            )
        }
    }
}

fn bounded_degree(value: f64, lo: f64, hi: f64, tol: f64) -> bool {
    value.is_finite() && value >= lo - tol && value <= hi + tol
}

/// Tolerance for declaring a *genuine* violation when comparing noisy kNN MI estimates (or
/// degrees derived from them). KSG estimates carry finite-sample noise on the order of
/// 0.01–0.05 nats, so comparing them with an exact-identity tolerance (1e-9) reports estimator
/// noise as a violation. A violation counts only when it exceeds the larger of an absolute
/// noise floor and a relative fraction of the quantity's own magnitude. Reserve 1e-9 for exact
/// algebraic identities (e.g. the PID atom-sum reconstruction), not for cross-estimate checks.
fn estimate_tol(scale: f64) -> f64 {
    const ABS_TOL: f64 = 0.05;
    const REL_TOL: f64 = 0.1;
    ABS_TOL.max(REL_TOL * scale.abs())
}

fn optional_synergy_outcome(
    mi_s1_t: f64,
    mi_s2_t: f64,
    mi_s1s2_t: f64,
    redundancy: ScientificOutcome<f64>,
) -> ScientificOutcome<f64> {
    match redundancy {
        ScientificOutcome::Produced(redundancy) => {
            Pid2Result::from_estimate(Pid2Estimate::new(mi_s1_t, mi_s2_t, mi_s1s2_t, redundancy))
                .map(|pid| ScientificOutcome::Produced(pid.synergy))
                .unwrap_or(ScientificOutcome::Abstained {
                    reason: AbstentionReason::NumericalInstability,
                })
        }
        ScientificOutcome::Abstained { reason } => ScientificOutcome::Abstained { reason },
        ScientificOutcome::NotRequested => ScientificOutcome::NotRequested,
    }
}

fn compute_metrics(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    ksg_cfg: &KsgConfig,
) -> pid_core::PidResult<Metrics> {
    let mi_s1_t = ksg_mi(s1, t, ksg_cfg)?;
    let mi_s2_t = ksg_mi(s2, t, ksg_cfg)?;
    let mi_s1s2_t = ksg_mi_concat_xy(s1, s2, t, ksg_cfg)?;
    let ci = co_information_pairwise(s1, s2, t, ksg_cfg)?;

    let red_ehrlich = optional_scalar_estimate_outcome(isx_redundancy(
        s1,
        s2,
        t,
        &IsxConfig {
            k: ksg_cfg.k,
            metric: ksg_cfg.metric,
            tie_epsilon: ksg_cfg.tie_epsilon,
            method: IsxMethod::EhrlichKsg,
            support_contract: ksg_cfg.support_contract,
        },
    ))?;

    let red_local_min = optional_scalar_estimate_outcome(isx_redundancy(
        s1,
        s2,
        t,
        &IsxConfig {
            k: ksg_cfg.k,
            metric: ksg_cfg.metric,
            tie_epsilon: ksg_cfg.tie_epsilon,
            method: IsxMethod::LocalMinKsg,
            support_contract: ksg_cfg.support_contract,
        },
    ))?;

    let red_disjunction = optional_scalar_estimate_outcome(isx_redundancy(
        s1,
        s2,
        t,
        &IsxConfig {
            k: ksg_cfg.k,
            metric: ksg_cfg.metric,
            tie_epsilon: ksg_cfg.tie_epsilon,
            method: IsxMethod::DisjunctionFromLocalMi,
            support_contract: ksg_cfg.support_contract,
        },
    ))?;

    let r_bar = normalized_invariant_outcome(&average_degree_of_redundancy(
        &[mi_s1_t, mi_s2_t],
        mi_s1s2_t,
    ))?;
    let v_bar = normalized_invariant_outcome(&average_degree_of_vulnerability(
        mi_s1s2_t,
        &[mi_s2_t, mi_s1_t],
    ))?;
    let syn_ehrlich = optional_synergy_outcome(mi_s1_t, mi_s2_t, mi_s1s2_t, red_ehrlich);
    for (context, value) in [
        ("exp0 I(S1;T)", mi_s1_t),
        ("exp0 I(S2;T)", mi_s2_t),
        ("exp0 I(S1,S2;T)", mi_s1s2_t),
        ("exp0 co-information", ci),
    ] {
        if !value.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
    }

    Ok(Metrics {
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        ci,
        r_bar,
        v_bar,
        red_ehrlich,
        red_local_min,
        red_disjunction,
        syn_ehrlich,
    })
}

fn print_metrics(
    out: &mut dyn Write,
    name: &str,
    d: usize,
    seed: u64,
    m: Metrics,
) -> io::Result<()> {
    let format_outcome = |outcome: ScientificOutcome<f64>, precision: usize| match outcome {
        ScientificOutcome::Produced(value) => format!("{value:.precision$}"),
        ScientificOutcome::Abstained { reason } => {
            format!("abstained({})", reason.as_str())
        }
        ScientificOutcome::NotRequested => "not_requested".to_string(),
    };
    let r_bar = format_outcome(m.r_bar, 2);
    let v_bar = format_outcome(m.v_bar, 2);
    let red_ehrlich = format_outcome(m.red_ehrlich, 3);
    let red_local_min = format_outcome(m.red_local_min, 3);
    let red_disjunction = format_outcome(m.red_disjunction, 3);
    let syn_ehrlich = format_outcome(m.syn_ehrlich, 3);
    writeln!(
        out,
        "{name:>20} d={d:<4} seed={seed:<10} | I1={:>7.3} I2={:>7.3} I12={:>7.3} CoI={:>7.3} | r_bar={r_bar} v_bar={v_bar} | Red(ehr)={red_ehrlich} Red(local)={red_local_min} Syn(ehr)={syn_ehrlich} | Red(disj)={red_disjunction}",
        m.mi_s1_t,
        m.mi_s2_t,
        m.mi_s1s2_t,
        m.ci,
    )?;
    Ok(())
}

fn write_case_csv_header(out: &mut dyn Write) -> io::Result<()> {
    writeln!(out, "{}", case_csv_columns().join(","))
}

fn case_csv_columns() -> Vec<String> {
    let mut columns = [
        "case_name",
        "seed",
        "projection",
        "d",
        "n",
        "k",
        "metric",
        "project_to",
        "case_status",
        "case_reason",
        "mi_s1_t",
        "mi_s2_t",
        "mi_s1s2_t",
        "ci",
    ]
    .into_iter()
    .map(str::to_string)
    .collect::<Vec<_>>();
    append_outcome_column_names(&mut columns, "r_bar");
    append_outcome_column_names(&mut columns, "v_bar");
    append_outcome_column_names(&mut columns, "red_ehrlich");
    append_outcome_column_names(&mut columns, "red_local_min");
    append_outcome_column_names(&mut columns, "red_disjunction");
    append_outcome_column_names(&mut columns, "syn_ehrlich");
    for name in [
        "id_s1",
        "id_s2",
        "id_t",
        "id_s12",
        "dc_cv_s1",
        "dc_nnratio_s1",
        "dc_cv_s2",
        "dc_nnratio_s2",
        "dc_cv_s12",
        "dc_nnratio_s12",
        "four_point_delta_mean_s1",
        "four_point_delta_mean_s2",
        "four_point_delta_mean_s12",
        "four_point_delta_mean_t",
        "four_point_delta_normalized_mean_s1",
        "four_point_delta_normalized_mean_s2",
        "four_point_delta_normalized_mean_s12",
        "four_point_delta_normalized_mean_t",
    ] {
        append_outcome_column_names(&mut columns, name);
    }
    columns
}

fn append_outcome_column_names(columns: &mut Vec<String>, name: &str) {
    columns.push(name.to_string());
    columns.push(format!("{name}_status"));
    columns.push(format!("{name}_reason"));
}

#[derive(Clone, Copy)]
enum ProjectionMethod {
    None,
    Hash,
    Pca,
}

impl ProjectionMethod {
    fn as_str(self) -> &'static str {
        match self {
            ProjectionMethod::None => "none",
            ProjectionMethod::Hash => "hash",
            ProjectionMethod::Pca => "pca",
        }
    }
}

struct CaseCsvRow<'a> {
    name: &'a str,
    seed: u64,
    projection: ProjectionMethod,
    d: usize,
    n: usize,
    project_to: Option<usize>,
    metrics: Metrics,
    diag: Diagnostics,
}

struct CaseCsvAbstentionRow<'a> {
    name: &'a str,
    seed: u64,
    projection: ProjectionMethod,
    d: usize,
    n: usize,
    project_to: Option<usize>,
    reason: AbstentionReason,
}

fn write_case_csv_row(
    out: &mut dyn Write,
    ksg_cfg: &KsgConfig,
    row: CaseCsvRow<'_>,
) -> Result<(), Exp0Error> {
    let project_to = row.project_to.map_or_else(String::new, |v| v.to_string());
    let mut fields = vec![
        row.name.to_string(),
        row.seed.to_string(),
        row.projection.as_str().to_string(),
        row.d.to_string(),
        row.n.to_string(),
        ksg_cfg.k.to_string(),
        format!("{:?}", ksg_cfg.metric),
        project_to,
        "produced".to_string(),
        String::new(),
        finite_csv_scalar("mi_s1_t", row.metrics.mi_s1_t)?,
        finite_csv_scalar("mi_s2_t", row.metrics.mi_s2_t)?,
        finite_csv_scalar("mi_s1s2_t", row.metrics.mi_s1s2_t)?,
        finite_csv_scalar("ci", row.metrics.ci)?,
    ];
    append_outcome_csv_fields(&mut fields, row.metrics.r_bar)?;
    append_outcome_csv_fields(&mut fields, row.metrics.v_bar)?;
    append_outcome_csv_fields(&mut fields, row.metrics.red_ehrlich)?;
    append_outcome_csv_fields(&mut fields, row.metrics.red_local_min)?;
    append_outcome_csv_fields(&mut fields, row.metrics.red_disjunction)?;
    append_outcome_csv_fields(&mut fields, row.metrics.syn_ehrlich)?;
    for outcome in [
        row.diag.id_s1,
        row.diag.id_s2,
        row.diag.id_t,
        row.diag.id_s12,
        row.diag.dc_cv_s1,
        row.diag.dc_nnr_s1,
        row.diag.dc_cv_s2,
        row.diag.dc_nnr_s2,
        row.diag.dc_cv_s12,
        row.diag.dc_nnr_s12,
        row.diag.four_point_delta_mean_s1,
        row.diag.four_point_delta_mean_s2,
        row.diag.four_point_delta_mean_s12,
        row.diag.four_point_delta_mean_t,
        row.diag.four_point_delta_normalized_mean_s1,
        row.diag.four_point_delta_normalized_mean_s2,
        row.diag.four_point_delta_normalized_mean_s12,
        row.diag.four_point_delta_normalized_mean_t,
    ] {
        append_outcome_csv_fields(&mut fields, outcome)?;
    }
    let expected = case_csv_columns().len();
    if fields.len() != expected {
        return Err(Exp0Error::Config(format!(
            "internal CSV schema mismatch: expected {expected} fields, built {}",
            fields.len()
        )));
    }
    writeln!(out, "{}", fields.join(","))?;
    Ok(())
}

fn write_case_csv_abstention_row(
    out: &mut dyn Write,
    ksg_cfg: &KsgConfig,
    row: CaseCsvAbstentionRow<'_>,
) -> Result<(), Exp0Error> {
    let columns = case_csv_columns();
    let mut fields = vec![
        row.name.to_string(),
        row.seed.to_string(),
        row.projection.as_str().to_string(),
        row.d.to_string(),
        row.n.to_string(),
        ksg_cfg.k.to_string(),
        format!("{:?}", ksg_cfg.metric),
        row.project_to.map_or_else(String::new, |v| v.to_string()),
        "abstained".to_string(),
        row.reason.as_str().to_string(),
    ];
    fields.resize(columns.len(), String::new());
    writeln!(out, "{}", fields.join(","))?;
    Ok(())
}

fn finite_csv_scalar(name: &'static str, value: f64) -> Result<String, Exp0Error> {
    if !value.is_finite() {
        return Err(Exp0Error::Pid(PidError::NumericalInstability {
            context: name,
        }));
    }
    Ok(format!("{value:.15e}"))
}

fn append_outcome_csv_fields(
    fields: &mut Vec<String>,
    outcome: ScientificOutcome<f64>,
) -> Result<(), Exp0Error> {
    match outcome {
        ScientificOutcome::Produced(value) => {
            fields.push(finite_csv_scalar("exp0 CSV produced outcome", value)?);
            fields.push("produced".to_string());
            fields.push(String::new());
        }
        ScientificOutcome::Abstained { reason } => {
            fields.push(String::new());
            fields.push("abstained".to_string());
            fields.push(reason.as_str().to_string());
        }
        ScientificOutcome::NotRequested => {
            fields.push(String::new());
            fields.push("not_requested".to_string());
            fields.push(String::new());
        }
    }
    Ok(())
}

fn write_gaussian_csv_header(out: &mut dyn Write) -> io::Result<()> {
    writeln!(out, "sigma,n,k,metric,mi_hat,mi_true,err")
}

fn write_gaussian_csv_row(
    out: &mut dyn Write,
    sigma: f64,
    n: usize,
    ksg_cfg: &KsgConfig,
    mi_hat: f64,
    mi_true: f64,
) -> io::Result<()> {
    writeln!(
        out,
        "{sigma:.15e},{n},{},{:?},{mi_hat:.15e},{mi_true:.15e},{:.15e}",
        ksg_cfg.k,
        ksg_cfg.metric,
        mi_hat - mi_true
    )
}

fn gen_independent_additive(
    n: usize,
    d: usize,
    noise_std: f64,
    seed: u64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = Rng64::new(seed);
    let mut s1 = vec![0.0; n * d];
    let mut s2 = vec![0.0; n * d];
    let mut t = vec![0.0; n];

    for i in 0..n {
        for j in 0..d {
            s1[i * d + j] = rng.normal();
            s2[i * d + j] = rng.normal();
        }
        t[i] = s1[i * d] + s2[i * d] + noise_std * rng.normal();
    }
    (s1, s2, t)
}

fn gen_redundant_copy(
    n: usize,
    d: usize,
    noise_std: f64,
    seed: u64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = Rng64::new(seed);
    let mut s1 = vec![0.0; n * d];
    let mut s2 = vec![0.0; n * d];
    let mut t = vec![0.0; n];

    for i in 0..n {
        let base = rng.normal();
        t[i] = base;
        s1[i * d] = base + noise_std * rng.normal();
        s2[i * d] = base + noise_std * rng.normal();
        for j in 1..d {
            s1[i * d + j] = rng.normal();
            s2[i * d + j] = rng.normal();
        }
    }
    (s1, s2, t)
}

fn gen_unique_s1(n: usize, d: usize, noise_std: f64, seed: u64) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = Rng64::new(seed);
    let mut s1 = vec![0.0; n * d];
    let mut s2 = vec![0.0; n * d];
    let mut t = vec![0.0; n];

    for i in 0..n {
        for j in 0..d {
            s1[i * d + j] = rng.normal();
            s2[i * d + j] = rng.normal();
        }
        t[i] = s1[i * d] + noise_std * rng.normal();
    }
    (s1, s2, t)
}

fn gen_xor_like(n: usize, d: usize, noise_std: f64, seed: u64) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = Rng64::new(seed);
    let mut s1 = vec![0.0; n * d];
    let mut s2 = vec![0.0; n * d];
    let mut t = vec![0.0; n];

    for i in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        s1[i * d] = a;
        s2[i * d] = b;

        // XOR-like: target depends on the interaction sign(a*b) rather than either alone.
        let sign = if a * b > 0.0 { 1.0 } else { -1.0 };
        t[i] = sign + noise_std * rng.normal();

        for j in 1..d {
            s1[i * d + j] = rng.normal();
            s2[i * d + j] = rng.normal();
        }
    }
    (s1, s2, t)
}

#[derive(Clone)]
struct Rng64 {
    state: u64,
}

impl Rng64 {
    fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    fn next_u64(&mut self) -> u64 {
        // xorshift64*
        let mut x = self.state;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.state = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }

    fn next_f64(&mut self) -> f64 {
        let u = self.next_u64() >> 11; // 53 bits
        (u as f64) * (1.0 / ((1u64 << 53) as f64))
    }

    fn normal(&mut self) -> f64 {
        // Box–Muller requires an open lower endpoint; redraw zero rather than truncating the
        // Gaussian tail with an arbitrary clamp.
        let u1 = loop {
            let draw = self.next_f64();
            if draw > 0.0 {
                break draw;
            }
        };
        let u2 = self.next_f64();
        let r = (-2.0 * u1.ln()).sqrt();
        let theta = 2.0 * std::f64::consts::PI * u2;
        r * theta.cos()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn seed_schedule_capacity_overflow_returns_config_error_without_panicking() {
        let result = std::panic::catch_unwind(|| make_seeds(usize::MAX));

        assert!(matches!(result, Ok(Err(Exp0Error::Config(_)))));
    }

    #[test]
    fn support_incompatible_projection_is_typed_abstention() {
        let s1_data = [
            0.0, 0.03, 0.0, 0.17, 0.0, 0.31, 0.0, 0.52, 0.0, 0.76, 0.0, 1.01, 0.0, 1.29, 0.0, 1.62,
        ];
        let s2_data = [
            1.73, 0.11, 1.41, 0.23, 1.16, 0.37, 0.88, 0.49, 0.63, 0.68, 0.39, 0.91, 0.21, 1.14,
            0.07, 1.39,
        ];
        let target_data = [0.12, 0.29, 0.48, 0.71, 0.97, 1.22, 1.51, 1.85];
        let s1 = MatRef::new(&s1_data, 8, 2).unwrap();
        let s2 = MatRef::new(&s2_data, 8, 2).unwrap();
        let target = MatRef::new(&target_data, 8, 1).unwrap();
        let s1 = standardize_projected_sample(s1).unwrap();
        let s2 = standardize_projected_sample(s2).unwrap();
        let target = standardize_projected_sample(target).unwrap();
        assert_eq!(
            s1.as_ref().ncols(),
            2,
            "the constant coordinate is retained"
        );
        assert!(s1.as_ref().row(0)[0].abs() == 0.0);
        let cfg = KsgConfig::assume_regular_full_dimensional();
        let result =
            projection_metrics_outcome(s1.as_ref(), s2.as_ref(), target.as_ref(), &cfg).unwrap();

        assert!(matches!(
            result,
            ScientificOutcome::Abstained {
                reason: AbstentionReason::ObservedContinuousSampleIncompatibility
            }
        ));

        let mut csv = Vec::new();
        write_case_csv_abstention_row(
            &mut csv,
            &cfg,
            CaseCsvAbstentionRow {
                name: "synthetic_hashproj",
                seed: 7,
                projection: ProjectionMethod::Hash,
                d: 2,
                n: 8,
                project_to: Some(2),
                reason: AbstentionReason::ObservedContinuousSampleIncompatibility,
            },
        )
        .unwrap();
        let csv = String::from_utf8(csv).unwrap();
        let fields = csv.trim_end().split(',').collect::<Vec<_>>();
        assert_eq!(fields[8], "abstained");
        assert_eq!(fields[9], "observed_continuous_sample_incompatibility");
        assert!(fields[10..].iter().all(|field| field.is_empty()));
    }

    #[test]
    fn optional_ambiguous_shell_is_a_typed_abstention() {
        let outcome = diagnostic_outcome::<Metrics>(Err(PidError::AmbiguousKthNeighborShell {
            context: "synthetic optional projection",
            query_index: 0,
            k: 3,
            radius: 1.0,
            interior_count: 2,
            boundary_count: 2,
        }))
        .unwrap();

        assert!(matches!(
            outcome,
            ScientificOutcome::Abstained {
                reason: AbstentionReason::AmbiguousKthNeighborShell
            }
        ));
    }

    #[test]
    fn non_finite_produced_diagnostic_is_rejected() {
        let result = finite_mapped_outcome(
            ScientificOutcome::Produced(()),
            |()| f64::NAN,
            "synthetic non-finite diagnostic",
        );

        assert!(matches!(
            result,
            Err(Exp0Error::Pid(PidError::NumericalInstability {
                context: "synthetic non-finite diagnostic"
            }))
        ));
    }

    #[test]
    fn coherent_resampling_failure_counts_as_a_gate_instability() {
        let mut instabilities = 0;
        let retained = retain_resampling_or_count_instability::<()>(
            Err(PidError::NumericalInstability {
                context: "synthetic failed resample",
            }),
            &mut instabilities,
        )
        .unwrap();

        assert_eq!(
            retained,
            ScientificOutcome::Abstained {
                reason: AbstentionReason::NumericalInstability
            }
        );
        assert_eq!(instabilities, 1);

        let invalid_config = retain_resampling_or_count_instability::<()>(
            Err(PidError::InvalidConfig {
                context: "synthetic bad config",
                message: "bad",
            }),
            &mut instabilities,
        );
        assert!(matches!(invalid_config, Err(Exp0Error::Pid(_))));
        assert_eq!(instabilities, 1);
    }

    fn temp_path(name: &str) -> String {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir()
            .join(format!("pid-exp0-{name}-{stamp}"))
            .display()
            .to_string()
    }

    fn args_with_artifacts(summary_json: String, runlog: String) -> Args {
        Args {
            csv: false,
            seeds: 1,
            strict_gate: false,
            strict_band: false,
            summary_json: Some(summary_json),
            runlog: Some(runlog),
            uncertainty: UncertaintyConfig::default(),
        }
    }

    #[test]
    fn artifact_paths_reject_exact_and_normalized_aliases_before_writing() {
        let path = PathBuf::from(temp_path("artifact-alias"));
        let normalized_alias = path
            .parent()
            .unwrap()
            .join("alias-parent")
            .join("..")
            .join(path.file_name().unwrap());

        let exact = args_with_artifacts(path.display().to_string(), path.display().to_string());
        let normalized = args_with_artifacts(
            path.display().to_string(),
            normalized_alias.display().to_string(),
        );

        assert!(matches!(
            validate_artifact_paths(&exact),
            Err(Exp0Error::Config(_))
        ));
        assert!(matches!(
            validate_artifact_paths(&normalized),
            Err(Exp0Error::Config(_))
        ));
    }

    #[test]
    fn artifact_paths_reject_missing_case_only_aliases_on_case_insensitive_filesystems() {
        let parent = PathBuf::from(temp_path("artifact-case-insensitive-parent"));
        std::fs::create_dir(&parent).unwrap();
        if !filesystem_is_case_insensitive(&parent).unwrap() {
            std::fs::remove_dir(parent).unwrap();
            return;
        }

        let summary = parent.join("case-only-artifact.json");
        let runlog = parent.join("CASE-ONLY-ARTIFACT.JSON");
        assert!(!summary.exists());
        assert!(!runlog.exists());
        let args = args_with_artifacts(summary.display().to_string(), runlog.display().to_string());

        assert!(matches!(
            validate_artifact_paths(&args),
            Err(Exp0Error::Config(_))
        ));
        assert!(!summary.exists());
        assert!(!runlog.exists());
        assert!(std::fs::read_dir(&parent).unwrap().next().is_none());

        std::fs::remove_dir(parent).unwrap();
    }

    #[test]
    fn artifact_paths_reject_hard_link_aliases() {
        let original = PathBuf::from(temp_path("artifact-hardlink-original"));
        let alias = PathBuf::from(temp_path("artifact-hardlink-alias"));
        std::fs::write(&original, b"existing artifact").unwrap();
        std::fs::hard_link(&original, &alias).unwrap();
        let args = args_with_artifacts(original.display().to_string(), alias.display().to_string());

        assert!(matches!(
            validate_artifact_paths(&args),
            Err(Exp0Error::Config(_))
        ));

        let _ = std::fs::remove_file(alias);
        let _ = std::fs::remove_file(original);
    }

    #[cfg(unix)]
    #[test]
    fn artifact_paths_reject_symbolic_link_aliases() {
        use std::os::unix::fs::symlink;

        let original = PathBuf::from(temp_path("artifact-symlink-original"));
        let alias = PathBuf::from(temp_path("artifact-symlink-alias"));
        std::fs::write(&original, b"existing artifact").unwrap();
        symlink(&original, &alias).unwrap();
        let args = args_with_artifacts(original.display().to_string(), alias.display().to_string());

        assert!(matches!(
            validate_artifact_paths(&args),
            Err(Exp0Error::Config(_))
        ));

        let _ = std::fs::remove_file(alias);
        let _ = std::fs::remove_file(original);
    }

    #[cfg(unix)]
    #[test]
    fn artifact_paths_reject_missing_destinations_through_symlinked_parents() {
        use std::os::unix::fs::symlink;

        let real_parent = PathBuf::from(temp_path("artifact-real-parent"));
        let alias_parent = PathBuf::from(temp_path("artifact-parent-alias"));
        std::fs::create_dir(&real_parent).unwrap();
        symlink(&real_parent, &alias_parent).unwrap();
        let original = real_parent.join("not-created-yet.jsonl");
        let alias = alias_parent.join("not-created-yet.jsonl");
        let args = args_with_artifacts(original.display().to_string(), alias.display().to_string());

        assert!(matches!(
            validate_artifact_paths(&args),
            Err(Exp0Error::Config(_))
        ));

        let _ = std::fs::remove_file(alias_parent);
        let _ = std::fs::remove_dir(real_parent);
    }

    #[cfg(unix)]
    #[test]
    fn artifact_paths_reject_dangling_symbolic_link_aliases() {
        use std::os::unix::fs::symlink;

        let original = PathBuf::from(temp_path("artifact-dangling-target"));
        let alias = PathBuf::from(temp_path("artifact-dangling-alias"));
        symlink(&original, &alias).unwrap();
        let args = args_with_artifacts(original.display().to_string(), alias.display().to_string());

        assert!(matches!(
            validate_artifact_paths(&args),
            Err(Exp0Error::Config(_))
        ));

        let _ = std::fs::remove_file(alias);
    }

    #[test]
    fn strict_gate_failure_is_recorded_in_summary_and_runlog() {
        let summary_path = temp_path("strict-failure-summary.json");
        let runlog_path = temp_path("strict-failure-runlog.jsonl");
        let default_gates = GateSummary {
            case_results: 1,
            ..Default::default()
        };
        let strict_band = GateSummary {
            case_results: 1,
            analytic_mi_recovery_failures: 1,
            ..GateSummary::curated_analytic_mi()
        };
        let dims = [10usize];
        let seeds = [42u64];
        write_summary_json(
            &summary_path,
            &default_gates,
            500,
            3,
            &dims,
            &seeds,
            Some(64),
            None,
            Some(&strict_band),
            true,
        )
        .unwrap();
        write_exp0_runlog(
            &runlog_path,
            Some(&summary_path),
            &default_gates,
            Exp0RunConfig {
                n: 500,
                k: 3,
                dims: &dims,
                seeds: &seeds,
                hash_project_to: Some(64),
                uncertainty: UncertaintyConfig::default(),
            },
            None,
            Some(&strict_band),
            true,
        )
        .unwrap();

        let summary_json: serde_json::Value =
            serde_json::from_slice(&std::fs::read(&summary_path).unwrap()).unwrap();
        assert_eq!(summary_json["status"], "NO-GO");
        assert_eq!(summary_json["status_scope"], "curated_analytic_mi_recovery");
        assert_eq!(
            summary_json["verdict_scope"],
            "high_dimensional_mi_coherence"
        );
        assert_eq!(summary_json["default_sweep_status"], "GO");
        assert_eq!(summary_json["strict_band"]["status"], "NO-GO");
        assert_eq!(summary_json["strict_gate_enforced"], true);
        assert_eq!(summary_json["strict_gate_passed"], false);

        let events = pid_runlog::read_events_from_path(&runlog_path).unwrap();
        let validation = pid_runlog::validate_events(&events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        assert!(events.iter().any(|event| matches!(
            event,
            RunLogEvent::PidMetric { name, .. }
                if name == "exp0.strict_band.analytic_mi_recovery_verdict_code"
        )));
        assert!(events.iter().any(|event| matches!(
            event,
            RunLogEvent::ErrorLogged {
                recoverable: false,
                ..
            }
        )));
        let run_started_metadata = events.iter().find_map(|event| match event {
            RunLogEvent::RunStarted { metadata, .. } => Some(metadata),
            _ => None,
        });
        let run_started_metadata = run_started_metadata.expect("run-started metadata");
        assert_eq!(
            run_started_metadata.get("status").map(String::as_str),
            Some("NO-GO")
        );
        assert_eq!(
            run_started_metadata.get("status_scope").map(String::as_str),
            Some("curated_analytic_mi_recovery")
        );
        assert_eq!(
            run_started_metadata
                .get("verdict_scope")
                .map(String::as_str),
            Some("high_dimensional_mi_coherence")
        );
        let artifact_metadata = events.iter().find_map(|event| match event {
            RunLogEvent::ArtifactLogged { metadata, .. } => Some(metadata),
            _ => None,
        });
        let artifact_metadata = artifact_metadata.expect("summary artifact metadata");
        assert_eq!(
            artifact_metadata.get("status").map(String::as_str),
            Some("NO-GO")
        );
        assert_eq!(
            artifact_metadata.get("status_scope").map(String::as_str),
            Some("curated_analytic_mi_recovery")
        );
        assert_eq!(
            artifact_metadata
                .get("atom_measure_validation")
                .map(String::as_str),
            Some("not_adjudicated")
        );
        assert_eq!(
            artifact_metadata
                .get("atom_estimator_validation")
                .map(String::as_str),
            Some("blocked")
        );
        assert!(matches!(
            events.last(),
            Some(RunLogEvent::RunEnded {
                status: RunStatus::Failed,
                ..
            })
        ));

        let _ = std::fs::remove_file(summary_path);
        let _ = std::fs::remove_file(runlog_path);
    }

    #[test]
    fn runlog_config_hash_commits_to_uncertainty_parameters() {
        let first_path = temp_path("uncertainty-config-first.jsonl");
        let second_path = temp_path("uncertainty-config-second.jsonl");
        let gates = GateSummary {
            case_results: 1,
            ..Default::default()
        };
        let write = |path: &str, seed: u64| {
            let uncertainty_config = UncertaintyConfig {
                n_boot: 0,
                n_perm: 1,
                block_size: 1,
                alpha: 0.05,
                seed,
            };
            let uncertainty = UncertaintySummary {
                enabled: true,
                n_boot: 0,
                n_perm: 1,
                block_size: 1,
                subsample_len: None,
                alpha: 0.05,
                seed,
                ..Default::default()
            };
            write_exp0_runlog(
                path,
                None,
                &gates,
                Exp0RunConfig {
                    n: 500,
                    k: 3,
                    dims: &[10],
                    seeds: &[42],
                    hash_project_to: Some(64),
                    uncertainty: uncertainty_config,
                },
                Some(&uncertainty),
                None,
                false,
            )
            .unwrap();
        };
        write(&first_path, 7);
        write(&second_path, 8);

        let config_hash = |path: &str| {
            pid_runlog::read_events_from_path(path)
                .unwrap()
                .into_iter()
                .find_map(|event| match event {
                    RunLogEvent::RunStarted { config_hash, .. } => Some(config_hash),
                    _ => None,
                })
                .unwrap()
        };
        assert_ne!(config_hash(&first_path), config_hash(&second_path));

        let _ = std::fs::remove_file(first_path);
        let _ = std::fs::remove_file(second_path);
    }

    #[test]
    fn exp0_runlog_export_is_valid_and_summarizable() {
        let summary_path = temp_path("summary.json");
        let runlog_path = temp_path("runlog.jsonl");
        let gates = GateSummary {
            case_results: 1,
            ..Default::default()
        };
        let dims = [10usize, 64, 256];
        let seeds = [42u64];
        write_summary_json(
            &summary_path,
            &gates,
            500,
            3,
            &dims,
            &seeds,
            Some(64),
            None,
            None,
            false,
        )
        .unwrap();
        let summary_json: serde_json::Value =
            serde_json::from_slice(&std::fs::read(&summary_path).unwrap()).unwrap();
        assert_eq!(
            summary_json["verdict_scope"],
            "high_dimensional_mi_coherence"
        );
        assert_eq!(summary_json["mi_coherence_verdict"], "GO");
        assert!(summary_json.get("analytic_mi_recovery_verdict").is_none());
        assert!(summary_json.get("analytic_mi_recovery_failures").is_none());
        assert_eq!(
            summary_json["atom_validation"]["measure"]["status"],
            "not_adjudicated"
        );
        assert_eq!(
            summary_json["atom_validation"]["estimator"]["status"],
            "blocked"
        );
        assert!(summary_json.get("red_zero_checks").is_none());
        write_exp0_runlog(
            &runlog_path,
            Some(&summary_path),
            &gates,
            Exp0RunConfig {
                n: 500,
                k: 3,
                dims: &dims,
                seeds: &seeds,
                hash_project_to: Some(64),
                uncertainty: UncertaintyConfig::default(),
            },
            None,
            None,
            false,
        )
        .unwrap();

        let events = pid_runlog::read_events_from_path(&runlog_path).unwrap();
        let validation = pid_runlog::validate_events(&events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        let summary = pid_runlog::summarize_events(&events).unwrap();
        assert_eq!(summary.run_id.as_deref(), Some("exp0-rust-quick-run"));
        assert_eq!(summary.pid_metrics, 6);
        assert_eq!(summary.pid_metric_events, 6);
        assert_eq!(summary.artifacts, 1);
        assert_eq!(summary.errors, 0);
        assert!(!events.iter().any(|event| matches!(
            event,
            RunLogEvent::PidMetric { name, .. }
                if name.contains("red_zero") || name.contains("atom")
        )));

        let _ = std::fs::remove_file(summary_path);
        let _ = std::fs::remove_file(runlog_path);
    }

    #[test]
    fn curated_scope_serializers_omit_high_dimensional_counter_placeholders() {
        let summary_path = temp_path("curated-summary.json");
        let runlog_path = temp_path("curated-runlog.jsonl");
        let gates = GateSummary {
            case_results: 3,
            analytic_mi_recovery_failures: 1,
            ..GateSummary::curated_analytic_mi()
        };
        write_summary_json(
            &summary_path,
            &gates,
            4_000,
            3,
            &[1],
            &[42],
            None,
            None,
            None,
            false,
        )
        .unwrap();
        let summary_json: serde_json::Value =
            serde_json::from_slice(&std::fs::read(&summary_path).unwrap()).unwrap();
        assert_eq!(
            summary_json["verdict_scope"],
            "curated_analytic_mi_recovery"
        );
        assert_eq!(summary_json["analytic_mi_recovery_verdict"], "NO-GO");
        assert_eq!(summary_json["analytic_mi_recovery_failures"], 1);
        assert!(summary_json.get("mi_coherence_verdict").is_none());
        assert!(summary_json.get("monotonicity_violations").is_none());
        assert!(summary_json
            .get("normalized_invariant_violations")
            .is_none());
        assert!(summary_json.get("geometry_warnings").is_none());

        let mut human = Vec::new();
        gates.print(&mut human).unwrap();
        let human = String::from_utf8(human).unwrap();
        assert!(human.contains("Analytic MI Recovery Failures: 1"));
        assert!(!human.contains("Geometry Warnings"));
        assert!(!human.contains("Monotonicity Violations"));

        let mut csv = Vec::new();
        write_gate_csv_summary(&mut csv, &gates).unwrap();
        let csv = String::from_utf8(csv).unwrap();
        assert!(csv.contains("analytic_mi_recovery_verdict"));
        assert!(!csv.contains("mi_coherence_verdict"));
        assert!(!csv.contains("normalized_invariant_violations"));

        write_exp0_runlog(
            &runlog_path,
            None,
            &gates,
            Exp0RunConfig {
                n: 4_000,
                k: 3,
                dims: &[1],
                seeds: &[42],
                hash_project_to: None,
                uncertainty: UncertaintyConfig::default(),
            },
            None,
            None,
            false,
        )
        .unwrap();
        let events = pid_runlog::read_events_from_path(&runlog_path).unwrap();
        let validation = pid_runlog::validate_events(&events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        let metric_names = events
            .iter()
            .filter_map(|event| match event {
                RunLogEvent::PidMetric { name, .. } => Some(name.as_str()),
                _ => None,
            })
            .collect::<Vec<_>>();
        assert_eq!(metric_names.len(), 3);
        assert!(metric_names.contains(&"exp0.analytic_mi_recovery_failures"));
        assert!(metric_names.contains(&"exp0.analytic_mi_recovery_verdict_code"));
        assert!(!metric_names
            .iter()
            .any(|name| name.contains("monotonicity") || name.contains("mi_coherence")));
        let run_started_metadata = events.iter().find_map(|event| match event {
            RunLogEvent::RunStarted { metadata, .. } => Some(metadata),
            _ => None,
        });
        let run_started_metadata = run_started_metadata.expect("run_started event");
        assert_eq!(
            run_started_metadata
                .get("analytic_mi_recovery_verdict")
                .map(String::as_str),
            Some("NO-GO")
        );
        assert!(!run_started_metadata.contains_key("mi_coherence_verdict"));

        let _ = std::fs::remove_file(summary_path);
        let _ = std::fs::remove_file(runlog_path);
    }

    #[test]
    fn exp0_runlog_records_non_go_status_as_recoverable_error() {
        let runlog_path = temp_path("nogate.jsonl");
        let gates = GateSummary {
            case_results: 0,
            ..Default::default()
        };
        write_exp0_runlog(
            &runlog_path,
            None,
            &gates,
            Exp0RunConfig {
                n: 500,
                k: 3,
                dims: &[10],
                seeds: &[42],
                hash_project_to: Some(64),
                uncertainty: UncertaintyConfig::default(),
            },
            None,
            None,
            false,
        )
        .unwrap();

        let events = pid_runlog::read_events_from_path(&runlog_path).unwrap();
        let validation = pid_runlog::validate_events(&events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        let summary = pid_runlog::summarize_events(&events).unwrap();
        assert_eq!(summary.errors, 1);
        assert!(events.iter().any(|event| matches!(
            event,
            RunLogEvent::ErrorLogged {
                recoverable: true,
                ..
            }
        )));

        let _ = std::fs::remove_file(runlog_path);
    }

    fn ksg_cfg_for_test() -> KsgConfig {
        KsgConfig::assume_regular_full_dimensional()
            .with_k(3)
            .with_metric(Metric::Chebyshev)
            .with_tie_epsilon(0.0)
            // Mirrors the config `run()` builds: Allow, per the PID-identity convention.
            .with_negative_handling(NegativeHandling::Allow)
            .with_support_contract(SupportContract::assume_regular_full_dimensional())
    }

    fn metrics_with_invariants(joint_mi: f64, r_bar: Option<f64>, v_bar: Option<f64>) -> Metrics {
        let invariant = |value| match value {
            Some(value) => ScientificOutcome::Produced(value),
            None => ScientificOutcome::Abstained {
                reason: AbstentionReason::NonPositiveDenominator,
            },
        };
        Metrics {
            mi_s1_t: 0.0,
            mi_s2_t: 0.0,
            mi_s1s2_t: joint_mi,
            ci: 0.0,
            r_bar: invariant(r_bar),
            v_bar: invariant(v_bar),
            red_ehrlich: ScientificOutcome::Produced(0.0),
            red_local_min: ScientificOutcome::Produced(0.0),
            red_disjunction: ScientificOutcome::Produced(0.0),
            syn_ehrlich: ScientificOutcome::Produced(joint_mi),
        }
    }

    fn quiet_diagnostics() -> Diagnostics {
        let produced = ScientificOutcome::Produced;
        Diagnostics {
            id_s1: produced(1.0),
            id_s2: produced(1.0),
            id_t: produced(1.0),
            id_s12: produced(2.0),
            dc_cv_s1: produced(1.0),
            dc_nnr_s1: produced(1.0),
            dc_cv_s2: produced(1.0),
            dc_nnr_s2: produced(1.0),
            dc_cv_s12: produced(1.0),
            dc_nnr_s12: produced(1.0),
            four_point_delta_mean_s1: produced(1.0),
            four_point_delta_mean_s2: produced(1.0),
            four_point_delta_mean_s12: produced(1.0),
            four_point_delta_mean_t: produced(1.0),
            four_point_delta_normalized_mean_s1: produced(1.0),
            four_point_delta_normalized_mean_s2: produced(1.0),
            four_point_delta_normalized_mean_s12: produced(1.0),
            four_point_delta_normalized_mean_t: produced(1.0),
        }
    }

    #[test]
    fn undefined_normalized_invariants_are_explicit_and_gate_by_resolution() {
        let undefined_low = metrics_with_invariants(0.0, None, None);
        let mut low_information_gate = GateSummary::default();
        low_information_gate.observe_case("null", undefined_low, quiet_diagnostics());
        assert_eq!(low_information_gate.normalized_invariant_violations, 0);

        let mut resolved_gate = GateSummary::default();
        resolved_gate.observe_case(
            "resolvable",
            metrics_with_invariants(0.5, None, None),
            quiet_diagnostics(),
        );
        assert_eq!(resolved_gate.normalized_invariant_violations, 1);

        let mut human = Vec::new();
        print_metrics(&mut human, "null", 1, 7, undefined_low).unwrap();
        let human = String::from_utf8(human).unwrap();
        assert!(human.contains("r_bar=abstained(non_positive_denominator)"));
        assert!(human.contains("v_bar=abstained(non_positive_denominator)"));

        let mut csv = Vec::new();
        write_case_csv_row(
            &mut csv,
            &ksg_cfg_for_test(),
            CaseCsvRow {
                name: "null",
                seed: 7,
                projection: ProjectionMethod::None,
                d: 1,
                n: 8,
                project_to: None,
                metrics: undefined_low,
                diag: quiet_diagnostics(),
            },
        )
        .unwrap();
        let csv = String::from_utf8(csv).unwrap();
        let fields: Vec<&str> = csv.trim_end().split(',').collect();
        let columns = case_csv_columns();
        assert_eq!(fields.len(), columns.len());
        let index = |name: &str| columns.iter().position(|column| column == name).unwrap();
        assert_eq!(fields[index("r_bar")], "");
        assert_eq!(fields[index("r_bar_status")], "abstained");
        assert_eq!(fields[index("r_bar_reason")], "non_positive_denominator");
        assert_eq!(fields[index("v_bar")], "");
        assert!(!csv.contains("NaN"));
    }

    #[test]
    fn positive_independent_additive_shared_exclusions_redundancy_cannot_fail_mi_gate() {
        let mut metrics = metrics_with_invariants(0.8, Some(1.0), Some(1.0));
        metrics.red_ehrlich = ScientificOutcome::Produced(0.25);
        metrics.syn_ehrlich = ScientificOutcome::Produced(1.05);

        let mut gate = GateSummary::high_dimensional();
        gate.observe_case("independent_additive", metrics, quiet_diagnostics());

        assert_eq!(gate.verdict(), GateVerdict::Go);
        assert_eq!(ATOM_MEASURE_VALIDATION_STATUS, "not_adjudicated");
        assert_eq!(ATOM_ESTIMATOR_VALIDATION_STATUS, "blocked");
    }

    #[test]
    fn atom_estimator_instability_is_typed_and_non_gating() {
        let atom = optional_scalar_estimate_outcome(Err(PidError::NumericalInstability {
            context: "synthetic atom-estimator instability",
        }))
        .unwrap();
        assert_eq!(
            atom,
            ScientificOutcome::Abstained {
                reason: AbstentionReason::NumericalInstability,
            }
        );
        assert_eq!(optional_synergy_outcome(0.2, 0.1, 0.8, atom), atom);

        let mut metrics = metrics_with_invariants(0.8, Some(1.0), Some(1.0));
        metrics.red_ehrlich = atom;
        metrics.red_local_min = atom;
        metrics.red_disjunction = atom;
        metrics.syn_ehrlich = atom;

        let mut gate = GateSummary::high_dimensional();
        gate.observe_case("independent_additive", metrics, quiet_diagnostics());

        assert_eq!(gate.verdict(), GateVerdict::Go);

        let mut csv = Vec::new();
        write_case_csv_row(
            &mut csv,
            &ksg_cfg_for_test(),
            CaseCsvRow {
                name: "independent_additive",
                seed: 7,
                projection: ProjectionMethod::None,
                d: 1,
                n: 8,
                project_to: None,
                metrics,
                diag: quiet_diagnostics(),
            },
        )
        .unwrap();
        let csv = String::from_utf8(csv).unwrap();
        let fields = csv.trim_end().split(',').collect::<Vec<_>>();
        let columns = case_csv_columns();
        let index = |name: &str| columns.iter().position(|column| column == name).unwrap();
        assert_eq!(fields[index("red_ehrlich")], "");
        assert_eq!(fields[index("red_ehrlich_status")], "abstained");
        assert_eq!(fields[index("red_ehrlich_reason")], "numerical_instability");
        assert_eq!(fields[index("syn_ehrlich_status")], "abstained");
    }

    #[test]
    fn high_dimensional_mi_monotonicity_failure_is_no_go() {
        let mut metrics = metrics_with_invariants(0.5, Some(1.0), Some(1.0));
        metrics.mi_s1_t = 1.0;
        metrics.mi_s2_t = 0.2;

        let mut gate = GateSummary::high_dimensional();
        gate.observe_case("redundant_copy", metrics, quiet_diagnostics());

        assert_eq!(gate.monotonicity_violations, 1);
        assert_eq!(gate.verdict(), GateVerdict::NoGo);
        assert_eq!(gate.scope, GateScope::HighDimensionalMiCoherence);
    }

    #[test]
    fn geometry_warning_is_reported_as_non_gating_pivot() {
        let metrics = metrics_with_invariants(0.8, Some(1.0), Some(1.0));
        let mut diagnostics = quiet_diagnostics();
        diagnostics.id_s1 = ScientificOutcome::Produced(25.0);

        let mut gate = GateSummary::high_dimensional();
        gate.observe_case("independent_additive", metrics, diagnostics);

        assert_eq!(gate.verdict(), GateVerdict::Go);
        assert_eq!(gate.geometry_disposition(), GateVerdict::Pivot);
        assert_eq!(gate.geometry_warnings, 1);
    }

    #[test]
    fn abstained_csv_outcomes_have_reason_and_no_numeric_placeholder() {
        let mut diagnostics = quiet_diagnostics();
        diagnostics.id_t = ScientificOutcome::Abstained {
            reason: AbstentionReason::AmbiguousKthNeighborShell,
        };
        let metrics = metrics_with_invariants(0.0, None, None);
        let mut csv = Vec::new();
        write_case_csv_row(
            &mut csv,
            &ksg_cfg_for_test(),
            CaseCsvRow {
                name: "typed_abstention",
                seed: 7,
                projection: ProjectionMethod::None,
                d: 1,
                n: 8,
                project_to: None,
                metrics,
                diag: diagnostics,
            },
        )
        .unwrap();

        let csv = String::from_utf8(csv).unwrap();
        let fields = csv.trim_end().split(',').collect::<Vec<_>>();
        let columns = case_csv_columns();
        let index = |name: &str| columns.iter().position(|column| column == name).unwrap();
        assert_eq!(fields[index("id_t")], "");
        assert_eq!(fields[index("id_t_status")], "abstained");
        assert_eq!(fields[index("id_t_reason")], "ambiguous_kth_neighbor_shell");
        assert!(!csv.contains("NaN"));
        assert!(!csv.contains("nan"));
    }

    #[test]
    fn abstained_uncertainty_json_omits_numeric_value_fields() {
        let summary = UncertaintySummary {
            enabled: true,
            n_boot: 1,
            n_perm: 1,
            block_size: 1,
            subsample_len: Some(4),
            alpha: 0.05,
            seed: 7,
            scenarios: vec![ScenarioUncertainty {
                name: "independent_additive",
                boot: ScientificOutcome::Abstained {
                    reason: AbstentionReason::NumericalInstability,
                },
                perm_s1: ScientificOutcome::Abstained {
                    reason: AbstentionReason::IncompleteResamplingDistribution,
                },
                perm_s2: ScientificOutcome::NotRequested,
            }],
            permutation_checks: 1,
            permutation_agreements: 0,
            bootstrap_instabilities: 1,
        };

        let json = uncertainty_json(&summary).unwrap();
        let bootstrap = &json["scenarios"][0]["bootstrap"];
        assert_eq!(bootstrap["status"], "abstained");
        assert_eq!(bootstrap["reason"], "numerical_instability");
        assert!(bootstrap.get("value").is_none());
        assert!(bootstrap.get("point").is_none());
        let rendered = serde_json::to_string(&json).unwrap();
        assert!(rendered.contains("\"status\":\"not_requested\""));
        assert!(!rendered.contains(":null"));
        assert!(!rendered.contains("NaN"));

        let mut csv = Vec::new();
        write_uncertainty_csv(&mut csv, &summary).unwrap();
        let csv = String::from_utf8(csv).unwrap();
        for line in csv.lines().filter(|line| !line.is_empty()) {
            assert_eq!(line.split(',').count(), 10, "malformed row: {line}");
        }
        let bootstrap_row = csv
            .lines()
            .find(|line| line.contains("bootstrap_all,abstained"))
            .unwrap()
            .split(',')
            .collect::<Vec<_>>();
        assert!(bootstrap_row[4..10].iter().all(|field| field.is_empty()));

        let mut writer = RunLogWriter::new(Vec::new());
        write_exp0_uncertainty_events(&mut writer, &summary, 6, 7).unwrap();
        let events = pid_runlog::read_events(std::io::BufReader::new(std::io::Cursor::new(
            writer.into_inner(),
        )))
        .unwrap();
        assert!(events.iter().any(|event| matches!(
            event,
            RunLogEvent::EvaluationMetric { name, metadata, .. }
                if name == "exp0.uncertainty.independent_additive.bootstrap_status_code"
                    && metadata.get("status").map(String::as_str) == Some("abstained")
                    && metadata.get("reason").map(String::as_str)
                        == Some("numerical_instability")
        )));
        assert!(events.iter().any(|event| matches!(
            event,
            RunLogEvent::EvaluationMetric { name, metadata, .. }
                if name == "exp0.uncertainty.independent_additive.perm_s2_status_code"
                    && metadata.get("status").map(String::as_str) == Some("not_requested")
        )));
        assert!(!events.iter().any(|event| matches!(
            event,
            RunLogEvent::EvaluationMetric { name, .. }
                if name == "exp0.uncertainty.independent_additive.perm_s1_p"
                    || name.contains("independent_additive.i1_point")
                    || name.contains("independent_additive.i1_quantile")
        )));
    }

    #[test]
    fn produced_uncertainty_runlog_retains_points_and_valid_counts() {
        let summary = UncertaintySummary {
            enabled: true,
            n_boot: 3,
            n_perm: 5,
            block_size: 1,
            subsample_len: Some(4),
            alpha: 0.05,
            seed: 7,
            scenarios: vec![ScenarioUncertainty {
                name: "unique_s1",
                boot: ScientificOutcome::Produced(BootMiTriple {
                    i1: QuantileTriple {
                        point: 0.1,
                        quantile_low: 0.05,
                        quantile_high: 0.15,
                        n_valid: 3,
                    },
                    i2: QuantileTriple {
                        point: 0.2,
                        quantile_low: 0.1,
                        quantile_high: 0.3,
                        n_valid: 3,
                    },
                    i12: QuantileTriple {
                        point: 0.4,
                        quantile_low: 0.2,
                        quantile_high: 0.6,
                        n_valid: 3,
                    },
                }),
                perm_s1: ScientificOutcome::Produced(PermutationDiagnostic {
                    tail_fraction: 0.01,
                    n_valid: 5,
                }),
                perm_s2: ScientificOutcome::NotRequested,
            }],
            permutation_checks: 1,
            permutation_agreements: 1,
            bootstrap_instabilities: 0,
        };

        let mut writer = RunLogWriter::new(Vec::new());
        write_exp0_uncertainty_events(&mut writer, &summary, 6, 7).unwrap();
        let events = pid_runlog::read_events(std::io::BufReader::new(std::io::Cursor::new(
            writer.into_inner(),
        )))
        .unwrap();

        for (name, expected) in [
            ("exp0.uncertainty.unique_s1.i1_point", 0.1_f64),
            ("exp0.uncertainty.unique_s1.i2_point", 0.2_f64),
            ("exp0.uncertainty.unique_s1.i12_point", 0.4_f64),
        ] {
            assert!(events.iter().any(|event| matches!(
                event,
                RunLogEvent::EvaluationMetric {
                    name: event_name,
                    value,
                    metadata,
                    ..
                } if event_name == name
                    && value.to_bits() == expected.to_bits()
                    && metadata.get("n_valid").map(String::as_str) == Some("3")
            )));
        }
        for name in [
            "exp0.uncertainty.unique_s1.perm_s1_status_code",
            "exp0.uncertainty.unique_s1.perm_s1_p",
        ] {
            assert!(events.iter().any(|event| matches!(
                event,
                RunLogEvent::EvaluationMetric {
                    name: event_name,
                    metadata,
                    ..
                } if event_name == name
                    && metadata.get("n_valid").map(String::as_str) == Some("5")
            )));
        }
    }

    #[test]
    fn permutation_only_uncertainty_csv_has_fixed_width() {
        let summary = UncertaintySummary {
            enabled: true,
            n_boot: 0,
            n_perm: 1,
            block_size: 1,
            subsample_len: None,
            alpha: 0.05,
            seed: 7,
            scenarios: vec![ScenarioUncertainty {
                name: "unique_s1",
                boot: ScientificOutcome::NotRequested,
                perm_s1: ScientificOutcome::Produced(PermutationDiagnostic {
                    tail_fraction: 0.01,
                    n_valid: 1,
                }),
                perm_s2: ScientificOutcome::Produced(PermutationDiagnostic {
                    tail_fraction: 0.5,
                    n_valid: 1,
                }),
            }],
            permutation_checks: 2,
            permutation_agreements: 2,
            bootstrap_instabilities: 0,
        };

        let mut csv = Vec::new();
        write_uncertainty_csv(&mut csv, &summary).unwrap();
        let csv = String::from_utf8(csv).unwrap();
        for line in csv.lines().filter(|line| !line.is_empty()) {
            assert_eq!(line.split(',').count(), 10, "malformed row: {line}");
        }
        let bootstrap_row = csv
            .lines()
            .find(|line| line.contains("bootstrap_all,not_requested"))
            .unwrap();
        assert_eq!(bootstrap_row.split(',').count(), 10);
    }

    #[test]
    fn permutation_only_uncertainty_ignores_bootstrap_block_constraints() {
        let cfg = UncertaintyConfig {
            n_boot: 0,
            n_perm: 1,
            block_size: 40,
            alpha: 0.05,
            seed: 7,
        };

        let summary = compute_uncertainty(40, &ksg_cfg_for_test(), cfg).unwrap();

        assert_eq!(summary.subsample_len, None);
        assert!(summary
            .scenarios
            .iter()
            .all(|scenario| matches!(scenario.boot, ScientificOutcome::NotRequested)));
        let json = uncertainty_json(&summary).unwrap();
        assert_eq!(json["bootstrap_config"]["status"], "not_requested");
        assert!(json["bootstrap_config"].get("block_size").is_none());
    }

    #[test]
    fn uncertainty_callback_and_statistic_are_mi_only() {
        let n = 80;
        let (s1, s2, target) = gen_independent_additive(n, 1, 0.05, 42);
        let s1 = MatRef::new(&s1, n, 1).unwrap();
        let s2 = MatRef::new(&s2, n, 1).unwrap();
        let target = MatRef::new(&target, n, 1).unwrap();
        let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
        let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
        let (target, _) = Standardizer::fit_transform(target, ConstantColumnPolicy::Error).unwrap();
        let mats = [s1.as_ref(), s2.as_ref(), target.as_ref()];

        let declaration = uncertainty_callback_declaration(&mats).unwrap();
        let values = uncertainty_stat_vec(&mats, &ksg_cfg_for_test()).unwrap();

        assert_eq!(declaration.output_values, 3);
        assert_eq!(values.len(), 3);
        assert!(values.iter().all(|value| value.is_finite()));
    }

    #[test]
    fn uncertainty_recovers_marginal_truth_table() {
        // The preregistered, ground-truth-derived contract: the permutation null
        // test must call a source significant iff it is marginally informative by
        // construction. On healthy small-d data this should be recovered exactly.
        // Small counts keep this fast under `cargo test` (debug).
        let cfg = UncertaintyConfig {
            n_boot: 24,
            n_perm: 60,
            block_size: 1,
            alpha: 0.05,
            seed: 0xC0FFEE,
        };
        let u = compute_uncertainty(240, &ksg_cfg_for_test(), cfg).unwrap();
        // All four scenarios, both sources → 8 checks; all should agree.
        assert_eq!(u.permutation_checks, 8);
        assert_eq!(
            u.permutation_agreements, 8,
            "permutation null failed to recover marginal-informativeness truth"
        );
        // This deterministic fixture should not lose any subsample statistics numerically.
        assert_eq!(u.bootstrap_instabilities, 0);
        // Per-scenario sanity: unique_s1 → S1 significant, S2 not.
        let unique = u
            .scenarios
            .iter()
            .find(|s| s.name == "unique_s1")
            .expect("unique_s1 present");
        let ScientificOutcome::Produced(perm_s1) = unique.perm_s1 else {
            panic!("unique_s1 S1 permutation must be produced");
        };
        let ScientificOutcome::Produced(perm_s2) = unique.perm_s2 else {
            panic!("unique_s1 S2 permutation must be produced");
        };
        assert!(perm_s1.tail_fraction < cfg.alpha);
        assert!(perm_s2.tail_fraction >= cfg.alpha);
    }

    #[test]
    fn uncertainty_violations_block_go_but_not_when_clean() {
        // A clean uncertainty run (agreements == checks, no instabilities) must
        // contribute zero violations and therefore not change the verdict.
        let mut gates = GateSummary {
            case_results: 1,
            ..Default::default()
        };
        assert_eq!(gates.status(), "GO");
        let clean = UncertaintySummary {
            enabled: true,
            permutation_checks: 8,
            permutation_agreements: 8,
            bootstrap_instabilities: 0,
            ..Default::default()
        };
        gates.observe_uncertainty(&clean);
        assert_eq!(gates.uncertainty_violations(), 0);
        assert_eq!(gates.status(), "GO");

        // A disagreement (e.g. a pure-noise source flagged significant) must block GO.
        let dirty = UncertaintySummary {
            enabled: true,
            permutation_checks: 8,
            permutation_agreements: 6,
            bootstrap_instabilities: 1,
            ..Default::default()
        };
        gates.observe_uncertainty(&dirty);
        assert_eq!(gates.uncertainty_violations(), 3);
        assert_ne!(gates.status(), "GO");
    }

    #[test]
    fn uncertainty_runlog_is_valid_and_keeps_gate_metric_family_separate() {
        let runlog_path = temp_path("unc-runlog.jsonl");
        let mut gates = GateSummary {
            case_results: 12,
            normalized_invariant_violations: 7,
            ..Default::default()
        };
        let cfg = UncertaintyConfig {
            n_boot: 16,
            n_perm: 40,
            block_size: 1,
            alpha: 0.05,
            seed: 7,
        };
        let u = compute_uncertainty(200, &ksg_cfg_for_test(), cfg).unwrap();
        gates.observe_uncertainty(&u);
        write_exp0_runlog(
            &runlog_path,
            None,
            &gates,
            Exp0RunConfig {
                n: 200,
                k: 3,
                dims: &[10],
                seeds: &[42],
                hash_project_to: Some(64),
                uncertainty: cfg,
            },
            Some(&u),
            None,
            false,
        )
        .unwrap();

        let events = pid_runlog::read_events_from_path(&runlog_path).unwrap();
        let validation = pid_runlog::validate_events(&events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        let summary = pid_runlog::summarize_events(&events).unwrap();
        // Uncertainty events are EvaluationMetric, so the six PidMetric gate events
        // are unchanged; the CI smoke greps rely on this invariant.
        assert_eq!(summary.pid_metrics, 6);
        assert!(summary.evaluation_metrics >= 4);

        let _ = std::fs::remove_file(runlog_path);
    }

    #[test]
    fn gaussian_mi_truth_matches_closed_form() {
        // Independent jointly-Gaussian system T = a*S1 + b*S2 + c*Z; verify the
        // measure-independent MI terms against hand-checked Cover--Thomas algebra.
        let (a, b, c) = (1.0, 1.0, 1.0);
        let truth = gaussian_mi_truth(a, b, c);
        // var_t = 3, Var(T|S1,S2) = 1 => I12 = 0.5 ln 3.
        assert!((truth.i12 - 0.5 * 3.0_f64.ln()).abs() < 1e-12);
        // I(S1;T) = 0.5 ln(3/2) (b^2+c^2 = 2); symmetric in a<->b so I1 == I2 here.
        assert!((truth.i1 - 0.5 * (3.0_f64 / 2.0).ln()).abs() < 1e-12);
        assert!((truth.i2 - truth.i1).abs() < 1e-12);
        // Asymmetric system: a > b implies I(S1;T) > I(S2;T).
        let asym = gaussian_mi_truth(1.0, 0.3, 1.0);
        assert!(asym.i1 > asym.i2);
    }

    #[test]
    fn strict_band_gate_is_go_in_analytically_checked_regime() {
        // The curated analytic band (d=1 Gaussian grid at STRICT_BAND_GATE_N) must return GO:
        // this is the regime where the KSG estimator recovers the closed-form MI terms within
        // the documented scale-aware noise floor, so a regression here is a genuine signal.
        // This is the only sweep `--strict-gate` enforces. Default high-dimensional MI/coherence
        // NO-GO or geometry PIVOT findings stay informative and ungated.
        let mut sink = Vec::new();
        let band = strict_band_gate(&mut sink, true, &ksg_cfg_for_test()).unwrap();
        assert_eq!(
            band.status(),
            "GO",
            "curated analytic band must be GO in its analytically checked regime; analytic_mi_recovery_failures={}",
            band.analytic_mi_recovery_failures
        );
        // Three grid systems, each contributing one case result; all MI checks within tol.
        assert_eq!(band.case_results, STRICT_BAND_GAUSS_GRID.len());
        assert_eq!(band.analytic_mi_recovery_failures, 0);
        assert_eq!(band.scope, GateScope::CuratedAnalyticMiRecovery);
        let csv = String::from_utf8(sink).unwrap();
        assert!(csv.contains("curated_analytic_mi_recovery,GO,not_adjudicated"));
    }
}
