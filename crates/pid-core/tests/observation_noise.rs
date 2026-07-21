#![cfg(feature = "experimental-pipelines")]

use pid_core::experimental::pipelines::{
    observation_noise_matrix_identity, GaussianNoiseApplicationContext, GaussianNoiseDeclaration,
    GaussianNoiseInputBinding, GaussianNoisePurpose, GaussianNoiseScaleReference,
    GaussianNoiseScientificClaimBoundary, GaussianNoiseSecurityScope,
    GaussianNoiseSensitivityCoupling, GaussianNoiseSpecification, GaussianNoiseStream,
    GaussianNoiseStreamSelection, GaussianNoiseTransform,
};
use pid_core::{CancellationToken, MatRef, PidError, ResourceBudget};

fn common_units() -> GaussianNoiseScaleReference {
    GaussianNoiseScaleReference::DeclaredCommonInputUnits {
        unit_identity_sha256: [0x11; 32],
    }
}

fn specification(std: f64) -> GaussianNoiseSpecification {
    GaussianNoiseSpecification::new(std, common_units()).unwrap()
}

fn declaration(
    std: f64,
    purpose: GaussianNoisePurpose,
    rationale: &str,
) -> GaussianNoiseDeclaration {
    GaussianNoiseDeclaration::new(
        specification(std),
        purpose,
        GaussianNoiseInputBinding::ApplicationInputOnly,
        rationale,
    )
    .unwrap()
}

fn stream(seed: u64, logical_identity: u8, domain_identity: u8) -> GaussianNoiseStream {
    GaussianNoiseStream::new(
        seed,
        GaussianNoiseStreamSelection::FixedBeforeEvaluationDataInspection,
        [logical_identity; 32],
        [domain_identity; 32],
    )
}

fn input() -> (Vec<f64>, usize, usize) {
    (vec![0.0, 1.0, 2.0, 3.0, -1.0, -2.0, -3.0, -4.0], 4, 2)
}

#[test]
fn specification_rejects_degenerate_or_nonfinite_scale() {
    for invalid in [0.0, -0.0, -1.0, f64::NAN, f64::INFINITY] {
        assert!(GaussianNoiseSpecification::new(invalid, common_units()).is_err());
    }
}

#[test]
fn model_declaration_and_application_identities_separate_domains() {
    let purpose = GaussianNoisePurpose::DeclaredObservationModel;
    let first = declaration(0.1, purpose, "declared sensor model");
    let second = declaration(0.1, purpose, "same kernel with a revised rationale");
    assert_eq!(
        first.specification().model_identity_sha256(),
        second.specification().model_identity_sha256()
    );
    assert_ne!(
        first.declaration_identity_sha256(),
        second.declaration_identity_sha256()
    );

    let (values, rows, columns) = input();
    let matrix = MatRef::new(&values, rows, columns).unwrap();
    let first_result = GaussianNoiseTransform::new(first, stream(7, 1, 2))
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();
    let second_result = GaussianNoiseTransform::new(second, stream(8, 1, 2))
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();

    assert_eq!(
        first_result
            .report()
            .declaration()
            .specification()
            .model_identity_sha256(),
        second_result
            .report()
            .declaration()
            .specification()
            .model_identity_sha256()
    );
    assert_ne!(
        first_result.report().application_identity_sha256(),
        second_result.report().application_identity_sha256()
    );
}

#[test]
fn purpose_changes_declaration_not_population_kernel_identity() {
    let model = specification(0.01);
    let declared = GaussianNoiseDeclaration::new(
        model,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ApplicationInputOnly,
        "declared measurement kernel",
    )
    .unwrap();
    let probe = GaussianNoiseDeclaration::new(
        model,
        GaussianNoisePurpose::SeededScaleSensitivityProbe {
            study_identity_sha256: [0x44; 32],
            coupling: GaussianNoiseSensitivityCoupling::CommonStandardNormalDrawsAcrossScales,
        },
        GaussianNoiseInputBinding::ApplicationInputOnly,
        "one member of a named scale study",
    )
    .unwrap();

    assert_eq!(
        declared.specification().model_identity_sha256(),
        probe.specification().model_identity_sha256()
    );
    assert_ne!(
        declared.declaration_identity_sha256(),
        probe.declaration_identity_sha256()
    );
}

