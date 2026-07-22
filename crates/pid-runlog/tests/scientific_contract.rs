use pid_runlog::experimental::schema3::*;
use pid_runlog::EstimatorIdentity;
use serde_json::json;

const PID2_KEYS: [&str; 8] = [
    "mi_source_1_action",
    "mi_source_2_action",
    "mi_joint_action",
    "co_information",
    "redundancy",
    "unique_source_1",
    "unique_source_2",
    "synergy",
];

fn hash(byte: u8, revision: ScientificHashRevision) -> ScientificHashIdentity {
    ScientificHashIdentity::sha256(revision, format!("{byte:02x}").repeat(32)).unwrap()
}

fn content(schema: &str, byte: u8) -> VersionedContentIdentity {
    VersionedContentIdentity::new(
        schema,
        "1",
        hash(byte, ScientificHashRevision::CanonicalJsonV2),
    )
    .unwrap()
}

fn reason(code: &str) -> ScientificReason {
    ScientificReason::new(
        ScientificReasonCode::new(code).unwrap(),
        format!("The condition has code {code}."),
    )
    .unwrap()
}

fn warning(code: &str) -> ScientificWarning {
    ScientificWarning::new(
        ScientificReasonCode::new(code).unwrap(),
        format!("The result has warning {code}."),
    )
    .unwrap()
}

fn artifact_not_applicable() -> ScientificArtifactIdentity {
    ScientificArtifactIdentity::not_applicable(reason("pid_runlog.not_applicable"))
}

fn method() -> ScientificMethodIdentity {
    let catalog_id = "pid2.isx.continuous";
    ScientificMethodIdentity::new(ScientificMethodIdentityInputs {
        catalog_id: catalog_id.to_string(),
        origin: ScientificMethodOrigin::PaperDerived,
        estimand_regime: ScientificEstimandRegime::ConditionalContinuous,
        api_maturity: ScientificApiMaturity::Experimental,
        completeness: ScientificCompleteness::Complete,
        availability: ScientificAvailability::LocalImplementation,
        catalog_entry: content(&format!("pid-rs/method-catalog-entry/{catalog_id}"), 1),
    })
    .unwrap()
}

fn estimator() -> ScientificEstimatorIdentity {
    ScientificEstimatorIdentity::available(EstimatorIdentity {
        family: "shared_exclusions".to_string(),
        definition_revision: "ehrlich_2024".to_string(),
        estimator_revision: "pid_rs_continuous_v1".to_string(),
    })
    .unwrap()
}

fn quantity(key: &str, byte: u8) -> ScientificQuantityDefinition {
    let origin = if key == "co_information" {
        ScientificMethodOrigin::PaperDerived
    } else {
        ScientificMethodOrigin::PaperDefined
    };
    ScientificQuantityDefinition::new(
        key,
        ScientificUnit::Nats,
        origin,
        content(&format!("pid-rs/quantity-definition/{key}"), byte),
    )
    .unwrap()
}

fn output_schema() -> ScientificOutputSchema {
    ScientificOutputSchema::new(
        "pid-rs/prisoma-pid2-output",
        "1",
        PID2_KEYS
            .iter()
            .enumerate()
            .map(|(index, key)| quantity(key, u8::try_from(index + 10).unwrap()))
            .collect(),
    )
    .unwrap()
}

fn values() -> ScientificValueSet {
    ScientificValueSet::try_from_pairs([
        ("mi_source_1_action", 0.40),
        ("mi_source_2_action", 0.30),
        ("mi_joint_action", 0.80),
        ("co_information", -0.10),
        ("redundancy", 0.10),
        ("unique_source_1", 0.30),
        ("unique_source_2", 0.20),
        ("synergy", 0.20),
    ])
    .unwrap()
}

fn pid2_invariants() -> ScientificInvariantContract {
    let invariant = |id: &str, terms: &[(&str, f64)]| {
        ScientificLinearInvariant::new(
            id,
            terms
                .iter()
                .map(|(key, coefficient)| ScientificLinearTerm::new(*key, *coefficient).unwrap())
                .collect(),
            1.0e-12,
            1.0e-12,
        )
        .unwrap()
    };
    ScientificInvariantContract::linear(vec![
        invariant(
            "pid2.atom_sum",
            &[
                ("redundancy", 1.0),
                ("unique_source_1", 1.0),
                ("unique_source_2", 1.0),
                ("synergy", 1.0),
                ("mi_joint_action", -1.0),
            ],
        ),
        invariant(
            "pid2.source_1_reconstruction",
            &[
                ("redundancy", 1.0),
                ("unique_source_1", 1.0),
                ("mi_source_1_action", -1.0),
            ],
        ),
        invariant(
            "pid2.source_2_reconstruction",
            &[
                ("redundancy", 1.0),
                ("unique_source_2", 1.0),
                ("mi_source_2_action", -1.0),
            ],
        ),
        invariant(
            "pid2.co_information",
            &[
                ("co_information", 1.0),
                ("mi_source_1_action", -1.0),
                ("mi_source_2_action", -1.0),
                ("mi_joint_action", 1.0),
            ],
        ),
        invariant(
            "pid2.redundancy_minus_synergy",
            &[
                ("redundancy", 1.0),
                ("synergy", -1.0),
                ("co_information", -1.0),
            ],
        ),
    ])
    .unwrap()
}

fn data(salt: f64) -> Vec<ScientificDataIdentity> {
    let members = [0, 1, 2, 3];
    let membership = scientific_split_membership_identity_v1(&members).unwrap();
    [
        (
            InformationVariableRole::Source { index: 0 },
            "source_1",
            [0.0 + salt, 1.0 + salt, 0.0 + salt, 1.0 + salt],
            30,
        ),
        (
            InformationVariableRole::Source { index: 1 },
            "source_2",
            [0.0 + salt, 0.0 + salt, 1.0 + salt, 1.0 + salt],
            31,
        ),
        (
            InformationVariableRole::Target,
            "action",
            [0.0 + salt, 1.0 + salt, 1.0 + salt, 0.0 + salt],
            32,
        ),
    ]
    .into_iter()
    .map(|(role, variable_id, matrix, byte)| {
        ScientificDataIdentity::new(
            role,
            variable_id,
            scientific_f64_matrix_identity_v1(4, 1, &matrix).unwrap(),
            membership.clone(),
            ScientificArtifactIdentity::available(content(
                &format!("pid-rs/source-artifact/{variable_id}"),
                byte,
            )),
        )
        .unwrap()
    })
    .collect()
}

fn data_on_members(
    template: &[ScientificDataIdentity],
    members: &[u64],
    include_target: bool,
) -> Vec<ScientificDataIdentity> {
    let membership = scientific_split_membership_identity_v1(members).unwrap();
    template
        .iter()
        .filter(|identity| {
            include_target || matches!(identity.role(), InformationVariableRole::Source { .. })
        })
        .enumerate()
        .map(|(index, identity)| {
            let values = (0..members.len())
                .map(|row| index as f64 + row as f64 / 10.0)
                .collect::<Vec<_>>();
            ScientificDataIdentity::new(
                identity.role(),
                identity.variable_id(),
                scientific_f64_matrix_identity_v1(
                    u64::try_from(members.len()).unwrap(),
                    1,
                    &values,
                )
                .unwrap(),
                membership.clone(),
                identity.source_artifact().clone(),
            )
            .unwrap()
        })
        .collect()
}

fn all_support_sets(data: &[ScientificDataIdentity]) -> Vec<Vec<String>> {
    let mut variables = data
        .iter()
        .map(|identity| identity.variable_id().to_string())
        .collect::<Vec<_>>();
    variables.sort();
    (1usize..(1usize << variables.len()))
        .map(|mask| {
            variables
                .iter()
                .enumerate()
                .filter(|(index, _)| mask & (1usize << index) != 0)
                .map(|(_, variable)| variable.clone())
                .collect()
        })
        .collect()
}

