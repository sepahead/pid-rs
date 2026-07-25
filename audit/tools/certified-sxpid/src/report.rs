use serde::Serialize;

use crate::digest::{canonical_digest, canonical_json_bytes, sha256_hex};
use crate::directed::{DyadicOutput, Enclosure};
use crate::error::CertError;
use crate::exact::{ExactLogTerm, LogExpression};
use crate::extract::{ExactComponents, ExactExtraction, ExtractionChecks};
use crate::lattice2::{self, ATOM_IDS, NODE_IDS};
use crate::product::{self, ExactProductEvidence, ExactProductResult, ExactProductSign};
use crate::resource::{
    PrecisionPolicy, PrecisionPolicyEvidence, DEFINITION_REVISION, MAX_CANONICAL_PAYLOAD_BYTES,
    MAX_ESTIMATED_EXACT_TERM_JSON_BYTES, MAX_TERMS_PER_EXPRESSION, MAX_TOTAL_EXACT_TERMS, UNITS,
};
use crate::schema::NormalizedInput;

pub(crate) const REPORT_SCHEMA: &str = "pid-rs/certified-sxpid-report/v2";
const EXPRESSION_SCHEMA: &str = "pid-rs/exact-log-linear/v1";

#[derive(Debug, Serialize)]
pub struct CertificateEnvelope {
    pub(crate) payload_sha256: String,
    pub(crate) payload: CertificatePayload,
}

#[derive(Debug, Serialize)]
pub(crate) struct CertificatePayload {
    schema: &'static str,
    status: &'static str,
    route: &'static str,
    definition_revision: &'static str,
    units: &'static str,
    input: InputEvidence,
    exact_expression: ExpressionEvidence,
    lattice: LatticeBinding,
    extraction_checks: ExtractionChecks,
    precision_policy: PrecisionPolicyBinding,
    arithmetic: ArithmeticEvidence,
    tool_binding: ToolBinding,
    coordinates: Vec<CertifiedCoordinate>,
    cross_checks: NumericalCrossChecks,
    claim_boundary: ClaimBoundary,
}

#[derive(Clone, Debug, Serialize)]
struct InputEvidence {
    raw_input_sha256: String,
    semantic_input_sha256: String,
    row_count: usize,
    total_count: String,
    source_state_widths: [usize; 2],
    target_state_width: usize,
}

#[derive(Clone, Debug, Serialize)]
struct ExpressionEvidence {
    schema: &'static str,
    coordinate_count: usize,
    coordinates_sha256: String,
    resource_use: ExpressionResourceUse,
}

#[derive(Clone, Debug, Serialize)]
struct ExpressionResourceUse {
    total_exact_terms: usize,
    maximum_terms_in_one_expression: usize,
    estimated_exact_term_json_bytes_upper_bound: usize,
}

#[derive(Clone, Debug, Serialize)]
struct LatticeBinding {
    sha256: String,
    value: lattice2::LatticeEvidence,
}

#[derive(Clone, Debug, Serialize)]
struct PrecisionPolicyBinding {
    sha256: String,
    value: PrecisionPolicyEvidence,
}

