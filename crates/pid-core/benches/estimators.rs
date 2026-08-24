//! Criterion microbenchmarks for the core estimators.
//!
//! These track the cost of the exact kNN backend (kd-tree where applicable, brute force otherwise)
//! and the discrete SxPID lattice as a function of sample size. Run with:
//!
//! ```text
//! cargo bench --locked -p pid-core --all-features --bench estimators
//! ```
//!
//! Inputs are drawn from a tiny self-contained deterministic RNG so benchmarks are reproducible
//! and need no dev-dependency beyond criterion.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};
use pid_core::experimental::continuous::raw_scalars::{isx_redundancy, ksg_mi};
use pid_core::experimental::continuous::{pid2_isx, IsxConfig, Pid2Config};
use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid2_averaged, discrete_sxpid3_averaged, discrete_sxpid_n_averaged,
};
use pid_core::stable::continuous::KsgConfig;
use pid_core::stable::imin::imin_pid2;
use pid_core::stable::quantized::{EqualWidthQuantizer, QuantizerConfig};
use pid_core::{DiscreteMatRef, MatRef};
use std::hint::black_box;

/// xorshift64* + Box–Muller — deterministic, dependency-free.
struct Rng(u64);
impl Rng {
    fn next_u64(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }

    fn unit(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / ((1u64 << 53) as f64)
    }
    fn normal(&mut self) -> f64 {
        let u1 = self.unit().max(1e-12);
        let u2 = self.unit();
        (-2.0 * u1.ln()).sqrt() * (std::f64::consts::TAU * u2).cos()
    }
}

fn make_categorical_system(
    n: usize,
    source_count: usize,
    alphabet_size: usize,
) -> (Vec<Vec<usize>>, Vec<usize>) {
    let mut rng = Rng(0xD1B5_4A32_D192_ED03);
    let mut sources = vec![vec![0; n]; source_count];
    let mut target = vec![0; n];
    for row in 0..n {
        let mut source_sum = 0usize;
        for source in &mut sources {
            let value = rng.next_u64() as usize % alphabet_size;
            source[row] = value;
            source_sum = source_sum.wrapping_add(value);
        }
        let noise = usize::from(rng.next_u64().is_multiple_of(5));
        target[row] = source_sum.wrapping_add(noise) % alphabet_size;
    }
    (sources, target)
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
    let cfg = KsgConfig::assume_regular_full_dimensional();
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
    let cfg = IsxConfig::assume_regular_full_dimensional();
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
    let cfg = Pid2Config::assume_regular_full_dimensional();
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

fn bench_quantized_sxpid2(c: &mut Criterion) {
    let mut g = c.benchmark_group("quantized_sxpid2");
    for &n in &SIZES {
        let (s1, s2, t) = make_system(n);
        let s1m = MatRef::new(&s1, n, 1).unwrap();
        let s2m = MatRef::new(&s2, n, 1).unwrap();
        let tm = MatRef::new(&t, n, 1).unwrap();
        g.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| {
                let q1 = EqualWidthQuantizer::fit(black_box(s1m), 8, QuantizerConfig::default())
                    .unwrap();
                let q2 = EqualWidthQuantizer::fit(black_box(s2m), 8, QuantizerConfig::default())
                    .unwrap();
                let qt =
                    EqualWidthQuantizer::fit(black_box(tm), 8, QuantizerConfig::default()).unwrap();
                let s1q = q1.transform(s1m).unwrap();
                let s2q = q2.transform(s2m).unwrap();
                let tq = qt.transform(tm).unwrap();
                discrete_sxpid2(s1q.as_ref(), s2q.as_ref(), tq.as_ref()).unwrap()
            });
        });
    }
    g.finish();
}

fn bench_quantizer_transform_paths(c: &mut Criterion) {
    const N: usize = 100_000;
    const DIMENSIONS: usize = 4;
    const BINS: usize = 256;

    let mut rng = Rng(0xA409_3822_299F_31D0);
    let data = (0..N * DIMENSIONS)
        .map(|_| rng.normal())
        .collect::<Vec<_>>();
    let matrix = MatRef::new(&data, N, DIMENSIONS).unwrap();
    let quantizer = EqualWidthQuantizer::fit(matrix, BINS, QuantizerConfig::default()).unwrap();

    let mut group = c.benchmark_group("equal_width_quantizer_transform");
    group.bench_function("labels_only", |b| {
        b.iter(|| quantizer.transform(black_box(matrix)).unwrap());
    });
    group.bench_function("with_report", |b| {
        b.iter(|| quantizer.transform_with_report(black_box(matrix)).unwrap());
    });
    group.finish();
}

fn bench_categorical_pid_latency(c: &mut Criterion) {
    let mut group = c.benchmark_group("categorical_pid_latency");

    let (sources, target) = make_categorical_system(128, 2, 4);
    let s0 = DiscreteMatRef::new(&sources[0], 128, 1).unwrap();
    let s1 = DiscreteMatRef::new(&sources[1], 128, 1).unwrap();
    let target_ref = DiscreteMatRef::new(&target, 128, 1).unwrap();
    group.bench_function("imin2_n128_q4", |b| {
        b.iter(|| imin_pid2(black_box(s0), black_box(s1), black_box(target_ref)).unwrap());
    });
    group.bench_function("sx2_averaged_n128_q4", |b| {
        b.iter(|| {
            discrete_sxpid2_averaged(black_box(s0), black_box(s1), black_box(target_ref)).unwrap()
        });
    });

    let (sources, target) = make_categorical_system(64, 3, 2);
    let s0 = DiscreteMatRef::new(&sources[0], 64, 1).unwrap();
    let s1 = DiscreteMatRef::new(&sources[1], 64, 1).unwrap();
    let s2 = DiscreteMatRef::new(&sources[2], 64, 1).unwrap();
    let target_ref = DiscreteMatRef::new(&target, 64, 1).unwrap();
    group.bench_function("sx3_averaged_n64_q2", |b| {
        b.iter(|| {
            discrete_sxpid3_averaged(
                black_box(s0),
                black_box(s1),
                black_box(s2),
                black_box(target_ref),
            )
            .unwrap()
        });
    });

    let (sources, target) = make_categorical_system(32, 4, 2);
    let source_refs = sources
        .iter()
        .map(|source| DiscreteMatRef::new(source, 32, 1).unwrap())
        .collect::<Vec<_>>();
    let target_ref = DiscreteMatRef::new(&target, 32, 1).unwrap();
    group.bench_function("sx4_averaged_n32_q2", |b| {
        b.iter(|| {
            discrete_sxpid_n_averaged(black_box(&source_refs), black_box(target_ref)).unwrap()
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_ksg_mi,
    bench_isx_redundancy,
    bench_pid2,
    bench_quantized_sxpid2,
    bench_quantizer_transform_paths,
    bench_categorical_pid_latency
);
criterion_main!(benches);
