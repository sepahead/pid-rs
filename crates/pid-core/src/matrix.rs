use crate::error::{PidError, PidResult};
use crate::resource::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};

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

    /// Borrow the complete row-major buffer.
    #[inline]
    pub fn as_slice(&self) -> &'a [f64] {
        self.data
    }

    #[inline]
    /// Return row `i`.
    ///
    /// # Panics
    ///
    /// Panics when `i >= self.nrows()`.
    pub fn row(&self, i: usize) -> &'a [f64] {
        assert!(i < self.nrows, "row index out of bounds");
        let start = i * self.ncols;
        &self.data[start..start + self.ncols]
    }

    /// Return row `i`, or `None` when it is outside the matrix.
    #[inline]
    pub fn checked_row(&self, i: usize) -> Option<&'a [f64]> {
        if i >= self.nrows {
            return None;
        }
        let start = i * self.ncols;
        Some(&self.data[start..start + self.ncols])
    }
}

#[derive(Debug)]
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

    /// Preflight copying this matrix's backing buffer.
    pub fn try_clone_resource_estimate(&self) -> PidResult<ResourceEstimate> {
        ResourceEstimate::contiguous::<f64>("MatOwned::try_clone_with_budget", self.data.len())
    }

    /// Fallibly copy this owned matrix under an explicit resource ceiling.
    ///
    /// `MatOwned` deliberately does not implement [`Clone`]: its backing buffer is externally
    /// sized, while `Clone::clone` cannot report allocation failure or enforce a budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        budget.check(
            "MatOwned::try_clone_with_budget",
            self.try_clone_resource_estimate()?,
        )?;
        let mut data =
            try_vec_with_capacity("MatOwned::try_clone_with_budget", self.data.len(), budget)?;
        data.extend_from_slice(&self.data);
        Self::new(data, self.nrows, self.ncols)
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

    /// Return sample row `i`, or `None` when it is outside the matrix.
    #[inline]
    pub fn checked_row(&self, i: usize) -> Option<&'a [usize]> {
        if i >= self.nrows {
            return None;
        }
        let start = i * self.ncols;
        Some(&self.data[start..start + self.ncols])
    }
}

/// Owned row-major matrix of categorical state labels.
#[derive(Debug, PartialEq, Eq)]
pub struct DiscreteMatOwned {
    data: Vec<usize>,
    nrows: usize,
    ncols: usize,
}

impl DiscreteMatOwned {
    /// Construct an owned categorical matrix, validating its shape.
    pub fn new(data: Vec<usize>, nrows: usize, ncols: usize) -> PidResult<Self> {
        let expected_len = nrows.checked_mul(ncols).ok_or(PidError::SizeOverflow {
            operation: "DiscreteMatOwned::new",
        })?;
        if data.len() != expected_len {
            return Err(PidError::ShapeMismatch {
                context: "DiscreteMatOwned::new",
                expected_len,
                actual_len: data.len(),
            });
        }
        Ok(Self { data, nrows, ncols })
    }

    /// Borrow the matrix without copying.
    pub fn as_ref(&self) -> DiscreteMatRef<'_> {
        DiscreteMatRef {
            data: &self.data,
            nrows: self.nrows,
            ncols: self.ncols,
        }
    }

    /// Borrow the row-major labels.
    pub fn data(&self) -> &[usize] {
        &self.data
    }

    pub fn nrows(&self) -> usize {
        self.nrows
    }

    pub fn ncols(&self) -> usize {
        self.ncols
    }

    /// Preflight copying this categorical matrix's backing labels.
    pub fn try_clone_resource_estimate(&self) -> PidResult<ResourceEstimate> {
        ResourceEstimate::contiguous::<usize>(
            "DiscreteMatOwned::try_clone_with_budget",
            self.data.len(),
        )
    }

    /// Fallibly copy this categorical matrix under an explicit resource ceiling.
    ///
    /// The ordinary [`Clone`] trait is intentionally absent because the label buffer is
    /// externally sized and copying it must preserve the crate's structured allocation contract.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        budget.check(
            "DiscreteMatOwned::try_clone_with_budget",
            self.try_clone_resource_estimate()?,
        )?;
        let mut data = try_vec_with_capacity(
            "DiscreteMatOwned::try_clone_with_budget",
            self.data.len(),
            budget,
        )?;
        data.extend_from_slice(&self.data);
        Self::new(data, self.nrows, self.ncols)
    }
}

pub fn concat_horiz(a: MatRef<'_>, b: MatRef<'_>) -> PidResult<MatOwned> {
    concat_horiz_with_budget(a, b, ResourceBudget::default())
}

/// Horizontally concatenate two matrices under an explicit memory/operation budget.
pub fn concat_horiz_with_budget(
    a: MatRef<'_>,
    b: MatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<MatOwned> {
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

    budget.check(
        "concat_horiz",
        ResourceEstimate {
            estimated_bytes: (out_len as u128) * std::mem::size_of::<f64>() as u128,
            pairwise_distances: 0,
            operations_hint: out_len as u128,
        },
    )?;
    let mut out = try_vec_with_capacity("concat_horiz", out_len, budget)?;
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

    #[test]
    fn owned_matrix_copy_is_fallible_and_budgeted() {
        let matrix = MatOwned::new(vec![1.0, 2.0], 2, 1).unwrap();
        let tiny = ResourceBudget {
            max_bytes: 15,
            ..ResourceBudget::default()
        };

        assert!(matches!(
            matrix.try_clone_with_budget(tiny),
            Err(PidError::ResourceLimitExceeded {
                resource: "bytes",
                requested: 16,
                limit: 15,
                ..
            })
        ));
        let copied = matrix
            .try_clone_with_budget(ResourceBudget::default())
            .unwrap();
        assert_eq!(copied.as_ref().as_slice(), matrix.as_ref().as_slice());
    }

    #[test]
    fn categorical_owned_matrix_copy_is_fallible_and_budgeted() {
        let matrix = DiscreteMatOwned::new(vec![1, 2], 2, 1).unwrap();
        let tiny = ResourceBudget {
            max_bytes: (2 * std::mem::size_of::<usize>() - 1) as u64,
            ..ResourceBudget::default()
        };

        assert!(matches!(
            matrix.try_clone_with_budget(tiny),
            Err(PidError::ResourceLimitExceeded {
                resource: "bytes",
                ..
            })
        ));
        let copied = matrix
            .try_clone_with_budget(ResourceBudget::default())
            .unwrap();
        assert_eq!(copied, matrix);
    }
}
