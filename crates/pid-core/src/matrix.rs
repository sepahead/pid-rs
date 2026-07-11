use crate::error::{PidError, PidResult};

#[derive(Clone, Copy, Debug)]
pub struct MatRef<'a> {
    data: &'a [f64],
    nrows: usize,
    ncols: usize,
}

impl<'a> MatRef<'a> {
    pub fn new(data: &'a [f64], nrows: usize, ncols: usize) -> PidResult<Self> {
        let expected_len = nrows.checked_mul(ncols).ok_or(PidError::InvalidConfig {
            context: "MatRef::new",
            message: "matrix size overflow",
        })?;
        if data.len() != expected_len {
            return Err(PidError::ShapeMismatch {
                context: "MatRef::new",
                expected_len,
                actual_len: data.len(),
            });
        }
        if data.iter().any(|v| !v.is_finite()) {
            return Err(PidError::NonFiniteInput {
                context: "MatRef::new",
            });
        }
        Ok(Self { data, nrows, ncols })
    }

    #[inline]
    pub fn nrows(&self) -> usize {
        self.nrows
    }

    #[inline]
    pub fn ncols(&self) -> usize {
        self.ncols
    }

    #[inline]
    pub fn row(&self, i: usize) -> &'a [f64] {
        assert!(i < self.nrows, "row index out of bounds");
        let start = i * self.ncols;
        &self.data[start..start + self.ncols]
    }
}

#[derive(Clone, Debug)]
pub struct MatOwned {
    data: Vec<f64>,
    nrows: usize,
    ncols: usize,
}

impl MatOwned {
    pub fn new(data: Vec<f64>, nrows: usize, ncols: usize) -> PidResult<Self> {
        let expected_len = nrows.checked_mul(ncols).ok_or(PidError::InvalidConfig {
            context: "MatOwned::new",
            message: "matrix size overflow",
        })?;
        if data.len() != expected_len {
            return Err(PidError::ShapeMismatch {
                context: "MatOwned::new",
                expected_len,
                actual_len: data.len(),
            });
        }
        if data.iter().any(|v| !v.is_finite()) {
            return Err(PidError::NonFiniteInput {
                context: "MatOwned::new",
            });
        }
        Ok(Self { data, nrows, ncols })
    }

    #[inline]
    pub fn as_ref(&self) -> MatRef<'_> {
        MatRef {
            data: &self.data,
            nrows: self.nrows,
            ncols: self.ncols,
        }
    }
}

/// Borrowed row-major matrix of categorical state labels.
///
/// Unlike [`MatRef`], values are not interpreted numerically: only equality of complete rows
/// matters. Sparse and non-monotone labels are therefore valid and a bijective relabeling cannot
/// change a discrete information measure.
#[derive(Clone, Copy, Debug)]
pub struct DiscreteMatRef<'a> {
    data: &'a [usize],
    nrows: usize,
    ncols: usize,
}

impl<'a> DiscreteMatRef<'a> {
    /// Construct a categorical matrix from a row-major label buffer.
    pub fn new(data: &'a [usize], nrows: usize, ncols: usize) -> PidResult<Self> {
        let expected_len = nrows.checked_mul(ncols).ok_or(PidError::InvalidConfig {
            context: "DiscreteMatRef::new",
            message: "matrix size overflow",
        })?;
        if data.len() != expected_len {
            return Err(PidError::ShapeMismatch {
                context: "DiscreteMatRef::new",
                expected_len,
                actual_len: data.len(),
            });
        }
        Ok(Self { data, nrows, ncols })
    }

    /// Number of sample rows.
    #[inline]
    pub fn nrows(&self) -> usize {
        self.nrows
    }

    /// Number of categorical coordinates per sample.
    #[inline]
    pub fn ncols(&self) -> usize {
        self.ncols
    }

    /// Return sample row `i`.
    ///
    /// # Panics
    ///
    /// Panics when `i >= self.nrows()`.
    #[inline]
    pub fn row(&self, i: usize) -> &'a [usize] {
        assert!(i < self.nrows, "row index out of bounds");
        let start = i * self.ncols;
        &self.data[start..start + self.ncols]
    }
}

pub fn concat_horiz(a: MatRef<'_>, b: MatRef<'_>) -> PidResult<MatOwned> {
    if a.nrows() != b.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "concat_horiz",
            left_rows: a.nrows(),
            right_rows: b.nrows(),
        });
    }
    let n = a.nrows();
    let da = a.ncols();
    let db = b.ncols();

    let out_cols = da.checked_add(db).ok_or(PidError::InvalidConfig {
        context: "concat_horiz",
        message: "column count overflow",
    })?;
    let out_len = n.checked_mul(out_cols).ok_or(PidError::InvalidConfig {
        context: "concat_horiz",
        message: "output size overflow",
    })?;

    // A zero-area matrix may carry an arbitrarily large logical row count without backing data.
    // Iterating all of those rows to append empty slices is unnecessary and can turn a valid,
    // constant-size input into effectively unbounded work.
    if out_len == 0 {
        return MatOwned::new(Vec::new(), n, out_cols);
    }

    let mut out = Vec::with_capacity(out_len);
    for i in 0..n {
        out.extend_from_slice(a.row(i));
        out.extend_from_slice(b.row(i));
    }
    MatOwned::new(out, n, out_cols)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[should_panic(expected = "row index out of bounds")]
    fn zero_column_discrete_matrix_still_checks_row_bounds() {
        let matrix = DiscreteMatRef::new(&[], 2, 0).unwrap();
        let _ = matrix.row(2);
    }

    #[test]
    fn matrix_size_overflow_is_rejected() {
        assert!(MatRef::new(&[], usize::MAX, 2).is_err());
        assert!(DiscreteMatRef::new(&[], usize::MAX, 2).is_err());
        assert!(MatOwned::new(Vec::new(), usize::MAX, 2).is_err());
    }

    #[test]
    fn concatenating_zero_area_matrices_is_constant_size_even_with_many_logical_rows() {
        let empty = MatRef::new(&[], usize::MAX, 0).unwrap();

        let joined = concat_horiz(empty, empty).unwrap();

        assert_eq!(joined.as_ref().nrows(), usize::MAX);
        assert_eq!(joined.as_ref().ncols(), 0);
    }
}
