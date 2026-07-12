use pid_core::stable::categorical::{discrete_sxpid2_resource_estimate, DiscreteInputEncoding};
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2, fitted_quantized_sxpid2_resource_estimate,
    fitted_quantized_sxpid2_with_budget, EqualWidthQuantizer, QuantizerConfig,
};
use pid_core::{MatRef, PidError, ResourceBudget};

#[test]
fn composed_quantized_sxpid_serializes_edges_hashes_and_occupancy_with_pid() {
    let training = [0.0, 1.0, 2.0, 3.0];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, 4, 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let s1_values = [0.25, 0.75, 2.25, 2.75];
    let s2_values = [2.75, 2.25, 0.75, 0.25];
    let target_values = [0.25, 2.25, 2.25, 0.25];
    let s1 = quantizer
        .transform_with_report(MatRef::new(&s1_values, 4, 1).unwrap())
        .unwrap();
    let s2 = quantizer
        .transform_with_report(MatRef::new(&s2_values, 4, 1).unwrap())
        .unwrap();
    let target = quantizer
        .transform_with_report(MatRef::new(&target_values, 4, 1).unwrap())
        .unwrap();

    let categorical_estimate = discrete_sxpid2_resource_estimate(
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
        false,
    )
    .unwrap();
    let quantized_estimate = fitted_quantized_sxpid2_resource_estimate(&s1, &s2, &target).unwrap();
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
        fitted_quantized_sxpid2_with_budget(&s1, &s2, &target, report_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));

    let result = fitted_quantized_sxpid2(&s1, &s2, &target).unwrap();
    let json = serde_json::to_value(&result).unwrap();

    assert_eq!(
        result.pid.input.encoding,
        DiscreteInputEncoding::FittedEqualWidth
    );
    assert!(!result.pid.pointwise_included);
    assert_eq!(
        json["source_quantization"][0]["bin_edges"],
        serde_json::json!([[0.0, 1.5, 3.0]])
    );
    assert!(json["source_quantization"][0]["training_data_hash"]
        .as_array()
        .is_some());
    assert_eq!(json["target_quantization"]["observed_joint_cardinality"], 2);
    assert!(json["pid"]["mi_s1s2_t"].as_f64().unwrap().is_finite());
}
