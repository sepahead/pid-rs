#![no_main]

use libfuzzer_sys::fuzz_target;
use pid_core::diagnostics::{
    continuous_input_diagnostics_with_budget, intrinsic_dimension_report,
    joint_entropy_discrete_with_budget, sampled_four_point_delta_summary_with_budget,
    symmetric_distance_resources, symmetric_distances_with_budget, HyperbolicityConfig,
    IntrinsicDimConfig,
};
use pid_core::stable::categorical::discrete_sxpid2_averaged_with_budget;
use pid_core::stable::continuous::{
    ksg_k_trajectory, ksg_mi_report_with_budget, KsgConfig, KsgProvenance,
};
use pid_core::stable::imin::imin_pid2_with_budget;
use pid_core::stable::preprocessing::{HashProjector, PcaProjector};
use pid_core::stable::quantized::{EqualWidthQuantizer, OutOfRangePolicy, QuantizerConfig};
use pid_core::{DiscreteMatRef, MatRef, Metric, ResourceBudget, ResourceEstimate};

fuzz_target!(|data: &[u8]| {
    let number = data
        .iter()
        .take(8)
        .enumerate()
        .fold(0_u64, |value, (shift, byte)| {
            value | (u64::from(*byte) << (shift * 8))
        });
    let rows = usize::try_from(number).unwrap_or(usize::MAX);
    let simultaneous = data.get(8).map_or(1, |byte| usize::from(*byte));
    let operations = u128::from(data.get(9).copied().unwrap_or(1));
    let estimate =
        ResourceEstimate::triangular_f64("fuzz resource estimate", rows, simultaneous, operations);
    let mut budget = ResourceBudget::default();
    budget.max_bytes = number;
    budget.max_pairwise_distances = number.rotate_left(13);
    budget.max_operations_hint = u128::from(number).saturating_mul(u128::from(number));
    budget.max_threads = data.get(10).map_or(0, |byte| usize::from(*byte));
    let _ = budget.validate("fuzz resource budget");
    if let Ok(estimate) = estimate {
        let _ = budget.check("fuzz resource budget", estimate);
    }
    let _ = symmetric_distance_resources(rows);

    // Exercise real public preflights with decoded giant sizes while all materialized inputs stay
    // tiny. The fuzz oracle is simply "never panic, abort, or attempt an uncontrolled allocation";
    // each API may return any structured domain/resource error appropriate to the bytes.
    let mut tiny_budget = ResourceBudget::default();
    tiny_budget.max_bytes = 512;
    tiny_budget.max_pairwise_distances = 64;
    tiny_budget.max_operations_hint = 512;
    tiny_budget.max_threads = 1;
    if let Ok(virtual_matrix) = MatRef::new(&[], rows, 0) {
        let _ = symmetric_distances_with_budget(virtual_matrix, Metric::Chebyshev, tiny_budget);
    }

    let four_values = [0.0, 0.7, 1.9, 4.2];
    let four = MatRef::new(&four_values, 4, 1).expect("fixed shape");
    let _ = sampled_four_point_delta_summary_with_budget(
        four,
        &HyperbolicityConfig::default()
            .with_n_samples(rows.max(1))
            .with_metric(Metric::Chebyshev)
            .with_seed(number),
        tiny_budget,
    );
    let _ = intrinsic_dimension_report(
        four,
        &IntrinsicDimConfig::default()
            .with_k(3)
            .with_metric(Metric::Chebyshev),
        tiny_budget,
    );
    let _ = continuous_input_diagnostics_with_budget(four, 1, Metric::Chebyshev, tiny_budget);

    let training = [0.0, 1.0];
    let training = MatRef::new(&training, 2, 1).expect("fixed shape");
    let bins = rows.max(2);
    if let Ok(config) = QuantizerConfig::new(OutOfRangePolicy::Error, false, 1, "fuzz", tiny_budget)
    {
        let _ = EqualWidthQuantizer::fit(training, bins, config);
    }

    let y_values = [0.2, 1.1, 2.3, 4.9];
    let y = MatRef::new(&y_values, 4, 1).expect("fixed shape");
    let config = KsgConfig::assume_regular_full_dimensional().with_k(1);
    let provenance = KsgProvenance::new("fuzz identity", "fuzz continuous model", None)
        .expect("fixed provenance");
    let _ = ksg_mi_report_with_budget(four, y, &config, &provenance, tiny_budget);

    let mut thread_budget = tiny_budget;
    thread_budget.max_threads = rows.max(1);
    let _ = ksg_mi_report_with_budget(four, y, &config, &provenance, thread_budget);
    let _ = ksg_k_trajectory(four, y, &[1, 2], &config, &provenance, tiny_budget);

    if let Ok(projector) = HashProjector::new(1, rows.max(1), number) {
        let _ = projector.transform_with_budget(training, tiny_budget);
    }
    let _ = PcaProjector::fit_resource_estimate(four, rows.max(1));

    let source1 = [0usize, 0, 1, 1];
    let source2 = [0usize, 1, 0, 1];
    let target = [0usize, 1, 1, 0];
    let source1_matrix = DiscreteMatRef::new(&source1, 4, 1).expect("fixed shape");
    let source2_matrix = DiscreteMatRef::new(&source2, 4, 1).expect("fixed shape");
    let target_matrix = DiscreteMatRef::new(&target, 4, 1).expect("fixed shape");
    let _ = discrete_sxpid2_averaged_with_budget(
        source1_matrix,
        source2_matrix,
        target_matrix,
        tiny_budget,
    );
    let _ = imin_pid2_with_budget(source1_matrix, source2_matrix, target_matrix, tiny_budget);
    let source1_u32 = [0u32, 0, 1, 1];
    let source2_u32 = [0u32, 1, 0, 1];
    let _ = joint_entropy_discrete_with_budget(&[&source1_u32, &source2_u32], tiny_budget);
});