fn support(data: &[ScientificDataIdentity], with_envelope: bool) -> ScientificSupportIdentity {
    ScientificSupportIdentity::declared(
        content("pid-rs/support-contract", 40),
        all_support_sets(data),
        with_envelope.then(|| content("pid-rs/application-envelope", 41)),
    )
    .unwrap()
}

fn full_split(data: &[ScientificDataIdentity]) -> ScientificSplitIdentity {
    ScientificSplitIdentity::new(
        ScientificSplitRole::FullSample,
        "full_sample",
        data[0].row_membership_identity().clone(),
        content("pid-rs/parent-row-ledger", 42),
        artifact_not_applicable(),
    )
    .unwrap()
}

fn variables_from_data(data: &[ScientificDataIdentity]) -> Vec<ScientificRequestVariable> {
    data.iter()
        .map(|identity| {
            ScientificRequestVariable::new(identity.role(), identity.variable_id()).unwrap()
        })
        .collect()
}

fn pipeline_plan(lineage: &ScientificDataLineage) -> ScientificPipelinePlan {
    ScientificPipelinePlan::new(
        lineage
            .transforms()
            .iter()
            .map(|transform| {
                let fit = match transform.fit().status() {
                    ScientificTransformFitStatus::Stateless => {
                        ScientificTransformFitPlan::stateless()
                    }
                    ScientificTransformFitStatus::Fitted => ScientificTransformFitPlan::fitted(
                        transform.fit().access().unwrap(),
                        transform.fit().fit_split().unwrap(),
                    )
                    .unwrap(),
                    _ => unreachable!("test fixtures use known transform-fit states"),
                };
                ScientificTransformPlanStep::new(
                    transform.step_id(),
                    transform.kind(),
                    transform.contract().clone(),
                    fit,
                )
                .unwrap()
            })
            .collect(),
    )
    .unwrap()
}

#[allow(clippy::too_many_arguments)]
fn analysis_plan_for(
    plan_id: &str,
    method: &ScientificMethodIdentity,
    output_schema: &ScientificOutputSchema,
    lineage: &ScientificDataLineage,
    estimator: &ScientificEstimatorIdentity,
    estimator_contract: &ScientificArtifactIdentity,
    analysis_scope: &VersionedContentIdentity,
    support: &ScientificSupportIdentity,
    splits: &[ScientificSplitIdentity],
    planned_split: &ScientificSplitSelection,
) -> ScientificAnalysisPlan {
    let variables = lineage
        .source_data()
        .data()
        .map(variables_from_data)
        .unwrap_or_else(|| variables_from_data(&data(0.0)));
    ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: plan_id.to_string(),
        method: method.clone(),
        output_schema: output_schema.clone(),
        invariants: pid2_invariants(),
        variables,
        source_data: lineage.source_data().clone(),
        estimator: estimator.clone(),
        estimator_contract: estimator_contract.clone(),
        analysis_scope: analysis_scope.clone(),
        pipeline: pipeline_plan(lineage),
        support: support.clone(),
        splits: splits.to_vec(),
        planned_split: planned_split.clone(),
    })
    .unwrap()
}

fn implemented_regime(
    lineage: ScientificDataLineage,
    support: ScientificSupportIdentity,
    splits: Vec<ScientificSplitIdentity>,
    estimator_split: ScientificSplitSelection,
    preprocessing: ScientificArtifactIdentity,
    observation_model: ScientificArtifactIdentity,
    resampling: ScientificArtifactIdentity,
) -> ScientificRegime {
    let method = method();
    let estimator = estimator();
    let output_schema = output_schema();
    let estimator_contract =
        ScientificArtifactIdentity::available(content("pid-rs/estimator-contract", 46));
    let analysis_scope = content("pid-rs/analysis-scope/full", 47);
    let analysis_plan = ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: "plan_1".to_string(),
        method: method.clone(),
        output_schema: output_schema.clone(),
        invariants: pid2_invariants(),
        variables: variables_from_data(lineage.source_data().data().unwrap()),
        source_data: lineage.source_data().clone(),
        estimator: estimator.clone(),
        estimator_contract: estimator_contract.clone(),
        analysis_scope: analysis_scope.clone(),
        pipeline: pipeline_plan(&lineage),
        support: support.clone(),
        splits: splits.clone(),
        planned_split: estimator_split.clone(),
    })
    .unwrap();
    ScientificRegime::new(ScientificRegimeInputs {
        analysis_plan,
        method,
        estimator,
        output_schema,
        lineage,
        software: content("pid-rs/software-identity", 43),
        estimator_contract,
        estimator_report: ScientificArtifactIdentity::available(content(
            "pid-rs/estimate-report",
            44,
        )),
        analysis_scope,
        preprocessing,
        observation_model,
        resampling,
        support,
        splits,
        estimator_split,
    })
    .unwrap()
}

fn direct_regime(with_envelope: bool) -> ScientificRegime {
    let estimator_data = data(0.0);
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
        vec![],
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
    )
    .unwrap();
    implemented_regime(
        lineage,
        support(&estimator_data, with_envelope),
        vec![full_split(&estimator_data)],
        ScientificSplitSelection::selected("full_sample").unwrap(),
        artifact_not_applicable(),
        artifact_not_applicable(),
        artifact_not_applicable(),
    )
}

fn not_requested_regime() -> ScientificRegime {
    let source_data = data(0.0);
    let not_requested = reason("pid_runlog.not_requested");
    let method = method();
    let estimator = estimator();
    let output_schema = output_schema();
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::available(source_data.clone()).unwrap(),
        vec![],
        ScientificDataSet::not_applicable(not_requested.clone()),
    )
    .unwrap();
    let estimator_contract =
        ScientificArtifactIdentity::available(content("pid-rs/estimator-contract", 46));
    let analysis_scope = content("pid-rs/analysis-scope/full", 47);
    let support = support(&source_data, true);
    let splits = vec![full_split(&source_data)];
    let planned_split = ScientificSplitSelection::selected("full_sample").unwrap();
    let analysis_plan = ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: "plan_1".to_string(),
        method: method.clone(),
        output_schema: output_schema.clone(),
        invariants: pid2_invariants(),
        variables: variables_from_data(&source_data),
        source_data: lineage.source_data().clone(),
        estimator: estimator.clone(),
        estimator_contract: estimator_contract.clone(),
        analysis_scope: analysis_scope.clone(),
        pipeline: pipeline_plan(&lineage),
        support: support.clone(),
        splits: splits.clone(),
        planned_split,
    })
    .unwrap();
    ScientificRegime::new(ScientificRegimeInputs {
        analysis_plan,
        method,
        estimator,
        output_schema,
        lineage,
        software: content("pid-rs/software-identity", 43),
        estimator_contract,
        estimator_report: ScientificArtifactIdentity::not_applicable(not_requested.clone()),
        analysis_scope,
        preprocessing: artifact_not_applicable(),
        observation_model: artifact_not_applicable(),
        resampling: artifact_not_applicable(),
        support,
        splits,
        estimator_split: ScientificSplitSelection::not_applicable(not_requested),
    })
    .unwrap()
}

fn request_entry(
    regime: &ScientificRegime,
    outcome_id: &str,
    requested: bool,
) -> ScientificRequestEntry {
    ScientificRequestEntry::new(ScientificRequestEntryInputs {
        outcome_id: outcome_id.to_string(),
        requested,
        analysis_plan: regime.analysis_plan().identity().clone(),
    })
    .unwrap()
}

fn request_ledger(regime: &ScientificRegime, ids: &[&str]) -> ScientificRequestLedger {
    let entries = ids
        .iter()
        .map(|id| request_entry(regime, id, !id.ends_with("not_requested")))
        .collect();
    ScientificRequestLedger::new(
        "screen_1",
        regime
            .splits()
            .first()
            .map(|split| split.parent_row_ledger().clone())
            .unwrap_or_else(|| content("pid-rs/parent-row-ledger", 42)),
        entries,
    )
    .unwrap()
}

