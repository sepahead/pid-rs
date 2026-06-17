//! Estimate mutual information and 2-source PID atoms on a synthetic system.
//!
//! The target `T = S1 + S2 + noise` depends on both sources, so we expect non-trivial
//! redundancy/unique/synergy structure. Run with:
//!
//! ```text
//! cargo run --release --example ksg_and_pid
//! ```
use pid_core::{ksg_mi, pid2_isx, IsxConfig, KsgConfig, MatRef, NegativeHandling, Pid2Config};

/// Tiny self-contained deterministic RNG (xorshift64* + Box–Muller) so the example
/// needs no extra dependencies and is reproducible.
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

fn main() -> Result<(), pid_core::PidError> {
    let n = 500;
    let mut rng = Rng(0x1234_5678_9abc_def0);
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + 0.2 * rng.normal());
    }

    let s1 = MatRef::new(&s1, n, 1)?;
    let s2 = MatRef::new(&s2, n, 1)?;
    let t = MatRef::new(&t, n, 1)?;

    // Use `Allow` so atoms cancel exactly in the PID identities (clamping is a reporting choice).
    let ksg = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };

    println!("Mutual information (nats):");
    println!("  I(S1; T)     = {:.4}", ksg_mi(s1, t, &ksg)?);
    println!("  I(S2; T)     = {:.4}", ksg_mi(s2, t, &ksg)?);

    let cfg = Pid2Config {
        ksg: ksg.clone(),
        isx: IsxConfig::default(),
    };
    let pid = pid2_isx(s1, s2, t, &cfg)?;

    println!("\n2-source PID atoms (I^sx_∩), nats:");
    println!("  Redundancy   = {:.4}", pid.redundancy);
    println!("  Unique(S1)   = {:.4}", pid.unique_s1);
    println!("  Unique(S2)   = {:.4}", pid.unique_s2);
    println!("  Synergy      = {:.4}", pid.synergy);
    println!(
        "  (sum of atoms = {:.4} = I(S1,S2; T))",
        pid.redundancy + pid.unique_s1 + pid.unique_s2 + pid.synergy
    );
    Ok(())
}
