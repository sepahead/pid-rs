#![cfg(feature = "experimental-hyperbolic")]

use pid_core::diagnostics::{
    continuous_input_diagnostics_resource_estimate, continuous_joint_shell_resource_estimate,
    distance_concentration_resource_estimate, intrinsic_dimension_resource_estimate,
    sampled_four_point_resource_estimate, symmetric_distance_resources_for, HyperbolicityConfig,
};
use pid_core::experimental::hyperbolic::{
    hyperbolic_continuous_input_diagnostics,
    hyperbolic_continuous_input_diagnostics_resource_estimate,
    hyperbolic_continuous_input_diagnostics_with_budget,
    hyperbolic_continuous_joint_shell_diagnostics,
    hyperbolic_continuous_joint_shell_diagnostics_with_budget,
    hyperbolic_continuous_joint_shell_resource_estimate,
    hyperbolic_distance_concentration_resource_estimate, hyperbolic_distance_concentration_stats,
    hyperbolic_distance_concentration_stats_with_budget, hyperbolic_intrinsic_dimension_multi_k,
    hyperbolic_intrinsic_dimension_report, hyperbolic_intrinsic_dimension_resource_estimate,
    hyperbolic_sampled_four_point_delta_summary,
    hyperbolic_sampled_four_point_delta_summary_with_budget,
    hyperbolic_sampled_four_point_delta_summary_with_budget_and_cancellation,
    hyperbolic_sampled_four_point_resource_estimate, hyperbolic_symmetric_distance_resources_for,
    hyperbolic_symmetric_distances, hyperbolic_symmetric_distances_with_budget,
    hyperbolic_symmetric_distances_with_budget_and_cancellation, HyperbolicCurvature,
    HyperbolicDistanceConcentrationConfig, HyperbolicFourPointConfig, HyperbolicIntrinsicDimConfig,
    HyperbolicMetric,
};
use pid_core::{CancellationToken, MatRef, PidError, ResourceBudget};

const CURVATURE: HyperbolicCurvature = HyperbolicCurvature::NegativeOne;
const METRIC: HyperbolicMetric = HyperbolicMetric::lorentz(CURVATURE);

fn line_points(parameters: &[f64]) -> Vec<f64> {
    let mut points = Vec::with_capacity(parameters.len() * 2);
    for &parameter in parameters {
        points.push(parameter.cosh());
        points.push(parameter.sinh());
    }
    points
}

fn tiny_budget() -> ResourceBudget {
    ResourceBudget::new(1, 1, 1, 1).unwrap()
}

fn assert_lorentz_width_error(error: PidError, context: &'static str) {
    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: actual_context,
            message: "Lorentz-hyperboloid inputs must have row width d+1 >= 2",
        } if actual_context == context
    ));
}

#[test]
fn typed_diagnostics_run_and_intrinsic_reports_retain_the_lorentz_metric() {
    let parameters = [0.0_f64, 0.07, 0.23, 0.51, 0.94, 1.58, 2.47, 3.61, 5.02];
    let data = line_points(&parameters);
    let points = MatRef::new(&data, parameters.len(), 2).unwrap();

    let distances = hyperbolic_symmetric_distances(points, METRIC).unwrap();
    assert_eq!(distances.n(), parameters.len());
    assert!((distances.get(0, 1) - (parameters[1] - parameters[0])).abs() < 1.0e-14);

    let concentration = hyperbolic_distance_concentration_stats(
        points,
        &HyperbolicDistanceConcentrationConfig::new(METRIC),
    )
    .unwrap();
    assert_eq!(concentration.pairwise_count, 36);
    assert!(concentration.pairwise_mean.is_finite());

    let input_diagnostics = hyperbolic_continuous_input_diagnostics(points, 3, METRIC).unwrap();
    assert_eq!(input_diagnostics.n_samples, parameters.len());
    assert_eq!(input_diagnostics.ambient_dimension, 2);
    assert_eq!(
        input_diagnostics.marginal_shells.query_count,
        parameters.len()
    );

    let joint_diagnostics =
        hyperbolic_continuous_joint_shell_diagnostics(&[points], 3, METRIC).unwrap();
    assert_eq!(joint_diagnostics.query_count, parameters.len());

    let intrinsic = hyperbolic_intrinsic_dimension_report(
        points,
        &HyperbolicIntrinsicDimConfig::new(METRIC).with_k(3),
        ResourceBudget::default(),
    )
    .unwrap();
    assert_eq!(intrinsic.metric, METRIC);
    assert_eq!(intrinsic.k, 3);
    assert_eq!(intrinsic.ambient_dimension, 2);
    assert_eq!(intrinsic.local_estimates.len(), parameters.len());
    assert!(intrinsic.mean.is_finite() && intrinsic.mean > 0.0);

    let trajectory =
        hyperbolic_intrinsic_dimension_multi_k(points, &[3, 4], METRIC, ResourceBudget::default())
            .unwrap();
    assert_eq!(trajectory.reports.len(), 2);
    assert!(trajectory
        .reports
        .iter()
        .all(|report| report.metric == METRIC));

    let four_point = hyperbolic_sampled_four_point_delta_summary(
        points,
        &HyperbolicFourPointConfig::new(METRIC)
            .with_n_samples(16)
            .with_seed(7),
    )
    .unwrap();
    assert_eq!(four_point.sample_count, 16);
    assert!(four_point.mean.is_finite());
}

