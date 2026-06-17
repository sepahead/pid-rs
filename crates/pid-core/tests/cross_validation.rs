//! Cross-validation of the discrete `I_min` PID against an **independent**
//! reference implementation and against the structural ground truth of canonical
//! logic-gate systems.
//!
//! Rather than depend on an external reference implementation that is not CI-reproducible,
//! we re-derive the Williams–Beer `I_min` PID here by a deliberately different route — directly from
//! the empirical joint distribution over `HashMap`s — and confirm `pid_core`'s
//! count-based `discrete_pid2` agrees, on systems whose decomposition is known a
//! priori (XOR is pure synergy, COPY is pure redundancy, etc.). Agreement between
//! two independent implementations *and* with the analytic structure validates the
//! estimator far more than either alone.
//!
//! All quantities are in nats, matching `pid_core`.

use std::collections::HashMap;

use pid_core::{discrete_pid2, MatOwned};

/// A named (s1, s2, t) truth table for a logic-gate system.
type GateSystem<'a> = (&'a str, &'a [(usize, usize, usize)]);

/// Independent Williams–Beer `I_min` PID2 computed directly from the empirical
/// joint of integer-coded variables. Returns `(redundancy, unique_s1, unique_s2,
/// synergy, mi_s1_t, mi_s2_t, mi_s1s2_t)`.
#[allow(clippy::type_complexity)]
fn reference_pid2(s1: &[usize], s2: &[usize], t: &[usize]) -> [f64; 7] {
    let n = s1.len();
    assert!(n > 0 && s2.len() == n && t.len() == n);
    let nf = n as f64;

    // Count tables.
    let mut c_t: HashMap<usize, f64> = HashMap::new();
    let mut c_s1: HashMap<usize, f64> = HashMap::new();
    let mut c_s2: HashMap<usize, f64> = HashMap::new();
    let mut c_s12: HashMap<(usize, usize), f64> = HashMap::new();
    let mut c_s1t: HashMap<(usize, usize), f64> = HashMap::new();
    let mut c_s2t: HashMap<(usize, usize), f64> = HashMap::new();
    let mut c_s12t: HashMap<((usize, usize), usize), f64> = HashMap::new();
    for i in 0..n {
        *c_t.entry(t[i]).or_insert(0.0) += 1.0;
        *c_s1.entry(s1[i]).or_insert(0.0) += 1.0;
        *c_s2.entry(s2[i]).or_insert(0.0) += 1.0;
        *c_s12.entry((s1[i], s2[i])).or_insert(0.0) += 1.0;
        *c_s1t.entry((s1[i], t[i])).or_insert(0.0) += 1.0;
        *c_s2t.entry((s2[i], t[i])).or_insert(0.0) += 1.0;
        *c_s12t.entry(((s1[i], s2[i]), t[i])).or_insert(0.0) += 1.0;
    }

    // MI(X;T) = Σ (c_xt/n) ln( c_xt * n / (c_x * c_t) ), in nats.
    let mi = |c_xt: &HashMap<(usize, usize), f64>,
              c_x: &HashMap<usize, f64>,
              c_t: &HashMap<usize, f64>|
     -> f64 {
        let mut acc = 0.0;
        for (&(x, tt), &cxt) in c_xt {
            let cx = c_x[&x];
            let ct = c_t[&tt];
            acc += (cxt / nf) * (cxt * nf / (cx * ct)).ln();
        }
        acc
    };
    let mi_joint = {
        let mut acc = 0.0;
        for (&(x, tt), &cxt) in &c_s12t {
            let cx = c_s12[&x];
            let ct = c_t[&tt];
            acc += (cxt / nf) * (cxt * nf / (cx * ct)).ln();
        }
        acc
    };

    let mi_s1_t = mi(&c_s1t, &c_s1, &c_t);
    let mi_s2_t = mi(&c_s2t, &c_s2, &c_t);

    // i_spec(S; t) = Σ_s (c_st/c_t) ln( c_st * n / (c_s * c_t) ).
    let i_spec =
        |c_xt: &HashMap<(usize, usize), f64>, c_x: &HashMap<usize, f64>| -> HashMap<usize, f64> {
            let mut out: HashMap<usize, f64> = HashMap::new();
            for (&(x, tt), &cxt) in c_xt {
                let cx = c_x[&x];
                let ct = c_t[&tt];
                *out.entry(tt).or_insert(0.0) += (cxt / ct) * (cxt * nf / (cx * ct)).ln();
            }
            out
        };
    let is1 = i_spec(&c_s1t, &c_s1);
    let is2 = i_spec(&c_s2t, &c_s2);

    // Red = Σ_t p(t) min(i_spec(S1;t), i_spec(S2;t)).
    let mut redundancy = 0.0;
    for (&tt, &ct) in &c_t {
        let a = is1.get(&tt).copied().unwrap_or(0.0);
        let b = is2.get(&tt).copied().unwrap_or(0.0);
        redundancy += (ct / nf) * a.min(b);
    }

    let unique_s1 = mi_s1_t - redundancy;
    let unique_s2 = mi_s2_t - redundancy;
    let synergy = mi_joint - redundancy - unique_s1 - unique_s2;
    [
        redundancy, unique_s1, unique_s2, synergy, mi_s1_t, mi_s2_t, mi_joint,
    ]
}

