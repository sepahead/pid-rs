//! Categorical **shared-exclusions** PID — the `i^sx_∩` construction of Makkeh, Gutknecht & Wibral
//! (2021, Phys. Rev. E 103, 032149; arXiv:2002.03356), with the part-whole / formal-logic
//! foundation of Gutknecht, Wibral & Makkeh (2021, arXiv:2008.09535).
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED.** The categorical redundancy functional, redundancy lattice, and pointwise
//! Möbius inversion come from the cited shared-exclusions papers. The default build provides a
//! direct empirical-PMF implementation for two to four sources. Resource budgets, cancellation,
//! deterministic accumulation, and result provenance are project-defined engineering around
//! that published method. External SxPID implementations are validation references, not the
//! definition of this code.
//!
//! Method catalog: shared-exclusions.categorical
//!
//! **EXTERNAL REFERENCE CODE.** A pinned external SxPID implementation is used for bounded
//! reference-fixture comparisons of values and sign/lattice conventions. Its GPL-3.0-only code is
//! not embedded in this library and is not the scientific definition of shared exclusions.
//!
//! Method catalog: validation.sxpid-reference-code
//!
//! **EXTERNAL REFERENCE CODE.** A pinned IDTxl revision supplies additional bounded comparison
//! fixtures. Its GPL-3.0-only code is not embedded in this library and does not define pid-rs
//! behavior.
//!
//! Method catalog: validation.idtxl-reference-code
//!
//! Fitted equal-width adapters are a separate project-defined composition: they first define new
//! categorical variables and then call this method. They are cataloged with the quantizer and are
//! not continuous shared-exclusions estimators.
//!
//! # Why this exists (and how it differs from the `discrete_pid` module)
//!
//! The `discrete_pid` module computes the Williams & Beer (2010) `I_min` redundancy, which is a
//! different functional. On the two-bit COPY of *independent* sources, `I_min` attributes the
//! **maximal** 1 bit of redundancy. The Harder et al. (2013) identity axiom would assign redundancy
//! equal to `I(S1;S2)`, which is zero here, while `I^sx_∩` assigns `ln(4/3)` nats and therefore does
//! not satisfy that axiom. SxPID instead defines
//! redundancy through **shared exclusions**: the information that source realizations *jointly
//! exclude* about the target, combined by logical **disjunction** over a redundancy lattice.
//! Three- and four-source lattices are computable here, but computability is distinct from
//! satisfying every desired cross-subsystem consistency property. General multivariate
//! lattice-consistency limitations identified by Lyu, Clark & Raviv (2026) are therefore treated
//! as a scope caveat, not as a claim that these routines settle multivariate PID theory.
//! The categorical functional and the continuous `I^sx_∩` estimator in `isx` share this scientific
//! lineage, but they use different observation models and finite-sample algorithms. Availability
//! in both regimes is not a license to pool atoms or assume identical estimator behavior.
//!
//! # The measure (direct empirical-PMF evaluation)
//!
//! For a realization `(s_1,…,s_n,t)`, a *collection* `a ⊆ {1..n}` denotes the event
//! `𝔞 = ⋂_{i∈a}{S_i = s_i}`; write `𝔱 = {T = t}`. A lattice node is an **antichain**
//! `α = {a_1,…,a_k}` (no collection a subset of another). Define
//!
//! ```text
//! i⁺(t:α) = −log P(⋃_j 𝔞_j)                      (informative; sources only)
//! i⁻(t:α) =  log[ P(t) / P(𝔱 ∩ ⋃_j 𝔞_j) ]        (misinformative)
//! i^sx_∩(t:α) = i⁺ − i⁻ = log[ P(𝔱 ∩ ⋃_j 𝔞_j) / (P(t)·P(⋃_j 𝔞_j)) ]
//! ```
//!
//! `P(⋃_j 𝔞_j)` is evaluated directly over the empirical support. The **pointwise atoms**
//! `π^sx(t:α)` are the Möbius inverse on the redundancy lattice
//! (`i^sx_∩(t:α) = Σ_{β ⪯ α} π^sx(t:β)`); **averaged atoms** are `Π(α) = Σ_rlz p(rlz) π(rlz,α)`
//! (inversion and averaging commute). A single-collection node gives `i^sx_∩(t:{a}) = i(t:s_a)`
//! (pointwise MI), i.e. the **self-redundancy** axiom.
//!
//! # Conventions (match the rest of the crate)
//!
//! - **Units: nats** (natural log). The reference fixtures (Abzinger/SxPID, IDTxl) are in bits;
//!   the regression tests convert with `× ln 2`.
//! - **Net atoms can be negative** — pointwise *and* averaged (e.g. XOR redundancy
//!   `= log(2/3) < 0`; for the UNQ gate (`T = S1`) the uninformative source's unique atom
//!   `= log(3/4) < 0`). The informative and misinformative partial atoms are separately
//!   non-negative (up to floating-point roundoff); only their difference can be negative. Nothing
//!   is clamped.
//! - **Determinism**: the joint pmf is built by sorting borrowed row indices and run-length
//!   encoding equal realizations, so realization and floating-point accumulation order are fixed.
//!
//! # Complexity
//!
//! Brute-force over the empirical distribution: with `D` distinct realizations the cost is
//! `O(D² · #nodes · max collections)`. This is meant for low-effective-dimension categorical data
//! (gates, or explicitly quantized PLS/PCA-reduced variables).

#[cfg(feature = "experimental-pipelines")]
use crate::discrete_pid::quantize_equal_width;
use crate::discrete_pid::{
    discrete_antichains_3, discrete_mi_with_budget_and_cancellation, discrete_mobius_inversion_3,
    quantization_report_heap_bytes, try_clone_quantization_report,
    try_clone_quantization_report_with_cancellation,
};
use crate::error::{PidError, PidResult};
use crate::matrix::DiscreteMatRef;
#[cfg(feature = "experimental-pipelines")]
use crate::matrix::MatRef;
use crate::quantizer::{QuantizationReport, QuantizedData};
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_filled, try_vec_with_capacity, CancellationToken,
    ResourceBudget, ResourceEstimate,
};
use crate::stats::compensated_sum;
use serde::Serialize;

const CANCELLATION_CHECK_INTERVAL: usize = 1_024;

fn check_cancellation(
    cancellation: &CancellationToken,
    operation: &'static str,
    completed_units: usize,
    total_units: usize,
) -> PidResult<()> {
    if completed_units == 0
        || completed_units == total_units
        || completed_units.is_multiple_of(CANCELLATION_CHECK_INTERVAL)
    {
        cancellation.check(operation, completed_units, total_units)?;
    }
    Ok(())
}

/// How the categorical state vectors supplied to a discrete SxPID result were obtained.
#[non_exhaustive]
#[derive(Debug, PartialEq, Eq, Serialize)]
pub enum DiscreteInputEncoding {
    /// Caller-supplied categorical labels. Only row equality is meaningful.
    Categorical,
    /// Labels produced by fixed equal-width quantizers fitted outside the evaluated rows.
    FittedEqualWidth,
}

/// Input provenance recorded on every discrete SxPID result.
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct DiscreteInputMetadata {
    /// Whether labels were supplied exactly or produced by equal-width quantization.
    pub encoding: DiscreteInputEncoding,
    /// Number of distinct multivariate row states for each source, followed by the target.
    pub observed_cardinalities: Vec<usize>,
}

/// Empirical support/occupancy diagnostics for the joint source-target PMF.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct EmpiricalPmfDiagnostics {
    pub sample_count: usize,
    pub observed_joint_states: usize,
    pub singleton_joint_states: usize,
    pub low_count_joint_states: usize,
    pub minimum_observed_count: usize,
    pub maximum_observed_count: usize,
    /// Good--Turing-style observed-coverage warning statistic `1 - f1/n`; it is not a proof of
    /// population support coverage.
    pub observed_coverage_indicator: f64,
    pub population_caveat: &'static str,
}

/// Two-source SxPID together with the fixed transforms that define its quantized estimand.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct FittedQuantizedSxPid2Result {
    pub pid: DiscreteSxPid2Result,
    pub source_quantization: [QuantizationReport; 2],
    pub target_quantization: QuantizationReport,
}

/// Three-source SxPID together with the fixed transforms that define its quantized estimand.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct FittedQuantizedSxPid3Result {
    pub pid: DiscreteSxPid3Result,
    pub source_quantization: [QuantizationReport; 3],
    pub target_quantization: QuantizationReport,
}

/// General 2--4-source SxPID plus every fixed transform defining the quantized estimand.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct FittedQuantizedSxPidNResult {
    pub pid: DiscreteSxPidNResult,
    pub source_quantization: Vec<QuantizationReport>,
    pub target_quantization: QuantizationReport,
}

/// A single shared-exclusions PID atom: the informative (`π⁺`) and misinformative (`π⁻`) parts
/// and their net `π = π⁺ − π⁻`. All in nats.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct SxAtom {
    pub informative: f64,
    pub misinformative: f64,
    pub net: f64,
}

/// One pointwise (per-realization) decomposition for the 2-source lattice.
///
/// `s1`, `s2`, `t` are the categorical realization labels; `prob` its empirical probability. Atoms
/// are ordered as the 2-source lattice: unique-1 `{{1}}`, unique-2 `{{2}}`, synergy `{{1,2}}`,
/// redundancy `{{1},{2}}`.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct SxPointwise2 {
    pub s1: Vec<usize>,
    pub s2: Vec<usize>,
    pub t: Vec<usize>,
    pub prob: f64,
    pub unq1: SxAtom,
    pub unq2: SxAtom,
    pub syn: SxAtom,
    pub red: SxAtom,
}

/// Result of a discrete 2-source shared-exclusions PID.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct DiscreteSxPid2Result {
    /// One entry per distinct realization (the signature pointwise output of SxPID).
    pub pointwise: Vec<SxPointwise2>,
    pub pointwise_included: bool,
    /// Probability-weighted (averaged) atoms.
    pub unq1: SxAtom,
    pub unq2: SxAtom,
    pub syn: SxAtom,
    pub red: SxAtom,
    /// MI terms (nats), for the reconstruction / self-redundancy identities.
    pub mi_s1_t: f64,
    pub mi_s2_t: f64,
    pub mi_s1s2_t: f64,
    /// Categorical/quantized input provenance and observed state counts.
    pub input: DiscreteInputMetadata,
    pub empirical_pmf: EmpiricalPmfDiagnostics,
}

/// One pointwise decomposition for the 3-source lattice (18 antichains, in the canonical
/// `discrete_antichains_3` order).
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct SxPointwise3 {
    pub s0: Vec<usize>,
    pub s1: Vec<usize>,
    pub s2: Vec<usize>,
    pub t: Vec<usize>,
    pub prob: f64,
    pub atoms: Vec<SxAtom>,
}

/// Result of a discrete 3-source shared-exclusions PID.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct DiscreteSxPid3Result {
    pub pointwise: Vec<SxPointwise3>,
    pub pointwise_included: bool,
    /// The 18 antichains (as set-lists of bitmasks), aligned with `atoms`.
    pub antichains: Vec<Vec<u8>>,
    /// Averaged atoms, aligned with `antichains`.
    pub atoms: Vec<SxAtom>,
    pub mi_s0_t: f64,
    pub mi_s1_t: f64,
    pub mi_s2_t: f64,
    pub mi_s0s1s2_t: f64,
    /// Mutual information for every non-empty source subset. Index `mask - 1` corresponds to the
    /// source bitmask `mask` (`1..=7`) and equals the sum of atoms in that node's down-set.
    pub subset_mis: Vec<f64>,
    /// Categorical/quantized input provenance and observed state counts.
    pub input: DiscreteInputMetadata,
    pub empirical_pmf: EmpiricalPmfDiagnostics,
}

impl DiscreteSxPid3Result {
    /// Look up the averaged atom for an antichain given as a slice of bitmasks (e.g. `&[0b001,
    /// 0b010, 0b100]` for `{{0},{1},{2}}`). Order-insensitive.
    pub fn atom(&self, sets: &[u8]) -> Option<SxAtom> {
        self.antichains
            .iter()
            .position(|antichain| unordered_masks_equal(antichain, sets))
            .map(|i| self.atoms[i])
    }
}

fn unordered_masks_equal(canonical: &[u8], candidate: &[u8]) -> bool {
    canonical.len() == candidate.len()
        && candidate
            .iter()
            .enumerate()
            .all(|(index, mask)| !candidate[..index].contains(mask))
        && canonical.iter().all(|mask| candidate.contains(mask))
}

