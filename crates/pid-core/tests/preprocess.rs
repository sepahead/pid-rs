use pid_core::{HashProjector, Jitter, MatRef, PcaProjector, PidError};

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