#[derive(Clone, Debug, Serialize)]
struct ArithmeticEvidence {
    locked_rug_crate_version: &'static str,
    locked_transitive_gmp_mpfr_sys_crate_version: &'static str,
    manifest_requested_rug_features: [&'static str; 3],
    direct_gmp_mpfr_sys_dependency_status: &'static str,
    effective_dependency_feature_resolution_status: &'static str,
    compiled_native_version_constants_status: &'static str,
    runtime_native_version_probe: &'static str,
    native_archive_digests: Option<&'static str>,
    native_archive_digest_status: &'static str,
    authoritative_endpoint_encoding: &'static str,
}

#[derive(Clone, Debug, Serialize)]
struct ToolBinding {
    runtime_source_manifest_sha256: String,
    source_manifest_encoding: &'static str,
    cargo_lock_sha256: String,
    canonical_json_encoding: &'static str,
    build_context: BuildContextEvidence,
    executable_digest_status: &'static str,
    project_distribution_route: &'static str,
    artifact_distribution_status: &'static str,
}

#[derive(Clone, Debug, Serialize)]
struct BuildContextEvidence {
    schema: &'static str,
    rustc_verbose_version: &'static str,
    build_host: &'static str,
    build_target: &'static str,
    cargo_profile_name: &'static str,
    cargo_profile_optimization_level: &'static str,
    cargo_profile_debug: &'static str,
    native_cache_policy: &'static str,
    context_scope: &'static str,
}

#[derive(Clone, Debug, Serialize)]
struct CertifiedCoordinate {
    identity: CoordinateIdentity,
    exact_terms: Vec<ExactLogTerm>,
    expression_sha256: String,
    interval: IntervalEvidence,
    exact_product: ExactProductEvidence,
}

#[derive(Clone, Debug, Serialize)]
struct CoordinateIdentity {
    kind: &'static str,
    node: &'static str,
    component: &'static str,
}

#[derive(Clone, Debug, Serialize)]
struct IntervalEvidence {
    lower: DyadicOutput,
    upper: DyadicOutput,
    final_working_precision_bits: u32,
    precision_iterations: u32,
    target_width_met: bool,
    decision: &'static str,
    exact_zero_witness: Option<&'static str>,
}

#[derive(Clone, Debug, Serialize)]
struct NumericalCrossChecks {
    direct_net_vs_informative_minus_misinformative_overlaps_checked: usize,
    successive_interval_intersections_checked: usize,
    all_passed: bool,
}

#[derive(Clone, Debug, Serialize)]
struct ClaimBoundary {
    permitted_claim: &'static str,
    excluded_claims: [&'static str; 12],
}

#[derive(Clone, Debug)]
pub(crate) struct EvaluationResult {
    pub(crate) intervals: Vec<Enclosure>,
    pub(crate) final_precision_bits: u32,
    pub(crate) iterations: u32,
    pub(crate) successive_intersections_checked: usize,
}

#[derive(Serialize)]
struct ExpressionCoordinateDigest<'a> {
    identity: CoordinateIdentity,
    exact_terms: &'a [ExactLogTerm],
}

pub(crate) fn build_certificate(
    input: &NormalizedInput,
    extraction: &ExactExtraction,
    policy: &PrecisionPolicy,
    evaluation: EvaluationResult,
    source_manifest_sha256: String,
    cargo_lock_sha256: String,
) -> Result<CertificateEnvelope, CertError> {
    let expression_specs = expression_specs(extraction);
    if expression_specs.len() != 24 || evaluation.intervals.len() != 24 {
        return Err(CertError::internal(
            "certificate assembly requires exactly 24 complete coordinates",
        ));
    }

    let expression_resource_use =
        preflight_expression_resources(expression_specs.iter().map(|spec| spec.expression))?;
    let exact_term_sets = expression_specs
        .iter()
        .map(|spec| spec.expression.canonical_terms())
        .collect::<Vec<_>>();
    let expression_digest_items = expression_specs
        .iter()
        .zip(&exact_term_sets)
        .map(|(spec, terms)| ExpressionCoordinateDigest {
            identity: CoordinateIdentity {
                kind: spec.kind,
                node: spec.node,
                component: spec.component,
            },
            exact_terms: terms,
        })
        .collect::<Vec<_>>();
    let coordinates_sha256 = canonical_digest(&expression_digest_items)?;
    let exact_products = product::compare_all(
        &expression_specs
            .iter()
            .map(|spec| spec.expression)
            .collect::<Vec<_>>(),
        &input.total_count,
    )?;
    if exact_products.len() != 24 {
        return Err(CertError::internal(
            "exact-product comparison requires exactly 24 complete coordinates",
        ));
    }

    let mut coordinates = Vec::with_capacity(24);
    for (index, (((spec, terms), interval), exact_product)) in expression_specs
        .iter()
        .zip(exact_term_sets)
        .zip(evaluation.intervals.iter())
        .zip(exact_products)
        .enumerate()
    {
        interval.validate()?;
        let target_width_met = interval.width() <= policy.target_width;
        if !target_width_met {
            return Err(CertError::internal(
                "certificate assembly received an interval above the target width",
            ));
        }
        let symbolic_zero = spec.expression.is_symbolic_zero();
        validate_product_interval_consistency(&exact_product, interval)?;
        coordinates.push(CertifiedCoordinate {
            identity: CoordinateIdentity {
                kind: spec.kind,
                node: spec.node,
                component: spec.component,
            },
            exact_terms: terms,
            expression_sha256: spec.expression.digest()?,
            interval: IntervalEvidence {
                lower: interval.lower.output(),
                upper: interval.upper.output(),
                final_working_precision_bits: evaluation.final_precision_bits,
                precision_iterations: evaluation.iterations,
                target_width_met,
                decision: interval.sign(symbolic_zero),
                exact_zero_witness: symbolic_zero
                    .then_some("canonical_exact_expression_has_no_terms"),
            },
            exact_product: exact_product.evidence,
        });
        if index >= 24 {
            return Err(CertError::internal(
                "coordinate iterator exceeded the two-source lattice",
            ));
        }
    }

    let direct_overlap_checks = validate_net_overlaps(&evaluation.intervals)?;
    let payload = CertificatePayload {
        schema: REPORT_SCHEMA,
        status: "certified",
        route: "categorical_sxpid2_averaged",
        definition_revision: DEFINITION_REVISION,
        units: UNITS,
        input: InputEvidence {
            raw_input_sha256: input.raw_input_sha256.clone(),
            semantic_input_sha256: input.semantic_input_sha256.clone(),
            row_count: input.rows.len(),
            total_count: input.total_count.to_string(),
            source_state_widths: input.source_widths,
            target_state_width: input.target_width,
        },
        exact_expression: ExpressionEvidence {
            schema: EXPRESSION_SCHEMA,
            coordinate_count: coordinates.len(),
            coordinates_sha256,
            resource_use: expression_resource_use,
        },
        lattice: LatticeBinding {
            sha256: lattice2::digest()?,
            value: lattice2::evidence(),
        },
        extraction_checks: extraction.checks.clone(),
        precision_policy: PrecisionPolicyBinding {
            sha256: policy.digest()?,
            value: policy.evidence(),
        },
        arithmetic: ArithmeticEvidence {
            locked_rug_crate_version: "1.30.0",
            locked_transitive_gmp_mpfr_sys_crate_version: "1.7.1",
            manifest_requested_rug_features: ["float", "rational", "std"],
            direct_gmp_mpfr_sys_dependency_status:
                "absent_to_remove_direct_dependency_feature_injection_surface",
            effective_dependency_feature_resolution_status:
                "not_self_reported_or_bound_official_qualification_separately_requires_default_locked_metadata_graph",
            compiled_native_version_constants_status:
                "not_reported_no_direct_native_sys_api_dependency",
            runtime_native_version_probe: "not_performed_by_safe_rust_wrapper",
            native_archive_digests: None,
            native_archive_digest_status:
                "absent_not_claimed_external_build_evidence_required_for_archive_binding",
            authoritative_endpoint_encoding: "normalized_exact_dyadic_significand_times_2^exponent2",
        },
        tool_binding: ToolBinding {
            runtime_source_manifest_sha256: source_manifest_sha256,
            source_manifest_encoding:
                "domain_tag_then_repeated_u64be_path_length_path_u64be_content_length_content",
            cargo_lock_sha256,
            canonical_json_encoding:
                "serde_json_value_recursive_lexicographic_object_keys_no_floats_v1",
            build_context: BuildContextEvidence {
                schema: env!("PID_CERTIFIER_BUILD_CONTEXT_SCHEMA"),
                rustc_verbose_version: env!("PID_CERTIFIER_RUSTC_VERBOSE_VERSION"),
                build_host: env!("PID_CERTIFIER_BUILD_HOST"),
                build_target: env!("PID_CERTIFIER_BUILD_TARGET"),
                cargo_profile_name: env!("PID_CERTIFIER_BUILD_PROFILE"),
                cargo_profile_optimization_level: env!("PID_CERTIFIER_BUILD_OPT_LEVEL"),
                cargo_profile_debug: env!("PID_CERTIFIER_BUILD_DEBUG"),
                native_cache_policy: env!("PID_CERTIFIER_NATIVE_CACHE_POLICY"),
                context_scope: "non_exhaustive_cargo_profile_metadata_only_external_evidence_required_for_effective_dependency_feature_resolution_rustc_wrappers_effective_flags_cargo_linker_native_compiler_and_cache_content",
            },
            executable_digest_status: "absent_runtime_tool_does_not_self_attest_its_executable",
            project_distribution_route: "source_only_policy",
            artifact_distribution_status: "not_verified_by_runtime",
        },
        coordinates,
        cross_checks: NumericalCrossChecks {
            direct_net_vs_informative_minus_misinformative_overlaps_checked:
                direct_overlap_checks,
            successive_interval_intersections_checked: evaluation
                .successive_intersections_checked,
            all_passed: true,
        },
        claim_boundary: ClaimBoundary {
            permitted_claim: "For this canonical exact two-source empirical count table, pinned SxPID definition and lattice, precision policy, and locked dependency versions, each emitted dyadic interval encloses the tool-encoded exact-real averaged categorical SxPID coordinate, conditional on the recorded source wrapper, explicitly non-exhaustive build context, and unverified effective dependency-feature resolution, native-library, compiler, effective-build-flags, and data-meaning trust boundary. When a coordinate's separately bounded exact-product record has status compared, that record additionally certifies exact equality to zero or strict sign by exact rational-product comparison after integer denominator clearing; the dyadic endpoints remain the enclosure authority and the interval-local decision is not rewritten. Manifest-requested Rug features and locked crate versions are reported; compiled native version constants, native archive digests, and executable digests are absent and are not claimed.",
            excluded_claims: [
                "pid-core_binary64_correctness",
                "population_or_sampling_assumptions",
                "estimator_consistency_or_calibration",
                "continuous_ksg_isx_or_pid",
                "three_or_four_source_sxpid",
                "imin",
                "pointwise_sxpid",
                "quantization_equivalence",
                "input_data_authenticity_or_provenance",
                "mpfr_gmp_rug_or_compiler_correctness",
                "downstream_application_validity",
                "formal_verification_of_all_pid_rs",
            ],
        },
    };
    let payload_bytes = canonical_json_bytes(&payload)?;
    if payload_bytes.len() > MAX_CANONICAL_PAYLOAD_BYTES {
        return Err(CertError::new(
            "certificate_resource_limit",
            format!(
                "canonical certificate payload has {} bytes; maximum is {MAX_CANONICAL_PAYLOAD_BYTES}",
                payload_bytes.len()
            ),
        ));
    }
    let payload_sha256 = sha256_hex(&payload_bytes);
    Ok(CertificateEnvelope {
        payload_sha256,
        payload,
    })
}

fn validate_product_interval_consistency(
    exact_product: &ExactProductResult,
    interval: &Enclosure,
) -> Result<(), CertError> {
    let lower = interval.lower.to_rational();
    let upper = interval.upper.to_rational();
    let consistent = match exact_product.sign {
        Some(ExactProductSign::Negative) => lower < 0,
        Some(ExactProductSign::Zero) => lower <= 0 && upper >= 0,
        Some(ExactProductSign::Positive) => upper > 0,
        None => true,
    };
    if !consistent {
        return Err(CertError::internal(
            "directed interval contradicts the bounded exact-product comparison",
        ));
    }
    Ok(())
}

fn preflight_expression_resources<'a>(
    expressions: impl Iterator<Item = &'a LogExpression>,
) -> Result<ExpressionResourceUse, CertError> {
    let mut total_exact_terms = 0usize;
    let mut maximum_terms_in_one_expression = 0usize;
    let mut estimated_exact_term_json_bytes_upper_bound = 0usize;

    for expression in expressions {
        let terms = expression.len();
        if terms > MAX_TERMS_PER_EXPRESSION {
            return Err(CertError::new(
                "certificate_resource_limit",
                format!(
                    "one exact expression has {terms} terms; maximum is {MAX_TERMS_PER_EXPRESSION}"
                ),
            ));
        }
        total_exact_terms = total_exact_terms.checked_add(terms).ok_or_else(|| {
            CertError::new(
                "certificate_resource_limit",
                "total exact-expression term count overflowed",
            )
        })?;
        if total_exact_terms > MAX_TOTAL_EXACT_TERMS {
            return Err(CertError::new(
                "certificate_resource_limit",
                format!(
                    "exact expressions have {total_exact_terms} total terms; maximum is {MAX_TOTAL_EXACT_TERMS}"
                ),
            ));
        }
        maximum_terms_in_one_expression = maximum_terms_in_one_expression.max(terms);
        estimated_exact_term_json_bytes_upper_bound = estimated_exact_term_json_bytes_upper_bound
            .checked_add(expression.estimated_canonical_terms_json_bytes()?)
            .ok_or_else(|| {
                CertError::new(
                    "certificate_resource_limit",
                    "exact-expression serialization estimate overflowed",
                )
            })?;
        if estimated_exact_term_json_bytes_upper_bound > MAX_ESTIMATED_EXACT_TERM_JSON_BYTES {
            return Err(CertError::new(
                "certificate_resource_limit",
                format!(
                    "estimated exact-term JSON requires at most {estimated_exact_term_json_bytes_upper_bound} bytes; policy maximum is {MAX_ESTIMATED_EXACT_TERM_JSON_BYTES}"
                ),
            ));
        }
    }

    Ok(ExpressionResourceUse {
        total_exact_terms,
        maximum_terms_in_one_expression,
        estimated_exact_term_json_bytes_upper_bound,
    })
}