fn gate(
    verdict: ScientificGateVerdict,
    code: &str,
    evidence: Vec<VersionedContentIdentity>,
) -> ScientificGateDecision {
    ScientificGateDecision::new(verdict, reason(code), evidence).unwrap()
}

fn estimator_evidence(regime: &ScientificRegime) -> Vec<VersionedContentIdentity> {
    vec![
        regime.estimator_contract().identity().unwrap().clone(),
        regime.estimator_report().identity().unwrap().clone(),
        regime.software().clone(),
        regime.lineage().identity().clone(),
    ]
}

fn application_evidence(regime: &ScientificRegime) -> Vec<VersionedContentIdentity> {
    let mut evidence = vec![
        regime.support().application_envelope().unwrap().clone(),
        regime.analysis_scope().clone(),
        regime.splits()[0].parent_row_ledger().clone(),
        regime
            .splits()
            .iter()
            .find(|split| Some(split.split_name()) == regime.estimator_split().split_name())
            .unwrap()
            .identity()
            .clone(),
    ];
    if let Some(resampling) = regime.resampling().identity() {
        evidence.push(resampling.clone());
    }
    evidence
}

fn passed_gates(regime: &ScientificRegime, interpretation_allowed: bool) -> ScientificGateSet {
    ScientificGateSet::new(
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.population_passed",
            vec![regime.support().declaration_identity().unwrap().clone()],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.measure_passed",
            vec![
                regime.output_schema().identity().clone(),
                regime.method().catalog_entry().clone(),
            ],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.estimator_passed",
            estimator_evidence(regime),
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.application_passed",
            application_evidence(regime),
        ),
        InterpretationDecision::new(
            interpretation_allowed,
            reason("pid_runlog.interpretation_decision"),
        ),
    )
    .unwrap()
}

fn not_requested_gates() -> ScientificGateSet {
    let decision = || {
        gate(
            ScientificGateVerdict::NotApplicable,
            "pid_runlog.not_requested",
            vec![],
        )
    };
    ScientificGateSet::new(
        decision(),
        decision(),
        decision(),
        decision(),
        InterpretationDecision::new(false, reason("pid_runlog.not_requested")),
    )
    .unwrap()
}

fn abstained_gates(regime: &ScientificRegime, code: &str) -> ScientificGateSet {
    ScientificGateSet::new(
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.population_passed",
            vec![regime.support().declaration_identity().unwrap().clone()],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.measure_passed",
            vec![
                regime.output_schema().identity().clone(),
                regime.method().catalog_entry().clone(),
            ],
        ),
        gate(ScientificGateVerdict::Blocked, code, vec![]),
        gate(
            ScientificGateVerdict::NotEvaluated,
            "pid_runlog.application_not_evaluated",
            vec![],
        ),
        InterpretationDecision::new(false, reason("pid_runlog.interpretation_denied")),
    )
    .unwrap()
}

const TERMINAL_OUTCOME_IDS: [&str; 4] = [
    "case.not_requested",
    "case.produced",
    "case.warning",
    "case.abstained",
];

fn terminal_outcome_fixture() -> (ScientificRequestLedger, [ScientificOutcomeReport; 4]) {
    let regime = direct_regime(true);
    let inactive_regime = not_requested_regime();
    let ledger = ScientificRequestLedger::new(
        "screen_1",
        regime.splits()[0].parent_row_ledger().clone(),
        vec![
            request_entry(&inactive_regime, TERMINAL_OUTCOME_IDS[0], false),
            request_entry(&regime, TERMINAL_OUTCOME_IDS[1], true),
            request_entry(&regime, TERMINAL_OUTCOME_IDS[2], true),
            request_entry(&regime, TERMINAL_OUTCOME_IDS[3], true),
        ],
    )
    .unwrap();
    let reports = [
        ScientificOutcomeReport::new(
            TERMINAL_OUTCOME_IDS[0],
            ledger.clone(),
            inactive_regime,
            not_requested_gates(),
            ScientificStageSet::not_requested(),
            ScientificComputationOutcome::not_requested(reason("pid_runlog.not_requested")),
        )
        .unwrap(),
        ScientificOutcomeReport::new(
            TERMINAL_OUTCOME_IDS[1],
            ledger.clone(),
            regime.clone(),
            passed_gates(&regime, true),
            ScientificStageSet::requested(true, true, true).unwrap(),
            ScientificComputationOutcome::produced(values()),
        )
        .unwrap(),
        ScientificOutcomeReport::new(
            TERMINAL_OUTCOME_IDS[2],
            ledger.clone(),
            regime.clone(),
            passed_gates(&regime, false),
            ScientificStageSet::requested(true, true, true).unwrap(),
            ScientificComputationOutcome::produced_with_warning(
                values(),
                vec![warning("pid_core.use_warning")],
            )
            .unwrap(),
        )
        .unwrap(),
        ScientificOutcomeReport::new(
            TERMINAL_OUTCOME_IDS[3],
            ledger.clone(),
            regime.clone(),
            abstained_gates(&regime, "pid_core.preflight_blocked"),
            ScientificStageSet::requested(true, false, false).unwrap(),
            ScientificComputationOutcome::abstained(reason("pid_core.preflight_blocked")),
        )
        .unwrap(),
    ];
    (ledger, reports)
}

fn produced_without_support_gates(regime: &ScientificRegime) -> ScientificGateSet {
    ScientificGateSet::new(
        gate(
            ScientificGateVerdict::Conditional,
            "pid_runlog.population_conditional",
            vec![],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.measure_passed",
            vec![
                regime.output_schema().identity().clone(),
                regime.method().catalog_entry().clone(),
            ],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.estimator_passed",
            estimator_evidence(regime),
        ),
        gate(
            ScientificGateVerdict::Conditional,
            "pid_runlog.application_conditional",
            vec![],
        ),
        InterpretationDecision::new(false, reason("pid_runlog.interpretation_denied")),
    )
    .unwrap()
}

#[test]
fn scientific_hashes_are_lowercase_and_byte_contracts_are_frozen() {
    let f64_identity = scientific_f64_matrix_identity_v1(2, 2, &[0.0, -0.0, 1.5, -2.25]).unwrap();
    assert_eq!(
        f64_identity.content_hash().digest(),
        "9ae60ebe7c61b2c0065329875ad7d94f311a355b73bc52e32e52c242403fd680"
    );
    let u64_identity = scientific_u64_matrix_identity_v1(2, 2, &[0, 1, 2, u64::MAX]).unwrap();
    assert_eq!(
        u64_identity.content_hash().digest(),
        "ad77162ce77d14ebbb5bae3589e73c79e8e2113dff3547a7e2469661652c3797"
    );
    let split_identity = scientific_split_membership_identity_v1(&[3, 1, 3]).unwrap();
    assert_eq!(
        split_identity.content_hash().digest(),
        "e290e62f17bf93335d189fe2cb9993fb90bc4a2a74fd642e78f12380f5b2a7f0"
    );

    assert!(scientific_f64_matrix_identity_v1(2, 2, &[0.0; 3]).is_err());
    assert!(scientific_u64_matrix_identity_v1(0, 1, &[]).is_err());
    assert!(scientific_split_membership_identity_v1(&[]).is_err());

    let mut encoded =
        serde_json::to_value(hash(0xab, ScientificHashRevision::CanonicalJsonV2)).unwrap();
    encoded["digest"] = json!("AB".repeat(32));
    assert!(serde_json::from_value::<ScientificHashIdentity>(encoded).is_err());
}

