//! Chebyshev (L∞) kd-tree for exact KSG neighbor queries.
//!
//! Replaces the O(n²·d) brute-force scans in the KSG/i^sx hot loops with a
//! balanced spatial index and pruned queries, **without changing a single
//! output bit**: leaf distances are evaluated with the same scalar fold as
//! [`crate::metric::chebyshev`], the k-th neighbor *value* is selected under
//! the same `total_cmp` order, and range counts use the same inclusive
//! `d <= eps` semantics the callers feed with [`crate::nn::strict_radius`].
//! Ties therefore resolve to identical *values* (the k-th distance and the
//! counts depend only on distance values, not on which tied point is chosen).
//!
//! Error-contract parity: the brute paths surface non-finite coordinates via
//! `Metric::checked_distance` on first touch. A tree *prunes* subtrees, so it
//! could silently skip a NaN a brute scan would have rejected — therefore
//! [`KdTree::build`] pre-scans every coordinate and span and refuses any value
//! whose subtraction could become non-finite, with the same error kind the
//! scalar path uses.
//!
//! Applicability is gated by the caller through [`kdtree_applicable`]: the
//! tree engages only for [`crate::metric::Metric::Chebyshev`] (the standard
//! KSG metric; the hyperbolic metric has no axis-aligned bounding volumes),
//! only above a break-even sample count, and only at low dimensionality —
//! axis-aligned pruning degenerates toward a full scan as `d` grows (curse of
//! dimensionality), where the branch-free brute loop is faster in practice.
//! Queries are typically sublinear on the gated data, but a query is O(n) in
//! the worst case and a full estimator call therefore remains O(n²) worst-case.

use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_filled, try_vec_with_capacity, CancellationToken,
    ResourceBudget, ResourceEstimate,
};

/// Below this many samples the O(n²) loop beats tree build + query overhead.
pub(crate) const KDTREE_MIN_N: usize = 128;
/// Above this joint dimensionality, axis-aligned pruning stops paying for
/// itself and the brute scan is kept.
pub(crate) const KDTREE_MAX_DIMS: usize = 16;

/// Should the kd-tree path be used for this (metric, n, joint dims)?
#[inline]
pub(crate) fn kdtree_applicable(metric: Metric, n: usize, dims: usize) -> bool {
    matches!(metric, Metric::Chebyshev) && n >= KDTREE_MIN_N && dims > 0 && dims <= KDTREE_MAX_DIMS
}

const LEAF_SIZE: usize = 16;

struct Node {
    /// Per-dimension bounding box of the points under this node
    /// (`lo[d] ..= hi[d]`), used for exact Chebyshev pruning.
    lo: Vec<f64>,
    hi: Vec<f64>,
    /// Range into `KdTree::order`.
    start: usize,
    end: usize,
    /// Children indices into `KdTree::nodes` (leaf iff `left == usize::MAX`).
    left: usize,
    right: usize,
}

/// An immutable Chebyshev kd-tree over `n` points of dimension `dims`,
/// assembled from one or more row-aligned blocks (max-over-blocks Chebyshev
/// equals Chebyshev over the concatenation).
pub(crate) struct KdTree {
    dims: usize,
    n: usize,
    /// Row-major `n × dims` copy of the (concatenated) points.
    pts: Vec<f64>,
    /// Permutation of point indices; tree nodes own contiguous subranges.
    order: Vec<u32>,
    nodes: Vec<Node>,
    root: usize,
    budget: ResourceBudget,
}

