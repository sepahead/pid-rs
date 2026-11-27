use pid_core::diagnostics::{distance_concentration_stats, DistanceConcentrationConfig};
use pid_core::{MatRef, Metric};
use std::io::{self, BufRead};

fn main() {
    for line in io::stdin().lock().lines() {
        let text = line.unwrap();
        let mut words = text.split_whitespace();
        let name = words.next().unwrap();
        let data: Vec<_> = words.map(|w| f64::from_bits(u64::from_str_radix(w, 16).unwrap())).collect();
        let x = MatRef::new(&data, 3, 2).unwrap();
        let cfg = DistanceConcentrationConfig::default().with_metric(Metric::Chebyshev);
        match distance_concentration_stats(x, &cfg) {
            Ok(v) => {
                let vals = [v.pairwise_min, v.pairwise_max, v.pairwise_mean, v.pairwise_std, v.pairwise_cv,
                            v.nn_min, v.nn_max, v.nn_mean, v.nn_std, v.nn_cv, v.nn_over_pairwise_mean];
                let transitions: Vec<String> = vals.iter().map(|q| format!("{:016x}", q.to_bits())).collect();
                println!("{name}\tok\t{}\t{}", v.pairwise_count, transitions.join(" "));
            }
            Err(error) => println!("{name}\terr\t{error:?}"),
        }
    }
}
