//! TEMPORARY audit probe (delete after use): does hierarchical_pairwise (default config,
//! ClampToZero) diverge from pid2_isx (forces Allow) on weakly-dependent data?

use pid_core::{
    hierarchical_pairwise, pid2_isx, HierarchicalConfig, MatRef, PairSelection, Pid2Config,
};

// SplitMix64 + Box-Muller, self-contained.
struct Rng(u64);
impl Rng {
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }
    fn f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn normal(&mut self) -> f64 {
        let u1 = self.f64().max(1e-15);
        let u2 = self.f64();
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }
}

fn main() {
    let mut rng = Rng(12345);
    let n = 300;
    let mut s1 = Vec::new();
    let mut s2 = Vec::new();
    let mut t = Vec::new();
    for _ in 0..n {
        s1.push(rng.normal());
        s2.push(rng.normal());
        t.push(rng.normal()); // independent target: MI estimates hover around 0
    }
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let direct = pid2_isx(s1, s2, t, &Pid2Config::default()).unwrap();
    println!(
        "pid2_isx  (Allow forced): Red={:+.6} Unq1={:+.6} Unq2={:+.6} Syn={:+.6}",
        direct.redundancy, direct.unique_s1, direct.unique_s2, direct.synergy
    );

    let cfg = HierarchicalConfig {
        selection: PairSelection::All,
        ..HierarchicalConfig::default()
    };
    let pairs = hierarchical_pairwise(&[s1, s2], t, &cfg).unwrap();
    let p = &pairs[0];
    println!(
        "hierarchy MI terms (default = ClampToZero): I1={:+.6} I2={:+.6} I12={:+.6} CI={:+.6}",
        p.mi_i_t, p.mi_j_t, p.mi_ij_t, p.ci
    );
    let h = p.pid.as_ref().unwrap();
    println!(
        "hierarchy (default cfg) : Red={:+.6} Unq1={:+.6} Unq2={:+.6} Syn={:+.6}",
        h.redundancy, h.unique_s1, h.unique_s2, h.synergy
    );
    println!(
        "atom deltas hierarchy-direct: dRed={:+.6} dUnq1={:+.6} dUnq2={:+.6} dSyn={:+.6}",
        h.redundancy - direct.redundancy,
        h.unique_s1 - direct.unique_s1,
        h.unique_s2 - direct.unique_s2,
        h.synergy - direct.synergy
    );
}