#[test]
fn declared_pid_pair_schema_requires_complete_and_coherent_values() {
    let outcome_id = "screen.pid_pair.source_1_source_2";
    let regime = direct_regime(true);
    let report = ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, true),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    );
    assert!(report.is_ok());

    let partial = ScientificValueSet::try_from_pairs(
        PID2_KEYS[..7]
            .iter()
            .enumerate()
            .map(|(index, key)| (*key, index as f64)),
    )
    .unwrap();
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(partial),
    )
    .is_err());

    let mut with_extra = values().as_map().clone();
    with_extra.insert("atom_sum".to_string(), 0.8);
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(ScientificValueSet::new(with_extra).unwrap()),
    )
    .is_err());

    let mut incoherent = values().as_map().clone();
    incoherent.insert("synergy".to_string(), 0.9);
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(ScientificValueSet::new(incoherent).unwrap()),
    )
    .is_err());

    let negative_atom_values = ScientificValueSet::try_from_pairs([
        ("mi_source_1_action", 0.40),
        ("mi_source_2_action", 0.30),
        ("mi_joint_action", 0.80),
        ("co_information", -0.10),
        ("redundancy", -0.10),
        ("unique_source_1", 0.50),
        ("unique_source_2", 0.40),
        ("synergy", 0.00),
    ])
    .unwrap();
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(negative_atom_values),
    )
    .is_ok());

    let large_cancelling_values = ScientificValueSet::try_from_pairs([
        ("mi_source_1_action", 0.0),
        ("mi_source_2_action", 0.0),
        ("mi_joint_action", 0.0),
        ("co_information", 0.0),
        ("redundancy", 1.0e308),
        ("unique_source_1", -1.0e308),
        ("unique_source_2", -1.0e308),
        ("synergy", 1.0e308),
    ])
    .unwrap();
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(large_cancelling_values),
    )
    .is_ok());
}

#[test]
fn value_maps_reject_duplicate_nonfinite_empty_and_oversized_input() {
    assert!(ScientificValueSet::scalar("redundancy", f64::NAN).is_err());
    assert!(
        ScientificValueSet::try_from_pairs([("redundancy", 0.1), ("redundancy", 0.2)]).is_err()
    );
    assert!(serde_json::from_str::<ScientificValueSet>("{}").is_err());
    assert!(
        serde_json::from_str::<ScientificValueSet>(r#"{"redundancy":0.1,"redundancy":0.2}"#)
            .is_err()
    );
    assert!(serde_json::from_str::<ScientificValueSet>(r#"{"redundancy":1e400}"#).is_err());

    let too_many = (0..=256)
        .map(|index| (format!("value_{index}"), index as f64))
        .collect();
    assert!(ScientificValueSet::new(too_many).is_err());
}

#[test]
fn request_ledger_rejects_duplicates_and_unlisted_reports() {
    let regime = direct_regime(true);
    let entry = ScientificRequestEntry::new(ScientificRequestEntryInputs {
        outcome_id: "case_1".to_string(),
        requested: true,
        analysis_plan: regime.analysis_plan().identity().clone(),
    })
    .unwrap();
    assert!(ScientificRequestLedger::new(
        "screen",
        regime.splits()[0].parent_row_ledger().clone(),
        vec![entry.clone(), entry],
    )
    .is_err());

    let outcome_id = "case_2";
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &["case_1"]),
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .is_err());
}

#[test]
fn regime_requires_support_for_every_nonempty_variable_tuple() {
    let estimator_data = data(0.0);
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
        vec![],
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
    )
    .unwrap();
    let axis_only = ScientificSupportIdentity::declared(
        content("pid-rs/support-contract", 40),
        estimator_data
            .iter()
            .map(|identity| vec![identity.variable_id().to_string()])
            .collect(),
        Some(content("pid-rs/application-envelope", 41)),
    )
    .unwrap();
    assert!(ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: "axis_only".to_string(),
        method: method(),
        output_schema: output_schema(),
        invariants: pid2_invariants(),
        variables: variables_from_data(&estimator_data),
        source_data: lineage.source_data().clone(),
        estimator: estimator(),
        estimator_contract: ScientificArtifactIdentity::available(content(
            "pid-rs/estimator-contract",
            46,
        )),
        analysis_scope: content("pid-rs/analysis-scope/full", 47),
        pipeline: pipeline_plan(&lineage),
        support: axis_only,
        splits: vec![full_split(&estimator_data)],
        planned_split: ScientificSplitSelection::selected("full_sample").unwrap(),
    })
    .is_err());
    assert!(direct_regime(true).support().covered_variable_sets().len() == 7);
}

#[test]
fn each_passed_gate_must_cite_matching_regime_evidence() {
    for bad_gate in 0..4 {
        let outcome_id = "case.gate_evidence";
        let regime = direct_regime(true);
        let unrelated = content("pid-rs/unrelated-evidence", 99);
        let population = gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.population_passed",
            if bad_gate == 0 {
                vec![unrelated.clone()]
            } else {
                vec![regime.support().declaration_identity().unwrap().clone()]
            },
        );
        let measure = gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.measure_passed",
            if bad_gate == 1 {
                vec![unrelated.clone()]
            } else {
                vec![
                    regime.output_schema().identity().clone(),
                    regime.method().catalog_entry().clone(),
                ]
            },
        );
        let estimator_gate = gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.estimator_passed",
            if bad_gate == 2 {
                vec![unrelated.clone()]
            } else {
                estimator_evidence(&regime)
            },
        );
        let application = gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.application_passed",
            if bad_gate == 3 {
                vec![unrelated]
            } else {
                application_evidence(&regime)
            },
        );
        let gates = ScientificGateSet::new(
            population,
            measure,
            estimator_gate,
            application,
            InterpretationDecision::new(false, reason("pid_runlog.interpretation_denied")),
        )
        .unwrap();
        assert!(ScientificOutcomeReport::new(
            outcome_id,
            request_ledger(&regime, &[outcome_id]),
            regime,
            gates,
            ScientificStageSet::requested(true, true, true).unwrap(),
            ScientificComputationOutcome::produced(values()),
        )
        .is_err());
    }
}

#[test]
fn outcome_status_and_stage_facts_cannot_contradict_each_other() {
    assert_eq!(
        ScientificStageSet::requested(true, true, false)
            .unwrap()
            .stop_stage(),
        ScientificStopStage::Estimation
    );
    assert!(ScientificStageSet::requested(true, false, true).is_err());

    let outcome_id = "case.stages";
    let regime = direct_regime(true);
    let discrete_like_gates = ScientificGateSet::new(
        gate(
            ScientificGateVerdict::NotApplicable,
            "pid_runlog.population_not_applicable",
            vec![],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.measure_passed",
            vec![
                regime.output_schema().identity().clone(),
                regime.method().catalog_entry().clone(),
            ],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.estimator_passed",
            estimator_evidence(&regime),
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.application_passed",
            application_evidence(&regime),
        ),
        InterpretationDecision::new(false, reason("pid_runlog.interpretation_denied")),
    )
    .unwrap();
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        discrete_like_gates.clone(),
        ScientificStageSet::requested(true, false, false).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .is_err());

    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        abstained_gates(&regime, "pid_core.estimation_failed"),
        ScientificStageSet::requested(true, true, false).unwrap(),
        ScientificComputationOutcome::abstained(reason("pid_core.estimation_failed")),
    )
    .is_ok());

    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        abstained_gates(&regime, "pid_core.preflight_blocked"),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::abstained(reason("pid_core.preflight_blocked")),
    )
    .is_err());

    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        discrete_like_gates,
        ScientificStageSet::requested(false, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .is_ok());
}

