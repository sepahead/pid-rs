#![cfg(feature = "experimental-pipelines")]

use pid_core::experimental::pipelines::Jitter;
use pid_core::stable::preprocessing::{
    ConstantColumnPolicy, HashProjector, PcaProjector, Standardizer,
};
use pid_core::{MatRef, PidError, ResourceBudget};

fn mat_equal(a: MatRef<'_>, b: MatRef<'_>, tol: f64) -> bool {
    if a.nrows() != b.nrows() || a.ncols() != b.ncols() {
        return false;
    }
    for i in 0..a.nrows() {
        for (&av, &bv) in a.row(i).iter().zip(b.row(i).iter()) {
            if (av - bv).abs() > tol {
                return false;
            }
        }
    }
    true
}

#[test]
fn hash_projector_is_deterministic() {
    let n = 4;
    let d = 7;
    let x: Vec<f64> = (0..(n * d)).map(|i| (i as f64) * 0.01).collect();
    let x = MatRef::new(&x, n, d).unwrap();

    let p1 = HashProjector::new(d, 3, 123).unwrap();
    let p2 = HashProjector::new(d, 3, 123).unwrap();

    let y1 = p1.transform(x).unwrap();
    let y2 = p2.transform(x).unwrap();

    assert!(mat_equal(y1.as_ref(), y2.as_ref(), 0.0));
}

/// CountSketch unbiasedness regression: `E[||Pv||²] = ||v||²` requires the ±1 sign hash to be
/// independent of the bucket hash (Charikar–Chen–Farach-Colton 2002). With the old
/// sign-from-bucket-parity scheme every feature colliding in a bucket carried the SAME sign for
/// even `out_dim`, so for the all-ones vector `||Pv||²` concentrated near `d²/out_dim` (≈16384
/// here) instead of `||v||²` (= 512) — a 32× inflation. We average over many seeds and assert
/// the mean is near `||v||²`; the biased scheme fails this bound by two orders of magnitude.
#[test]
fn hash_projector_norm_is_unbiased_for_even_out_dim() {
    let d = 512;
    let out_dim = 16; // even: the regime where sign-from-bucket-parity degenerates
    let v = vec![1.0f64; d]; // maximally "correlated" features: worst case for collisions
    let x = MatRef::new(&v, 1, d).unwrap();
    let norm_sq_true = d as f64; // ||v||² = 512

    let n_seeds = 200;
    let mut mean_norm_sq = 0.0;
    for seed in 0..n_seeds {
        let p = HashProjector::new(d, out_dim, 1000 + seed as u64).unwrap();
        let y = p.transform(x).unwrap();
        let norm_sq: f64 = y.as_ref().row(0).iter().map(|&z| z * z).sum();
        mean_norm_sq += norm_sq;
    }
    mean_norm_sq /= n_seeds as f64;

    // Per-seed std of ||Pv||² is ~sqrt(2·||v||⁴/out_dim) ≈ 181, so the 200-seed mean has
    // SE ≈ 13; 60 is ≈ 4.7σ. The pre-fix biased value (~16384) is unreachable.
    assert!(
        (mean_norm_sq - norm_sq_true).abs() < 60.0,
        "CountSketch norm not unbiased: mean ||Pv||² = {mean_norm_sq:.1}, want ≈ {norm_sq_true:.1}"
    );
}

#[test]
fn hash_projector_shapes_and_finite() {
    let n = 3;
    let d = 5;
    let x: Vec<f64> = (0..(n * d)).map(|i| (i as f64) - 3.0).collect();
    let x = MatRef::new(&x, n, d).unwrap();

    let p = HashProjector::new(d, 2, 7).unwrap();
    let y = p.transform(x).unwrap();
    let y = y.as_ref();

    assert_eq!(y.nrows(), n);
    assert_eq!(y.ncols(), 2);
    for i in 0..n {
        assert!(y.row(i).iter().all(|v| v.is_finite()));
    }
}

#[test]
fn hash_projector_reports_unrepresentable_output_allocation() {
    let data = [1.0];
    let x = MatRef::new(&data, 1, 1).unwrap();
    let projector = HashProjector::new(1, usize::MAX, 7).unwrap();

    let error = projector.transform(x).unwrap_err();

    assert!(matches!(
        error,
        PidError::ResourceLimitExceeded { .. } | PidError::SizeOverflow { .. }
    ));
}

