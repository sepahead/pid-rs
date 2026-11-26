//! Expose the labeled outputs of two public estimators on caller-supplied categorical rows.
use pid_core::stable::categorical::discrete_sxpid3_averaged;
use pid_core::stable::imin::imin_pid3;
use pid_core::DiscreteMatRef;
use serde_json::{json, Value};
use std::error::Error;
use std::io::{self, BufReader, Read};

fn bits(value: f64) -> Result<String, &'static str> {
    if value.is_finite() {
        Ok(format!("{:016x}", value.to_bits()))
    } else {
        Err("nonfinite public output")
    }
}

fn measure(rows: &[[usize; 4]]) -> Result<Value, Box<dyn Error>> {
    if rows.len() != 117 {
        return Err("expected 117 source episodes".into());
    }
    if rows.iter().any(|r| r[0] > 1 || r[1] != 0 || r[2] > 1 || r[3] != r[0]) {
        return Err("expected binary force and torque, constant middle source, copied force target".into());
    }
    let columns: [Vec<usize>; 4] =
        std::array::from_fn(|column| rows.iter().map(|row| row[column]).collect());
    let col = |i: usize| DiscreteMatRef::new(&columns[i], rows.len(), 1);
    let (force, constant, torque, target) = (col(0)?, col(1)?, col(2)?, col(3)?);
    let shared = discrete_sxpid3_averaged(force, constant, torque, target)?;
    let minimum = imin_pid3(force, constant, torque, target)?;
    if shared.antichains.len() != shared.atoms.len() {
        return Err("labels and shared-exclusions atoms have different lengths".into());
    }
    let mut shared_atoms = Vec::with_capacity(shared.atoms.len());
    for (masks, atom) in shared.antichains.iter().zip(&shared.atoms) {
        shared_atoms.push(json!({
            "masks": masks,
            "informative": bits(atom.informative_nats())?,
            "misinformative": bits(atom.misinformative_nats())?,
            "signed": bits(atom.net_nats())?,
        }));
    }
    let mut minimum_atoms = Vec::with_capacity(minimum.atoms.len());
    for atom in &minimum.atoms {
        minimum_atoms.push(json!({"masks": atom.antichain_sets, "imin": bits(atom.value)?}));
    }
    Ok(json!({
        "mgw": {
            "sample_count": shared.empirical_pmf.sample_count,
            "support": shared.empirical_pmf.observed_joint_states,
            "cardinalities": shared.input.observed_cardinalities,
            "encoding": shared.input.encoding,
            "pointwise_included": shared.pointwise_included,
            "pointwise_len": shared.pointwise.len(),
            "atoms": shared_atoms,
        },
        "imin": {
            "sample_count": minimum.empirical_pmf.sample_count,
            "support": minimum.empirical_pmf.observed_joint_states,
            "cardinalities": minimum.input.observed_cardinalities,
            "encoding": minimum.input.encoding,
            "atoms": minimum_atoms,
        }
    }))
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut input = Vec::new();
    let max_bytes = 100_000;
    BufReader::new(io::stdin().lock())
        .take(max_bytes + 1)
        .read_to_end(&mut input)?;
    if input.len() as u64 > max_bytes {
        return Err("input exceeds 100,000 bytes".into());
    }
    let rows: Vec<[usize; 4]> = serde_json::from_slice(&input)?;
    serde_json::to_writer(io::stdout().lock(), &measure(&rows)?)?;
    println!();
    Ok(())
}
