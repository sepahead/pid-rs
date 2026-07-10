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

use pid_core::{
    block_bootstrap, discrete_pid2, isx_redundancy, ksg_local_mi_terms, pid2_isx, pid3_isx,
    red_degree_discrete, vul_degree_discrete, Antichain3, BootstrapConfig, DiscretePid2Result,
    IsxConfig, KsgConfig, MatOwned, NegativeHandling, Pid2Config, Pid3Config,
};

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

fn ksg_cfg() -> KsgConfig {
    KsgConfig {
        k: 4,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    }
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

fn discrete_pid2_bits(result: &DiscretePid2Result) -> [u64; 7] {
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
        checksum, KSG_LOCAL_TERMS_CHECKSUM,
        "KSG local-MI term bits diverged"
    );
    assert_eq!(terms[0].to_bits(), KSG_LOCAL_TERM_0);
    assert_eq!(terms[N / 2].to_bits(), KSG_LOCAL_TERM_MID);
    assert_eq!(terms[N - 1].to_bits(), KSG_LOCAL_TERM_LAST);
}

#[test]
fn isx_redundancy_matches_serial_reference() {
    let (s1, s2, _s3, t) = make_system(N, SEED);
    let cfg = IsxConfig {
        k: 4,
        ..Default::default()
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
            ..Default::default()
        },
    };
    let r = pid2_isx(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(
        r.redundancy.to_bits(),
        PID2_RED_BITS,
        "pid2 Red bits diverged"
    );
    assert_eq!(
        r.unique_s1.to_bits(),
        PID2_UNQ1_BITS,
        "pid2 Unq1 bits diverged"
    );
    assert_eq!(
        r.unique_s2.to_bits(),
        PID2_UNQ2_BITS,
        "pid2 Unq2 bits diverged"
    );
    assert_eq!(r.synergy.to_bits(), PID2_SYN_BITS, "pid2 Syn bits diverged");
}

#[test]
fn pid3_atoms_match_serial_reference() {
    let (s1, s2, s3, t) = make_system(N, SEED);
    let cfg = Pid3Config {
        k: 4,
        ..Default::default()
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
    assert_eq!(atom_checksum, PID3_ATOM_CHECKSUM, "pid3 atom bits diverged");
    assert_eq!(
        red_checksum, PID3_RED_CHECKSUM,
        "pid3 redundancy bits diverged"
    );
    // Pin two individual atoms to localize a failure.
    let unq_s1 = r
        .atom(Antichain3::try_from_sets(&[0b001]).unwrap())
        .unwrap();
    let full_syn = r
        .atom(Antichain3::try_from_sets(&[0b111]).unwrap())
        .unwrap();
    assert_eq!(unq_s1.to_bits(), PID3_ATOM_001_BITS);
    assert_eq!(full_syn.to_bits(), PID3_ATOM_111_BITS);
}

#[test]
fn block_bootstrap_matches_serial_reference() {
    // A bootstrap over a KSG-MI statistic exercises the resample loop (the path made parallel
    // in `block_bootstrap`) with a non-trivial, RNG-order-sensitive statistic.
    let (s1, _s2, _s3, t) = make_system(N, SEED);
    let s1v = s1.clone();
    let tv = t.clone();
    let data: Vec<f64> = (0..N).map(|i| s1v.as_ref().row(i)[0]).collect();
    let cfg = BootstrapConfig {
        n_boot: 64,
        block_size: 12,
        seed: 7,
        alpha: 0.05,
    };
    // Statistic: KSG MI between the resampled 1-D column and the (fixed-length) target.
    let result = block_bootstrap(&data, &cfg, move |samples| {
        let m = samples.len();
        let x = MatOwned::new(samples.to_vec(), m, 1).unwrap();
        // Pair with the first m target rows so the statistic is well-defined for the
        // truncated resample length.
        let y_data: Vec<f64> = (0..m).map(|i| tv.as_ref().row(i)[0]).collect();
        let y = MatOwned::new(y_data, m, 1).unwrap();
        pid_core::ksg_mi(x.as_ref(), y.as_ref(), &ksg_cfg()).unwrap_or(f64::NAN)
    })
    .unwrap();
    assert_eq!(
        result.point_estimate.to_bits(),
        BOOT_POINT_BITS,
        "bootstrap point bits diverged"
    );
    assert_eq!(
        result.boot_mean.to_bits(),
        BOOT_MEAN_BITS,
        "bootstrap mean bits diverged"
    );
    assert_eq!(
        result.boot_se.to_bits(),
        BOOT_SE_BITS,
        "bootstrap SE bits diverged"
    );
    assert_eq!(
        result.ci_low.to_bits(),
        BOOT_CI_LOW_BITS,
        "bootstrap ci_low bits diverged"
    );
    assert_eq!(
        result.ci_high.to_bits(),
        BOOT_CI_HIGH_BITS,
        "bootstrap ci_high bits diverged"
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
    let expected =
        discrete_pid2_bits(&discrete_pid2(s1.as_ref(), s2.as_ref(), target.as_ref(), 6).unwrap());

    for _ in 0..32 {
        let actual = discrete_pid2(s1.as_ref(), s2.as_ref(), target.as_ref(), 6).unwrap();
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
const KSG_LOCAL_TERMS_CHECKSUM: u64 = 13714940533098631;
const KSG_LOCAL_TERM_0: u64 = 4611372573292626840;
const KSG_LOCAL_TERM_MID: u64 = 4608683422432580648;
const KSG_LOCAL_TERM_LAST: u64 = 4609053335123176930;
const ISX_REDUNDANCY_BITS: u64 = 4608069949341515057;
const PID2_RED_BITS: u64 = 4608069949341515057;
const PID2_UNQ1_BITS: u64 = 4590324628664985552;
const PID2_UNQ2_BITS: u64 = 13821388618758278360;
const PID2_SYN_BITS: u64 = 4591732782175302464;
const PID3_ATOM_CHECKSUM: u64 = 9260367673030977354;
const PID3_RED_CHECKSUM: u64 = 12358916445694697;
const PID3_ATOM_001_BITS: u64 = 13803885910316531136;
const PID3_ATOM_111_BITS: u64 = 4587721666143598784;
const BOOT_POINT_BITS: u64 = 4608755814359965444;
const BOOT_MEAN_BITS: u64 = 4572425370828128894;
const BOOT_SE_BITS: u64 = 4587373921562974537;
const BOOT_CI_LOW_BITS: u64 = 13814458274299527561;
const BOOT_CI_HIGH_BITS: u64 = 4593556301919050283;
