use pid_core::{
    average_degree_of_redundancy, average_degree_of_vulnerability,
    co_information_pairwise_discrete, o_information_discrete, red_degree_discrete,
    vul_degree_discrete, PidError,
};

fn ln2() -> f64 {
    2.0_f64.ln()
}

#[test]
fn red_vul_degrees_independent_bits() {
    // X,Y independent uniform bits (exactly represented by enumerating all 4 states once).
    let x = [0_u32, 0, 1, 1];
    let y = [0_u32, 1, 0, 1];

    let red = red_degree_discrete(&[&x, &y]).unwrap();
    let vul = vul_degree_discrete(&[&x, &y]).unwrap();

    assert!((red - 1.0).abs() < 1e-12, "Red° expected 1, got {red}");
    assert!((vul - 1.0).abs() < 1e-12, "Vul° expected 1, got {vul}");
}

#[test]
fn red_vul_degrees_perfect_redundancy() {
    // Y = X (perfect redundancy).
    let x = [0_u32, 0, 1, 1];
    let y = [0_u32, 0, 1, 1];

    let red = red_degree_discrete(&[&x, &y]).unwrap();
    let vul = vul_degree_discrete(&[&x, &y]).unwrap();

    assert!((red - 2.0).abs() < 1e-12, "Red° expected 2, got {red}");
    assert!(vul.abs() < 1e-12, "Vul° expected 0, got {vul}");
}

#[test]
fn red_vul_degrees_xor_triplet() {
    // X,Y independent bits; Z = XOR(X,Y). This is a classic synergy structure.
    let x = [0_u32, 0, 1, 1];
    let y = [0_u32, 1, 0, 1];
    let z = [0_u32, 1, 1, 0];

    let red = red_degree_discrete(&[&x, &y, &z]).unwrap();
    let vul = vul_degree_discrete(&[&x, &y, &z]).unwrap();

    assert!((red - 1.5).abs() < 1e-12, "Red° expected 1.5, got {red}");
    assert!(vul.abs() < 1e-12, "Vul° expected 0, got {vul}");
}

#[test]
fn o_information_signs_match_intuition() {
    // Ω>0 for redundant, Ω<0 for XOR-like.
    let x = [0_u32, 0, 1, 1];
    let y_ind = [0_u32, 1, 0, 1];
    let y_red = [0_u32, 0, 1, 1];
    let z_xor = [0_u32, 1, 1, 0];

    // Redundant triplet: X=Y=Z
    let omega_red = o_information_discrete(&[&x, &y_red, &y_red]).unwrap();
    assert!(
        (omega_red - ln2()).abs() < 1e-12,
        "Ω redundant expected ln2, got {omega_red}"
    );

    // XOR triplet: Ω = -ln 2
    let omega_xor = o_information_discrete(&[&x, &y_ind, &z_xor]).unwrap();
    assert!(
        (omega_xor + ln2()).abs() < 1e-12,
        "Ω XOR expected -ln2, got {omega_xor}"
    );
}

#[test]
fn pairwise_co_information_discrete_matches_xor() {
    // For XOR: I(X;Z)=0, I(Y;Z)=0, I(X,Y;Z)=H(Z)=ln2 => CI = -ln2.
    let x = [0_u32, 0, 1, 1];
    let y = [0_u32, 1, 0, 1];
    let z = [0_u32, 1, 1, 0];

    let ci = co_information_pairwise_discrete(&x, &y, &z).unwrap();
    assert!((ci + ln2()).abs() < 1e-12, "CI XOR expected -ln2, got {ci}");
}

#[test]
fn degrees_error_on_zero_joint_entropy() {
    // All-constant: H_joint=0 => degrees undefined.
    let x = [0_u32, 0, 0, 0];
    let y = [1_u32, 1, 1, 1];

    let err = red_degree_discrete(&[&x, &y]).unwrap_err();
    assert!(
        matches!(err, PidError::InvalidConfig { .. }),
        "expected InvalidConfig, got {err:?}"
    );

    let err = vul_degree_discrete(&[&x, &y]).unwrap_err();
    assert!(
        matches!(err, PidError::InvalidConfig { .. }),
        "expected InvalidConfig, got {err:?}"
    );
}

#[test]
fn average_degrees_avoid_representable_intermediate_overflow() {
    assert_eq!(
        average_degree_of_redundancy(&[f64::MAX, f64::MAX], f64::MAX),
        2.0
    );
    assert_eq!(average_degree_of_vulnerability(f64::MAX, &[0.0, 0.0]), 2.0);
    assert_eq!(
        average_degree_of_redundancy(&[f64::MAX, f64::MAX, -f64::MAX, -f64::MAX], 1.0),
        0.0
    );
    assert_eq!(
        average_degree_of_vulnerability(1.0, &[-f64::MAX, -f64::MAX, f64::MAX, f64::MAX]),
        4.0
    );
}

