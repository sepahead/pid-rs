use pid_core::stable::imin::{
    imin_pid2, imin_pid2_quantized, imin_pid2_quantized_resource_estimate,
    imin_pid2_quantized_with_budget, imin_pid2_resource_estimate, IminInputEncoding,
};
use pid_core::stable::quantized::{EqualWidthQuantizer, QuantizerConfig};
use pid_core::{DiscreteMatRef, MatRef, PidError, ResourceBudget};

#[test]
fn categorical_imin_records_empirical_pmf_metadata() {
    let s1 = [0, 0, 1, 1, 0, 0, 1, 1];
    let s2 = [0, 1, 0, 1, 0, 1, 0, 1];
    let target = [0, 1, 1, 0, 0, 1, 1, 0];
    let result = imin_pid2(
        DiscreteMatRef::new(&s1, 8, 1).unwrap(),
        DiscreteMatRef::new(&s2, 8, 1).unwrap(),
        DiscreteMatRef::new(&target, 8, 1).unwrap(),
    )
    .unwrap();

    assert_eq!(result.input.encoding, IminInputEncoding::Categorical);
    assert_eq!(result.input.observed_cardinalities, vec![2, 2, 2]);
    assert_eq!(result.empirical_pmf.sample_count, 8);
    assert_eq!(result.empirical_pmf.observed_joint_states, 4);
    assert_eq!(result.empirical_pmf.minimum_observed_count, 2);
}

#[test]
fn fitted_quantized_imin_serializes_every_fixed_transform_report() {
    let training = [0.0, 1.0, 2.0, 3.0];
    let evaluation_s1 = [0.25, 0.75, 2.25, 2.75];
    let evaluation_s2 = [2.75, 2.25, 0.75, 0.25];
    let evaluation_target = [0.25, 2.25, 2.25, 0.25];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, 4, 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let s1 = quantizer
        .transform_with_report(MatRef::new(&evaluation_s1, 4, 1).unwrap())
        .unwrap();
    let s2 = quantizer
        .transform_with_report(MatRef::new(&evaluation_s2, 4, 1).unwrap())
        .unwrap();
    let target = quantizer
        .transform_with_report(MatRef::new(&evaluation_target, 4, 1).unwrap())
        .unwrap();

    let categorical_estimate = imin_pid2_resource_estimate(
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
    )
    .unwrap();
    let quantized_estimate = imin_pid2_quantized_resource_estimate(&s1, &s2, &target).unwrap();
    assert!(quantized_estimate.estimated_bytes > categorical_estimate.estimated_bytes);
    let default_budget = ResourceBudget::default();
    let max_bytes = u64::try_from(quantized_estimate.estimated_bytes - 1).unwrap();
    let report_limited_budget = ResourceBudget::new(
        max_bytes,
        default_budget.max_pairwise_distances,
        default_budget.max_operations_hint,
        default_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        imin_pid2_quantized_with_budget(&s1, &s2, &target, report_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));

    let result = imin_pid2_quantized(&s1, &s2, &target).unwrap();
    let json = serde_json::to_value(&result).unwrap();

    assert_eq!(
        json["input"]["encoding"]["FittedEqualWidth"]["quantization_reports"]
            .as_array()
            .unwrap()
            .len(),
        3
    );
    assert_eq!(
        json["input"]["encoding"]["FittedEqualWidth"]["quantization_reports"][0]["bin_edges"],
        serde_json::json!([[0.0, 1.5, 3.0]])
    );
    assert_eq!(json["empirical_pmf"]["sample_count"], 4);
}