fn no_implementation_regime() -> ScientificRegime {
    let no_implementation = reason("pid_core.no_implementation");
    let catalog_id = "pid3.mixed_dimension.full";
    let method = ScientificMethodIdentity::new(ScientificMethodIdentityInputs {
        catalog_id: catalog_id.to_string(),
        origin: ScientificMethodOrigin::PaperDefined,
        estimand_regime: ScientificEstimandRegime::ConditionalContinuous,
        api_maturity: ScientificApiMaturity::NotApplicable,
        completeness: ScientificCompleteness::NotApplicable,
        availability: ScientificAvailability::NoImplementation,
        catalog_entry: content(&format!("pid-rs/method-catalog-entry/{catalog_id}"), 60),
    })
    .unwrap();
    let estimator = ScientificEstimatorIdentity::unavailable(no_implementation.clone());
    let output_schema = output_schema();
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::not_applicable(no_implementation.clone()),
        vec![],
        ScientificDataSet::not_applicable(no_implementation.clone()),
    )
    .unwrap();
    let estimator_contract = ScientificArtifactIdentity::not_applicable(no_implementation.clone());
    let analysis_scope = content("pid-rs/analysis-scope/full", 47);
    let support = ScientificSupportIdentity::unsupported(no_implementation.clone());
    let estimator_split = ScientificSplitSelection::not_applicable(no_implementation.clone());
    let analysis_plan = ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: "no_implementation".to_string(),
        method: method.clone(),
        output_schema: output_schema.clone(),
        invariants: pid2_invariants(),
        variables: variables_from_data(&data(0.0)),
        source_data: lineage.source_data().clone(),
        estimator: estimator.clone(),
        estimator_contract: estimator_contract.clone(),
        analysis_scope: analysis_scope.clone(),
        pipeline: pipeline_plan(&lineage),
        support: support.clone(),
        splits: vec![],
        planned_split: estimator_split.clone(),
    })
    .unwrap();
    ScientificRegime::new(ScientificRegimeInputs {
        analysis_plan,
        method,
        estimator,
        output_schema,
        lineage,
        software: content("pid-rs/software-identity", 61),
        estimator_contract,
        estimator_report: ScientificArtifactIdentity::not_applicable(no_implementation.clone()),
        analysis_scope,
        preprocessing: ScientificArtifactIdentity::not_applicable(no_implementation.clone()),
        observation_model: ScientificArtifactIdentity::not_applicable(no_implementation.clone()),
        resampling: ScientificArtifactIdentity::not_applicable(no_implementation.clone()),
        support,
        splits: vec![],
        estimator_split,
    })
    .unwrap()
}

fn implemented_method_without_selected_estimator() -> ScientificRegime {
    let source_data = data(0.0);
    let unavailable = reason("pid_core.estimator_unavailable");
    let method = method();
    let estimator = ScientificEstimatorIdentity::unavailable(unavailable.clone());
    let output_schema = output_schema();
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::available(source_data.clone()).unwrap(),
        vec![],
        ScientificDataSet::not_produced(unavailable.clone()),
    )
    .unwrap();
    let estimator_contract = ScientificArtifactIdentity::not_produced(unavailable.clone());
    let analysis_scope = content("pid-rs/analysis-scope/full", 47);
    let support = support(&source_data, true);
    let splits = vec![full_split(&source_data)];
    let estimator_split = ScientificSplitSelection::not_produced(unavailable.clone());
    let analysis_plan = ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: "estimator_unavailable".to_string(),
        method: method.clone(),
        output_schema: output_schema.clone(),
        invariants: pid2_invariants(),
        variables: variables_from_data(&source_data),
        source_data: lineage.source_data().clone(),
        estimator: estimator.clone(),
        estimator_contract: estimator_contract.clone(),
        analysis_scope: analysis_scope.clone(),
        pipeline: pipeline_plan(&lineage),
        support: support.clone(),
        splits: splits.clone(),
        planned_split: estimator_split.clone(),
    })
    .unwrap();
    ScientificRegime::new(ScientificRegimeInputs {
        analysis_plan,
        method,
        estimator,
        output_schema,
        lineage,
        software: content("pid-rs/software-identity", 61),
        estimator_contract,
        estimator_report: ScientificArtifactIdentity::not_produced(unavailable.clone()),
        analysis_scope,
        preprocessing: artifact_not_applicable(),
        observation_model: artifact_not_applicable(),
        resampling: artifact_not_applicable(),
        support,
        splits,
        estimator_split,
    })
    .unwrap()
}

#[test]
fn method_availability_is_separate_from_per_run_estimator_selection() {
    let outcome_id = "case.estimator_unavailable";
    let regime = implemented_method_without_selected_estimator();
    let gates = abstained_gates(&regime, "pid_core.estimator_unavailable");
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        gates.clone(),
        ScientificStageSet::requested(true, false, false).unwrap(),
        ScientificComputationOutcome::abstained(reason("pid_core.estimator_unavailable")),
    )
    .is_ok());
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime,
        gates,
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .is_err());
}

#[test]
fn no_implementation_state_cannot_carry_numeric_output() {
    let outcome_id = "case.no_implementation";
    let regime = no_implementation_regime();
    let blocked = || {
        gate(
            ScientificGateVerdict::Blocked,
            "pid_core.no_implementation",
            vec![],
        )
    };
    let gates = ScientificGateSet::new(
        blocked(),
        blocked(),
        blocked(),
        gate(
            ScientificGateVerdict::NotEvaluated,
            "pid_runlog.application_not_evaluated",
            vec![],
        ),
        InterpretationDecision::new(false, reason("pid_runlog.interpretation_denied")),
    )
    .unwrap();

    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        gates.clone(),
        ScientificStageSet::requested(false, false, false).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .is_err());
    assert!(ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime,
        gates,
        ScientificStageSet::requested(false, false, false).unwrap(),
        ScientificComputationOutcome::abstained(reason("pid_core.no_implementation")),
    )
    .is_ok());
}

#[test]
fn absent_artifacts_use_typed_states_without_hash_placeholders() {
    let regime = no_implementation_regime();
    let encoded = serde_json::to_value(&regime).unwrap();
    for name in [
        "estimator_report",
        "preprocessing",
        "observation_model",
        "resampling",
    ] {
        assert_eq!(encoded[name]["status"], "not_applicable");
        assert!(encoded[name].get("identity").is_none());
        assert!(encoded[name].get("content_hash").is_none());
    }
}

#[test]
fn transform_lineage_requires_exact_edges_and_matching_artifacts() {
    let source = data(0.0);
    let estimator_data = data(0.25);
    let observation_contract = content("pid-rs/observation-model", 70);
    let edge = ScientificTransformEdge::new(
        "observation_noise_1",
        ScientificTransformKind::ObservationModel,
        observation_contract.clone(),
        ScientificTransformFit::stateless(),
        source.clone(),
        estimator_data.clone(),
    )
    .unwrap();
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::available(source.clone()).unwrap(),
        vec![edge.clone()],
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
    )
    .unwrap();
    let observation_group = lineage
        .transform_group_identity(ScientificTransformKind::ObservationModel)
        .unwrap()
        .unwrap();
    assert!(implemented_regime(
        lineage,
        support(&estimator_data, true),
        vec![full_split(&estimator_data)],
        ScientificSplitSelection::selected("full_sample").unwrap(),
        artifact_not_applicable(),
        ScientificArtifactIdentity::available(observation_group),
        artifact_not_applicable(),
    )
    .observation_model()
    .identity()
    .is_some());

    assert!(ScientificDataLineage::new(
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
        vec![edge],
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
    )
    .is_err());

    let direct_lineage = ScientificDataLineage::new(
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
        vec![],
        ScientificDataSet::available(estimator_data.clone()).unwrap(),
    )
    .unwrap();
    let method = method();
    let estimator = estimator();
    let output_schema = output_schema();
    let estimator_contract =
        ScientificArtifactIdentity::available(content("pid-rs/estimator-contract", 46));
    let analysis_scope = content("pid-rs/analysis-scope/full", 47);
    let support = support(&estimator_data, true);
    let splits = vec![full_split(&estimator_data)];
    let estimator_split = ScientificSplitSelection::selected("full_sample").unwrap();
    let analysis_plan = analysis_plan_for(
        "direct",
        &method,
        &output_schema,
        &direct_lineage,
        &estimator,
        &estimator_contract,
        &analysis_scope,
        &support,
        &splits,
        &estimator_split,
    );
    let inputs = ScientificRegimeInputs {
        analysis_plan,
        method,
        estimator,
        output_schema,
        lineage: direct_lineage,
        software: content("pid-rs/software-identity", 43),
        estimator_contract,
        estimator_report: ScientificArtifactIdentity::available(content(
            "pid-rs/estimate-report",
            44,
        )),
        analysis_scope,
        preprocessing: artifact_not_applicable(),
        observation_model: ScientificArtifactIdentity::available(observation_contract),
        resampling: artifact_not_applicable(),
        support,
        splits,
        estimator_split,
    };
    assert!(ScientificRegime::new(inputs).is_err());
}