#[test]
fn average_vulnerability_retains_each_next_down_conditional_difference() {
    let next_down = f64::from_bits(1.0_f64.to_bits() - 1);
    let leave_one_out = [next_down; 3];

    let vulnerability = average_degree_of_vulnerability(1.0, &leave_one_out);

    assert_eq!(vulnerability, 3.0 * (1.0 - next_down));
}

#[test]
fn exact_independent_cartesian_invariants_do_not_accumulate_state_count_drift() {
    let cardinality = 32u32;
    let n = cardinality as usize * cardinality as usize * cardinality as usize;
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    let mut z = Vec::with_capacity(n);
    for x_state in 0..cardinality {
        for y_state in 0..cardinality {
            for z_state in 0..cardinality {
                x.push(x_state);
                y.push(y_state);
                z.push(z_state);
            }
        }
    }

    let ci = co_information_pairwise_discrete(&x, &y, &z).unwrap();
    let omega = o_information_discrete(&[&x, &y, &z]).unwrap();
    let vulnerability = vul_degree_discrete(&[&x, &y, &z]).unwrap();
    assert!(ci.abs() < 1e-13, "CI={ci}");
    assert!(omega.abs() < 1e-13, "omega={omega}");
    assert!(
        (vulnerability - 1.0).abs() < 1e-13,
        "vulnerability={vulnerability}"
    );
}

#[test]
fn average_degrees_reject_empty_or_nonfinite_inputs() {
    assert!(average_degree_of_redundancy(&[], 1.0).is_nan());
    assert!(average_degree_of_redundancy(&[f64::NAN], 1.0).is_nan());
    assert!(average_degree_of_vulnerability(1.0, &[]).is_nan());
    assert!(average_degree_of_vulnerability(f64::INFINITY, &[0.0]).is_nan());
}

fn next_random(state: &mut u64) -> u64 {
    *state = state
        .wrapping_mul(6_364_136_223_846_793_005)
        .wrapping_add(1_442_695_040_888_963_407);
    *state
}

#[test]
fn discrete_red_and_vulnerability_degrees_respect_shannon_bounds_on_skewed_laws() {
    // Subadditivity and monotonicity give 1 <= ΣH(X_i)/H(X_all) <= m. The dual-total-
    // correlation inequality gives 0 <= ΣH(X_i|X_-i)/H(X_all) <= 1.
    const TOLERANCE: f64 = 2.0e-12;
    for seed in 1..=200_u64 {
        let mut state = seed ^ 0xd1ce_ba5e_1234_5678;
        let n_vars = 2 + seed as usize % 4;
        let n = 40 + (next_random(&mut state) as usize % 81);
        let mut variables: Vec<Vec<u32>> = (0..n_vars).map(|_| Vec::with_capacity(n)).collect();
        for _ in 0..n {
            let latent = match (next_random(&mut state) >> 32) % 10 {
                0..=6 => 0_u32,
                7..=8 => 1,
                _ => 2,
            };
            for (index, variable) in variables.iter_mut().enumerate() {
                let draw = (next_random(&mut state) >> 32) % 10;
                let value = if draw < 7 {
                    (latent + index as u32) % 3
                } else {
                    (next_random(&mut state) >> 32) as u32 % 3
                };
                variable.push(value);
            }
        }
        // Guarantee positive joint entropy without weakening the arbitrary skew/correlation in the
        // rest of the empirical law.
        for (index, variable) in variables.iter_mut().enumerate() {
            variable[0] = 0;
            variable[1] = 1 + (index as u32 & 1);
        }
        let refs: Vec<&[u32]> = variables.iter().map(Vec::as_slice).collect();

        let redundancy = red_degree_discrete(&refs).unwrap();
        let vulnerability = vul_degree_discrete(&refs).unwrap();

        assert!(
            redundancy.is_finite()
                && (1.0 - TOLERANCE..=n_vars as f64 + TOLERANCE).contains(&redundancy),
            "seed={seed} m={n_vars} Red°={redundancy}"
        );
        assert!(
            vulnerability.is_finite() && (-TOLERANCE..=1.0 + TOLERANCE).contains(&vulnerability),
            "seed={seed} m={n_vars} Vul°={vulnerability}"
        );
    }
}
