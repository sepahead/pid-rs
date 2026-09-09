//! Recorded UCI office sensors: fitted categorical shared-exclusions PID and a continuous guard.
//!
//! Download and unpack the three files linked by UCI dataset DOI 10.24432/C5X01N, then run:
//!
//! ```text
//! cargo run --locked --release -p pid-core --example occupancy_sensors -- DATA_DIRECTORY
//! cargo run --locked --release -p pid-core --features experimental-continuous \
//!   --example occupancy_sensors -- DATA_DIRECTORY
//! ```
//!
//! The optional feature exercises the continuous Ehrlich/Wibral API's rejection of the declared
//! atomic/mixed occupancy law. It does not produce a continuous occupancy PID. Sources are light
//! (lux) and CO2 (ppm), fitted to four bins on the original training recording only; the target
//! remains the recorded binary occupancy label. Every result concerns that recording's empirical
//! categorical PMF under the retained maps. Time dependence, calibration, causal value and useful
//! sensor selection do not follow from PID identities. All information quantities are nats.
//!
//! Data: Luis Candanedo (2016), UCI Occupancy Detection, CC BY 4.0. Source and file identities are
//! checked below. No data are downloaded by this example. See the companion recorded-sensor note.

use std::collections::BTreeMap;
use std::fmt::Write as _;
use std::fs::File;
use std::io::Read;
use std::path::Path;

use anyhow::{ensure, Context, Result};
use pid_core::stable::categorical::{
    discrete_sxpid2_averaged_with_budget, discrete_sxpid2_resource_estimate,
};
use pid_core::stable::quantized::{EqualWidthQuantizer, OutOfRangePolicy, QuantizerConfig};
use pid_core::{DiscreteMatRef, MatRef, ResourceBudget};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const BINS: usize = 4;
const FILE_CAP: u64 = 2 * 1024 * 1024;
const FILES: [(&str, usize, &str); 3] = [
    (
        "datatraining.txt",
        8143,
        "b2c4d0ce2b9e4e453c476f7125ef31aeec2d1f5c7f5572d0e80de3df6521ab56",
    ),
    (
        "datatest.txt",
        2665,
        "1b92c7c1b2838963464fa891a610cf3c5db4becb7189189b29b330107a584c7f",
    ),
    (
        "datatest2.txt",
        9752,
        "d026d1bd5aeccd4aff4f3b3710d48e40613bd5fc370db7e61bbdcaa50d985095",
    ),
];

struct Recording {
    name: &'static str,
    sha256: String,
    timestamps: Vec<String>,
    light: Vec<f64>,
    co2: Vec<f64>,
    occupancy: Vec<usize>,
}