/// Replicate a (s1, s2, t) truth table `reps` times into column matrices plus the
/// integer vectors, so `pid_core` (quantized) and the reference (raw integers) see
/// the same exact empirical distribution.
fn build_system(
    rows: &[(usize, usize, usize)],
    reps: usize,
) -> (
    MatOwned,
    MatOwned,
    MatOwned,
    Vec<usize>,
    Vec<usize>,
    Vec<usize>,
) {
    let mut s1 = Vec::new();
    let mut s2 = Vec::new();
    let mut t = Vec::new();
    for _ in 0..reps {
        for &(a, b, c) in rows {
            s1.push(a);
            s2.push(b);
            t.push(c);
        }
    }
    let to_mat =
        |v: &[usize]| MatOwned::new(v.iter().map(|&x| x as f64).collect(), v.len(), 1).unwrap();
    let (m1, m2, mt) = (to_mat(&s1), to_mat(&s2), to_mat(&t));
    (m1, m2, mt, s1, s2, t)
}

fn assert_close(a: f64, b: f64, tol: f64, what: &str) {
    assert!(
        (a - b).abs() < tol,
        "{what}: {a} vs {b} (|Δ|={})",
        (a - b).abs()
    );
}

/// On every canonical gate, `pid_core::discrete_pid2` must match the independent
/// reference on all four atoms and the three MI terms.
#[test]
fn discrete_pid2_matches_independent_reference() {
    // (s1, s2, t) truth tables over binary sources.
    let xor = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)];
    let and = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)];
    let or = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)];
    let copy = [(0, 0, 0), (1, 1, 1)]; // s1==s2==t: pure redundancy
    let unique_s1 = [(0, 0, 0), (0, 1, 0), (1, 0, 1), (1, 1, 1)]; // t == s1
    let systems: [GateSystem<'_>; 5] = [
        ("xor", &xor),
        ("and", &and),
        ("or", &or),
        ("copy", &copy),
        ("unique_s1", &unique_s1),
    ];
    for (name, rows) in systems {
        let (m1, m2, mt, s1, s2, t) = build_system(rows, 50);
        let got = discrete_pid2(m1.as_ref(), m2.as_ref(), mt.as_ref(), 2).unwrap();
        let r = reference_pid2(&s1, &s2, &t);
        let tol = 1e-9;
        assert_close(got.redundancy, r[0], tol, &format!("{name} redundancy"));
        assert_close(got.unique_s1, r[1], tol, &format!("{name} unique_s1"));
        assert_close(got.unique_s2, r[2], tol, &format!("{name} unique_s2"));
        assert_close(got.synergy, r[3], tol, &format!("{name} synergy"));
        assert_close(got.mi_s1_t, r[4], tol, &format!("{name} mi_s1_t"));
        assert_close(got.mi_s2_t, r[5], tol, &format!("{name} mi_s2_t"));
        assert_close(got.mi_s1s2_t, r[6], tol, &format!("{name} mi_s1s2_t"));
    }
}

