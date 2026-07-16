use pid_core::stable::categorical::{
    discrete_sxpid2_resource_estimate, discrete_sxpid3_averaged, discrete_sxpid3_resource_estimate,
    discrete_sxpid_n_averaged, discrete_sxpid_n_resource_estimate, DiscreteInputEncoding,
    DiscreteSxPid3Result, DiscreteSxPidNResult, SxAtom,
};
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2, fitted_quantized_sxpid2_resource_estimate,
    fitted_quantized_sxpid2_with_budget, fitted_quantized_sxpid3,
    fitted_quantized_sxpid3_resource_estimate, fitted_quantized_sxpid3_with_budget,
    fitted_quantized_sxpid_n, fitted_quantized_sxpid_n_resource_estimate,
    fitted_quantized_sxpid_n_with_budget, EqualWidthQuantizer, QuantizerConfig,
};
use pid_core::{MatRef, PidError, ResourceBudget};

fn assert_close(left: f64, right: f64, context: &str) {
    assert!(
        (left - right).abs() < 1.0e-12,
        "{context}: left={left:.17e}, right={right:.17e}"
    );
}

fn assert_sx_atom_equal(left: SxAtom, right: SxAtom, context: &str) {
    assert_close(left.informative, right.informative, context);
    assert_close(left.misinformative, right.misinformative, context);
    assert_close(left.net, right.net, context);
}

fn assert_sxpid3_numerics_equal(left: &DiscreteSxPid3Result, right: &DiscreteSxPid3Result) {
    assert_eq!(left.antichains, right.antichains);
    assert_eq!(left.atoms.len(), right.atoms.len());
    for ((antichain, &left_atom), &right_atom) in
        left.antichains.iter().zip(&left.atoms).zip(&right.atoms)
    {
        assert_sx_atom_equal(left_atom, right_atom, &format!("PID3 atom {antichain:?}"));
    }
    for (context, left_value, right_value) in [
        ("I(S0;T)", left.mi_s0_t, right.mi_s0_t),
        ("I(S1;T)", left.mi_s1_t, right.mi_s1_t),
        ("I(S2;T)", left.mi_s2_t, right.mi_s2_t),
        ("I(S0,S1,S2;T)", left.mi_s0s1s2_t, right.mi_s0s1s2_t),
    ] {
        assert_close(left_value, right_value, context);
    }
    assert_eq!(left.subset_mis.len(), right.subset_mis.len());
    for (mask_index, (&left_value, &right_value)) in
        left.subset_mis.iter().zip(&right.subset_mis).enumerate()
    {
        assert_close(
            left_value,
            right_value,
            &format!("PID3 subset MI mask {:#05b}", mask_index + 1),
        );
    }
    assert!(!left.pointwise_included);
    assert!(!right.pointwise_included);
    assert!(left.pointwise.is_empty());
    assert!(right.pointwise.is_empty());
}

