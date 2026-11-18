use pid_core::stable::preprocessing::{ConstantColumnPolicy, Standardizer};
use pid_core::MatRef;

#[test]
fn adjacent_training_values_keep_their_midpoint_on_held_out_rows() {
    let high = 2_f64.powi(53);
    for sign in [1.0, -1.0] {
        let training = [sign * (high - 1.0), sign * high];
        let rows = MatRef::new(&training, 2, 1).unwrap();
        let fit = Standardizer::fit(rows, ConstantColumnPolicy::Error).unwrap();

        assert_eq!(fit.mean(), &[sign * high]);
        assert_eq!(fit.inv_std().unwrap(), [2.0]);
        let scores = fit.transform(rows).unwrap();
        assert_eq!(scores.as_ref().as_slice(), &[-sign, sign]);

        let held_out = [sign * (high + 2.0)];
        let scores = fit
            .transform(MatRef::new(&held_out, 1, 1).unwrap())
            .unwrap();
        assert_eq!(scores.as_ref().as_slice(), &[sign * 5.0]);
    }
}

#[cfg(feature = "experimental-pipelines")]
#[test]
fn scalar_bootstrap_spread_tracks_the_multiplicities_of_adjacent_values() {
    use pid_core::experimental::pipelines::{
        block_bootstrap, BlockLengthSelection, BootstrapConfig, BootstrapReplicateStatus,
        ResamplingValidityDeclaration, StatisticCallbackDeclaration,
    };
    use pid_core::ResourceEstimate;

    let high = 2_f64.powi(53);
    let data = [high - 1.0, high];
    let cfg = BootstrapConfig::new(
        16,
        1,
        42,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let result = block_bootstrap(
        &data,
        &cfg,
        StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
        |rows| Ok(rows[0]),
    )
    .unwrap();
    let mut high_count = 0;
    for replicate in &result.replicates {
        let BootstrapReplicateStatus::Complete { value } = replicate.status else {
            panic!("expected a complete scalar bootstrap replicate");
        };
        assert!(data.contains(&value));
        high_count += usize::from(value == high);
    }
    let count = result.replicates.len();
    assert!(high_count > 0 && high_count < count);
    // For unit-spaced values with multiplicities k and B-k, the exact sample
    // variance is k(B-k)/(B(B-1)). This reference never subtracts the rounded mean.
    let expected =
        ((high_count * (count - high_count)) as f64 / (count * (count - 1)) as f64).sqrt();
    let spread = result.summary.unwrap().resample_standard_deviation;
    assert!((spread - expected).abs() <= f64::EPSILON * expected);
}
