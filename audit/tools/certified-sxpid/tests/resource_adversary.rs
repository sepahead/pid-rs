use pid_certified_sxpid::{certify_sxpid2, MAX_INPUT_BYTES};
use serde::Serialize;
use sha2::{Digest, Sha256};

#[derive(Serialize)]
struct InputDocument {
    schema: &'static str,
    definition_revision: &'static str,
    units: &'static str,
    resource_policy_id: &'static str,
    rows: Vec<InputRow>,
}

#[derive(Serialize)]
struct InputRow {
    source_states: [Vec<String>; 2],
    target_state: Vec<String>,
    count: String,
}

#[test]
fn dense_large_integer_table_should_reject_during_incremental_extraction() {
    let mut state = 0x_6a09_e667_f3bc_c909_u64;
    let mut rows = Vec::with_capacity(64 * 64);
    for source_one in 0..64 {
        for source_two in 0..64 {
            rows.push(InputRow {
                source_states: [
                    vec![format!("s{source_one:02}")],
                    vec![format!("s{source_two:02}")],
                ],
                target_state: vec![format!("t{:02}", (source_one + source_two) % 64)],
                count: deterministic_decimal(&mut state, 850),
            });
        }
    }
    let input = serde_json::to_vec(&InputDocument {
        schema: "pid-rs/categorical-sxpid2-count-table/v1",
        definition_revision: "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1",
        units: "nats",
        resource_policy_id: "sxpid2-certification-default-v1",
        rows,
    })
    .expect("serialize bounded resource adversary");
    assert_eq!(input.len(), 3_768_525);
    assert_eq!(
        lower_hex(&Sha256::digest(&input)),
        "6b560da958f89fd3d21afe4cee0df6c78b3168ee62a02714efd3bb9d62431e60"
    );
    assert!(input.len() < MAX_INPUT_BYTES);

    let error =
        certify_sxpid2(&input).expect_err("dense large-integer expression growth must fail closed");

    assert_eq!(error.code(), "certificate_resource_limit");
    assert_eq!(
        error.message(),
        "cumulative extraction reached 1643 terms; maximum is 1638"
    );
}

fn lower_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for &byte in bytes {
        output.push(char::from(HEX[usize::from(byte >> 4)]));
        output.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    output
}

fn deterministic_decimal(state: &mut u64, digits: usize) -> String {
    let mut output = String::with_capacity(digits);
    output.push(char::from(b'1' + next_digit(state) % 9));
    for _ in 1..digits {
        output.push(char::from(b'0' + next_digit(state)));
    }
    output
}

fn next_digit(state: &mut u64) -> u8 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    (*state % 10) as u8
}
