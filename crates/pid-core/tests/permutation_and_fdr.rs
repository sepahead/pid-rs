//! Public-API tests for the [`PermutationScheme`] machinery and the
//! Benjamini–Hochberg FDR adjustment.
//!
//! The load-bearing guarantees:
//! 1. The delegating wrappers (`permutation_pid3`, `permutation_rows_pvalue`) are
//!    **bit-identical** to the `_with(FullShuffle)` variants at the same seed.
//! 2. `BlockShuffle` permutes equal-sized blocks while preserving order within each
//!    block, validates its finite-group preconditions, and is deterministic by seed.
//! 3. `CircularShift` really produces rotations, with offsets confined to
//!    `[min_shift, n − min_shift]`, and rejects degenerate configurations.
//! 4. `benjamini_hochberg` matches hand-computed step-up q-values, clamps to 1,
//!    passes `NaN` through while counting failed hypotheses conservatively in `m`, and rejects
//!    invalid p-values.

use std::cell::RefCell;

use pid_core::{
    benjamini_hochberg, permutation_pid3, permutation_pid3_with, permutation_rows_pvalue,
    permutation_rows_pvalue_with, MatOwned, MatRef, PermutationScheme, Pid3Config,
};

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
    assert_eq!(
        a.p_value.to_bits(),
        b.p_value.to_bits(),
        "p must be bit-identical"
    );
    assert_eq!(a.n_valid, b.n_valid);
    assert_eq!(a.observed.to_bits(), b.observed.to_bits());
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

    let cfg = Pid3Config::default();
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
    assert_eq!(old.atoms.len(), new.atoms.len());
    for (oa, na) in old.atoms.iter().zip(&new.atoms) {
        assert_eq!(
            oa.p_value.to_bits(),
            na.p_value.to_bits(),
            "atom {:?}: p must be bit-identical",
            oa.antichain
        );
    }
    assert_eq!(old.scheme, PermutationScheme::FullShuffle);
    assert_eq!(new.scheme, PermutationScheme::FullShuffle);
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
    assert_eq!(full.p_value.to_bits(), blocks.p_value.to_bits());
    assert_eq!(full.n_attempted, blocks.n_attempted);
    assert_eq!(full.n_valid, blocks.n_valid);
    assert_eq!(full.shuffled_index, blocks.shuffled_index);
    assert_eq!(full.scheme, PermutationScheme::FullShuffle);
    assert_eq!(
        blocks.scheme,
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
    assert!(
        r.p_value <= 0.15,
        "true alignment should survive the rotation null: p = {}",
        r.p_value
    );
}

#[test]
fn benjamini_hochberg_matches_hand_computed_qvalues() {
    // m = 4, sorted p = [.005, .01, .03, .04] → raw q = [.02, .02, .04, .04];
    // step-up running-min leaves [.02, .02, .04, .04]; mapped back to input order.
    let q = benjamini_hochberg(&[0.01, 0.04, 0.03, 0.005]).unwrap();
    let expect = [0.02, 0.04, 0.04, 0.02];
    for (i, (&got, &want)) in q.iter().zip(&expect).enumerate() {
        assert!((got - want).abs() < 1e-12, "q[{i}] = {got}, want {want}");
    }
}

#[test]
fn benjamini_hochberg_clamps_monotone_and_handles_nan() {
    // Clamp to 1 and enforce monotonicity of the step-up walk.
    let q = benjamini_hochberg(&[0.9, 0.95]).unwrap();
    assert!(
        (q[0] - 0.95).abs() < 1e-12 && (q[1] - 0.95).abs() < 1e-12,
        "{q:?}"
    );

    // NaN passes through but counts conservatively toward the declared 3-test family.
    let q = benjamini_hochberg(&[0.02, f64::NAN, 0.5]).unwrap();
    assert!((q[0] - 0.06).abs() < 1e-12, "{q:?}");
    assert!(q[1].is_nan(), "{q:?}");
    assert!((q[2] - 0.75).abs() < 1e-12, "{q:?}");

    // Invalid inputs error.
    assert!(benjamini_hochberg(&[]).is_err());
    assert!(benjamini_hochberg(&[1.5]).is_err());
    assert!(benjamini_hochberg(&[-0.1]).is_err());
}
