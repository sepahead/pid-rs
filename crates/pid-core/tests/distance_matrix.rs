use pid_core::diagnostics::{
    symmetric_distances, symmetric_distances_with_budget_and_cancellation,
};
use pid_core::{CancellationToken, MatRef, Metric, PidError, ResourceBudget};

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

#[test]
fn symmetric_distance_cancellation_preserves_parity_and_stops_mid_work() {
    let data = [0.0, 1.0, 3.0, 6.0];
    let matrix = MatRef::new(&data, 4, 1).unwrap();
    let baseline = symmetric_distances(matrix, Metric::Chebyshev).unwrap();
    let running = CancellationToken::new();
    let cancellable = symmetric_distances_with_budget_and_cancellation(
        matrix,
        Metric::Chebyshev,
        ResourceBudget::default(),
        &running,
    )
    .unwrap();
    assert_eq!(baseline.n(), cancellable.n());
    for row in 0..baseline.n() {
        for column in 0..baseline.n() {
            assert_eq!(
                baseline.get(row, column).to_bits(),
                cancellable.get(row, column).to_bits()
            );
        }
    }

    let cancelled = CancellationToken::new();
    cancelled.cancel();
    assert!(matches!(
        symmetric_distances_with_budget_and_cancellation(
            matrix,
            Metric::Chebyshev,
            ResourceBudget::default(),
            &cancelled,
        ),
        Err(PidError::Cancelled {
            operation: "symmetric_distances",
            completed_units: 0,
            ..
        })
    ));

    let n = 3_000usize;
    let dimensions = 16usize;
    let large_data: Vec<f64> = (0..n * dimensions)
        .map(|index| (index as f64).mul_add(0.000_031, (index % 17) as f64 * 0.000_001))
        .collect();
    let large = MatRef::new(&large_data, n, dimensions).unwrap();
    let token = std::sync::Arc::new(CancellationToken::new());
    let canceller = std::sync::Arc::clone(&token);
    let request = std::thread::spawn(move || {
        std::thread::sleep(std::time::Duration::from_millis(5));
        canceller.cancel();
    });
    let error = symmetric_distances_with_budget_and_cancellation(
        large,
        Metric::Chebyshev,
        ResourceBudget::default(),
        token.as_ref(),
    )
    .unwrap_err();
    request.join().unwrap();
    assert!(matches!(
        error,
        PidError::Cancelled {
            operation: "symmetric_distances",
            ..
        }
    ));
}