fn assert_sxpid_n_numerics_equal(left: &DiscreteSxPidNResult, right: &DiscreteSxPidNResult) {
    assert_eq!(left.n_sources, right.n_sources);
    assert_eq!(left.antichains, right.antichains);
    assert_eq!(left.atoms.len(), right.atoms.len());
    for ((antichain, &left_atom), &right_atom) in
        left.antichains.iter().zip(&left.atoms).zip(&right.atoms)
    {
        assert_sx_atom_equal(left_atom, right_atom, &format!("PID-N atom {antichain:?}"));
    }
    assert_close(left.joint_mi, right.joint_mi, "PID-N joint MI");
    assert_eq!(left.subset_mis.len(), right.subset_mis.len());
    for (mask_index, (&left_value, &right_value)) in
        left.subset_mis.iter().zip(&right.subset_mis).enumerate()
    {
        assert_close(
            left_value,
            right_value,
            &format!("PID-N subset MI mask {:#06b}", mask_index + 1),
        );
    }
    assert!(!left.pointwise_included);
    assert!(!right.pointwise_included);
    assert!(left.pointwise.is_empty());
    assert!(right.pointwise.is_empty());
}

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
    assert_eq!(
        result.source_quantization[0].training_input_hash,
        s1.report.training_input_hash
    );
    assert_eq!(
        result.source_quantization[0].transform_input_hash,
        s1.report.transform_input_hash
    );
    assert_eq!(
        result.source_quantization[0].categorical_output_hash,
        s1.report.categorical_output_hash
    );
    assert_eq!(
        result.target_quantization.categorical_output_hash,
        target.report.categorical_output_hash
    );
    assert!(!result.pid.pointwise_included);
    assert_eq!(
        json["source_quantization"][0]["bin_edges"],
        serde_json::json!([[0.0, 1.5, 3.0]])
    );
    assert!(json["source_quantization"][0]["training_input_hash"]
        .as_array()
        .is_some());
    assert_eq!(json["target_quantization"]["observed_joint_cardinality"], 2);
    assert!(json["pid"]["mi_s1s2_t"].as_f64().unwrap().is_finite());
}

#[test]
fn fitted_quantized_sxpid3_matches_categorical_labels_and_retains_report_order() {
    let training = [0.0, 1.0, 2.0, 3.0];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, 4, 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let s0_values = [0.25, 0.75, 2.25, 2.75, 0.25, 0.75, 2.25, 2.75];
    let s1_values = [0.25, 2.25, 0.75, 2.75, 2.25, 0.25, 2.75, 0.75];
    let s2_values = [0.25, 2.25, 2.25, 0.25, 2.75, 0.75, 0.75, 2.75];
    let target_values = [0.25, 2.25, 0.25, 2.25, 2.25, 0.25, 2.25, 0.25];
    let s0 = quantizer
        .transform_with_report(MatRef::new(&s0_values, 8, 1).unwrap())
        .unwrap();
    let s1 = quantizer
        .transform_with_report(MatRef::new(&s1_values, 8, 1).unwrap())
        .unwrap();
    let s2 = quantizer
        .transform_with_report(MatRef::new(&s2_values, 8, 1).unwrap())
        .unwrap();
    let target = quantizer
        .transform_with_report(MatRef::new(&target_values, 8, 1).unwrap())
        .unwrap();

    let categorical_estimate = discrete_sxpid3_resource_estimate(
        s0.matrix.as_ref(),
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
        false,
    )
    .unwrap();
    let quantized_estimate =
        fitted_quantized_sxpid3_resource_estimate(&s0, &s1, &s2, &target).unwrap();
    assert!(quantized_estimate.estimated_bytes > categorical_estimate.estimated_bytes);
    let default_budget = ResourceBudget::default();
    let report_limited_budget = ResourceBudget::new(
        u64::try_from(quantized_estimate.estimated_bytes - 1).unwrap(),
        default_budget.max_pairwise_distances,
        default_budget.max_operations_hint,
        default_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid3_with_budget(&s0, &s1, &s2, &target, report_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));

    let categorical = discrete_sxpid3_averaged(
        s0.matrix.as_ref(),
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
    )
    .unwrap();
    let result = fitted_quantized_sxpid3(&s0, &s1, &s2, &target).unwrap();
    assert_sxpid3_numerics_equal(&result.pid, &categorical);
    assert_eq!(
        result.pid.input.encoding,
        DiscreteInputEncoding::FittedEqualWidth
    );
    assert_eq!(
        result.pid.input.observed_cardinalities,
        categorical.input.observed_cardinalities
    );
    assert_eq!(result.pid.empirical_pmf, categorical.empirical_pmf);

    let expected_reports = [&s0.report, &s1.report, &s2.report];
    for (actual, expected) in result.source_quantization.iter().zip(expected_reports) {
        assert_eq!(actual, expected);
        assert_eq!(actual.training_input_hash, expected.training_input_hash);
        assert_eq!(actual.transform_input_hash, expected.transform_input_hash);
        assert_eq!(
            actual.categorical_output_hash,
            expected.categorical_output_hash
        );
    }
    assert_eq!(&result.target_quantization, &target.report);
}

