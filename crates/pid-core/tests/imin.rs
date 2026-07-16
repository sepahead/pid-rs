use pid_core::stable::imin::{
    imin_pid2, imin_pid2_quantized, imin_pid2_quantized_resource_estimate,
    imin_pid2_quantized_with_budget, imin_pid2_resource_estimate, imin_pid3, imin_pid3_quantized,
    imin_pid3_quantized_resource_estimate, imin_pid3_quantized_with_budget,
    imin_pid3_resource_estimate, IminInputEncoding, IminPid3Result,
};
use pid_core::stable::quantized::{EqualWidthQuantizer, QuantizerConfig};
use pid_core::{DiscreteMatRef, MatRef, PidError, ResourceBudget};

fn assert_close(left: f64, right: f64, context: &str) {
    assert!(
        (left - right).abs() < 1.0e-12,
        "{context}: left={left:.17e}, right={right:.17e}"
    );
}

fn antichain_leq(lower: &[u8], upper: &[u8]) -> bool {
    upper
        .iter()
        .all(|upper_mask| lower.iter().any(|lower_mask| lower_mask & !upper_mask == 0))
}

fn assert_pid3_numerics_equal(left: &IminPid3Result, right: &IminPid3Result) {
    for (context, left_value, right_value) in [
        ("I(S0;T)", left.mi_s0_t, right.mi_s0_t),
        ("I(S1;T)", left.mi_s1_t, right.mi_s1_t),
        ("I(S2;T)", left.mi_s2_t, right.mi_s2_t),
        ("I(S0,S1;T)", left.mi_s0s1_t, right.mi_s0s1_t),
        ("I(S0,S2;T)", left.mi_s0s2_t, right.mi_s0s2_t),
        ("I(S1,S2;T)", left.mi_s1s2_t, right.mi_s1s2_t),
        ("I(S0,S1,S2;T)", left.mi_s0s1s2_t, right.mi_s0s1s2_t),
    ] {
        assert_close(left_value, right_value, context);
    }

    assert_eq!(left.redundancies.len(), right.redundancies.len());
    for (index, (&left_value, &right_value)) in left
        .redundancies
        .iter()
        .zip(&right.redundancies)
        .enumerate()
    {
        assert_close(
            left_value,
            right_value,
            &format!("redundancy at lattice index {index}"),
        );
    }

    assert_eq!(left.atoms.len(), right.atoms.len());
    for (left_atom, right_atom) in left.atoms.iter().zip(&right.atoms) {
        assert_eq!(left_atom.antichain_sets, right_atom.antichain_sets);
        assert_close(
            left_atom.value,
            right_atom.value,
            &format!("atom {:?}", left_atom.antichain_sets),
        );
    }
}

#[test]
fn categorical_imin_pid3_reconstructs_each_lattice_node_and_joint_information() {
    let mut s0 = Vec::new();
    let mut s1 = Vec::new();
    let mut s2 = Vec::new();
    let mut target = Vec::new();
    for _ in 0..3 {
        for a in 0..2 {
            for b in 0..2 {
                for c in 0..2 {
                    s0.push(a);
                    s1.push(b);
                    s2.push(c);
                    target.push(a | (b & c));
                }
            }
        }
    }
    let n = s0.len();
    let result = imin_pid3(
        DiscreteMatRef::new(&s0, n, 1).unwrap(),
        DiscreteMatRef::new(&s1, n, 1).unwrap(),
        DiscreteMatRef::new(&s2, n, 1).unwrap(),
        DiscreteMatRef::new(&target, n, 1).unwrap(),
    )
    .unwrap();

    assert_eq!(result.atoms.len(), 18);
    assert_eq!(result.redundancies.len(), 18);
    for (node_index, node) in result.atoms.iter().enumerate() {
        let reconstructed: f64 = result
            .atoms
            .iter()
            .filter(|candidate| antichain_leq(&candidate.antichain_sets, &node.antichain_sets))
            .map(|candidate| candidate.value)
            .sum();
        assert_close(
            reconstructed,
            result.redundancies[node_index],
            &format!("down-set reconstruction for {:?}", node.antichain_sets),
        );
    }

    let redundancy_at = |mask: u8| {
        let index = result
            .atoms
            .iter()
            .position(|atom| atom.antichain_sets == [mask])
            .unwrap();
        result.redundancies[index]
    };
    for (mask, expected) in [
        (0b001, result.mi_s0_t),
        (0b010, result.mi_s1_t),
        (0b100, result.mi_s2_t),
        (0b011, result.mi_s0s1_t),
        (0b101, result.mi_s0s2_t),
        (0b110, result.mi_s1s2_t),
        (0b111, result.mi_s0s1s2_t),
    ] {
        assert_close(
            redundancy_at(mask),
            expected,
            &format!("self-redundancy for subset {mask:#05b}"),
        );
    }

    let atom_sum: f64 = result.atoms.iter().map(|atom| atom.value).sum();
    assert_close(atom_sum, result.mi_s0s1s2_t, "full PID reconstruction");
}

