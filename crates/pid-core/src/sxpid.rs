//! Discrete **shared-exclusions** PID — the genuine `i^sx_∩` of Makkeh, Gutknecht & Wibral
//! (2021, Phys. Rev. E 103, 032149; arXiv:2002.03356), with the part-whole / formal-logic
//! foundation of Gutknecht, Wibral & Makkeh (2021, arXiv:2008.09535).
//!
//! # Why this exists (and how it differs from the `discrete_pid` module)
//!
//! The `discrete_pid` module computes the Williams & Beer (2010) `I_min` redundancy. `I_min` is
//! precisely the measure SxPID was introduced to replace: on the two-bit COPY of *independent*
//! sources it attributes the **maximal** 1 bit of redundancy. The Harder et al. (2013) identity
//! axiom would assign zero, while `I^sx_∩` assigns `ln(4/3)` nats and therefore does not satisfy
//! that axiom. SxPID instead defines
//! redundancy through **shared exclusions**: the information that source realizations *jointly
//! exclude* about the target, combined by logical **disjunction** over a redundancy lattice.
//! This is the discrete sibling of the continuous `I^sx_∩` estimator (the `isx` / `pid2` modules)
//! — so the library now decomposes information with **one** measure across the discrete and
//! continuous regimes.
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
//! - **Determinism**: the joint pmf is built over a `BTreeMap`, so realization order — and hence
//!   every floating-point accumulation — is fixed.
//!
//! # Complexity
//!
//! Brute-force over the empirical distribution: with `D` distinct realizations the cost is
//! `O(D² · #nodes · max collections)`. This is meant for low-effective-dimension categorical data
//! (gates, or explicitly quantized PLS/PCA-reduced variables).

use crate::discrete_pid::{
    discrete_antichains_3, discrete_mi, discrete_mobius_inversion_3, quantize_equal_width,
};
use crate::error::{PidError, PidResult};
use crate::matrix::{DiscreteMatRef, MatRef};
use std::collections::{BTreeMap, BTreeSet};

/// How the categorical state vectors supplied to a discrete SxPID result were obtained.
#[non_exhaustive]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiscreteInputEncoding {
    /// Caller-supplied categorical labels. Only row equality is meaningful.
    Categorical,
    /// Per-column equal-width quantization of continuous inputs.
    EqualWidth { num_bins: usize },
}

/// Input provenance recorded on every discrete SxPID result.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteInputMetadata {
    /// Whether labels were supplied exactly or produced by equal-width quantization.
    pub encoding: DiscreteInputEncoding,
    /// Number of distinct multivariate row states for each source, followed by the target.
    pub observed_cardinalities: Vec<usize>,
}

/// A single shared-exclusions PID atom: the informative (`π⁺`) and misinformative (`π⁻`) parts
/// and their net `π = π⁺ − π⁻`. All in nats.
#[derive(Debug, Clone, Copy, PartialEq)]
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
#[derive(Debug, Clone)]
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
#[derive(Debug, Clone)]
pub struct DiscreteSxPid2Result {
    /// One entry per distinct realization (the signature pointwise output of SxPID).
    pub pointwise: Vec<SxPointwise2>,
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
}

/// One pointwise decomposition for the 3-source lattice (18 antichains, in the canonical
/// `discrete_antichains_3` order).
#[derive(Debug, Clone)]
pub struct SxPointwise3 {
    pub s0: Vec<usize>,
    pub s1: Vec<usize>,
    pub s2: Vec<usize>,
    pub t: Vec<usize>,
    pub prob: f64,
    pub atoms: Vec<SxAtom>,
}

/// Result of a discrete 3-source shared-exclusions PID.
#[derive(Debug, Clone)]
pub struct DiscreteSxPid3Result {
    pub pointwise: Vec<SxPointwise3>,
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
}

impl DiscreteSxPid3Result {
    /// Look up the averaged atom for an antichain given as a slice of bitmasks (e.g. `&[0b001,
    /// 0b010, 0b100]` for `{{0},{1},{2}}`). Order-insensitive.
    pub fn atom(&self, sets: &[u8]) -> Option<SxAtom> {
        let mut want = sets.to_vec();
        want.sort_unstable();
        self.antichains
            .iter()
            .position(|ac| {
                let mut a = ac.clone();
                a.sort_unstable();
                a == want
            })
            .map(|i| self.atoms[i])
    }
}

