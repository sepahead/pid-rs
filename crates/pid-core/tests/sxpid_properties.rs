//! Property-based invariants for discrete shared-exclusions PID (`i^sx_∩`).
//!
//! These must hold for *every* discrete system, not just the canonical gates: the PID atoms
//! reconstruct the joint MI, and the down-set of each singleton node reconstructs that source's
//! MI (self-redundancy). We sweep many random systems (varying n, alphabet size, and skew) and
//! assert both identities to floating-point tolerance.

mod common;
use common::Rng64;

use pid_core::{
    discrete_pid2, discrete_pid3, discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n,
    quantized_sxpid2, quantized_sxpid3, quantized_sxpid_n, DiscreteMatRef, MatRef,
};

/// Every discrete PID entry point must reject empty input loudly — an empty joint pmf would
/// otherwise silently yield an all-zero "decomposition" that looks like a valid result.
#[test]
fn discrete_paths_reject_empty_input() {
    let empty_data: &[f64] = &[];
    let e = MatRef::new(empty_data, 0, 1).unwrap();
    let empty_labels: &[usize] = &[];
    let d = DiscreteMatRef::new(empty_labels, 0, 1).unwrap();
    assert!(discrete_sxpid2(d, d, d).is_err());
    assert!(discrete_sxpid3(d, d, d, d).is_err());
    assert!(discrete_sxpid_n(&[d, d], d).is_err());
    assert!(quantized_sxpid2(e, e, e, 2).is_err());
    assert!(quantized_sxpid3(e, e, e, e, 2).is_err());
    assert!(quantized_sxpid_n(&[e, e], e, 2).is_err());
    assert!(discrete_pid2(e, e, e, 2).is_err());
    assert!(discrete_pid3(e, e, e, e, 2).is_err());
}

#[test]
fn exact_and_quantized_paths_validate_shapes_and_configuration() {
    let labels = [0usize, 1];
    let exact = DiscreteMatRef::new(&labels, 2, 1).unwrap();
    let zero_cols = DiscreteMatRef::new(&[], 2, 0).unwrap();
    let longer = DiscreteMatRef::new(&[0, 1, 2], 3, 1).unwrap();
    assert!(discrete_sxpid2(zero_cols, exact, exact).is_err());
    assert!(discrete_sxpid2(longer, exact, exact).is_err());
    assert!(discrete_sxpid_n(&[exact], exact).is_err());

    let values = [0.0, 1.0];
    let quantized = MatRef::new(&values, 2, 1).unwrap();
    let quantized_zero_cols = MatRef::new(&[], 2, 0).unwrap();
    assert!(quantized_sxpid2(quantized_zero_cols, quantized, quantized, 2).is_err());
    assert!(quantized_sxpid2(quantized, quantized, quantized, 1).is_err());
    assert!(quantized_sxpid_n(&[quantized], quantized, 2).is_err());
}

/// Draw `n` integer labels in `0..alphabet`, with a deliberately skewed (non-uniform) law so the
/// probability-weighting is exercised.
fn draw(rng: &mut Rng64, n: usize, alphabet: usize) -> Vec<usize> {
    (0..n)
        .map(|_| {
            // Square the uniform to skew toward small labels.
            let u = rng.next_f64();
            let v = (u * u * alphabet as f64) as usize;
            v.min(alphabet - 1)
        })
        .collect()
}

#[test]
fn sxpid2_identities_hold_for_random_systems() {
    let mut rng = Rng64::new(0xA11CE);
    for trial in 0..60 {
        let n = 60 + (trial * 7) % 200;
        let alpha = 2 + (trial % 3); // 2..=4 distinct values per source
        let s1 = draw(&mut rng, n, alpha);
        let s2 = draw(&mut rng, n, alpha);
        // Target depends on both sources plus noise → all atoms generally nonzero.
        let t: Vec<usize> = (0..n)
            .map(|i| {
                let mix = s1[i] + 2 * s2[i] + (rng.next_u64() as usize % 2);
                mix % (alpha + 1)
            })
            .collect();

        let s1m = DiscreteMatRef::new(&s1, n, 1).unwrap();
        let s2m = DiscreteMatRef::new(&s2, n, 1).unwrap();
        let tm = DiscreteMatRef::new(&t, n, 1).unwrap();
        let r = discrete_sxpid2(s1m, s2m, tm).unwrap();

        let sum = r.unq1.net + r.unq2.net + r.syn.net + r.red.net;
        assert!(
            (sum - r.mi_s1s2_t).abs() < 1e-9,
            "trial {trial}: reconstruction {sum} != I(S1,S2;T) {}",
            r.mi_s1s2_t
        );
        assert!(
            (r.unq1.net + r.red.net - r.mi_s1_t).abs() < 1e-9,
            "trial {trial}: self-redundancy S1"
        );
        assert!(
            (r.unq2.net + r.red.net - r.mi_s2_t).abs() < 1e-9,
            "trial {trial}: self-redundancy S2"
        );
        // net == informative − misinformative, pointwise and averaged.
        for p in &r.pointwise {
            for a in [p.unq1, p.unq2, p.syn, p.red] {
                assert!((a.net - (a.informative - a.misinformative)).abs() < 1e-9);
            }
        }
    }
}

#[test]
fn sxpid3_reconstruction_holds_for_random_systems() {
    let mut rng = Rng64::new(0xB0B);
    for trial in 0..40 {
        let n = 80 + (trial * 11) % 160;
        let alpha = 2 + (trial % 2); // 2..=3
        let s0 = draw(&mut rng, n, alpha);
        let s1 = draw(&mut rng, n, alpha);
        let s2 = draw(&mut rng, n, alpha);
        let t: Vec<usize> = (0..n)
            .map(|i| {
                let mix = s0[i] + s1[i] + s2[i];
                mix % (alpha + 1)
            })
            .collect();

        let s0m = DiscreteMatRef::new(&s0, n, 1).unwrap();
        let s1m = DiscreteMatRef::new(&s1, n, 1).unwrap();
        let s2m = DiscreteMatRef::new(&s2, n, 1).unwrap();
        let tm = DiscreteMatRef::new(&t, n, 1).unwrap();
        let r = discrete_sxpid3(s0m, s1m, s2m, tm).unwrap();

        let sum: f64 = r.atoms.iter().map(|a| a.net).sum();
        assert!(
            (sum - r.mi_s0s1s2_t).abs() < 1e-9,
            "trial {trial}: 3-source reconstruction {sum} != joint MI {}",
            r.mi_s0s1s2_t
        );
        assert_eq!(r.atoms.len(), 18);
        for mask in 1u8..=0b111 {
            let downset_sum: f64 = r
                .antichains
                .iter()
                .zip(&r.atoms)
                .filter(|(antichain, _)| {
                    [mask]
                        .iter()
                        .all(|bb| antichain.iter().any(|aa| aa & bb == *aa))
                })
                .map(|(_, atom)| atom.net)
                .sum();
            assert!(
                (downset_sum - r.subset_mis[usize::from(mask - 1)]).abs() < 1e-9,
                "trial {trial}: subset self-redundancy for mask {mask:#05b}"
            );
        }
    }
}