// ----------------------------------------------------------------------------------------------
// Core primitives
// ----------------------------------------------------------------------------------------------

#[derive(Clone, Copy, Default)]
struct NeumaierAccumulator {
    sum: f64,
    correction: f64,
}

impl NeumaierAccumulator {
    fn add(&mut self, value: f64) {
        let next = self.sum + value;
        if self.sum.abs() >= value.abs() {
            self.correction += (self.sum - next) + value;
        } else {
            self.correction += (value - next) + self.sum;
        }
        self.sum = next;
    }

    fn total(self) -> f64 {
        self.sum + self.correction
    }
}

/// Empirical joint PMF counts over distinct realizations in deterministic lexicographic order.
/// Keeping integer mass lets event probabilities sum exactly before their single division.
struct EmpiricalPmf {
    entries: Vec<(Vec<Vec<usize>>, usize)>,
    sample_count: usize,
}

impl EmpiricalPmf {
    fn probability(&self, count: usize) -> f64 {
        count as f64 / self.sample_count as f64
    }

    fn event_probability_with_cancellation(
        &self,
        cancellation: &CancellationToken,
        mut includes: impl FnMut(&[Vec<usize>]) -> bool,
    ) -> PidResult<f64> {
        const OPERATION: &str = "categorical empirical event mass";
        let mut count = 0usize;
        cancellation.check(OPERATION, 0, self.entries.len())?;
        for (index, (realization, mass)) in self.entries.iter().enumerate() {
            check_cancellation(cancellation, OPERATION, index, self.entries.len())?;
            if includes(realization) {
                count = count.checked_add(*mass).ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
            }
        }
        cancellation.check(OPERATION, self.entries.len(), self.entries.len())?;
        if count > self.sample_count {
            return Err(PidError::NumericalInstability {
                context: "categorical empirical event mass exceeds sample count",
            });
        }
        Ok(self.probability(count))
    }

    fn diagnostics_with_cancellation(
        &self,
        cancellation: &CancellationToken,
    ) -> PidResult<EmpiricalPmfDiagnostics> {
        const OPERATION: &str = "categorical empirical PMF diagnostics";
        cancellation.check(OPERATION, 0, self.entries.len())?;
        let mut singleton_joint_states = 0usize;
        let mut low_count_joint_states = 0usize;
        let mut minimum_observed_count = usize::MAX;
        let mut maximum_observed_count = 0usize;
        for (index, (_, count)) in self.entries.iter().enumerate() {
            check_cancellation(cancellation, OPERATION, index, self.entries.len())?;
            singleton_joint_states += usize::from(*count == 1);
            low_count_joint_states += usize::from(*count <= 5);
            minimum_observed_count = minimum_observed_count.min(*count);
            maximum_observed_count = maximum_observed_count.max(*count);
        }
        cancellation.check(OPERATION, self.entries.len(), self.entries.len())?;
        Ok(EmpiricalPmfDiagnostics {
            sample_count: self.sample_count,
            observed_joint_states: self.entries.len(),
            singleton_joint_states,
            low_count_joint_states,
            minimum_observed_count: if self.entries.is_empty() {
                0
            } else {
                minimum_observed_count
            },
            maximum_observed_count,
            observed_coverage_indicator: 1.0
                - singleton_joint_states as f64 / self.sample_count as f64,
            population_caveat: "direct evaluation on the empirical categorical PMF; unseen population states have empirical probability zero and plug-in bias remains",
        })
    }
}

/// `var_states[v]` is variable `v`'s per-sample categorical state vector; the last variable is
/// the target.
#[cfg(test)]
fn build_pmf(var_states: &[&[Vec<usize>]], budget: ResourceBudget) -> PidResult<EmpiricalPmf> {
    let cancellation = CancellationToken::new();
    build_pmf_with_cancellation(var_states, budget, &cancellation)
}

fn build_pmf_with_cancellation(
    var_states: &[&[Vec<usize>]],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<EmpiricalPmf> {
    const OPERATION: &str = "categorical empirical PMF";
    let n = var_states[0].len();
    if n as u128 > (1_u128 << 53) {
        return Err(PidError::SampleCountPrecisionExceeded {
            operation: OPERATION,
            sample_count: n as u128,
            maximum_exact_sample_count: 1_u128 << 53,
        });
    }
    let mut order = try_vec_with_capacity(OPERATION, n, budget)?;
    cancellation.check(OPERATION, 0, n)?;
    for index in 0..n {
        check_cancellation(cancellation, OPERATION, index, n)?;
        order.push(index);
    }
    sort_unstable_by_with_cancellation(OPERATION, &mut order, cancellation, |&left, &right| {
        var_states
            .iter()
            .map(|states| states[left].cmp(&states[right]))
            .find(|ordering| !ordering.is_eq())
            .unwrap_or(std::cmp::Ordering::Equal)
    })?;

    let mut entries = try_vec_with_capacity(OPERATION, n, budget)?;
    let mut cursor = 0;
    while cursor < order.len() {
        check_cancellation(cancellation, OPERATION, cursor, order.len())?;
        let representative = order[cursor];
        let mut next = cursor + 1;
        while next < order.len()
            && var_states
                .iter()
                .all(|states| states[order[next]] == states[representative])
        {
            check_cancellation(cancellation, OPERATION, next, order.len())?;
            next += 1;
        }
        let count = next.checked_sub(cursor).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
        entries.push((
            clone_realization_with_cancellation(
                var_states,
                representative,
                OPERATION,
                budget,
                cancellation,
            )?,
            count,
        ));
        cursor = next;
    }
    cancellation.check(OPERATION, order.len(), order.len())?;
    Ok(EmpiricalPmf {
        entries,
        sample_count: n,
    })
}

fn clone_realization_with_cancellation(
    var_states: &[&[Vec<usize>]],
    row: usize,
    operation: &'static str,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<usize>>> {
    let total_units = var_states.iter().try_fold(0usize, |total, states| {
        total
            .checked_add(states[row].len())
            .ok_or(PidError::SizeOverflow { operation })
    })?;
    let mut completed_units = 0usize;
    cancellation.check(operation, 0, total_units)?;
    let mut realization = try_vec_with_capacity(operation, var_states.len(), budget)?;
    for states in var_states {
        let source = states[row].as_slice();
        let mut state = try_vec_with_capacity(operation, source.len(), budget)?;
        for chunk in source.chunks(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(operation, completed_units, total_units)?;
            state.extend_from_slice(chunk);
            completed_units = completed_units
                .checked_add(chunk.len())
                .ok_or(PidError::SizeOverflow { operation })?;
        }
        realization.push(state);
    }
    cancellation.check(operation, completed_units, total_units)?;
    Ok(realization)
}

fn clone_state_with_cancellation(
    state: &[usize],
    operation: &'static str,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<usize>> {
    let mut copy = try_vec_with_capacity(operation, state.len(), budget)?;
    cancellation.check(operation, 0, state.len())?;
    for (chunk_index, chunk) in state.chunks(CANCELLATION_CHECK_INTERVAL).enumerate() {
        cancellation.check(
            operation,
            chunk_index.saturating_mul(CANCELLATION_CHECK_INTERVAL),
            state.len(),
        )?;
        copy.extend_from_slice(chunk);
    }
    cancellation.check(operation, state.len(), state.len())?;
    Ok(copy)
}

fn clone_owned_realization_with_cancellation(
    realization: &[Vec<usize>],
    operation: &'static str,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<usize>>> {
    let mut copy = try_vec_with_capacity(operation, realization.len(), budget)?;
    for state in realization {
        copy.push(clone_state_with_cancellation(
            state,
            operation,
            budget,
            cancellation,
        )?);
    }
    Ok(copy)
}

/// Marginal probability of the event "agrees with `rlz` on the source indices in `source_mask`
/// (and on the target if `with_target`)".
#[cfg(test)]
fn marg(
    pmf: &EmpiricalPmf,
    rlz: &[Vec<usize>],
    source_mask: u32,
    n_sources: usize,
    with_target: bool,
) -> PidResult<f64> {
    let cancellation = CancellationToken::new();
    marg_with_cancellation(pmf, rlz, source_mask, n_sources, with_target, &cancellation)
}

fn marg_with_cancellation(
    pmf: &EmpiricalPmf,
    rlz: &[Vec<usize>],
    source_mask: u32,
    n_sources: usize,
    with_target: bool,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    pmf.event_probability_with_cancellation(cancellation, |cand| {
        let mut ok = true;
        for src in 0..n_sources {
            if source_mask & (1 << src) != 0 && cand[src] != rlz[src] {
                ok = false;
                break;
            }
        }
        if ok && with_target && cand[n_sources] != rlz[n_sources] {
            ok = false;
        }
        ok
    })
}

/// `P(⋃_j 𝔞_j)` (optionally intersected with the target event), evaluated directly over the
/// empirical support. Each collection is a source bitmask.
#[cfg(test)]
fn union_prob(
    pmf: &EmpiricalPmf,
    rlz: &[Vec<usize>],
    collections: &[u8],
    n_sources: usize,
    with_target: bool,
) -> PidResult<f64> {
    let cancellation = CancellationToken::new();
    union_prob_with_cancellation(pmf, rlz, collections, n_sources, with_target, &cancellation)
}

fn union_prob_with_cancellation(
    pmf: &EmpiricalPmf,
    rlz: &[Vec<usize>],
    collections: &[u8],
    n_sources: usize,
    with_target: bool,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    pmf.event_probability_with_cancellation(cancellation, |cand| {
        if with_target && cand[n_sources] != rlz[n_sources] {
            return false;
        }
        collections.iter().any(|&collection| {
            (0..n_sources).all(|src| collection & (1 << src) == 0 || cand[src] == rlz[src])
        })
    })
}

fn input_metadata_with_cancellation(
    vars: &[&[Vec<usize>]],
    encoding: DiscreteInputEncoding,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteInputMetadata> {
    const OPERATION: &str = "categorical input metadata";
    let mut observed_cardinalities = try_vec_with_capacity(OPERATION, vars.len(), budget)?;
    for rows in vars {
        let mut states = try_vec_with_capacity(OPERATION, rows.len(), budget)?;
        cancellation.check(OPERATION, 0, rows.len())?;
        for (index, row) in rows.iter().enumerate() {
            check_cancellation(cancellation, OPERATION, index, rows.len())?;
            states.push(row.as_slice());
        }
        sort_unstable_by_with_cancellation(OPERATION, &mut states, cancellation, |left, right| {
            left.cmp(right)
        })?;
        let mut cardinality = 0usize;
        let mut previous: Option<&[usize]> = None;
        for (index, &state) in states.iter().enumerate() {
            check_cancellation(cancellation, OPERATION, index, states.len())?;
            if previous != Some(state) {
                cardinality = cardinality.checked_add(1).ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
                previous = Some(state);
            }
        }
        cancellation.check(OPERATION, states.len(), states.len())?;
        observed_cardinalities.push(cardinality);
    }
    Ok(DiscreteInputMetadata {
        encoding,
        observed_cardinalities,
    })
}

fn states_from_discrete(
    mat: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<usize>>> {
    let cancellation = CancellationToken::new();
    states_from_discrete_with_cancellation(mat, budget, &cancellation)
}

fn states_from_discrete_with_cancellation(
    mat: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<usize>>> {
    const OPERATION: &str = "categorical state materialization";
    let total_units = mat
        .nrows()
        .checked_mul(mat.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    cancellation.check(OPERATION, 0, total_units)?;
    let mut completed_units = 0usize;
    let mut states = try_vec_with_capacity(OPERATION, mat.nrows(), budget)?;
    for row in 0..mat.nrows() {
        let mut state = try_vec_with_capacity(OPERATION, mat.ncols(), budget)?;
        for chunk in mat.row(row).chunks(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(OPERATION, completed_units, total_units)?;
            state.extend_from_slice(chunk);
            completed_units =
                completed_units
                    .checked_add(chunk.len())
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
        }
        states.push(state);
    }
    cancellation.check(OPERATION, completed_units, total_units)?;
    Ok(states)
}

fn checked_resource_add(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_add(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn checked_resource_mul(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_mul(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn add_sxpid_estimate_bytes(
    operation: &'static str,
    estimate: ResourceEstimate,
    extra_bytes: u128,
) -> PidResult<ResourceEstimate> {
    Ok(ResourceEstimate {
        estimated_bytes: checked_resource_add(operation, estimate.estimated_bytes, extra_bytes)?,
        pairwise_distances: estimate.pairwise_distances,
        operations_hint: estimate.operations_hint,
    })
}

fn quantization_reports_heap_bytes(
    operation: &'static str,
    reports: &[&QuantizationReport],
) -> PidResult<u128> {
    reports.iter().try_fold(0u128, |sum, report| {
        checked_resource_add(
            operation,
            sum,
            quantization_report_heap_bytes(operation, report)?,
        )
    })
}

fn sxpid_ceil_log2(value: usize) -> u128 {
    if value <= 1 {
        1
    } else {
        (usize::BITS - (value - 1).leading_zeros()) as u128
    }
}

fn sxpid_resource_estimate_impl(
    operation: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    include_pointwise: bool,
) -> PidResult<ResourceEstimate> {
    if !(2..=4).contains(&sources.len()) {
        return Err(PidError::NotImplemented {
            feature: "categorical SxPID resource estimates support 2..=4 sources",
        });
    }
    let n_rows = target.nrows();
    if n_rows == 0 {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "need at least 1 sample (got 0 rows)",
        });
    }
    if target.ncols() == 0 || sources.iter().any(|source| source.ncols() == 0) {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "categorical variables must have at least 1 column",
        });
    }
    for source in sources {
        if source.nrows() != n_rows {
            return Err(PidError::RowCountMismatch {
                context: operation,
                left_rows: n_rows,
                right_rows: source.nrows(),
            });
        }
    }
    if n_rows as u128 > (1_u128 << 53) {
        return Err(PidError::SampleCountPrecisionExceeded {
            operation,
            sample_count: n_rows as u128,
            maximum_exact_sample_count: 1_u128 << 53,
        });
    }

    let n = n_rows as u128;
    let n_sources = sources.len() as u128;
    let variable_count = n_sources + 1;
    let source_coordinates = sources.iter().try_fold(0u128, |sum, source| {
        checked_resource_add(operation, sum, source.ncols() as u128)
    })?;
    let coordinates = checked_resource_add(operation, source_coordinates, target.ncols() as u128)?;
    let usize_bytes = std::mem::size_of::<usize>() as u128;
    let vec_header = std::mem::size_of::<Vec<usize>>() as u128;
    let slice_reference = std::mem::size_of::<&[usize]>() as u128;

    let state_payload = checked_resource_mul(
        operation,
        checked_resource_mul(operation, n, coordinates)?,
        usize_bytes,
    )?;
    let state_headers = checked_resource_mul(
        operation,
        checked_resource_mul(operation, n, variable_count)?,
        vec_header,
    )?;
    let materialized_states = checked_resource_add(operation, state_payload, state_headers)?;

    // PMF entries retain one nested realization per distinct state; D <= n, so D=n is the safe
    // public preflight. This includes tuple/vector headers as well as categorical coordinates.
    let pmf_entry_bytes = [
        std::mem::size_of::<(Vec<Vec<usize>>, usize)>() as u128,
        checked_resource_mul(operation, variable_count, vec_header)?,
        checked_resource_mul(operation, coordinates, usize_bytes)?,
    ]
    .into_iter()
    .try_fold(0u128, |sum, bytes| {
        checked_resource_add(operation, sum, bytes)
    })?;
    let pmf_bytes = checked_resource_add(
        operation,
        checked_resource_mul(operation, n, usize_bytes)?,
        checked_resource_mul(operation, n, pmf_entry_bytes)?,
    )?;

    // Each subset MI builds joined rows and three sorted borrowed-key histograms. Count every
    // repeated construction so the estimate includes allocation exposure, not only raw payload.
    let subset_count = (1u128 << sources.len()) - 1;
    let joined_subset_bytes = checked_resource_add(
        operation,
        checked_resource_mul(
            operation,
            checked_resource_mul(operation, n, source_coordinates)?,
            usize_bytes,
        )?,
        checked_resource_mul(operation, n, vec_header)?,
    )?;
    let histogram_entry = checked_resource_add(
        operation,
        std::mem::size_of::<(&[usize], &[usize])>() as u128,
        checked_resource_mul(operation, 2, usize_bytes)?,
    )?;
    let histogram_bytes = checked_resource_add(
        operation,
        checked_resource_mul(operation, n, usize_bytes)?,
        checked_resource_mul(operation, n, histogram_entry)?,
    )?;
    let repeated_subset_working = checked_resource_mul(
        operation,
        subset_count,
        checked_resource_add(
            operation,
            joined_subset_bytes,
            checked_resource_mul(operation, 3, histogram_bytes)?,
        )?,
    )?;
    let metadata_sort_bytes = checked_resource_mul(
        operation,
        checked_resource_mul(operation, variable_count, n)?,
        slice_reference,
    )?;

    let (lattice_nodes, max_collections) = match sources.len() {
        2 => (4u128, 2u128),
        3 => (18u128, 3u128),
        4 => (166u128, 6u128),
        _ => {
            return Err(PidError::NotImplemented {
                feature: "categorical SxPID resource estimates support 2..=4 sources",
            });
        }
    };
    let lattice_working = [
        checked_resource_mul(
            operation,
            lattice_nodes,
            std::mem::size_of::<Vec<u8>>() as u128,
        )?,
        checked_resource_mul(
            operation,
            lattice_nodes,
            std::mem::size_of::<[NeumaierAccumulator; 2]>() as u128,
        )?,
        checked_resource_mul(
            operation,
            checked_resource_mul(operation, lattice_nodes, 6)?,
            std::mem::size_of::<f64>() as u128,
        )?,
        checked_resource_mul(
            operation,
            checked_resource_mul(operation, lattice_nodes, 3)?,
            usize_bytes,
        )?,
    ]
    .into_iter()
    .try_fold(0u128, |sum, bytes| {
        checked_resource_add(operation, sum, bytes)
    })?;

    let pointwise_bytes = if include_pointwise {
        let per_realization = [
            std::mem::size_of::<SxPointwiseN>() as u128,
            checked_resource_mul(operation, variable_count, vec_header)?,
            checked_resource_mul(operation, coordinates, usize_bytes)?,
            checked_resource_mul(
                operation,
                lattice_nodes,
                std::mem::size_of::<SxAtom>() as u128,
            )?,
        ]
        .into_iter()
        .try_fold(0u128, |sum, bytes| {
            checked_resource_add(operation, sum, bytes)
        })?;
        checked_resource_mul(operation, n, per_realization)?
    } else {
        0
    };

    let estimated_bytes = [
        materialized_states,
        pmf_bytes,
        repeated_subset_working,
        metadata_sort_bytes,
        lattice_working,
        pointwise_bytes,
    ]
    .into_iter()
    .try_fold(0u128, |sum, bytes| {
        checked_resource_add(operation, sum, bytes)
    })?;

    let event_scans = checked_resource_mul(
        operation,
        checked_resource_mul(operation, n, n)?,
        checked_resource_mul(
            operation,
            lattice_nodes,
            checked_resource_mul(
                operation,
                2,
                checked_resource_mul(operation, max_collections, n_sources)?,
            )?,
        )?,
    )?;
    let mobius_work = checked_resource_mul(
        operation,
        n,
        checked_resource_mul(operation, lattice_nodes, lattice_nodes)?,
    )?;
    let histogram_work = checked_resource_mul(
        operation,
        checked_resource_mul(operation, subset_count, n)?,
        checked_resource_mul(operation, sxpid_ceil_log2(n_rows), coordinates.max(1))?,
    )?;
    let operations_hint = checked_resource_add(
        operation,
        checked_resource_add(operation, event_scans, mobius_work)?,
        histogram_work,
    )?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances: 0,
        operations_hint,
    })
}

fn validate_discrete_mats(
    context: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    include_pointwise: bool,
) -> PidResult<()> {
    if sources.is_empty() {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least one source",
        });
    }
    let n = target.nrows();
    if n == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least 1 sample (got 0 rows)",
        });
    }
    if target.ncols() == 0 || sources.iter().any(|source| source.ncols() == 0) {
        return Err(PidError::InvalidConfig {
            context,
            message: "categorical variables must have at least 1 column",
        });
    }
    for source in sources {
        if source.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context,
                left_rows: n,
                right_rows: source.nrows(),
            });
        }
    }
    let estimate = sxpid_resource_estimate_impl(context, sources, target, include_pointwise)?;
    budget.check(context, estimate)
}

