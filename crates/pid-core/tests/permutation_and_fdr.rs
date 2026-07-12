#![cfg(feature = "experimental-pipelines")]

//! Public-API tests for the [`PermutationScheme`] machinery and the
//! Benjamini–Hochberg FDR adjustment.
//!
//! The load-bearing guarantees:
//! 1. The delegating wrappers (`permutation_pid3`, `permutation_rows_pvalue`) are
//!    **bit-identical** to the explicit `FullShuffle` + `Upper` variants at the same seed.
//! 2. Signed lower-tail inference on `T` is bit-identical to upper-tail inference on `-T`.
//! 3. `BlockShuffle` permutes equal-sized blocks while preserving order within each
//!    block, validates its finite-group preconditions, and is deterministic by seed.
//! 4. `CircularShift` really produces rotations, with offsets confined to
//!    `[min_shift, n − min_shift]`, and rejects degenerate configurations.
//! 5. `benjamini_hochberg` matches hand-computed step-up q-values, clamps to 1, and rejects
//!    missing/non-finite or out-of-range p-values instead of emitting sentinel q-values.

use std::cell::RefCell;

use pid_core::experimental::mixed_dimension_pid3::Pid3Config;
use pid_core::experimental::pipelines::{
    benjamini_hochberg, benjamini_yekutieli, permutation_pid3, permutation_pid3_with,
    permutation_pid3_with_tail, permutation_rows_pvalue as permutation_rows_pvalue_impl,
    permutation_rows_pvalue_with as permutation_rows_pvalue_with_impl,
    permutation_rows_pvalue_with_tail as permutation_rows_pvalue_with_tail_impl,
    PermutationAlgorithmRevision, PermutationCalibration, PermutationFamily,
    PermutationNullAssumption, PermutationReplicateStatus, PermutationScheme, PermutationTail,
    RowPermutationStat, StatisticCallbackDeclaration,
};
use pid_core::{MatOwned, MatRef, ResourceEstimate};

mod common;
use common::Rng64;

fn col(data: Vec<f64>) -> MatOwned {
    let n = data.len();
    MatOwned::new(data, n, 1).expect("column matrix")
}

/// A cheap aligned-sum statistic: mean of the products of the first two matrices'
/// first columns (a covariance-like alignment score, finite for any input).
fn alignment_stat(mats: &[MatRef<'_>]) -> pid_core::PidResult<f64> {
    let n = mats[0].nrows();
    let mut acc = 0.0;
    for i in 0..n {
        acc += mats[0].row(i)[0] * mats[1].row(i)[0];
    }
    Ok(acc / n as f64)
}

fn callback() -> StatisticCallbackDeclaration {
    StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO)
}

fn permutation_rows_pvalue<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    statistic: F,
) -> pid_core::PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> pid_core::PidResult<f64>,
{
    permutation_rows_pvalue_impl(mats, shuffled_index, n_perm, seed, callback(), statistic)
}

fn permutation_rows_pvalue_with<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    statistic: F,
) -> pid_core::PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> pid_core::PidResult<f64>,
{
    permutation_rows_pvalue_with_impl(
        mats,
        shuffled_index,
        n_perm,
        seed,
        scheme,
        callback(),
        statistic,
    )
}

fn permutation_rows_pvalue_with_tail<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    tail: PermutationTail,
    statistic: F,
) -> pid_core::PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> pid_core::PidResult<f64>,
{
    permutation_rows_pvalue_with_tail_impl(
        mats,
        shuffled_index,
        n_perm,
        seed,
        scheme,
        tail,
        callback(),
        statistic,
    )
}

fn complete_values(result: &RowPermutationStat) -> Vec<Vec<u64>> {
    result
        .replicates
        .iter()
        .map(|replicate| {
            let PermutationReplicateStatus::Complete { statistics } = &replicate.status else {
                panic!("expected complete permutation outcome");
            };
            statistics.iter().map(|value| value.to_bits()).collect()
        })
        .collect()
}

fn family(id: u64, size: usize) -> PermutationFamily {
    PermutationFamily::new(id, size).unwrap()
}