#[test]
fn typed_resource_estimates_account_for_lorentz_coordinate_work() {
    let parameters = [0.0_f64, 0.07, 0.23, 0.51, 0.94, 1.58, 2.47, 3.61];
    let data = line_points(&parameters);
    let points = MatRef::new(&data, parameters.len(), 2).unwrap();

    let pairs = [
        (
            hyperbolic_symmetric_distance_resources_for(points).unwrap(),
            symmetric_distance_resources_for(points).unwrap(),
        ),
        (
            hyperbolic_distance_concentration_resource_estimate(points).unwrap(),
            distance_concentration_resource_estimate(points).unwrap(),
        ),
        (
            hyperbolic_intrinsic_dimension_resource_estimate(points).unwrap(),
            intrinsic_dimension_resource_estimate(points).unwrap(),
        ),
        (
            hyperbolic_continuous_input_diagnostics_resource_estimate(points).unwrap(),
            continuous_input_diagnostics_resource_estimate(points).unwrap(),
        ),
        (
            hyperbolic_continuous_joint_shell_resource_estimate(&[points]).unwrap(),
            continuous_joint_shell_resource_estimate(&[points]).unwrap(),
        ),
        (
            hyperbolic_sampled_four_point_resource_estimate(
                points,
                &HyperbolicFourPointConfig::new(METRIC).with_n_samples(8),
            )
            .unwrap(),
            sampled_four_point_resource_estimate(
                points,
                &HyperbolicityConfig::default().with_n_samples(8),
            )
            .unwrap(),
        ),
    ];

    for (hyperbolic, chebyshev) in pairs {
        assert_eq!(hyperbolic.estimated_bytes, chebyshev.estimated_bytes);
        assert_eq!(hyperbolic.pairwise_distances, chebyshev.pairwise_distances);
        assert!(hyperbolic.operations_hint > chebyshev.operations_hint);
    }
}

#[test]
fn distance_concentration_shape_error_precedes_lorentz_width_validation() {
    let one_column = [1.0_f64; 4];
    let one_row = MatRef::new(&one_column[..1], 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_distance_concentration_stats_with_budget(
            one_row,
            &HyperbolicDistanceConcentrationConfig::new(METRIC),
            tiny_budget(),
        ),
        Err(PidError::InvalidConfig {
            context: "distance_concentration_stats",
            message: "x must have at least 2 rows and 1 column",
        })
    ));
}

#[test]
fn intrinsic_k_error_precedes_lorentz_width_validation() {
    let one_column = [1.0_f64; 4];
    let four_rows = MatRef::new(&one_column, 4, 1).unwrap();

    assert!(matches!(
        hyperbolic_intrinsic_dimension_report(
            four_rows,
            &HyperbolicIntrinsicDimConfig::new(METRIC).with_k(4),
            tiny_budget(),
        ),
        Err(PidError::InvalidK { k: 4, n_samples: 4 })
    ));
}

#[test]
fn support_k_error_precedes_lorentz_width_validation() {
    let one_column = [1.0_f64; 4];
    let four_rows = MatRef::new(&one_column, 4, 1).unwrap();

    assert!(matches!(
        hyperbolic_continuous_input_diagnostics_with_budget(four_rows, 4, METRIC, tiny_budget(),),
        Err(PidError::InvalidK { k: 4, n_samples: 4 })
    ));
}

#[test]
fn four_point_shape_error_precedes_lorentz_width_validation() {
    let one_column = [1.0_f64; 4];

    let three_rows = MatRef::new(&one_column[..3], 3, 1).unwrap();
    assert!(matches!(
        hyperbolic_sampled_four_point_delta_summary_with_budget(
            three_rows,
            &HyperbolicFourPointConfig::new(METRIC).with_n_samples(1),
            tiny_budget(),
        ),
        Err(PidError::InvalidConfig {
            context: "sampled_four_point_delta_summary",
            message: "need at least 4 points to sample four-point deltas",
        })
    ));
}

#[test]
fn joint_shell_row_error_precedes_lorentz_width_validation() {
    let four_column_values = [1.0_f64; 4];
    let four_rows = MatRef::new(&four_column_values, 4, 1).unwrap();

    let three_column_values = [1.0_f64; 3];
    let mismatched_rows = MatRef::new(&three_column_values, 3, 1).unwrap();
    assert!(matches!(
        hyperbolic_continuous_joint_shell_diagnostics_with_budget(
            &[four_rows, mismatched_rows],
            2,
            METRIC,
            tiny_budget(),
        ),
        Err(PidError::RowCountMismatch {
            context: "continuous_joint_shell_diagnostics",
            left_rows: 4,
            right_rows: 3,
        })
    ));
}

