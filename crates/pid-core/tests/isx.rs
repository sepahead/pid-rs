#![cfg(feature = "experimental-continuous")]

use pid_core::experimental::continuous::raw_scalars::isx_redundancy;
#[cfg(feature = "experimental-heuristics")]
use pid_core::experimental::continuous::raw_scalars::ksg_local_mi_terms;
use pid_core::experimental::continuous::{pid2_isx, IsxConfig, IsxMethod, Pid2Config};
#[cfg(feature = "experimental-heuristics")]
use pid_core::stable::continuous::{KsgConfig, NegativeHandling};
use pid_core::{MatRef, PidError};

mod common;

use common::{csxpid_reference, Rng64};

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

    let red = isx_redundancy(s1, s2, t, &IsxConfig::assume_regular_full_dimensional()).unwrap();
    assert!(red.is_finite());
}

#[test]
fn public_isx_api_cannot_bypass_support_preflight() {
    let s1_data = [0.03, 0.17, 0.31, 0.52, 0.76, 1.01, 1.29, 1.62];
    let s2_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21, 0.07];
    let target_data = [0.12, 0.29, 0.48, 0.71, 0.97, 1.22, 1.51, 1.85];
    let s1 = MatRef::new(&s1_data, 8, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 8, 1).unwrap();
    let target = MatRef::new(&target_data, 8, 1).unwrap();
    assert!(matches!(
        isx_redundancy(s1, s2, target, &IsxConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));

    let tied_data = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let tied = MatRef::new(&tied_data, 8, 1).unwrap();
    assert!(matches!(
        isx_redundancy(
            tied,
            s2,
            target,
            &IsxConfig::assume_regular_full_dimensional()
        ),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. })
    ));
}

#[test]
fn isx_rejects_every_nonzero_or_nonfinite_tie_epsilon() {
    let s1_data = [0.0, 0.2, 0.5, 0.9];
    let s2_data = [0.1, 0.3, 0.6, 1.0];
    let target_data = [0.05, 0.25, 0.55, 0.95];
    let s1 = MatRef::new(&s1_data, 4, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 4, 1).unwrap();
    let target = MatRef::new(&target_data, 4, 1).unwrap();

    for tie_epsilon in [-1.0, 1.0e-12, f64::NAN, f64::INFINITY] {
        let config = IsxConfig {
            tie_epsilon,
            ..IsxConfig::default()
        };
        assert!(isx_redundancy(s1, s2, target, &config).is_err());
    }
}

#[test]
fn isx_rejects_unequal_ambient_source_dimensions() {
    let scalar_data = [0.0, 0.2, 0.5, 0.9];
    let vector_data = [0.0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.9, 1.0];
    let target_data = [0.05, 0.25, 0.55, 0.95];
    let scalar = MatRef::new(&scalar_data, 4, 1).unwrap();
    let vector = MatRef::new(&vector_data, 4, 2).unwrap();
    let target = MatRef::new(&target_data, 4, 1).unwrap();

    let error = isx_redundancy(scalar, vector, target, &IsxConfig::default()).unwrap_err();

    assert!(matches!(
        error,
        PidError::SourceDimensionMismatch {
            context: "isx_redundancy",
            left_cols: 1,
            right_cols: 2,
        }
    ));
}

#[test]
fn every_continuous_isx_method_rejects_an_ambiguous_positive_shell() {
    let source_data = [0.0, 0.5, 1.0, 0.3, 3.0];
    let target_data = [0.0, 0.4, 0.2, 1.0, 3.0];
    let source = MatRef::new(&source_data, 5, 1).unwrap();
    let target = MatRef::new(&target_data, 5, 1).unwrap();

    #[cfg(not(feature = "experimental-heuristics"))]
    let methods = [IsxMethod::EhrlichKsg];
    #[cfg(feature = "experimental-heuristics")]
    let methods = [
        IsxMethod::EhrlichKsg,
        IsxMethod::HeuristicSketch,
        IsxMethod::LocalMinKsg,
        IsxMethod::DisjunctionFromLocalMi,
    ];
    for method in methods {
        let config = IsxConfig {
            k: 2,
            method,
            ..IsxConfig::assume_regular_full_dimensional()
        };
        assert!(matches!(
            isx_redundancy(source, source, target, &config),
            Err(PidError::AmbiguousKthNeighborShell { .. })
        ));
    }
}

#[cfg(feature = "experimental-heuristics")]
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
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    assert!(red.is_finite());
}