fn capture_block_orders(n: usize, block_size: usize, n_perm: usize, seed: u64) -> Vec<Vec<usize>> {
    let x = col((0..n).map(|i| i as f64).collect());
    let y = col(vec![1.0; n]);
    let mats = [x.as_ref(), y.as_ref()];
    let orders: RefCell<Vec<Vec<usize>>> = RefCell::new(Vec::new());
    let observe = |mats: &[MatRef<'_>]| -> pid_core::PidResult<f64> {
        let order = (0..n / block_size)
            .map(|output_block| mats[0].row(output_block * block_size)[0] as usize / block_size)
            .collect();
        orders.borrow_mut().push(order);
        Ok(1.0)
    };

    permutation_rows_pvalue_with(
        &mats,
        0,
        n_perm,
        seed,
        PermutationScheme::BlockShuffle { block_size },
        observe,
    )
    .expect("valid block shuffle");
    orders.into_inner()
}

#[test]
fn full_shuffle_wrapper_is_bit_identical_for_rows_pvalue() {
    let mut rng = Rng64::new(0xF00D);
    let x = col((0..160).map(|_| rng.normal()).collect());
    let y = col((0..160).map(|_| rng.normal()).collect());
    let mats = [x.as_ref(), y.as_ref()];

    let a = permutation_rows_pvalue(&mats, 0, 37, 42, alignment_stat).unwrap();
    let b = permutation_rows_pvalue_with(
        &mats,
        0,
        37,
        42,
        PermutationScheme::FullShuffle,
        alignment_stat,
    )
    .unwrap();
    let explicit = permutation_rows_pvalue_with_tail(
        &mats,
        0,
        37,
        42,
        PermutationScheme::FullShuffle,
        PermutationTail::Upper,
        alignment_stat,
    )
    .unwrap();

    assert_eq!(a.tail_fraction, b.tail_fraction);
    assert_eq!(b.tail_fraction, explicit.tail_fraction);
    assert_eq!(complete_values(&a), complete_values(&b));
    assert_eq!(complete_values(&b), complete_values(&explicit));
    assert_eq!(explicit.null.tail, PermutationTail::Upper);
    assert_eq!(
        explicit.null.assumption,
        PermutationNullAssumption::ExchangeableRows
    );
    assert_eq!(
        explicit.null.calibration,
        PermutationCalibration::MonteCarloPValue
    );
    assert_eq!(explicit.null.seed, 42);
    assert_eq!(explicit.null.family.size, 1);
    assert_eq!(
        explicit.null.algorithm_revision,
        PermutationAlgorithmRevision::SeededRowTransformV1
    );
}

#[test]
fn lower_tail_of_t_is_bit_identical_to_upper_tail_of_negated_t() {
    let mut rng = Rng64::new(0x51_6E_ED);
    let x = col((0..96).map(|_| rng.normal()).collect());
    let y = col((0..96).map(|_| rng.normal()).collect());
    let mats = [x.as_ref(), y.as_ref()];
    let lower = permutation_rows_pvalue_with_tail(
        &mats,
        0,
        73,
        9,
        PermutationScheme::FullShuffle,
        PermutationTail::Lower,
        alignment_stat,
    )
    .unwrap();
    let upper_negated = permutation_rows_pvalue_with_tail(
        &mats,
        0,
        73,
        9,
        PermutationScheme::FullShuffle,
        PermutationTail::Upper,
        |permuted| Ok(-alignment_stat(permuted)?),
    )
    .unwrap();

    assert_eq!(
        lower.tail_fraction.unwrap().to_bits(),
        upper_negated.tail_fraction.unwrap().to_bits()
    );
    assert_eq!(
        lower.observed.to_bits(),
        (-upper_negated.observed).to_bits()
    );
    assert_eq!(lower.n_valid, upper_negated.n_valid);
    assert_eq!(lower.null.tail, PermutationTail::Lower);
    assert_eq!(upper_negated.null.tail, PermutationTail::Upper);
}

