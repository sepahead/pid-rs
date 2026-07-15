#![cfg(all(feature = "experimental-pipelines", feature = "parallel"))]

//! Serial == parallel **bit-identity** guard.
//!
//! The `parallel` (rayon) feature is required to be bit-for-bit identical to the serial path
//! (`f64::to_bits` equality) — a non-negotiable project convention. This test pins that
//! contract for every estimator that the `parallel` feature touches:
//!
//! - `ksg_local_mi_terms` (the per-point KSG local MI contributions),
//! - the 2-source PID atoms (`pid2_isx`),
//! - the 3-source PID atoms / redundancies (`pid3_isx`, whose `redundancy_for_antichain` is
//!   the parallelized hot loop),
//! - the continuous `I^sx_∩` redundancy (`isx_redundancy`, `IsxMethod::EhrlichKsg`), and
//! - a block-bootstrap result (`block_bootstrap`).
//!
//! Strategy: the expected values below are **frozen `f64::to_bits` patterns captured from the
//! serial build** (`cargo test -p pid-core`). The same test then runs under
//! `cargo test -p pid-core --features parallel`; if any parallelized path changed a single bit,
//! the corresponding `assert_eq!` on `to_bits()` fails. Running it in *both* configurations is
//! what makes it a serial==parallel guard: the serial run proves the frozen constants are the
//! serial truth, the parallel run proves the parallel path reproduces them exactly.
//!
//! The constants are NOT scientific ground truth — they are whatever the (unchanged) serial
//! estimator produces on this fixed synthetic dataset; the test's only job is to detect any
//! serial/parallel divergence (or any accidental change to the serial numbers).
//!
//! The count-based tests use a deliberately non-uniform empirical distribution and compare
//! repeated calls with `f64::to_bits`. Those paths do not use Rayon; their guard catches
//! iteration-order nondeterminism in histogram accumulation across invocations.

use pid_core::diagnostics::{red_degree_discrete, vul_degree_discrete};
use pid_core::experimental::continuous::raw_scalars::{isx_redundancy, ksg_local_mi_terms};
use pid_core::experimental::continuous::{pid2_isx, IsxConfig, Pid2Config};
use pid_core::experimental::mixed_dimension_pid3::{pid3_isx, Antichain3, Pid3Config};
use pid_core::experimental::pipelines::{
    block_bootstrap, block_bootstrap_with_budget,
    exploratory_same_sample_quantized_imin_pid2 as discrete_pid2, BlockLengthSelection,
    BootstrapConfig, BootstrapReplicateStatus, ResamplingValidityDeclaration,
    StatisticCallbackDeclaration,
};
use pid_core::stable::continuous::{
    ksg_mi_report_with_budget, KsgConfig, KsgMiReport, KsgProvenance, NegativeHandling,
};
use pid_core::stable::imin::IminPid2Result;
use pid_core::{MatOwned, ResourceBudget, ResourceEstimate};

mod common;
use common::Rng64;

/// Deterministic synthetic system: V and L share a latent signal that drives the target A;
/// D is an independent noisy copy. Fixed seed, so the data is identical on every run and in
/// both feature configurations.
fn make_system(n: usize, seed: u64) -> (MatOwned, MatOwned, MatOwned, MatOwned) {
    let mut rng = Rng64::new(seed);
    let mut s1 = Vec::with_capacity(n * 2);
    let mut s2 = Vec::with_capacity(n * 2);
    let mut s3 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let signal = rng.normal();
        s1.push(signal + 0.2 * rng.normal());
        s1.push(0.5 * rng.normal());
        s2.push(signal + 0.3 * rng.normal());
        s2.push(0.5 * rng.normal());
        s3.push(0.7 * signal + 0.7 * rng.normal());
        t.push(signal + 0.1 * rng.normal());
    }
    (
        MatOwned::new(s1, n, 2).unwrap(),
        MatOwned::new(s2, n, 2).unwrap(),
        MatOwned::new(s3, n, 1).unwrap(),
        MatOwned::new(t, n, 1).unwrap(),
    )
}