struct ExpressionSpec<'a> {
    kind: &'static str,
    node: &'static str,
    component: &'static str,
    expression: &'a LogExpression,
}

pub(crate) fn expressions(extraction: &ExactExtraction) -> Vec<&LogExpression> {
    expression_specs(extraction)
        .into_iter()
        .map(|spec| spec.expression)
        .collect()
}

pub(crate) fn validate_resource_bounds(extraction: &ExactExtraction) -> Result<(), CertError> {
    let specs = expression_specs(extraction);
    preflight_expression_resources(specs.iter().map(|spec| spec.expression)).map(|_| ())
}

fn expression_specs(extraction: &ExactExtraction) -> Vec<ExpressionSpec<'_>> {
    let mut specs = Vec::with_capacity(24);
    append_component_specs(&mut specs, "cumulative", &NODE_IDS, &extraction.cumulative);
    append_component_specs(&mut specs, "atom", &ATOM_IDS, &extraction.atoms);
    specs
}

fn append_component_specs<'a>(
    specs: &mut Vec<ExpressionSpec<'a>>,
    kind: &'static str,
    node_ids: &[&'static str; 4],
    components: &'a ExactComponents,
) {
    for (component, expressions) in [
        ("informative", &components.informative),
        ("misinformative", &components.misinformative),
        ("net", &components.net),
    ] {
        for (node, expression) in node_ids.iter().zip(expressions) {
            specs.push(ExpressionSpec {
                kind,
                node,
                component,
                expression,
            });
        }
    }
}