#[test]
fn full_shuffle_wrapper_is_bit_identical_for_pid3() {
    let mut rng = Rng64::new(0xBEEF);
    let n = 60;
    let v = col((0..n).map(|_| rng.normal()).collect());
    let l = col((0..n).map(|_| rng.normal()).collect());
    let d = col((0..n).map(|_| rng.normal()).collect());
    let a: Vec<f64> = (0..n)
        .map(|i| v.as_ref().row(i)[0] + 0.5 * rng.normal())
        .collect();
    let a = col(a);

    let cfg = Pid3Config {
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::assume_regular_full_dimensional()
    };
    let old = permutation_pid3(
        v.as_ref(),
        l.as_ref(),
        d.as_ref(),
        a.as_ref(),
        &cfg,
        3,
        0,
        7,
    )
    .unwrap();
    let new = permutation_pid3_with(
        v.as_ref(),
        l.as_ref(),
        d.as_ref(),
        a.as_ref(),
        &cfg,
        3,
        0,
        7,
        PermutationScheme::FullShuffle,
    )
    .unwrap();
    let explicit = permutation_pid3_with_tail(
        v.as_ref(),
        l.as_ref(),
        d.as_ref(),
        a.as_ref(),
        &cfg,
        3,
        0,
        7,
        PermutationScheme::FullShuffle,
        PermutationTail::Upper,
    )
    .unwrap();
    let lower = permutation_pid3_with_tail(
        v.as_ref(),
        l.as_ref(),
        d.as_ref(),
        a.as_ref(),
        &cfg,
        3,
        0,
        7,
        PermutationScheme::FullShuffle,
        PermutationTail::Lower,
    )
    .unwrap();
    assert_eq!(old.atoms.len(), new.atoms.len());
    assert_eq!(new.atoms.len(), explicit.atoms.len());
    for ((old_atom, new_atom), explicit_atom) in
        old.atoms.iter().zip(&new.atoms).zip(&explicit.atoms)
    {
        assert_eq!(old_atom.antichain, new_atom.antichain);
        assert_eq!(new_atom.antichain, explicit_atom.antichain);
        assert_eq!(
            [old_atom.observed.to_bits(), new_atom.observed.to_bits()],
            [explicit_atom.observed.to_bits(); 2]
        );
        assert_eq!(
            [
                old_atom.tail_fraction.unwrap().to_bits(),
                new_atom.tail_fraction.unwrap().to_bits(),
            ],
            [explicit_atom.tail_fraction.unwrap().to_bits(); 2],
            "atom {:?}: p must be bit-identical",
            old_atom.antichain
        );
        assert_eq!(
            [old_atom.n_valid, new_atom.n_valid],
            [explicit_atom.n_valid; 2]
        );
    }
    assert_eq!([old.n_perm, new.n_perm], [explicit.n_perm; 2]);
    assert_eq!(
        [old.source_shuffled, new.source_shuffled],
        [explicit.source_shuffled; 2]
    );
    assert_eq!(old.null.scheme, PermutationScheme::FullShuffle);
    assert_eq!(new.null.scheme, PermutationScheme::FullShuffle);
    assert_eq!(explicit.null.scheme, PermutationScheme::FullShuffle);
    assert_eq!(old.null.tail, PermutationTail::Upper);
    assert_eq!(new.null.tail, PermutationTail::Upper);
    assert_eq!(explicit.null.tail, PermutationTail::Upper);
    assert_eq!(lower.null.tail, PermutationTail::Lower);
    assert!(lower
        .atoms
        .iter()
        .all(|atom| atom.tail_fraction.is_some_and(f64::is_finite)));
}

