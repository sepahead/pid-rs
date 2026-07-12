#![allow(dead_code)]

pub fn finite_values(data: &[u8], maximum: usize) -> Vec<f64> {
    data.chunks_exact(8)
        .take(maximum)
        .map(|chunk| {
            let mut bytes = [0_u8; 8];
            bytes.copy_from_slice(chunk);
            f64::from_bits(u64::from_le_bytes(bytes))
        })
        .filter(|value| value.is_finite())
        .collect()
}

pub fn categorical_values(data: &[u8], maximum: usize) -> Vec<usize> {
    data.iter()
        .take(maximum)
        .map(|value| usize::from(*value))
        .collect()
}

pub fn dimensions(data: &[u8], len: usize) -> (usize, usize) {
    let rows = data.first().map_or(0, |value| usize::from(*value % 17));
    let columns = data.get(1).map_or(0, |value| usize::from(*value % 5));
    if rows.checked_mul(columns) == Some(len) {
        (rows, columns)
    } else if len == 0 {
        (rows, 0)
    } else {
        (1, len)
    }
}