#[test]
fn lorentz_width_errors_precede_resource_preflight() {
    let data = [1.0_f64; 5];
    let two_rows = MatRef::new(&data[..2], 2, 1).unwrap();
    let four_rows = MatRef::new(&data[..4], 4, 1).unwrap();
    let five_rows = MatRef::new(&data, 5, 1).unwrap();

    assert_lorentz_width_error(
        hyperbolic_symmetric_distances_with_budget(four_rows, METRIC, tiny_budget()).unwrap_err(),
        "symmetric_distances",
    );
    assert_lorentz_width_error(
        hyperbolic_distance_concentration_stats_with_budget(
            two_rows,
            &HyperbolicDistanceConcentrationConfig::new(METRIC),
            tiny_budget(),
        )
        .unwrap_err(),
        "distance_concentration_stats",
    );
    assert_lorentz_width_error(
        hyperbolic_intrinsic_dimension_report(
            five_rows,
            &HyperbolicIntrinsicDimConfig::new(METRIC).with_k(3),
            tiny_budget(),
        )
        .unwrap_err(),
        "intrinsic_dimension_levina_bickel",
    );
    assert_lorentz_width_error(
        hyperbolic_continuous_input_diagnostics_with_budget(four_rows, 2, METRIC, tiny_budget())
            .unwrap_err(),
        "continuous_input_diagnostics",
    );
    assert_lorentz_width_error(
        hyperbolic_continuous_joint_shell_diagnostics_with_budget(
            &[four_rows],
            2,
            METRIC,
            tiny_budget(),
        )
        .unwrap_err(),
        "continuous_joint_shell_diagnostics",
    );
    assert_lorentz_width_error(
        hyperbolic_sampled_four_point_delta_summary_with_budget(
            four_rows,
            &HyperbolicFourPointConfig::new(METRIC).with_n_samples(4),
            tiny_budget(),
        )
        .unwrap_err(),
        "sampled_four_point_delta_summary",
    );
}

#[test]
fn intrinsic_multi_k_rejects_every_k_before_aggregate_resource_preflight() {
    let parameters = [0.0_f64, 0.07, 0.23, 0.51, 0.94, 1.58, 2.47, 3.61];
    let data = line_points(&parameters);
    let points = MatRef::new(&data, parameters.len(), 2).unwrap();

    assert!(matches!(
        hyperbolic_intrinsic_dimension_multi_k(
            points,
            &[3, parameters.len()],
            METRIC,
            tiny_budget(),
        ),
        Err(PidError::InvalidK {
            k,
            n_samples,
        }) if k == parameters.len() && n_samples == parameters.len()
    ));
}

#[test]
fn one_row_symmetric_distance_still_validates_the_lorentz_point() {
    let invalid = [2.0_f64, 0.0];
    let invalid = MatRef::new(&invalid, 1, 2).unwrap();
    assert!(matches!(
        hyperbolic_symmetric_distances(invalid, METRIC),
        Err(PidError::InvalidConfig { .. })
    ));

    let valid = [1.0_f64, 0.0];
    let valid = MatRef::new(&valid, 1, 2).unwrap();
    let distances = hyperbolic_symmetric_distances(valid, METRIC).unwrap();
    assert_eq!(distances.n(), 1);
    assert_eq!(distances.get(0, 0), 0.0);
}

#[test]
fn typed_cancellation_reports_one_monotone_public_work_total() {
    let parameters = [0.0_f64, 0.23];
    let data = line_points(&parameters);
    let points = MatRef::new(&data, parameters.len(), 2).unwrap();
    let cancellation = CancellationToken::new();
    cancellation.cancel();

    assert!(matches!(
        hyperbolic_symmetric_distances_with_budget_and_cancellation(
            points,
            METRIC,
            ResourceBudget::default(),
            &cancellation,
        ),
        Err(PidError::Cancelled {
            operation: "symmetric_distances",
            completed_units: 0,
            total_units: 3,
        })
    ));

    let parameters = [0.0_f64, 0.07, 0.23, 0.51];
    let data = line_points(&parameters);
    let points = MatRef::new(&data, parameters.len(), 2).unwrap();
    let config = HyperbolicFourPointConfig::new(METRIC).with_n_samples(5);
    assert!(matches!(
        hyperbolic_sampled_four_point_delta_summary_with_budget_and_cancellation(
            points,
            &config,
            ResourceBudget::default(),
            &cancellation,
        ),
        Err(PidError::Cancelled {
            operation: "sampled_four_point_delta_summary",
            completed_units: 0,
            total_units: 40,
        })
    ));
}
