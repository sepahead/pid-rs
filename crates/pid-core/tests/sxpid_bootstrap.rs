#![cfg(feature = "experimental-pipelines")]

//! Dependence-aware raw resampling-percentile diagnostics for discrete SxPID atoms.

use pid_core::experimental::pipelines::{
    bootstrap_quantized_sxpid2, exploratory_same_sample_quantized_sxpid2 as quantized_sxpid2,
    BlockLengthSelection, BlockResamplingAlgorithmRevision, BootstrapConfig,
    ResamplingValidityDeclaration, RowResampleScheme, RowResampleStatus,
    SxBootstrapEvidentialScope, SxBootstrapSummaryComponent, SxBootstrapSummaryScope,
    SxPid2BootstrapSummaryStatus,
};
use pid_core::MatRef;

fn and_gate(reps: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>, usize) {
    let rows = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)];
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..reps {
        for &(a, b, c) in &rows {
            s1.push(a as f64);
            s2.push(b as f64);
            t.push(c as f64);
        }
    }
    (s1.clone(), s2.clone(), t.clone(), 4 * reps)
}

#[test]
fn bootstrap_sxpid2_point_estimate_and_raw_percentiles() {
    let (s1, s2, t, n) = and_gate(40); // n = 160
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = BootstrapConfig::new(
        200,
        1, // i.i.d. rows
        7,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let boot = bootstrap_quantized_sxpid2(s1, s2, t, 2, &cfg).unwrap();

    assert_eq!(boot.num_bins, 2);
    assert_eq!(boot.alpha, cfg.alpha);
    assert_eq!(boot.n_boot, cfg.n_boot);
    assert_eq!(boot.block_size, cfg.block_size);
    assert_eq!(boot.effective_resample_len, n);
    assert_eq!(
        boot.scheme,
        RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 }
    );
    assert_eq!(boot.provenance.validity, cfg.validity);
    assert_eq!(boot.provenance.original_row_count, n);
    assert_eq!(boot.provenance.seed, cfg.seed);
    assert_eq!(boot.provenance.block_size, cfg.block_size);
    assert_eq!(boot.provenance.requested_replicates, cfg.n_boot);
    assert_eq!(
        boot.provenance.algorithm_revision,
        BlockResamplingAlgorithmRevision::V2SeparatedPerturbationStreams
    );
    assert_eq!(boot.replicates.len(), cfg.n_boot);
    assert!(boot
        .replicates
        .iter()
        .all(|replicate| matches!(&replicate.status, RowResampleStatus::Complete { .. })));
    for replicate in &boot.replicates {
        let RowResampleStatus::Complete { statistics } = &replicate.status else {
            unreachable!("all outcomes were checked complete above");
        };
        assert_eq!(statistics.len(), 4);
    }

    let summaries = match &boot.summary_status {
        SxPid2BootstrapSummaryStatus::Complete { summaries } => summaries,
        SxPid2BootstrapSummaryStatus::UnavailableDueToFailedReplicate => {
            panic!("balanced discrete fixture should produce complete summaries")
        }
        _ => panic!("unexpected future summary status"),
    };
    let redundancy = &summaries.redundancy;
    let unique_s1 = &summaries.unique_s1;
    let unique_s2 = &summaries.unique_s2;
    let synergy = &summaries.synergy;

    // Point estimate equals the direct estimator exactly.
    let direct = quantized_sxpid2(s1, s2, t, 2)
        .unwrap()
        .into_categorical_result();
    assert!((redundancy.summary.point_estimate - direct.red.net_nats()).abs() < 1e-12);
    assert!((synergy.summary.point_estimate - direct.syn.net_nats()).abs() < 1e-12);

    // Discrete data ⇒ every resample is valid (no NaN/instability from duplicates).
    for atom in [redundancy, unique_s1, unique_s2, synergy] {
        let interpretation = atom.interpretation();
        assert_eq!(interpretation.contract_revision(), 1);
        assert_eq!(
            interpretation.summary_scope(),
            SxBootstrapSummaryScope::OriginalPointAndMovingBlockResamplingSummary
        );
        assert_eq!(
            interpretation.summary_scope().as_str(),
            "original_point_and_moving_block_resampling_summary"
        );
        assert_eq!(
            interpretation.summary_component(),
            SxBootstrapSummaryComponent::SignedNetNats
        );
        assert_eq!(
            interpretation.summary_component().as_str(),
            "signed_net_nats"
        );
        assert_eq!(
            interpretation.evidential_scope(),
            SxBootstrapEvidentialScope::DescriptiveResamplingVariabilityNoCoverageGuarantee
        );
        assert_eq!(
            interpretation.evidential_scope().as_str(),
            "descriptive_resampling_variability_no_coverage_guarantee"
        );
        assert_eq!(
            interpretation
                .estimand_interpretation()
                .aggregation_scope()
                .as_str(),
            "empirical_pmf_average"
        );
        assert_eq!(interpretation.guard_origin().as_str(), "project_defined");
        let s = &atom.summary;
        assert_eq!(
            s.n_valid, cfg.n_boot,
            "all discrete resamples should be valid"
        );
        assert!(s.resample_standard_deviation.is_finite() && s.resample_standard_deviation >= 0.0);
        assert!(
            s.percentile_lower <= s.percentile_upper,
            "raw percentiles must be ordered"
        );
        assert!(
            s.percentile_lower <= s.resample_mean + 1e-12
                && s.resample_mean <= s.percentile_upper + 1e-12
        );
    }
    // A balanced gate resampled with replacement has nonzero spread in the redundancy atom.
    assert!(redundancy.summary.resample_standard_deviation > 0.0);
}