impl KdTree {
    /// Build over the concatenation of `blocks` (all `n` rows each). Fails on
    /// any non-finite coordinate or coordinate span — mirroring the brute
    /// path's `checked_distance` contract (which would reject a subtraction
    /// that overflows during its full scan).
    #[cfg(any(feature = "experimental-continuous", test))]
    #[cfg(test)]
    pub(crate) fn build(blocks: &[MatRef<'_>]) -> PidResult<Self> {
        Self::build_with_budget(blocks, ResourceBudget::default())
    }

    #[cfg(any(feature = "experimental-continuous", test))]
    pub(crate) fn build_with_budget(
        blocks: &[MatRef<'_>],
        budget: ResourceBudget,
    ) -> PidResult<Self> {
        let cancellation = CancellationToken::new();
        Self::build_with_budget_and_cancellation(blocks, budget, &cancellation)
    }

    pub(crate) fn build_with_budget_and_cancellation(
        blocks: &[MatRef<'_>],
        budget: ResourceBudget,
        cancellation: &CancellationToken,
    ) -> PidResult<Self> {
        let Some(first) = blocks.first() else {
            return Err(PidError::InvalidConfig {
                context: "KdTree::build",
                message: "at least one non-empty block is required",
            });
        };
        let n = first.nrows();
        let dims = blocks
            .iter()
            .try_fold(0usize, |sum, block| sum.checked_add(block.ncols()));
        let Some(dims) = dims else {
            return Err(PidError::InvalidConfig {
                context: "KdTree::build",
                message: "concatenated dimension overflow",
            });
        };
        if n == 0 || dims == 0 {
            return Err(PidError::InvalidConfig {
                context: "KdTree::build",
                message: "blocks must have at least one row and one total column",
            });
        }
        for block in blocks {
            if block.nrows() != n {
                return Err(PidError::RowCountMismatch {
                    context: "KdTree::build",
                    left_rows: n,
                    right_rows: block.nrows(),
                });
            }
        }
        if n > u32::MAX as usize {
            return Err(PidError::InvalidConfig {
                context: "KdTree::build",
                message: "row count exceeds kd-tree index capacity",
            });
        }
        let capacity = n.checked_mul(dims).ok_or(PidError::InvalidConfig {
            context: "KdTree::build",
            message: "matrix size overflow",
        })?;

        let minimum_leaf_size = LEAF_SIZE / 2;
        let leaf_capacity = n
            .checked_add(minimum_leaf_size - 1)
            .and_then(|value| value.checked_div(minimum_leaf_size))
            .ok_or(PidError::SizeOverflow {
                operation: "KdTree::build",
            })?;
        let node_capacity = leaf_capacity
            .checked_mul(2)
            .and_then(|value| value.checked_sub(1))
            .ok_or(PidError::SizeOverflow {
                operation: "KdTree::build",
            })?;
        let point_bytes = (capacity as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "KdTree::build",
            })?;
        let order_bytes = (n as u128)
            .checked_mul(std::mem::size_of::<u32>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "KdTree::build",
            })?;
        let node_bytes = (node_capacity as u128)
            .checked_mul(std::mem::size_of::<Node>() as u128)
            .and_then(|value| {
                value.checked_add(
                    (node_capacity as u128)
                        .checked_mul(2)?
                        .checked_mul(dims as u128)?
                        .checked_mul(std::mem::size_of::<f64>() as u128)?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: "KdTree::build",
            })?;
        let initial_bounds_bytes = (dims as u128)
            .checked_mul(2)
            .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "KdTree::build",
            })?;
        let log_n = if n <= 1 {
            1u128
        } else {
            (usize::BITS - (n - 1).leading_zeros()) as u128
        };
        budget.check(
            "KdTree::build",
            ResourceEstimate {
                estimated_bytes: point_bytes
                    .checked_add(order_bytes)
                    .and_then(|value| value.checked_add(node_bytes))
                    .and_then(|value| value.checked_add(initial_bounds_bytes))
                    .ok_or(PidError::SizeOverflow {
                        operation: "KdTree::build",
                    })?,
                pairwise_distances: 0,
                operations_hint: (n as u128)
                    .checked_mul(dims as u128)
                    .and_then(|value| value.checked_mul(log_n))
                    .ok_or(PidError::SizeOverflow {
                        operation: "KdTree::build",
                    })?,
            },
        )?;
        let mut pts = try_vec_with_capacity("KdTree::build", capacity, budget)?;
        let mut lo = try_vec_filled("KdTree::build", dims, f64::INFINITY, budget)?;
        let mut hi = try_vec_filled("KdTree::build", dims, f64::NEG_INFINITY, budget)?;
        cancellation.check("KdTree::build", 0, capacity)?;
        let mut completed_coordinates = 0usize;
        for i in 0..n {
            let mut dim = 0;
            for b in blocks {
                for &v in b.row(i) {
                    if !v.is_finite() {
                        return Err(PidError::NonFiniteInput {
                            context: "KdTree::build: non-finite coordinate",
                        });
                    }
                    lo[dim] = lo[dim].min(v);
                    hi[dim] = hi[dim].max(v);
                    pts.push(v);
                    dim += 1;
                    completed_coordinates += 1;
                    if completed_coordinates.is_multiple_of(1024) {
                        cancellation.check("KdTree::build", completed_coordinates, capacity)?;
                    }
                }
            }
        }
        if lo
            .iter()
            .zip(&hi)
            .any(|(&min, &max)| !(max - min).is_finite())
        {
            return Err(PidError::NonFiniteInput {
                context: "KdTree::build: coordinate span exceeds finite f64 distance",
            });
        }

        let mut order = try_vec_with_capacity("KdTree::build", n, budget)?;
        order.extend(0..n as u32);
        // A split of the smallest splittable node (17 points) can create an 8-point leaf, so a
        // tree has at most ceil(n / 8) leaves and `2 * leaves - 1` total nodes. Reserving the
        // weaker `2*n/LEAF_SIZE` bound can under-allocate (notably near powers of two), causing an
        // infallible growth allocation inside `push`.
        let nodes = try_vec_with_capacity("KdTree::build", node_capacity, budget)?;
        let mut tree = Self {
            dims,
            n,
            pts,
            order,
            nodes,
            root: 0,
            budget,
        };
        tree.root = tree.build_node(0, n, cancellation)?;
        Ok(tree)
    }

