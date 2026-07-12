use pid_core::diagnostics::symmetric_distances;
use pid_core::{MatRef, Metric};

#[test]
fn symmetric_distance_matrix_get_matches_metric() {
    let n = 4;
    let x: Vec<f64> = vec![0.0, 1.0, 3.0, 6.0];
    let m = MatRef::new(&x, n, 1).unwrap();

    let dm = symmetric_distances(m, Metric::Chebyshev).unwrap();
    assert_eq!(dm.n(), n);

    for i in 0..n {
        assert_eq!(dm.get(i, i), 0.0);
    }
    for i in 0..n {
        for j in 0..n {
            let expected = (x[i] - x[j]).abs();
            let got = dm.get(i, j);
            assert!(
                (got - expected).abs() < 1e-12,
                "d({i},{j}) mismatch: got={got} expected={expected}"
            );
        }
    }
}

#[test]
#[should_panic(expected = "row index 4 outside 0..4")]
fn symmetric_distance_matrix_rejects_equal_out_of_bounds_indices() {
    let x = [0.0, 1.0, 3.0, 6.0];
    let matrix = MatRef::new(&x, 4, 1).unwrap();
    let distances = symmetric_distances(matrix, Metric::Chebyshev).unwrap();

    let _ = distances.get(4, 4);
}
