//! Executable evidence for the project-defined categorical SxPID interpretation contract.

use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n, DiscreteSxPid2Result, SxAtomAggregation,
    SxAtomContextRequirement, SxAtomCoordinateSemantics, SxAtomDecompositionMeasure,
    SxAtomEvidentialScope, SxAtomInterpretation, SxAveragedAtom, SxInterpretationGuardOrigin,
    SxPointwise2, SxPointwiseAtom, SxUnsupportedInference,
};
use pid_core::DiscreteMatRef;
use serde_json::json;

const GUARDS: [SxUnsupportedInference; 6] = [
    SxUnsupportedInference::IntentionalDeception,
    SxUnsupportedInference::CausalEffect,
    SxUnsupportedInference::FaultAttribution,
    SxUnsupportedInference::PerSourceResponsibility,
    SxUnsupportedInference::MeasureIndependentDecomposition,
    SxUnsupportedInference::UnbiasedPopulationEstimate,
];

fn run2(rows: &[(usize, usize, usize)]) -> DiscreteSxPid2Result {
    let mut s1 = Vec::with_capacity(rows.len());
    let mut s2 = Vec::with_capacity(rows.len());
    let mut target = Vec::with_capacity(rows.len());
    for &(a, b, t) in rows {
        s1.push(a);
        s2.push(b);
        target.push(t);
    }
    discrete_sxpid2(
        DiscreteMatRef::new(&s1, rows.len(), 1).unwrap(),
        DiscreteMatRef::new(&s2, rows.len(), 1).unwrap(),
        DiscreteMatRef::new(&target, rows.len(), 1).unwrap(),
    )
    .unwrap()
}

fn assert_interpretation(
    interpretation: SxAtomInterpretation,
    expected_aggregation: SxAtomAggregation,
) {
    assert_eq!(interpretation.contract_revision(), 1);
    assert_eq!(interpretation.aggregation_scope(), expected_aggregation);
    assert_eq!(
        interpretation.context_requirement(),
        SxAtomContextRequirement::ContainingResultForCoordinateAndRealizationContext
    );
    assert_eq!(
        interpretation.decomposition_measure(),
        SxAtomDecompositionMeasure::SharedExclusionsSxPid
    );
    assert_eq!(
        interpretation.coordinate_semantics(),
        SxAtomCoordinateSemantics::SourceCollectionAntichainMobiusContribution
    );
    assert_eq!(
        interpretation.evidential_scope(),
        SxAtomEvidentialScope::StatisticalInformationUnderSuppliedDistribution
    );
    assert_eq!(
        interpretation.guard_origin(),
        SxInterpretationGuardOrigin::ProjectDefined
    );
    assert_eq!(interpretation.not_established_by_atom_alone(), &GUARDS);
}

fn assert_pointwise_atom_contract(atom: SxPointwiseAtom) {
    assert!(atom.informative_nats().is_finite());
    assert!(atom.misinformative_nats().is_finite());
    assert!(atom.informative_nats() >= -2.0e-12);
    assert!(atom.misinformative_nats() >= -2.0e-12);
    assert_eq!(
        atom.net_nats(),
        atom.informative_nats() - atom.misinformative_nats()
    );
    assert_interpretation(
        atom.interpretation(),
        SxAtomAggregation::PointwiseDistinctJointRealization,
    );
}

fn assert_averaged_atom_contract(atom: SxAveragedAtom) {
    assert!(atom.informative_nats().is_finite());
    assert!(atom.misinformative_nats().is_finite());
    assert!(atom.informative_nats() >= -2.0e-12);
    assert!(atom.misinformative_nats() >= -2.0e-12);
    assert_eq!(
        atom.net_nats(),
        atom.informative_nats() - atom.misinformative_nats()
    );
    assert_interpretation(
        atom.interpretation(),
        SxAtomAggregation::EmpiricalPmfAverage,
    );
}

