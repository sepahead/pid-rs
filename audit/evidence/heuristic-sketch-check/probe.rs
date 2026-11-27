use pid_core::experimental::continuous::{
    pid2_isx, pid2_isx_estimate, pid2_isx_report, IsxConfig, IsxMethod, Pid2Config, Pid2Provenance,
};
use pid_core::experimental::isx_heuristics::heuristic_sketch_baseline;
use pid_core::{MatRef, PidError};

fn one(x: &[f64]) -> MatRef<'_> {
    MatRef::new(x, x.len(), 1).unwrap()
}

fn config(k: usize) -> IsxConfig {
    IsxConfig {
        k,
        ..IsxConfig::assume_regular_full_dimensional()
    }
}

fn rows(n: usize, wide: bool) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let nf = n as f64;
    let spread = |i: usize| i as f64 + (i * i) as f64 / (4.0 * nf * nf);
    let x = (0..n).map(|i| i as f64 / (4.0 * nf)).collect();
    let y = (0..n)
        .map(|i| {
            let j = (3 * i + 1) % n;
            if wide {
                4.0 * nf * spread(j)
            } else {
                j as f64 / (4.0 * nf)
            }
        })
        .collect();
    let t = (0..n).map(spread).collect();
    (x, y, t)
}

fn uniform_points(mut seed: u64, n: usize) -> Vec<f64> {
    (0..n)
        .map(|_| {
            seed = seed.wrapping_add(0x9e3779b97f4a7c15);
            let mut z = seed;
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
            ((z ^ (z >> 31)) >> 12) as f64 / 4503599627370496.0
        })
        .collect()
}

fn endpoints() {
    for n in [4, 8, 16, 32] {
        for k in [1, 2, n - 1] {
            for wide in [false, true] {
                let (x, y, t) = rows(n, wide);
                for swapped in [false, true] {
                    let (a, b) = if swapped { (&y, &x) } else { (&x, &y) };
                    let s = heuristic_sketch_baseline(one(a), one(b), one(&t), &config(k)).unwrap();
                    println!(
                        "endpoint\t{n}\t{k}\t{wide}\t{swapped}\t{:016x}",
                        s.to_bits()
                    );
                }
            }
        }
    }
}

fn samples() {
    let x = uniform_points(104729, 256);
    let y = uniform_points(1299709, 256);
    let t = uniform_points(15485863, 256);
    let mut cfg = Pid2Config::assume_regular_full_dimensional();
    cfg.isx.method = IsxMethod::HeuristicSketch;
    cfg.isx.k = 3;
    cfg.ksg.k = 3;
    let provenance = Pid2Provenance::new(
        "scalar S1",
        "scalar S2",
        "scalar target",
        "fixed pseudo-random test inputs",
    )
    .unwrap();
    for n in [8, 32, 128, 256] {
        let (a, b, c) = (one(&x[..n]), one(&y[..n]), one(&t[..n]));
        let r = heuristic_sketch_baseline(a, b, c, &cfg.isx).unwrap();
        let estimate = pid2_isx_estimate(a, b, c, &cfg).unwrap();
        println!(
            "sample\t{n}\t{:016x}\t{:016x}\t{:016x}\t{:016x}\t{:016x}",
            r.to_bits(),
            estimate.mi_s1_t.to_bits(),
            estimate.mi_s2_t.to_bits(),
            estimate.mi_s1s2_t.to_bits(),
            estimate.redundancy_isx.to_bits()
        );
        match pid2_isx(a, b, c, &cfg) {
            Ok(z) => println!(
                "pid2\t{n}\taccepted\t{:016x}\t{:016x}\t{:016x}\t{:016x}",
                z.redundancy.to_bits(),
                z.unique_s1.to_bits(),
                z.unique_s2.to_bits(),
                z.synergy.to_bits()
            ),
            Err(PidError::NumericalInstability { context }) => {
                println!("pid2\t{n}\trefused\t{context}")
            }
            Err(e) => panic!("unexpected raw PID2 result: {e:?}"),
        }
        match pid2_isx_report(a, b, c, &cfg, &provenance) {
            Err(PidError::InvalidConfig { context, message }) => {
                println!("report\t{n}\t{context}\t{message}")
            }
            x => panic!("unexpected report result: {x:?}"),
        }
    }
}

fn controls() {
    let (x, y, t) = rows(4, false);
    let a = one(&x);
    let b = one(&y);
    let c = one(&t);
    for (name, cfg) in [
        ("rank_zero", config(0)),
        ("rank_n", config(4)),
        (
            "unspecified",
            IsxConfig {
                k: 2,
                ..IsxConfig::default()
            },
        ),
        (
            "epsilon",
            IsxConfig {
                tie_epsilon: 1e-10,
                ..config(2)
            },
        ),
    ] {
        println!(
            "refusal\t{name}\t{:?}",
            heuristic_sketch_baseline(a, b, c, &cfg).unwrap_err()
        );
    }
    let xy: Vec<_> = x.iter().zip(&y).flat_map(|(&a, &b)| [a, b]).collect();
    let two = MatRef::new(&xy, 4, 2).unwrap();
    println!(
        "refusal\tdimension\t{:?}",
        heuristic_sketch_baseline(a, two, c, &config(2)).unwrap_err()
    );
    println!(
        "refusal\ttarget_duplicate\t{:?}",
        heuristic_sketch_baseline(a, b, one(&[0., 0., 1., 2.]), &config(2)).unwrap_err()
    );
    let q = one(&[0.0, 0.5, 1.0, 0.3, 3.0]);
    println!(
        "refusal\tambiguous\t{:?}",
        heuristic_sketch_baseline(q, q, one(&[0.0, 0.4, 0.2, 1.0, 3.0]), &config(2)).unwrap_err()
    );
    let tt: Vec<_> = t.iter().map(|&v| [v, v / 16.0]).flatten().collect();
    let result =
        heuristic_sketch_baseline(a, b, MatRef::new(&tt, 4, 2).unwrap(), &config(2)).unwrap();
    println!("target2\t{:016x}", result.to_bits());
}

fn main() {
    endpoints();
    samples();
    controls();
}
