use pid_core::{
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
