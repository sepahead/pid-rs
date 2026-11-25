# How the angular claim was examined

**Sepehr Mahmoudian · 2026**

The question concerns a population calculation with exact proper terms. The earlier result put the supremum of radii permitting a passing direction strictly between 0.30 and 0.39. That statement alone did not exclude disjoint intervals of failure. The new proof supplies strict monotonicity for each admissible positive integer order and each fixed direction. The [report](EXPOSITION.md) contains the proof and the quantitative decision. [Exact calculation and review scope](EVIDENCE.md)

## Approaches compared

| Approach | Premise and decision | What could change the decision |
|---|---|---|
| Keep the earlier bounds | Suitable if a coarse operational cutoff is enough. They leave the first exact change of decision unresolved. | A use with only amplitudes below 0.29 or above 0.39 does not need this refinement. |
| Use direct quadrature for the two-dimensional integral | Useful for checking values at specified phases and amplitudes. A finite grid misses possible directions. | A proved bound between all grid points would expand its scope. |
| Use ordinary joint mutual information | It gives the denominator for a different truncation problem. The proper shared-exclusions terms change the atom and its relative error. | An explicit equivalence for the named population and both numerators and denominators would be needed. |
| Use absolute error | It describes joint-tail magnitude. The assigned positive atom varies with direction. | A common constant denominator would permit transfer of rankings. |
| Compare adjacent coefficients by monotone ratios | Some coefficients of the exact atom are negative. A positive-weight ratio argument cannot use them directly. | A different positive representation with an actual monotone ratio could give another proof. |
| Bound the derivative only near the numerical crossing | A uniform derivative comparison near 0.34 suffices for local uniqueness. It leaves other radii and orders unresolved. | Use when the wider moment series or the unit-boundary proof is unavailable. |
| Compare the marginal radial growth of the atom and tail | The combination $4A-rA'$ removes the fourth-order coefficient. Its remaining negative part has a uniform summable bound. Selected for the all-order theorem. | A change of the density, gauge, proper terms or coefficient bound requires a new argument. |
| Search over angles in binary64 | It located a candidate radius and direction. Roundoff or missed narrow minima can select a false decision. | Treat as a numerical suggestion only until both strict signs are proved. |
| Use stationary points of a truncated polynomial | Root isolation could certify every critical point and endpoint. Higher-degree root multiplicities and the infinite remainder add work. | Useful if the identity or uniqueness of the minimizing direction becomes the question. |
| Use Bernstein coefficients on dyadic subintervals | Nonnegative basis weights give a full-interval lower bound. Exact subdivision settled all 17 intervals. Selected for the first certificate. | A nonpositive coefficient on an unrefined interval would require further evidence. |
| Use a midpoint polynomial expansion | The triangle inequality gives another exact full-interval bound. The second program needed 44 subintervals. | A nonpositive lower bound can be inconclusive even when the true polynomial is positive. |
| Count real roots of a lower polynomial | Eighteen moment terms give a degree-36 lower bound. The derivative and successive negative remainders give 18 sign changes at each endpoint. Both endpoint values are positive. This obtains the upper-radius decision through a separate implementation. | If the lower polynomial has a real zero, its root count alone cannot establish strict positivity of the full series there. |
| Fit an angular sensor model or evaluate controller loss | Would address measurements or physical performance. No input samples, fitting or task loss enter this population problem. | New deployment evidence needs a declared population, sampling design, measurement units, comparators and a meaningful task endpoint. |

## Scientific reading

The roles below are questions applied during model-assisted review. They name 50 lenses. They do not name 50 separate persons or supply a vote on mathematical truth.

| Five lenses | What was checked |
|---|---|
| Source provenance, author lineage, functional identity, redundancy definition, quantity estimated | The continuous functional follows Ehrlich and coauthors. The source grouping and common radian gauge determine this atom. The repository supplies the population family and truncation question. |
| Physical coordinates, dimensional units, joint population support, coordinate change, input statistics | Four periodic angular coordinates, a unit-determinant transform, the uniform integration measure and the population weight are given separately. Sign changes correspond to phase shifts. |
| Vacuity, origin, density zero, invalid exterior, strict tolerance | The atom is positive for every positive admissible radius. At zero the ratio is undefined. At one the weighted integral has a limiting value. Beyond one the proposed density is negative on an open set. Equality fails the strict test. |
| Index ranges, subtraction signs, high-order cancellation, sign of atom coefficients, summability | The derivative combination cancels the term at index two. The proof uses an upper bound on signed coefficients and the exact sum of their possible negative contributions to the derivative comparison. |
| Derivatives, endpoint limits, monotone direction minimum, compactness, supremum versus first failure | Each fixed-direction ratio grows. Compactness supplies a minimizing direction and continuity. Choosing a minimizer at the larger radius supplies strict increase of the minimum. |
| Non-PID baseline, pure-axis comparator, worst direction, best direction, absolute versus relative error | Direct ordinary integral and absolute-tail calculations answer different questions. The first boundary and the second boundary have different quantifiers over directions. The pure axes at 0.30 demonstrate that difference. |
| Candidate selection, floating-point exposure, scientific independence, mathematical counterexample, negative evidence | The binary64 pilot preceded the exact targets. The two proof readers share the earlier series and host. A direction grid alone was rejected. The earlier ambiguity in a caption is retained with its original evidence. |
| Exact arithmetic, omitted positive tail, coefficient conversion, dyadic interval coverage, alternative expansion | Bounds use exact rational arithmetic. One program covers all 17 Bernstein intervals; a distinct expansion covers 44 intervals. A gap, overlap or nonpositive bound fails the published check. |
| Schema exactness, Boolean-versus-integer typing, duplicate properties, altered examples, bounded termination | The native replay pins its inputs and sources, calculates the certificates anew, compares exact fields, and exercises malformed cases. Depth, work and time are bounded; an unresolved calculation cannot pass. |
| Software refinement, toolchain trust, sensor application, sampling uncertainty, novelty and human review | This proof has no Rust sampling-estimator refinement. A fixed population supplies reference decisions, while real sensor use requires its own data and input model. Formal-kernel or human review and scientific priority have separate evidence requirements. |

The proposer and the other mathematical reader both obtained the same radial sign before reading one another's derivations. One differentiated in ordinary amplitude. The other used squared amplitude. They share the population, binomial series, host custody and model assistance. The first two exact numerical programs have one implementation author. Another model reader wrote the root-count program. All three used the selected radii, with the expected signs known. Their proof certificates refer to every direction on a fixed interval. No unseen data or independent empirical confirmation was used.