#[test]
fn enum_and_interpretation_wire_spellings_are_exact() {
    assert_eq!(
        SxAtomAggregation::PointwiseDistinctJointRealization.as_str(),
        "pointwise_distinct_joint_realization"
    );
    assert_eq!(
        SxAtomAggregation::EmpiricalPmfAverage.as_str(),
        "empirical_pmf_average"
    );
    assert_eq!(
        SxAtomContextRequirement::ContainingResultForCoordinateAndRealizationContext.as_str(),
        "containing_result_for_coordinate_and_realization_context"
    );
    assert_eq!(
        SxAtomCoordinateSemantics::SourceCollectionAntichainMobiusContribution.as_str(),
        "source_collection_antichain_mobius_contribution"
    );
    assert_eq!(
        SxAtomDecompositionMeasure::SharedExclusionsSxPid.as_str(),
        "shared_exclusions_sxpid"
    );
    assert_eq!(
        SxAtomEvidentialScope::StatisticalInformationUnderSuppliedDistribution.as_str(),
        "statistical_information_under_supplied_distribution"
    );
    assert_eq!(
        SxInterpretationGuardOrigin::ProjectDefined.as_str(),
        "project_defined"
    );
    assert_eq!(
        GUARDS.map(SxUnsupportedInference::as_str),
        [
            "intentional_deception",
            "causal_effect",
            "fault_attribution",
            "per_source_responsibility",
            "measure_independent_decomposition",
            "unbiased_population_estimate",
        ]
    );

    for (value, expected) in [
        (
            serde_json::to_value(SxAtomAggregation::PointwiseDistinctJointRealization).unwrap(),
            json!("pointwise_distinct_joint_realization"),
        ),
        (
            serde_json::to_value(SxAtomAggregation::EmpiricalPmfAverage).unwrap(),
            json!("empirical_pmf_average"),
        ),
        (
            serde_json::to_value(
                SxAtomContextRequirement::ContainingResultForCoordinateAndRealizationContext,
            )
            .unwrap(),
            json!("containing_result_for_coordinate_and_realization_context"),
        ),
        (
            serde_json::to_value(
                SxAtomCoordinateSemantics::SourceCollectionAntichainMobiusContribution,
            )
            .unwrap(),
            json!("source_collection_antichain_mobius_contribution"),
        ),
        (
            serde_json::to_value(SxAtomDecompositionMeasure::SharedExclusionsSxPid).unwrap(),
            json!("shared_exclusions_sxpid"),
        ),
        (
            serde_json::to_value(
                SxAtomEvidentialScope::StatisticalInformationUnderSuppliedDistribution,
            )
            .unwrap(),
            json!("statistical_information_under_supplied_distribution"),
        ),
        (
            serde_json::to_value(SxInterpretationGuardOrigin::ProjectDefined).unwrap(),
            json!("project_defined"),
        ),
    ] {
        assert_eq!(value, expected);
    }

    let xor = run2(&[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]);
    let pointwise = xor.pointwise[0].red;
    let expected_pointwise_interpretation = json!({
        "contract_revision": 1,
        "aggregation_scope": "pointwise_distinct_joint_realization",
        "context_requirement": "containing_result_for_coordinate_and_realization_context",
        "decomposition_measure": "shared_exclusions_sxpid",
        "coordinate_semantics": "source_collection_antichain_mobius_contribution",
        "evidential_scope": "statistical_information_under_supplied_distribution",
        "guard_origin": "project_defined",
        "not_established_by_atom_alone": [
            "intentional_deception",
            "causal_effect",
            "fault_attribution",
            "per_source_responsibility",
            "measure_independent_decomposition",
            "unbiased_population_estimate"
        ]
    });
    assert_eq!(
        serde_json::to_value(pointwise.interpretation()).unwrap(),
        expected_pointwise_interpretation
    );
    assert_eq!(
        serde_json::to_value(pointwise).unwrap(),
        json!({
            "informative_nats": pointwise.informative_nats(),
            "misinformative_nats": pointwise.misinformative_nats(),
            "net_nats": pointwise.net_nats(),
            "interpretation": expected_pointwise_interpretation
        })
    );

    let averaged = xor.red;
    let expected_averaged_interpretation = json!({
        "contract_revision": 1,
        "aggregation_scope": "empirical_pmf_average",
        "context_requirement": "containing_result_for_coordinate_and_realization_context",
        "decomposition_measure": "shared_exclusions_sxpid",
        "coordinate_semantics": "source_collection_antichain_mobius_contribution",
        "evidential_scope": "statistical_information_under_supplied_distribution",
        "guard_origin": "project_defined",
        "not_established_by_atom_alone": [
            "intentional_deception",
            "causal_effect",
            "fault_attribution",
            "per_source_responsibility",
            "measure_independent_decomposition",
            "unbiased_population_estimate"
        ]
    });
    assert_eq!(
        serde_json::to_value(averaged).unwrap(),
        json!({
            "informative_nats": averaged.informative_nats(),
            "misinformative_nats": averaged.misinformative_nats(),
            "net_nats": averaged.net_nats(),
            "interpretation": expected_averaged_interpretation
        })
    );
}

