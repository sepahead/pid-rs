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
}

impl KdTree {
    /// Build over the concatenation of `blocks` (all `n` rows each). Fails on
    /// any non-finite coordinate or coordinate span — mirroring the brute
    /// path's `checked_distance` contract (which would reject a subtraction
    /// that overflows during its full scan).
    pub(crate) fn build(blocks: &[MatRef<'_>]) -> PidResult<Self> {
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

        let mut pts = Vec::with_capacity(capacity);
        let mut lo = vec![f64::INFINITY; dims];
        let mut hi = vec![f64::NEG_INFINITY; dims];
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

        let mut tree = Self {
            dims,
            n,
            pts,
            order: (0..n as u32).collect(),
            nodes: Vec::with_capacity(n.saturating_mul(2) / LEAF_SIZE + 2),
            root: 0,
        };
        tree.root = tree.build_node(0, n);
        Ok(tree)
    }

    #[inline]
    fn point(&self, i: u32) -> &[f64] {
        let i = i as usize * self.dims;
        &self.pts[i..i + self.dims]
    }

    fn bounds_of(&self, start: usize, end: usize) -> (Vec<f64>, Vec<f64>) {
        let mut lo = vec![f64::INFINITY; self.dims];
        let mut hi = vec![f64::NEG_INFINITY; self.dims];
        for &pi in &self.order[start..end] {
            let p = self.point(pi);
            for d in 0..self.dims {
                lo[d] = lo[d].min(p[d]);
                hi[d] = hi[d].max(p[d]);
            }
        }
        (lo, hi)
    }

    fn build_node(&mut self, start: usize, end: usize) -> usize {
        let (lo, hi) = self.bounds_of(start, end);
        let id = self.nodes.len();
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
            let mid = (start + end) / 2;
            let dims = self.dims;
            let pts = std::mem::take(&mut self.pts);
            self.order[start..end].select_nth_unstable_by(mid - start, |&a, &b| {
                pts[a as usize * dims + split_dim].total_cmp(&pts[b as usize * dims + split_dim])
            });
            self.pts = pts;
            // Degenerate guard: if all coordinates are identical the split
            // makes no progress; keep the node a leaf.
            if mid > start && mid < end {
                let left = self.build_node(start, mid);
                let right = self.build_node(mid, end);
                self.nodes[id].left = left;
                self.nodes[id].right = right;
            }
        }
        id
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
    pub(crate) fn kth_distance(&self, q: &[f64], k: usize, skip: u32) -> f64 {
        debug_assert!(k >= 1 && k < self.n);
        // Bounded max-heap of the k best distances seen so far.
        let mut heap: Vec<f64> = Vec::with_capacity(k + 1);
        self.kth_rec(self.root, q, k, skip, &mut heap);
        debug_assert_eq!(heap.len(), k);
        heap[0]
    }

    fn kth_rec(&self, node_id: usize, q: &[f64], k: usize, skip: u32, heap: &mut Vec<f64>) {
        let node = &self.nodes[node_id];
        if heap.len() == k && Self::min_dist_to_box(node, q) > heap[0] {
            return;
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
            return;
        }
        // Visit the nearer child first for tighter early bounds.
        let (l, r) = (node.left, node.right);
        let dl = Self::min_dist_to_box(&self.nodes[l], q);
        let dr = Self::min_dist_to_box(&self.nodes[r], q);
        let (first, second) = if dl <= dr { (l, r) } else { (r, l) };
        self.kth_rec(first, q, k, skip, heap);
        self.kth_rec(second, q, k, skip, heap);
    }

    /// Number of points with Chebyshev distance `<= eps` from `q`, excluding
    /// point `skip`. Exact: equals the brute inclusive count.
    pub(crate) fn count_within(&self, q: &[f64], eps: f64, skip: u32) -> usize {
        self.count_rec(self.root, q, eps, skip)
    }

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
            .map(|j| crate::metric::chebyshev(pts.as_ref().row(q), pts.as_ref().row(j)))
            .collect();
        d.select_nth_unstable_by(k - 1, |a, b| a.total_cmp(b));
        d[k - 1]
    }

    fn brute_count(pts: &MatOwned, q: usize, eps: f64) -> usize {
        (0..pts.as_ref().nrows())
            .filter(|&j| j != q)
            .filter(|&j| crate::metric::chebyshev(pts.as_ref().row(q), pts.as_ref().row(j)) <= eps)
            .count()
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
                let got = tree.kth_distance(m.as_ref().row(q), k, q as u32);
                assert_eq!(
                    got.to_bits(),
                    expect.to_bits(),
                    "n={n} d={d} k={k} q={q} quantize={quantize}"
                );
            }
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
            let k1 = t_blocks.kth_distance(&buf, 3, q as u32);
            let k2 = t_cat.kth_distance(catm.as_ref().row(q), 3, q as u32);
            assert_eq!(k1.to_bits(), k2.to_bits());
        }
    }

    #[test]
    fn identical_points_stay_a_leaf_and_answer_exactly() {
        // All-duplicate data: split can make no progress; the degenerate
        // guard keeps the node a leaf and queries stay exact (distance 0).
        let m = MatOwned::new(vec![0.5; 400], 200, 2).unwrap();
        let tree = KdTree::build(&[m.as_ref()]).unwrap();
        assert_eq!(tree.kth_distance(m.as_ref().row(0), 5, 0), 0.0);
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
