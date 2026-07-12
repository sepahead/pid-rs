#![no_main]

mod common;

use libfuzzer_sys::fuzz_target;
use pid_core::stable::categorical::{discrete_sxpid2, discrete_sxpid3};
use pid_core::stable::quantized::{EqualWidthQuantizer, OutOfRangePolicy, QuantizerConfig};
use pid_core::{DiscreteMatRef, MatRef, ResourceBudget};

fuzz_target!(|data: &[u8]| {
    let values = common::finite_values(data, 96);
    if !values.is_empty() {
        let rows = values.len();
        if let Ok(matrix) = MatRef::new(&values, rows, 1) {
            let bins = data.first().map_or(2, |byte| usize::from(*byte % 8) + 2);
            let policy = if data.get(1).is_some_and(|byte| byte & 1 == 1) {
                OutOfRangePolicy::ClampToBoundary
            } else {
                OutOfRangePolicy::Error
            };
            let config =
                QuantizerConfig::new(policy, true, 1, "fuzz raw units", ResourceBudget::default());
            if let Ok(config) = config {
                if let Ok(quantizer) = EqualWidthQuantizer::fit(matrix, bins, config) {
                    let _ = quantizer.transform_with_report(matrix);
                    let _ = serde_json::to_vec(&quantizer);
                }
            }
        }
    }

    let labels = common::categorical_values(data, 96);
    if labels.is_empty() {
        return;
    }
    let rows = labels.len();
    if let Ok(matrix) = DiscreteMatRef::new(&labels, rows, 1) {
        let _ = discrete_sxpid2(matrix, matrix, matrix);
        let _ = discrete_sxpid3(matrix, matrix, matrix, matrix);
    }
});