const N: usize = 120;
const SEED: u64 = 20240917;
const THREAD_BUDGET_N: usize = 48;

fn ksg_cfg() -> KsgConfig {
    KsgConfig::assume_regular_full_dimensional()
        .with_k(4)
        .with_negative_handling(NegativeHandling::Allow)
}

/// An irregular empirical PMF with many distinct probabilities. Using uniform logic-gate data
/// here would let reordered floating-point accumulation accidentally produce the same bits.
fn nonuniform_discrete_labels() -> [Vec<u32>; 4] {
    let states = [
        (0, 4, 1, 9, 17),
        (0, 2, 1, 8, 5),
        (1, 4, 0, 8, 13),
        (1, 2, 2, 7, 7),
        (2, 3, 0, 7, 11),
        (2, 3, 2, 6, 3),
        (3, 1, 1, 6, 19),
        (3, 0, 2, 5, 2),
        (4, 1, 3, 5, 23),
        (4, 0, 3, 4, 6),
        (5, 2, 4, 4, 29),
        (5, 4, 0, 9, 4),
    ];
    let n = states.iter().map(|state| state.4).sum();
    let mut labels = std::array::from_fn(|_| Vec::with_capacity(n));
    for &(x, y, z, w, count) in &states {
        for _ in 0..count {
            labels[0].push(x);
            labels[1].push(y);
            labels[2].push(z);
            labels[3].push(w);
        }
    }
    labels
}

fn discrete_pid2_bits(result: &IminPid2Result) -> [u64; 7] {
    [
        result.redundancy.to_bits(),
        result.unique_s1.to_bits(),
        result.unique_s2.to_bits(),
        result.synergy.to_bits(),
        result.mi_s1_t.to_bits(),
        result.mi_s2_t.to_bits(),
        result.mi_s1s2_t.to_bits(),
    ]
}

fn thread_limits_through_available_maximum() -> Vec<usize> {
    let mut limits = vec![1, 2, 3, 4, ResourceBudget::default().max_threads];
    limits.sort_unstable();
    limits.dedup();
    limits
}

fn budget_with_threads(max_threads: usize) -> ResourceBudget {
    let mut budget = ResourceBudget::default();
    budget.max_threads = max_threads;
    budget
}

fn normalize_ksg_resource_accounting(report: &mut KsgMiReport) {
    report.resource_budget = budget_with_threads(1);
    report.resource_estimate = ResourceEstimate::ZERO;
}

fn pid3_bits(result: &pid_core::experimental::mixed_dimension_pid3::Pid3Result) -> Vec<u64> {
    result
        .redundancies
        .iter()
        .map(|entry| entry.value.to_bits())
        .chain(result.atoms.iter().map(|entry| entry.value.to_bits()))
        .collect()
}

fn bootstrap_result_bits(result: &pid_core::experimental::pipelines::BootstrapResult) -> Vec<u64> {
    let mut bits = vec![result.point_estimate.to_bits()];
    let summary = result
        .summary
        .as_ref()
        .expect("the deterministic statistic must complete for every replicate");
    bits.extend([
        summary.resample_mean.to_bits(),
        summary.resample_standard_deviation.to_bits(),
        summary.percentile_lower.to_bits(),
        summary.percentile_upper.to_bits(),
    ]);
    for outcome in &result.replicates {
        bits.push(outcome.replicate_index as u64);
        match &outcome.status {
            BootstrapReplicateStatus::Complete { value } => bits.push(value.to_bits()),
            BootstrapReplicateStatus::Failed { error } => {
                panic!("deterministic bootstrap replicate failed: {error}")
            }
            _ => panic!("unexpected future bootstrap replicate status"),
        }
    }
    bits
}

