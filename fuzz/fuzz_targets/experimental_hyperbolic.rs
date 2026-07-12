#![no_main]

mod common;

use libfuzzer_sys::fuzz_target;
use pid_core::experimental::hyperbolic::{
    hyperbolic_distance_lorentz, lorentz_dot, lorentz_to_poincare, poincare_to_lorentz,
    poincare_to_lorentz_resource_estimate, poincare_to_lorentz_with_budget, HyperbolicCurvature,
};
use pid_core::ResourceBudget;

const CURVATURE: HyperbolicCurvature = HyperbolicCurvature::NegativeOne;

fuzz_target!(|data: &[u8]| {
    let values = common::finite_values(data, 32);
    let split = values.len() / 2;
    let left = &values[..split];
    let right = &values[split..];
    let _ = lorentz_dot(left, right);
    let _ = hyperbolic_distance_lorentz(left, right, CURVATURE);
    let _ = poincare_to_lorentz(left, CURVATURE);
    let _ = poincare_to_lorentz_resource_estimate(left.len());
    let _ = poincare_to_lorentz_with_budget(
        left,
        CURVATURE,
        ResourceBudget::new(64, 1, 1_000, 1).expect("fixed nonzero resource budget"),
    );

    if !left.is_empty() {
        let scale = left.iter().map(|value| value.abs()).sum::<f64>();
        if scale.is_finite() && scale > 1.0 {
            let inside: Vec<f64> = left.iter().map(|value| value / (2.0 * scale)).collect();
            if let Ok(point) = poincare_to_lorentz(&inside, CURVATURE) {
                let _ = hyperbolic_distance_lorentz(&point, &point, CURVATURE);
                let _ = lorentz_to_poincare(&point, CURVATURE);
            }
        }
    }
});
