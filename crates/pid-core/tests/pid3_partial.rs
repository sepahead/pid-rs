use pid_core::{
    pid3_isx, pid3_isx_partial, pid3_isx_partial_report, Antichain3, MatRef, Metric, Pid3Config,
    Pid3PartialAtom, Pid3Provenance, PidError, SupportContract,
};

mod common;

fn antichain(sets: &[u8]) -> Antichain3 {
    Antichain3::try_from_sets(sets).unwrap()
}

fn trivariate_fixture() -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
    let reference = common::csxpid_reference();
    let rows = reference["cases"]["trivariate"]["rows"].as_array().unwrap();
    let mut s0 = Vec::with_capacity(rows.len());
    let mut s1 = Vec::with_capacity(rows.len());
    let mut s2 = Vec::with_capacity(rows.len());
    let mut target = Vec::with_capacity(rows.len());
    for row in rows {
        let row = row.as_array().unwrap();
        s0.push(row[0].as_f64().unwrap());
        s1.push(row[1].as_f64().unwrap());
        s2.push(row[2].as_f64().unwrap());
        target.push(row[3].as_f64().unwrap());
    }
    (s0, s1, s2, target)
}

fn assert_unavailable_dependencies(atom: &Pid3PartialAtom, expected: &[Antichain3]) {
    assert_eq!(
        atom.unavailable_redundancies, expected,
        "wrong unavailable dependencies for {:?}",
        atom.antichain
    );
}

