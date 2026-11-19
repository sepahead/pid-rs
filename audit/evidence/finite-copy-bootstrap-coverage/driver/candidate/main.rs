use std::error::Error;
use std::io::{self, Write};
use std::mem::size_of;

use pid_core::experimental::pipelines::{
    block_bootstrap, BlockLengthSelection, BlockResamplingAlgorithmRevision, BootstrapConfig,
    BootstrapReplicateStatus, BootstrapResult, ResamplingValidityDeclaration,
    StatisticCallbackDeclaration,
};
use pid_core::stable::categorical::{
    discrete_sxpid2_averaged, discrete_sxpid2_resource_estimate, DiscreteSxPid2Result,
};
use pid_core::{DiscreteMatRef, PidError, PidResult, ResourceEstimate};
use serde_json::{json, Value};

const ROW_COUNT: usize = 4;
const OUTPUT_LIMIT: usize = 1_048_576;

fn check_row_count(rows: &[f64], context: &'static str) -> PidResult<()> {
    if rows.len() != ROW_COUNT {
        return Err(PidError::ShapeMismatch {
            context,
            expected_len: ROW_COUNT,
            actual_len: rows.len(),
        });
    }
    Ok(())
}

fn digit(value: f64, largest: u8, context: &'static str) -> PidResult<u8> {
    if !value.is_finite() {
        return Err(PidError::NonFiniteInput { context });
    }
    let digit = value as u8;
    if digit > largest || f64::from(digit) != value {
        return Err(PidError::InvalidConfig {
            context,
            message: "row value must be an integer in the declared alphabet",
        });
    }
    Ok(digit)
}

fn copy_redundancy(rows: &[f64]) -> PidResult<f64> {
    const CONTEXT: &str = "categorical copy statistic";
    check_row_count(rows, CONTEXT)?;
    let mut labels = [0usize; ROW_COUNT];
    for (label, &value) in labels.iter_mut().zip(rows) {
        *label = usize::from(digit(value, 1, CONTEXT)?);
    }
    let view = DiscreteMatRef::new(&labels, ROW_COUNT, 1)?;
    let result = discrete_sxpid2_averaged(view, view, view)?;
    Ok(result.red.net_nats())
}

fn observe_indices(rows: &[f64]) -> PidResult<f64> {
    const CONTEXT: &str = "bootstrap row-index observer";
    check_row_count(rows, CONTEXT)?;
    let mut packed = 0u8;
    for &value in rows {
        packed = (packed << 2) | digit(value, 3, CONTEXT)?;
    }
    Ok(f64::from(packed))
}

fn scalar_declaration(
    mut bound: ResourceEstimate,
    local_storage_bytes: usize,
) -> StatisticCallbackDeclaration {
    // Both callbacks check the slice length and scan four values. Allow 16 operations per
    // row for iteration, finite/alphabet checks, conversion and storage or bit packing.
    // The fixed allowance covers setup, matrix validation or packing setup, and return.
    bound.operations_hint += 32 + 16 * ROW_COUNT as u128;
    // In addition to the named local objects, allow space for the slice, iterators, scalar
    // temporaries, and transient validation results. The supplied bound retains its pair count.
    bound.estimated_bytes += 512 + local_storage_bytes as u128;
    StatisticCallbackDeclaration::scalar(bound)
}

fn observe_mask(mask: u8, config: &BootstrapConfig) -> PidResult<BootstrapResult> {
    let labels: [usize; ROW_COUNT] = std::array::from_fn(|row| usize::from((mask >> row) & 1));
    let view = DiscreteMatRef::new(&labels, ROW_COUNT, 1)?;
    let bound = discrete_sxpid2_resource_estimate(view, view, view, false)?;
    let local_storage_bytes = size_of::<[usize; ROW_COUNT]>()
        + size_of::<DiscreteMatRef<'_>>()
        + size_of::<PidResult<DiscreteSxPid2Result>>();
    let declaration = scalar_declaration(bound, local_storage_bytes);
    let data = labels.map(|label| label as f64);
    block_bootstrap(&data, config, declaration, copy_redundancy)
}