#[test]
fn preprocessing_scale_reference_must_bind_the_exact_input_matrix() {
    let (values, rows, columns) = input();
    let matrix = MatRef::new(&values, rows, columns).unwrap();
    let matrix_identity = observation_noise_matrix_identity(matrix).unwrap();
    let scale_reference = GaussianNoiseScaleReference::DeclaredAfterFixedPreprocessing {
        preprocessing_identity_sha256: [0x22; 32],
        output_unit_identity_sha256: [0x33; 32],
    };
    let specification = GaussianNoiseSpecification::new(0.1, scale_reference).unwrap();
    let declaration = GaussianNoiseDeclaration::new(
        specification,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ExactFixedPreprocessingOutput {
            preprocessing_output_matrix_sha256: matrix_identity,
        },
        "fixed preprocessing output in common units",
    )
    .unwrap();
    assert!(GaussianNoiseTransform::new(declaration, stream(9, 1, 1))
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .is_ok());

    let bad_declaration = GaussianNoiseDeclaration::new(
        specification,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ExactFixedPreprocessingOutput {
            preprocessing_output_matrix_sha256: [0xFF; 32],
        },
        "mismatched preprocessing output",
    )
    .unwrap();
    assert!(matches!(
        GaussianNoiseTransform::new(bad_declaration, stream(9, 1, 1))
            .apply(matrix, GaussianNoiseApplicationContext::DirectInput),
        Err(PidError::InvalidConfig { .. })
    ));
}

#[test]
fn finite_input_binding_is_not_part_of_population_model_identity() {
    let scale_reference = GaussianNoiseScaleReference::DeclaredAfterFixedPreprocessing {
        preprocessing_identity_sha256: [0x22; 32],
        output_unit_identity_sha256: [0x33; 32],
    };
    let model = GaussianNoiseSpecification::new(0.1, scale_reference).unwrap();
    let first = GaussianNoiseDeclaration::new(
        model,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ExactFixedPreprocessingOutput {
            preprocessing_output_matrix_sha256: [0x44; 32],
        },
        "first fixed preprocessing output",
    )
    .unwrap();
    let second = GaussianNoiseDeclaration::new(
        model,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ExactFixedPreprocessingOutput {
            preprocessing_output_matrix_sha256: [0x55; 32],
        },
        "first fixed preprocessing output",
    )
    .unwrap();

    assert_eq!(
        first.specification().model_identity_sha256(),
        second.specification().model_identity_sha256()
    );
    assert_ne!(
        first.declaration_identity_sha256(),
        second.declaration_identity_sha256()
    );
}