// ----------------------------------------------------------------------------------------------
// Core primitives
// ----------------------------------------------------------------------------------------------

/// Empirical joint pmf over distinct realizations. `var_states[v]` is variable `v`'s per-sample
/// categorical state vector; the last variable is the target. Returns `(realization, probability)`
/// pairs in a deterministic (`BTreeMap`) order.
fn build_pmf(var_states: &[&[Vec<usize>]]) -> Vec<(Vec<Vec<usize>>, f64)> {
    let n = var_states[0].len();
    let mut counts: BTreeMap<Vec<Vec<usize>>, usize> = BTreeMap::new();
    for i in 0..n {
        let rlz: Vec<Vec<usize>> = var_states.iter().map(|states| states[i].clone()).collect();
        *counts.entry(rlz).or_insert(0) += 1;
    }
    let inv_n = 1.0 / n as f64;
    counts
        .into_iter()
        .map(|(k, c)| (k, c as f64 * inv_n))
        .collect()
}

/// Marginal probability of the event "agrees with `rlz` on the source indices in `source_mask`
/// (and on the target if `with_target`)".
fn marg(
    pmf: &[(Vec<Vec<usize>>, f64)],
    rlz: &[Vec<usize>],
    source_mask: u32,
    n_sources: usize,
    with_target: bool,
) -> f64 {
    let mut s = 0.0;
    for (cand, p) in pmf {
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
        if ok {
            s += p;
        }
    }
    s
}

/// `P(⋃_j 𝔞_j)` (optionally intersected with the target event), evaluated directly over the
/// empirical support. Each collection is a source bitmask.
fn union_prob(
    pmf: &[(Vec<Vec<usize>>, f64)],
    rlz: &[Vec<usize>],
    collections: &[u8],
    n_sources: usize,
    with_target: bool,
) -> f64 {
    let mut total = 0.0;
    for (cand, p) in pmf {
        if with_target && cand[n_sources] != rlz[n_sources] {
            continue;
        }
        let in_union = collections.iter().any(|&collection| {
            (0..n_sources).all(|src| collection & (1 << src) == 0 || cand[src] == rlz[src])
        });
        if in_union {
            total += p;
        }
    }
    total
}

fn input_metadata(
    vars: &[&[Vec<usize>]],
    encoding: DiscreteInputEncoding,
) -> DiscreteInputMetadata {
    let observed_cardinalities = vars
        .iter()
        .map(|rows| {
            rows.iter()
                .map(Vec::as_slice)
                .collect::<BTreeSet<_>>()
                .len()
        })
        .collect();
    DiscreteInputMetadata {
        encoding,
        observed_cardinalities,
    }
}

fn states_from_discrete(mat: DiscreteMatRef<'_>) -> Vec<Vec<usize>> {
    (0..mat.nrows()).map(|i| mat.row(i).to_vec()).collect()
}

fn validate_discrete_mats(
    context: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
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
    Ok(())
}

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
fn node_terms(
    pmf: &[(Vec<Vec<usize>>, f64)],
    rlz: &[Vec<usize>],
    collections: &[u8],
    n_sources: usize,
    p_t: f64,
) -> PidResult<(f64, f64)> {
    let p_union = union_prob(pmf, rlz, collections, n_sources, false);
    let p_t_union = union_prob(pmf, rlz, collections, n_sources, true);
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
    let unq1 = cum[0] - red;
    let unq2 = cum[1] - red;
    let syn = cum[2] - unq1 - unq2 - red;
    [unq1, unq2, syn, red]
}

/// Discrete 2-source shared-exclusions PID (`i^sx_∩`).
///
/// Inputs are categorical state labels. Numeric spacing has no meaning: sparse IDs and any
/// bijective relabeling produce the same decomposition. Use [`quantized_sxpid2`] when starting
/// from continuous measurements that need equal-width binning.
///
/// # Example
/// ```
/// use pid_core::{discrete_sxpid2, DiscreteMatRef};
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
    validate_discrete_mats("discrete_sxpid2", &[s1, s2], target)?;
    let s1_states = states_from_discrete(s1);
    let s2_states = states_from_discrete(s2);
    let target_states = states_from_discrete(target);
    sxpid2_from_states(
        &s1_states,
        &s2_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
    )
}

