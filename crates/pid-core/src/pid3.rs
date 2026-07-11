use crate::distance_matrix::{symmetric_distances, SymmetricDistanceMatrix};
use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
use crate::stats::{compensated_sum, digamma, digamma_int_table};
use crate::support::{
    validate_observed_sample_conditions, validate_support_contract, SupportContract,
};

#[derive(Clone, Copy)]
struct DistIsx3 {
    joint: f64,
    ds: f64,
    dt: f64,
}

#[derive(Debug, Clone)]
pub struct Pid3Config {
    pub k: usize,
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    /// Strict counts use the predecessor of the raw kNN radius.
    pub tie_epsilon: f64,
    /// Caller-declared population support assumptions. The default is unspecified and fails
    /// closed; use [`Pid3Config::assume_absolutely_continuous`] for an explicit assertion.
    pub support_contract: SupportContract,
    /// Explicit research opt-in for the full mixed-dimensional redundancy lattice.
    ///
    /// Every full three-source lattice contains antichains such as
    /// `{{S0}, {S1,S2}}`. The current kNN construction compares a singleton source ball with a
    /// concatenated pair-source ball without a dimension-derived normalization. Setting this to
    /// `true` preserves the implementation for reference reproduction and diagnostics; it does
    /// not validate a mixed-dimensional small-ball limit for scientific inference.
    pub experimental_allow_mixed_dimension_lattice: bool,
}

impl Default for Pid3Config {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            support_contract: SupportContract::Unspecified,
            experimental_allow_mixed_dimension_lattice: false,
        }
    }
}

impl Pid3Config {
    /// Construct a configuration that explicitly asserts full-dimensional absolute continuity.
    ///
    /// The full mixed-dimensional lattice remains research-gated. This constructor therefore
    /// leaves [`Self::experimental_allow_mixed_dimension_lattice`] disabled and is intended first
    /// for [`pid3_isx_partial`].
    pub fn assume_absolutely_continuous() -> Self {
        Self {
            support_contract: SupportContract::AssumeAbsolutelyContinuous,
            ..Self::default()
        }
    }
}

/// A 3-source antichain on indices {0,1,2}, represented as up to 3 conjunction masks.
///
/// Each mask is a non-zero subset bitmask over {0,1,2}:
/// - bit 0 => source 0
/// - bit 1 => source 1
/// - bit 2 => source 2
///
/// Example: `{ {0}, {1,2} }` is encoded as `[0b001, 0b110]`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Antichain3 {
    sets: [u8; 3],
    len: u8,
}

impl Antichain3 {
    pub fn sets(&self) -> &[u8] {
        &self.sets[..(self.len as usize)]
    }

    pub fn len(&self) -> usize {
        self.len as usize
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Create an antichain from a list of non-empty subset masks over {0,1,2}.
    ///
    /// The input is canonicalized (sorted ascending) and validated to satisfy the
    /// antichain property (no set is a subset of another).
    pub fn try_from_sets(sets: &[u8]) -> PidResult<Self> {
        if sets.is_empty() || sets.len() > 3 {
            return Err(PidError::InvalidConfig {
                context: "Antichain3::try_from_sets",
                message: "need 1..=3 sets",
            });
        }

        let mut out = [0u8; 3];
        for (idx, &m) in sets.iter().enumerate() {
            if m == 0 || m > 0b111 {
                return Err(PidError::InvalidConfig {
                    context: "Antichain3::try_from_sets",
                    message: "set masks must be in 1..=0b111",
                });
            }
            out[idx] = m;
        }

        let len = sets.len();
        out[..len].sort_unstable();

        for i in 0..len {
            for j in (i + 1)..len {
                let a = out[i];
                let b = out[j];
                if a == b {
                    return Err(PidError::InvalidConfig {
                        context: "Antichain3::try_from_sets",
                        message: "duplicate set mask",
                    });
                }
                if (a & b) == a || (a & b) == b {
                    return Err(PidError::InvalidConfig {
                        context: "Antichain3::try_from_sets",
                        message: "not an antichain (subset relation present)",
                    });
                }
            }
        }

        Ok(Self {
            sets: out,
            len: len as u8,
        })
    }
}

impl Ord for Antichain3 {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.len
            .cmp(&other.len)
            .then_with(|| self.sets().cmp(other.sets()))
    }
}

