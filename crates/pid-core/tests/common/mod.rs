// Shared test helper compiled into each integration-test binary via `mod common;`; its `pub`
// surface is intentionally broad (not every test uses every method).
#![allow(dead_code, unreachable_pub)]

pub fn csxpid_reference() -> serde_json::Value {
    const FIXTURE: &[u8] = include_bytes!("../fixtures/csxpid_reference.json");
    const CHECKSUM: &str = include_str!("../fixtures/csxpid_reference.json.sha256");

    let expected_hash = CHECKSUM
        .split_whitespace()
        .next()
        .expect("csxpid fixture checksum must contain a SHA-256 digest");
    let actual_hash = pid_runlog::sha256_hex(FIXTURE);
    assert_eq!(
        actual_hash, expected_hash,
        "csxpid fixture does not match its committed SHA-256 digest"
    );

    serde_json::from_slice(FIXTURE).expect("csxpid fixture must contain valid JSON")
}

#[derive(Clone)]
pub struct Rng64 {
    state: u64,
}

impl Rng64 {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    pub fn next_u64(&mut self) -> u64 {
        // xorshift64*
        let mut x = self.state;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.state = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }

    pub fn next_f64(&mut self) -> f64 {
        // Uniform in [0,1) using 53 bits.
        let u = self.next_u64() >> 11;
        (u as f64) * (1.0 / ((1u64 << 53) as f64))
    }

    pub fn normal(&mut self) -> f64 {
        // Box–Muller.
        let u1 = self.next_f64().max(1e-12);
        let u2 = self.next_f64();
        let r = (-2.0 * u1.ln()).sqrt();
        let theta = 2.0 * std::f64::consts::PI * u2;
        r * theta.cos()
    }
}