/// The decomposition must also match the *known structure* of each gate — this is
/// the part that would catch a bug shared by both implementations.
#[test]
fn discrete_pid2_recovers_known_gate_structure() {
    let ln2 = std::f64::consts::LN_2;

    // XOR: neither source has marginal info; all information is synergistic.
    let xor = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)];
    let (m1, m2, mt, ..) = build_system(&xor, 64);
    let r = discrete_pid2(m1.as_ref(), m2.as_ref(), mt.as_ref(), 2).unwrap();
    assert_close(r.mi_s1_t, 0.0, 1e-9, "xor mi_s1_t");
    assert_close(r.redundancy, 0.0, 1e-9, "xor redundancy");
    assert_close(r.unique_s1, 0.0, 1e-9, "xor unique_s1");
    assert_close(r.synergy, ln2, 1e-9, "xor synergy"); // 1 bit = ln2 nats

    // COPY (s1==s2==t): purely redundant; 1 bit of redundancy, no unique/synergy.
    let copy = [(0, 0, 0), (1, 1, 1)];
    let (m1, m2, mt, ..) = build_system(&copy, 64);
    let r = discrete_pid2(m1.as_ref(), m2.as_ref(), mt.as_ref(), 2).unwrap();
    assert_close(r.redundancy, ln2, 1e-9, "copy redundancy");
    assert_close(r.unique_s1, 0.0, 1e-9, "copy unique_s1");
    assert_close(r.unique_s2, 0.0, 1e-9, "copy unique_s2");
    assert_close(r.synergy, 0.0, 1e-9, "copy synergy");

    // UNIQUE_S1 (t==s1, s2 carries the same bit here too via the table) — use a
    // table where s2 is independent of t to isolate unique_s1.
    let uniq = [(0, 0, 0), (0, 1, 0), (1, 0, 1), (1, 1, 1)]; // t == s1; s2 independent of t
    let (m1, m2, mt, ..) = build_system(&uniq, 64);
    let r = discrete_pid2(m1.as_ref(), m2.as_ref(), mt.as_ref(), 2).unwrap();
    assert_close(r.mi_s2_t, 0.0, 1e-9, "uniq mi_s2_t");
    assert_close(r.redundancy, 0.0, 1e-9, "uniq redundancy");
    assert_close(r.unique_s1, ln2, 1e-9, "uniq unique_s1"); // s1 fully determines t
    assert_close(r.unique_s2, 0.0, 1e-9, "uniq unique_s2");
    assert_close(r.synergy, 0.0, 1e-9, "uniq synergy");
}

/// PID atoms must sum to the joint MI (the consistency equation) on every system.
#[test]
fn discrete_pid2_atoms_sum_to_joint_mi() {
    let systems: [&[(usize, usize, usize)]; 3] = [
        &[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)], // xor
        &[(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)], // and
        &[(0, 0, 0), (1, 1, 1)],                       // copy
    ];
    for rows in systems {
        let (m1, m2, mt, ..) = build_system(rows, 40);
        let r = discrete_pid2(m1.as_ref(), m2.as_ref(), mt.as_ref(), 2).unwrap();
        let sum = r.redundancy + r.unique_s1 + r.unique_s2 + r.synergy;
        assert_close(sum, r.mi_s1s2_t, 1e-9, "atoms sum to joint MI");
        // I_min atoms are non-negative on empirical distributions (§8.1.6).
        for (atom, v) in [
            ("redundancy", r.redundancy),
            ("unique_s1", r.unique_s1),
            ("unique_s2", r.unique_s2),
            ("synergy", r.synergy),
        ] {
            assert!(v >= -1e-9, "{atom} negative: {v}");
        }
    }
}