impl PartialOrd for Antichain3 {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug, Clone)]
pub struct Pid3Redundancy {
    pub antichain: Antichain3,
    pub value: f64,
}

#[derive(Debug, Clone)]
pub struct Pid3Atom {
    pub antichain: Antichain3,
    pub value: f64,
}

/// Scientific maturity of a full continuous PID3 result.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum Pid3MethodStatus {
    /// Reference-reproduction path containing mixed-dimensional lattice comparisons without an
    /// established small-ball limit.
    ExperimentalMixedDimension,
}

const FULL_PID3_WARNINGS: [&str; 3] = [
    "the full continuous PID3 lattice compares mixed-dimensional source neighborhoods and has no established small-ball consistency result",
    "the support contract is caller-declared; sample checks can identify incompatible observations but cannot determine their cause or verify population support",
    "relative source units and preprocessing are part of the shared-exclusions estimand and must be recorded alongside every reported result",
];

/// Full 18-coordinate continuous PID3 result with attached status and configuration metadata.
///
/// This type is produced only after the explicit mixed-dimensional research opt-in. Its metadata
/// and warnings are part of the result contract, not a validation claim. Use [`Pid3Report`] when
/// caller-declared preprocessing and observation-model descriptions must travel with it.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct Pid3Result {
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub support_contract: SupportContract,
    pub source_ambient_dimensions: [usize; 3],
    pub target_ambient_dimension: usize,
    pub method_status: Pid3MethodStatus,
    pub warnings: Vec<&'static str>,
    pub redundancies: Vec<Pid3Redundancy>,
    pub atoms: Vec<Pid3Atom>,
}

/// Structurally checked, caller-declared provenance for a [`Pid3Report`].
///
/// Separate source descriptions are required because relative source scaling changes the
/// shared-exclusions estimand. Construction checks only nonemptiness, not truth or adequacy.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Pid3Provenance {
    source1_preprocessing_description: String,
    source2_preprocessing_description: String,
    source3_preprocessing_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
}

impl Pid3Provenance {
    pub fn new(
        source1_preprocessing_description: impl Into<String>,
        source2_preprocessing_description: impl Into<String>,
        source3_preprocessing_description: impl Into<String>,
        target_preprocessing_description: impl Into<String>,
        observation_model_description: impl Into<String>,
    ) -> PidResult<Self> {
        let source1_preprocessing_description = source1_preprocessing_description.into();
        let source2_preprocessing_description = source2_preprocessing_description.into();
        let source3_preprocessing_description = source3_preprocessing_description.into();
        let target_preprocessing_description = target_preprocessing_description.into();
        let observation_model_description = observation_model_description.into();
        for (description, message) in [
            (
                source1_preprocessing_description.as_str(),
                "source1_preprocessing_description must be nonempty",
            ),
            (
                source2_preprocessing_description.as_str(),
                "source2_preprocessing_description must be nonempty",
            ),
            (
                source3_preprocessing_description.as_str(),
                "source3_preprocessing_description must be nonempty",
            ),
            (
                target_preprocessing_description.as_str(),
                "target_preprocessing_description must be nonempty",
            ),
            (
                observation_model_description.as_str(),
                "observation_model_description must be nonempty",
            ),
        ] {
            if description.trim().is_empty() {
                return Err(PidError::InvalidConfig {
                    context: "Pid3Provenance::new",
                    message,
                });
            }
        }
        Ok(Self {
            source1_preprocessing_description,
            source2_preprocessing_description,
            source3_preprocessing_description,
            target_preprocessing_description,
            observation_model_description,
        })
    }

    pub fn source1_preprocessing_description(&self) -> &str {
        &self.source1_preprocessing_description
    }

    pub fn source2_preprocessing_description(&self) -> &str {
        &self.source2_preprocessing_description
    }

    pub fn source3_preprocessing_description(&self) -> &str {
        &self.source3_preprocessing_description
    }

    pub fn target_preprocessing_description(&self) -> &str {
        &self.target_preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
    }
}

/// Full experimental PID3 result with caller-declared preprocessing and observation provenance.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct Pid3Report {
    pub result: Pid3Result,
    pub provenance: Pid3Provenance,
}

