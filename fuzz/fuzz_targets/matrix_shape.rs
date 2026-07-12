#![no_main]

mod common;

use libfuzzer_sys::fuzz_target;
use pid_core::{
    concat_horiz_with_budget, DiscreteMatOwned, DiscreteMatRef, MatOwned, MatRef, ResourceBudget,
};

fuzz_target!(|data: &[u8]| {
    let values = common::finite_values(data, 128);
    let labels = common::categorical_values(data, 128);
    let (rows, columns) = common::dimensions(data, values.len());
    let shape_rows = if data.get(2).is_some_and(|byte| byte & 1 == 1) {
        usize::MAX
    } else {
        rows
    };
    let shape_columns = if data.get(2).is_some_and(|byte| byte & 2 == 2) {
        usize::MAX
    } else {
        columns
    };

    let _ = MatRef::new(&values, shape_rows, shape_columns);
    let _ = MatOwned::new(values.clone(), shape_rows, shape_columns);
    let _ = DiscreteMatRef::new(&labels, shape_rows, shape_columns);
    let _ = DiscreteMatOwned::new(labels, shape_rows, shape_columns);

    if let Ok(matrix) = MatRef::new(&values, rows, columns) {
        let _ = matrix.checked_row(rows);
        let mut budget = ResourceBudget::default();
        budget.max_bytes = u64::from(data.get(3).copied().unwrap_or(1)).max(1);
        budget.max_pairwise_distances = 256;
        budget.max_operations_hint = 256;
        budget.max_threads = 1;
        let _ = concat_horiz_with_budget(matrix, matrix, budget);
    }
});
