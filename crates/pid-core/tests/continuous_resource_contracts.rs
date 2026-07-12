#![cfg(feature = "experimental-continuous")]

use pid_core::experimental::continuous::raw_scalars::co_information_pairwise_with_budget;
#[cfg(feature = "experimental-heuristics")]
use pid_core::experimental::continuous::IsxConfig;
use pid_core::experimental::continuous::{
    incomplete_pid3_diagnostic_with_budget, incomplete_pid3_resource_estimate,
    pid2_isx_with_budget, Pid2Config, Pid3Config,
};
use pid_core::{MatRef, PidError, ResourceBudget};

fn tiny_budget() -> ResourceBudget {
    ResourceBudget::new(1, 1_000_000, 1_000_000_000, 1).unwrap()
}

fn inputs() -> ([f64; 8], [f64; 8], [f64; 8], [f64; 8]) {
    (
        [0.13, 0.91, 0.37, 0.62, 0.04, 0.78, 0.49, 0.25],
        [0.84, 0.17, 0.55, 0.03, 0.69, 0.31, 0.96, 0.42],
        [0.22, 0.73, 0.08, 0.95, 0.46, 0.11, 0.67, 0.34],
        [0.99, 1.06, 0.93, 0.61, 0.75, 1.08, 1.49, 0.64],
    )
}

#[test]
fn pid2_tiny_budget_rejects_before_estimation() {
    let (a, b, _, t) = inputs();
    let error = pid2_isx_with_budget(
        MatRef::new(&a, 8, 1).unwrap(),
        MatRef::new(&b, 8, 1).unwrap(),
        MatRef::new(&t, 8, 1).unwrap(),
        &Pid2Config::assume_regular_full_dimensional(),
        tiny_budget(),
    )
    .unwrap_err();

    assert!(matches!(
        error,
        PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        }
    ));
}

#[test]
fn incomplete_pid3_budget_aggregates_all_four_distance_matrices() {
    let (a, b, c, t) = inputs();
    let matrices = [
        MatRef::new(&a, 8, 1).unwrap(),
        MatRef::new(&b, 8, 1).unwrap(),
        MatRef::new(&c, 8, 1).unwrap(),
        MatRef::new(&t, 8, 1).unwrap(),
    ];
    let config = Pid3Config::assume_regular_full_dimensional();
    let estimate = incomplete_pid3_resource_estimate(
        matrices[0],
        matrices[1],
        matrices[2],
        matrices[3],
        &config,
    )
    .unwrap();
    let four_triangles = 4 * (8 * 7 / 2) * std::mem::size_of::<f64>();
    assert!(estimate.estimated_bytes >= four_triangles as u128);

    let error = incomplete_pid3_diagnostic_with_budget(
        matrices[0],
        matrices[1],
        matrices[2],
        matrices[3],
        &config,
        ResourceBudget::new((four_triangles - 1) as u64, 1_000_000, 1_000_000_000, 1).unwrap(),
    )
    .unwrap_err();
    assert!(matches!(
        error,
        PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        }
    ));
}

#[test]
fn pairwise_co_information_checks_aggregate_work_budget() {
    let (a, b, _, t) = inputs();
    let error = co_information_pairwise_with_budget(
        MatRef::new(&a, 8, 1).unwrap(),
        MatRef::new(&b, 8, 1).unwrap(),
        MatRef::new(&t, 8, 1).unwrap(),
        &pid_core::stable::continuous::KsgConfig::assume_regular_full_dimensional(),
        ResourceBudget::new(u64::MAX, u64::MAX, 1, 1).unwrap(),
    )
    .unwrap_err();

    assert!(matches!(
        error,
        PidError::ResourceLimitExceeded {
            resource: "operations_hint",
            ..
        }
    ));
}

#[test]
fn giant_zero_column_pid3_shape_has_structured_preflight_failure() {
    let giant = MatRef::new(&[], 1_600_000_000, 0).unwrap();
    let estimate =
        incomplete_pid3_resource_estimate(giant, giant, giant, giant, &Pid3Config::default())
            .unwrap();

    assert!(matches!(
        ResourceBudget::default().check("giant PID3 fixture", estimate),
        Err(PidError::ResourceLimitExceeded { .. })
    ));
}

#[cfg(feature = "experimental-hierarchy")]
#[test]
fn hierarchy_rejects_pair_enumeration_under_tiny_budget() {
    use pid_core::experimental::hierarchy::{
        hierarchical_pairwise_with_budget, HierarchicalConfig,
    };

    let (a, b, c, t) = inputs();
    let sources = [
        MatRef::new(&a, 8, 1).unwrap(),
        MatRef::new(&b, 8, 1).unwrap(),
        MatRef::new(&c, 8, 1).unwrap(),
    ];
    let error = hierarchical_pairwise_with_budget(
        &sources,
        MatRef::new(&t, 8, 1).unwrap(),
        &HierarchicalConfig::assume_regular_full_dimensional(),
        tiny_budget(),
    )
    .unwrap_err();

    assert!(matches!(error, PidError::ResourceLimitExceeded { .. }));
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn heuristic_isx_inherits_default_resource_preflight() {
    let (a, b, _, t) = inputs();
    let mut config = Pid2Config::assume_regular_full_dimensional();
    config.isx = IsxConfig {
        method: pid_core::experimental::continuous::IsxMethod::LocalMinKsg,
        ..IsxConfig::assume_regular_full_dimensional()
    };

    let error = pid2_isx_with_budget(
        MatRef::new(&a, 8, 1).unwrap(),
        MatRef::new(&b, 8, 1).unwrap(),
        MatRef::new(&t, 8, 1).unwrap(),
        &config,
        tiny_budget(),
    )
    .unwrap_err();
    assert!(matches!(error, PidError::ResourceLimitExceeded { .. }));
}
