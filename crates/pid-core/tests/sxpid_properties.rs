#![cfg(feature = "experimental-pipelines")]

//! Property-based invariants for discrete shared-exclusions PID (`i^sx_∩`).
//!
//! These must hold for *every* discrete system, not just the canonical gates: the PID atoms
//! reconstruct the joint MI, and the down-set of each singleton node reconstructs that source's
//! MI (self-redundancy). We sweep many random systems (varying n, alphabet size, and skew) and
//! assert both identities to floating-point tolerance.

mod common;
use common::Rng64;

use pid_core::experimental::pipelines::{
    exploratory_same_sample_quantized_imin_pid2 as discrete_pid2,
    exploratory_same_sample_quantized_imin_pid3 as discrete_pid3,
    exploratory_same_sample_quantized_sxpid2 as quantized_sxpid2,
    exploratory_same_sample_quantized_sxpid3 as quantized_sxpid3,
    exploratory_same_sample_quantized_sxpid_n as quantized_sxpid_n,
};
use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid2_resource_estimate, discrete_sxpid3,
    discrete_sxpid3_resource_estimate, discrete_sxpid_n, discrete_sxpid_n_resource_estimate,
};
use pid_core::stable::imin::{
    imin_pid2, imin_pid2_resource_estimate, imin_pid3, imin_pid3_resource_estimate,
};
use pid_core::{
    DiscreteMatRef, MatRef, PidError, PidResult, DEFAULT_MAX_BYTES, DEFAULT_MAX_OPERATIONS_HINT,
};

fn assert_resource_limit<T>(
    result: PidResult<T>,
    expected_operation: &'static str,
    expected_resource: &'static str,
    expected_requested: u128,
    expected_limit: u128,
) {
    match result {
        Err(PidError::ResourceLimitExceeded {
            operation,
            resource,
            requested,
            limit,
        }) => assert_eq!(
            (operation, resource, requested, limit),
            (
                expected_operation,
                expected_resource,
                expected_requested,
                expected_limit,
            )
        ),
        Err(other) => panic!("expected typed resource rejection, got {other:?}"),
        Ok(_) => panic!("expected typed resource rejection, got success"),
    }
}

fn assert_invalid_config<T>(
    result: PidResult<T>,
    expected_context: &'static str,
    expected_message: &'static str,
) {
    match result {
        Err(PidError::InvalidConfig { context, message }) => {
            assert_eq!((context, message), (expected_context, expected_message));
        }
        Err(other) => panic!("expected typed invalid configuration, got {other:?}"),
        Ok(_) => panic!("expected typed invalid configuration, got success"),
    }
}

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

#[test]
fn mixed_invalid_same_sample_calls_pin_bin_count_precedence() {
    let empty = MatRef::new(&[], 0, 1).unwrap();
    assert_invalid_config(
        quantized_sxpid2(empty, empty, empty, 1),
        "quantized_sxpid2",
        "num_bins must be >= 2",
    );
    assert_invalid_config(
        discrete_pid2(empty, empty, empty, 1),
        "same_sample_quantized_imin_pid2",
        "num_bins must be >= 2",
    );
}

#[test]
fn resource_estimates_bind_asymmetric_source_and_target_coordinate_totals() {
    const N: usize = 8;
    let source_1_data = [0usize; N];
    let source_2_data = [0usize; N * 2];
    let source_3_data = [0usize; N * 3];
    let target_data = [0usize; N * 4];
    let source_1 = DiscreteMatRef::new(&source_1_data, N, 1).unwrap();
    let source_2 = DiscreteMatRef::new(&source_2_data, N, 2).unwrap();
    let source_3 = DiscreteMatRef::new(&source_3_data, N, 3).unwrap();
    let target = DiscreteMatRef::new(&target_data, N, 4).unwrap();

    // For three sources, 18 lattice nodes and seven nonempty subsets give:
    // event scans 20_736 + compensated Möbius work 2_592 + exact final-averaging work 24_480 +
    // histogram work 7 * N * ceil(log2(N)) * (1 + 2 + 3 + 4) = 1_680.
    assert_eq!(
        discrete_sxpid3_resource_estimate(source_1, source_2, source_3, target, true)
            .unwrap()
            .operations_hint,
        49_488
    );

    // The three-source I_min lattice has 31 antichain sets, hence 168 histogram passes:
    // 168 * N * ceil(log2(N)) * 10 coordinate values + N * 6 source coordinates. Its Möbius
    // inversion deliberately retains the pre-existing compensated reduction.
    assert_eq!(
        imin_pid3_resource_estimate(source_1, source_2, source_3, target)
            .unwrap()
            .operations_hint,
        40_368
    );
}