#[cfg(feature = "experimental-pipelines")]
fn validate_quantized_mats(
    context: &'static str,
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<()> {
    if num_bins < 2 {
        return Err(PidError::InvalidConfig {
            context,
            message: "num_bins must be >= 2",
        });
    }
    if sources.is_empty() {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least one source",
        });
    }
    let n = target.nrows();
    if n == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least 1 sample (got 0 rows)",
        });
    }
    if target.ncols() == 0 || sources.iter().any(|source| source.ncols() == 0) {
        return Err(PidError::InvalidConfig {
            context,
            message: "variables must have at least 1 column",
        });
    }
    for source in sources {
        if source.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context,
                left_rows: n,
                right_rows: source.nrows(),
            });
        }
    }
    Ok(())
}

/// The two cumulative terms `(i⁺, i⁻)` for one antichain node at one realization. Their net is
/// formed as `i⁺ - i⁻`, so the public net identity holds by construction.
#[cfg(test)]
fn node_terms(
    pmf: &EmpiricalPmf,
    rlz: &[Vec<usize>],
    collections: &[u8],
    n_sources: usize,
    p_t: f64,
) -> PidResult<(f64, f64)> {
    let cancellation = CancellationToken::new();
    node_terms_with_cancellation(pmf, rlz, collections, n_sources, p_t, &cancellation)
}

fn node_terms_with_cancellation(
    pmf: &EmpiricalPmf,
    rlz: &[Vec<usize>],
    collections: &[u8],
    n_sources: usize,
    p_t: f64,
    cancellation: &CancellationToken,
) -> PidResult<(f64, f64)> {
    let p_union =
        union_prob_with_cancellation(pmf, rlz, collections, n_sources, false, cancellation)?;
    let p_t_union =
        union_prob_with_cancellation(pmf, rlz, collections, n_sources, true, cancellation)?;
    // The realization itself lies in every collection-event, so all three probabilities are >0
    // for any positive-mass realization. Guard defensively against accumulated round-off anyway.
    if !(p_t > 0.0 && p_union > 0.0 && p_t_union > 0.0) {
        return Err(PidError::NumericalInstability {
            context: "sxpid: degenerate union/target probability (non-positive)",
        });
    }
    let i_plus = -p_union.ln();
    let i_minus = (p_t / p_t_union).ln();
    Ok((i_plus, i_minus))
}

// ----------------------------------------------------------------------------------------------
// 2-source
// ----------------------------------------------------------------------------------------------

/// 2-source lattice nodes in the canonical order `[unq1, unq2, syn, red]`, each a list of source
/// collections (bitmasks over `{0,1}`).
const NODES2: [&[u8]; 4] = [&[0b01], &[0b10], &[0b11], &[0b01, 0b10]];

/// Explicit Möbius inversion of a length-4 cumulative vector (`[unq1, unq2, syn, red]` order) into
/// atoms. The lattice: `red` is the bottom; `unq1`, `unq2` cover `red`; `syn` is the top.
#[inline]
fn invert2(cum: [f64; 4]) -> [f64; 4] {
    let red = cum[3];
    let unq1 = compensated_sum([cum[0], -red]);
    let unq2 = compensated_sum([cum[1], -red]);
    let syn = compensated_sum([cum[2], -unq1, -unq2, -red]);
    [unq1, unq2, syn, red]
}