#[test]
fn ksg_report_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let (s1, _s2, _s3, target) = make_system(THREAD_BUDGET_N, SEED ^ 0x4B53_4701);
    let provenance = KsgProvenance::new("identity", "seeded continuous fixture", None).unwrap();
    let mut expected = ksg_mi_report_with_budget(
        s1.as_ref(),
        target.as_ref(),
        &ksg_cfg(),
        &provenance,
        budget_with_threads(1),
    )
    .unwrap();
    normalize_ksg_resource_accounting(&mut expected);

    for max_threads in thread_limits_through_available_maximum() {
        let mut actual = ksg_mi_report_with_budget(
            s1.as_ref(),
            target.as_ref(),
            &ksg_cfg(),
            &provenance,
            budget_with_threads(max_threads),
        )
        .unwrap();
        normalize_ksg_resource_accounting(&mut actual);
        assert_eq!(
            actual, expected,
            "KSG report changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn pid2_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let (s1, s2, _s3, target) = make_system(THREAD_BUDGET_N, SEED ^ 0x5049_4432);
    let cfg = Pid2Config {
        ksg: ksg_cfg(),
        isx: IsxConfig {
            k: 4,
            ..IsxConfig::assume_regular_full_dimensional()
        },
    };
    let expected = pid_core::experimental::continuous::pid2_isx_with_budget(
        s1.as_ref(),
        s2.as_ref(),
        target.as_ref(),
        &cfg,
        budget_with_threads(1),
    )
    .unwrap();

    for max_threads in thread_limits_through_available_maximum() {
        let actual = pid_core::experimental::continuous::pid2_isx_with_budget(
            s1.as_ref(),
            s2.as_ref(),
            target.as_ref(),
            &cfg,
            budget_with_threads(max_threads),
        )
        .unwrap();
        assert_eq!(
            actual, expected,
            "PID2 atoms changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn pid3_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let (s0, s1, s2, target) = make_system(THREAD_BUDGET_N, SEED ^ 0x5049_4433);
    let cfg = Pid3Config {
        k: 4,
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::assume_regular_full_dimensional()
    };
    let expected = pid3_bits(
        &pid_core::experimental::mixed_dimension_pid3::pid3_isx_with_budget(
            s0.as_ref(),
            s1.as_ref(),
            s2.as_ref(),
            target.as_ref(),
            &cfg,
            budget_with_threads(1),
        )
        .unwrap(),
    );

    for max_threads in thread_limits_through_available_maximum() {
        let actual = pid3_bits(
            &pid_core::experimental::mixed_dimension_pid3::pid3_isx_with_budget(
                s0.as_ref(),
                s1.as_ref(),
                s2.as_ref(),
                target.as_ref(),
                &cfg,
                budget_with_threads(max_threads),
            )
            .unwrap(),
        );
        assert_eq!(
            actual, expected,
            "PID3 coordinates changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn bootstrap_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let data: Vec<f64> = (0..THREAD_BUDGET_N)
        .map(|index| ((index % 19) as i32 - 9) as f64 / 8.0)
        .collect();
    let cfg = BootstrapConfig::new(
        32,
        6,
        0x4255_4447_4554,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let evaluate = |max_threads| {
        block_bootstrap_with_budget(
            &data,
            &cfg,
            budget_with_threads(max_threads),
            StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
            |samples| Ok(samples.iter().sum::<f64>() / samples.len() as f64),
        )
        .map(|result| bootstrap_result_bits(&result))
    };
    let expected = evaluate(1).unwrap();

    for max_threads in thread_limits_through_available_maximum() {
        let actual = evaluate(max_threads).unwrap();
        assert_eq!(
            actual, expected,
            "bootstrap distribution changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn ksg_local_mi_terms_match_serial_reference() {
    let (s1, _s2, _s3, t) = make_system(N, SEED);
    let terms = ksg_local_mi_terms(s1.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();
    assert_eq!(terms.len(), N);
    // Frozen reference: bit-pattern checksum + the first/last/mid term bits. We XOR-fold all
    // term bits into one u64 so a divergence at any index trips the checksum, then also pin a
    // few individual terms to localize a failure.
    let checksum = terms.iter().fold(0u64, |acc, &x| acc ^ x.to_bits());
    assert_eq!(
        [
            checksum,
            terms[0].to_bits(),
            terms[N / 2].to_bits(),
            terms[N - 1].to_bits(),
        ],
        [
            KSG_LOCAL_TERMS_CHECKSUM,
            KSG_LOCAL_TERM_0,
            KSG_LOCAL_TERM_MID,
            KSG_LOCAL_TERM_LAST,
        ],
        "KSG local-MI term bits diverged"
    );
}

#[test]
fn isx_redundancy_matches_serial_reference() {
    let (s1, s2, _s3, t) = make_system(N, SEED);
    let cfg = IsxConfig {
        k: 4,
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let red = isx_redundancy(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(red.to_bits(), ISX_REDUNDANCY_BITS, "I^sx_∩ bits diverged");
}

#[test]
fn pid2_atoms_match_serial_reference() {
    let (s1, s2, _s3, t) = make_system(N, SEED);
    let cfg = Pid2Config {
        ksg: ksg_cfg(),
        isx: IsxConfig {
            k: 4,
            ..IsxConfig::assume_regular_full_dimensional()
        },
    };
    let r = pid2_isx(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(
        [
            r.redundancy.to_bits(),
            r.unique_s1.to_bits(),
            r.unique_s2.to_bits(),
            r.synergy.to_bits(),
        ],
        [PID2_RED_BITS, PID2_UNQ1_BITS, PID2_UNQ2_BITS, PID2_SYN_BITS],
        "pid2 atom bits diverged"
    );
}

#[test]
fn pid3_atoms_match_serial_reference() {
    let (s1, s2, s3, t) = make_system(N, SEED);
    let cfg = Pid3Config {
        k: 4,
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::assume_regular_full_dimensional()
    };
    let r = pid3_isx(s1.as_ref(), s2.as_ref(), s3.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(r.atoms.len(), 18);
    // XOR-fold every atom's bits (order is the canonical antichain order, fixed) and every
    // redundancy's bits — `redundancy_for_antichain` is the parallelized loop.
    let atom_checksum = r.atoms.iter().fold(0u64, |acc, a| acc ^ a.value.to_bits());
    let red_checksum = r
        .redundancies
        .iter()
        .fold(0u64, |acc, x| acc ^ x.value.to_bits());
    // Pin two individual atoms to localize a failure.
    let unq_s1 = r
        .atom(Antichain3::try_from_sets(&[0b001]).unwrap())
        .unwrap();
    let full_syn = r
        .atom(Antichain3::try_from_sets(&[0b111]).unwrap())
        .unwrap();
    assert_eq!(
        [
            atom_checksum,
            red_checksum,
            unq_s1.to_bits(),
            full_syn.to_bits(),
        ],
        [
            PID3_ATOM_CHECKSUM,
            PID3_RED_CHECKSUM,
            PID3_ATOM_001_BITS,
            PID3_ATOM_111_BITS,
        ],
        "pid3 bits diverged"
    );
}

#[test]
fn block_bootstrap_matches_serial_reference() {
    // A bootstrap over a floating-point mean exercises the resample loop (the path made parallel
    // in `block_bootstrap`) with a non-trivial, RNG-order-sensitive statistic. Unlike continuous
    // kNN estimators, the mean remains defined when with-replacement resampling duplicates rows.
    // Use exactly represented binary-rational inputs. The estimator fixtures above intentionally
    // exercise transcendental RNG output, but a frozen bootstrap *mean* must not depend on a
    // platform libm's last bits before the serial/parallel comparison even begins.
    let data: Vec<f64> = (0..N)
        .map(|i| ((i % 29) as i32 - 14) as f64 / 8.0)
        .collect();
    let cfg = BootstrapConfig::new(
        64,
        12,
        7,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let result = block_bootstrap(
        &data,
        &cfg,
        StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
        |samples| Ok(samples.iter().sum::<f64>() / samples.len() as f64),
    )
    .unwrap();
    let summary = result.summary.unwrap();
    assert_eq!(
        [
            result.point_estimate.to_bits(),
            summary.resample_mean.to_bits(),
            summary.resample_standard_deviation.to_bits(),
            summary.percentile_lower.to_bits(),
            summary.percentile_upper.to_bits(),
        ],
        [
            BOOT_POINT_BITS,
            BOOT_MEAN_BITS,
            BOOT_SE_BITS,
            BOOT_CI_LOW_BITS,
            BOOT_CI_HIGH_BITS,
        ],
        "bootstrap bits diverged"
    );
}

#[test]
fn discrete_pid2_is_bit_identical_across_repeated_calls() {
    let [x, y, z, w] = nonuniform_discrete_labels();
    let n = x.len();
    let mut s1_data = Vec::with_capacity(2 * n);
    for (&x_i, &w_i) in x.iter().zip(&w) {
        s1_data.extend([f64::from(x_i), f64::from(w_i)]);
    }
    let s1 = MatOwned::new(s1_data, n, 2).unwrap();
    let s2 = MatOwned::new(y.into_iter().map(f64::from).collect(), n, 1).unwrap();
    let target = MatOwned::new(z.into_iter().map(f64::from).collect(), n, 1).unwrap();
    let expected = discrete_pid2_bits(
        &discrete_pid2(s1.as_ref(), s2.as_ref(), target.as_ref(), 6)
            .unwrap()
            .into_categorical_result(),
    );

    for _ in 0..32 {
        let actual = discrete_pid2(s1.as_ref(), s2.as_ref(), target.as_ref(), 6)
            .unwrap()
            .into_categorical_result();
        assert_eq!(discrete_pid2_bits(&actual), expected);
    }
}

#[test]
fn red_degree_discrete_is_bit_identical_across_repeated_calls() {
    let labels = nonuniform_discrete_labels();
    let vars = labels.iter().map(Vec::as_slice).collect::<Vec<_>>();
    let expected = red_degree_discrete(&vars).unwrap().to_bits();

    for _ in 0..32 {
        assert_eq!(red_degree_discrete(&vars).unwrap().to_bits(), expected);
    }
}

#[test]
fn vul_degree_discrete_is_bit_identical_across_repeated_calls() {
    let labels = nonuniform_discrete_labels();
    let vars = labels.iter().map(Vec::as_slice).collect::<Vec<_>>();
    let expected = vul_degree_discrete(&vars).unwrap().to_bits();

    for _ in 0..32 {
        assert_eq!(vul_degree_discrete(&vars).unwrap().to_bits(), expected);
    }
}

// ── Frozen serial reference bit-patterns (captured from `cargo test -p pid-core`) ──
//
// The ISX/PID2 values below intentionally reflect deterministic Neumaier accumulation of the
// sample-index-ordered local terms. Compared with the former plain fold, only cancellation
// roundoff in the final local-term mean changes; neighbor selection and every local term are
// unchanged.
const KSG_LOCAL_TERMS_CHECKSUM: u64 = 13714940533901959;
const KSG_LOCAL_TERM_0: u64 = 4611372573292626840;
const KSG_LOCAL_TERM_MID: u64 = 4608683422432580648;
const KSG_LOCAL_TERM_LAST: u64 = 4609053335123176934;
const ISX_REDUNDANCY_BITS: u64 = 4608069949341512170;
const PID2_RED_BITS: u64 = 4608069949341512170;
const PID2_UNQ1_BITS: u64 = 4590324628665003312;
const PID2_UNQ2_BITS: u64 = 13821388618758275488;
const PID2_SYN_BITS: u64 = 4591732782175321616;
// Updated when PID3 local redundancy averages and exact Möbius linear combinations adopted
// deterministic Neumaier summation. Neighbor selection and local terms are unchanged; these new
// bits are the more accurate serial reduction and remain the serial/parallel identity oracle.
const PID3_ATOM_CHECKSUM: u64 = 9260367673031410956;
const PID3_RED_CHECKSUM: u64 = 12358916445649141;
const PID3_ATOM_001_BITS: u64 = 13803885910316517312;
const PID3_ATOM_111_BITS: u64 = 4587721666143603440;
const BOOT_POINT_BITS: u64 = 13811038857269521067;
const BOOT_MEAN_BITS: u64 = 4578959861135162299;
const BOOT_SE_BITS: u64 = 4597572063773922634;
const BOOT_CI_LOW_BITS: u64 = 13825206431097290752;
const BOOT_CI_HIGH_BITS: u64 = 4603598304096568388;