#[test]
fn fitted_quantized_sxpid_n_matches_four_source_categorical_lattice_and_budget() {
    let training = [0.0, 1.0, 2.0, 3.0];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, 4, 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let s0_values = [0.25, 0.75, 2.25, 2.75, 0.25, 0.75, 2.25, 2.75];
    let s1_values = [0.25, 2.25, 0.75, 2.75, 2.25, 0.25, 2.75, 0.75];
    let s2_values = [0.25, 2.25, 2.25, 0.25, 2.75, 0.75, 0.75, 2.75];
    let s3_values = [2.75, 0.25, 2.25, 0.75, 0.75, 2.75, 0.25, 2.25];
    let target_values = [0.25, 2.25, 0.25, 2.25, 2.25, 0.25, 2.25, 0.25];
    let s0 = quantizer
        .transform_with_report(MatRef::new(&s0_values, 8, 1).unwrap())
        .unwrap();
    let s1 = quantizer
        .transform_with_report(MatRef::new(&s1_values, 8, 1).unwrap())
        .unwrap();
    let s2 = quantizer
        .transform_with_report(MatRef::new(&s2_values, 8, 1).unwrap())
        .unwrap();
    let s3 = quantizer
        .transform_with_report(MatRef::new(&s3_values, 8, 1).unwrap())
        .unwrap();
    let target = quantizer
        .transform_with_report(MatRef::new(&target_values, 8, 1).unwrap())
        .unwrap();
    let quantized_sources = [&s0, &s1, &s2, &s3];
    let categorical_sources = [
        s0.matrix.as_ref(),
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        s3.matrix.as_ref(),
    ];

    let categorical_estimate =
        discrete_sxpid_n_resource_estimate(&categorical_sources, target.matrix.as_ref(), false)
            .unwrap();
    let quantized_estimate =
        fitted_quantized_sxpid_n_resource_estimate(&quantized_sources, &target).unwrap();
    assert!(quantized_estimate.estimated_bytes > categorical_estimate.estimated_bytes);
    let default_budget = ResourceBudget::default();
    let report_limited_budget = ResourceBudget::new(
        u64::try_from(quantized_estimate.estimated_bytes - 1).unwrap(),
        default_budget.max_pairwise_distances,
        default_budget.max_operations_hint,
        default_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid_n_with_budget(&quantized_sources, &target, report_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));

    let categorical =
        discrete_sxpid_n_averaged(&categorical_sources, target.matrix.as_ref()).unwrap();
    let result = fitted_quantized_sxpid_n(&quantized_sources, &target).unwrap();
    assert_sxpid_n_numerics_equal(&result.pid, &categorical);
    assert_eq!(result.pid.n_sources, 4);
    assert_eq!(result.pid.antichains.len(), 166);
    assert_eq!(
        result.pid.input.encoding,
        DiscreteInputEncoding::FittedEqualWidth
    );
    assert_eq!(
        result.pid.input.observed_cardinalities,
        categorical.input.observed_cardinalities
    );
    assert_eq!(result.pid.empirical_pmf, categorical.empirical_pmf);

    let expected_reports = [&s0.report, &s1.report, &s2.report, &s3.report];
    assert_eq!(result.source_quantization.len(), expected_reports.len());
    for (actual, expected) in result.source_quantization.iter().zip(expected_reports) {
        assert_eq!(actual, expected);
        assert_eq!(actual.training_input_hash, expected.training_input_hash);
        assert_eq!(actual.transform_input_hash, expected.transform_input_hash);
        assert_eq!(
            actual.categorical_output_hash,
            expected.categorical_output_hash
        );
    }
    assert_eq!(&result.target_quantization, &target.report);
}