#[test]
fn fitted_transform_policies_bind_access_split_and_ordered_steps() {
    let source = data(0.0);
    let standardized = data(0.1);
    let projected = data(0.2);
    let training_members = [0, 1];

    assert!(ScientificTransformFit::fitted(
        content("pid-rs/fitted-state/invalid-unsupervised", 71),
        ScientificFitAccess::UnsupervisedSources,
        data_on_members(&source, &training_members, true),
        "training",
    )
    .is_err());
    assert!(ScientificTransformFit::fitted(
        content("pid-rs/fitted-state/invalid-supervised", 72),
        ScientificFitAccess::SupervisedSourcesAndTarget,
        data_on_members(&source, &training_members, false),
        "training",
    )
    .is_err());

    let standardize = ScientificTransformEdge::new(
        "standardize_1",
        ScientificTransformKind::Preprocessing,
        content("pid-rs/transform/standardize", 73),
        ScientificTransformFit::fitted(
            content("pid-rs/fitted-state/standardize", 74),
            ScientificFitAccess::UnsupervisedSources,
            data_on_members(&source, &training_members, false),
            "training",
        )
        .unwrap(),
        source.clone(),
        standardized.clone(),
    )
    .unwrap();
    let project = ScientificTransformEdge::new(
        "pls_1",
        ScientificTransformKind::Preprocessing,
        content("pid-rs/transform/pls", 75),
        ScientificTransformFit::fitted(
            content("pid-rs/fitted-state/pls", 76),
            ScientificFitAccess::SupervisedSourcesAndTarget,
            data_on_members(&standardized, &training_members, true),
            "training",
        )
        .unwrap(),
        standardized.clone(),
        projected.clone(),
    )
    .unwrap();
    let lineage = ScientificDataLineage::new(
        ScientificDataSet::available(source.clone()).unwrap(),
        vec![standardize, project],
        ScientificDataSet::available(projected.clone()).unwrap(),
    )
    .unwrap();
    let training = ScientificSplitIdentity::new(
        ScientificSplitRole::Training,
        "training",
        scientific_split_membership_identity_v1(&training_members).unwrap(),
        content("pid-rs/parent-row-ledger", 42),
        ScientificArtifactIdentity::available(content("pid-rs/partition-manifest", 77)),
    )
    .unwrap();
    let splits = vec![full_split(&source), training.clone()];
    let preprocessing = ScientificArtifactIdentity::available(
        lineage
            .transform_group_identity(ScientificTransformKind::Preprocessing)
            .unwrap()
            .unwrap(),
    );
    let regime = implemented_regime(
        lineage.clone(),
        support(&projected, true),
        splits.clone(),
        ScientificSplitSelection::selected("full_sample").unwrap(),
        preprocessing.clone(),
        artifact_not_applicable(),
        artifact_not_applicable(),
    );
    assert_eq!(regime.lineage().transforms().len(), 2);
    assert_eq!(
        regime.lineage().transforms()[0].fit().access(),
        Some(ScientificFitAccess::UnsupervisedSources)
    );
    assert_eq!(
        regime.lineage().transforms()[1].fit().access(),
        Some(ScientificFitAccess::SupervisedSourcesAndTarget)
    );

    let method = method();
    let estimator = estimator();
    let schema = output_schema();
    let estimator_contract =
        ScientificArtifactIdentity::available(content("pid-rs/estimator-contract", 46));
    let analysis_scope = content("pid-rs/analysis-scope/full", 47);
    assert!(ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
        plan_id: "missing_fit_split".to_string(),
        method: method.clone(),
        output_schema: schema.clone(),
        invariants: pid2_invariants(),
        variables: variables_from_data(&source),
        source_data: lineage.source_data().clone(),
        estimator: estimator.clone(),
        estimator_contract: estimator_contract.clone(),
        analysis_scope: analysis_scope.clone(),
        pipeline: pipeline_plan(&lineage),
        support: support(&projected, true),
        splits: vec![full_split(&source)],
        planned_split: ScientificSplitSelection::selected("full_sample").unwrap(),
    })
    .is_err());

    let mismatched_training = ScientificSplitIdentity::new(
        ScientificSplitRole::Training,
        "training",
        scientific_split_membership_identity_v1(&[0, 2]).unwrap(),
        content("pid-rs/parent-row-ledger", 42),
        training.partition_manifest().clone(),
    )
    .unwrap();
    let bad_splits = vec![full_split(&source), mismatched_training];
    let estimator_split = ScientificSplitSelection::selected("full_sample").unwrap();
    let declared_support = support(&projected, true);
    let plan = analysis_plan_for(
        "mismatched_fit_membership",
        &method,
        &schema,
        &lineage,
        &estimator,
        &estimator_contract,
        &analysis_scope,
        &declared_support,
        &bad_splits,
        &estimator_split,
    );
    assert!(ScientificRegime::new(ScientificRegimeInputs {
        analysis_plan: plan,
        method,
        estimator,
        output_schema: schema,
        lineage,
        software: content("pid-rs/software-identity", 43),
        estimator_contract,
        estimator_report: ScientificArtifactIdentity::available(content(
            "pid-rs/estimate-report",
            44,
        )),
        analysis_scope,
        preprocessing,
        observation_model: artifact_not_applicable(),
        resampling: artifact_not_applicable(),
        support: declared_support,
        splits: bad_splits,
        estimator_split,
    })
    .is_err());

    assert!(ScientificTransformEdge::new(
        "row_changing_preprocess",
        ScientificTransformKind::Preprocessing,
        content("pid-rs/transform/row-changing", 78),
        ScientificTransformFit::stateless(),
        source,
        data_on_members(&projected, &[0, 1], true),
    )
    .is_err());
}

#[test]
fn set_like_fields_have_canonical_order() {
    let mut reversed_data = data(0.0);
    let ordered_data = reversed_data.clone();
    reversed_data.reverse();
    assert_eq!(
        ScientificDataSet::available(ordered_data).unwrap(),
        ScientificDataSet::available(reversed_data).unwrap()
    );

    let mut quantities = PID2_KEYS
        .iter()
        .enumerate()
        .map(|(index, key)| quantity(key, u8::try_from(index + 10).unwrap()))
        .collect::<Vec<_>>();
    quantities.reverse();
    assert_eq!(
        ScientificOutputSchema::new("pid-rs/prisoma-pid2-output", "1", quantities)
            .unwrap()
            .identity(),
        output_schema().identity()
    );

    let data = data(0.0);
    let mut support_sets = all_support_sets(&data);
    support_sets.reverse();
    assert_eq!(
        ScientificSupportIdentity::declared(
            content("pid-rs/support-contract", 40),
            support_sets,
            Some(content("pid-rs/application-envelope", 41)),
        )
        .unwrap(),
        support(&data, true)
    );

    let evidence_a = content("pid-rs/evidence/a", 80);
    let evidence_b = content("pid-rs/evidence/b", 81);
    assert_eq!(
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.gate_passed",
            vec![evidence_a.clone(), evidence_b.clone()],
        ),
        gate(
            ScientificGateVerdict::Passed,
            "pid_runlog.gate_passed",
            vec![evidence_b, evidence_a],
        )
    );

    let warned = ScientificComputationOutcome::produced_with_warning(
        values(),
        vec![warning("pid_core.z_warning"), warning("pid_core.a_warning")],
    )
    .unwrap();
    assert_eq!(warned.warnings()[0].code().as_str(), "pid_core.a_warning");

    let regime = direct_regime(true);
    let ledger_a = request_ledger(&regime, &["case_b", "case_a"]);
    let ledger_b = request_ledger(&regime, &["case_a", "case_b"]);
    assert_eq!(ledger_a, ledger_b);
}