#[test]
fn same_sample_sxpid_aggregate_gate_matches_direct_first_rejection_boundaries() {
    let check_two_sources = || {
        const N: usize = 17_667;
        const REQUESTED: u128 = 10_000_212_101;
        let labels = vec![0usize; N];
        let values = vec![0.0f64; N];
        let categorical_before = DiscreteMatRef::new(&labels[..N - 1], N - 1, 1).unwrap();
        let categorical = DiscreteMatRef::new(&labels, N, 1).unwrap();
        let numeric = MatRef::new(&values, N, 1).unwrap();
        assert!(
            discrete_sxpid2_resource_estimate(
                categorical_before,
                categorical_before,
                categorical_before,
                true,
            )
            .unwrap()
            .operations_hint
                <= DEFAULT_MAX_OPERATIONS_HINT
        );
        assert_eq!(
            discrete_sxpid2_resource_estimate(categorical, categorical, categorical, true)
                .unwrap()
                .operations_hint,
            REQUESTED
        );
        assert_resource_limit(
            discrete_sxpid2(categorical, categorical, categorical),
            "discrete_sxpid2",
            "operations_hint",
            REQUESTED,
            DEFAULT_MAX_OPERATIONS_HINT,
        );
        assert_resource_limit(
            quantized_sxpid2(numeric, numeric, numeric, 2),
            "quantized_sxpid2",
            "operations_hint",
            REQUESTED,
            DEFAULT_MAX_OPERATIONS_HINT,
        );
    };

    let check_three_sources = || {
        const N: usize = 5_551;
        const REQUESTED: u128 = 10_001_019_556;
        let labels = vec![0usize; N];
        let values = vec![0.0f64; N];
        let categorical_before = DiscreteMatRef::new(&labels[..N - 1], N - 1, 1).unwrap();
        let categorical = DiscreteMatRef::new(&labels, N, 1).unwrap();
        let numeric = MatRef::new(&values, N, 1).unwrap();
        assert!(
            discrete_sxpid3_resource_estimate(
                categorical_before,
                categorical_before,
                categorical_before,
                categorical_before,
                true,
            )
            .unwrap()
            .operations_hint
                <= DEFAULT_MAX_OPERATIONS_HINT
        );
        assert_eq!(
            discrete_sxpid3_resource_estimate(
                categorical,
                categorical,
                categorical,
                categorical,
                true,
            )
            .unwrap()
            .operations_hint,
            REQUESTED
        );
        assert_resource_limit(
            discrete_sxpid3(categorical, categorical, categorical, categorical),
            "discrete_sxpid3",
            "operations_hint",
            REQUESTED,
            DEFAULT_MAX_OPERATIONS_HINT,
        );
        assert_resource_limit(
            quantized_sxpid3(numeric, numeric, numeric, numeric, 2),
            "quantized_sxpid3",
            "operations_hint",
            REQUESTED,
            DEFAULT_MAX_OPERATIONS_HINT,
        );
    };

    let check_four_sources = || {
        const N: usize = 1_118;
        const REQUESTED: u128 = 10_016_409_510;
        let labels = vec![0usize; N];
        let values = vec![0.0f64; N];
        let categorical_before = DiscreteMatRef::new(&labels[..N - 1], N - 1, 1).unwrap();
        let categorical = DiscreteMatRef::new(&labels, N, 1).unwrap();
        let numeric = MatRef::new(&values, N, 1).unwrap();
        assert!(
            discrete_sxpid_n_resource_estimate(&[categorical_before; 4], categorical_before, true,)
                .unwrap()
                .operations_hint
                <= DEFAULT_MAX_OPERATIONS_HINT
        );
        assert_eq!(
            discrete_sxpid_n_resource_estimate(&[categorical; 4], categorical, true)
                .unwrap()
                .operations_hint,
            REQUESTED
        );
        assert_resource_limit(
            discrete_sxpid_n(&[categorical; 4], categorical),
            "discrete_sxpid_n",
            "operations_hint",
            REQUESTED,
            DEFAULT_MAX_OPERATIONS_HINT,
        );
        assert_resource_limit(
            quantized_sxpid_n(&[numeric; 4], numeric, 2),
            "quantized_sxpid_n",
            "operations_hint",
            REQUESTED,
            DEFAULT_MAX_OPERATIONS_HINT,
        );
    };

    check_two_sources();
    check_three_sources();
    check_four_sources();
}

