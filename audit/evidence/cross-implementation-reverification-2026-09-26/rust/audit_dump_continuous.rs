// Evidence generator: write seeded Gaussian systems and pid-rs continuous outputs as JSON (see ../../cross-implementation-reverification-2026-09-26.md).
use pid_core::experimental::continuous::raw_scalars::{
    isx_redundancy, ksg_local_mi_terms, ksg_mi, ksg_mi_concat_xy,
};
use pid_core::experimental::continuous::{
    incomplete_pid3_diagnostic, pid2_isx, IsxConfig, KsgConfig, Pid2Config, Pid3Config,
};
use pid_core::experimental::mixed_dimension_pid3::pid3_isx;
use pid_core::MatRef;
use serde_json::json;

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn unif(&mut self) -> f64 {
        ((self.next() >> 11) as f64 + 0.5) / (1u64 << 53) as f64
    }
    fn normal(&mut self) -> f64 {
        let u1 = self.unif();
        let u2 = self.unif();
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }
}

fn main() {
    let mut rng = Rng(77);
    let mut cases = Vec::new();
    for (case, &(n, d, k)) in [
        (60usize, 1usize, 1usize),
        (60, 1, 3),
        (150, 2, 3),
        (300, 1, 5),
        (400, 2, 4),
        (200, 1, 2),
    ]
    .iter()
    .enumerate()
    {
        let mut s0 = Vec::new();
        let mut s1 = Vec::new();
        let mut s2 = Vec::new();
        let mut t = Vec::new();
        for _ in 0..n {
            let mut row_t = Vec::new();
            let mut a = Vec::new();
            let mut b = Vec::new();
            let mut c = Vec::new();
            for _ in 0..d {
                let x = rng.normal();
                let y = 0.5 * x + rng.normal();
                let z = rng.normal();
                a.push(x);
                b.push(y);
                c.push(z);
                row_t.push(x + 0.7 * y + if case % 2 == 0 { x * z } else { 0.3 * z } + 0.5 * rng.normal());
            }
            s0.extend(a);
            s1.extend(b);
            s2.extend(c);
            t.extend(row_t);
        }
        let m0 = MatRef::new(&s0, n, d).unwrap();
        let m1 = MatRef::new(&s1, n, d).unwrap();
        let m2 = MatRef::new(&s2, n, d).unwrap();
        let mt = MatRef::new(&t, n, d).unwrap();
        let kcfg = KsgConfig::assume_regular_full_dimensional().with_k(k);
        let mut icfg = IsxConfig::assume_regular_full_dimensional();
        icfg.k = k;
        let mut pcfg = Pid2Config::assume_regular_full_dimensional();
        pcfg.ksg = kcfg.clone();
        pcfg.isx = icfg.clone();
        let mut p3 = Pid3Config::assume_regular_full_dimensional();
        p3.k = k;
        let local = ksg_local_mi_terms(m0, mt, &kcfg).unwrap();
        let pid2 = pid2_isx(m0, m1, mt, &pcfg).unwrap();
        let inc = incomplete_pid3_diagnostic(m0, m1, m2, mt, &p3).unwrap();
        let mut p3full = p3.clone();
        p3full.experimental_allow_mixed_dimension_lattice = true;
        let full = pid3_isx(m0, m1, m2, mt, &p3full);
        cases.push(json!({
            "n": n, "d": d, "k": k,
            "s0": s0, "s1": s1, "s2": s2, "t": t,
            "ksg_s0_t": ksg_mi(m0, mt, &kcfg).unwrap(),
            "ksg_s1_t": ksg_mi(m1, mt, &kcfg).unwrap(),
            "ksg_s0s1_t": ksg_mi_concat_xy(m0, m1, mt, &kcfg).unwrap(),
            "ksg_local_s0_t": local,
            "isx_s0_s1_t": isx_redundancy(m0, m1, mt, &icfg).unwrap(),
            "pid2": [pid2.redundancy, pid2.unique_s1, pid2.unique_s2, pid2.synergy],
            "inc_pid3": inc.redundancies.iter().map(|r| json!({"sets": r.antichain.sets(), "value": r.value})).collect::<Vec<_>>(),
            "full_pid3": match full {
                Ok(f) => json!(f.redundancies.iter().map(|r| json!({"sets": r.antichain.sets(), "value": r.value})).collect::<Vec<_>>()),
                Err(e) => json!(format!("{e:?}")),
            },
        }));
    }
    println!("{}", serde_json::to_string(&cases).unwrap());
}
