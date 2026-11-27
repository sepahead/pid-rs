use pid_core::diagnostics::{distance_concentration_stats, DistanceConcentrationConfig};
use pid_core::MatRef;

fn main() {
    let p = f64::from_bits(1.0_f64.to_bits() - 1);
    let a = [0.0, 0.0];
    let b = [p, 0.0];
    let c = [0.0, 1.0];
    let equal = [1.0, 0.0];
    for (name, points) in [
        ("p-one-one", [a, b, c]),
        ("one-p-one", [a, c, b]),
        ("equal", [a, equal, c]),
    ] {
        let flat = points.concat();
        let input = MatRef::new(&flat, 3, 2).unwrap();
        let result = distance_concentration_stats(input, &DistanceConcentrationConfig::default()).unwrap();
        println!("{name} n={} min={:016x} max={:016x} mean={:016x} std={:.17e} cv={:.17e} nn_std={:.17e}",
                 result.pairwise_count, result.pairwise_min.to_bits(), result.pairwise_max.to_bits(),
                 result.pairwise_mean.to_bits(), result.pairwise_std, result.pairwise_cv, result.nn_std);
    }
}
