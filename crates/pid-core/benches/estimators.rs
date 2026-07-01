//! Criterion microbenchmarks for the core estimators.
//!
//! These track the cost of the brute-force O(n²) kNN backend and the discrete SxPID lattice as a
//! function of sample size, so performance regressions surface as a diff. Run with:
//!
//! ```text
//! cargo bench -p pid-core
//! ```
//!
//! Inputs are drawn from a tiny self-contained deterministic RNG so benchmarks are reproducible
//! and need no dev-dependency beyond criterion.

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use pid_core::{
    discrete_sxpid2, isx_redundancy, ksg_mi, pid2_isx, IsxConfig, KsgConfig, MatRef,
    NegativeHandling, Pid2Config,
};

/// xorshift64* + Box–Muller — deterministic, dependency-free.
struct Rng(u64);
impl Rng {
    fn unit(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / ((1u64 << 53) as f64)
    }
    fn normal(&mut self) -> f64 {
        let u1 = self.unit().max(1e-12);
        let u2 = self.unit();
        (-2.0 * u1.ln()).sqrt() * (std::f64::consts::TAU * u2).cos()
    }
}

/// Additive synthetic system: `T = S1 + S2 + noise` (both sources inform T).
fn make_system(n: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut rng = Rng(0x9E37_79B9_7F4A_7C15);
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + 0.3 * rng.normal());
    }
    (s1, s2, t)
}

const SIZES: [usize; 3] = [100, 300, 800];

fn bench_ksg_mi(c: &mut Criterion) {
    let mut g = c.benchmark_group("ksg_mi");
    let cfg = KsgConfig::default();
    for &n in &SIZES {
        let (s1, _, t) = make_system(n);
        let s1m = MatRef::new(&s1, n, 1).unwrap();
        let tm = MatRef::new(&t, n, 1).unwrap();
        g.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| ksg_mi(black_box(s1m), black_box(tm), &cfg).unwrap());
        });
    }
    g.finish();
}

fn bench_isx_redundancy(c: &mut Criterion) {
    let mut g = c.benchmark_group("isx_redundancy_ehrlich");
    let cfg = IsxConfig::default();
    for &n in &SIZES {
        let (s1, s2, t) = make_system(n);
        let s1m = MatRef::new(&s1, n, 1).unwrap();
        let s2m = MatRef::new(&s2, n, 1).unwrap();
        let tm = MatRef::new(&t, n, 1).unwrap();
        g.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| isx_redundancy(black_box(s1m), black_box(s2m), black_box(tm), &cfg).unwrap());
        });
    }
    g.finish();
}

fn bench_pid2(c: &mut Criterion) {
    let mut g = c.benchmark_group("pid2_isx");
    let cfg = Pid2Config {
        ksg: KsgConfig {
            negative_handling: NegativeHandling::Allow,
            ..Default::default()
        },
        isx: IsxConfig::default(),
    };
    for &n in &SIZES {
        let (s1, s2, t) = make_system(n);
        let s1m = MatRef::new(&s1, n, 1).unwrap();
        let s2m = MatRef::new(&s2, n, 1).unwrap();
        let tm = MatRef::new(&t, n, 1).unwrap();
        g.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| pid2_isx(black_box(s1m), black_box(s2m), black_box(tm), &cfg).unwrap());
        });
    }
    g.finish();
}

fn bench_discrete_sxpid2(c: &mut Criterion) {
    let mut g = c.benchmark_group("discrete_sxpid2");
    for &n in &SIZES {
        let (s1, s2, t) = make_system(n);
        let s1m = MatRef::new(&s1, n, 1).unwrap();
        let s2m = MatRef::new(&s2, n, 1).unwrap();
        let tm = MatRef::new(&t, n, 1).unwrap();
        g.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| discrete_sxpid2(black_box(s1m), black_box(s2m), black_box(tm), 8).unwrap());
        });
    }
    g.finish();
}

criterion_group!(
    benches,
    bench_ksg_mi,
    bench_isx_redundancy,
    bench_pid2,
    bench_discrete_sxpid2
);
criterion_main!(benches);