#[test]
fn block_shuffle_preserves_blocks_and_within_block_order() {
    let n = 24usize;
    let block_size = 4usize;
    let n_blocks = n / block_size;
    let x = col((0..n).map(|i| i as f64).collect());
    let y = col(vec![1.0; n]);
    let mats = [x.as_ref(), y.as_ref()];
    let orders: RefCell<Vec<Vec<usize>>> = RefCell::new(Vec::new());
    let observe = |mats: &[MatRef<'_>]| -> pid_core::PidResult<f64> {
        let shuffled = mats[0];
        let mut order = Vec::with_capacity(n_blocks);
        for output_block in 0..n_blocks {
            let output_start = output_block * block_size;
            let input_start = shuffled.row(output_start)[0] as usize;
            assert_eq!(
                input_start % block_size,
                0,
                "output block {output_block} starts inside an input block"
            );
            for offset in 0..block_size {
                assert_eq!(
                    shuffled.row(output_start + offset)[0] as usize,
                    input_start + offset,
                    "within-block order changed in output block {output_block}"
                );
            }
            order.push(input_start / block_size);
        }
        let mut sorted = order.clone();
        sorted.sort_unstable();
        assert_eq!(sorted, (0..n_blocks).collect::<Vec<_>>());
        orders.borrow_mut().push(order);
        Ok(1.0)
    };

    permutation_rows_pvalue_with(
        &mats,
        0,
        16,
        0xB10C,
        PermutationScheme::BlockShuffle { block_size },
        observe,
    )
    .unwrap();

    let orders = orders.into_inner();
    assert_eq!(orders.len(), 17, "observed pass plus 16 block shuffles");
    assert!(
        orders[1..].iter().any(|order| *order != orders[0]),
        "seed unexpectedly produced only identity block permutations"
    );
}

#[test]
fn block_shuffle_is_deterministic_at_a_fixed_seed() {
    let first = capture_block_orders(24, 4, 20, 0xD37E);
    let second = capture_block_orders(24, 4, 20, 0xD37E);
    assert_eq!(first, second);
}

#[test]
fn unit_block_fixture_matches_full_shuffle_numerically_and_reports_scheme() {
    let x = col((0..32).map(|i| i as f64).collect());
    let y = col((0..32).map(|i| (i * i) as f64).collect());
    let mats = [x.as_ref(), y.as_ref()];

    let full = permutation_rows_pvalue_with(
        &mats,
        0,
        23,
        99,
        PermutationScheme::FullShuffle,
        alignment_stat,
    )
    .unwrap();
    let blocks = permutation_rows_pvalue_with(
        &mats,
        0,
        23,
        99,
        PermutationScheme::BlockShuffle { block_size: 1 },
        alignment_stat,
    )
    .unwrap();

    assert_eq!(full.observed.to_bits(), blocks.observed.to_bits());
    assert_eq!(
        full.tail_fraction.unwrap().to_bits(),
        blocks.tail_fraction.unwrap().to_bits()
    );
    assert_eq!(full.n_attempted, blocks.n_attempted);
    assert_eq!(full.n_valid, blocks.n_valid);
    assert_eq!(full.shuffled_index, blocks.shuffled_index);
    assert_eq!(full.null.scheme, PermutationScheme::FullShuffle);
    assert_eq!(
        blocks.null.scheme,
        PermutationScheme::BlockShuffle { block_size: 1 }
    );
}

#[test]
fn block_shuffle_rejects_non_group_configurations() {
    let x = col((0..12).map(|i| i as f64).collect());
    let y = col(vec![0.0; 12]);
    let mats = [x.as_ref(), y.as_ref()];

    for block_size in [0, 5, 12] {
        let result = permutation_rows_pvalue_with(
            &mats,
            0,
            5,
            1,
            PermutationScheme::BlockShuffle { block_size },
            alignment_stat,
        );
        assert!(
            result.is_err(),
            "block_size={block_size} must fail for n=12"
        );
    }
}

#[test]
fn block_shuffle_accepts_equal_sized_multiple_blocks() {
    let x = col((0..12).map(|i| i as f64).collect());
    let y = col(vec![0.0; 12]);
    let mats = [x.as_ref(), y.as_ref()];

    let result = permutation_rows_pvalue_with(
        &mats,
        0,
        5,
        1,
        PermutationScheme::BlockShuffle { block_size: 4 },
        alignment_stat,
    );
    assert!(
        result.is_ok(),
        "three equal blocks should form a valid group"
    );
}

#[test]
fn permutation_rows_rejects_zero_row_matrices() {
    let x = MatOwned::new(Vec::new(), 0, 1).unwrap();
    let y = MatOwned::new(Vec::new(), 0, 1).unwrap();
    let mats = [x.as_ref(), y.as_ref()];

    let result = permutation_rows_pvalue(&mats, 0, 5, 1, |_| Ok(0.0));
    assert!(result.is_err(), "zero-row matrices must be rejected");
}

