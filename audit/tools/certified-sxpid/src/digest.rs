use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

use crate::error::CertError;

pub(crate) fn sha256_hex(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    lower_hex(&digest.finalize())
}

pub(crate) fn canonical_json_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>, CertError> {
    let tree = serde_json::to_value(value).map_err(|error| {
        CertError::internal(format!("canonical JSON value conversion failed: {error}"))
    })?;
    serde_json::to_vec(&sort_object_keys(tree)).map_err(|error| {
        CertError::internal(format!("canonical JSON serialization failed: {error}"))
    })
}

pub(crate) fn canonical_digest<T: Serialize>(value: &T) -> Result<String, CertError> {
    canonical_json_bytes(value).map(|bytes| sha256_hex(&bytes))
}

pub(crate) fn manifest_digest(files: &[(&str, &[u8])]) -> Result<String, CertError> {
    let mut digest = Sha256::new();
    digest.update(b"pid-certified-sxpid-source-manifest-v1\0");
    for (path, bytes) in files {
        let path_len = u64::try_from(path.len())
            .map_err(|_| CertError::internal("source-manifest path length exceeds u64"))?;
        let byte_len = u64::try_from(bytes.len())
            .map_err(|_| CertError::internal("source-manifest file length exceeds u64"))?;
        digest.update(path_len.to_be_bytes());
        digest.update(path.as_bytes());
        digest.update(byte_len.to_be_bytes());
        digest.update(bytes);
    }
    Ok(lower_hex(&digest.finalize()))
}

fn lower_hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn sort_object_keys(value: Value) -> Value {
    match value {
        Value::Array(values) => Value::Array(values.into_iter().map(sort_object_keys).collect()),
        Value::Object(values) => {
            let mut entries = values.into_iter().collect::<Vec<_>>();
            entries.sort_unstable_by(|left, right| left.0.cmp(&right.0));
            let mut sorted = Map::new();
            for (key, value) in entries {
                sorted.insert(key, sort_object_keys(value));
            }
            Value::Object(sorted)
        }
        scalar => scalar,
    }
}

#[cfg(test)]
mod tests {
    use serde::Serialize;
    use serde_json::json;

    use super::{canonical_json_bytes, manifest_digest};

    #[derive(Serialize)]
    struct ReverseDeclarationOrder {
        zeta: u8,
        alpha: u8,
    }

    #[test]
    fn canonical_json_should_sort_object_keys_recursively() {
        let declared = ReverseDeclarationOrder { zeta: 2, alpha: 1 };
        let reordered = json!({"alpha": 1, "zeta": 2});

        assert_eq!(
            canonical_json_bytes(&declared).expect("canonical declared object"),
            canonical_json_bytes(&reordered).expect("canonical reordered object")
        );
        assert_eq!(
            canonical_json_bytes(&declared).expect("canonical object"),
            br#"{"alpha":1,"zeta":2}"#
        );
    }

    #[test]
    fn manifest_digest_should_bind_path_boundaries_and_file_boundaries() {
        let first = manifest_digest(&[("ab", b"c"), ("d", b"ef")]).expect("first manifest");
        let second = manifest_digest(&[("a", b"bc"), ("de", b"f")]).expect("second manifest");

        assert_ne!(first, second);
    }
}
