use crate::distance_matrix::{symmetric_distances, SymmetricDistanceMatrix};
use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::strict_radius;
use crate::stats::{digamma, digamma_int_table};

#[derive(Clone, Copy)]
struct DistIsx3 {
    joint: f64,
    ds: f64,
    dt: f64,
}

#[derive(Debug, Clone)]
pub struct Pid3Config {
    pub k: usize,
    pub metric: Metric,
    pub tie_epsilon: f64,
}

impl Default for Pid3Config {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
        }
    }
}

/// A 3-source antichain on indices {0,1,2}, represented as up to 3 conjunction masks.
///
/// Each mask is a non-zero subset bitmask over {0,1,2}:
/// - bit 0 => source 0
/// - bit 1 => source 1
/// - bit 2 => source 2
///
/// Example: `{ {0}, {1,2} }` is encoded as `[0b001, 0b110]`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Antichain3 {
    sets: [u8; 3],
    len: u8,
}

impl Antichain3 {
    pub fn sets(&self) -> &[u8] {
        &self.sets[..(self.len as usize)]
    }

    pub fn len(&self) -> usize {
        self.len as usize
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Create an antichain from a list of non-empty subset masks over {0,1,2}.
    ///
    /// The input is canonicalized (sorted ascending) and validated to satisfy the
    /// antichain property (no set is a subset of another).
    pub fn try_from_sets(sets: &[u8]) -> PidResult<Self> {
        if sets.is_empty() || sets.len() > 3 {
            return Err(PidError::InvalidConfig {
                context: "Antichain3::try_from_sets",
                message: "need 1..=3 sets",
            });
        }

        let mut out = [0u8; 3];
        for (idx, &m) in sets.iter().enumerate() {
            if m == 0 || m > 0b111 {
                return Err(PidError::InvalidConfig {
                    context: "Antichain3::try_from_sets",
                    message: "set masks must be in 1..=0b111",
                });
            }
            out[idx] = m;
        }

        let len = sets.len();
        out[..len].sort_unstable();

        for i in 0..len {
            for j in (i + 1)..len {
                let a = out[i];
                let b = out[j];
                if a == b {
                    return Err(PidError::InvalidConfig {
                        context: "Antichain3::try_from_sets",
                        message: "duplicate set mask",
                    });
                }
                if (a & b) == a || (a & b) == b {
                    return Err(PidError::InvalidConfig {
                        context: "Antichain3::try_from_sets",
                        message: "not an antichain (subset relation present)",
                    });
                }
            }
        }

        Ok(Self {
            sets: out,
            len: len as u8,
        })
    }
}

impl Ord for Antichain3 {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.len
            .cmp(&other.len)
            .then_with(|| self.sets().cmp(other.sets()))
    }
}

impl PartialOrd for Antichain3 {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug, Clone)]
pub struct Pid3Redundancy {
    pub antichain: Antichain3,
    pub value: f64,
}

#[derive(Debug, Clone)]
pub struct Pid3Atom {
    pub antichain: Antichain3,
    pub value: f64,
}

#[derive(Debug, Clone)]
pub struct Pid3Result {
    pub redundancies: Vec<Pid3Redundancy>,
    pub atoms: Vec<Pid3Atom>,
}

impl Pid3Result {
    pub fn redundancy(&self, antichain: Antichain3) -> Option<f64> {
        self.redundancies
            .iter()
            .find(|r| r.antichain == antichain)
            .map(|r| r.value)
    }

    pub fn atom(&self, antichain: Antichain3) -> Option<f64> {
        self.atoms
            .iter()
            .find(|a| a.antichain == antichain)
            .map(|a| a.value)
    }
}

/// Full 3-source continuous SxPID using shared exclusions (Ehrlich et al. 2024).
///
/// Computes all 18 PID atoms for three sources by:
/// 1) Estimating `I^sx_∩(T : α)` for every non-empty antichain α on {0,1,2} using the kNN estimator
///    (a KSG-style construction with disjunction neighborhoods).
/// 2) Applying Möbius inversion on the redundancy lattice to obtain the PID atoms Π^sx(α).
///
/// Units: nats (natural logarithm).
pub fn pid3_isx(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<Pid3Result> {
    if s0.nrows() != s1.nrows() || s0.nrows() != s2.nrows() || s0.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "pid3_isx",
            left_rows: s0.nrows(),
            right_rows: t.nrows(),
        });
    }
    if s0.ncols() == 0 || s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "pid3_isx",
            message: "inputs must have at least 1 column",
        });
    }
    if !cfg.tie_epsilon.is_finite() || cfg.tie_epsilon < 0.0 {
        return Err(PidError::InvalidConfig {
            context: "pid3_isx",
            message: "tie_epsilon must be finite and >= 0",
        });
    }
    if cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context: "pid3_isx",
            message: "PID3 ISX is validated only for Metric::Chebyshev (L∞). Other metrics are research-gated.",
        });
    }

    let n = t.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let sources = [
        symmetric_distances(s0, cfg.metric)?,
        symmetric_distances(s1, cfg.metric)?,
        symmetric_distances(s2, cfg.metric)?,
    ];
    let target = symmetric_distances(t, cfg.metric)?;

    let antichains = antichains_3();
    let mut redundancies = Vec::with_capacity(antichains.len());
    for &a in antichains {
        let val = redundancy_for_antichain(&sources, &target, a, cfg)?;
        redundancies.push(Pid3Redundancy {
            antichain: a,
            value: val,
        });
    }

    let atoms = mobius_inversion_atoms(antichains, &redundancies)?;
    Ok(Pid3Result {
        redundancies,
        atoms,
    })
}

