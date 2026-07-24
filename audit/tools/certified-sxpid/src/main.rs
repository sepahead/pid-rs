use std::ffi::OsString;
use std::fs::File;
use std::io::{self, Read, Write};
use std::path::Path;

use pid_certified_sxpid::{certify_sxpid2, CertError, FailureEnvelope, MAX_INPUT_BYTES};
use serde::Serialize;

fn main() {
    let result = run();
    let exit_code = match result {
        Ok(certificate) => match emit_json(&certificate) {
            Ok(()) => 0,
            Err(message) => {
                let _ = writeln!(io::stderr().lock(), "{message}");
                1
            }
        },
        Err(error) => {
            let exit_code = if error.is_precision_limit() { 3 } else { 2 };
            if let Err(message) = emit_json(&FailureEnvelope::from_error(&error)) {
                let _ = writeln!(io::stderr().lock(), "{message}");
                std::process::exit(1);
            }
            exit_code
        }
    };
    std::process::exit(exit_code);
}

fn run() -> Result<pid_certified_sxpid::CertificateEnvelope, CertError> {
    let input_path = parse_input_path(std::env::args_os().skip(1))?;
    let input = read_bounded(&input_path)?;
    certify_sxpid2(&input)
}

fn parse_input_path(mut arguments: impl Iterator<Item = OsString>) -> Result<OsString, CertError> {
    let input_path = arguments.next().ok_or_else(|| {
        CertError::usage("usage: pid-certified-sxpid INPUT.json (use '-' for standard input)")
    })?;
    if arguments.next().is_some() {
        return Err(CertError::usage(
            "exactly one input path is required; use '-' for standard input",
        ));
    }
    Ok(input_path)
}

fn read_bounded(input_path: &OsString) -> Result<Vec<u8>, CertError> {
    let byte_limit = u64::try_from(MAX_INPUT_BYTES)
        .map_err(|_| CertError::input_io("input byte limit is not representable as u64"))?;
    let read_limit = byte_limit
        .checked_add(1)
        .ok_or_else(|| CertError::input_io("input byte limit overflow"))?;
    let mut bytes = Vec::new();

    if input_path == "-" {
        io::stdin()
            .lock()
            .take(read_limit)
            .read_to_end(&mut bytes)
            .map_err(|error| CertError::input_io(format!("cannot read standard input: {error}")))?;
    } else {
        let path = Path::new(input_path);
        let file = File::open(path).map_err(|error| {
            CertError::input_io(format!(
                "cannot open input '{}': {error}",
                path.to_string_lossy()
            ))
        })?;
        file.take(read_limit)
            .read_to_end(&mut bytes)
            .map_err(|error| {
                CertError::input_io(format!(
                    "cannot read input '{}': {error}",
                    path.to_string_lossy()
                ))
            })?;
    }

    if bytes.len() > MAX_INPUT_BYTES {
        return Err(CertError::input_io(format!(
            "input exceeds the {MAX_INPUT_BYTES}-byte resource limit"
        )));
    }
    Ok(bytes)
}

fn emit_json(value: &impl Serialize) -> Result<(), String> {
    let stdout = io::stdout();
    let mut output = stdout.lock();
    serde_json::to_writer(&mut output, value)
        .map_err(|error| format!("cannot serialize result envelope: {error}"))?;
    output
        .write_all(b"\n")
        .map_err(|error| format!("cannot write result envelope: {error}"))
}