    #[inline]
    fn point(&self, i: u32) -> &[f64] {
        let i = i as usize * self.dims;
        &self.pts[i..i + self.dims]
    }

    fn bounds_of(
        &self,
        start: usize,
        end: usize,
        cancellation: &CancellationToken,
    ) -> PidResult<(Vec<f64>, Vec<f64>)> {
        let mut lo = try_vec_filled("KdTree::bounds_of", self.dims, f64::INFINITY, self.budget)?;
        let mut hi = try_vec_filled(
            "KdTree::bounds_of",
            self.dims,
            f64::NEG_INFINITY,
            self.budget,
        )?;
        for (offset, &pi) in self.order[start..end].iter().enumerate() {
            if offset.is_multiple_of(1024) {
                cancellation.check("KdTree::bounds_of", offset, end - start)?;
            }
            let p = self.point(pi);
            for d in 0..self.dims {
                lo[d] = lo[d].min(p[d]);
                hi[d] = hi[d].max(p[d]);
            }
        }
        Ok((lo, hi))
    }

    fn build_node(
        &mut self,
        start: usize,
        end: usize,
        cancellation: &CancellationToken,
    ) -> PidResult<usize> {
        cancellation.check("KdTree::build", self.nodes.len(), self.nodes.capacity())?;
        let (lo, hi) = self.bounds_of(start, end, cancellation)?;
        let id = self.nodes.len();
        if id == self.nodes.capacity() {
            return Err(PidError::ResourceLimitExceeded {
                operation: "KdTree::build",
                resource: "reserved_nodes",
                requested: id.saturating_add(1) as u128,
                limit: self.nodes.capacity() as u128,
            });
        }
        self.nodes.push(Node {
            lo,
            hi,
            start,
            end,
            left: usize::MAX,
            right: usize::MAX,
        });
        if end - start > LEAF_SIZE {
            // Split on the widest extent at the median.
            let (lo, hi) = (&self.nodes[id].lo, &self.nodes[id].hi);
            let split_dim = (0..self.dims)
                .max_by(|&a, &b| (hi[a] - lo[a]).total_cmp(&(hi[b] - lo[b])))
                .unwrap_or(0);
            if hi[split_dim] == lo[split_dim] {
                // Every point in the node is identical on every axis. Median partitioning would
                // create a deeper tree without adding any pruning power.
                return Ok(id);
            }
            let mid = start + (end - start) / 2;
            let dims = self.dims;
            let pts = std::mem::take(&mut self.pts);
            sort_unstable_by_with_cancellation(
                "KdTree::build partition",
                &mut self.order[start..end],
                cancellation,
                |&a, &b| {
                    pts[a as usize * dims + split_dim]
                        .total_cmp(&pts[b as usize * dims + split_dim])
                },
            )?;
            self.pts = pts;
            if mid > start && mid < end {
                let left = self.build_node(start, mid, cancellation)?;
                let right = self.build_node(mid, end, cancellation)?;
                self.nodes[id].left = left;
                self.nodes[id].right = right;
            }
        }
        Ok(id)
    }

