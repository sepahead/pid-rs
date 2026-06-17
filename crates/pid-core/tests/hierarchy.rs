use pid_core::{
    co_information_triplet, hierarchical_pairwise, hierarchical_triplet, pid3_isx,
    HierarchicalConfig, MatRef, PairSelection, Pid3Config, Standardizer,
};

mod common;

use common::Rng64;

#[test]
fn hierarchical_pairwise_screening_returns_all_pairs() {
    let mut rng = Rng64::new(404);
    let n = 240;

    // 3 sources => 3 choose 2 = 3 pairs.
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut s3 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let c = rng.normal();
        s1.push(a);
        s2.push(b);
        s3.push(c);
        t.push(a + b + 0.1 * rng.normal());
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let s3 = MatRef::new(&s3, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let (s1, _) = Standardizer::fit_transform(s1).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2).unwrap();
    let (s3, _) = Standardizer::fit_transform(s3).unwrap();
    let (t, _) = Standardizer::fit_transform(t).unwrap();

    let cfg = HierarchicalConfig {
        compute_pid: false,
        ..HierarchicalConfig::default()
    };
    let out =
        hierarchical_pairwise(&[s1.as_ref(), s2.as_ref(), s3.as_ref()], t.as_ref(), &cfg).unwrap();

    assert_eq!(out.len(), 3);
    assert!(out.iter().all(|p| p.pid.is_none()));
    assert!(out.iter().all(|p| p.ci.is_finite()));
}

#[test]
fn hierarchical_pairwise_topk_selects_exactly_k_pairs() {
    let mut rng = Rng64::new(405);
    let n = 260;

    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut s3 = Vec::with_capacity(n);
    let mut s4 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let c = rng.normal();
        let d = rng.normal();
        s1.push(a);
        s2.push(b);
        s3.push(c);
        s4.push(d);
        // Make two sources matter to ensure some CI spread.
        t.push(a - b + 0.1 * rng.normal());
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let s3 = MatRef::new(&s3, n, 1).unwrap();
    let s4 = MatRef::new(&s4, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let (s1, _) = Standardizer::fit_transform(s1).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2).unwrap();
    let (s3, _) = Standardizer::fit_transform(s3).unwrap();
    let (s4, _) = Standardizer::fit_transform(s4).unwrap();
    let (t, _) = Standardizer::fit_transform(t).unwrap();

    let cfg = HierarchicalConfig {
        selection: PairSelection::TopKMostNegativeCi { k: 2 },
        compute_pid: true,
        ..HierarchicalConfig::default()
    };
    let out = hierarchical_pairwise(
        &[s1.as_ref(), s2.as_ref(), s3.as_ref(), s4.as_ref()],
        t.as_ref(),
        &cfg,
    )
    .unwrap();

    let computed = out.iter().filter(|p| p.pid.is_some()).count();
    assert_eq!(computed, 2);

    // Selected pairs must correspond to the 2 smallest CI values.
    let mut cis: Vec<f64> = out.iter().map(|p| p.ci).collect();
    cis.sort_by(|a, b| a.total_cmp(b));
    let cutoff = cis[1];
    for p in &out {
        if p.pid.is_some() {
            assert!(p.ci <= cutoff + 1e-12);
        }
    }
}

#[test]
fn hierarchical_triplet_ci_matches_direct_computation() {
    let mut rng = Rng64::new(406);
    let n = 220;

    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    let mut z = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let c = rng.normal();
        x.push(a);
        y.push(b);
        z.push(c);
        t.push(a + b + c + 0.1 * rng.normal());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let z = MatRef::new(&z, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let (x, _) = Standardizer::fit_transform(x).unwrap();
    let (y, _) = Standardizer::fit_transform(y).unwrap();
    let (z, _) = Standardizer::fit_transform(z).unwrap();
    let (t, _) = Standardizer::fit_transform(t).unwrap();

    let cfg = HierarchicalConfig {
        compute_pid: false,
        ..HierarchicalConfig::default()
    };

    let out = hierarchical_triplet(x.as_ref(), y.as_ref(), z.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(out.pairwise.len(), 3);
    assert!(out.ci_triplet.is_finite());
    assert!(out.mi_xyz_t.is_finite());
    assert!(out.pid3.is_none());

    let ci_direct =
        co_information_triplet(x.as_ref(), y.as_ref(), z.as_ref(), t.as_ref(), &cfg.ksg).unwrap();
    assert!(
        (out.ci_triplet - ci_direct).abs() < 1e-12,
        "ci_triplet mismatch: hierarchical={} direct={}",
        out.ci_triplet,
        ci_direct
    );
}

#[test]
fn hierarchical_triplet_can_compute_full_pid3() {
    let mut rng = Rng64::new(407);
    let n = 140;

    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    let mut z = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        x.push(base);
        y.push(base + 0.1 * rng.normal());
        z.push(base + 0.1 * rng.normal());
        t.push(base + 0.1 * rng.normal());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let z = MatRef::new(&z, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let (x, _) = Standardizer::fit_transform(x).unwrap();
    let (y, _) = Standardizer::fit_transform(y).unwrap();
    let (z, _) = Standardizer::fit_transform(z).unwrap();
    let (t, _) = Standardizer::fit_transform(t).unwrap();

    let pid3_cfg = Pid3Config::default();
    let cfg = HierarchicalConfig {
        compute_pid: false,
        compute_pid3: true,
        pid3: pid3_cfg.clone(),
        ..HierarchicalConfig::default()
    };

    let out = hierarchical_triplet(x.as_ref(), y.as_ref(), z.as_ref(), t.as_ref(), &cfg).unwrap();
    let pid3_direct = pid3_isx(x.as_ref(), y.as_ref(), z.as_ref(), t.as_ref(), &pid3_cfg).unwrap();

    assert!(out.pid3.is_some());
    let pid3_h = out.pid3.unwrap();
    assert_eq!(pid3_h.atoms.len(), pid3_direct.atoms.len());
    for (a, b) in pid3_h.atoms.iter().zip(pid3_direct.atoms.iter()) {
        assert_eq!(a.antichain, b.antichain);
        assert!((a.value - b.value).abs() < 1e-12);
    }
}
