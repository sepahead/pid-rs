#![no_main]

mod common;

use libfuzzer_sys::fuzz_target;
use pid_core::diagnostics::{
    continuous_input_diagnostics, intrinsic_dimension_levina_bickel, IntrinsicDimConfig,
};
use pid_core::stable::continuous::{ksg_mi_report, KsgConfig, KsgProvenance};
use pid_core::{MatRef, Metric};

fuzz_target!(|data: &[u8]| {
    let values = common::finite_values(data, 128);
    if values.len() < 2 {
        return;
    }
    let rows = values.len();
    let Ok(matrix) = MatRef::new(&values, rows, 1) else {
        return;
    };
    let k = data.first().map_or(1, |byte| usize::from(*byte % 16) + 1);
    let _ = continuous_input_diagnostics(matrix, k, Metric::Chebyshev);
    let _ = intrinsic_dimension_levina_bickel(
        matrix,
        &IntrinsicDimConfig::default()
            .with_k(k)
            .with_metric(Metric::Chebyshev),
    );

    let mut config = KsgConfig::assume_regular_full_dimensional();
    config.k = k;
    config.tie_epsilon = if data.get(1).is_some_and(|byte| byte & 1 == 1) {
        f64::EPSILON
    } else {
        0.0
    };
    if let Ok(provenance) = KsgProvenance::new("fuzz input", "fuzz observation model", None) {
        let _ = ksg_mi_report(matrix, matrix, &config, &provenance);
    }
});