/// One continuous PID3 redundancy coordinate with its branch ambient dimensions.
///
/// `value` is present only when every branch in the antichain has the same ambient dimension.
/// This dimension check is necessary but does not certify compatible intrinsic dimensions,
/// reference measures, or leading-order intersection behavior.
#[derive(Debug, Clone)]
pub struct Pid3PartialRedundancy {
    pub antichain: Antichain3,
    pub branch_dimensions: Vec<usize>,
    pub value: Option<f64>,
}

/// One PID3 atom derived from the exactly available redundancy coordinates.
#[derive(Debug, Clone)]
pub struct Pid3PartialAtom {
    pub antichain: Antichain3,
    pub value: Option<f64>,
    /// Every unavailable redundancy coordinate with a non-zero coefficient in this atom's exact
    /// Möbius expansion, in canonical antichain order.
    pub unavailable_redundancies: Vec<Antichain3>,
}

/// Ambient-dimension-compatible part of a continuous three-source PID lattice.
///
/// This result deliberately does not fill unavailable coordinates with zeros or inferred values.
/// Consequently the available atoms are valid exact linear combinations of the returned
/// redundancy estimates, but they do not by themselves form a complete 18-atom decomposition.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct Pid3PartialResult {
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub support_contract: SupportContract,
    pub source_ambient_dimensions: [usize; 3],
    pub target_ambient_dimension: usize,
    /// Always `true`: dimension compatibility removes a known invalid comparison but does not
    /// establish a consistency theorem for the remaining shared-exclusions coordinates.
    pub experimental: bool,
    /// Deterministically ordered scientific limitations that must travel with the estimates.
    pub warnings: Vec<&'static str>,
    pub redundancies: Vec<Pid3PartialRedundancy>,
    pub atoms: Vec<Pid3PartialAtom>,
}

const PARTIAL_PID3_WARNINGS: [&str; 4] = [
    "the support contract is caller-declared; sample checks can identify incompatible observations but cannot determine their cause or verify population support",
    "equal ambient branch dimensions do not establish equal intrinsic dimensions, compatible reference measures, or regular leading-order intersections",
    "relative source units and preprocessing are part of the shared-exclusions estimand and must be recorded alongside every reported result",
    "unavailable coordinates are not imputed; available atoms do not form a complete 18-atom decomposition",
];

/// Partial PID3 availability result with caller-declared preprocessing/observation provenance.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct Pid3PartialReport {
    pub result: Pid3PartialResult,
    pub provenance: Pid3Provenance,
}

impl Pid3PartialResult {
    pub fn redundancy(&self, antichain: Antichain3) -> Option<&Pid3PartialRedundancy> {
        self.redundancies
            .iter()
            .find(|redundancy| redundancy.antichain == antichain)
    }

    pub fn atom(&self, antichain: Antichain3) -> Option<&Pid3PartialAtom> {
        self.atoms.iter().find(|atom| atom.antichain == antichain)
    }
}

impl Pid3Result {
    pub fn redundancy(&self, antichain: Antichain3) -> Option<f64> {
        self.redundancies
            .iter()
            .find(|r| r.antichain == antichain)
            .map(|r| r.value)
    }

    pub fn atom(&self, antichain: Antichain3) -> Option<f64> {
        self.atoms
            .iter()
            .find(|a| a.antichain == antichain)
            .map(|a| a.value)
    }
}

