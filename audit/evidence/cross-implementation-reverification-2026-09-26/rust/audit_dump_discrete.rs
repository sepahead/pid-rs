// Evidence generator: write seeded categorical systems and pid-rs outputs as JSON (see ../../cross-implementation-reverification-2026-09-26.md).
use pid_core::stable::categorical::{discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n};
use pid_core::stable::imin::{imin_pid2, imin_pid3};
use pid_core::DiscreteMatRef;
use serde_json::{json, Value};

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn below(&mut self, m: u64) -> usize {
        (self.next() % m) as usize
    }
}

fn atoms_json(antichains: &[Vec<u8>], atoms: &[pid_core::stable::categorical::SxAveragedAtom]) -> Value {
    Value::Array(
        antichains
            .iter()
            .zip(atoms)
            .map(|(a, x)| {
                json!({"antichain": a, "plus": x.informative_nats(), "minus": x.misinformative_nats(), "net": x.net_nats()})
            })
            .collect(),
    )
}

fn main() {
    let mut cases = Vec::new();
    let mut rng = Rng(20260925);
    for case in 0..60 {
        let n_sources = 2 + case % 3; // 2,3,4
        let alphabet = 2 + (rng.below(2) as usize); // 2..3
        let t_alphabet = 2 + (rng.below(2) as usize);
        let n = 8 + rng.below(120);
        // Build a random, possibly structured, system.
        let mut sources: Vec<Vec<usize>> = vec![Vec::with_capacity(n); n_sources];
        let mut target = Vec::with_capacity(n);
        let mode = case % 4;
        for _ in 0..n {
            let mut s = Vec::with_capacity(n_sources);
            for _ in 0..n_sources {
                s.push(rng.below(alphabet as u64));
            }
            let t = match mode {
                0 => rng.below(t_alphabet as u64),
                1 => s.iter().sum::<usize>() % t_alphabet,
                2 => {
                    if rng.below(4) == 0 {
                        rng.below(t_alphabet as u64)
                    } else {
                        (s[0] + s[1]) % t_alphabet
                    }
                }
                _ => (s[0] * s[1] + s[n_sources - 1]) % t_alphabet,
            };
            for (k, v) in s.into_iter().enumerate() {
                sources[k].push(v);
            }
            target.push(t);
        }
        let srefs: Vec<DiscreteMatRef<'_>> = sources
            .iter()
            .map(|s| DiscreteMatRef::new(s, n, 1).unwrap())
            .collect();
        let tref = DiscreteMatRef::new(&target, n, 1).unwrap();
        let rn = discrete_sxpid_n(&srefs, tref).unwrap();
        let mut obj = json!({
            "n_sources": n_sources,
            "sources": sources,
            "target": target,
            "n": atoms_json(&rn.antichains, &rn.atoms),
            "n_joint_mi": rn.joint_mi,
            "n_subset_mis": rn.subset_mis,
        });
        if n_sources == 2 {
            let r2 = discrete_sxpid2(srefs[0], srefs[1], tref).unwrap();
            obj["two"] = json!({
                "unq1": [r2.unq1.informative_nats(), r2.unq1.misinformative_nats()],
                "unq2": [r2.unq2.informative_nats(), r2.unq2.misinformative_nats()],
                "syn": [r2.syn.informative_nats(), r2.syn.misinformative_nats()],
                "red": [r2.red.informative_nats(), r2.red.misinformative_nats()],
                "mi": [r2.mi_s1_t, r2.mi_s2_t, r2.mi_s1s2_t],
            });
            let im = imin_pid2(srefs[0], srefs[1], tref).unwrap();
            obj["imin2"] = json!([im.redundancy, im.unique_s1, im.unique_s2, im.synergy, im.mi_s1_t, im.mi_s2_t, im.mi_s1s2_t]);
        }
        if n_sources == 3 {
            let r3 = discrete_sxpid3(srefs[0], srefs[1], srefs[2], tref).unwrap();
            obj["three"] = atoms_json(&r3.antichains, &r3.atoms);
            let im = imin_pid3(srefs[0], srefs[1], srefs[2], tref).unwrap();
            obj["imin3"] = Value::Array(
                im.atoms
                    .iter()
                    .zip(im.redundancies.iter())
                    .map(|(a, r)| json!({"antichain": a.antichain_sets, "atom": a.value, "red": r}))
                    .collect(),
            );
        }
        cases.push(obj);
    }
    println!("{}", serde_json::to_string(&cases).unwrap());
}
