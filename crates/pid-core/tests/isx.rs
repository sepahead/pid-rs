use pid_core::{isx_redundancy, pid2_isx, IsxConfig, IsxMethod, KsgConfig, MatRef, Pid2Config};

mod common;

use common::Rng64;

#[test]
fn exp0_isx_redundancy_smoke() {
    let mut rng = Rng64::new(2026);
    let n = 200;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let red = isx_redundancy(s1, s2, t, &IsxConfig::default()).unwrap();
    assert!(red.is_finite());
}

#[test]
fn exp0_isx_redundancy_heuristic_sketch_smoke() {
    let mut rng = Rng64::new(2028);
    let n = 200;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        method: IsxMethod::HeuristicSketch,
        ..IsxConfig::default()
    };
    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    assert!(red.is_finite());
}

#[test]
fn exp0_isx_redundancy_disjunction_smoke() {
    let mut rng = Rng64::new(2029);
    let n = 250;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        let noise1 = 0.01 * rng.normal();
        let noise2 = 0.01 * rng.normal();
        t.push(base);
        s1.push(base + noise1);
        s2.push(base + noise2);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        method: IsxMethod::DisjunctionFromLocalMi,
        ..IsxConfig::default()
    };
    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    assert!(red.is_finite());
}

#[test]
fn exp0_pid2_isx_smoke() {
    let mut rng = Rng64::new(2027);
    let n = 220;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = Pid2Config {
        ksg: KsgConfig::default(),
        isx: IsxConfig::default(),
    };
    let out = pid2_isx(s1, s2, t, &cfg).unwrap();
    assert!(out.redundancy.is_finite());
    assert!(out.unique_s1.is_finite());
    assert!(out.unique_s2.is_finite());
    assert!(out.synergy.is_finite());
}

#[test]
fn ehrlich_ksg_matches_reference_implementation_on_fixed_data() {
    // Cross-check against the authors' reference implementation:
    // gitlab.gwdg.de/wibral/continuouspidestimator (csxpid), as described in
    // Ehrlich et al. (2024), arXiv:2311.06373v3, Appendix H (Algorithms 3–6).
    //
    // The expected value was produced by running csxpid with k=3 (L∞ metric),
    // on the exact same fixed dataset and converting from bits to nats.

    let n = 80usize;
    let k = 3usize;

    let mut rng = Rng64::new(987_654_321);

    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.next_f64();
        let u2 = rng.next_f64();
        let u3 = rng.next_f64();
        s1.push(base);
        s2.push(base + 0.5 * u2);
        t.push(base + 0.25 * u3);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        k,
        method: IsxMethod::EhrlichKsg,
        ..IsxConfig::default()
    };

    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    let expected = 1.030_144_904_550_196_5_f64;

    assert!(red.is_finite());
    assert!(
        (red - expected).abs() < 1e-10,
        "I^sx mismatch: estimated={red:.15e} expected={expected:.15e}"
    );
}