#[test]
fn circular_shift_produces_bounded_rotations() {
    // Recognisable payload: x[i] = i, so a rotation is identifiable and its offset
    // recoverable from the shuffled matrix the statistic receives.
    let n = 50usize;
    let min_shift = 8usize;
    let x = col((0..n).map(|i| i as f64).collect());
    let y = col(vec![1.0; n]);
    let mats = [x.as_ref(), y.as_ref()];

    let offsets: RefCell<Vec<usize>> = RefCell::new(Vec::new());
    let observe = |mats: &[MatRef<'_>]| -> pid_core::PidResult<f64> {
        let m = mats[0];
        // The first call is the observed (unshuffled) pass: offset 0. Record all.
        let k = m.row(0)[0] as usize; // rotation offset: row 0 holds x[(0 + k) % n] = k
                                      // Verify it is a *rotation* of 0..n, not an arbitrary permutation.
        for i in 0..m.nrows() {
            assert_eq!(
                m.row(i)[0] as usize,
                (i + k) % n,
                "not a rotation at row {i}"
            );
        }
        offsets.borrow_mut().push(k);
        Ok(1.0)
    };

    permutation_rows_pvalue_with(
        &mats,
        0,
        25,
        123,
        PermutationScheme::CircularShift { min_shift },
        observe,
    )
    .unwrap();

    let offsets = offsets.into_inner();
    assert_eq!(
        offsets[0], 0,
        "first evaluation is the unshuffled observed pass"
    );
    assert_eq!(offsets.len(), 26, "observed + 25 permutations");
    for &k in &offsets[1..] {
        assert!(
            (min_shift..=n - min_shift).contains(&k),
            "offset {k} outside [{min_shift}, {}]",
            n - min_shift
        );
    }
    // With 25 draws over 35 admissible offsets, the null must not be degenerate.
    let distinct: std::collections::BTreeSet<usize> = offsets[1..].iter().copied().collect();
    assert!(
        distinct.len() > 5,
        "rotation offsets look degenerate: {distinct:?}"
    );
}

#[test]
fn circular_shift_rejects_degenerate_configs() {
    let x = col((0..10).map(|i| i as f64).collect());
    let y = col(vec![0.0; 10]);
    let mats = [x.as_ref(), y.as_ref()];

    // min_shift = 0 is meaningless (identity rotation would enter the null).
    assert!(permutation_rows_pvalue_with(
        &mats,
        0,
        5,
        1,
        PermutationScheme::CircularShift { min_shift: 0 },
        alignment_stat,
    )
    .is_err());
    // Validation must reject arithmetic overflow instead of panicking in debug builds or
    // wrapping into an apparently valid range in release builds.
    assert!(permutation_rows_pvalue_with(
        &mats,
        0,
        5,
        1,
        PermutationScheme::CircularShift {
            min_shift: usize::MAX,
        },
        alignment_stat,
    )
    .is_err());
    // n = 10 < 2*5 + 1: only one admissible offset — refuse.
    assert!(permutation_rows_pvalue_with(
        &mats,
        0,
        5,
        1,
        PermutationScheme::CircularShift { min_shift: 5 },
        alignment_stat,
    )
    .is_err());
    // n = 10 >= 2*4 + 1: two admissible offsets — accepted.
    assert!(permutation_rows_pvalue_with(
        &mats,
        0,
        5,
        1,
        PermutationScheme::CircularShift { min_shift: 4 },
        alignment_stat,
    )
    .is_ok());
}

