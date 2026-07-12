use pid_core::stable::categorical::{
    discrete_sxpid2_averaged_with_budget, discrete_sxpid2_resource_estimate,
    discrete_sxpid2_with_budget,
};
use pid_core::stable::imin::{
    imin_pid2_resource_estimate, imin_pid2_with_budget, imin_pid3_resource_estimate,
    imin_pid3_with_budget,
};
use pid_core::{DiscreteMatRef, PidError, ResourceBudget};

fn binary_columns() -> (
    DiscreteMatRef<'static>,
    DiscreteMatRef<'static>,
    DiscreteMatRef<'static>,
    DiscreteMatRef<'static>,
) {
    static S0: [usize; 8] = [0, 0, 0, 0, 1, 1, 1, 1];
    static S1: [usize; 8] = [0, 0, 1, 1, 0, 0, 1, 1];
    static S2: [usize; 8] = [0, 1, 0, 1, 0, 1, 0, 1];
    static TARGET: [usize; 8] = [0, 1, 1, 0, 1, 0, 0, 1];
    (
        DiscreteMatRef::new(&S0, 8, 1).unwrap(),
        DiscreteMatRef::new(&S1, 8, 1).unwrap(),
        DiscreteMatRef::new(&S2, 8, 1).unwrap(),
        DiscreteMatRef::new(&TARGET, 8, 1).unwrap(),
    )
}

fn one_byte_budget() -> ResourceBudget {
    let default = ResourceBudget::default();
    ResourceBudget::new(
        1,
        default.max_pairwise_distances,
        default.max_operations_hint,
        default.max_threads,
    )
    .unwrap()
}

#[test]
fn sxpid_preflight_accounts_for_retained_pointwise_output() {
    let (s0, s1, _, target) = binary_columns();
    let averaged = discrete_sxpid2_resource_estimate(s0, s1, target, false).unwrap();
    let pointwise = discrete_sxpid2_resource_estimate(s0, s1, target, true).unwrap();

    assert!(pointwise.estimated_bytes > averaged.estimated_bytes);
}

#[test]
fn sxpid_tiny_budget_fails_before_pointwise_or_averaged_allocation() {
    let (s0, s1, _, target) = binary_columns();

    for result in [
        discrete_sxpid2_with_budget(s0, s1, target, one_byte_budget()),
        discrete_sxpid2_averaged_with_budget(s0, s1, target, one_byte_budget()),
    ] {
        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded {
                resource: "bytes",
                ..
            })
        ));
    }
}

#[test]
fn imin_preflight_includes_repeated_histograms_and_rejects_tiny_budget() {
    let (s0, s1, s2, target) = binary_columns();
    let two_source = imin_pid2_resource_estimate(s0, s1, target).unwrap();
    let three_source = imin_pid3_resource_estimate(s0, s1, s2, target).unwrap();
    let raw_payload_bytes = 8_u128 * 4 * std::mem::size_of::<usize>() as u128;

    assert!(two_source.estimated_bytes > raw_payload_bytes);
    assert!(three_source.estimated_bytes > two_source.estimated_bytes);
    assert_eq!(two_source.operations_hint, 1_456);
    assert_eq!(three_source.operations_hint, 16_152);
    assert!(matches!(
        imin_pid2_with_budget(s0, s1, target, one_byte_budget()),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));
    assert!(matches!(
        imin_pid3_with_budget(s0, s1, s2, target, one_byte_budget()),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));
}