/// Equal-width-quantized 2-source shared-exclusions PID for continuous inputs.
///
/// This is a preprocessing convenience, not an exact categorical estimator: results can change
/// with `num_bins` and with nonlinear rescaling of the input coordinates.
pub fn quantized_sxpid2(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<DiscreteSxPid2Result> {
    validate_quantized_mats("quantized_sxpid2", &[s1, s2], target, num_bins)?;

    let s1_bins = quantize_equal_width(s1, num_bins)?;
    let s2_bins = quantize_equal_width(s2, num_bins)?;
    let t_bins = quantize_equal_width(target, num_bins)?;

    sxpid2_from_states(
        &s1_bins,
        &s2_bins,
        &t_bins,
        DiscreteInputEncoding::EqualWidth { num_bins },
    )
}

fn sxpid2_from_states(
    s1_states: &[Vec<usize>],
    s2_states: &[Vec<usize>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
) -> PidResult<DiscreteSxPid2Result> {
    let mi_s1_t = discrete_mi(s1_states, target_states, 0)?;
    let mi_s2_t = discrete_mi(s2_states, target_states, 0)?;
    let mi_s1s2_t = discrete_mi(&join_pair(s1_states, s2_states), target_states, 0)?;

    let vars = [s1_states, s2_states, target_states];
    let input = input_metadata(&vars, encoding);
    let pmf = build_pmf(&vars);
    let n_sources = 2;

    let mut pointwise = Vec::with_capacity(pmf.len());
    // Averaged accumulators for [unq1, unq2, syn, red] × (plus, minus).
    let mut avg = [[0.0f64; 2]; 4];

    for (rlz, prob) in &pmf {
        let p_t = marg(&pmf, rlz, 0, n_sources, true);
        let mut cum_plus = [0.0f64; 4];
        let mut cum_minus = [0.0f64; 4];
        for (node_idx, collections) in NODES2.iter().enumerate() {
            let (ip, im) = node_terms(&pmf, rlz, collections, n_sources, p_t)?;
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
            avg[i][0] += prob * atoms[i].informative;
            avg[i][1] += prob * atoms[i].misinformative;
        }

        pointwise.push(SxPointwise2 {
            s1: rlz[0].clone(),
            s2: rlz[1].clone(),
            t: rlz[2].clone(),
            prob: *prob,
            unq1: atoms[0],
            unq2: atoms[1],
            syn: atoms[2],
            red: atoms[3],
        });
    }

    let mk = |a: [f64; 2]| SxAtom {
        informative: a[0],
        misinformative: a[1],
        net: a[0] - a[1],
    };
    Ok(DiscreteSxPid2Result {
        pointwise,
        unq1: mk(avg[0]),
        unq2: mk(avg[1]),
        syn: mk(avg[2]),
        red: mk(avg[3]),
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        input,
    })
}

// ----------------------------------------------------------------------------------------------
// 3-source
// ----------------------------------------------------------------------------------------------

/// Direct empirical-PMF categorical 3-source shared-exclusions PID over the 18-antichain lattice.
///
/// Only equality of complete rows matters. Use [`quantized_sxpid3`] to equal-width-bin continuous
/// measurements first.
pub fn discrete_sxpid3(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<DiscreteSxPid3Result> {
    validate_discrete_mats("discrete_sxpid3", &[s0, s1, s2], target)?;
    let s0_states = states_from_discrete(s0);
    let s1_states = states_from_discrete(s1);
    let s2_states = states_from_discrete(s2);
    let target_states = states_from_discrete(target);
    sxpid3_from_states(
        &s0_states,
        &s1_states,
        &s2_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
    )
}

/// Equal-width-quantized 3-source shared-exclusions PID for continuous inputs.
pub fn quantized_sxpid3(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<DiscreteSxPid3Result> {
    validate_quantized_mats("quantized_sxpid3", &[s0, s1, s2], target, num_bins)?;
    let s0_states = quantize_equal_width(s0, num_bins)?;
    let s1_states = quantize_equal_width(s1, num_bins)?;
    let s2_states = quantize_equal_width(s2, num_bins)?;
    let target_states = quantize_equal_width(target, num_bins)?;
    sxpid3_from_states(
        &s0_states,
        &s1_states,
        &s2_states,
        &target_states,
        DiscreteInputEncoding::EqualWidth { num_bins },
    )
}

fn sxpid3_from_states(
    s0_states: &[Vec<usize>],
    s1_states: &[Vec<usize>],
    s2_states: &[Vec<usize>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
) -> PidResult<DiscreteSxPid3Result> {
    let source_states = [s0_states, s1_states, s2_states];
    let subset_mis = subset_mutual_information(&source_states, target_states)?;
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
    let input = input_metadata(&vars, encoding);
    let pmf = build_pmf(&vars);
    let n_sources = 3;
    let m = antichains.len();

    let mut pointwise = Vec::with_capacity(pmf.len());
    let mut avg = vec![[0.0f64; 2]; m];

    for (rlz, prob) in &pmf {
        let p_t = marg(&pmf, rlz, 0, n_sources, true);
        let mut cum_plus = vec![0.0f64; m];
        let mut cum_minus = vec![0.0f64; m];
        for (idx, collections) in node_collections.iter().enumerate() {
            let (ip, im) = node_terms(&pmf, rlz, collections, n_sources, p_t)?;
            cum_plus[idx] = ip;
            cum_minus[idx] = im;
        }
        // Reuse the measure-agnostic Möbius inversion (returns atoms aligned with `antichains`).
        let pi_plus = discrete_mobius_inversion_3(&antichains, &cum_plus);
        let pi_minus = discrete_mobius_inversion_3(&antichains, &cum_minus);

        let mut atoms = Vec::with_capacity(m);
        for i in 0..m {
            let a = SxAtom {
                informative: pi_plus[i].value,
                misinformative: pi_minus[i].value,
                net: pi_plus[i].value - pi_minus[i].value,
            };
            avg[i][0] += prob * a.informative;
            avg[i][1] += prob * a.misinformative;
            atoms.push(a);
        }

        pointwise.push(SxPointwise3 {
            s0: rlz[0].clone(),
            s1: rlz[1].clone(),
            s2: rlz[2].clone(),
            t: rlz[3].clone(),
            prob: *prob,
            atoms,
        });
    }

    let atoms_avg: Vec<SxAtom> = avg
        .iter()
        .map(|a| SxAtom {
            informative: a[0],
            misinformative: a[1],
            net: a[0] - a[1],
        })
        .collect();

    Ok(DiscreteSxPid3Result {
        pointwise,
        antichains: node_collections,
        atoms: atoms_avg,
        mi_s0_t,
        mi_s1_t,
        mi_s2_t,
        mi_s0s1s2_t,
        subset_mis,
        input,
    })
}

// ----------------------------------------------------------------------------------------------
// Small local join helpers (the `discrete_pid` ones are private; these keep this module
// self-contained without widening that module's surface further).
// ----------------------------------------------------------------------------------------------

fn join_pair(a: &[Vec<usize>], b: &[Vec<usize>]) -> Vec<Vec<usize>> {
    a.iter()
        .zip(b)
        .map(|(x, y)| {
            let mut r = x.clone();
            r.extend_from_slice(y);
            r
        })
        .collect()
}

fn subset_mutual_information(
    sources: &[&[Vec<usize>]],
    target: &[Vec<usize>],
) -> PidResult<Vec<f64>> {
    let n = target.len();
    let mut out = Vec::with_capacity((1usize << sources.len()) - 1);
    for mask in 1usize..(1usize << sources.len()) {
        let mut joined = vec![Vec::new(); n];
        for (source_index, source) in sources.iter().enumerate() {
            if mask & (1 << source_index) != 0 {
                for (row, state) in joined.iter_mut().zip(source.iter()) {
                    row.extend_from_slice(state);
                }
            }
        }
        out.push(discrete_mi(&joined, target, 0)?);
    }
    Ok(out)
}

// ----------------------------------------------------------------------------------------------
// General n-source (n = 2..=4) — same redundancy lattice machinery for arbitrary source count.
// The per-realization probability primitives (`union_prob`, `node_terms`) are already n-general;
// the only n-specific parts are the antichain enumeration and the Möbius inversion below. The
// 2- and 3-source `discrete_sxpid2/3` paths above are kept as the validated reference; tests pin
// this general path to numerical agreement within floating-point tolerance.
// ----------------------------------------------------------------------------------------------

/// One pointwise decomposition for the general n-source lattice.
#[derive(Debug, Clone)]
pub struct SxPointwiseN {
    /// The realization as per-variable categorical states: `n_sources` sources then the target.
    pub realization: Vec<Vec<usize>>,
    pub prob: f64,
    /// Atoms aligned with [`DiscreteSxPidNResult::antichains`].
    pub atoms: Vec<SxAtom>,
}

/// Result of a general n-source discrete shared-exclusions PID.
#[derive(Debug, Clone)]
pub struct DiscreteSxPidNResult {
    pub n_sources: usize,
    /// Lattice nodes as set-lists of source bitmasks (canonical: each list sorted ascending).
    pub antichains: Vec<Vec<u8>>,
    /// Averaged atoms, aligned with `antichains`.
    pub atoms: Vec<SxAtom>,
    pub pointwise: Vec<SxPointwiseN>,
    /// Joint MI `I(S_0,…,S_{n-1}; T)` — the sum of all averaged net atoms (reconstruction).
    pub joint_mi: f64,
    /// Mutual information for every non-empty source subset. Index `mask - 1` corresponds to the
    /// source bitmask `mask` and equals the sum of atoms in that node's down-set.
    pub subset_mis: Vec<f64>,
    /// Categorical/quantized input provenance and observed state counts.
    pub input: DiscreteInputMetadata,
}

impl DiscreteSxPidNResult {
    /// Averaged atom for an antichain given as a slice of bitmasks (order-insensitive).
    pub fn atom(&self, sets: &[u8]) -> Option<SxAtom> {
        let mut want = sets.to_vec();
        want.sort_unstable();
        self.antichains
            .iter()
            .position(|ac| *ac == want)
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
fn antichains_n(n: usize) -> Vec<Vec<u8>> {
    let masks: Vec<u8> = (1u16..(1u16 << n)).map(|m| m as u8).collect();
    let mut out = Vec::new();
    for combo in 1u32..(1u32 << masks.len()) {
        let sel: Vec<u8> = masks
            .iter()
            .enumerate()
            .filter(|(i, _)| combo & (1 << i) != 0)
            .map(|(_, &m)| m)
            .collect();
        // Antichain iff no member is a subset of another.
        let is_antichain =
            (0..sel.len()).all(|i| (0..sel.len()).all(|j| i == j || (sel[i] & sel[j]) != sel[i]));
        if is_antichain {
            out.push(sel); // already ascending: `masks` is ascending and the filter preserves order
        }
    }
    out
}

/// Möbius inversion of a per-antichain cumulative vector into atoms (general n).
fn mobius_n(antichains: &[Vec<u8>], topo: &[usize], cumulative: &[f64]) -> Vec<f64> {
    let m = antichains.len();
    let mut atoms = vec![0.0f64; m];
    for (pos, &idx) in topo.iter().enumerate() {
        let mut val = cumulative[idx];
        for &j in &topo[..pos] {
            if leq_n(&antichains[j], &antichains[idx]) {
                val -= atoms[j];
            }
        }
        atoms[idx] = val;
    }
    atoms
}

/// Topological order (minimal elements first) of the antichain lattice.
fn topo_order_n(antichains: &[Vec<u8>]) -> Vec<usize> {
    let mut remaining: Vec<usize> = (0..antichains.len()).collect();
    let mut out = Vec::with_capacity(remaining.len());
    while !remaining.is_empty() {
        let mut mins: Vec<usize> = remaining
            .iter()
            .copied()
            .filter(|&i| {
                !remaining
                    .iter()
                    .any(|&j| j != i && leq_n(&antichains[j], &antichains[i]))
            })
            .collect();
        mins.sort_unstable();
        let chosen = mins[0];
        out.push(chosen);
        remaining.retain(|&x| x != chosen);
    }
    out
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
    let n_sources = sources.len();
    if !(2..=4).contains(&n_sources) {
        return Err(PidError::NotImplemented {
            feature: "discrete_sxpid_n supports 2..=4 sources",
        });
    }
    validate_discrete_mats("discrete_sxpid_n", sources, target)?;
    let source_states: Vec<Vec<Vec<usize>>> =
        sources.iter().copied().map(states_from_discrete).collect();
    let target_states = states_from_discrete(target);
    sxpid_n_from_states(
        &source_states,
        &target_states,
        DiscreteInputEncoding::Categorical,
    )
}

/// Equal-width-quantized shared-exclusions PID for two to four continuous sources.
pub fn quantized_sxpid_n(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<DiscreteSxPidNResult> {
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
    sxpid_n_from_states(
        &source_states,
        &target_states,
        DiscreteInputEncoding::EqualWidth { num_bins },
    )
}

fn sxpid_n_from_states(
    source_states: &[Vec<Vec<usize>>],
    target_states: &[Vec<usize>],
    encoding: DiscreteInputEncoding,
) -> PidResult<DiscreteSxPidNResult> {
    let n_sources = source_states.len();
    let source_refs: Vec<&[Vec<usize>]> = source_states.iter().map(Vec::as_slice).collect();
    let subset_mis = subset_mutual_information(&source_refs, target_states)?;
    let joint_mi = subset_mis[(1usize << n_sources) - 2];

    // Variables are ordered as sources then target.
    let mut var_states = source_refs;
    var_states.push(target_states);
    let input = input_metadata(&var_states, encoding);
    let pmf = build_pmf(&var_states);

    let antichains = antichains_n(n_sources);
    let topo = topo_order_n(&antichains);
    let m = antichains.len();

    let mut pointwise = Vec::with_capacity(pmf.len());
    let mut avg = vec![[0.0f64; 2]; m];

    for (rlz, prob) in &pmf {
        let p_t = marg(&pmf, rlz, 0, n_sources, true);
        let mut cum_plus = vec![0.0f64; m];
        let mut cum_minus = vec![0.0f64; m];
        for (idx, collections) in antichains.iter().enumerate() {
            let (ip, im) = node_terms(&pmf, rlz, collections, n_sources, p_t)?;
            cum_plus[idx] = ip;
            cum_minus[idx] = im;
        }
        let pi_plus = mobius_n(&antichains, &topo, &cum_plus);
        let pi_minus = mobius_n(&antichains, &topo, &cum_minus);

        let mut atoms = Vec::with_capacity(m);
        for i in 0..m {
            let a = SxAtom {
                informative: pi_plus[i],
                misinformative: pi_minus[i],
                net: pi_plus[i] - pi_minus[i],
            };
            avg[i][0] += prob * a.informative;
            avg[i][1] += prob * a.misinformative;
            atoms.push(a);
        }
        pointwise.push(SxPointwiseN {
            realization: rlz.clone(),
            prob: *prob,
            atoms,
        });
    }

    let atoms_avg: Vec<SxAtom> = avg
        .iter()
        .map(|a| SxAtom {
            informative: a[0],
            misinformative: a[1],
            net: a[0] - a[1],
        })
        .collect();

    Ok(DiscreteSxPidNResult {
        n_sources,
        antichains,
        atoms: atoms_avg,
        pointwise,
        joint_mi,
        subset_mis,
        input,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::LN_2;

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

        // Equal-width binning is intentionally a different contract: numeric spacing matters.
        let quantized_a: Vec<f64> = source_a.iter().map(|&label| label as f64).collect();
        let quantized_b = [0.0, 50.0, 100.0, 0.0, 50.0, 100.0];
        let quantized_noise = [0.0; 6];
        let qa = quantized_sxpid2(
            MatRef::new(&quantized_a, 6, 1).unwrap(),
            MatRef::new(&quantized_noise, 6, 1).unwrap(),
            MatRef::new(&quantized_a, 6, 1).unwrap(),
            3,
        )
        .unwrap();
        let qb = quantized_sxpid2(
            MatRef::new(&quantized_b, 6, 1).unwrap(),
            MatRef::new(&quantized_noise, 6, 1).unwrap(),
            MatRef::new(&quantized_b, 6, 1).unwrap(),
            3,
        )
        .unwrap();
        assert!(qb.mi_s1s2_t - qa.mi_s1s2_t > 0.4);
        assert_eq!(
            qa.input.encoding,
            DiscreteInputEncoding::EqualWidth { num_bins: 3 }
        );
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
        let joint_pmf = build_pmf(&[&s1, &s2, &joint_target]);
        let first_pmf = build_pmf(&[&s1, &s2, &t1]);

        for (joint_realization, _) in &joint_pmf {
            let first_realization = vec![
                joint_realization[0].clone(),
                joint_realization[1].clone(),
                vec![joint_realization[2][0]],
            ];
            let p_joint = marg(&joint_pmf, joint_realization, 0, 2, true);
            let p_first = marg(&first_pmf, &first_realization, 0, 2, true);
            for collections in NODES2 {
                let p_union = union_prob(&joint_pmf, joint_realization, collections, 2, false);
                let p_joint_union = union_prob(&joint_pmf, joint_realization, collections, 2, true);
                let p_first_union =
                    union_prob(&first_pmf, &first_realization, collections, 2, true);

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
