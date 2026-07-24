use std::env;
use std::process::Command;

const BUILD_CONTEXT_SCHEMA: &str = "pid-rs/certified-sxpid-build-context/v1";
const MAX_RUSTC_VERSION_BYTES: usize = 8192;

fn main() {
    for name in [
        "RUSTC",
        "HOST",
        "TARGET",
        "PROFILE",
        "OPT_LEVEL",
        "DEBUG",
        "GMP_MPFR_SYS_CACHE",
    ] {
        println!("cargo::rerun-if-env-changed={name}");
    }

    let rustc = env::var_os("RUSTC").expect("Cargo must provide RUSTC to the build script");
    let output = Command::new(rustc)
        .arg("-vV")
        .output()
        .expect("the configured Rust compiler must answer rustc -vV");
    assert!(
        output.status.success(),
        "the configured Rust compiler rejected rustc -vV"
    );
    assert!(
        output.stdout.len() <= MAX_RUSTC_VERSION_BYTES,
        "rustc -vV output exceeded the bounded build-evidence limit"
    );
    let verbose_version =
        String::from_utf8(output.stdout).expect("rustc -vV output must be valid UTF-8");

    emit("PID_CERTIFIER_BUILD_CONTEXT_SCHEMA", BUILD_CONTEXT_SCHEMA);
    emit(
        "PID_CERTIFIER_RUSTC_VERBOSE_VERSION",
        &single_line(&verbose_version),
    );
    emit_required("PID_CERTIFIER_BUILD_HOST", "HOST");
    emit_required("PID_CERTIFIER_BUILD_TARGET", "TARGET");
    emit_required("PID_CERTIFIER_BUILD_PROFILE", "PROFILE");
    emit_required("PID_CERTIFIER_BUILD_OPT_LEVEL", "OPT_LEVEL");
    emit_required("PID_CERTIFIER_BUILD_DEBUG", "DEBUG");
    emit(
        "PID_CERTIFIER_NATIVE_CACHE_POLICY",
        if env::var_os("GMP_MPFR_SYS_CACHE").is_some() {
            "explicit_gmp_mpfr_sys_cache_present_path_not_recorded"
        } else {
            "default_gmp_mpfr_sys_cache_selection"
        },
    );
}

fn emit_required(output_name: &str, input_name: &str) {
    let value = env::var(input_name)
        .unwrap_or_else(|_| panic!("Cargo must provide {input_name} to the build script"));
    emit(output_name, &single_line(&value));
}

fn emit(name: &str, value: &str) {
    assert!(
        !value.is_empty() && !value.contains('\0') && !value.contains('\n'),
        "build-evidence value must be nonempty and single-line"
    );
    println!("cargo::rustc-env={name}={value}");
}

fn single_line(value: &str) -> String {
    value
        .trim()
        .chars()
        .map(|character| {
            if character == '\n' || character == '\r' {
                '|'
            } else if character.is_control() {
                '?'
            } else {
                character
            }
        })
        .collect()
}