fn validate_net_overlaps(intervals: &[Enclosure]) -> Result<usize, CertError> {
    if intervals.len() != 24 {
        return Err(CertError::internal(
            "net-overlap validation requires 24 coordinate intervals",
        ));
    }
    let mut checks = 0usize;
    for block_start in [0usize, 12] {
        for node in 0..4 {
            let informative = &intervals[block_start + node];
            let misinformative = &intervals[block_start + 4 + node];
            let net = &intervals[block_start + 8 + node];
            let derived = Enclosure::exact_subtract(informative, misinformative)?;
            if !derived.overlaps(net) {
                return Err(CertError::internal(format!(
                    "direct net interval is disjoint from informative-minus-misinformative at coordinate block {block_start}, node {node}"
                )));
            }
            checks += 1;
        }
    }
    Ok(checks)
}

#[derive(Serialize)]
pub struct FailureEnvelope<'a> {
    schema: &'static str,
    status: &'static str,
    error_code: &'a str,
    message: &'a str,
}

impl<'a> FailureEnvelope<'a> {
    /// Creates a machine-readable rejected-result envelope.
    #[must_use]
    pub fn from_error(error: &'a CertError) -> Self {
        Self {
            schema: REPORT_SCHEMA,
            status: "rejected",
            error_code: error.code(),
            message: error.message(),
        }
    }
}