#[test]
fn hash_projector_preserves_a_representable_sum_after_extreme_cancellation() {
    // For this deterministic projector the three signs are [+1, +1, -1]. A raw left-to-right
    // accumulator overflows at MAX + MAX even though the final sketch value is exactly MAX.
    let data = [f64::MAX; 3];
    let x = MatRef::new(&data, 1, 3).unwrap();
    let projector = HashProjector::new(3, 1, 7).unwrap();

    let projected = projector.transform(x).unwrap();

    assert_eq!(projected.as_ref().row(0)[0], f64::MAX);
}

#[test]
fn jitter_std_zero_is_identity() {
    let n = 2;
    let d = 4;
    let x: Vec<f64> = vec![0.0, 1.0, 2.0, 3.0, -1.0, -2.0, -3.0, -4.0];
    let x = MatRef::new(&x, n, d).unwrap();

    let j = Jitter::new(0.0, 999).unwrap();
    let y = j.apply(x).unwrap();
    assert!(mat_equal(x, y.as_ref(), 0.0));
}

#[test]
fn jitter_is_deterministic_given_seed() {
    let n = 2;
    let d = 6;
    let x: Vec<f64> = (0..(n * d)).map(|i| (i as f64) * 0.1).collect();
    let x = MatRef::new(&x, n, d).unwrap();

    let j1 = Jitter::new(0.01, 2026).unwrap();
    let j2 = Jitter::new(0.01, 2026).unwrap();
    let y1 = j1.apply(x).unwrap();
    let y2 = j2.apply(x).unwrap();

    assert!(mat_equal(y1.as_ref(), y2.as_ref(), 0.0));
}

#[test]
fn preprocess_rejects_invalid_configs() {
    assert!(HashProjector::new(0, 2, 1).is_err());
    assert!(HashProjector::new(2, 0, 1).is_err());
    assert!(Jitter::new(-1.0, 0).is_err());
    assert!(Jitter::new(f64::NAN, 0).is_err());
}

#[test]
fn pca_projector_shapes_and_direction_sanity() {
    // A simple 2D dataset concentrated along the x-axis.
    let n = 200usize;
    let d = 2usize;
    let mut data = Vec::with_capacity(n * d);
    for i in 0..n {
        let x = i as f64;
        data.push(x);
        data.push(0.0);
    }
    let xref = MatRef::new(&data, n, d).unwrap();

    let p = PcaProjector::fit(xref, 1).unwrap();
    assert_eq!(p.in_dim(), 2);
    assert_eq!(p.out_dim(), 1);

    // Component should be (approximately) aligned with the x-axis (sign is arbitrary).
    let w = p.components();
    assert_eq!(w.len(), 2);
    assert!(w[0].abs() > 0.99, "w={w:?}");
    assert!(w[1].abs() < 1e-8, "w={w:?}");

    let y = p.transform(xref).unwrap();
    assert_eq!(y.as_ref().nrows(), n);
    assert_eq!(y.as_ref().ncols(), 1);
}

