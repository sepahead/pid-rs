use pid_core::{
    co_information_triplet, hierarchical_pairwise, hierarchical_triplet, ksg_mi, pid3_isx,
    HierarchicalConfig, KsgConfig, MatRef, NegativeHandling, PairSelection, Pid3Config,
    Standardizer,
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
fn hierarchical_pairwise_allows_mixed_dimensions_only_for_level_one() {
    let mut rng = Rng64::new(0xD1_6E_05);
    let n = 80;
    let mut scalar = Vec::with_capacity(n);
    let mut vector = Vec::with_capacity(n * 2);
    let mut target = Vec::with_capacity(n);
    for _ in 0..n {
        let signal = rng.normal();
        scalar.push(signal + 0.2 * rng.normal());
        vector.push(signal + 0.3 * rng.normal());
        vector.push(rng.normal());
        target.push(signal + 0.1 * rng.normal());
    }
    let scalar = MatRef::new(&scalar, n, 1).unwrap();
    let vector = MatRef::new(&vector, n, 2).unwrap();
    let target = MatRef::new(&target, n, 1).unwrap();

    let level_one = HierarchicalConfig {
        selection: PairSelection::All,
        compute_pid: false,
        ..HierarchicalConfig::default()
    };
    let screened = hierarchical_pairwise(&[scalar, vector], target, &level_one).unwrap();
    assert_eq!(screened.len(), 1);
    assert!(screened[0].pid.is_none());

    let level_two = HierarchicalConfig {
        selection: PairSelection::All,
        compute_pid: true,
        ..HierarchicalConfig::default()
    };
    assert!(matches!(
        hierarchical_pairwise(&[scalar, vector], target, &level_two),
        Err(pid_core::PidError::SourceDimensionMismatch {
            left_cols: 1,
            right_cols: 2,
            ..
        })
    ));
}

#[test]
fn hierarchical_pairwise_rejects_nonfinite_ci_thresholds() {
    let source_a = [0.0, 1.0, 2.0, 3.0];
    let source_b = [0.2, 1.2, 2.2, 3.2];
    let target = [0.1, 0.9, 2.1, 2.9];
    let a = MatRef::new(&source_a, 4, 1).unwrap();
    let b = MatRef::new(&source_b, 4, 1).unwrap();
    let t = MatRef::new(&target, 4, 1).unwrap();

    for threshold in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        let config = HierarchicalConfig {
            selection: PairSelection::CiBelow { threshold },
            compute_pid: false,
            ..HierarchicalConfig::default()
        };
        assert!(matches!(
            hierarchical_pairwise(&[a, b], t, &config),
            Err(pid_core::PidError::InvalidConfig { .. })
        ));
    }
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

/// Regression for the ClampToZero bug: with an all-independent system, raw KSG MI estimates go
/// negative, and the hierarchical CI must STILL match the direct co-information (both paths
/// force `Allow` internally). Before the fix, `hierarchical_pairwise`/`hierarchical_triplet`
/// honoured the caller's default `ClampToZero`, so the two paths diverged exactly here. The
/// negativity guard keeps this test from silently becoming vacuous.
#[test]
fn hierarchical_triplet_ci_matches_direct_in_negative_mi_regime() {
    let mut rng = Rng64::new(0xD1CE);
    let n = 150;

    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    let mut z = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        // Fully independent: the true MI of every term is 0, so unclamped KSG estimates
        // fluctuate around 0 and go negative.
        x.push(rng.normal());
        y.push(rng.normal());
        z.push(rng.normal());
        t.push(rng.normal());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let z = MatRef::new(&z, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    // Guard: at least one raw (Allow) marginal MI estimate must actually be negative on this
    // seed, i.e. we really are in the regime where clamping would fire.
    let allow = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..KsgConfig::default()
    };
    let raw_min = [
        ksg_mi(x, t, &allow).unwrap(),
        ksg_mi(y, t, &allow).unwrap(),
        ksg_mi(z, t, &allow).unwrap(),
    ]
    .into_iter()
    .fold(f64::INFINITY, f64::min);
    assert!(
        raw_min < 0.0,
        "guard: expected a negative raw MI estimate on this seed, got min={raw_min}"
    );

    let cfg = HierarchicalConfig {
        compute_pid: false,
        ..HierarchicalConfig::default()
    };
    let out = hierarchical_triplet(x, y, z, t, &cfg).unwrap();
    let ci_direct = co_information_triplet(x, y, z, t, &cfg.ksg).unwrap();
    assert!(
        (out.ci_triplet - ci_direct).abs() < 1e-12,
        "ci_triplet mismatch in negative-MI regime: hierarchical={} direct={}",
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

    let pid3_cfg = Pid3Config {
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::default()
    };
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