#[test]
fn empirical_pmf_results_are_bitwise_invariant_to_row_permutation() {
    let rows = [
        (1, 0, 1),
        (0, 0, 0),
        (1, 1, 0),
        (0, 1, 1),
        (1, 1, 0),
        (0, 0, 0),
        (1, 0, 1),
        (1, 1, 0),
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 1),
    ];
    let permuted = [
        rows[10], rows[4], rows[1], rows[8], rows[3], rows[0], rows[9], rows[6], rows[2], rows[7],
        rows[5],
    ];

    let original = serde_json::to_vec(&run2(&rows)).unwrap();
    let reordered = serde_json::to_vec(&run2(&permuted)).unwrap();
    assert_eq!(original, reordered);
}

fn assert_weighted_average(
    points: &[SxPointwise2],
    pointwise_atom: impl Fn(&SxPointwise2) -> SxPointwiseAtom,
    averaged: SxAveragedAtom,
) {
    let informative: f64 = points
        .iter()
        .map(|point| point.empirical_probability * pointwise_atom(point).informative_nats())
        .sum();
    let misinformative: f64 = points
        .iter()
        .map(|point| point.empirical_probability * pointwise_atom(point).misinformative_nats())
        .sum();
    assert!((informative - averaged.informative_nats()).abs() < 1.0e-14);
    assert!((misinformative - averaged.misinformative_nats()).abs() < 1.0e-14);
}

#[test]
fn two_source_records_are_distinct_states_with_auditable_pmf_weights() {
    let result = run2(&[
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0),
        (0, 1, 1),
        (1, 0, 1),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 0),
        (1, 1, 0),
        (1, 1, 0),
    ]);
    assert_eq!(result.empirical_pmf.sample_count, 10);
    assert_eq!(result.pointwise.len(), 4);
    assert_eq!(result.empirical_pmf.observed_joint_states, 4);
    assert_eq!(
        result
            .pointwise
            .iter()
            .map(|point| point.empirical_count)
            .sum::<usize>(),
        10
    );

    for point in &result.pointwise {
        assert_eq!(
            point.empirical_probability,
            point.empirical_count as f64 / result.empirical_pmf.sample_count as f64
        );
        for atom in [point.unq1, point.unq2, point.syn, point.red] {
            assert_pointwise_atom_contract(atom);
        }
    }
    let expected_counts = [
        ((0, 0, 0), 3),
        ((0, 1, 1), 1),
        ((1, 0, 1), 2),
        ((1, 1, 0), 4),
    ];
    for ((s1, s2, target), count) in expected_counts {
        let point = result
            .pointwise
            .iter()
            .find(|point| point.s1 == [s1] && point.s2 == [s2] && point.t == [target])
            .unwrap();
        assert_eq!(point.empirical_count, count);
    }

    for atom in [result.unq1, result.unq2, result.syn, result.red] {
        assert_averaged_atom_contract(atom);
    }
    assert_weighted_average(&result.pointwise, |point| point.unq1, result.unq1);
    assert_weighted_average(&result.pointwise, |point| point.unq2, result.unq2);
    assert_weighted_average(&result.pointwise, |point| point.syn, result.syn);
    assert_weighted_average(&result.pointwise, |point| point.red, result.red);

    let point_wire = serde_json::to_value(&result.pointwise[0]).unwrap();
    assert_eq!(point_wire["empirical_count"], 3);
    assert_eq!(point_wire["empirical_probability"], 0.3);
    assert!(point_wire.get("prob").is_none());
}