    /// Exact Chebyshev distance, same fold as [`crate::metric::chebyshev`].
    #[inline]
    fn dist(&self, q: &[f64], pi: u32) -> f64 {
        let p = self.point(pi);
        let mut acc = 0.0f64;
        for d in 0..self.dims {
            let diff = (q[d] - p[d]).abs();
            if diff > acc {
                acc = diff;
            }
        }
        acc
    }

    /// Smallest possible Chebyshev distance from `q` to any point inside the
    /// node's bounding box (0 if `q` is inside on every axis).
    #[inline]
    fn min_dist_to_box(node: &Node, q: &[f64]) -> f64 {
        let mut acc = 0.0f64;
        for (d, &qd) in q.iter().enumerate() {
            let below = node.lo[d] - qd;
            let above = qd - node.hi[d];
            let gap = below.max(above);
            if gap > acc {
                acc = gap;
            }
        }
        acc
    }

    /// Distance to the k-th nearest neighbor of `q`, excluding point
    /// `skip` (the query point itself). Exact: equals the brute-force
    /// `select_nth_unstable_by(k-1, total_cmp)` value.
    ///
    /// `k` must satisfy `k <= n - 1`; callers validate this via their
    /// existing `InvalidK` checks.
    #[cfg(any(feature = "experimental-continuous", test))]
    pub(crate) fn kth_distance(&self, q: &[f64], k: usize, skip: u32) -> PidResult<f64> {
        let cancellation = CancellationToken::new();
        self.kth_distance_with_cancellation(q, k, skip, &cancellation)
    }

