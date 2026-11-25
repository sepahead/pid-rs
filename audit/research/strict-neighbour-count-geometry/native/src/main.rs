use pid_core::experimental::continuous::{isx_redundancy_report, IsxConfig, IsxProvenance};
use pid_core::{MatRef, PidError, ResourceBudget};
use serde_json::json;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let first = [0.0, 2.0, 33.0, 19.0, 41.0];
    let second = [0.0, 26.0, 5.0, 27.0, 22.0];
    let target = [0.0, 3.0, 10.0, 2.0, 7.0];
    let first = MatRef::new(&first, 5, 1)?;
    let second = MatRef::new(&second, 5, 1)?;
    let target = MatRef::new(&target, 5, 1)?;
    let mut config = IsxConfig::assume_regular_full_dimensional();
    config.k = 2;
    let provenance = IsxProvenance::new(
        "Scalar, identity, common raw numerical scale",
        "Scalar, identity, common raw numerical scale",
        "Scalar target, identity",
        "Fixed integer observations for the two-arm strict-count check",
        "The open neighborhoods can occur in five independent draws from a trivariate standard normal density",
        None,
        None,
    )?;
    let call = |cfg: &IsxConfig| {
        isx_redundancy_report(first, second, target, cfg, &provenance, ResourceBudget::default())
    };
    let report = call(&config)?;
    let mut missing = IsxConfig::default();
    missing.k = 2;
    let support_error = call(&missing);
    config.k = 0;
    let k_error = call(&config);
    println!("{}", json!({
        "n": report.n_samples,
        "k": report.k,
        "mean_nats": report.estimate_nats,
        "diagnostics": report.local_diagnostics,
        "bad_support": matches!(support_error, Err(PidError::SupportContractRequired { .. })),
        "bad_k": matches!(k_error, Err(PidError::InvalidK { .. }))
    }));
    Ok(())
}