#[test]
fn partial_pid3_reports_exact_dimension_and_mobius_availability() {
    let (s0, s1, s2, target) = trivariate_fixture();
    let n = s0.len();
    let s0 = MatRef::new(&s0, n, 1).unwrap();
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let target = MatRef::new(&target, n, 1).unwrap();

    let config = Pid3Config::assume_absolutely_continuous();
    let partial = pid3_isx_partial(s0, s1, s2, target, &config).unwrap();
    assert_eq!(partial.n_samples, n);
    assert_eq!(partial.k, 3);
    assert_eq!(partial.metric, Metric::Chebyshev);
    assert_eq!(
        partial.support_contract,
        SupportContract::AssumeAbsolutelyContinuous
    );
    assert_eq!(partial.source_ambient_dimensions, [1, 1, 1]);
    assert_eq!(partial.target_ambient_dimension, 1);
    assert!(partial.experimental);
    assert_eq!(
        partial.warnings,
        [
            "the support contract is caller-declared; sample checks can identify incompatible observations but cannot determine their cause or verify population support",
            "equal ambient branch dimensions do not establish equal intrinsic dimensions, compatible reference measures, or regular leading-order intersections",
            "relative source units and preprocessing are part of the shared-exclusions estimand and must be recorded alongside every reported result",
            "unavailable coordinates are not imputed; available atoms do not form a complete 18-atom decomposition",
        ]
    );

    let provenance = Pid3Provenance::new(
        "source 1 standardized",
        "source 2 standardized",
        "source 3 standardized",
        "target unchanged",
        "continuous observation model; no post-hoc jitter",
    )
    .unwrap();
    let report = pid3_isx_partial_report(s0, s1, s2, target, &config, &provenance).unwrap();
    assert_eq!(
        report.provenance.source1_preprocessing_description(),
        "source 1 standardized"
    );
    assert_eq!(report.result.redundancies.len(), 18);

    let mixed_redundancies = [
        antichain(&[0b001, 0b110]),
        antichain(&[0b010, 0b101]),
        antichain(&[0b011, 0b100]),
    ];
    let unavailable_redundancies = partial
        .redundancies
        .iter()
        .filter(|redundancy| redundancy.value.is_none())
        .map(|redundancy| redundancy.antichain)
        .collect::<Vec<_>>();
    assert_eq!(unavailable_redundancies, mixed_redundancies);
    assert_eq!(
        partial
            .redundancy(mixed_redundancies[0])
            .unwrap()
            .branch_dimensions,
        [1, 2]
    );
    assert_eq!(
        partial
            .redundancy(mixed_redundancies[1])
            .unwrap()
            .branch_dimensions,
        [1, 2]
    );
    assert_eq!(
        partial
            .redundancy(mixed_redundancies[2])
            .unwrap()
            .branch_dimensions,
        [2, 1]
    );
    assert_eq!(
        partial
            .redundancies
            .iter()
            .filter(|redundancy| redundancy.value.is_some())
            .count(),
        15
    );

    let unavailable_atoms = [
        antichain(&[0b001]),
        antichain(&[0b010]),
        antichain(&[0b100]),
        antichain(&[0b001, 0b110]),
        antichain(&[0b010, 0b101]),
        antichain(&[0b011, 0b100]),
        antichain(&[0b011, 0b101]),
        antichain(&[0b011, 0b110]),
        antichain(&[0b101, 0b110]),
        antichain(&[0b011, 0b101, 0b110]),
    ];
    assert_eq!(
        partial
            .atoms
            .iter()
            .filter(|atom| atom.value.is_none())
            .map(|atom| atom.antichain)
            .collect::<Vec<_>>(),
        unavailable_atoms
    );
    assert_eq!(
        partial
            .atoms
            .iter()
            .filter(|atom| atom.value.is_some())
            .count(),
        8
    );

    let r0_12 = antichain(&[0b001, 0b110]);
    let r1_02 = antichain(&[0b010, 0b101]);
    let r01_2 = antichain(&[0b011, 0b100]);
    let expected_dependencies = [
        (antichain(&[0b001]), vec![r0_12]),
        (antichain(&[0b010]), vec![r1_02]),
        (antichain(&[0b100]), vec![r01_2]),
        (r0_12, vec![r0_12]),
        (r1_02, vec![r1_02]),
        (r01_2, vec![r01_2]),
        (antichain(&[0b011, 0b101]), vec![r0_12]),
        (antichain(&[0b011, 0b110]), vec![r1_02]),
        (antichain(&[0b101, 0b110]), vec![r01_2]),
        (antichain(&[0b011, 0b101, 0b110]), vec![r0_12, r1_02, r01_2]),
    ];
    for (atom, dependencies) in expected_dependencies {
        assert_unavailable_dependencies(partial.atom(atom).unwrap(), &dependencies);
    }

    let mut full_config = config;
    full_config.experimental_allow_mixed_dimension_lattice = true;
    let full = pid3_isx(s0, s1, s2, target, &full_config).unwrap();
    for partial_atom in partial.atoms.iter().filter(|atom| atom.value.is_some()) {
        let partial_value = partial_atom.value.unwrap();
        let full_value = full.atom(partial_atom.antichain).unwrap();
        assert!(
            (partial_value - full_value).abs() < 1.0e-12,
            "available atom mismatch for {:?}: partial={partial_value:.15e}, full={full_value:.15e}",
            partial_atom.antichain
        );
    }
}

#[test]
fn partial_pid3_fails_closed_without_a_support_contract() {
    let data = [0.01, 0.13, 0.29, 0.47, 0.71, 1.03, 1.41, 1.89];
    let input = MatRef::new(&data, data.len(), 1).unwrap();

    let error = pid3_isx_partial(input, input, input, input, &Pid3Config::default()).unwrap_err();

    assert!(error
        .to_string()
        .contains("support contract is unspecified"));
}

#[test]
fn partial_pid3_checks_observed_support_for_every_input() {
    let unique = [0.01, 0.13, 0.29, 0.47, 0.71, 1.03, 1.41, 1.89];
    let tied = [0.01, 0.13, 0.29, 0.47, 0.71, 1.03, 1.41, 1.41];
    let unique = MatRef::new(&unique, unique.len(), 1).unwrap();
    let tied = MatRef::new(&tied, tied.len(), 1).unwrap();
    let config = Pid3Config::assume_absolutely_continuous();

    for expected_input_index in 0..4 {
        let mut inputs = [unique; 4];
        inputs[expected_input_index] = tied;
        let error =
            pid3_isx_partial(inputs[0], inputs[1], inputs[2], inputs[3], &config).unwrap_err();
        assert!(matches!(
            error,
            PidError::ObservedContinuousSampleIncompatibility { input_index, .. }
                if input_index == expected_input_index
        ));
    }
}