/// Full 3-source continuous SxPID using shared exclusions (Ehrlich et al. 2024).
///
/// Computes all 18 PID atoms for three sources by:
/// 1) Estimating `I^sx_∩(T : α)` for every non-empty antichain α on {0,1,2} using the kNN estimator
///    (a KSG-style construction with disjunction neighborhoods).
/// 2) Applying Möbius inversion on the redundancy lattice to obtain the PID atoms Π^sx(α).
///
/// Units: nats (natural logarithm).
///
/// # Experimental mixed-dimensional lattice
///
/// A full three-source lattice necessarily includes singleton-vs-pair antichains such as
/// `{{S0}, {S1,S2}}`. Their source neighborhoods live in different ambient dimensions, so their
/// raw small-ball radii do not share a dimension-independent reference scaling. Consequently this
/// entry point rejects the default configuration. Set
/// [`Pid3Config::experimental_allow_mixed_dimension_lattice`] to `true` only to reproduce reference
/// fixtures or run explicitly labelled diagnostics. That opt-in does not make the resulting atoms
/// validated mixed-dimensional scientific estimates. Equal dimensions among the three singleton
/// source matrices would not remove the singleton-vs-pair mismatch, nor prove compatible intrinsic
/// dimensions or reference measures.
///
/// Relative source units/preprocessing are part of the continuous shared-exclusions estimand;
/// record them and do not compare atoms across schemes. Exact deterministic continuous maps have
/// infinite MI and require a justified noise model or a suitable discrete/mixed estimator.
/// Collapsed or ambiguous positive k-th-neighbor shells are rejected rather than assigned a silent
/// tie convention.
pub fn pid3_isx(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<Pid3Result> {
    validate_pid3_common("pid3_isx", s0, s1, s2, t, cfg)?;
    if !cfg.experimental_allow_mixed_dimension_lattice {
        return Err(PidError::InvalidConfig {
            context: "pid3_isx",
            message: "the full continuous PID3 lattice compares mixed-dimensional singleton and pair source neighborhoods; set experimental_allow_mixed_dimension_lattice=true only for reference reproduction or explicitly labelled diagnostics",
        });
    }
    let n = t.nrows();
    let k = cfg.k;
    validate_support_contract("pid3_isx", cfg.support_contract, cfg.metric)?;
    validate_observed_sample_conditions("pid3_isx", cfg.support_contract, &[s0, s1, s2, t])?;

    let sources = [
        symmetric_distances(s0, cfg.metric)?,
        symmetric_distances(s1, cfg.metric)?,
        symmetric_distances(s2, cfg.metric)?,
    ];
    let target = symmetric_distances(t, cfg.metric)?;

    let antichains = antichains_3();
    let mut redundancies = Vec::with_capacity(antichains.len());
    for &a in antichains {
        let val = redundancy_for_antichain("pid3_isx", &sources, &target, a, cfg)?;
        redundancies.push(Pid3Redundancy {
            antichain: a,
            value: val,
        });
    }

    let atoms = mobius_inversion_atoms(antichains, &redundancies)?;
    Ok(Pid3Result {
        n_samples: n,
        k,
        metric: cfg.metric,
        support_contract: cfg.support_contract,
        source_ambient_dimensions: [s0.ncols(), s1.ncols(), s2.ncols()],
        target_ambient_dimension: t.ncols(),
        method_status: Pid3MethodStatus::ExperimentalMixedDimension,
        warnings: FULL_PID3_WARNINGS.to_vec(),
        redundancies,
        atoms,
    })
}

/// Compute full experimental PID3 while preserving caller-declared provenance.
///
/// Provenance construction checks only for nonempty descriptions. Neither that structural check
/// nor this wrapper validates the mixed-dimensional estimator, population support, preprocessing
/// choice, or observation model.
pub fn pid3_isx_report(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
) -> PidResult<Pid3Report> {
    Ok(Pid3Report {
        result: pid3_isx(s0, s1, s2, t, cfg)?,
        provenance: provenance.clone(),
    })
}

/// Estimate only the ambient-dimension-compatible coordinates of continuous three-source PID.
///
/// For each redundancy antichain, the ambient dimension of a branch is the sum of the column
/// counts of the sources in that branch. A redundancy is estimated only when all of its branches
/// have the same dimension. Each atom is then expanded exactly as an integer linear combination
/// of redundancy coordinates by Möbius inversion. Its value is returned only when every
/// non-zero-coefficient dependency is available; otherwise `value` is `None` and
/// [`Pid3PartialAtom::unavailable_redundancies`] lists the exact missing coordinates.
///
/// This is a conservative availability API, not a proof of estimator consistency. Equal ambient
/// dimensions do not establish equal intrinsic dimensions, compatible reference measures, or
/// regular leading-order intersections. The declared support contract remains a caller assertion,
/// and observations with exact ties are conservatively rejected as incompatible with ideal
/// i.i.d., unrounded continuous-sample conditions, without inferring their cause or population
/// support.
///
/// # Errors
///
/// Returns an error for incompatible shapes or configuration, an unsupported or unspecified
/// support contract, observations incompatible with ideal continuous-sample conditions, invalid
/// `k`, or degenerate or ambiguous k-nearest-neighbor geometry in any redundancy that is actually
/// estimated.
pub fn pid3_isx_partial(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<Pid3PartialResult> {
    const CONTEXT: &str = "pid3_isx_partial";

    validate_pid3_common(CONTEXT, s0, s1, s2, t, cfg)?;
    let n = t.nrows();
    let k = cfg.k;
    validate_support_contract(CONTEXT, cfg.support_contract, cfg.metric)?;
    validate_observed_sample_conditions(CONTEXT, cfg.support_contract, &[s0, s1, s2, t])?;

    let sources = [
        symmetric_distances(s0, cfg.metric)?,
        symmetric_distances(s1, cfg.metric)?,
        symmetric_distances(s2, cfg.metric)?,
    ];
    let target = symmetric_distances(t, cfg.metric)?;
    let source_dimensions = [s0.ncols(), s1.ncols(), s2.ncols()];
    let antichains = antichains_3();

    let mut redundancies = Vec::with_capacity(antichains.len());
    for &antichain in antichains {
        let branch_dimensions = antichain_branch_dimensions(antichain, source_dimensions)?;
        let compatible = branch_dimensions
            .windows(2)
            .all(|dimensions| dimensions[0] == dimensions[1]);
        let value = if compatible {
            Some(redundancy_for_antichain(
                CONTEXT, &sources, &target, antichain, cfg,
            )?)
        } else {
            None
        };
        redundancies.push(Pid3PartialRedundancy {
            antichain,
            branch_dimensions,
            value,
        });
    }

    let atoms = partial_mobius_inversion_atoms(antichains, &redundancies)?;
    Ok(Pid3PartialResult {
        n_samples: n,
        k,
        metric: cfg.metric,
        support_contract: cfg.support_contract,
        source_ambient_dimensions: source_dimensions,
        target_ambient_dimension: t.ncols(),
        experimental: true,
        warnings: PARTIAL_PID3_WARNINGS.to_vec(),
        redundancies,
        atoms,
    })
}

/// Compute the conservative partial PID3 surface while preserving caller-declared provenance.
///
/// Provenance is checked only for nonempty descriptions and does not establish estimator
/// consistency, support, preprocessing validity, or an observation model.
pub fn pid3_isx_partial_report(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
) -> PidResult<Pid3PartialReport> {
    Ok(Pid3PartialReport {
        result: pid3_isx_partial(s0, s1, s2, t, cfg)?,
        provenance: provenance.clone(),
    })
}

fn validate_pid3_common(
    context: &'static str,
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<()> {
    if s0.nrows() != s1.nrows() || s0.nrows() != s2.nrows() || s0.nrows() != t.nrows() {
        let n = s0.nrows();
        let right_rows = if s1.nrows() != n {
            s1.nrows()
        } else if s2.nrows() != n {
            s2.nrows()
        } else {
            t.nrows()
        };
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: n,
            right_rows,
        });
    }
    if s0.ncols() == 0 || s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "inputs must have at least 1 column",
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    if cfg.k == 0 || s0.nrows() <= cfg.k {
        return Err(PidError::InvalidK {
            k: cfg.k,
            n_samples: s0.nrows(),
        });
    }
    if cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context,
            message: "PID3 ISX is restricted to its paper-faithful Metric::Chebyshev (L∞) convention; other metrics are research-gated",
        });
    }
    Ok(())
}