#[test]
fn split_selection_must_match_membership_parent_and_partition_manifest() {
    let estimator_data = data(0.0);
    let lineage = || {
        ScientificDataLineage::new(
            ScientificDataSet::available(estimator_data.clone()).unwrap(),
            vec![],
            ScientificDataSet::available(estimator_data.clone()).unwrap(),
        )
        .unwrap()
    };
    let wrong_membership = ScientificSplitIdentity::new(
        ScientificSplitRole::FullSample,
        "full_sample",
        scientific_split_membership_identity_v1(&[3, 2, 1, 0]).unwrap(),
        content("pid-rs/parent-row-ledger", 42),
        artifact_not_applicable(),
    )
    .unwrap();
    let base_plan = |splits| {
        let lineage = lineage();
        ScientificAnalysisPlan::new(ScientificAnalysisPlanInputs {
            plan_id: "split_plan".to_string(),
            method: method(),
            output_schema: output_schema(),
            invariants: pid2_invariants(),
            variables: variables_from_data(&estimator_data),
            source_data: lineage.source_data().clone(),
            estimator: estimator(),
            estimator_contract: ScientificArtifactIdentity::available(content(
                "pid-rs/estimator-contract",
                46,
            )),
            analysis_scope: content("pid-rs/analysis-scope/full", 47),
            pipeline: pipeline_plan(&lineage),
            support: support(&estimator_data, true),
            splits,
            planned_split: ScientificSplitSelection::selected("full_sample").unwrap(),
        })
    };
    assert!(base_plan(vec![wrong_membership]).is_err());

    let parent_a = content("pid-rs/parent-row-ledger", 90);
    let parent_b = content("pid-rs/parent-row-ledger", 91);
    let manifest = ScientificArtifactIdentity::available(content("pid-rs/partition-manifest", 92));
    let evaluation = ScientificSplitIdentity::new(
        ScientificSplitRole::Evaluation,
        "full_sample",
        estimator_data[0].row_membership_identity().clone(),
        parent_a,
        manifest.clone(),
    )
    .unwrap();
    let test = ScientificSplitIdentity::new(
        ScientificSplitRole::Test,
        "test",
        scientific_split_membership_identity_v1(&[0, 1]).unwrap(),
        parent_b,
        manifest,
    )
    .unwrap();
    assert!(base_plan(vec![evaluation, test]).is_err());

    assert!(ScientificSplitIdentity::new(
        ScientificSplitRole::Training,
        "training",
        scientific_split_membership_identity_v1(&[0, 1]).unwrap(),
        content("pid-rs/parent-row-ledger", 90),
        artifact_not_applicable(),
    )
    .is_err());
}

#[test]
fn all_outcome_states_round_trip_and_absent_states_have_no_numbers() {
    let (_, reports) = terminal_outcome_fixture();

    for report in reports {
        let encoded = serde_json::to_value(&report).unwrap();
        if matches!(
            report.outcome().status(),
            ScientificOutcomeStatus::NotRequested | ScientificOutcomeStatus::Abstained
        ) {
            assert!(encoded["outcome"].get("values_nats").is_none());
        }
        let decoded: ScientificOutcomeReport = serde_json::from_value(encoded).unwrap();
        assert_eq!(decoded, report);
    }
}

#[test]
fn outcome_coverage_counts_each_terminal_state_in_any_order() {
    let (ledger, reports) = terminal_outcome_fixture();
    let mut forward = ScientificOutcomeCoverageValidator::new(ledger.clone()).unwrap();
    for report in &reports {
        forward.push(report).unwrap();
    }
    let forward = forward.finish().unwrap();

    let mut reverse = ScientificOutcomeCoverageValidator::new(ledger.clone()).unwrap();
    for report in reports.iter().rev() {
        reverse.push(report).unwrap();
    }
    let reverse = reverse.finish().unwrap();

    assert_eq!(forward, reverse);
    assert_eq!(forward.request_ledger(), &ledger);
    assert_eq!(forward.expected(), 4);
    assert_eq!(forward.requested(), 3);
    assert_eq!(forward.not_requested(), 1);
    assert_eq!(forward.produced(), 1);
    assert_eq!(forward.produced_with_warning(), 1);
    assert_eq!(forward.abstained(), 1);
    assert_eq!(forward.declared_support_compatible(), 3);
    assert_eq!(forward.preflight_passed(), 2);
    assert_eq!(forward.estimated(), 2);
    assert_eq!(
        forward.expected(),
        forward.not_requested()
            + forward.produced()
            + forward.produced_with_warning()
            + forward.abstained()
    );
    assert_eq!(
        forward.requested(),
        forward.produced() + forward.produced_with_warning() + forward.abstained()
    );
    assert_eq!(
        forward.not_requested(),
        forward.expected() - forward.requested()
    );
    assert_eq!(
        forward.estimated(),
        forward.produced() + forward.produced_with_warning()
    );
    assert!(forward.estimated() <= forward.preflight_passed());
    assert!(forward.preflight_passed() <= forward.requested());
    assert!(forward.declared_support_compatible() <= forward.requested());
}

#[test]
fn outcome_coverage_rejects_duplicate_without_mutating_state() {
    let (ledger, reports) = terminal_outcome_fixture();
    let mut validator = ScientificOutcomeCoverageValidator::new(ledger).unwrap();
    validator.push(&reports[0]).unwrap();

    let error = validator.push(&reports[0]).unwrap_err();

    assert!(format!("{error:#}").contains("duplicate terminal scientific outcome ID"));
    for report in &reports[1..] {
        validator.push(report).unwrap();
    }
    let coverage = validator.finish().unwrap();
    assert_eq!(coverage.expected(), 4);
    assert_eq!(coverage.not_requested(), 1);
}

