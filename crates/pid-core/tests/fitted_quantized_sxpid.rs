use pid_core::stable::categorical::{
    discrete_sxpid2_resource_estimate, discrete_sxpid3_averaged, discrete_sxpid3_resource_estimate,
    discrete_sxpid_n_averaged, discrete_sxpid_n_resource_estimate, DiscreteInputEncoding,
    DiscreteSxPid3Result, DiscreteSxPidNResult, SxAveragedAtom,
};
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2, fitted_quantized_sxpid2_resource_estimate,
    fitted_quantized_sxpid2_with_budget, fitted_quantized_sxpid3,
    fitted_quantized_sxpid3_resource_estimate, fitted_quantized_sxpid3_with_budget,
    fitted_quantized_sxpid_n, fitted_quantized_sxpid_n_resource_estimate,
    fitted_quantized_sxpid_n_with_budget, EqualWidthQuantizer, QuantizationReport, QuantizerConfig,
};
use pid_core::{MatRef, PidError, ResourceBudget};

fn quantization_report_copy_cost(report: &QuantizationReport) -> (u128, u128) {
    let edge_count = report.bin_edges.iter().map(Vec::len).sum::<usize>() as u128;
    let diagnostic_count = [
        report.distinct_binary64_edge_value_counts.len(),
        report.positive_width_interval_counts.len(),
        report.reachable_binary64_label_counts.len(),
        report.observed_label_counts.len(),
    ]
    .into_iter()
    .sum::<usize>() as u128;
    let string_bytes = report.scaling_description.len() as u128;
    let heap_bytes = report.bin_edges.len() as u128 * std::mem::size_of::<Vec<f64>>() as u128
        + edge_count * std::mem::size_of::<f64>() as u128
        + diagnostic_count * std::mem::size_of::<usize>() as u128
        + string_bytes;
    (heap_bytes, edge_count + diagnostic_count + string_bytes)
}

fn assert_close(left: f64, right: f64, context: &str) {
    assert!(
        (left - right).abs() < 1.0e-12,
        "{context}: left={left:.17e}, right={right:.17e}"
    );
}

