#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
checker="$repo_root/scripts/check-cargo-deny-toolchain.sh"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-cargo-deny-preflight.XXXXXX")"
trap 'rm -rf -- "$test_root"' EXIT

mkdir -p "$test_root/bin" "$test_root/empty"
fake_cargo="$test_root/bin/cargo"

cat >"$fake_cargo" <<'FAKE_CARGO'
#!/bin/sh
if [ "$#" -ne 2 ] || [ "$1" != "deny" ] || [ "$2" != "--version" ]; then
    printf 'unexpected fake cargo arguments\n' >&2
    exit 97
fi

case "${PID_RS_FAKE_CARGO_CASE:-}" in
    exact)
        printf 'cargo-deny 0.20.2\n'
        ;;
    old)
        printf 'cargo-deny 0.19.9\n'
        ;;
    nearby)
        printf 'cargo-deny 0.20.1\n'
        ;;
    suffix)
        printf 'cargo-deny 0.20.2-custom\n'
        ;;
    malformed)
        printf 'cargo-deny v0.20.2\n'
        ;;
    multiline)
        printf 'cargo-deny 0.20.2\nunexpected second line\n'
        ;;
    blankline)
        printf 'cargo-deny 0.20.2\n\n'
        ;;
    stderr)
        printf 'cargo-deny 0.20.2\n'
        printf 'unexpected warning\n' >&2
        ;;
    failure)
        printf 'synthetic version-probe failure\n' >&2
        exit 7
        ;;
    *)
        printf 'unknown fake cargo case\n' >&2
        exit 98
        ;;
esac
FAKE_CARGO
chmod 0755 "$fake_cargo"

case_count=0

expect_accept() {
    local case_name="$1"
    local output
    output="$(
        PATH="$test_root/bin:/usr/bin:/bin" \
            PID_RS_FAKE_CARGO_CASE="$case_name" \
            /bin/bash "$checker" 2>&1
    )"
    if [[ "$output" != "cargo-deny toolchain preflight passed: cargo-deny 0.20.2" ]]; then
        printf 'positive case %s returned unexpected output:\n%s\n' "$case_name" "$output" >&2
        exit 1
    fi
    case_count=$((case_count + 1))
}

expect_reject() {
    local case_name="$1"
    local required_fragment="$2"
    local output probe_status
    set +e
    output="$(
        PATH="$test_root/bin:/usr/bin:/bin" \
            PID_RS_FAKE_CARGO_CASE="$case_name" \
            /bin/bash "$checker" 2>&1
    )"
    probe_status=$?
    set -e
    if [[ "$probe_status" -eq 0 ]]; then
        printf 'negative case %s was accepted:\n%s\n' "$case_name" "$output" >&2
        exit 1
    fi
    if [[ "$output" != *"$required_fragment"* ]] || \
        [[ "$output" != *"cargo install cargo-deny --locked --version 0.20.2 --force"* ]]; then
        printf 'negative case %s omitted its diagnostic contract:\n%s\n' \
            "$case_name" "$output" >&2
        exit 1
    fi
    case_count=$((case_count + 1))
}

expect_accept exact
expect_reject old 'cargo-deny 0.19.9'
expect_reject nearby 'cargo-deny 0.20.1'
expect_reject suffix 'cargo-deny 0.20.2-custom'
expect_reject malformed 'cargo-deny v0.20.2'
expect_reject multiline 'unexpected second line'
expect_reject blankline 'expected one exact'
expect_reject stderr 'unexpected warning'
expect_reject failure 'exited with status 7'

set +e
missing_output="$(PATH="$test_root/empty" /bin/bash "$checker" 2>&1)"
missing_status=$?
set -e
if [[ "$missing_status" -eq 0 ]] || \
    [[ "$missing_output" != *'cargo is not available on PATH'* ]] || \
    [[ "$missing_output" != *'cargo install cargo-deny --locked --version 0.20.2 --force'* ]]; then
    printf 'missing-cargo case violated its diagnostic contract:\n%s\n' "$missing_output" >&2
    exit 1
fi
case_count=$((case_count + 1))

# Exercise Cargo's real external-subcommand resolution instead of only the fake
# cargo dispatcher above.  A cargo-deny binary that is first on PATH can still
# be shadowed by the plugin in the effective CARGO_HOME/bin.  The production
# checker must follow the literal `cargo deny` command that the recipes later
# run, so the old effective-home plugin is a required rejection.
real_cargo="$(command -v cargo)"
real_cargo_directory="$(cd "$(dirname "$real_cargo")" && pwd -P)"
resolution_root="$test_root/subcommand-resolution"
path_exact="$resolution_root/path-exact"
path_old="$resolution_root/path-old"
home_exact="$resolution_root/home-exact"
home_old="$resolution_root/home-old"
mkdir -p "$path_exact" "$path_old" "$home_exact/bin" "$home_old/bin"

make_version_plugin() {
    local destination="$1"
    local version="$2"
    printf '%s\n' \
        '#!/bin/sh' \
        "printf '%s\\n' 'cargo-deny $version'" \
        >"$destination"
    chmod 0755 "$destination"
}

make_version_plugin "$path_exact/cargo-deny" 0.20.2
make_version_plugin "$path_old/cargo-deny" 0.19.9
make_version_plugin "$home_exact/bin/cargo-deny" 0.20.2
make_version_plugin "$home_old/bin/cargo-deny" 0.19.9

set +e
shadowed_output="$(
    CARGO_HOME="$home_old" \
        PATH="$path_exact:$real_cargo_directory:/usr/bin:/bin" \
        /bin/bash "$checker" 2>&1
)"
shadowed_status=$?
set -e
if [[ "$shadowed_status" -eq 0 ]] || \
    [[ "$shadowed_output" != *'cargo-deny 0.19.9'* ]] || \
    [[ "$shadowed_output" != *'effective CARGO_HOME/bin'* ]] || \
    [[ "$shadowed_output" != *'cargo deny --version prints exactly cargo-deny 0.20.2'* ]]; then
    printf 'PATH-first exact plugin was not rejected when the effective Cargo home supplied 0.19.9:\n%s\n' \
        "$shadowed_output" >&2
    exit 1
fi
case_count=$((case_count + 1))

effective_home_output="$(
    CARGO_HOME="$home_exact" \
        PATH="$path_old:$real_cargo_directory:/usr/bin:/bin" \
        /bin/bash "$checker" 2>&1
)"
if [[ "$effective_home_output" != \
    'cargo-deny toolchain preflight passed: cargo-deny 0.20.2' ]]; then
    printf 'effective Cargo-home exact plugin returned unexpected output:\n%s\n' \
        "$effective_home_output" >&2
    exit 1
fi
case_count=$((case_count + 1))

printf 'cargo-deny toolchain preflight self-test passed: %s cases\n' "$case_count"