#[cfg(feature = "experimental-heuristics")]
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
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    assert!(red.is_finite());
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn local_min_heuristic_matches_its_named_formula_and_is_source_symmetric() {
    let mut rng = Rng64::new(2030);
    let n = 160;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        s1.push(a + 0.05 * rng.normal());
        s2.push(b + 0.05 * rng.normal());
        t.push(a + b + 0.1 * rng.normal());
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    let cfg = IsxConfig {
        method: IsxMethod::LocalMinKsg,
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let ksg_cfg = KsgConfig::default()
        .with_k(cfg.k)
        .with_metric(cfg.metric)
        .with_tie_epsilon(cfg.tie_epsilon)
        .with_negative_handling(NegativeHandling::Allow)
        .with_support_contract(cfg.support_contract);
    let local_s1 = ksg_local_mi_terms(s1, t, &ksg_cfg).unwrap();
    let local_s2 = ksg_local_mi_terms(s2, t, &ksg_cfg).unwrap();
    let expected = local_s1
        .iter()
        .zip(&local_s2)
        .map(|(&left, &right)| left.min(right))
        .sum::<f64>()
        / n as f64;
    let observed = isx_redundancy(s1, s2, t, &cfg).unwrap();
    let swapped = isx_redundancy(s2, s1, t, &cfg).unwrap();

    assert!((observed - expected).abs() < 1e-12);
    assert!((observed - swapped).abs() < 1e-12);
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn every_heuristic_scalar_baseline_is_source_symmetric_on_a_regular_fixture() {
    let mut rng = Rng64::new(2031);
    let n = 250;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        s1.push(base + 0.01 * rng.normal());
        s2.push(base + 0.01 * rng.normal());
        t.push(base);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    for method in [
        IsxMethod::HeuristicSketch,
        IsxMethod::LocalMinKsg,
        IsxMethod::DisjunctionFromLocalMi,
    ] {
        let cfg = IsxConfig {
            method,
            ..IsxConfig::assume_regular_full_dimensional()
        };
        let observed = isx_redundancy(s1, s2, t, &cfg).unwrap();
        let swapped = isx_redundancy(s2, s1, t, &cfg).unwrap();
        assert!(
            (observed - swapped).abs() < 1e-12,
            "{method:?}: observed={observed} swapped={swapped}"
        );
    }
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

    let cfg = Pid2Config::assume_regular_full_dimensional();
    let out = pid2_isx(s1, s2, t, &cfg).unwrap();
    assert!(out.redundancy.is_finite());
    assert!(out.unique_s1.is_finite());
    assert!(out.unique_s2.is_finite());
    assert!(out.synergy.is_finite());
}

#[test]
fn ehrlich_ksg_matches_pinned_csxpid_on_committed_fixture() {
    // Generated by scripts/generate-csxpid-reference.py from the authors' public csxpid
    // implementation. The JSON records the upstream commit, exact scientific Python
    // environment, SciPy kd-tree backend, complete input rows, bit-to-nat conversion, and output
    // hash. It is therefore an external cross-check rather than a self-generated regression pin.
    let reference = csxpid_reference();
    assert_eq!(
        reference["provenance"]["upstream"]["commit"].as_str(),
        Some("7bb984611a422cf7944ece68993fe3a27e2eadec")
    );

    let case = &reference["cases"]["bivariate"];
    let rows = case["rows"].as_array().unwrap();
    let n = rows.len();
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for row in rows {
        let row = row.as_array().unwrap();
        assert_eq!(row.len(), 3);
        s1.push(row[0].as_f64().unwrap());
        s2.push(row[1].as_f64().unwrap());
        t.push(row[2].as_f64().unwrap());
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        k: 3,
        method: IsxMethod::EhrlichKsg,
        ..IsxConfig::assume_regular_full_dimensional()
    };

    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    let expected = case["redundancy_bits"].as_f64().unwrap() * std::f64::consts::LN_2;
    let stored_nats = case["redundancy_nats"].as_f64().unwrap();
    assert!(
        (stored_nats - expected).abs() < 1e-15,
        "invalid bit-to-nat conversion in pinned csxpid fixture: bits*ln(2)={expected:.15e} stored={stored_nats:.15e}"
    );

    assert!(red.is_finite());
    assert!(
        (red - expected).abs() < 1e-12,
        "I^sx mismatch against pinned csxpid: estimated={red:.15e} expected={expected:.15e}"
    );
}
