use crate::error::{PidError, PidResult};

#[derive(Clone, Copy, Debug)]
pub struct MatRef<'a> {
    data: &'a [f64],
    nrows: usize,
    ncols: usize,
}

impl<'a> MatRef<'a> {
    pub fn new(data: &'a [f64], nrows: usize, ncols: usize) -> PidResult<Self> {
        let expected_len = nrows.saturating_mul(ncols);
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
        debug_assert!(i < self.nrows);
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
        let expected_len = nrows.saturating_mul(ncols);
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

    let mut out = Vec::with_capacity(out_len);
    for i in 0..n {
        out.extend_from_slice(a.row(i));
        out.extend_from_slice(b.row(i));
    }
    MatOwned::new(out, n, out_cols)
}