#[test]
fn categorical_imin_pid3_is_equivariant_under_source_swap() {
    let s0 = [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 1, 0];
    let s1 = [0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 2, 1];
    let s2 = [0, 1, 0, 1, 0, 1, 2, 2, 2, 1, 0, 2];
    let target = [0, 1, 1, 2, 0, 2, 1, 2, 0, 2, 1, 0];
    let n = target.len();
    let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let target = DiscreteMatRef::new(&target, n, 1).unwrap();

    let original = imin_pid3(s0, s1, s2, target).unwrap();
    let swapped = imin_pid3(s1, s0, s2, target).unwrap();

    for (context, left, right) in [
        ("S0 to swapped S1", original.mi_s0_t, swapped.mi_s1_t),
        ("S1 to swapped S0", original.mi_s1_t, swapped.mi_s0_t),
        ("S2 fixed", original.mi_s2_t, swapped.mi_s2_t),
        ("S0S1 unordered pair", original.mi_s0s1_t, swapped.mi_s0s1_t),
        (
            "S0S2 to swapped S1S2",
            original.mi_s0s2_t,
            swapped.mi_s1s2_t,
        ),
        (
            "S1S2 to swapped S0S2",
            original.mi_s1s2_t,
            swapped.mi_s0s2_t,
        ),
        (
            "joint source tuple",
            original.mi_s0s1s2_t,
            swapped.mi_s0s1s2_t,
        ),
    ] {
        assert_close(left, right, context);
    }

    let swap_01_mask = |mask: u8| {
        let bit0 = mask & 0b001;
        let bit1 = mask & 0b010;
        (mask & 0b100) | (bit0 << 1) | (bit1 >> 1)
    };
    for (original_index, original_atom) in original.atoms.iter().enumerate() {
        let mut swapped_key: Vec<u8> = original_atom
            .antichain_sets
            .iter()
            .map(|&mask| swap_01_mask(mask))
            .collect();
        swapped_key.sort_unstable();
        let swapped_index = swapped
            .atoms
            .iter()
            .position(|atom| atom.antichain_sets == swapped_key)
            .unwrap();
        assert_close(
            original_atom.value,
            swapped.atoms[swapped_index].value,
            &format!("permuted atom {:?}", original_atom.antichain_sets),
        );
        assert_close(
            original.redundancies[original_index],
            swapped.redundancies[swapped_index],
            &format!("permuted redundancy {:?}", original_atom.antichain_sets),
        );
    }
}

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

#[test]
fn fitted_quantized_imin_pid3_retains_four_reports_and_resource_preflight() {
    let training = [0.0, 1.0, 2.0, 3.0];
    let evaluation_s0 = [0.25, 0.75, 2.25, 2.75, 0.25, 0.75, 2.25, 2.75];
    let evaluation_s1 = [0.25, 2.25, 0.75, 2.75, 2.25, 0.25, 2.75, 0.75];
    let evaluation_s2 = [0.25, 2.25, 2.25, 0.25, 2.75, 0.75, 0.75, 2.75];
    let evaluation_target = [0.25, 2.25, 0.25, 2.25, 2.25, 0.25, 2.25, 0.25];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, 4, 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let s0 = quantizer
        .transform_with_report(MatRef::new(&evaluation_s0, 8, 1).unwrap())
        .unwrap();
    let s1 = quantizer
        .transform_with_report(MatRef::new(&evaluation_s1, 8, 1).unwrap())
        .unwrap();
    let s2 = quantizer
        .transform_with_report(MatRef::new(&evaluation_s2, 8, 1).unwrap())
        .unwrap();
    let target = quantizer
        .transform_with_report(MatRef::new(&evaluation_target, 8, 1).unwrap())
        .unwrap();

    let categorical_estimate = imin_pid3_resource_estimate(
        s0.matrix.as_ref(),
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
    )
    .unwrap();
    let estimate = imin_pid3_quantized_resource_estimate(&s0, &s1, &s2, &target).unwrap();
    assert!(estimate.estimated_bytes > categorical_estimate.estimated_bytes);
    let default_budget = ResourceBudget::default();
    let max_bytes = u64::try_from(estimate.estimated_bytes - 1).unwrap();
    let report_limited_budget = ResourceBudget::new(
        max_bytes,
        default_budget.max_pairwise_distances,
        default_budget.max_operations_hint,
        default_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        imin_pid3_quantized_with_budget(&s0, &s1, &s2, &target, report_limited_budget),
        Err(PidError::ResourceLimitExceeded {
            resource: "bytes",
            ..
        })
    ));

    let categorical = imin_pid3(
        s0.matrix.as_ref(),
        s1.matrix.as_ref(),
        s2.matrix.as_ref(),
        target.matrix.as_ref(),
    )
    .unwrap();
    let result = imin_pid3_quantized(&s0, &s1, &s2, &target).unwrap();
    assert_pid3_numerics_equal(&result, &categorical);
    assert_eq!(
        result.input.observed_cardinalities,
        categorical.input.observed_cardinalities
    );
    assert_eq!(result.empirical_pmf, categorical.empirical_pmf);

    let IminInputEncoding::FittedEqualWidth {
        quantization_reports,
    } = &result.input.encoding
    else {
        panic!("fitted quantized PID3 must retain fitted-transform provenance");
    };
    let expected_reports = [&s0.report, &s1.report, &s2.report, &target.report];
    assert_eq!(quantization_reports.len(), expected_reports.len());
    for (actual, expected) in quantization_reports.iter().zip(expected_reports) {
        assert_eq!(actual, expected);
        assert_eq!(actual.training_input_hash, expected.training_input_hash);
        assert_eq!(actual.transform_input_hash, expected.transform_input_hash);
        assert_eq!(
            actual.categorical_output_hash,
            expected.categorical_output_hash
        );
    }
}