    pub(crate) fn kth_distance_with_cancellation(
        &self,
        q: &[f64],
        k: usize,
        skip: u32,
        cancellation: &CancellationToken,
    ) -> PidResult<f64> {
        debug_assert!(k >= 1 && k < self.n);
        // Bounded max-heap of the k best distances seen so far.
        let capacity = k.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: "KdTree::kth_distance",
        })?;
        let mut heap = try_vec_with_capacity("KdTree::kth_distance", capacity, self.budget)?;
        self.kth_rec(self.root, q, k, skip, &mut heap, cancellation)?;
        debug_assert_eq!(heap.len(), k);
        Ok(heap[0])
    }

    fn kth_rec(
        &self,
        node_id: usize,
        q: &[f64],
        k: usize,
        skip: u32,
        heap: &mut Vec<f64>,
        cancellation: &CancellationToken,
    ) -> PidResult<()> {
        cancellation.check("KdTree::kth_distance", node_id, self.nodes.len())?;
        let node = &self.nodes[node_id];
        if heap.len() == k && Self::min_dist_to_box(node, q) > heap[0] {
            return Ok(());
        }
        if node.left == usize::MAX {
            for &pi in &self.order[node.start..node.end] {
                if pi == skip {
                    continue;
                }
                let d = self.dist(q, pi);
                if heap.len() < k {
                    heap.push(d);
                    sift_up(heap);
                } else if d.total_cmp(&heap[0]).is_lt() {
                    heap[0] = d;
                    sift_down(heap);
                }
            }
            return Ok(());
        }
        // Visit the nearer child first for tighter early bounds.
        let (l, r) = (node.left, node.right);
        let dl = Self::min_dist_to_box(&self.nodes[l], q);
        let dr = Self::min_dist_to_box(&self.nodes[r], q);
        let (first, second) = if dl <= dr { (l, r) } else { (r, l) };
        self.kth_rec(first, q, k, skip, heap, cancellation)?;
        self.kth_rec(second, q, k, skip, heap, cancellation)
    }

    /// Counts non-self points strictly inside and exactly on `radius` in one pruned traversal.
    ///
    /// This is the indexed counterpart of [`crate::nn::kth_neighbor_shell_counts`]. It is kept
    /// separate from [`Self::count_within`] because subtracting two inclusive counts would require
    /// two tree traversals per KSG query.
    #[cfg(any(feature = "experimental-continuous", test))]
    pub(crate) fn kth_neighbor_shell_counts(
        &self,
        q: &[f64],
        radius: f64,
        skip: u32,
    ) -> (usize, usize) {
        self.kth_neighbor_shell_counts_rec(self.root, q, radius, skip)
    }

    pub(crate) fn kth_neighbor_shell_counts_with_cancellation(
        &self,
        q: &[f64],
        radius: f64,
        skip: u32,
        cancellation: &CancellationToken,
    ) -> PidResult<(usize, usize)> {
        self.kth_neighbor_shell_counts_rec_with_cancellation(
            self.root,
            q,
            radius,
            skip,
            cancellation,
        )
    }

    fn kth_neighbor_shell_counts_rec_with_cancellation(
        &self,
        node_id: usize,
        q: &[f64],
        radius: f64,
        skip: u32,
        cancellation: &CancellationToken,
    ) -> PidResult<(usize, usize)> {
        cancellation.check(
            "KdTree::kth_neighbor_shell_counts",
            node_id,
            self.nodes.len(),
        )?;
        let node = &self.nodes[node_id];
        if Self::min_dist_to_box(node, q) > radius {
            return Ok((0, 0));
        }
        if node.left == usize::MAX {
            let mut interior_count = 0usize;
            let mut boundary_count = 0usize;
            for &pi in &self.order[node.start..node.end] {
                if pi == skip {
                    continue;
                }
                let distance = self.dist(q, pi);
                if distance < radius {
                    interior_count += 1;
                } else if distance == radius {
                    boundary_count += 1;
                }
            }
            return Ok((interior_count, boundary_count));
        }
        let left = self.kth_neighbor_shell_counts_rec_with_cancellation(
            node.left,
            q,
            radius,
            skip,
            cancellation,
        )?;
        let right = self.kth_neighbor_shell_counts_rec_with_cancellation(
            node.right,
            q,
            radius,
            skip,
            cancellation,
        )?;
        Ok((left.0 + right.0, left.1 + right.1))
    }

    #[cfg(any(feature = "experimental-continuous", test))]
    fn kth_neighbor_shell_counts_rec(
        &self,
        node_id: usize,
        q: &[f64],
        radius: f64,
        skip: u32,
    ) -> (usize, usize) {
        let node = &self.nodes[node_id];
        if Self::min_dist_to_box(node, q) > radius {
            return (0, 0);
        }
        if node.left == usize::MAX {
            let mut interior_count = 0usize;
            let mut boundary_count = 0usize;
            for &pi in &self.order[node.start..node.end] {
                if pi == skip {
                    continue;
                }
                let distance = self.dist(q, pi);
                if distance < radius {
                    interior_count += 1;
                } else if distance == radius {
                    boundary_count += 1;
                }
            }
            return (interior_count, boundary_count);
        }
        let left = self.kth_neighbor_shell_counts_rec(node.left, q, radius, skip);
        let right = self.kth_neighbor_shell_counts_rec(node.right, q, radius, skip);
        (left.0 + right.0, left.1 + right.1)
    }

    /// Number of points with Chebyshev distance `<= eps` from `q`, excluding
    /// point `skip`. Exact: equals the brute inclusive count.
    #[cfg(any(feature = "experimental-continuous", test))]
    pub(crate) fn count_within(&self, q: &[f64], eps: f64, skip: u32) -> usize {
        self.count_rec(self.root, q, eps, skip)
    }

    pub(crate) fn count_within_with_cancellation(
        &self,
        q: &[f64],
        eps: f64,
        skip: u32,
        cancellation: &CancellationToken,
    ) -> PidResult<usize> {
        self.count_rec_with_cancellation(self.root, q, eps, skip, cancellation)
    }

    fn count_rec_with_cancellation(
        &self,
        node_id: usize,
        q: &[f64],
        eps: f64,
        skip: u32,
        cancellation: &CancellationToken,
    ) -> PidResult<usize> {
        cancellation.check("KdTree::count_within", node_id, self.nodes.len())?;
        let node = &self.nodes[node_id];
        if Self::min_dist_to_box(node, q) > eps {
            return Ok(0);
        }
        if node.left == usize::MAX {
            let mut count = 0usize;
            for &pi in &self.order[node.start..node.end] {
                if pi != skip && self.dist(q, pi) <= eps {
                    count += 1;
                }
            }
            return Ok(count);
        }
        let left = self.count_rec_with_cancellation(node.left, q, eps, skip, cancellation)?;
        let right = self.count_rec_with_cancellation(node.right, q, eps, skip, cancellation)?;
        left.checked_add(right).ok_or(PidError::SizeOverflow {
            operation: "KdTree::count_within",
        })
    }

    #[cfg(any(feature = "experimental-continuous", test))]
    fn count_rec(&self, node_id: usize, q: &[f64], eps: f64, skip: u32) -> usize {
        let node = &self.nodes[node_id];
        if Self::min_dist_to_box(node, q) > eps {
            return 0;
        }
        if node.left == usize::MAX {
            let mut c = 0usize;
            for &pi in &self.order[node.start..node.end] {
                if pi != skip && self.dist(q, pi) <= eps {
                    c += 1;
                }
            }
            return c;
        }
        self.count_rec(node.left, q, eps, skip) + self.count_rec(node.right, q, eps, skip)
    }
}