#[test]
fn pca_matches_svd_subspace_on_fixed_data() {
    // Validate that our PCA implementation matches a direct SVD-based PCA subspace (the
    // scikit-learn-style approach), up to the usual sign/rotation ambiguities.
    use nalgebra as na;

    let n = 40usize;
    let d = 15usize;
    let k = 5usize;

    // Deterministic pseudo-random data (no RNG deps).
    //
    // Important: avoid low-rank constructions here; we want k < rank(Xc) so the PCA subspace is
    // well-defined (otherwise the "top-k" subspace can drift arbitrarily in the nullspace).
    let mut data = Vec::with_capacity(n * d);
    let mut state = 0xA5A5_5A5A_DEAD_BEEFu64;
    for _ in 0..(n * d) {
        // xorshift64*
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        state = state.wrapping_mul(0x2545_F491_4F6C_DD1D);
        // 53 bits -> [0, 1)
        let u = (state >> 11) as f64 * (1.0 / ((1u64 << 53) as f64));
        data.push(u - 0.5);
    }
    let xref = MatRef::new(&data, n, d).unwrap();

    let p = PcaProjector::fit(xref, k).unwrap();
    let w1 = na::DMatrix::from_row_slice(k, d, p.components());

    // Center X and compute SVD: Xc = U S V^T, so PCA components are rows of V^T.
    let mut mean = vec![0.0f64; d];
    for i in 0..n {
        for j in 0..d {
            mean[j] += data[i * d + j];
        }
    }
    for m in &mut mean {
        *m /= n as f64;
    }
    let mut centered = Vec::with_capacity(n * d);
    for i in 0..n {
        for j in 0..d {
            centered.push(data[i * d + j] - mean[j]);
        }
    }
    let xc = na::DMatrix::from_row_slice(n, d, &centered);
    let svd = na::linalg::SVD::new(xc, false, true);
    let vt = svd.v_t.expect("requested V^T");

    // nalgebra does not guarantee singular values are already sorted. Build PCA components by
    // selecting the top-k singular vectors explicitly.
    let svals: Vec<f64> = svd.singular_values.iter().copied().collect();
    let mut order: Vec<usize> = (0..d).collect();
    order.sort_by(|&a, &b| svals[b].partial_cmp(&svals[a]).unwrap());

    let mut w2_data = Vec::with_capacity(k * d);
    for &idx in order.iter().take(k) {
        for c in 0..d {
            w2_data.push(vt[(idx, c)]);
        }
    }
    let w2 = na::DMatrix::from_row_slice(k, d, &w2_data);

    // Compare the k-dim row subspaces via singular values of W1 * W2^T (should all be ~1).
    let m = &w1 * w2.transpose();
    let sv = na::linalg::SVD::new(m, false, false).singular_values;
    for s in sv.iter().copied() {
        assert!(
            (s - 1.0).abs() < 1e-6,
            "subspace mismatch: singular value {s}"
        );
    }
}

#[test]
fn pca_rejects_too_many_components() {
    let n = 5usize;
    let d = 3usize;
    let data = vec![0.0f64; n * d];
    let xref = MatRef::new(&data, n, d).unwrap();

    // After centering, rank ≤ n-1, so requesting out_dim = n is invalid.
    let err = PcaProjector::fit(xref, n).unwrap_err();
    match err {
        PidError::InvalidConfig { context, .. } => assert_eq!(context, "PcaProjector::fit"),
        other => panic!("unexpected error: {other:?}"),
    }
}

#[test]
fn pca_rejects_component_in_numerical_null_space() {
    // Rank-1 data (all three columns identical): the centered Gram has a single nonzero
    // eigenvalue. `out_dim = 2` clears the `out_dim <= min(d, n-1)` shape check, so the 2nd
    // component's eigenvalue is at the noise floor — it must be rejected (M1) rather than
    // amplified by `1/sqrt(lambda)` into a garbage component.
    let n = 8usize;
    let d = 3usize;
    let mut data = Vec::with_capacity(n * d);
    for i in 0..n {
        let v = i as f64; // varying signal along one direction only
        for _ in 0..d {
            data.push(v); // identical across all columns => rank 1
        }
    }
    let xref = MatRef::new(&data, n, d).unwrap();

    // out_dim = 1 (the true rank) succeeds.
    assert!(PcaProjector::fit(xref, 1).is_ok());

    // out_dim = 2 requests a null-space direction -> NumericalInstability.
    let err = PcaProjector::fit(xref, 2).unwrap_err();
    assert!(
        matches!(err, PidError::NumericalInstability { .. }),
        "expected NumericalInstability for a null-space component, got {err:?}"
    );
}