#[test]
fn finite_input_values_do_not_enter_effective_seed_derivation() {
    let first_values = vec![0.0; 8];
    let second_values = vec![1.0; 8];
    let first_matrix = MatRef::new(&first_values, 4, 2).unwrap();
    let second_matrix = MatRef::new(&second_values, 4, 2).unwrap();
    let model = GaussianNoiseSpecification::new(
        0.1,
        GaussianNoiseScaleReference::DeclaredAfterFixedPreprocessing {
            preprocessing_identity_sha256: [0x22; 32],
            output_unit_identity_sha256: [0x33; 32],
        },
    )
    .unwrap();
    let make_declaration = |matrix: MatRef<'_>| {
        GaussianNoiseDeclaration::new(
            model,
            GaussianNoisePurpose::DeclaredObservationModel,
            GaussianNoiseInputBinding::ExactFixedPreprocessingOutput {
                preprocessing_output_matrix_sha256: observation_noise_matrix_identity(matrix)
                    .unwrap(),
            },
            "fixed preprocessing output",
        )
        .unwrap()
    };
    let noise_stream = stream(91, 4, 8);
    let first = GaussianNoiseTransform::new(make_declaration(first_matrix), noise_stream)
        .apply(first_matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();
    let second = GaussianNoiseTransform::new(make_declaration(second_matrix), noise_stream)
        .apply(second_matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();

    assert_eq!(
        first.report().effective_seed(),
        second.report().effective_seed()
    );
    assert_ne!(
        first.report().application_identity_sha256(),
        second.report().application_identity_sha256()
    );
}

#[test]
fn declaration_rejects_a_binding_for_the_wrong_scale_reference() {
    let common = specification(0.1);
    assert!(GaussianNoiseDeclaration::new(
        common,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ExactFixedPreprocessingOutput {
            preprocessing_output_matrix_sha256: [0x44; 32],
        },
        "invalid binding kind",
    )
    .is_err());

    let fixed = GaussianNoiseSpecification::new(
        0.1,
        GaussianNoiseScaleReference::DeclaredAfterFixedPreprocessing {
            preprocessing_identity_sha256: [0x22; 32],
            output_unit_identity_sha256: [0x33; 32],
        },
    )
    .unwrap();
    assert!(GaussianNoiseDeclaration::new(
        fixed,
        GaussianNoisePurpose::DeclaredObservationModel,
        GaussianNoiseInputBinding::ApplicationInputOnly,
        "missing fixed-output binding",
    )
    .is_err());
}

#[test]
fn generated_report_is_bound_to_input_output_and_context() {
    let (values, rows, columns) = input();
    let matrix = MatRef::new(&values, rows, columns).unwrap();
    let declaration = declaration(
        0.05,
        GaussianNoisePurpose::DeclaredObservationModel,
        "declared sensor model",
    );
    let result = GaussianNoiseTransform::new(declaration, stream(42, 5, 6))
        .apply(
            matrix,
            GaussianNoiseApplicationContext::AfterDeclaredRowResampling {
                declared_resample_indices_hash_sha256: [0x77; 32],
            },
        )
        .unwrap();
    let report = result.report();

    assert!(report.verifies_input_matrix(matrix).unwrap());
    assert!(report.verifies_output_matrix(result.matrix()).unwrap());
    assert!(!report.verifies_output_matrix(matrix).unwrap());
    assert_eq!(report.rows(), rows);
    assert_eq!(report.columns(), columns);
    assert_eq!(
        report.bitwise_changed_elements() + report.bitwise_unchanged_elements(),
        rows * columns
    );
    assert!(report.bitwise_changed_elements() > 0);
    assert!(report.changes_estimand());
    assert_eq!(
        report.scientific_claim_boundary(),
        GaussianNoiseScientificClaimBoundary::IdealPopulationLawOnlyV1
    );
    assert_eq!(
        report.security_scope(),
        GaussianNoiseSecurityScope::NonCryptographicNoConfidentialityOrAuthenticity
    );
}

#[test]
fn stream_identity_separates_logical_matrices_and_resample_contexts() {
    let values = vec![0.0; 32];
    let matrix = MatRef::new(&values, 16, 2).unwrap();
    let make = |logical_identity, context| {
        GaussianNoiseTransform::new(
            declaration(
                0.1,
                GaussianNoisePurpose::DeclaredObservationModel,
                "logical stream separation",
            ),
            stream(123, logical_identity, 9),
        )
        .apply(matrix, context)
        .unwrap()
    };
    let direct_a = make(1, GaussianNoiseApplicationContext::DirectInput);
    let direct_b = make(2, GaussianNoiseApplicationContext::DirectInput);
    let resampled_a = make(
        1,
        GaussianNoiseApplicationContext::AfterDeclaredRowResampling {
            declared_resample_indices_hash_sha256: [0xAA; 32],
        },
    );

    assert_ne!(
        direct_a.report().effective_seed(),
        direct_b.report().effective_seed()
    );
    assert_ne!(direct_a.matrix().as_slice(), direct_b.matrix().as_slice());
    assert_ne!(
        direct_a.report().effective_seed(),
        resampled_a.report().effective_seed()
    );
}

#[test]
fn paired_scale_probe_reuses_standard_normal_pseudodraws() {
    let values = vec![0.0; 24];
    let matrix = MatRef::new(&values, 12, 2).unwrap();
    let purpose = GaussianNoisePurpose::SeededScaleSensitivityProbe {
        study_identity_sha256: [0xC1; 32],
        coupling: GaussianNoiseSensitivityCoupling::CommonStandardNormalDrawsAcrossScales,
    };
    let stream = stream(2026, 4, 8);
    let low = GaussianNoiseTransform::new(declaration(0.125, purpose, "low scale probe"), stream)
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();
    let high = GaussianNoiseTransform::new(declaration(0.25, purpose, "high scale probe"), stream)
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();

    assert_eq!(
        low.report().effective_seed(),
        high.report().effective_seed()
    );
    for (&low_value, &high_value) in low.matrix().as_slice().iter().zip(high.matrix().as_slice()) {
        assert_eq!(high_value, 2.0 * low_value);
    }
}

#[test]
fn effective_seed_derivation_matches_revision_vector() {
    let values = vec![0.0; 8];
    let matrix = MatRef::new(&values, 4, 2).unwrap();
    let purpose = GaussianNoisePurpose::SeededScaleSensitivityProbe {
        study_identity_sha256: [0xC1; 32],
        coupling: GaussianNoiseSensitivityCoupling::CommonStandardNormalDrawsAcrossScales,
    };
    let result = GaussianNoiseTransform::new(
        declaration(0.125, purpose, "fixed effective-seed revision fixture"),
        stream(2026, 4, 8),
    )
    .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
    .unwrap();

    assert_eq!(result.report().effective_seed(), 0x905A_9A72_9025_744F);
}

#[test]
fn separate_scale_probe_uses_different_pseudodraws() {
    let values = vec![0.0; 24];
    let matrix = MatRef::new(&values, 12, 2).unwrap();
    let purpose = GaussianNoisePurpose::SeededScaleSensitivityProbe {
        study_identity_sha256: [0xC2; 32],
        coupling: GaussianNoiseSensitivityCoupling::SeparatePseudodrawStreamsAcrossScales,
    };
    let stream = stream(2026, 4, 8);
    let low = GaussianNoiseTransform::new(declaration(0.125, purpose, "low scale probe"), stream)
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();
    let high = GaussianNoiseTransform::new(declaration(0.25, purpose, "high scale probe"), stream)
        .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
        .unwrap();

    assert_ne!(
        low.report().effective_seed(),
        high.report().effective_seed()
    );
    assert_ne!(low.matrix().as_slice(), high.matrix().as_slice());
}

#[test]
fn application_fails_when_positive_scale_has_no_representable_effect() {
    let values = [1.0e300];
    let matrix = MatRef::new(&values, 1, 1).unwrap();
    let result = GaussianNoiseTransform::new(
        declaration(
            f64::MIN_POSITIVE,
            GaussianNoisePurpose::DeclaredObservationModel,
            "deliberately unrepresentable scale",
        ),
        stream(1, 1, 1),
    )
    .apply(matrix, GaussianNoiseApplicationContext::DirectInput);

    assert!(matches!(result, Err(PidError::NumericalInstability { .. })));
}

#[test]
fn report_serialization_uses_revisioned_typed_vocabulary() {
    let (values, rows, columns) = input();
    let matrix = MatRef::new(&values, rows, columns).unwrap();
    let result = GaussianNoiseTransform::new(
        declaration(
            0.1,
            GaussianNoisePurpose::SeededScaleSensitivityProbe {
                study_identity_sha256: [0xAB; 32],
                coupling: GaussianNoiseSensitivityCoupling::SeparatePseudodrawStreamsAcrossScales,
            },
            "serialization vocabulary fixture",
        ),
        stream(88, 3, 7),
    )
    .apply(matrix, GaussianNoiseApplicationContext::DirectInput)
    .unwrap();
    let json = serde_json::to_value(result.report()).unwrap();

    assert_eq!(json["contract_revision"], 1);
    assert_eq!(
        json["declaration"]["purpose"]["kind"],
        "seeded_scale_sensitivity_probe"
    );
    assert_eq!(
        json["generator_revision"],
        "split_mix64_box_muller_cosine_no_cache_row_major_v1"
    );
    assert_eq!(
        json["scientific_claim_boundary"],
        "ideal_population_law_only_v1"
    );
    assert_eq!(json["changes_estimand"], true);
    assert_eq!(
        json["declaration"]["purpose"]["coupling"],
        "separate_pseudodraw_streams_across_scales"
    );
    assert_eq!(
        serde_json::to_value(GaussianNoiseStreamSelection::SelectedWithoutEvaluationDataDependence)
            .unwrap(),
        "selected_without_evaluation_data_dependence"
    );
}

#[test]
fn application_obeys_resource_budget_and_cancellation() {
    let (values, rows, columns) = input();
    let matrix = MatRef::new(&values, rows, columns).unwrap();
    let make = || {
        GaussianNoiseTransform::new(
            declaration(
                0.1,
                GaussianNoisePurpose::DeclaredObservationModel,
                "bounded application",
            ),
            stream(5, 1, 1),
        )
    };
    let defaults = ResourceBudget::default();
    let tiny = ResourceBudget::new(
        1,
        defaults.max_pairwise_distances,
        defaults.max_operations_hint,
        defaults.max_threads,
    )
    .unwrap();
    assert!(matches!(
        make().apply_with_budget(matrix, GaussianNoiseApplicationContext::DirectInput, tiny),
        Err(PidError::ResourceLimitExceeded { .. })
    ));

    let cancellation = CancellationToken::new();
    cancellation.cancel();
    assert!(matches!(
        make().apply_with_budget_and_cancellation(
            matrix,
            GaussianNoiseApplicationContext::DirectInput,
            ResourceBudget::default(),
            &cancellation,
        ),
        Err(PidError::Cancelled { .. })
    ));
}