#[cfg(target_pointer_width = "64")]
#[test]
fn same_sample_imin_aggregate_gate_matches_direct_first_rejection_boundaries() {
    let check_two_sources = || {
        const N: usize = 813_441;
        const REQUESTED: u128 = 1_073_742_120;
        let labels = vec![0usize; N];
        let values = vec![0.0f64; N];
        let categorical_before = DiscreteMatRef::new(&labels[..N - 1], N - 1, 1).unwrap();
        let categorical = DiscreteMatRef::new(&labels, N, 1).unwrap();
        let numeric = MatRef::new(&values, N, 1).unwrap();
        assert!(
            imin_pid2_resource_estimate(categorical_before, categorical_before, categorical_before,)
                .unwrap()
                .estimated_bytes <= u128::from(DEFAULT_MAX_BYTES)
        );
        assert_eq!(
            imin_pid2_resource_estimate(categorical, categorical, categorical)
                .unwrap()
                .estimated_bytes,
            REQUESTED
        );
        assert_resource_limit(
            imin_pid2(categorical, categorical, categorical),
            "imin_pid2",
            "bytes",
            REQUESTED,
            u128::from(DEFAULT_MAX_BYTES),
        );
        assert_resource_limit(
            discrete_pid2(numeric, numeric, numeric, 2),
            "same_sample_quantized_imin_pid2",
            "bytes",
            REQUESTED,
            u128::from(DEFAULT_MAX_BYTES),
        );
    };

    let check_three_sources = || {
        const N: usize = 110_924;
        const REQUESTED: u128 = 1_073_745_040;
        let labels = vec![0usize; N];
        let values = vec![0.0f64; N];
        let categorical_before = DiscreteMatRef::new(&labels[..N - 1], N - 1, 1).unwrap();
        let categorical = DiscreteMatRef::new(&labels, N, 1).unwrap();
        let numeric = MatRef::new(&values, N, 1).unwrap();
        assert!(
            imin_pid3_resource_estimate(
                categorical_before,
                categorical_before,
                categorical_before,
                categorical_before,
            )
            .unwrap()
            .estimated_bytes
                <= u128::from(DEFAULT_MAX_BYTES)
        );
        assert_eq!(
            imin_pid3_resource_estimate(categorical, categorical, categorical, categorical,)
                .unwrap()
                .estimated_bytes,
            REQUESTED
        );
        assert_resource_limit(
            imin_pid3(categorical, categorical, categorical, categorical),
            "imin_pid3",
            "bytes",
            REQUESTED,
            u128::from(DEFAULT_MAX_BYTES),
        );
        assert_resource_limit(
            discrete_pid3(numeric, numeric, numeric, numeric, 2),
            "same_sample_quantized_imin_pid3",
            "bytes",
            REQUESTED,
            u128::from(DEFAULT_MAX_BYTES),
        );
    };

    check_two_sources();
    check_three_sources();
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

        let sum = r.unq1.net_nats() + r.unq2.net_nats() + r.syn.net_nats() + r.red.net_nats();
        assert!(
            (sum - r.mi_s1s2_t).abs() < 1e-9,
            "trial {trial}: reconstruction {sum} != I(S1,S2;T) {}",
            r.mi_s1s2_t
        );
        assert!(
            (r.unq1.net_nats() + r.red.net_nats() - r.mi_s1_t).abs() < 1e-9,
            "trial {trial}: self-redundancy S1"
        );
        assert!(
            (r.unq2.net_nats() + r.red.net_nats() - r.mi_s2_t).abs() < 1e-9,
            "trial {trial}: self-redundancy S2"
        );
        // net == informative − misinformative, pointwise and averaged.
        for p in &r.pointwise {
            for a in [p.unq1, p.unq2, p.syn, p.red] {
                assert_eq!(a.net_nats(), a.informative_nats() - a.misinformative_nats());
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

        let sum: f64 = r.atoms.iter().map(|a| a.net_nats()).sum();
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
                .map(|(_, atom)| atom.net_nats())
                .sum();
            assert!(
                (downset_sum - r.subset_mis[usize::from(mask - 1)]).abs() < 1e-9,
                "trial {trial}: subset self-redundancy for mask {mask:#05b}"
            );
        }
    }
}