#[inline]
fn sift_up(heap: &mut [f64]) {
    let mut i = heap.len() - 1;
    while i > 0 {
        let parent = (i - 1) / 2;
        if heap[i].total_cmp(&heap[parent]).is_gt() {
            heap.swap(i, parent);
            i = parent;
        } else {
            break;
        }
    }
}

#[inline]
fn sift_down(heap: &mut [f64]) {
    let n = heap.len();
    let mut i = 0;
    loop {
        let (l, r) = (2 * i + 1, 2 * i + 2);
        let mut largest = i;
        if l < n && heap[l].total_cmp(&heap[largest]).is_gt() {
            largest = l;
        }
        if r < n && heap[r].total_cmp(&heap[largest]).is_gt() {
            largest = r;
        }
        if largest == i {
            break;
        }
        heap.swap(i, largest);
        i = largest;
    }
}

/// Concatenate the query row for a tree built from `blocks` into `buf`.
#[inline]
pub(crate) fn concat_row_into(blocks: &[MatRef<'_>], i: usize, buf: &mut Vec<f64>) {
    buf.clear();
    for b in blocks {
        buf.extend_from_slice(b.row(i));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::matrix::MatOwned;

    /// Deterministic xorshift for reproducible fixtures.
    struct Rng(u64);
    impl Rng {
        fn next_f64(&mut self) -> f64 {
            let mut x = self.0;
            x ^= x >> 12;
            x ^= x << 25;
            x ^= x >> 27;
            self.0 = x;
            (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        }
    }

    fn random_mat(rng: &mut Rng, n: usize, d: usize, quantize: bool) -> MatOwned {
        let mut data = Vec::with_capacity(n * d);
        for _ in 0..n * d {
            let v = rng.next_f64();
            // Quantized fixtures create exact duplicate coordinates and tied
            // distances — the case where value-exactness matters most.
            data.push(if quantize { (v * 8.0).round() / 8.0 } else { v });
        }
        MatOwned::new(data, n, d).unwrap()
    }

    fn brute_kth(pts: &MatOwned, q: usize, k: usize) -> f64 {
        let mut d: Vec<f64> = (0..pts.as_ref().nrows())
            .filter(|&j| j != q)
            .map(|j| {
                crate::metric::chebyshev(pts.as_ref().row(q), pts.as_ref().row(j), "test").unwrap()
            })
            .collect();
        d.select_nth_unstable_by(k - 1, |a, b| a.total_cmp(b));
        d[k - 1]
    }

    fn brute_count(pts: &MatOwned, q: usize, eps: f64) -> usize {
        (0..pts.as_ref().nrows())
            .filter(|&j| j != q)
            .filter(|&j| {
                crate::metric::chebyshev(pts.as_ref().row(q), pts.as_ref().row(j), "test").unwrap()
                    <= eps
            })
            .count()
    }

    fn brute_shell_counts(pts: &MatOwned, q: usize, radius: f64) -> (usize, usize) {
        crate::nn::kth_neighbor_shell_counts(
            (0..pts.as_ref().nrows()).filter(|&j| j != q).map(|j| {
                crate::metric::chebyshev(pts.as_ref().row(q), pts.as_ref().row(j), "test").unwrap()
            }),
            radius,
        )
    }

    #[test]
    fn kth_distance_is_bit_identical_to_brute_force() {
        for (n, d, k, quantize) in [
            (150, 1, 4, false),
            (150, 3, 4, true),
            (200, 2, 1, true),
            (137, 5, 7, false),
        ] {
            let mut rng = Rng(0xDEAD_BEEF ^ (n as u64) << 8 ^ (d as u64));
            let m = random_mat(&mut rng, n, d, quantize);
            let tree = KdTree::build(&[m.as_ref()]).unwrap();
            for q in 0..n {
                let expect = brute_kth(&m, q, k);
                let got = tree.kth_distance(m.as_ref().row(q), k, q as u32).unwrap();
                assert_eq!(
                    got.to_bits(),
                    expect.to_bits(),
                    "n={n} d={d} k={k} q={q} quantize={quantize}"
                );
            }
        }
    }

    #[test]
    fn identical_points_remain_in_one_leaf() {
        let matrix = MatOwned::new(vec![3.0; 40 * 2], 40, 2).unwrap();

        let tree = KdTree::build(&[matrix.as_ref()]).unwrap();

        assert_eq!(tree.nodes.len(), 1);
        assert_eq!(tree.nodes[tree.root].left, usize::MAX);
    }

    #[test]
    fn proven_node_reservation_covers_threshold_boundary_trees() {
        for n in [17, 33, 65, 129, 130, 136, 257] {
            let mut rng = Rng(0xCAFE_BABE ^ n as u64);
            let matrix = random_mat(&mut rng, n, 1, false);
            let tree = KdTree::build(&[matrix.as_ref()]).unwrap();
            let maximum_nodes = 2 * n.div_ceil(LEAF_SIZE / 2) - 1;
            assert!(tree.nodes.len() <= maximum_nodes, "n={n}");
        }
    }

    #[test]
    fn count_within_is_exactly_brute_force() {
        let mut rng = Rng(0xC0FF_EE11);
        let m = random_mat(&mut rng, 180, 2, true);
        let tree = KdTree::build(&[m.as_ref()]).unwrap();
        for q in 0..m.as_ref().nrows() {
            for &eps in &[0.0, 0.05, 0.125, 0.3, 1.0] {
                assert_eq!(
                    tree.count_within(m.as_ref().row(q), eps, q as u32),
                    brute_count(&m, q, eps),
                    "q={q} eps={eps}"
                );
            }
        }
    }

    #[test]
    fn kth_neighbor_shell_counts_are_exactly_brute_force() {
        let mut rng = Rng(0x5E11_C0DE);
        let matrix = random_mat(&mut rng, 180, 2, true);
        let tree = KdTree::build(&[matrix.as_ref()]).unwrap();
        for query_index in 0..matrix.as_ref().nrows() {
            let radius = brute_kth(&matrix, query_index, 4);
            assert_eq!(
                tree.kth_neighbor_shell_counts(
                    matrix.as_ref().row(query_index),
                    radius,
                    query_index as u32,
                ),
                brute_shell_counts(&matrix, query_index, radius),
                "query {query_index}, radius {radius}",
            );
        }
    }

    #[test]
    fn concatenated_blocks_match_single_block_tree() {
        let mut rng = Rng(0xABCD_EF01);
        let a = random_mat(&mut rng, 160, 2, false);
        let b = random_mat(&mut rng, 160, 1, false);
        // Tree over blocks == tree over an explicit concatenation.
        let mut cat = Vec::new();
        for i in 0..160 {
            cat.extend_from_slice(a.as_ref().row(i));
            cat.extend_from_slice(b.as_ref().row(i));
        }
        let catm = MatOwned::new(cat, 160, 3).unwrap();
        let t_blocks = KdTree::build(&[a.as_ref(), b.as_ref()]).unwrap();
        let t_cat = KdTree::build(&[catm.as_ref()]).unwrap();
        let mut buf = Vec::new();
        for q in 0..160 {
            concat_row_into(&[a.as_ref(), b.as_ref()], q, &mut buf);
            let k1 = t_blocks.kth_distance(&buf, 3, q as u32).unwrap();
            let k2 = t_cat
                .kth_distance(catm.as_ref().row(q), 3, q as u32)
                .unwrap();
            assert_eq!(k1.to_bits(), k2.to_bits());
        }
    }

    #[test]
    fn identical_points_stay_a_leaf_and_answer_exactly() {
        // All-duplicate data: split can make no progress; the degenerate
        // guard keeps the node a leaf and queries stay exact (distance 0).
        let m = MatOwned::new(vec![0.5; 400], 200, 2).unwrap();
        let tree = KdTree::build(&[m.as_ref()]).unwrap();
        assert_eq!(tree.kth_distance(m.as_ref().row(0), 5, 0).unwrap(), 0.0);
        assert_eq!(tree.count_within(m.as_ref().row(0), 0.0, 0), 199);
    }

    #[test]
    fn build_rejects_coordinate_span_that_overflows_distance() {
        let m = MatOwned::new(vec![-f64::MAX, f64::MAX], 2, 1).unwrap();

        assert!(KdTree::build(&[m.as_ref()]).is_err());
    }

    #[test]
    fn applicability_gate() {
        assert!(kdtree_applicable(Metric::Chebyshev, 128, 3));
        assert!(!kdtree_applicable(Metric::Chebyshev, 127, 3));
        assert!(!kdtree_applicable(Metric::Chebyshev, 1000, 17));
        assert!(!kdtree_applicable(Metric::Chebyshev, 1000, 0));
    }
}