fn antichain_branch_dimensions(
    antichain: Antichain3,
    source_dimensions: [usize; 3],
) -> PidResult<Vec<usize>> {
    let mut dimensions = Vec::with_capacity(antichain.len());
    for &source_set in antichain.sets() {
        let mut dimension = 0usize;
        for (source, &source_dimension) in source_dimensions.iter().enumerate() {
            if source_set & (1u8 << source) != 0 {
                dimension =
                    dimension
                        .checked_add(source_dimension)
                        .ok_or(PidError::InvalidConfig {
                            context: "pid3_isx_partial",
                            message: "source branch dimension overflow",
                        })?;
            }
        }
        dimensions.push(dimension);
    }
    Ok(dimensions)
}

fn redundancy_for_antichain(
    context: &'static str,
    sources: &[SymmetricDistanceMatrix; 3],
    target: &SymmetricDistanceMatrix,
    antichain: Antichain3,
    cfg: &Pid3Config,
) -> PidResult<f64> {
    let n = target.n();
    let k = cfg.k;
    let kth = k - 1;

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    // Per-point local term. Each point reads the shared (immutable) distance matrices and
    // allocates its own scratch, so the closure is pure and order-independent. Terms are
    // collected **in index order** and summed left-to-right exactly as the serial loop did,
    // so the `parallel` path is bit-for-bit identical to serial (see `par::map_index_ordered`).
    let local = |i: usize| -> PidResult<f64> {
        let mut scratch = Vec::with_capacity(n.saturating_sub(1));
        for j in 0..n {
            if i == j {
                continue;
            }
            let d0 = sources[0].get(i, j);
            let d1 = sources[1].get(i, j);
            let d2 = sources[2].get(i, j);
            let ds_disj = source_disjunction_distance(antichain, d0, d1, d2);
            let dt_ij = target.get(i, j);
            scratch.push(DistIsx3 {
                joint: dt_ij.max(ds_disj),
                ds: ds_disj,
                dt: dt_ij,
            });
        }

        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: pid3_non_positive_radius_context(context),
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(context, i, k, eps_raw, interior_count, boundary_count)?;
        let eps = strict_radius(eps_raw);

        // Counts exclude self; estimator uses inclusive counts.
        let mut n_alpha = 1usize;
        let mut n_t = 1usize;
        for d in &scratch {
            if d.ds <= eps {
                n_alpha += 1;
            }
            if d.dt <= eps {
                n_t += 1;
            }
        }

        Ok(psi_k + psi_n - psi_int[n_alpha] - psi_int[n_t])
    };

    let terms = crate::par::map_index_ordered(n, local)?;
    let sum = compensated_sum(terms.iter().copied());
    Ok(sum / (n as f64))
}