#[test]
fn outcome_coverage_rejects_different_ledger_without_mutating_state() {
    let (ledger, reports) = terminal_outcome_fixture();
    let regime = direct_regime(true);
    let other_ledger = request_ledger(&regime, &[TERMINAL_OUTCOME_IDS[1]]);
    assert_eq!(ledger.ledger_id(), other_ledger.ledger_id());
    assert_ne!(ledger, other_ledger);
    let other_report = ScientificOutcomeReport::new(
        TERMINAL_OUTCOME_IDS[1],
        other_ledger,
        regime.clone(),
        passed_gates(&regime, false),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .unwrap();
    let mut validator = ScientificOutcomeCoverageValidator::new(ledger).unwrap();

    let error = validator.push(&other_report).unwrap_err();

    assert!(format!("{error:#}").contains("does not match the declared request ledger"));
    for report in &reports {
        validator.push(report).unwrap();
    }
    assert_eq!(validator.finish().unwrap().expected(), 4);
}

#[test]
fn outcome_coverage_finish_reports_only_one_bounded_missing_id() {
    let (ledger, reports) = terminal_outcome_fixture();
    let mut validator = ScientificOutcomeCoverageValidator::new(ledger).unwrap();
    for report in &reports[..2] {
        validator.push(report).unwrap();
    }

    let error = validator.finish().unwrap_err();
    let message = format!("{error:#}");

    assert!(message.contains("missing terminal-outcome count: 2"));
    assert!(message.contains(TERMINAL_OUTCOME_IDS[3]));
    assert!(!message.contains(TERMINAL_OUTCOME_IDS[2]));
    assert!(message.len() < 512);
}

#[test]
fn outcome_coverage_cap_precedes_state_allocation() {
    let regime = direct_regime(true);
    let limit = ScientificOutcomeCoverageValidator::MAX_OUTCOMES;
    let mut entries = (0..limit)
        .map(|index| request_entry(&regime, &format!("case_{index:04}"), true))
        .collect::<Vec<_>>();
    let ledger_at_limit = ScientificRequestLedger::new(
        "large_screen",
        regime.splits()[0].parent_row_ledger().clone(),
        entries.clone(),
    )
    .unwrap();
    ScientificOutcomeCoverageValidator::new(ledger_at_limit).unwrap();

    entries.push(request_entry(&regime, &format!("case_{limit:04}"), true));
    let ledger = ScientificRequestLedger::new(
        "large_screen",
        regime.splits()[0].parent_row_ledger().clone(),
        entries,
    )
    .unwrap();

    let error = ScientificOutcomeCoverageValidator::new(ledger).unwrap_err();
    let message = format!("{error:#}");

    assert!(message.contains("supports at most 1024 ledger entries"));
    assert!(message.contains("got 1025"));
}

#[test]
fn outcome_coverage_keeps_support_and_preflight_counts_independent() {
    let outcome_id = "case.preflight_without_support";
    let regime = direct_regime(true);
    let ledger = request_ledger(&regime, &[outcome_id]);
    let report = ScientificOutcomeReport::new(
        outcome_id,
        ledger.clone(),
        regime.clone(),
        produced_without_support_gates(&regime),
        ScientificStageSet::requested(false, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .unwrap();
    let mut validator = ScientificOutcomeCoverageValidator::new(ledger).unwrap();
    validator.push(&report).unwrap();

    let coverage = validator.finish().unwrap();

    assert_eq!(coverage.declared_support_compatible(), 0);
    assert_eq!(coverage.preflight_passed(), 1);
    assert_eq!(coverage.estimated(), 1);
}

#[test]
fn canonical_identities_detect_tampering() {
    let outcome_id = "case.tamper";
    let regime = direct_regime(true);
    let report = ScientificOutcomeReport::new(
        outcome_id,
        request_ledger(&regime, &[outcome_id]),
        regime.clone(),
        passed_gates(&regime, true),
        ScientificStageSet::requested(true, true, true).unwrap(),
        ScientificComputationOutcome::produced(values()),
    )
    .unwrap();

    let mut encoded = serde_json::to_value(&report).unwrap();
    encoded["regime"]["method"]["api_maturity"] = json!("research_only");
    assert!(serde_json::from_value::<ScientificOutcomeReport>(encoded).is_err());

    let mut encoded = serde_json::to_value(&report).unwrap();
    encoded["regime"]["output_schema"]["revision"] = json!("2");
    assert!(serde_json::from_value::<ScientificOutcomeReport>(encoded).is_err());

    let mut encoded = serde_json::to_value(&report).unwrap();
    encoded["outcome"]["values_nats"]["synergy"] = json!(0.9);
    assert!(serde_json::from_value::<ScientificOutcomeReport>(encoded).is_err());

    let mut encoded = serde_json::to_value(&report).unwrap();
    encoded["request_ledger"]["ledger_id"] = json!("other_screen");
    assert!(serde_json::from_value::<ScientificOutcomeReport>(encoded).is_err());

    for pointer in [
        "/regime/analysis_plan/analysis_scope/content_hash/digest",
        "/regime/analysis_plan/estimator_contract/identity/content_hash/digest",
        "/regime/analysis_plan/pipeline/identity/content_hash/digest",
        "/regime/analysis_plan/support/declaration_identity/content_hash/digest",
        "/regime/analysis_plan/splits/0/identity/content_hash/digest",
    ] {
        let mut encoded = serde_json::to_value(&report).unwrap();
        *encoded.pointer_mut(pointer).unwrap() = json!("ff".repeat(32));
        assert!(
            serde_json::from_value::<ScientificOutcomeReport>(encoded).is_err(),
            "tampering at {pointer} must fail",
        );
    }
}

#[test]
fn hostile_deserialization_rejects_extra_fields_large_arrays_and_wide_integers() {
    assert!(serde_json::from_value::<InformationVariableRole>(json!({
        "kind": "target",
        "extra": true
    }))
    .is_err());

    let stage = ScientificStageSet::not_requested();
    let mut encoded = serde_json::to_value(stage).unwrap();
    encoded["extra"] = json!(true);
    assert!(serde_json::from_value::<ScientificStageSet>(encoded).is_err());

    let evidence = vec![content("pid-rs/evidence", 100); 1_025];
    let encoded = json!({
        "verdict": "passed",
        "reason": reason("pid_runlog.gate_passed"),
        "evidence": evidence,
    });
    assert!(serde_json::from_value::<ScientificGateDecision>(encoded).is_err());

    let encoded_data = serde_json::to_string(&data(0.0)[0]).unwrap();
    let encoded_data = encoded_data.replace("\"rows\":4", "\"rows\":18446744073709551616");
    assert!(serde_json::from_str::<ScientificDataIdentity>(&encoded_data).is_err());
}

#[test]
fn method_axes_and_catalog_binding_must_agree() {
    let catalog_id = "pid3.mixed_dimension.full";
    let entry = content(&format!("pid-rs/method-catalog-entry/{catalog_id}"), 110);
    assert!(
        ScientificMethodIdentity::new(ScientificMethodIdentityInputs {
            catalog_id: catalog_id.to_string(),
            origin: ScientificMethodOrigin::PaperDefined,
            estimand_regime: ScientificEstimandRegime::ConditionalContinuous,
            api_maturity: ScientificApiMaturity::ResearchOnly,
            completeness: ScientificCompleteness::Complete,
            availability: ScientificAvailability::NoImplementation,
            catalog_entry: entry.clone(),
        })
        .is_err()
    );
    assert!(
        ScientificMethodIdentity::new(ScientificMethodIdentityInputs {
            catalog_id: catalog_id.to_string(),
            origin: ScientificMethodOrigin::PaperDefined,
            estimand_regime: ScientificEstimandRegime::ConditionalContinuous,
            api_maturity: ScientificApiMaturity::NotApplicable,
            completeness: ScientificCompleteness::NotApplicable,
            availability: ScientificAvailability::NoImplementation,
            catalog_entry: entry,
        })
        .is_ok()
    );
    assert!(
        ScientificMethodIdentity::new(ScientificMethodIdentityInputs {
            catalog_id: catalog_id.to_string(),
            origin: ScientificMethodOrigin::PaperDefined,
            estimand_regime: ScientificEstimandRegime::ConditionalContinuous,
            api_maturity: ScientificApiMaturity::NotApplicable,
            completeness: ScientificCompleteness::NotApplicable,
            availability: ScientificAvailability::NoImplementation,
            catalog_entry: content("pid-rs/wrong-catalog-entry", 111),
        })
        .is_err()
    );
}

#[test]
fn reason_codes_keep_checked_one_part_source_values() {
    assert!(ScientificReasonCode::new("ambiguous_neighbor_shell").is_ok());
    assert!(ScientificReasonCode::new("pid_core.ambiguous_neighbor_shell").is_ok());
    for invalid in ["Pid_core.bad", "pid-core.bad", "pid_core.", ""] {
        assert!(ScientificReasonCode::new(invalid).is_err(), "{invalid}");
    }
}