/// Discrete 2-source shared-exclusions PID (`i^sx_∩`).
///
/// Inputs are categorical state labels. Numeric spacing has no meaning: sparse IDs and any
/// bijective relabeling produce the same decomposition. For continuous measurements, fit and
/// apply [`crate::stable::quantized::EqualWidthQuantizer`] on training/evaluation rows explicitly,
/// then pass the resulting categorical matrices here.
///
/// # Example
/// ```
/// use pid_core::{stable::categorical::discrete_sxpid2, DiscreteMatRef};
/// // XOR gate (T = S1 xor S2). Unlike I_min, the shared-exclusions redundancy is NEGATIVE here
/// // (its signature "misinformative" content), while the atoms still reconstruct the joint MI.
/// let s1 = [0, 0, 1, 1];
/// let s2 = [0, 1, 0, 1];
/// let t  = [0, 1, 1, 0];
/// let s1 = DiscreteMatRef::new(&s1, 4, 1)?;
/// let s2 = DiscreteMatRef::new(&s2, 4, 1)?;
/// let t  = DiscreteMatRef::new(&t, 4, 1)?;
/// let r = discrete_sxpid2(s1, s2, t)?; // values in nats
/// assert!((r.red.net - (2.0_f64 / 3.0).ln()).abs() < 1e-9); // ln(2/3) < 0
/// assert!((r.syn.net - (4.0_f64 / 3.0).ln()).abs() < 1e-9); // ln(4/3)
/// assert!((r.unq1.net - 1.5_f64.ln()).abs() < 1e-9);        // ln(3/2)
/// // Reconstruction: Red + Unq1 + Unq2 + Syn = I(S1,S2;T) = ln 2.
/// let sum = r.red.net + r.unq1.net + r.unq2.net + r.syn.net;
/// assert!((sum - 2.0_f64.ln()).abs() < 1e-9);
/// # Ok::<(), pid_core::PidError>(())
/// ```
pub fn discrete_sxpid2(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPid2Result> {
    discrete_sxpid2_with_budget(s1, s2, target, ResourceBudget::default())
}

/// Worst-case distinct-state resource estimate for [`discrete_sxpid2`].
pub fn discrete_sxpid2_resource_estimate(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    include_pointwise: bool,
) -> PidResult<ResourceEstimate> {
    sxpid_resource_estimate_impl("discrete_sxpid2", &[s1, s2], target, include_pointwise)
}

/// [`discrete_sxpid2`] with an explicit allocation and operation ceiling.
pub fn discrete_sxpid2_with_budget(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPid2Result> {
    validate_discrete_mats("discrete_sxpid2", &[s1, s2], target, budget, true)?;
    let s1_states = states_from_discrete(s1, budget)?;
    let s2_states = states_from_discrete(s2, budget)?;
    let target_states = states_from_discrete(target, budget)?;
    sxpid2_from_states(
        &s1_states,
        &s2_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
        true,
        budget,
    )
}

/// Compute only averaged 2-source atoms, avoiding pointwise-result materialization.
pub fn discrete_sxpid2_averaged(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPid2Result> {
    discrete_sxpid2_averaged_with_budget(s1, s2, target, ResourceBudget::default())
}

/// [`discrete_sxpid2_averaged`] with an explicit allocation and operation ceiling.
pub fn discrete_sxpid2_averaged_with_budget(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPid2Result> {
    let cancellation = CancellationToken::new();
    discrete_sxpid2_averaged_with_budget_and_cancellation(s1, s2, target, budget, &cancellation)
}

/// [`discrete_sxpid2_averaged_with_budget`] with cooperative cancellation throughout categorical
/// materialization, empirical-PMF construction, and shared-exclusion event scans.
pub fn discrete_sxpid2_averaged_with_budget_and_cancellation(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteSxPid2Result> {
    const OPERATION: &str = "discrete_sxpid2_averaged";
    validate_discrete_mats("discrete_sxpid2_averaged", &[s1, s2], target, budget, false)?;
    cancellation.check(OPERATION, 0, target.nrows())?;
    sxpid2_from_states_with_cancellation(
        &states_from_discrete_with_cancellation(s1, budget, cancellation)?,
        &states_from_discrete_with_cancellation(s2, budget, cancellation)?,
        &states_from_discrete_with_cancellation(target, budget, cancellation)?,
        DiscreteInputEncoding::Categorical,
        false,
        budget,
        cancellation,
    )
}

/// Evaluate averaged two-source SxPID while retaining the fitted quantizers that define the
/// quantized variables.
pub fn fitted_quantized_sxpid2(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<FittedQuantizedSxPid2Result> {
    fitted_quantized_sxpid2_with_budget(s1, s2, target, ResourceBudget::default())
}

/// Resource preflight for [`fitted_quantized_sxpid2`], including copied quantizer reports.
pub fn fitted_quantized_sxpid2_resource_estimate(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "fitted_quantized_sxpid2";
    let estimate = sxpid_resource_estimate_impl(
        OPERATION,
        &[s1.matrix.as_ref(), s2.matrix.as_ref()],
        target.matrix.as_ref(),
        false,
    )?;
    add_sxpid_estimate_bytes(
        OPERATION,
        estimate,
        quantization_reports_heap_bytes(OPERATION, &[&s1.report, &s2.report, &target.report])?,
    )
}

/// [`fitted_quantized_sxpid2`] with an explicit allocation and operation ceiling.
pub fn fitted_quantized_sxpid2_with_budget(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
    budget: ResourceBudget,
) -> PidResult<FittedQuantizedSxPid2Result> {
    let cancellation = CancellationToken::new();
    fitted_quantized_sxpid2_with_budget_and_cancellation(s1, s2, target, budget, &cancellation)
}

/// [`fitted_quantized_sxpid2_with_budget`] with cooperative cancellation through PID evaluation
/// and fitted-quantizer report copying.
pub fn fitted_quantized_sxpid2_with_budget_and_cancellation(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<FittedQuantizedSxPid2Result> {
    const OPERATION: &str = "fitted_quantized_sxpid2";
    budget.check(
        OPERATION,
        fitted_quantized_sxpid2_resource_estimate(s1, s2, target)?,
    )?;
    cancellation.check(OPERATION, 0, target.matrix.nrows())?;
    let mut pid = discrete_sxpid2_averaged_with_budget_and_cancellation(
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
        budget,
        cancellation,
    )?;
    pid.input.encoding = DiscreteInputEncoding::FittedEqualWidth;
    Ok(FittedQuantizedSxPid2Result {
        pid,
        source_quantization: [
            try_clone_quantization_report_with_cancellation(
                OPERATION,
                &s1.report,
                budget,
                cancellation,
            )?,
            try_clone_quantization_report_with_cancellation(
                OPERATION,
                &s2.report,
                budget,
                cancellation,
            )?,
        ],
        target_quantization: try_clone_quantization_report_with_cancellation(
            OPERATION,
            &target.report,
            budget,
            cancellation,
        )?,
    })
}

/// Equal-width-quantized 2-source shared-exclusions PID for continuous inputs.
///
/// This is a preprocessing convenience, not an exact categorical estimator: results can change
/// with `num_bins` and with nonlinear rescaling of the input coordinates.
#[cfg(feature = "experimental-pipelines")]
pub fn quantized_sxpid2(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<crate::same_sample::ExploratorySameSampleQuantizedResult<DiscreteSxPid2Result>> {
    validate_quantized_mats("quantized_sxpid2", &[s1, s2], target, num_bins)?;

    let s1_bins = quantize_equal_width(s1, num_bins)?;
    let s2_bins = quantize_equal_width(s2, num_bins)?;
    let t_bins = quantize_equal_width(target, num_bins)?;

    let categorical_result = sxpid2_from_states(
        &s1_bins,
        &s2_bins,
        &t_bins,
        DiscreteInputEncoding::Categorical,
        true,
        ResourceBudget::default(),
    )?;
    Ok(crate::same_sample::ExploratorySameSampleQuantizedResult::new(categorical_result, num_bins))
}

fn sxpid2_from_states(
    s1_states: &[Vec<usize>],
    s2_states: &[Vec<usize>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
    include_pointwise: bool,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPid2Result> {
    let cancellation = CancellationToken::new();
    sxpid2_from_states_with_cancellation(
        s1_states,
        s2_states,
        target_states,
        encoding,
        include_pointwise,
        budget,
        &cancellation,
    )
}

fn sxpid2_from_states_with_cancellation(
    s1_states: &[Vec<usize>],
    s2_states: &[Vec<usize>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
    include_pointwise: bool,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteSxPid2Result> {
    const OPERATION: &str = "discrete_sxpid2";
    cancellation.check(OPERATION, 0, target_states.len())?;
    let mi_s1_t = discrete_mi_with_budget_and_cancellation(
        s1_states,
        target_states,
        0,
        budget,
        cancellation,
    )?;
    let mi_s2_t = discrete_mi_with_budget_and_cancellation(
        s2_states,
        target_states,
        0,
        budget,
        cancellation,
    )?;
    let mi_s1s2_t = discrete_mi_with_budget_and_cancellation(
        &join_pair_with_cancellation(s1_states, s2_states, budget, cancellation)?,
        target_states,
        0,
        budget,
        cancellation,
    )?;

    let vars = [s1_states, s2_states, target_states];
    let input = input_metadata_with_cancellation(&vars, encoding, budget, cancellation)?;
    let pmf = build_pmf_with_cancellation(&vars, budget, cancellation)?;
    let empirical_pmf = pmf.diagnostics_with_cancellation(cancellation)?;
    let n_sources = 2;

    let pointwise_capacity = if include_pointwise {
        pmf.entries.len()
    } else {
        0
    };
    let mut pointwise = try_vec_with_capacity(
        "discrete_sxpid2 pointwise output",
        pointwise_capacity,
        budget,
    )?;
    // Averaged accumulators for [unq1, unq2, syn, red] × (plus, minus).
    let mut avg = [[NeumaierAccumulator::default(); 2]; 4];

    for (realization_index, (rlz, count)) in pmf.entries.iter().enumerate() {
        check_cancellation(
            cancellation,
            OPERATION,
            realization_index,
            pmf.entries.len(),
        )?;
        let prob = pmf.probability(*count);
        let p_t = marg_with_cancellation(&pmf, rlz, 0, n_sources, true, cancellation)?;
        let mut cum_plus = [0.0f64; 4];
        let mut cum_minus = [0.0f64; 4];
        for (node_idx, collections) in NODES2.iter().enumerate() {
            let (ip, im) =
                node_terms_with_cancellation(&pmf, rlz, collections, n_sources, p_t, cancellation)?;
            cum_plus[node_idx] = ip;
            cum_minus[node_idx] = im;
        }
        let pi_plus = invert2(cum_plus);
        let pi_minus = invert2(cum_minus);

        let atoms: [SxAtom; 4] = std::array::from_fn(|i| SxAtom {
            informative: pi_plus[i],
            misinformative: pi_minus[i],
            net: pi_plus[i] - pi_minus[i],
        });
        for i in 0..4 {
            avg[i][0].add(prob * atoms[i].informative);
            avg[i][1].add(prob * atoms[i].misinformative);
        }

        if include_pointwise {
            pointwise.push(SxPointwise2 {
                s1: clone_state_with_cancellation(
                    &rlz[0],
                    "discrete_sxpid2 pointwise output",
                    budget,
                    cancellation,
                )?,
                s2: clone_state_with_cancellation(
                    &rlz[1],
                    "discrete_sxpid2 pointwise output",
                    budget,
                    cancellation,
                )?,
                t: clone_state_with_cancellation(
                    &rlz[2],
                    "discrete_sxpid2 pointwise output",
                    budget,
                    cancellation,
                )?,
                prob,
                unq1: atoms[0],
                unq2: atoms[1],
                syn: atoms[2],
                red: atoms[3],
            });
        }
    }
    cancellation.check(OPERATION, pmf.entries.len(), pmf.entries.len())?;

    let mk = |a: [NeumaierAccumulator; 2]| {
        let informative = a[0].total();
        let misinformative = a[1].total();
        SxAtom {
            informative,
            misinformative,
            net: informative - misinformative,
        }
    };
    Ok(DiscreteSxPid2Result {
        pointwise,
        pointwise_included: include_pointwise,
        unq1: mk(avg[0]),
        unq2: mk(avg[1]),
        syn: mk(avg[2]),
        red: mk(avg[3]),
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        input,
        empirical_pmf,
    })
}

// ----------------------------------------------------------------------------------------------
// 3-source
// ----------------------------------------------------------------------------------------------

/// Direct empirical-PMF categorical 3-source shared-exclusions PID over the 18-antichain lattice.
///
/// Only equality of complete rows matters. Continuous measurements must first be transformed with
/// a fitted [`crate::stable::quantized::EqualWidthQuantizer`].
pub fn discrete_sxpid3(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPid3Result> {
    discrete_sxpid3_with_budget(s0, s1, s2, target, ResourceBudget::default())
}

/// Worst-case distinct-state resource estimate for [`discrete_sxpid3`].
pub fn discrete_sxpid3_resource_estimate(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    include_pointwise: bool,
) -> PidResult<ResourceEstimate> {
    sxpid_resource_estimate_impl("discrete_sxpid3", &[s0, s1, s2], target, include_pointwise)
}

/// [`discrete_sxpid3`] with an explicit allocation and operation ceiling.
pub fn discrete_sxpid3_with_budget(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPid3Result> {
    validate_discrete_mats("discrete_sxpid3", &[s0, s1, s2], target, budget, true)?;
    let s0_states = states_from_discrete(s0, budget)?;
    let s1_states = states_from_discrete(s1, budget)?;
    let s2_states = states_from_discrete(s2, budget)?;
    let target_states = states_from_discrete(target, budget)?;
    sxpid3_from_states(
        &s0_states,
        &s1_states,
        &s2_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
        true,
        budget,
    )
}

/// Compute only averaged 3-source atoms, avoiding pointwise-result materialization.
pub fn discrete_sxpid3_averaged(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPid3Result> {
    discrete_sxpid3_averaged_with_budget(s0, s1, s2, target, ResourceBudget::default())
}

/// [`discrete_sxpid3_averaged`] with an explicit allocation and operation ceiling.
pub fn discrete_sxpid3_averaged_with_budget(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPid3Result> {
    let cancellation = CancellationToken::new();
    discrete_sxpid3_averaged_with_budget_and_cancellation(s0, s1, s2, target, budget, &cancellation)
}

/// [`discrete_sxpid3_averaged_with_budget`] with cooperative cancellation throughout categorical
/// materialization, empirical-PMF construction, and lattice event scans.
pub fn discrete_sxpid3_averaged_with_budget_and_cancellation(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteSxPid3Result> {
    const OPERATION: &str = "discrete_sxpid3_averaged";
    validate_discrete_mats(
        "discrete_sxpid3_averaged",
        &[s0, s1, s2],
        target,
        budget,
        false,
    )?;
    cancellation.check(OPERATION, 0, target.nrows())?;
    sxpid3_from_states_with_cancellation(
        [
            &states_from_discrete_with_cancellation(s0, budget, cancellation)?,
            &states_from_discrete_with_cancellation(s1, budget, cancellation)?,
            &states_from_discrete_with_cancellation(s2, budget, cancellation)?,
        ],
        &states_from_discrete_with_cancellation(target, budget, cancellation)?,
        DiscreteInputEncoding::Categorical,
        false,
        budget,
        cancellation,
    )
}

/// Evaluate averaged three-source SxPID while retaining every fitted quantizer report.
pub fn fitted_quantized_sxpid3(
    s0: &QuantizedData,
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<FittedQuantizedSxPid3Result> {
    fitted_quantized_sxpid3_with_budget(s0, s1, s2, target, ResourceBudget::default())
}

/// Resource preflight for [`fitted_quantized_sxpid3`], including copied quantizer reports.
pub fn fitted_quantized_sxpid3_resource_estimate(
    s0: &QuantizedData,
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "fitted_quantized_sxpid3";
    let estimate = sxpid_resource_estimate_impl(
        OPERATION,
        &[s0.matrix.as_ref(), s1.matrix.as_ref(), s2.matrix.as_ref()],
        target.matrix.as_ref(),
        false,
    )?;
    add_sxpid_estimate_bytes(
        OPERATION,
        estimate,
        quantization_reports_heap_bytes(
            OPERATION,
            &[&s0.report, &s1.report, &s2.report, &target.report],
        )?,
    )
}

/// [`fitted_quantized_sxpid3`] with an explicit allocation and operation ceiling.
pub fn fitted_quantized_sxpid3_with_budget(
    s0: &QuantizedData,
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
    budget: ResourceBudget,
) -> PidResult<FittedQuantizedSxPid3Result> {
    const OPERATION: &str = "fitted_quantized_sxpid3";
    budget.check(
        OPERATION,
        fitted_quantized_sxpid3_resource_estimate(s0, s1, s2, target)?,
    )?;
    let mut pid = discrete_sxpid3_averaged_with_budget(
        s0.matrix.as_ref(),
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
        budget,
    )?;
    pid.input.encoding = DiscreteInputEncoding::FittedEqualWidth;
    Ok(FittedQuantizedSxPid3Result {
        pid,
        source_quantization: [
            try_clone_quantization_report(OPERATION, &s0.report, budget)?,
            try_clone_quantization_report(OPERATION, &s1.report, budget)?,
            try_clone_quantization_report(OPERATION, &s2.report, budget)?,
        ],
        target_quantization: try_clone_quantization_report(OPERATION, &target.report, budget)?,
    })
}

/// Equal-width-quantized 3-source shared-exclusions PID for continuous inputs.
#[cfg(feature = "experimental-pipelines")]
pub fn quantized_sxpid3(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<crate::same_sample::ExploratorySameSampleQuantizedResult<DiscreteSxPid3Result>> {
    validate_quantized_mats("quantized_sxpid3", &[s0, s1, s2], target, num_bins)?;
    let s0_states = quantize_equal_width(s0, num_bins)?;
    let s1_states = quantize_equal_width(s1, num_bins)?;
    let s2_states = quantize_equal_width(s2, num_bins)?;
    let target_states = quantize_equal_width(target, num_bins)?;
    let categorical_result = sxpid3_from_states(
        &s0_states,
        &s1_states,
        &s2_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
        true,
        ResourceBudget::default(),
    )?;
    Ok(crate::same_sample::ExploratorySameSampleQuantizedResult::new(categorical_result, num_bins))
}

fn sxpid3_from_states(
    s0_states: &[Vec<usize>],
    s1_states: &[Vec<usize>],
    s2_states: &[Vec<usize>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
    include_pointwise: bool,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPid3Result> {
    let cancellation = CancellationToken::new();
    sxpid3_from_states_with_cancellation(
        [s0_states, s1_states, s2_states],
        target_states,
        encoding,
        include_pointwise,
        budget,
        &cancellation,
    )
}

fn sxpid3_from_states_with_cancellation(
    source_states: [&[Vec<usize>]; 3],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
    include_pointwise: bool,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteSxPid3Result> {
    const OPERATION: &str = "discrete_sxpid3";
    cancellation.check(OPERATION, 0, target_states.len())?;
    let [s0_states, s1_states, s2_states] = source_states;
    let subset_mis = subset_mutual_information_with_cancellation(
        &[s0_states, s1_states, s2_states],
        target_states,
        budget,
        cancellation,
    )?;
    let mi_s0_t = subset_mis[0];
    let mi_s1_t = subset_mis[1];
    let mi_s2_t = subset_mis[3];
    let mi_s0s1s2_t = subset_mis[6];

    let antichains = discrete_antichains_3();
    // Each antichain's nonzero masks = its list of source collections.
    let node_collections: Vec<Vec<u8>> = antichains
        .iter()
        .map(|ac| ac.iter().copied().filter(|&m| m != 0).collect())
        .collect();

    let vars = [s0_states, s1_states, s2_states, target_states];
    let input = input_metadata_with_cancellation(&vars, encoding, budget, cancellation)?;
    let pmf = build_pmf_with_cancellation(&vars, budget, cancellation)?;
    let empirical_pmf = pmf.diagnostics_with_cancellation(cancellation)?;
    let n_sources = 3;
    let m = antichains.len();

    let pointwise_capacity = if include_pointwise {
        pmf.entries.len()
    } else {
        0
    };
    let mut pointwise = try_vec_with_capacity(
        "discrete_sxpid3 pointwise output",
        pointwise_capacity,
        budget,
    )?;
    let mut avg = try_vec_filled(
        "discrete_sxpid3 averaged accumulators",
        m,
        [NeumaierAccumulator::default(); 2],
        budget,
    )?;

    for (realization_index, (rlz, count)) in pmf.entries.iter().enumerate() {
        check_cancellation(
            cancellation,
            OPERATION,
            realization_index,
            pmf.entries.len(),
        )?;
        let prob = pmf.probability(*count);
        let p_t = marg_with_cancellation(&pmf, rlz, 0, n_sources, true, cancellation)?;
        let mut cum_plus = try_vec_filled("discrete_sxpid3 cumulative terms", m, 0.0, budget)?;
        let mut cum_minus = try_vec_filled("discrete_sxpid3 cumulative terms", m, 0.0, budget)?;
        for (idx, collections) in node_collections.iter().enumerate() {
            let (ip, im) =
                node_terms_with_cancellation(&pmf, rlz, collections, n_sources, p_t, cancellation)?;
            cum_plus[idx] = ip;
            cum_minus[idx] = im;
        }
        // Reuse the shared compensated 3-source inversion (atoms align with `antichains`).
        let pi_plus = discrete_mobius_inversion_3(&antichains, &cum_plus);
        let pi_minus = discrete_mobius_inversion_3(&antichains, &cum_minus);

        let mut atoms = try_vec_with_capacity("discrete_sxpid3 pointwise atoms", m, budget)?;
        for i in 0..m {
            let a = SxAtom {
                informative: pi_plus[i].value,
                misinformative: pi_minus[i].value,
                net: pi_plus[i].value - pi_minus[i].value,
            };
            avg[i][0].add(prob * a.informative);
            avg[i][1].add(prob * a.misinformative);
            atoms.push(a);
        }

        if include_pointwise {
            pointwise.push(SxPointwise3 {
                s0: clone_state_with_cancellation(
                    &rlz[0],
                    "discrete_sxpid3 pointwise output",
                    budget,
                    cancellation,
                )?,
                s1: clone_state_with_cancellation(
                    &rlz[1],
                    "discrete_sxpid3 pointwise output",
                    budget,
                    cancellation,
                )?,
                s2: clone_state_with_cancellation(
                    &rlz[2],
                    "discrete_sxpid3 pointwise output",
                    budget,
                    cancellation,
                )?,
                t: clone_state_with_cancellation(
                    &rlz[3],
                    "discrete_sxpid3 pointwise output",
                    budget,
                    cancellation,
                )?,
                prob,
                atoms,
            });
        }
    }
    cancellation.check(OPERATION, pmf.entries.len(), pmf.entries.len())?;

    let mut atoms_avg = try_vec_with_capacity("discrete_sxpid3 averaged atoms", m, budget)?;
    for a in &avg {
        let informative = a[0].total();
        let misinformative = a[1].total();
        atoms_avg.push(SxAtom {
            informative,
            misinformative,
            net: informative - misinformative,
        });
    }

    Ok(DiscreteSxPid3Result {
        pointwise,
        pointwise_included: include_pointwise,
        antichains: node_collections,
        atoms: atoms_avg,
        mi_s0_t,
        mi_s1_t,
        mi_s2_t,
        mi_s0s1s2_t,
        subset_mis,
        input,
        empirical_pmf,
    })
}

// ----------------------------------------------------------------------------------------------
// Small local join helpers (the `discrete_pid` ones are private; these keep this module
// self-contained without widening that module's surface further).
// ----------------------------------------------------------------------------------------------

fn join_pair_with_cancellation(
    a: &[Vec<usize>],
    b: &[Vec<usize>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<usize>>> {
    const OPERATION: &str = "categorical source join";
    cancellation.check(OPERATION, 0, a.len())?;
    let mut joined = try_vec_with_capacity(OPERATION, a.len(), budget)?;
    for (row_index, (left, right)) in a.iter().zip(b).enumerate() {
        check_cancellation(cancellation, OPERATION, row_index, a.len())?;
        let width = left
            .len()
            .checked_add(right.len())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let mut row = try_vec_with_capacity(OPERATION, width, budget)?;
        for chunk in left
            .chunks(CANCELLATION_CHECK_INTERVAL)
            .chain(right.chunks(CANCELLATION_CHECK_INTERVAL))
        {
            cancellation.check(OPERATION, row_index, a.len())?;
            row.extend_from_slice(chunk);
        }
        joined.push(row);
    }
    cancellation.check(OPERATION, a.len(), a.len())?;
    Ok(joined)
}

fn subset_mutual_information_with_cancellation(
    sources: &[&[Vec<usize>]],
    target: &[Vec<usize>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<f64>> {
    const OPERATION: &str = "categorical subset MI";
    let n = target.len();
    let subset_count = (1usize << sources.len())
        .checked_sub(1)
        .ok_or(PidError::SizeOverflow {
            operation: "categorical subset MI",
        })?;
    cancellation.check(OPERATION, 0, subset_count)?;
    let mut out = try_vec_with_capacity("categorical subset MI", subset_count, budget)?;
    for mask in 1usize..(1usize << sources.len()) {
        check_cancellation(cancellation, OPERATION, mask - 1, subset_count)?;
        let width = sources
            .iter()
            .enumerate()
            .filter(|(source_index, _)| mask & (1 << source_index) != 0)
            .map(|(_, source)| source.first().map_or(0, Vec::len))
            .try_fold(0usize, usize::checked_add)
            .ok_or(PidError::SizeOverflow {
                operation: "categorical subset MI",
            })?;
        let mut joined = try_vec_with_capacity("categorical subset MI", n, budget)?;
        for row_index in 0..n {
            check_cancellation(cancellation, OPERATION, row_index, n)?;
            let mut row = try_vec_with_capacity("categorical subset MI", width, budget)?;
            for (source_index, source) in sources.iter().enumerate() {
                if mask & (1 << source_index) != 0 {
                    for chunk in source[row_index].chunks(CANCELLATION_CHECK_INTERVAL) {
                        cancellation.check(OPERATION, row_index, n)?;
                        row.extend_from_slice(chunk);
                    }
                }
            }
            joined.push(row);
        }
        out.push(discrete_mi_with_budget_and_cancellation(
            &joined,
            target,
            0,
            budget,
            cancellation,
        )?);
    }
    cancellation.check(OPERATION, subset_count, subset_count)?;
    Ok(out)
}

// ----------------------------------------------------------------------------------------------
// General n-source (n = 2..=4) — same redundancy lattice machinery for arbitrary source count.
// The per-realization probability primitives (`union_prob`, `node_terms`) are already n-general;
// the only n-specific parts are the antichain enumeration and the Möbius inversion below. The
// 2- and 3-source `discrete_sxpid2/3` paths above are kept as specialized comparison paths; tests
// pin this general path to numerical agreement within floating-point tolerance.
// ----------------------------------------------------------------------------------------------

/// One pointwise decomposition for the general n-source lattice.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct SxPointwiseN {
    /// The realization as per-variable categorical states: `n_sources` sources then the target.
    pub realization: Vec<Vec<usize>>,
    pub prob: f64,
    /// Atoms aligned with [`DiscreteSxPidNResult::antichains`].
    pub atoms: Vec<SxAtom>,
}

/// Result of a general n-source discrete shared-exclusions PID.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct DiscreteSxPidNResult {
    pub n_sources: usize,
    /// Lattice nodes as set-lists of source bitmasks (canonical: each list sorted ascending).
    pub antichains: Vec<Vec<u8>>,
    /// Averaged atoms, aligned with `antichains`.
    pub atoms: Vec<SxAtom>,
    pub pointwise: Vec<SxPointwiseN>,
    pub pointwise_included: bool,
    /// Joint MI `I(S_0,…,S_{n-1}; T)` — the sum of all averaged net atoms (reconstruction).
    pub joint_mi: f64,
    /// Mutual information for every non-empty source subset. Index `mask - 1` corresponds to the
    /// source bitmask `mask` and equals the sum of atoms in that node's down-set.
    pub subset_mis: Vec<f64>,
    /// Categorical/quantized input provenance and observed state counts.
    pub input: DiscreteInputMetadata,
    pub empirical_pmf: EmpiricalPmfDiagnostics,
}

impl DiscreteSxPidNResult {
    /// Averaged atom for an antichain given as a slice of bitmasks (order-insensitive).
    pub fn atom(&self, sets: &[u8]) -> Option<SxAtom> {
        self.antichains
            .iter()
            .position(|antichain| unordered_masks_equal(antichain, sets))
            .map(|i| self.atoms[i])
    }
}

/// `a ⪯ b` on the redundancy lattice: every collection in `b` contains some collection in `a`.
/// (`aa ⊆ bb` is tested as `aa & !bb == 0` — no bit of `aa` lies outside `bb`.)
fn leq_n(a: &[u8], b: &[u8]) -> bool {
    b.iter().all(|&bb| a.iter().any(|&aa| aa & !bb == 0))
}

/// All antichains over the non-empty subsets of `{0..n}` (n ≤ 4), each canonicalised to an
/// ascending mask list. Brute-force over the powerset of the `2^n − 1` non-empty masks.
fn antichains_n_with_cancellation(
    n: usize,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<u8>>> {
    const OPERATION: &str = "categorical antichain lattice";
    let mask_count = (1usize << n).checked_sub(1).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let mut masks = try_vec_with_capacity(OPERATION, mask_count, budget)?;
    for mask in 1u16..(1u16 << n) {
        masks.push(mask as u8);
    }
    let lattice_capacity = [0usize, 1, 4, 18, 166][n];
    let mut out = try_vec_with_capacity(OPERATION, lattice_capacity, budget)?;
    let combination_count = (1u32 << masks.len()) - 1;
    cancellation.check(OPERATION, 0, combination_count as usize)?;
    for combo in 1u32..=combination_count {
        check_cancellation(
            cancellation,
            OPERATION,
            (combo - 1) as usize,
            combination_count as usize,
        )?;
        let selected_count = (combo.count_ones()) as usize;
        let mut sel = try_vec_with_capacity(OPERATION, selected_count, budget)?;
        sel.extend(
            masks
                .iter()
                .enumerate()
                .filter(|(index, _)| combo & (1 << index) != 0)
                .map(|(_, &mask)| mask),
        );
        // Antichain iff no member is a subset of another.
        let is_antichain =
            (0..sel.len()).all(|i| (0..sel.len()).all(|j| i == j || (sel[i] & sel[j]) != sel[i]));
        if is_antichain {
            out.push(sel); // already ascending: `masks` is ascending and the filter preserves order
        }
    }
    cancellation.check(
        OPERATION,
        combination_count as usize,
        combination_count as usize,
    )?;
    Ok(out)
}

/// Möbius inversion of a per-antichain cumulative vector into atoms (general n).
#[cfg(test)]
fn mobius_n(
    antichains: &[Vec<u8>],
    topo: &[usize],
    cumulative: &[f64],
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    let cancellation = CancellationToken::new();
    mobius_n_with_cancellation(antichains, topo, cumulative, budget, &cancellation)
}

fn mobius_n_with_cancellation(
    antichains: &[Vec<u8>],
    topo: &[usize],
    cumulative: &[f64],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<f64>> {
    const OPERATION: &str = "categorical Mobius inversion";
    let m = antichains.len();
    cancellation.check(OPERATION, 0, m)?;
    let mut atoms = try_vec_filled(OPERATION, m, 0.0, budget)?;
    for (pos, &idx) in topo.iter().enumerate() {
        // Apply each subtraction's sign before compensated accumulation. Negative lower atoms
        // therefore contribute positively, while `topo` preserves a canonical deterministic
        // order for all same-sign and cancelling terms.
        check_cancellation(cancellation, OPERATION, pos, m)?;
        let mut accumulator = NeumaierAccumulator::default();
        accumulator.add(cumulative[idx]);
        for (lower_index, &j) in topo[..pos].iter().enumerate() {
            check_cancellation(cancellation, OPERATION, lower_index, pos)?;
            if leq_n(&antichains[j], &antichains[idx]) {
                accumulator.add(-atoms[j]);
            }
        }
        atoms[idx] = accumulator.total();
    }
    cancellation.check(OPERATION, m, m)?;
    Ok(atoms)
}

fn topo_order_n_with_cancellation(
    antichains: &[Vec<u8>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<usize>> {
    const OPERATION: &str = "categorical lattice topological order";
    let mut remaining = try_vec_with_capacity(OPERATION, antichains.len(), budget)?;
    remaining.extend(0..antichains.len());
    let mut out = try_vec_with_capacity(OPERATION, remaining.len(), budget)?;
    let total_units = antichains
        .len()
        .checked_mul(antichains.len())
        .and_then(|value| value.checked_mul(antichains.len()))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let mut completed_units = 0usize;
    cancellation.check(OPERATION, 0, total_units)?;
    while !remaining.is_empty() {
        let mut chosen: Option<usize> = None;
        for &i in &remaining {
            let mut minimal = true;
            for &j in &remaining {
                check_cancellation(cancellation, OPERATION, completed_units, total_units)?;
                completed_units = completed_units.saturating_add(1);
                if j != i && leq_n(&antichains[j], &antichains[i]) {
                    minimal = false;
                    break;
                }
            }
            if minimal && chosen.is_none_or(|current| i < current) {
                chosen = Some(i);
            }
        }
        let chosen = chosen.ok_or(PidError::NumericalInstability {
            context: "categorical lattice topological order had no minimal node",
        })?;
        out.push(chosen);
        remaining.retain(|&x| x != chosen);
    }
    cancellation.check(OPERATION, completed_units, total_units)?;
    Ok(out)
}

/// Direct empirical-PMF categorical shared-exclusions PID for a variable number of sources
/// (`2 ≤ n ≤ 4`).
///
/// Same measure as [`discrete_sxpid2`]/[`discrete_sxpid3`] (matching them within floating-point
/// tolerance), extended
/// to the full antichain lattice for up to four sources — matching the source count IDTxl's SxPID
/// estimator supports. Atoms are keyed by their antichain (a set-list of source bitmasks), e.g.
/// `&[0b0001, 0b0010, 0b0100, 0b1000]` is the all-singletons (global) redundancy for `n = 4`.
pub fn discrete_sxpid_n(
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPidNResult> {
    discrete_sxpid_n_with_budget(sources, target, ResourceBudget::default())
}

/// Worst-case distinct-state resource estimate for [`discrete_sxpid_n`].
pub fn discrete_sxpid_n_resource_estimate(
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    include_pointwise: bool,
) -> PidResult<ResourceEstimate> {
    sxpid_resource_estimate_impl("discrete_sxpid_n", sources, target, include_pointwise)
}

/// [`discrete_sxpid_n`] with an explicit allocation and operation ceiling.
pub fn discrete_sxpid_n_with_budget(
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPidNResult> {
    let n_sources = sources.len();
    if !(2..=4).contains(&n_sources) {
        return Err(PidError::NotImplemented {
            feature: "discrete_sxpid_n supports 2..=4 sources",
        });
    }
    validate_discrete_mats("discrete_sxpid_n", sources, target, budget, true)?;
    let mut source_states =
        try_vec_with_capacity("discrete_sxpid_n source states", n_sources, budget)?;
    for source in sources {
        source_states.push(states_from_discrete(*source, budget)?);
    }
    let target_states = states_from_discrete(target, budget)?;
    sxpid_n_from_states(
        &source_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
        true,
        budget,
    )
}

/// Compute only averaged atoms for two to four categorical sources.
pub fn discrete_sxpid_n_averaged(
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPidNResult> {
    discrete_sxpid_n_averaged_with_budget(sources, target, ResourceBudget::default())
}

/// [`discrete_sxpid_n_averaged`] with an explicit allocation and operation ceiling.
pub fn discrete_sxpid_n_averaged_with_budget(
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPidNResult> {
    let cancellation = CancellationToken::new();
    discrete_sxpid_n_averaged_with_budget_and_cancellation(sources, target, budget, &cancellation)
}

/// [`discrete_sxpid_n_averaged_with_budget`] with cooperative cancellation throughout
/// categorical materialization, antichain construction, and empirical shared-exclusion scans.
pub fn discrete_sxpid_n_averaged_with_budget_and_cancellation(
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteSxPidNResult> {
    const OPERATION: &str = "discrete_sxpid_n_averaged";
    let n_sources = sources.len();
    if !(2..=4).contains(&n_sources) {
        return Err(PidError::NotImplemented {
            feature: "discrete_sxpid_n_averaged supports 2..=4 sources",
        });
    }
    validate_discrete_mats("discrete_sxpid_n_averaged", sources, target, budget, false)?;
    cancellation.check(OPERATION, 0, target.nrows())?;
    let mut source_states =
        try_vec_with_capacity("discrete_sxpid_n source states", n_sources, budget)?;
    for source in sources {
        source_states.push(states_from_discrete_with_cancellation(
            *source,
            budget,
            cancellation,
        )?);
    }
    sxpid_n_from_states_with_cancellation(
        &source_states,
        &states_from_discrete_with_cancellation(target, budget, cancellation)?,
        DiscreteInputEncoding::Categorical,
        false,
        budget,
        cancellation,
    )
}

/// Evaluate averaged 2--4-source SxPID while retaining every fixed quantizer report.
pub fn fitted_quantized_sxpid_n(
    sources: &[&QuantizedData],
    target: &QuantizedData,
) -> PidResult<FittedQuantizedSxPidNResult> {
    fitted_quantized_sxpid_n_with_budget(sources, target, ResourceBudget::default())
}

/// Resource preflight for [`fitted_quantized_sxpid_n`], including copied quantizer reports.
pub fn fitted_quantized_sxpid_n_resource_estimate(
    sources: &[&QuantizedData],
    target: &QuantizedData,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "fitted_quantized_sxpid_n";
    if !(2..=4).contains(&sources.len()) {
        return Err(PidError::NotImplemented {
            feature: "fitted_quantized_sxpid_n supports 2..=4 sources",
        });
    }
    let mut source_matrices = [target.matrix.as_ref(); 4];
    for (destination, source) in source_matrices.iter_mut().zip(sources) {
        *destination = source.matrix.as_ref();
    }
    let reports_heap = sources.iter().try_fold(
        quantization_report_heap_bytes(OPERATION, &target.report)?,
        |sum, source| {
            checked_resource_add(
                OPERATION,
                sum,
                quantization_report_heap_bytes(OPERATION, &source.report)?,
            )
        },
    )?;
    let report_vector_bytes = checked_resource_mul(
        OPERATION,
        sources.len() as u128,
        std::mem::size_of::<QuantizationReport>() as u128,
    )?;
    let estimate = sxpid_resource_estimate_impl(
        OPERATION,
        &source_matrices[..sources.len()],
        target.matrix.as_ref(),
        false,
    )?;
    add_sxpid_estimate_bytes(
        OPERATION,
        estimate,
        checked_resource_add(OPERATION, reports_heap, report_vector_bytes)?,
    )
}

/// [`fitted_quantized_sxpid_n`] with an explicit allocation and operation ceiling.
pub fn fitted_quantized_sxpid_n_with_budget(
    sources: &[&QuantizedData],
    target: &QuantizedData,
    budget: ResourceBudget,
) -> PidResult<FittedQuantizedSxPidNResult> {
    const OPERATION: &str = "fitted_quantized_sxpid_n";
    if !(2..=4).contains(&sources.len()) {
        return Err(PidError::NotImplemented {
            feature: "fitted_quantized_sxpid_n supports 2..=4 sources",
        });
    }
    budget.check(
        OPERATION,
        fitted_quantized_sxpid_n_resource_estimate(sources, target)?,
    )?;
    let mut source_matrices =
        try_vec_with_capacity("fitted_quantized_sxpid_n sources", sources.len(), budget)?;
    source_matrices.extend(sources.iter().map(|source| source.matrix.as_ref()));
    let mut pid =
        discrete_sxpid_n_averaged_with_budget(&source_matrices, target.matrix.as_ref(), budget)?;
    pid.input.encoding = DiscreteInputEncoding::FittedEqualWidth;
    let mut source_quantization =
        try_vec_with_capacity("fitted_quantized_sxpid_n reports", sources.len(), budget)?;
    for source in sources {
        source_quantization.push(try_clone_quantization_report(
            OPERATION,
            &source.report,
            budget,
        )?);
    }
    Ok(FittedQuantizedSxPidNResult {
        pid,
        source_quantization,
        target_quantization: try_clone_quantization_report(OPERATION, &target.report, budget)?,
    })
}

/// Equal-width-quantized shared-exclusions PID for two to four continuous sources.
#[cfg(feature = "experimental-pipelines")]
pub fn quantized_sxpid_n(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<crate::same_sample::ExploratorySameSampleQuantizedResult<DiscreteSxPidNResult>> {
    let n_sources = sources.len();
    if !(2..=4).contains(&n_sources) {
        return Err(PidError::NotImplemented {
            feature: "quantized_sxpid_n supports 2..=4 sources",
        });
    }
    validate_quantized_mats("quantized_sxpid_n", sources, target, num_bins)?;
    let source_states = sources
        .iter()
        .map(|source| quantize_equal_width(*source, num_bins))
        .collect::<PidResult<Vec<_>>>()?;
    let target_states = quantize_equal_width(target, num_bins)?;
    let categorical_result = sxpid_n_from_states(
        &source_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
        true,
        ResourceBudget::default(),
    )?;
    Ok(crate::same_sample::ExploratorySameSampleQuantizedResult::new(categorical_result, num_bins))
}

fn sxpid_n_from_states(
    source_states: &[Vec<Vec<usize>>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
    include_pointwise: bool,
    budget: ResourceBudget,
) -> PidResult<DiscreteSxPidNResult> {
    let cancellation = CancellationToken::new();
    sxpid_n_from_states_with_cancellation(
        source_states,
        target_states,
        encoding,
        include_pointwise,
        budget,
        &cancellation,
    )
}

fn sxpid_n_from_states_with_cancellation(
    source_states: &[Vec<Vec<usize>>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
    include_pointwise: bool,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DiscreteSxPidNResult> {
    const OPERATION: &str = "discrete_sxpid_n";
    cancellation.check(OPERATION, 0, target_states.len())?;
    let n_sources = source_states.len();
    let reference_capacity = n_sources.checked_add(1).ok_or(PidError::SizeOverflow {
        operation: "discrete_sxpid_n source references",
    })?;
    let mut source_refs = try_vec_with_capacity(
        "discrete_sxpid_n source references",
        reference_capacity,
        budget,
    )?;
    source_refs.extend(source_states.iter().map(Vec::as_slice));
    let subset_mis = subset_mutual_information_with_cancellation(
        &source_refs,
        target_states,
        budget,
        cancellation,
    )?;
    let joint_mi = subset_mis[(1usize << n_sources) - 2];

    // Variables are ordered as sources then target.
    let mut var_states = source_refs;
    var_states.push(target_states);
    let input = input_metadata_with_cancellation(&var_states, encoding, budget, cancellation)?;
    let pmf = build_pmf_with_cancellation(&var_states, budget, cancellation)?;
    let empirical_pmf = pmf.diagnostics_with_cancellation(cancellation)?;

    let antichains = antichains_n_with_cancellation(n_sources, budget, cancellation)?;
    let topo = topo_order_n_with_cancellation(&antichains, budget, cancellation)?;
    let m = antichains.len();

    let pointwise_capacity = if include_pointwise {
        pmf.entries.len()
    } else {
        0
    };
    let mut pointwise = try_vec_with_capacity(
        "discrete_sxpid_n pointwise output",
        pointwise_capacity,
        budget,
    )?;
    let mut avg = try_vec_filled(
        "discrete_sxpid_n averaged accumulators",
        m,
        [NeumaierAccumulator::default(); 2],
        budget,
    )?;

    for (realization_index, (rlz, count)) in pmf.entries.iter().enumerate() {
        check_cancellation(
            cancellation,
            OPERATION,
            realization_index,
            pmf.entries.len(),
        )?;
        let prob = pmf.probability(*count);
        let p_t = marg_with_cancellation(&pmf, rlz, 0, n_sources, true, cancellation)?;
        let mut cum_plus = try_vec_filled("discrete_sxpid_n cumulative terms", m, 0.0, budget)?;
        let mut cum_minus = try_vec_filled("discrete_sxpid_n cumulative terms", m, 0.0, budget)?;
        for (idx, collections) in antichains.iter().enumerate() {
            check_cancellation(cancellation, OPERATION, idx, m)?;
            let (ip, im) =
                node_terms_with_cancellation(&pmf, rlz, collections, n_sources, p_t, cancellation)?;
            cum_plus[idx] = ip;
            cum_minus[idx] = im;
        }
        let pi_plus =
            mobius_n_with_cancellation(&antichains, &topo, &cum_plus, budget, cancellation)?;
        let pi_minus =
            mobius_n_with_cancellation(&antichains, &topo, &cum_minus, budget, cancellation)?;

        let mut atoms = try_vec_with_capacity("discrete_sxpid_n pointwise atoms", m, budget)?;
        for i in 0..m {
            check_cancellation(cancellation, OPERATION, i, m)?;
            let a = SxAtom {
                informative: pi_plus[i],
                misinformative: pi_minus[i],
                net: pi_plus[i] - pi_minus[i],
            };
            avg[i][0].add(prob * a.informative);
            avg[i][1].add(prob * a.misinformative);
            atoms.push(a);
        }
        if include_pointwise {
            pointwise.push(SxPointwiseN {
                realization: clone_owned_realization_with_cancellation(
                    rlz,
                    "discrete_sxpid_n pointwise output",
                    budget,
                    cancellation,
                )?,
                prob,
                atoms,
            });
        }
    }
    cancellation.check(OPERATION, pmf.entries.len(), pmf.entries.len())?;

    let mut atoms_avg = try_vec_with_capacity("discrete_sxpid_n averaged atoms", m, budget)?;
    for (index, a) in avg.iter().enumerate() {
        check_cancellation(cancellation, OPERATION, index, avg.len())?;
        let informative = a[0].total();
        let misinformative = a[1].total();
        atoms_avg.push(SxAtom {
            informative,
            misinformative,
            net: informative - misinformative,
        });
    }
    cancellation.check(OPERATION, avg.len(), avg.len())?;

    Ok(DiscreteSxPidNResult {
        n_sources,
        antichains,
        atoms: atoms_avg,
        pointwise,
        pointwise_included: include_pointwise,
        joint_mi,
        subset_mis,
        input,
        empirical_pmf,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(feature = "experimental-pipelines")]
    use crate::matrix::MatRef;
    use std::f64::consts::LN_2;

    #[test]
    fn sxpid2_averaged_with_cancellation_honors_a_pre_cancelled_token() {
        let s1 = [0, 0, 1, 1];
        let s2 = [0, 1, 0, 1];
        let target = [0, 1, 1, 0];
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = discrete_sxpid2_averaged_with_budget_and_cancellation(
            DiscreteMatRef::new(&s1, 4, 1).unwrap(),
            DiscreteMatRef::new(&s2, 4, 1).unwrap(),
            DiscreteMatRef::new(&target, 4, 1).unwrap(),
            ResourceBudget::default(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "discrete_sxpid2_averaged",
                completed_units: 0,
                ..
            })
        ));
    }

    #[test]
    fn sxpid3_averaged_with_cancellation_honors_a_pre_cancelled_token() {
        let s0 = [0, 0, 1, 1];
        let s1 = [0, 1, 0, 1];
        let s2 = [1, 0, 1, 0];
        let target = [0, 1, 1, 0];
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = discrete_sxpid3_averaged_with_budget_and_cancellation(
            DiscreteMatRef::new(&s0, 4, 1).unwrap(),
            DiscreteMatRef::new(&s1, 4, 1).unwrap(),
            DiscreteMatRef::new(&s2, 4, 1).unwrap(),
            DiscreteMatRef::new(&target, 4, 1).unwrap(),
            ResourceBudget::default(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "discrete_sxpid3_averaged",
                completed_units: 0,
                ..
            })
        ));
    }

    #[test]
    fn sxpid_n_averaged_with_cancellation_honors_a_pre_cancelled_token() {
        let s0 = [0, 0, 1, 1];
        let s1 = [0, 1, 0, 1];
        let target = [0, 1, 1, 0];
        let sources = [
            DiscreteMatRef::new(&s0, 4, 1).unwrap(),
            DiscreteMatRef::new(&s1, 4, 1).unwrap(),
        ];
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = discrete_sxpid_n_averaged_with_budget_and_cancellation(
            &sources,
            DiscreteMatRef::new(&target, 4, 1).unwrap(),
            ResourceBudget::default(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "discrete_sxpid_n_averaged",
                completed_units: 0,
                ..
            })
        ));
    }

    #[test]
    fn uncancelled_sxpid2_matches_compatibility_entry_point_bit_exactly() {
        let s1 = [0, 0, 1, 1];
        let s2 = [0, 1, 0, 1];
        let target = [0, 1, 1, 0];
        let s1 = DiscreteMatRef::new(&s1, 4, 1).unwrap();
        let s2 = DiscreteMatRef::new(&s2, 4, 1).unwrap();
        let target = DiscreteMatRef::new(&target, 4, 1).unwrap();
        let expected =
            discrete_sxpid2_averaged_with_budget(s1, s2, target, ResourceBudget::default())
                .unwrap();
        let cancellation = CancellationToken::new();
        let actual = discrete_sxpid2_averaged_with_budget_and_cancellation(
            s1,
            s2,
            target,
            ResourceBudget::default(),
            &cancellation,
        )
        .unwrap();

        assert_eq!(
            [
                actual.unq1.net.to_bits(),
                actual.unq2.net.to_bits(),
                actual.syn.net.to_bits(),
                actual.red.net.to_bits(),
                actual.mi_s1_t.to_bits(),
                actual.mi_s2_t.to_bits(),
                actual.mi_s1s2_t.to_bits(),
            ],
            [
                expected.unq1.net.to_bits(),
                expected.unq2.net.to_bits(),
                expected.syn.net.to_bits(),
                expected.red.net.to_bits(),
                expected.mi_s1_t.to_bits(),
                expected.mi_s2_t.to_bits(),
                expected.mi_s1s2_t.to_bits(),
            ]
        );
    }

    /// Exactly-enumerated 2-input gate dataset (no sampling error → exact pmf).
    fn gate2(
        rows: &[(usize, usize, usize)],
        reps: usize,
    ) -> (Vec<usize>, Vec<usize>, Vec<usize>, usize) {
        let mut s1 = Vec::new();
        let mut s2 = Vec::new();
        let mut t = Vec::new();
        for _ in 0..reps {
            for &(a, b, c) in rows {
                s1.push(a);
                s2.push(b);
                t.push(c);
            }
        }
        let n = rows.len() * reps;
        (s1, s2, t, n)
    }

    fn run2(rows: &[(usize, usize, usize)]) -> DiscreteSxPid2Result {
        let (s1, s2, t, n) = gate2(rows, 8);
        let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
        let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
        let t = DiscreteMatRef::new(&t, n, 1).unwrap();
        discrete_sxpid2(s1, s2, t).unwrap()
    }

    #[test]
    fn empirical_event_probability_sums_counts_before_division() {
        let source = vec![vec![0], vec![0], vec![0], vec![1], vec![1]];
        let target = vec![vec![0], vec![0], vec![1], vec![1], vec![1]];
        let pmf = build_pmf(&[&source, &target], ResourceBudget::default()).unwrap();
        let realization = vec![vec![0], vec![0]];

        assert_eq!(
            marg(&pmf, &realization, 0, 1, true).unwrap().to_bits(),
            (2.0_f64 / 5.0).to_bits()
        );
    }

    #[test]
    fn neumaier_accumulator_retains_small_signed_expectation_term() {
        let mut accumulator = NeumaierAccumulator::default();
        for value in [1.0e16, 1.0, -1.0e16] {
            accumulator.add(value);
        }

        assert_eq!(accumulator.total(), 1.0);
    }

    #[test]
    fn general_mobius_inversion_compensates_mixed_sign_lower_atoms() {
        let antichains = vec![vec![0b001], vec![0b010], vec![0b100], vec![0b111]];
        let topo = vec![0, 1, 2, 3];
        let cumulative = [1.0e16, 1.0, -1.0e16, 0.0];

        let atoms = mobius_n(&antichains, &topo, &cumulative, ResourceBudget::default()).unwrap();

        assert_eq!(atoms[3], -1.0);
    }

    #[test]
    fn xor_pointwise_matches_reference() {
        // Reference (bits): every realization is [3/2, 3/2, 4/3, 2/3] in log2; here in nats (ln).
        let r = run2(&[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]);
        let want = [
            1.5_f64.ln(),
            1.5_f64.ln(),
            (4.0_f64 / 3.0).ln(),
            (2.0_f64 / 3.0).ln(),
        ];
        for p in &r.pointwise {
            for (got, w) in [p.unq1.net, p.unq2.net, p.syn.net, p.red.net]
                .iter()
                .zip(want)
            {
                assert!((got - w).abs() < 1e-12, "got {got} want {w}");
            }
            // net == informative − misinformative, always.
            for a in [p.unq1, p.unq2, p.syn, p.red] {
                assert!((a.net - (a.informative - a.misinformative)).abs() < 1e-12);
            }
        }
        // Averaged XOR shared = log2(2/3) bits (IDTxl's value), in nats.
        assert!((r.red.net - (2.0_f64 / 3.0).ln()).abs() < 1e-12);
    }

    #[test]
    fn and_averaged_red_matches_idtxl() {
        // IDTxl: averaged shared(AND) = 0.12255624891826572 bits.
        let r = run2(&[(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]);
        let want_nats = 0.12255624891826572 * LN_2;
        assert!(
            (r.red.net - want_nats).abs() < 1e-12,
            "red={} want {want_nats}",
            r.red.net
        );
        // Reconstruction: atoms sum to I(S1,S2;T).
        let sum = r.unq1.net + r.unq2.net + r.syn.net + r.red.net;
        assert!((sum - r.mi_s1s2_t).abs() < 1e-9);
    }

    #[test]
    fn self_redundancy_and_reconstruction() {
        // UNQ gate T = S1: unq1+red = I(S1;T), and atoms sum to I(S1,S2;T).
        let r = run2(&[(0, 0, 0), (0, 1, 0), (1, 0, 1), (1, 1, 1)]);
        assert!((r.unq1.net + r.red.net - r.mi_s1_t).abs() < 1e-9);
        assert!((r.unq2.net + r.red.net - r.mi_s2_t).abs() < 1e-9);
        let sum = r.unq1.net + r.unq2.net + r.syn.net + r.red.net;
        assert!((sum - r.mi_s1s2_t).abs() < 1e-9);
    }

    #[test]
    fn symmetry_under_source_swap() {
        let rows = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]; // AND
        let r = run2(&rows);
        let swapped: Vec<(usize, usize, usize)> = rows.iter().map(|&(a, b, c)| (b, a, c)).collect();
        let rs = run2(&swapped);
        assert!((r.unq1.net - rs.unq2.net).abs() < 1e-12);
        assert!((r.unq2.net - rs.unq1.net).abs() < 1e-12);
        assert!((r.red.net - rs.red.net).abs() < 1e-12);
        assert!((r.syn.net - rs.syn.net).abs() < 1e-12);
    }

    #[test]
    fn tri_rnd_3source() {
        // Giant bit over 3 sources: all atoms 0 except {{0},{1},{2}} = log 2.
        let n = 8 * 2;
        let mut s0 = Vec::new();
        let mut s1 = Vec::new();
        let mut s2 = Vec::new();
        let mut t = Vec::new();
        for _ in 0..8 {
            for b in [0, 1] {
                s0.push(b);
                s1.push(b);
                s2.push(b);
                t.push(b);
            }
        }
        let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
        let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
        let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
        let t = DiscreteMatRef::new(&t, n, 1).unwrap();
        let r = discrete_sxpid3(s0, s1, s2, t).unwrap();

        let red_all = r.atom(&[0b001, 0b010, 0b100]).unwrap();
        assert!(
            (red_all.net - 2.0_f64.ln()).abs() < 1e-12,
            "red_all={}",
            red_all.net
        );
        // Reconstruction: all atoms sum to the joint MI (= log 2 here).
        let sum: f64 = r.atoms.iter().map(|a| a.net).sum();
        assert!((sum - r.mi_s0s1s2_t).abs() < 1e-9);
        assert!((sum - 2.0_f64.ln()).abs() < 1e-9);

        for mask in 1u8..=0b111 {
            let downset_sum: f64 = r
                .antichains
                .iter()
                .zip(&r.atoms)
                .filter(|(antichain, _)| leq_n(antichain, &[mask]))
                .map(|(_, atom)| atom.net)
                .sum();
            assert!((downset_sum - r.subset_mis[usize::from(mask - 1)]).abs() < 1e-12);
        }
    }

    #[test]
    fn categorical_labels_are_invariant_under_bijections() {
        let source_a = [0, 1, 100, 0, 1, 100];
        let source_b = [100, 0, 50, 100, 0, 50];
        let noise = [7, 7, 7, 7, 7, 7];
        let target_a = [10, 20, 30, 10, 20, 30];
        let target_b = [2, 900, 41, 2, 900, 41];
        let run = |source: &[usize], target: &[usize]| {
            discrete_sxpid2(
                DiscreteMatRef::new(source, 6, 1).unwrap(),
                DiscreteMatRef::new(&noise, 6, 1).unwrap(),
                DiscreteMatRef::new(target, 6, 1).unwrap(),
            )
            .unwrap()
        };
        let a = run(&source_a, &target_a);
        let b = run(&source_b, &target_b);
        assert_eq!(a.input.encoding, DiscreteInputEncoding::Categorical);
        assert_eq!(a.input.observed_cardinalities, vec![3, 1, 3]);
        for (left, right) in [
            (a.unq1, b.unq1),
            (a.unq2, b.unq2),
            (a.syn, b.syn),
            (a.red, b.red),
        ] {
            assert!((left.informative - right.informative).abs() < 1e-12);
            assert!((left.misinformative - right.misinformative).abs() < 1e-12);
            assert!((left.net - right.net).abs() < 1e-12);
        }
        assert!((a.mi_s1s2_t - 3.0_f64.ln()).abs() < 1e-12);
        assert!((a.mi_s1s2_t - b.mi_s1s2_t).abs() < 1e-12);

        #[cfg(feature = "experimental-pipelines")]
        {
            // Same-sample equal-width binning is intentionally a different, exploratory contract:
            // numeric spacing matters.
            let quantized_a: Vec<f64> = source_a.iter().map(|&label| label as f64).collect();
            let quantized_b = [0.0, 50.0, 100.0, 0.0, 50.0, 100.0];
            let quantized_noise = [0.0; 6];
            let qa = quantized_sxpid2(
                MatRef::new(&quantized_a, 6, 1).unwrap(),
                MatRef::new(&quantized_noise, 6, 1).unwrap(),
                MatRef::new(&quantized_a, 6, 1).unwrap(),
                3,
            )
            .unwrap()
            .into_categorical_result();
            let qb = quantized_sxpid2(
                MatRef::new(&quantized_b, 6, 1).unwrap(),
                MatRef::new(&quantized_noise, 6, 1).unwrap(),
                MatRef::new(&quantized_b, 6, 1).unwrap(),
                3,
            )
            .unwrap()
            .into_categorical_result();
            assert!(qb.mi_s1s2_t - qa.mi_s1s2_t > 0.4);
            assert_eq!(qa.input.encoding, DiscreteInputEncoding::Categorical);
        }
    }

    #[test]
    fn target_chain_rule_holds_pointwise_for_every_two_source_node() {
        let weighted = [
            (0, 0, 0, 0, 3usize),
            (0, 1, 0, 1, 1),
            (1, 0, 1, 0, 2),
            (1, 1, 1, 1, 4),
            (2, 0, 1, 1, 2),
        ];
        let (mut s1, mut s2, mut t1, mut joint_target) =
            (Vec::new(), Vec::new(), Vec::new(), Vec::new());
        for (a, b, c, d, weight) in weighted {
            for _ in 0..weight {
                s1.push(vec![a]);
                s2.push(vec![b]);
                t1.push(vec![c]);
                joint_target.push(vec![c, d]);
            }
        }
        let joint_pmf = build_pmf(&[&s1, &s2, &joint_target], ResourceBudget::default()).unwrap();
        let first_pmf = build_pmf(&[&s1, &s2, &t1], ResourceBudget::default()).unwrap();

        for (joint_realization, _) in &joint_pmf.entries {
            let first_realization = vec![
                joint_realization[0].clone(),
                joint_realization[1].clone(),
                vec![joint_realization[2][0]],
            ];
            let p_joint = marg(&joint_pmf, joint_realization, 0, 2, true).unwrap();
            let p_first = marg(&first_pmf, &first_realization, 0, 2, true).unwrap();
            for collections in NODES2 {
                let p_union =
                    union_prob(&joint_pmf, joint_realization, collections, 2, false).unwrap();
                let p_joint_union =
                    union_prob(&joint_pmf, joint_realization, collections, 2, true).unwrap();
                let p_first_union =
                    union_prob(&first_pmf, &first_realization, collections, 2, true).unwrap();

                let (joint_plus, joint_minus) =
                    node_terms(&joint_pmf, joint_realization, collections, 2, p_joint).unwrap();
                let (first_plus, first_minus) =
                    node_terms(&first_pmf, &first_realization, collections, 2, p_first).unwrap();
                let joint_information = joint_plus - joint_minus;
                let first_information = first_plus - first_minus;
                let conditional_information =
                    ((p_joint_union / p_first_union) / (p_joint / p_first)).ln();

                assert!(p_union > 0.0);
                assert!(
                    (joint_information - first_information - conditional_information).abs() < 1e-12,
                    "target chain rule failed for {collections:?}"
                );
            }
        }
    }
}
