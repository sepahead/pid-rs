# Call-site and index map for KSG-INTEGER-HARMONIC-001 revision 1

## Exact special-function reduction

For positive integers, the digamma recurrence and base value give

```text
psi(1) = -gamma,
psi(m + 1) = psi(m) + 1/m,
therefore psi(m) = H_(m-1) - gamma.
```

Substitution into a four-term combination with coefficients `(+1,+1,-1,-1)` cancels all four
copies of `gamma`.  For harmonic indices

```text
K = k - 1,
N = n - 1,
a = min(x_index, y_index),
b = max(x_index, y_index),
```

where `K <= a <= b <= N`, the exact-real term is

```text
H_K + H_N - H_a - H_b = (H_N - H_b) - (H_a - H_K).
```

The last form is symmetric in the two counts before binary64 subtraction.  Exact `Fraction`
enumeration of every feasible tuple through `n = 16` found no identity or index failure.  The
three independently hand-checked boundaries retained by the generator are `11/6`, `5/6`, and
`-1/3`.

## Direct runtime sites

| Function/path | Current positive-integer arguments | Harmonic indices | Classification |
|---|---|---|---|
| `ksg::ksg_local_mi_terms_backend`, tree branch | `psi(k)+psi(n)-psi(nx+1)-psi(ny+1)` | `k-1,n-1,nx,ny` | migrate |
| `ksg::ksg_local_mi_terms_backend`, brute branch | same | same | migrate through the same helper |
| `ksg::ksg_local_mi_terms_xblocks_with_budget`, tree branch | `psi(k)+psi(n)-psi(nx+1)-psi(ny+1)` | `k-1,n-1,nx,ny` | migrate |
| `ksg::ksg_local_mi_terms_xblocks_with_budget`, brute branch | same | same | migrate through the same helper |
| `isx::isx_local_diagnostics` (`EhrlichKsg`) | `psi(k)+psi(n)-psi(n_alpha)-psi(n_t)` | `k-1,n-1,n_alpha-1,n_t-1` | migrate |
| `pid3::redundancy_for_antichain` | `psi(k)+psi(n)-psi(n_alpha)-psi(n_t)` | `k-1,n-1,n_alpha-1,n_t-1` | migrate |
| `isx::isx_redundancy_heuristic_sketch` | `psi(k)+psi(n)+psi(shared)-0.5psi(s1)-0.5psi(s2)` | not applicable | retain general digamma; coefficients sum to two |

The KSG marginal counts exclude the anchor.  The validated unique joint shell has exactly `k-1`
strict-interior neighbors; each lies inside both marginal strict radii, so
`k-1 <= nx,ny <= n-1`.  The cited shared-exclusions paths initialize their marginal counts with
the anchor, hence `k <= n_alpha,n_t <= n`; subtracting one gives the same admitted harmonic-index
domain.  These bounds are consequences of the existing shell validation and count construction;
the arithmetic change does not validate the neighbor search independently.

## Indirectly affected paths

- Hyperbolic KSG uses the same KSG kernel with a different typed metric/support mode.
- `LocalMinKsg` and `DisjunctionFromLocalMi` heuristics call the KSG local-term paths and inherit
  the revision; `HeuristicSketch` deliberately does not.
- Continuous co-information, PID2, incomplete/full PID3, hierarchy, and composed pipelines can
  inherit changed values through KSG or continuous shared-exclusions calls.
- Python entry points are bindings to these Rust paths and do not form a separate estimator.

Every release-scope family that can emit a changed scalar must therefore either migrate its own
estimator revision or retain child reports whose revisions unambiguously identify all changed
constituents.  Raw scalar compositions without such child identity require an explicit revision
migration.

## Shared cut and residual boundaries

The critical cut is the conjunction of this call-site classification and the off-by-one index map.
The Decimal corpus and exact rational route share that mathematical cut.  Neighbor counts, shell
semantics, support assumptions, estimator consistency, statistical calibration, application
validity, and a universal binary64 error bound remain outside it.