fn pid3_non_positive_radius_context(context: &'static str) -> &'static str {
    match context {
        "pid3_isx_partial" => "pid3_isx_partial: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
        _ => "pid3_isx: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
    }
}

#[inline]
fn source_disjunction_distance(antichain: Antichain3, d0: f64, d1: f64, d2: f64) -> f64 {
    let mut best = f64::INFINITY;
    for &m in antichain.sets() {
        let mut v = 0.0f64;
        if (m & 0b001) != 0 {
            v = v.max(d0);
        }
        if (m & 0b010) != 0 {
            v = v.max(d1);
        }
        if (m & 0b100) != 0 {
            v = v.max(d2);
        }
        best = best.min(v);
    }
    best
}

fn mobius_inversion_atoms(
    antichains: &[Antichain3],
    redundancies: &[Pid3Redundancy],
) -> PidResult<Vec<Pid3Atom>> {
    if antichains.len() != redundancies.len() {
        return Err(PidError::InvalidConfig {
            context: "mobius_inversion_atoms",
            message: "antichains/redundancies length mismatch",
        });
    }
    let coefficients = mobius_redundancy_coefficients(antichains)?;
    let mut atoms = Vec::with_capacity(antichains.len());
    for (idx, &a) in antichains.iter().enumerate() {
        let value = compensated_sum(
            coefficients[idx]
                .iter()
                .zip(redundancies)
                .filter(|(coefficient, _)| **coefficient != 0)
                .map(|(&coefficient, redundancy)| coefficient as f64 * redundancy.value),
        );
        if !value.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "mobius_inversion_atoms",
            });
        }
        atoms.push(Pid3Atom {
            antichain: a,
            value,
        });
    }
    Ok(atoms)
}