#[test]
fn interpretation_and_numeric_invariants_hold_for_three_and_general_source_paths() {
    let s0 = [0, 0, 0, 0, 1, 1, 1, 1];
    let s1 = [0, 0, 1, 1, 0, 0, 1, 1];
    let s2 = [0, 1, 0, 1, 0, 1, 0, 1];
    let target: Vec<usize> = (0..8).map(|i| s0[i] ^ s1[i] ^ s2[i]).collect();
    let s0m = DiscreteMatRef::new(&s0, 8, 1).unwrap();
    let s1m = DiscreteMatRef::new(&s1, 8, 1).unwrap();
    let s2m = DiscreteMatRef::new(&s2, 8, 1).unwrap();
    let tm = DiscreteMatRef::new(&target, 8, 1).unwrap();
    let three = discrete_sxpid3(s0m, s1m, s2m, tm).unwrap();
    assert_eq!(three.pointwise.len(), 8);
    for point in &three.pointwise {
        assert_eq!(point.empirical_count, 1);
        assert_eq!(point.empirical_probability, 0.125);
        for &atom in &point.atoms {
            assert_pointwise_atom_contract(atom);
        }
    }
    for &atom in &three.atoms {
        assert_averaged_atom_contract(atom);
    }

    let bit = [0, 0, 1, 1];
    let bit_matrix = DiscreteMatRef::new(&bit, 4, 1).unwrap();
    let general = discrete_sxpid_n(
        &[bit_matrix, bit_matrix, bit_matrix, bit_matrix],
        bit_matrix,
    )
    .unwrap();
    assert_eq!(general.pointwise.len(), 2);
    for point in &general.pointwise {
        assert_eq!(point.empirical_count, 2);
        assert_eq!(point.empirical_probability, 0.5);
        for &atom in &point.atoms {
            assert_pointwise_atom_contract(atom);
        }
    }
    for &atom in &general.atoms {
        assert_averaged_atom_contract(atom);
    }
}

#[test]
fn identical_tuple_atoms_remain_distribution_context_dependent() {
    let and = run2(&[(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]);
    let xor = run2(&[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]);
    let at_zero = |result: &DiscreteSxPid2Result| {
        result
            .pointwise
            .iter()
            .find(|point| point.s1 == [0] && point.s2 == [0] && point.t == [0])
            .unwrap()
            .red
    };
    let and_atom = at_zero(&and);
    let xor_atom = at_zero(&xor);

    assert!(and_atom.net_nats() > 0.0);
    assert!(xor_atom.net_nats() < 0.0);
    assert_eq!(and_atom.interpretation(), xor_atom.interpretation());
    assert_interpretation(
        and_atom.interpretation(),
        SxAtomAggregation::PointwiseDistinctJointRealization,
    );
}

#[test]
fn paper_defined_informative_component_depends_only_on_the_source_state() {
    // The paper-defined i+ cumulative quantities are source-only. Therefore their pointwise
    // Möbius components agree when the source state is fixed, even when the target label differs.
    // This assertion is deliberately limited to the informative components, not the full atom.
    let result = run2(&[
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 1),
    ]);
    let point = |target: usize| {
        result
            .pointwise
            .iter()
            .find(|point| point.s1 == [0] && point.s2 == [0] && point.t == [target])
            .unwrap()
    };
    let left = point(0);
    let right = point(1);
    for (left_atom, right_atom) in [
        (left.unq1, right.unq1),
        (left.unq2, right.unq2),
        (left.syn, right.syn),
        (left.red, right.red),
    ] {
        assert!((left_atom.informative_nats() - right_atom.informative_nats()).abs() < 1.0e-12);
    }
}