fn bits(value: f64) -> String {
    format!("{:016x}", value.to_bits())
}

fn outcome(result: PidResult<BootstrapResult>) -> io::Result<Value> {
    let report = match result {
        Ok(report) => report,
        Err(error) => {
            return Ok(json!({"kind": "error", "error_debug": format!("{error:?}")}));
        }
    };
    let provenance = report.provenance;
    let mut replicates = Vec::with_capacity(report.replicates.len());
    for replicate in report.replicates {
        let index = replicate.replicate_index;
        let entry = match replicate.status {
            BootstrapReplicateStatus::Complete { value } => {
                json!({"index": index, "value_bits": bits(value)})
            }
            BootstrapReplicateStatus::Failed { error } => {
                json!({"index": index, "error_debug": format!("{error:?}")})
            }
            // A new status in a different pid-core revision needs a new wire contract.
            _ => {
                return Err(io::Error::new(
                    io::ErrorKind::InvalidData,
                    "unknown replicate status",
                ));
            }
        };
        replicates.push(entry);
    }
    let summary = report.summary.map(|value| {
        json!({
            "mean_bits": bits(value.resample_mean),
            "std_bits": bits(value.resample_standard_deviation),
            "lower_bits": bits(value.percentile_lower),
            "upper_bits": bits(value.percentile_upper),
        })
    });
    Ok(json!({
        "kind": "report",
        "provenance": {
            "original_row_count": provenance.original_row_count,
            "requested_replicates": provenance.requested_replicates,
            "block_size": provenance.block_size,
            "seed": provenance.seed,
            "algorithm_revision": format!("{:?}", provenance.algorithm_revision),
            "dependence": format!("{:?}", provenance.validity.dependence),
            "block_length_selection": format!("{:?}", provenance.validity.block_length_selection),
        },
        "point_bits": bits(report.point_estimate),
        "summary": summary,
        "replicates": replicates,
    }))
}

fn main() -> Result<(), Box<dyn Error>> {
    let validity =
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori);
    let alpha = f64::from_bits(0x3fa9_9999_9999_999a);
    let config = BootstrapConfig::new(200, 1, 7, alpha, validity)?;
    let row_ids: [f64; ROW_COUNT] = [0.0, 1.0, 2.0, 3.0];
    let observer_cost = scalar_declaration(ResourceEstimate::ZERO, size_of::<u8>());
    let schedule = outcome(block_bootstrap(
        &row_ids,
        &config,
        observer_cost,
        observe_indices,
    ))?;
    let mut rows = Vec::with_capacity(1 << ROW_COUNT);
    for mask in 0u8..(1u8 << ROW_COUNT) {
        let observed = outcome(observe_mask(mask, &config))?;
        rows.push(json!({"mask": mask, "outcome": observed}));
    }
    let document = json!({
        "schema": "pid-copy-bootstrap-observation-v2",
        "configuration": {
            "n": row_ids.len(),
            "replicates": config.n_boot,
            "block_size": config.block_size,
            "seed": config.seed,
            "alpha_bits": bits(config.alpha),
            "algorithm_revision": format!("{:?}", BlockResamplingAlgorithmRevision::V1),
            "dependence": format!("{:?}", config.validity.dependence),
            "block_length_selection": format!("{:?}", config.validity.block_length_selection),
        },
        "schedule": schedule,
        "rows": rows,
    });
    let bytes = serde_json::to_vec(&document)?;
    if bytes.len() > OUTPUT_LIMIT {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "observation exceeds byte limit")
            .into());
    }
    let mut stdout = io::stdout().lock();
    stdout.write_all(&bytes)?;
    stdout.flush()?;
    Ok(())
}