fn assert_sx_atom_equal(left: SxAveragedAtom, right: SxAveragedAtom, context: &str) {
    assert_close(left.informative_nats(), right.informative_nats(), context);
    assert_close(
        left.misinformative_nats(),
        right.misinformative_nats(),
        context,
    );
    assert_close(left.net_nats(), right.net_nats(), context);
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
    assert!(quantized_estimate.operations_hint > categorical_estimate.operations_hint);
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
    let operation_limited_budget = ResourceBudget::new(
        default_budget.max_bytes,
        default_budget.max_pairwise_distances,
        quantized_estimate.operations_hint - 1,
        default_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid2_with_budget(&s1, &s2, &target, operation_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            resource: "operations_hint",
            requested,
            limit,
            ..
        }) if requested == quantized_estimate.operations_hint
            && limit == quantized_estimate.operations_hint - 1
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
fn fitted_quantized_sxpid_resource_estimates_track_mutated_report_payloads_exactly() {
    let training = [0.0, 1.0, 2.0, 3.0];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, 4, 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let mut s1 = quantizer
        .transform_with_report(MatRef::new(&training, 4, 1).unwrap())
        .unwrap();
    let mut s2 = quantizer
        .transform_with_report(MatRef::new(&training, 4, 1).unwrap())
        .unwrap();
    let mut target = quantizer
        .transform_with_report(MatRef::new(&training, 4, 1).unwrap())
        .unwrap();
    s1.report.bin_edges = vec![vec![-1.0, 0.0], vec![1.0; 3]];
    s1.report.distinct_binary64_edge_value_counts = vec![0; 2];
    s1.report.positive_width_interval_counts = vec![0; 3];
    s1.report.reachable_binary64_label_counts = vec![0; 5];
    s1.report.observed_label_counts = vec![0; 7];
    s1.report.scaling_description = "σ→τ".to_owned();
    s2.report.bin_edges = vec![vec![], vec![2.0; 4], vec![3.0]];
    s2.report.distinct_binary64_edge_value_counts = vec![0; 11];
    s2.report.positive_width_interval_counts = vec![0; 13];
    s2.report.reachable_binary64_label_counts = vec![0; 17];
    s2.report.observed_label_counts = vec![0; 19];
    s2.report.scaling_description = "µm²".to_owned();
    target.report.bin_edges = vec![vec![4.0; 2], vec![5.0; 5]];
    target.report.distinct_binary64_edge_value_counts = vec![0; 23];
    target.report.positive_width_interval_counts = vec![0; 29];
    target.report.reachable_binary64_label_counts = vec![0; 31];
    target.report.observed_label_counts = vec![0; 37];
    target.report.scaling_description = "Δt→∞".to_owned();
    let sources = [&s1, &s2];
    let categorical_sources = [s1.matrix.as_ref(), s2.matrix.as_ref()];
    let fixed_base = discrete_sxpid2_resource_estimate(
        categorical_sources[0],
        categorical_sources[1],
        target.matrix.as_ref(),
        false,
    )
    .unwrap();
    let n_base =
        discrete_sxpid_n_resource_estimate(&categorical_sources, target.matrix.as_ref(), false)
            .unwrap();
    let report_costs = [&s1.report, &s2.report, &target.report].map(quantization_report_copy_cost);
    let report_heap_bytes = report_costs.iter().map(|cost| cost.0).sum::<u128>();
    let report_copy_operations = report_costs.iter().map(|cost| cost.1).sum::<u128>();
    let fixed_expected_bytes = fixed_base.estimated_bytes + report_heap_bytes;
    let fixed_expected_operations = fixed_base.operations_hint + report_copy_operations;
    let n_expected_bytes = n_base.estimated_bytes
        + report_heap_bytes
        + sources.len() as u128 * std::mem::size_of::<QuantizationReport>() as u128;
    let n_expected_operations = n_base.operations_hint + report_copy_operations;
    let fixed_estimate = fitted_quantized_sxpid2_resource_estimate(&s1, &s2, &target).unwrap();
    let n_estimate = fitted_quantized_sxpid_n_resource_estimate(&sources, &target).unwrap();

    assert_eq!(
        [
            (
                fixed_estimate.estimated_bytes,
                fixed_estimate.operations_hint,
                fixed_estimate.pairwise_distances,
            ),
            (
                n_estimate.estimated_bytes,
                n_estimate.operations_hint,
                n_estimate.pairwise_distances,
            ),
        ],
        [
            (
                fixed_expected_bytes,
                fixed_expected_operations,
                fixed_base.pairwise_distances,
            ),
            (
                n_expected_bytes,
                n_expected_operations,
                n_base.pairwise_distances,
            ),
        ]
    );

    let defaults = ResourceBudget::default();
    let fixed_exact_budget = ResourceBudget::new(
        u64::try_from(fixed_expected_bytes).unwrap(),
        defaults.max_pairwise_distances,
        fixed_expected_operations,
        defaults.max_threads,
    )
    .unwrap();
    assert!(fitted_quantized_sxpid2_with_budget(&s1, &s2, &target, fixed_exact_budget).is_ok());
    let fixed_byte_limited_budget = ResourceBudget::new(
        u64::try_from(fixed_expected_bytes - 1).unwrap(),
        defaults.max_pairwise_distances,
        fixed_expected_operations,
        defaults.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid2_with_budget(&s1, &s2, &target, fixed_byte_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            operation: "fitted_quantized_sxpid2",
            resource: "bytes",
            requested,
            limit,
            ..
        }) if requested == fixed_expected_bytes && limit == fixed_expected_bytes - 1
    ));
    let fixed_operation_limited_budget = ResourceBudget::new(
        u64::try_from(fixed_expected_bytes).unwrap(),
        defaults.max_pairwise_distances,
        fixed_expected_operations - 1,
        defaults.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid2_with_budget(
            &s1,
            &s2,
            &target,
            fixed_operation_limited_budget
        ),
        Err(PidError::ResourceLimitExceeded {
            operation: "fitted_quantized_sxpid2",
            resource: "operations_hint",
            requested,
            limit,
            ..
        }) if requested == fixed_expected_operations
            && limit == fixed_expected_operations - 1
    ));

    let n_exact_budget = ResourceBudget::new(
        u64::try_from(n_expected_bytes).unwrap(),
        defaults.max_pairwise_distances,
        n_expected_operations,
        defaults.max_threads,
    )
    .unwrap();
    assert!(fitted_quantized_sxpid_n_with_budget(&sources, &target, n_exact_budget).is_ok());
    let n_byte_limited_budget = ResourceBudget::new(
        u64::try_from(n_expected_bytes - 1).unwrap(),
        defaults.max_pairwise_distances,
        n_expected_operations,
        defaults.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid_n_with_budget(&sources, &target, n_byte_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            operation: "fitted_quantized_sxpid_n",
            resource: "bytes",
            requested,
            limit,
            ..
        }) if requested == n_expected_bytes && limit == n_expected_bytes - 1
    ));
    let n_operation_limited_budget = ResourceBudget::new(
        u64::try_from(n_expected_bytes).unwrap(),
        defaults.max_pairwise_distances,
        n_expected_operations - 1,
        defaults.max_threads,
    )
    .unwrap();
    assert!(matches!(
        fitted_quantized_sxpid_n_with_budget(
            &sources,
            &target,
            n_operation_limited_budget
        ),
        Err(PidError::ResourceLimitExceeded {
            operation: "fitted_quantized_sxpid_n",
            resource: "operations_hint",
            requested,
            limit,
            ..
        }) if requested == n_expected_operations && limit == n_expected_operations - 1
    ));
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