#[test]
fn circular_shift_detects_true_alignment_on_autocorrelated_data() {
    // A slowly varying (strongly autocorrelated) series aligned with itself plus
    // noise: every rotation destroys the alignment, so the observed statistic
    // should beat (nearly) all rotations — small p under the dependence-respecting
    // null, at an n_perm giving p as low as 1/(1+19) = 0.05.
    let mut rng = Rng64::new(0xA11C);
    let n = 240usize;
    let x: Vec<f64> = (0..n)
        .map(|i| (i as f64 * 0.07).sin() + 0.1 * rng.normal())
        .collect();
    let y: Vec<f64> = x.iter().map(|&v| v + 0.1 * rng.normal()).collect();
    let (x, y) = (col(x), col(y));
    let mats = [x.as_ref(), y.as_ref()];

    let r = permutation_rows_pvalue_with(
        &mats,
        0,
        19,
        9,
        PermutationScheme::CircularShift { min_shift: 24 },
        alignment_stat,
    )
    .unwrap();
    assert_eq!(
        r.null.calibration,
        PermutationCalibration::ApproximateSurrogateScore
    );
    assert_eq!(
        r.null.assumption,
        PermutationNullAssumption::WeaklyStationarySeries { minimum_shift: 24 }
    );
    assert!(
        r.tail_fraction.unwrap() <= 0.15,
        "true alignment should survive the rotation null: p = {}",
        r.tail_fraction.unwrap()
    );
}

#[test]
fn benjamini_hochberg_matches_hand_computed_qvalues() {
    // m = 4, sorted p = [.005, .01, .03, .04] → raw q = [.02, .02, .04, .04];
    // step-up running-min leaves [.02, .02, .04, .04]; mapped back to input order.
    let declared_family = family(77, 4);
    let report = benjamini_hochberg(&[0.01, 0.04, 0.03, 0.005], declared_family).unwrap();
    assert_eq!(report.family, declared_family);
    let q = report.adjusted_p_values;
    let expect = [0.02, 0.04, 0.04, 0.02];
    for (i, (&got, &want)) in q.iter().zip(&expect).enumerate() {
        assert!((got - want).abs() < 1e-12, "q[{i}] = {got}, want {want}");
    }
}

#[test]
fn benjamini_hochberg_clamps_monotone_and_rejects_missing_values() {
    // Clamp to 1 and enforce monotonicity of the step-up walk.
    let q = benjamini_hochberg(&[0.9, 0.95], family(1, 2))
        .unwrap()
        .adjusted_p_values;
    assert!(
        (q[0] - 0.95).abs() < 1e-12 && (q[1] - 0.95).abs() < 1e-12,
        "{q:?}"
    );

    // Invalid inputs error.
    assert!(benjamini_hochberg(&[], family(1, 1)).is_err());
    assert!(benjamini_hochberg(&[0.02, f64::NAN, 0.5], family(1, 3)).is_err());
    assert!(benjamini_hochberg(&[1.5], family(1, 1)).is_err());
    assert!(benjamini_hochberg(&[-0.1], family(1, 1)).is_err());
    assert!(benjamini_hochberg(&[0.1], family(1, 2)).is_err());
}

#[test]
fn benjamini_yekutieli_applies_arbitrary_dependence_correction() {
    let p = [0.01, 0.04, 0.03, 0.005];
    let declared_family = family(8, p.len());
    let bh_report = benjamini_hochberg(&p, declared_family).unwrap();
    let by_report = benjamini_yekutieli(&p, declared_family).unwrap();
    assert_eq!(bh_report.family, by_report.family);
    let bh = bh_report.adjusted_p_values;
    let by = by_report.adjusted_p_values;

    // For m=4, c(m)=1+1/2+1/3+1/4=25/12. On this fixture no value clamps at 1,
    // so every BY q-value is exactly the corresponding BH value times 25/12.
    let harmonic = 25.0 / 12.0;
    for (i, (&got, &bh_value)) in by.iter().zip(&bh).enumerate() {
        let expected = bh_value * harmonic;
        assert!(
            (got - expected).abs() < 1e-12,
            "q[{i}] = {got}, want {expected}"
        );
        assert!(got >= bh_value);
    }
}

#[test]
fn benjamini_yekutieli_rejects_missing_and_invalid_input() {
    assert!(benjamini_yekutieli(&[], family(1, 1)).is_err());
    assert!(benjamini_yekutieli(&[0.02, f64::NAN, 0.5], family(1, 3)).is_err());
    assert!(benjamini_yekutieli(&[f64::INFINITY], family(1, 1)).is_err());
    assert!(benjamini_yekutieli(&[-0.1], family(1, 1)).is_err());
}