#[test]
fn pca_is_invariant_to_tiny_uniform_scaling() {
    let base = [0.0, 0.0, 1.0, 0.2, 2.0, 0.1, 3.0, 0.3];
    let tiny: Vec<f64> = base.iter().map(|value| value * 1.0e-200).collect();
    let base_ref = MatRef::new(&base, 4, 2).unwrap();
    let tiny_ref = MatRef::new(&tiny, 4, 2).unwrap();

    let (base_scores, base_projector) = PcaProjector::fit_transform(base_ref, 1).unwrap();
    let (tiny_scores, tiny_projector) = PcaProjector::fit_transform(tiny_ref, 1).unwrap();

    let alignment: f64 = base_projector
        .components()
        .iter()
        .zip(tiny_projector.components())
        .map(|(&a, &b)| a * b)
        .sum();
    assert!((alignment.abs() - 1.0).abs() < 1.0e-12);
    for i in 1..4 {
        let base_distance = (base_scores.as_ref().row(i)[0] - base_scores.as_ref().row(0)[0]).abs();
        let tiny_distance = (tiny_scores.as_ref().row(i)[0] - tiny_scores.as_ref().row(0)[0]).abs();
        assert!((tiny_distance / 1.0e-200 - base_distance).abs() < 1.0e-12);
    }
}

#[test]
fn pca_rejects_truncation_through_a_tied_eigenspace() {
    let tied_cloud = [1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, -1.0];
    let x = MatRef::new(&tied_cloud, 4, 2).unwrap();

    let error = PcaProjector::fit(x, 1).unwrap_err();

    assert!(matches!(error, PidError::NumericalInstability { .. }));
    assert!(PcaProjector::fit(x, 2).is_ok());
}

#[test]
fn pca_fits_opposite_extremes_without_centering_overflow() {
    let data = [-f64::MAX, 0.0, f64::MAX, 0.0, 0.0, 1.0];
    let x = MatRef::new(&data, 3, 2).unwrap();

    let projector = PcaProjector::fit(x, 1).unwrap();

    assert!(projector.components().iter().all(|value| value.is_finite()));
    assert!(projector.components()[0].abs() > 0.99);
}

#[test]
fn pca_ignores_a_huge_constant_offset_without_erasing_tiny_variation() {
    let data = [
        f64::MAX,
        0.0,
        f64::MAX,
        1.0e-200,
        f64::MAX,
        2.0e-200,
        f64::MAX,
        3.0e-200,
    ];
    let x = MatRef::new(&data, 4, 2).unwrap();

    let (scores, projector) = PcaProjector::fit_transform(x, 1).unwrap();

    assert!(projector.components()[0].abs() < 1.0e-12);
    assert!(projector.components()[1].abs() > 0.99);
    for row in 1..4 {
        let step = (scores.as_ref().row(row)[0] - scores.as_ref().row(row - 1)[0]).abs();
        assert!(
            (step / 1.0e-200 - 1.0).abs() < 1.0e-12,
            "row={row} step={step}"
        );
    }
}

#[test]
fn pca_rejects_unrepresentable_centered_dynamic_range() {
    let smallest = f64::from_bits(1);
    let data = [-f64::MAX, 0.0, f64::MAX, smallest];
    let x = MatRef::new(&data, 2, 2).unwrap();

    let error = PcaProjector::fit(x, 1).unwrap_err();

    assert!(matches!(error, PidError::NumericalInstability { .. }));
}

#[test]
fn standardizer_constant_column_policies_are_distinct_on_held_out_rows() {
    let training = [5.0, 0.0, 5.0, 1.0, 5.0, 2.0, 5.0, 3.0];
    let held_out = [9.0, 4.0, 1.0, 5.0];
    let training = MatRef::new(&training, 4, 2).unwrap();
    let held_out = MatRef::new(&held_out, 2, 2).unwrap();

    assert!(Standardizer::fit(training, ConstantColumnPolicy::Error).is_err());

    let zero = Standardizer::fit(training, ConstantColumnPolicy::Zero).unwrap();
    let zero_scores = zero.transform(held_out).unwrap();
    assert_eq!(zero_scores.as_ref().ncols(), 2);
    assert_eq!(zero_scores.as_ref().row(0)[0], 0.0);
    assert_eq!(zero_scores.as_ref().row(1)[0], 0.0);

    let centered = Standardizer::fit(training, ConstantColumnPolicy::LeaveCentered).unwrap();
    let centered_scores = centered.transform(held_out).unwrap();
    assert_eq!(centered_scores.as_ref().row(0)[0], 4.0);
    assert_eq!(centered_scores.as_ref().row(1)[0], -4.0);

    let dropped = Standardizer::fit(training, ConstantColumnPolicy::Drop).unwrap();
    let dropped_scores = dropped.transform(held_out).unwrap();
    assert_eq!(dropped.retained_columns(), &[1]);
    assert_eq!(dropped_scores.as_ref().ncols(), 1);
}