#[cfg(test)]
mod tests {
    use rug::{Integer, Rational};

    use crate::directed::Enclosure;
    use crate::exact::LogExpression;
    use crate::product::compare_all;
    use crate::resource::MAX_TERMS_PER_EXPRESSION;

    use super::{preflight_expression_resources, validate_product_interval_consistency};

    fn one_term_product(argument: Rational) -> crate::product::ExactProductResult {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(1), argument)
            .expect("positive nonunit argument");
        compare_all(&[&expression], &Integer::from(1))
            .expect("bounded exact-product comparison")
            .remove(0)
    }

    #[test]
    fn strict_positive_product_requires_interval_with_positive_upper_endpoint() {
        let product = one_term_product(Rational::from(2));

        let error = validate_product_interval_consistency(&product, &Enclosure::exact_zero())
            .expect_err("an exact positive value cannot be enclosed by an interval ending at zero");

        assert_eq!(error.code(), "internal_soundness_failure");
    }

    #[test]
    fn strict_negative_product_requires_interval_with_negative_lower_endpoint() {
        let product = one_term_product(Rational::from((1, 2)));

        let error = validate_product_interval_consistency(&product, &Enclosure::exact_zero())
            .expect_err(
                "an exact negative value cannot be enclosed by an interval starting at zero",
            );

        assert_eq!(error.code(), "internal_soundness_failure");
    }

    #[test]
    fn expression_preflight_should_reject_term_amplification_before_serialization() {
        let mut expression = LogExpression::default();
        for index in 0..MAX_TERMS_PER_EXPRESSION {
            let denominator = i32::try_from(index + 2).expect("bounded denominator");
            expression
                .add_term(
                    Rational::from(1),
                    Rational::from((denominator + 1, denominator)),
                )
                .expect("positive distinct argument");
        }

        let denominator = i32::try_from(MAX_TERMS_PER_EXPRESSION + 2).expect("bounded denominator");
        let error = expression
            .add_term(
                Rational::from(1),
                Rational::from((denominator + 1, denominator)),
            )
            .expect_err("term amplification must fail during exact extraction");

        assert_eq!(error.code(), "certificate_resource_limit");
        preflight_expression_resources(std::iter::once(&expression))
            .expect("an expression at the declared limit remains admissible");
    }
}