fn read_recording(directory: &Path, spec: (&'static str, usize, &str)) -> Result<Recording> {
    let (name, expected_rows, expected_hash) = spec;
    let path = directory.join(name);
    let mut raw = Vec::new();
    File::open(&path)
        .with_context(|| format!("open {}", path.display()))?
        .take(FILE_CAP + 1)
        .read_to_end(&mut raw)?;
    ensure!(raw.len() as u64 <= FILE_CAP, "{name}: file cap exceeded");
    let mut sha256 = String::with_capacity(64);
    for byte in Sha256::digest(&raw) {
        write!(sha256, "{byte:02x}")?;
    }
    ensure!(
        sha256 == expected_hash,
        "{name}: original UCI bytes changed"
    );
    let text = std::str::from_utf8(&raw)?;
    let mut lines = text.lines();
    ensure!(
        lines.next() == Some("\"date\",\"Temperature\",\"Humidity\",\"Light\",\"CO2\",\"HumidityRatio\",\"Occupancy\""),
        "{name}: unexpected header"
    );
    let mut recording = Recording {
        name,
        sha256,
        timestamps: Vec::with_capacity(expected_rows),
        light: Vec::with_capacity(expected_rows),
        co2: Vec::with_capacity(expected_rows),
        occupancy: Vec::with_capacity(expected_rows),
    };
    // This parser is for the three exact hash-checked files, not general CSV. Their leading row ID
    // is unnamed in the seven-field header; datatest2 timestamps are unquoted. No field contains
    // an embedded comma or escaped quote. The timestamp is retained with each original row.
    for (index, line) in lines.enumerate() {
        ensure!(index < expected_rows, "{name}: row cap exceeded");
        let fields: Vec<_> = line.split(',').map(|s| s.trim_matches('"')).collect();
        ensure!(
            fields.len() == 8,
            "{name}: row {} has wrong arity",
            index + 2
        );
        let _: usize = fields[0].parse()?;
        let timestamp = fields[1];
        ensure!(timestamp.len() == 19, "{name}: unexpected timestamp width");
        if let Some(previous) = recording.timestamps.last() {
            ensure!(
                previous.as_str() < timestamp,
                "{name}: timestamps not increasing"
            );
        }
        let mut measured = [0.0; 5];
        for (value, field) in measured.iter_mut().zip(&fields[2..7]) {
            *value = field.parse::<f64>()?;
            ensure!(value.is_finite(), "{name}: nonfinite sensor value");
        }
        let target = fields[7].parse::<usize>()?;
        ensure!(target <= 1, "{name}: occupancy must be 0 or 1");
        recording.timestamps.push(timestamp.to_owned());
        recording.light.push(measured[2]);
        recording.co2.push(measured[3]);
        recording.occupancy.push(target);
    }
    ensure!(
        recording.occupancy.len() == expected_rows,
        "{name}: row count changed"
    );
    Ok(recording)
}

fn fit(values: &[f64], description: &str, budget: ResourceBudget) -> Result<EqualWidthQuantizer> {
    let config = QuantizerConfig::new(
        OutOfRangePolicy::ClampToBoundary,
        true,
        5,
        description,
        budget,
    )?;
    Ok(EqualWidthQuantizer::fit(
        MatRef::new(values, values.len(), 1)?,
        BINS,
        config,
    )?)
}

fn tail_counts(values: &[f64], quantizer: &EqualWidthQuantizer) -> Value {
    let edges = &quantizer.edges()[0];
    json!({
        "below_training_min": values.iter().filter(|&&x| x < edges[0]).count(),
        "above_training_max": values.iter().filter(|&&x| x > edges[BINS]).count(),
    })
}

#[cfg(feature = "experimental-continuous")]
fn continuous_status(recording: &Recording, budget: ResourceBudget) -> Result<Value> {
    use pid_core::experimental::continuous::{
        pid2_isx_report_with_budget, IsxConfig, KsgConfig, Pid2Config, Pid2Provenance,
    };
    use pid_core::stable::continuous::SupportContract;
    use pid_core::PidError;

    let config = Pid2Config {
        ksg: KsgConfig::default().with_support_contract(SupportContract::KnownAtomicOrMixed),
        isx: IsxConfig {
            support_contract: SupportContract::KnownAtomicOrMixed,
            ..IsxConfig::default()
        },
    };
    let provenance = Pid2Provenance::new(
        "Light in lux, raw reported values; no scaling or noise",
        "CO2 in ppm, raw reported values; no scaling or noise",
        "Same-row occupancy label 0/1 from the supplied recording",
        "Recorded office time series; atomic target; no IID or full-dimensional law asserted",
    )?;
    let target: Vec<_> = recording.occupancy.iter().map(|&x| x as f64).collect();
    let n = target.len();
    match pid2_isx_report_with_budget(
        MatRef::new(&recording.light, n, 1)?,
        MatRef::new(&recording.co2, n, 1)?,
        MatRef::new(&target, n, 1)?,
        &config,
        &provenance,
        budget,
    ) {
        Err(
            error @ PidError::UnsupportedSupportContract {
                contract: SupportContract::KnownAtomicOrMixed,
                ..
            },
        ) => Ok(json!({
            "status": "expected_support_rejection_observed",
            "error": error.to_string(),
            "numeric_continuous_pid": null,
        })),
        Err(error) => Err(error).context("unexpected continuous guard error"),
        Ok(_) => anyhow::bail!("continuous binary-target call unexpectedly accepted"),
    }
}

#[cfg(not(feature = "experimental-continuous"))]
fn continuous_status(_recording: &Recording, _budget: ResourceBudget) -> Result<Value> {
    Ok(json!({
        "status": "guard_not_executed_feature_disabled",
        "reason": "Binary occupancy is outside the current full-dimensional continuous API domain",
        "numeric_continuous_pid": null,
    }))
}

fn evaluate(
    recording: &Recording,
    light_map: &EqualWidthQuantizer,
    co2_map: &EqualWidthQuantizer,
    budget: ResourceBudget,
) -> Result<Value> {
    let n = recording.occupancy.len();
    let light = light_map.transform_with_report(MatRef::new(&recording.light, n, 1)?)?;
    let co2 = co2_map.transform_with_report(MatRef::new(&recording.co2, n, 1)?)?;
    // Keep the original binary target. The categorical API receives the fitted source labels;
    // the two quantizer reports below retain their provenance explicitly. Do not describe its
    // internal Categorical encoding tag as evidence that the physical measurements were discrete.
    let target = DiscreteMatRef::new(&recording.occupancy, n, 1)?;
    let resource_estimate = discrete_sxpid2_resource_estimate(
        light.matrix.as_ref(),
        co2.matrix.as_ref(),
        target,
        false,
    )?;
    let result = discrete_sxpid2_averaged_with_budget(
        light.matrix.as_ref(),
        co2.matrix.as_ref(),
        target,
        budget,
    )?;
    let mut days: BTreeMap<&str, [usize; 2]> = BTreeMap::new();
    for (timestamp, &target) in recording.timestamps.iter().zip(&recording.occupancy) {
        days.entry(&timestamp[..10]).or_default()[target] += 1;
    }
    let sum = result.red.net_nats()
        + result.unq1.net_nats()
        + result.unq2.net_nats()
        + result.syn.net_nats();
    Ok(json!({
        "recording": recording.name,
        "raw_sha256": recording.sha256,
        "rows": n,
        "first_timestamp": recording.timestamps.first(),
        "last_timestamp": recording.timestamps.last(),
        "timezone": "unspecified in retrieved metadata",
        "daily_target_counts_0_1": days,
        "estimand": "Empirical joint PMF of training-fitted Q_light(Light), Q_co2(CO2), original occupancy 0/1",
        "units": "nats",
        "source1_quantizer": light.report,
        "source2_quantizer": co2.report,
        "source1_tails": tail_counts(&recording.light, light_map),
        "source2_tails": tail_counts(&recording.co2, co2_map),
        "shannon_cmi_light_given_co2": result.mi_s1s2_t - result.mi_s2_t,
        "shannon_cmi_co2_given_light": result.mi_s1s2_t - result.mi_s1_t,
        "atom_sum_minus_joint_mi_nats": sum - result.mi_s1s2_t,
        "shared_exclusions_resource_estimate": resource_estimate,
        "shared_exclusions_empirical": result,
        "continuous_track": continuous_status(recording, budget)?,
        "scope": "Finite recorded empirical PMF; signed atoms retained; no calibrated sampling inference or sensor-placement conclusion",
    }))
}

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args_os().collect();
    ensure!(args.len() == 2, "usage: occupancy_sensors DATA_DIRECTORY");
    let directory = Path::new(&args[1]);
    // The categorical preflight assumes as many distinct states as rows. Its conservative
    // operation hint exceeds 3 billion for the largest recording; this is not a CPU count.
    let budget = ResourceBudget::new(64 * 1024 * 1024, 1_000_000, 4_000_000_000, 1)?;
    let training = read_recording(directory, FILES[0])?;
    let light_map = fit(
        &training.light,
        "raw light in lux; training recording only",
        budget,
    )?;
    let co2_map = fit(
        &training.co2,
        "raw CO2 in ppm; training recording only",
        budget,
    )?;
    let mut results = vec![evaluate(&training, &light_map, &co2_map, budget)?];
    for spec in &FILES[1..] {
        let recording = read_recording(directory, *spec)?;
        results.push(evaluate(&recording, &light_map, &co2_map, budget)?);
    }
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "dataset": "UCI Occupancy Detection, DOI 10.24432/C5X01N",
            "training_file": FILES[0].0,
            "fixed_bins_per_source": BINS,
            "chronology": "datatest precedes training; datatest2 follows training",
            "resource_budget_per_library_call": budget,
            "results": results,
        }))?
    );
    Ok(())
}