#[test]
fn standardizer_fit_transform_checks_simultaneous_state_and_output_peak() {
    let data = [0.0, 2.0, 1.0, 1.0, 2.0, 0.0, 3.0, -1.0];
    let matrix = MatRef::new(&data, 4, 2).unwrap();
    let budget = ResourceBudget::new(120, u64::MAX, u128::MAX, 1).unwrap();

    // Fitted state + column scratch (112 bytes on supported 64-bit release targets) and the
    // output alone (64 bytes) each fit, but retained state + output (144 bytes) does not.
    let fitted =
        Standardizer::fit_with_budget(matrix, ConstantColumnPolicy::Error, budget).unwrap();
    fitted.transform_with_budget(matrix, budget).unwrap();
    assert!(matches!(
        Standardizer::fit_transform_with_budget(matrix, ConstantColumnPolicy::Error, budget,),
        Err(PidError::ResourceLimitExceeded {
            operation: "Standardizer::fit_transform",
            resource: "bytes",
            ..
        })
    ));
}

#[test]
fn pca_fit_accepts_a_caller_budget_at_its_reported_resource_boundary() {
    let data = [0.0, 0.0, 1.0, 2.0, 2.0, 1.0, 3.0, 4.0];
    let matrix = MatRef::new(&data, 4, 2).unwrap();
    let estimate = PcaProjector::fit_resource_estimate(matrix, 1).unwrap();
    let budget = ResourceBudget::new(
        u64::try_from(estimate.estimated_bytes).unwrap(),
        u64::try_from(estimate.pairwise_distances).unwrap(),
        estimate.operations_hint,
        1,
    )
    .unwrap();

    let projector = PcaProjector::fit_with_budget(matrix, 1, budget).unwrap();

    assert_eq!(projector.out_dim(), 1);
}

#[test]
fn fitted_preprocessors_expose_deterministic_training_and_parameter_hashes() {
    let data = [0.0, 2.0, 1.0, 1.0, 2.0, 0.0, 3.0, -1.0];
    let changed = [0.0, 2.0, 1.0, 1.0, 2.0, 0.0, 3.1, -1.0];
    let data = MatRef::new(&data, 4, 2).unwrap();
    let changed = MatRef::new(&changed, 4, 2).unwrap();

    let standardizer_a = Standardizer::fit(data, ConstantColumnPolicy::Error).unwrap();
    let standardizer_b = Standardizer::fit(data, ConstantColumnPolicy::Error).unwrap();
    let standardizer_changed = Standardizer::fit(changed, ConstantColumnPolicy::Error).unwrap();
    assert_eq!(
        standardizer_a.training_data_hash_sha256(),
        standardizer_b.training_data_hash_sha256()
    );
    assert_eq!(
        standardizer_a.parameter_hash_sha256(),
        standardizer_b.parameter_hash_sha256()
    );
    assert_ne!(
        standardizer_a.training_data_hash_sha256(),
        standardizer_changed.training_data_hash_sha256()
    );

    let pca_a = PcaProjector::fit(data, 1).unwrap();
    let pca_b = PcaProjector::fit(data, 1).unwrap();
    assert_eq!(
        pca_a.training_data_hash_sha256(),
        pca_b.training_data_hash_sha256()
    );
    assert_eq!(pca_a.parameter_hash_sha256(), pca_b.parameter_hash_sha256());

    let hash_a = HashProjector::new(5, 2, 17).unwrap();
    let hash_b = HashProjector::new(5, 2, 17).unwrap();
    let hash_c = HashProjector::new(5, 2, 18).unwrap();
    assert_eq!(
        hash_a.parameter_hash_sha256(),
        hash_b.parameter_hash_sha256()
    );
    assert_ne!(
        hash_a.parameter_hash_sha256(),
        hash_c.parameter_hash_sha256()
    );
}