fn partial_mobius_inversion_atoms(
    antichains: &[Antichain3],
    redundancies: &[Pid3PartialRedundancy],
) -> PidResult<Vec<Pid3PartialAtom>> {
    if antichains.len() != redundancies.len() {
        return Err(PidError::InvalidConfig {
            context: "partial_mobius_inversion_atoms",
            message: "antichains/redundancies length mismatch",
        });
    }

    let coefficients = mobius_redundancy_coefficients(antichains)?;
    let mut atoms = Vec::with_capacity(antichains.len());
    for (atom_index, &antichain) in antichains.iter().enumerate() {
        let unavailable_redundancies = coefficients[atom_index]
            .iter()
            .enumerate()
            .filter_map(|(redundancy_index, &coefficient)| {
                (coefficient != 0 && redundancies[redundancy_index].value.is_none())
                    .then_some(antichains[redundancy_index])
            })
            .collect::<Vec<_>>();

        let value = if unavailable_redundancies.is_empty() {
            let mut terms = Vec::with_capacity(antichains.len());
            for (redundancy_index, &coefficient) in coefficients[atom_index].iter().enumerate() {
                if coefficient == 0 {
                    continue;
                }
                let value =
                    redundancies[redundancy_index]
                        .value
                        .ok_or(PidError::InvalidConfig {
                            context: "partial_mobius_inversion_atoms",
                            message: "available atom has an unavailable redundancy dependency",
                        })?;
                terms.push((coefficient as f64) * value);
            }
            Some(compensated_sum(terms))
        } else {
            None
        };

        atoms.push(Pid3PartialAtom {
            antichain,
            value,
            unavailable_redundancies,
        });
    }
    Ok(atoms)
}

fn mobius_redundancy_coefficients(antichains: &[Antichain3]) -> PidResult<Vec<Vec<i64>>> {
    let n = antichains.len();
    let topo = topo_order(antichains);
    if topo.len() != n {
        return Err(PidError::InvalidConfig {
            context: "mobius_redundancy_coefficients",
            message: "topological sort failed",
        });
    }

    let mut coefficients = vec![vec![0i64; n]; n];
    for (position, &atom_index) in topo.iter().enumerate() {
        coefficients[atom_index][atom_index] = 1;
        for &lower_atom_index in &topo[..position] {
            if !leq(antichains[lower_atom_index], antichains[atom_index]) {
                continue;
            }
            let (atom_coefficients, lower_atom_coefficients) = if atom_index < lower_atom_index {
                let (before_lower, from_lower) = coefficients.split_at_mut(lower_atom_index);
                (&mut before_lower[atom_index], &from_lower[0])
            } else {
                let (before_atom, from_atom) = coefficients.split_at_mut(atom_index);
                (&mut from_atom[0], &before_atom[lower_atom_index])
            };
            for (atom_coefficient, &lower_atom_coefficient) in atom_coefficients
                .iter_mut()
                .zip(lower_atom_coefficients.iter())
            {
                *atom_coefficient = atom_coefficient.checked_sub(lower_atom_coefficient).ok_or(
                    PidError::InvalidConfig {
                        context: "mobius_redundancy_coefficients",
                        message: "integer coefficient overflow",
                    },
                )?;
            }
        }
    }
    Ok(coefficients)
}

fn topo_order(antichains: &[Antichain3]) -> Vec<usize> {
    let mut remaining: Vec<usize> = (0..antichains.len()).collect();
    let mut out = Vec::with_capacity(remaining.len());
    while !remaining.is_empty() {
        let mut mins = Vec::new();
        'outer: for &i in &remaining {
            for &j in &remaining {
                if i == j {
                    continue;
                }
                if leq(antichains[j], antichains[i]) {
                    continue 'outer;
                }
            }
            mins.push(i);
        }
        mins.sort_by(|&a, &b| antichains[a].cmp(&antichains[b]));
        let chosen = mins[0];
        out.push(chosen);
        remaining.retain(|&x| x != chosen);
    }
    out
}

#[inline]
fn leq(a: Antichain3, b: Antichain3) -> bool {
    // a ⪯ b iff for every set B in b, there exists A in a with A ⊆ B.
    for &b_set in b.sets() {
        let mut found = false;
        for &a_set in a.sets() {
            if (a_set & b_set) == a_set {
                found = true;
                break;
            }
        }
        if !found {
            return false;
        }
    }
    true
}

fn antichains_3() -> &'static [Antichain3] {
    // Canonical order: increasing number of sets, then lexicographic by mask.
    const ANTICHAINS: [Antichain3; 18] = [
        Antichain3 {
            sets: [0b001, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b010, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b100, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b011, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b101, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b110, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b111, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b001, 0b010, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b010, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b010, 0b101, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b101, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b101, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b010, 0b100],
            len: 3,
        },
        Antichain3 {
            sets: [0b011, 0b101, 0b110],
            len: 3,
        },
    ];
    &ANTICHAINS
}
