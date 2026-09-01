#!/usr/bin/env bash
set -euo pipefail

# This is an execution-environment preflight, not tool authenticity evidence
# or an atomic binding of the probe to a later process.
# Exact output is required because cargo-deny 0.19 and 0.20 place common CLI
# options differently. Accepting a nearby version can therefore defer a
# deterministic grammar failure until late in a release audit.
readonly expected_version="cargo-deny 0.20.2"
readonly install_command="cargo install cargo-deny --locked --version 0.20.2 --force"

print_guidance() {
    printf 'pid-rs requires exactly %s for cargo-deny gates.\n' "$expected_version" >&2
    printf 'Install it with: %s\n' "$install_command" >&2
    printf 'The gate probes the literal cargo deny command used by the recipes.\n' >&2
    printf 'Cargo can resolve that subcommand from the effective CARGO_HOME/bin before a PATH-first copy.\n' >&2
    printf 'Install into the effective Cargo home, or set CARGO_HOME to one whose bin/cargo-deny is 0.20.2.\n' >&2
    printf 'Then confirm that cargo deny --version prints exactly %s.\n' "$expected_version" >&2
}

if ! command -v cargo >/dev/null 2>&1; then
    printf 'cargo-deny toolchain preflight failed: cargo is not available on PATH.\n' >&2
    print_guidance
    exit 1
fi

umask 077
probe_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-cargo-deny-version.XXXXXX")"
trap 'rm -rf -- "$probe_root"' EXIT
probe_stdout="$probe_root/stdout"
probe_stderr="$probe_root/stderr"
expected_stdout="$probe_root/expected"
printf '%s\n' "$expected_version" >"$expected_stdout"

set +e
cargo deny --version >"$probe_stdout" 2>"$probe_stderr"
probe_status=$?
set -e

if [[ "$probe_status" -ne 0 ]]; then
    printf 'cargo-deny toolchain preflight failed: cargo deny --version exited with status %s.\n' \
        "$probe_status" >&2
    if [[ -s "$probe_stdout" ]]; then
        printf 'Probe standard output follows:\n%s\n' "$(<"$probe_stdout")" >&2
    fi
    if [[ -s "$probe_stderr" ]]; then
        printf 'Probe standard error follows:\n%s\n' "$(<"$probe_stderr")" >&2
    fi
    print_guidance
    exit 1
fi

if ! cmp -s "$expected_stdout" "$probe_stdout" || [[ -s "$probe_stderr" ]]; then
    printf 'cargo-deny toolchain preflight failed: expected one exact %s line on standard output and empty standard error.\n' \
        "$expected_version" >&2
    if [[ -s "$probe_stdout" ]]; then
        printf 'Observed standard output follows:\n%s\n' "$(<"$probe_stdout")" >&2
    else
        printf 'Observed standard output was empty.\n' >&2
    fi
    if [[ -s "$probe_stderr" ]]; then
        printf 'Observed standard error follows:\n%s\n' "$(<"$probe_stderr")" >&2
    fi
    print_guidance
    exit 1
fi

printf 'cargo-deny toolchain preflight passed: %s\n' "$expected_version"