fn redundancy_for_antichain(
    sources: &[SymmetricDistanceMatrix; 3],
    target: &SymmetricDistanceMatrix,
    antichain: Antichain3,
    cfg: &Pid3Config,
) -> PidResult<f64> {
    let n = target.n();
    let k = cfg.k;
    let kth = k - 1;

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    let mut scratch = Vec::with_capacity(n.saturating_sub(1));

    let mut sum = 0.0f64;
    for i in 0..n {
        scratch.clear();

        for j in 0..n {
            if i == j {
                continue;
            }
            let d0 = sources[0].get(i, j);
            let d1 = sources[1].get(i, j);
            let d2 = sources[2].get(i, j);
            let ds_disj = source_disjunction_distance(antichain, d0, d1, d2);
            let dt_ij = target.get(i, j);
            scratch.push(DistIsx3 {
                joint: dt_ij.max(ds_disj),
                ds: ds_disj,
                dt: dt_ij,
            });
        }

        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps = strict_radius(scratch[kth].joint, cfg.tie_epsilon);
        if eps == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "pid3_isx: kNN radius is non-positive; add jitter to break duplicates",
            });
        }

        // Counts exclude self; estimator uses inclusive counts.
        let mut n_alpha = 1usize;
        let mut n_t = 1usize;
        for d in &scratch {
            if d.ds <= eps {
                n_alpha += 1;
            }
            if d.dt <= eps {
                n_t += 1;
            }
        }

        sum += psi_k + psi_n - psi_int[n_alpha] - psi_int[n_t];
    }

    Ok(sum / (n as f64))
}

#[inline]
fn source_disjunction_distance(antichain: Antichain3, d0: f64, d1: f64, d2: f64) -> f64 {
    let mut best = f64::INFINITY;
    for &m in antichain.sets() {
        let mut v = 0.0f64;
        if (m & 0b001) != 0 {
            v = v.max(d0);
        }
        if (m & 0b010) != 0 {
            v = v.max(d1);
        }
        if (m & 0b100) != 0 {
            v = v.max(d2);
        }
        best = best.min(v);
    }
    best
}

fn mobius_inversion_atoms(
    antichains: &[Antichain3],
    redundancies: &[Pid3Redundancy],
) -> PidResult<Vec<Pid3Atom>> {
    if antichains.len() != redundancies.len() {
        return Err(PidError::InvalidConfig {
            context: "mobius_inversion_atoms",
            message: "antichains/redundancies length mismatch",
        });
    }
    let n = antichains.len();

    let topo = topo_order(antichains);
    if topo.len() != n {
        return Err(PidError::InvalidConfig {
            context: "mobius_inversion_atoms",
            message: "topological sort failed",
        });
    }

    let mut atoms_by_idx = vec![0.0f64; n];
    for (pos, &idx) in topo.iter().enumerate() {
        let mut val = redundancies[idx].value;
        for &j in topo[..pos].iter() {
            if leq(antichains[j], antichains[idx]) {
                val -= atoms_by_idx[j];
            }
        }
        atoms_by_idx[idx] = val;
    }

    let mut atoms = Vec::with_capacity(n);
    for (idx, &a) in antichains.iter().enumerate() {
        atoms.push(Pid3Atom {
            antichain: a,
            value: atoms_by_idx[idx],
        });
    }
    Ok(atoms)
}

fn topo_order(antichains: &[Antichain3]) -> Vec<usize> {
    let mut remaining: Vec<usize> = (0..antichains.len()).collect();
    let mut out = Vec::with_capacity(remaining.len());
    while !remaining.is_empty() {
        let mut mins = Vec::new();
        'outer: for &i in &remaining {
            for &j in &remaining {
                if i == j {
                    continue;
                }
                if leq(antichains[j], antichains[i]) {
                    continue 'outer;
                }
            }
            mins.push(i);
        }
        mins.sort_by(|&a, &b| antichains[a].cmp(&antichains[b]));
        let chosen = mins[0];
        out.push(chosen);
        remaining.retain(|&x| x != chosen);
    }
    out
}

#[inline]
fn leq(a: Antichain3, b: Antichain3) -> bool {
    // a ⪯ b iff for every set B in b, there exists A in a with A ⊆ B.
    for &b_set in b.sets() {
        let mut found = false;
        for &a_set in a.sets() {
            if (a_set & b_set) == a_set {
                found = true;
                break;
            }
        }
        if !found {
            return false;
        }
    }
    true
}

fn antichains_3() -> &'static [Antichain3] {
    // Canonical order: increasing number of sets, then lexicographic by mask.
    const ANTICHAINS: [Antichain3; 18] = [
        Antichain3 {
            sets: [0b001, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b010, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b100, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b011, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b101, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b110, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b111, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b001, 0b010, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b010, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b010, 0b101, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b101, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b101, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b010, 0b100],
            len: 3,
        },
        Antichain3 {
            sets: [0b011, 0b101, 0b110],
            len: 3,
        },
    ];
    &ANTICHAINS
}
