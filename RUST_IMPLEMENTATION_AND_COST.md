# Rust implementation and computational cost

This engineering reference describes the Rust implementation baseline at revision `8a1142cae32fae637b3bdfe39f890cb29176d144`. It separates source-derived work counts from measured latency. These counts describe the inspected algorithms, not a new PID theorem, a measured timing benchmark or a formally verified complexity proof. The [method catalog](method-catalog.json) and [public exports](crates/pid-core/src/lib.rs) retain their authority over scientific identity and API availability.

## Implemented routes and research boundaries

| Route | Current Rust entry point and gate | Boundary |
|---|---|---|
| Empirical categorical MGW | `stable::categorical::discrete_sxpid2/3/n` and averaged/budgeted variants; default build | Two to four sources; direct empirical-PMF evaluation |
| Training-fitted quantization | `stable::quantized::EqualWidthQuantizer` and `fitted_quantized_sxpid2/3/n`; default build | A declared categorical representation with fitted provenance |
| KSG mutual information | `stable::continuous::ksg_mi_report` and budget/cancellation variants; default build | Report-first continuous MI under its support contract |
| Ehrlich continuous PID2 | `experimental::continuous::pid2_isx_report` and related APIs; `experimental-continuous` | Separately estimated continuous redundancy and MI terms |
| Incomplete continuous PID3 | `experimental::continuous::incomplete_pid3_report`; `experimental-continuous` | Availability diagnostic, not a complete PID |
| Full continuous PID3 | `experimental::mixed_dimension_pid3::pid3_isx_report`; `research-mixed-dimension-pid3` | Research-only mixed-dimensional route |
| Resampling callbacks | `experimental::pipelines`; `experimental-pipelines` | Explicit callback and sampling assumptions; no generic calibration |
| Exact-count PID2 certifier | Separate `audit/tools/certified-sxpid` crate, `certify_sxpid2` API and CLI | Offline reference certificate, outside the published workspace |
| Finite-prefix or stopped MGW score estimator, PID training layer | No matching runtime API in the inspected workspace | Mathematical studies and proposals do not create an executable learner |

The source links below distinguish existing implementations from possible improvements. A feature gate identifies availability, not estimator or application validity.

## Scope and symbols

The categorical route evaluates the empirical shared-exclusions PID of Makkeh, Gutknecht and Wibral, [arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5). The continuous route estimates the distinct Ehrlich functional, [arXiv:2311.06373v3](https://arxiv.org/abs/2311.06373v3), with [KSG mutual information](https://doi.org/10.1103/PhysRevE.69.066138) as a separate component. Quantization produces a categorical estimand; it does not turn the categorical algorithm into the continuous estimator. All information values are in nats.

Evaluating an empirical categorical PMF requires no Gaussian model. It also does not require row independence merely to compute that PMF. Population inference, confidence bounds and held-out episode comparisons require their separately stated sampling assumptions. Counts, occupancy, dependence, missingness and the fitting role of each row must accompany the cost report.

Let $s$ be the number of sources, $N$ the number of aligned rows, $D$ the total number of categorical coordinates across sources and target, $K$ the number of observed distinct complete source–target states, and $m$ the number of nonempty lattice antichains. Let $a$ be the largest number of collections in one antichain. An antichain is a family of nonempty subsets of the source indices, with no distinct member containing another. For a fixed anchor, the MGW source event means agreement on every source within at least one such subset: AND within a subset, OR across subsets. Here $s$ is restricted to 2, 3 or 4. Each source can have several columns; one camera is not necessarily one scalar coordinate. For the continuous calculation, $d$ denotes the total real coordinate dimension. Let $B$ denote the number of resamples and $p$ the active worker count.

| Sources $s$ | Atoms $m$ | Maximum collections $a$ | Nonempty source subsets | Availability masks |
|---|---:|---:|---:|---:|
| 2 | 4 | 2 | 3 | 4 |
| 3 | 18 | 3 | 7 | 8 |
| 4 | 166 | 6 | 15 | 16 |

## Categorical MGW: what the current Rust code does

The general route is `stable::categorical::discrete_sxpid_n_averaged_with_budget_and_cancellation`. Its [implementation](crates/pid-core/src/sxpid.rs) validates the source count and matrix shapes, materializes row states, computes subset mutual information, groups complete states into an empirical PMF, generates the lattice, evaluates each supported anchor state, and averages its atoms. The specialized two- and three-source APIs have separate inversion paths; the exact counts below refer to the general `n`-source engine.

The specialized three-source route uses its fixed lattice, but its inversion helper recomputes the topological order for each informative and misinformative inversion at each anchor. The general route computes that order once per call. These different constant costs matter when comparing the APIs on small inputs.

For every one of the $K$ anchor states, the general engine makes one target-mass scan. For each of the $m$ nodes it makes two further scans: the source-union mass, and its intersection with the target event. Each scan visits all $K$ PMF entries. Thus a successful complete event pass visits exactly

$$
(2m+1)K^2
$$

PMF entries. This counts visits, not CPU instructions. A predicate can compare several source vectors and can stop its internal comparisons early. Its worst-case coordinate work is proportional to $aD$.

| Observed states $K$ | Two-source event visits | Three-source event visits | Four-source event visits |
|---:|---:|---:|---:|
| 100 | 90,000 | 370,000 | 3,330,000 |
| 1,000 | 9,000,000 | 37,000,000 | 333,000,000 |
| 10,000 | 900,000,000 | 3,700,000,000 | 33,300,000,000 |

These are conditional work counts if the call is admitted and finishes. Default resource preflight can refuse a row count before this work starts. No row in the table predicts seconds or proves that the input is statistically adequate.

Each anchor also undergoes two Möbius inversions. An inversion recovers each atom from its cumulative value by subtracting the already-accounted lower-node atom contributions. Each inversion considers $m(m-1)/2$ ordered earlier-node pairs. A lattice comparison can inspect up to $a^2$ collection pairs. The resulting inversion work is $O(Km^2a^2)$. Averaging uses fixed-size exact accumulators for represented binary64 addends, with $O(Km)$ additions. This improves reduction behavior; logarithms and products remain rounded, so the result is not an exact-real PID certificate.

Sorting rows and constructing the subset histograms cost at most $O((2^s-1)ND\log(\max(2,N)))$ coordinate comparisons. The general engine also rebuilds its small lattice per call. It enumerates $2^{2^s-1}-1$ candidate mask families—32,767 for four sources—and checks pairwise containment. Its current topological-order search has a conservative $O(m^3a^2)$ upper bound. These setup costs can matter on small fixtures and repeated calls; they are not included in the event-visit table.

A useful source-derived envelope for the general route is

$$
O\!\left((2^s-1)ND\log(\max(2,N))
 + maDK^2 + m^2a^2K + C_s\right),
$$

where $C_s$ is the lattice setup cost just described. For fixed source count and coordinate width, the event term is quadratic in observed support size. If $K$ stays small while $N$ grows, the sorting and row storage can dominate instead.

### Memory and resource refusal

Materialized rows use $O(ND)$ storage. The PMF keeps $K$ state payloads and reserves entry capacity for up to $N$ rows. Per-anchor scratch and the averaged accumulators scale with $m$; lattice storage scales with $ma$. Subset histograms are constructed sequentially. The averaged route therefore avoids retaining a $K$-by-$m$ atom table. Requesting pointwise output adds $O(K(m+D))$ storage. It does not change the dominant event work.

The general and specialized three-source averaged paths still allocate a temporary atom vector for each anchor. Reduced retained output is not zero allocation, constant total memory, or streaming input.

The [resource implementation](crates/pid-core/src/resource.rs) supplies preflight estimates, allocation errors and cooperative cancellation. Defaults include a 1 GiB estimated-memory limit and $10^{10}$ coarse operation units. These are guards, not latency, RSS or real-time guarantees. The categorical preflight substitutes $N$ for the unknown $K$ before building the PMF and counts some repeated allocation exposure; it can be conservative for repeated-state data.

Operation hints mix accounting units. The categorical event term does not multiply by the width of each vector comparison; the inversion term does not literally count each collection comparison or lattice setup operation. Treat the hint as the implemented admission rule, not a proven instruction-count bound.

Empty data, zero-width variables, mismatched row counts and unsupported source counts are rejected. Counts above $2^{53}$ are rejected by the binary64 count-conversion contract. The work estimates assume accepted finite machine inputs and fixed machine-word arithmetic; a cancellation or allocation failure returns an error instead of a partial numerical estimate.

In particular, the four-source event component alone is $7,968N^2$ operation-hint units. At $N=1,121$ it already exceeds $10^{10}$, before histogram, inversion and averaging terms. This is a sufficient default-refusal condition, not the exact largest accepted row count. A repeated-state dataset can therefore be refused although its realized event scan would be much smaller. Raising the budget changes resource admission, not scientific validity; it must follow a workload measurement.

## Fitted quantization

The [quantizer](crates/pid-core/src/quantizer.rs) separates fitting from transformation. For $N_{\rm train}$ training rows, $D$ scalar columns and $b$ bins per column, its numeric fit loops scan minima/maxima and construct edges in $O(N_{\rm train}D+bD)$ work, retaining $O(bD)$ edge storage. Metadata validation and optional training-data hashing add their own work. Bin fitting belongs on the training rows in an inferential workflow.

Applying fixed edges to $N$ evaluation rows takes $O(ND\log(b+1))$ worst-case edge-search work and retains $O(ND)$ labels. Constant columns and boundary cases can return earlier. The report-producing path additionally sorts rows for occupancy, analyzes bin geometry, clones provenance and retains reports. The labels-only path avoids constructing that report but preserves its conservative report-sized preflight admission envelope.

The fitted PID adapters then pay for categorical estimation and transformed-input reports. Their input domain is a quantized categorical estimand, not the original continuous law. Coarser bins can reduce occupied support and cost while discarding information. The smallest observed frequency does not establish a population mass floor.

## Continuous Ehrlich PID2 and KSG

The current [Ehrlich redundancy kernel](crates/pid-core/src/isx.rs) scans the other $N-1$ rows for each query, computes two source distances and a target distance, selects a neighbour radius, and counts the required events. The dominant coordinate work is $O(N^2d)$. [PID2](crates/pid-core/src/pid2.rs) combines this redundancy with separately estimated MI terms; the atom arithmetic is cheap compared with those estimations.

Eligible low-dimensional Chebyshev [KSG calls](crates/pid-core/src/ksg.rs) use an exact kd-tree. Favourable geometry permits pruning; a query can still visit the complete dataset. A generic $O(N\log N)$ runtime guarantee is therefore inappropriate. Neither kernel needs a retained $N$-by-$N$ distance matrix. With parallel query execution, scratch can scale as $O(pN)$, in addition to input, tree and diagnostic storage. Reports also perform support, cardinality and neighbour-shell checks; scalar-kernel timing omits those costs.

At the inspected revision, automatic tree selection requires Chebyshev distance, at least 128 rows, and total joint dimension from 1 through 16. A 512-coordinate embedding does not enter that accelerated path merely because a kd-tree exists elsewhere in the library.

This distinction is material: the stable report calls marginal-X, marginal-Y and joint neighbour-shell diagnostics after its estimator backend. The [diagnostic loop](crates/pid-core/src/support.rs) scans all other rows for each query and retains only a linear-size distance buffer. Thus the current complete report still includes quadratic distance-scan work even when the estimator's tree queries prune well. A faster scalar microbenchmark is not a latency measurement of the stable report API. Preserve these diagnostic checks when assessing a faster implementation; deleting them changes the report contract.

Two implementation details refine the tree cost. The [current builder](crates/pid-core/src/kdtree.rs) fully sorts each internal segment before splitting it, so a conservative build bound is $O(Nd\log N+N\log^2N)$. Its neighbour query maintains a heap of up to $k$ distances, where $1\leq k<N$. Allowing $k$ to vary gives the conservative all-query bound $O(N^2(d+\log(k+1)))$; treating $k$ as fixed removes that growing heap factor. These are upper envelopes, not observed scaling curves. The resource hint is not a literal comparison count for the recursive sorts.

Computational feasibility does not establish the continuous assumptions. The declared full-dimensional population support, sampling assumptions, chosen metric/gauge, neighbour parameter and numerical shell conditions remain separate. More threads do not repair high-dimensional distance concentration. The experimental Lorentz adaptation is a separate MI route; it is not a validated hyperbolic MGW or Ehrlich PID implementation.

The two-source Ehrlich route also requires equal ambient source dimensions. Projecting two sensors to the same number of coordinates satisfies that shape condition only; it does not establish the needed population densities, intrinsic dimensions or compatible source scales.

The current [continuous PID3 paths](crates/pid-core/src/pid3.rs) have a different memory profile. Both the incomplete diagnostic and the separately gated full research path retain four triangular distance matrices. Their distance payload alone is $4\cdot8\cdot N(N-1)/2=16N(N-1)$ bytes, before scratch and other allocations. At $N=10,000$ this is 1,599,840,000 bytes, already above the default 1 GiB estimate ceiling. This is a conditional allocation calculation, not an admitted runtime measurement. The incomplete path is an availability diagnostic; the full mixed-dimensional path remains research-only. Neither becomes a qualified three-source continuous PID because its memory fits.

## Exact-count numerical certificates

There is also a separate, non-published [Rust audit crate](audit/tools/certified-sxpid/src/lib.rs), `pid-certified-sxpid`. Its `certify_sxpid2` function constructs 24 exact two-source cumulative/atom expressions and computes directed enclosures. This is different from the workspace's binary64 estimator. Its Rug/MPFR/GMP arithmetic has a separate native-dependency and verification boundary. It does not certify a `pid-core` binary64 result, extend to PID3, or supply population confidence.

For $K$ canonical count-table rows, the main [event extraction](audit/tools/certified-sxpid/src/extract.rs) makes $8K^2$ row visits, with target marginal construction and exact expression processing added. Counts and rational operands are arbitrary-precision values: their bit lengths, state-token lengths, retained term counts and chosen precision affect time and memory. The [default precision policy](audit/tools/certified-sxpid/src/resource.rs) permits at most six passes at 128, 256, 512, 1024, 2048 and 4096 bits, with target interval width $2^{-160}$. Structural or precision exhaustion can fail rather than produce a certificate. Exact-product preflight exhaustion can instead abstain on a sign comparison while retaining an interval enclosure. The [resource policy](audit/tools/certified-sxpid/README.md#resource-policy) bounds memory-shaped objects and iterations, not elapsed time. Its 4,096-row structural ceiling does not guarantee admission of every such table; the retained growing-support witness reaches a cumulative-term limit at 410 rows. A credible end-to-end measurement must include the separate certificate verifier. The fixed-machine-word cost model of the ordinary estimator does not cover this tool.

## Statistical bounds and resampling

A scalar continuity modulus or a fixed-form confidence bound is usually cheap to evaluate once all required constants are supplied. Obtaining justified constants can be the difficult part. An observed minimum cell count does not establish a population mass floor. A declared dependence coloring does not establish independence within each color.

Formula evaluation cost does not imply that a matching Rust helper exists. Each study must name its actual implementation or state that the formula remains a proposed implementation.

A paired episode mean and its fixed-confidence lower bound need $O(E)$ arithmetic for $E$ completed independent episode scores. Computing the predictions that supply those scores is a separate cost. Several frames or masks from one episode do not become independent episodes.

For [bootstrap](crates/pid-core/src/bootstrap.rs) and [permutation pipelines](crates/pid-core/src/pipeline.rs), $B$ full statistic evaluations multiply the main estimator work, with row-copying, scheduling and summary costs added. A point estimate can require one additional evaluation. If every replicate refits preprocessing or a model, that fit is inside the multiplier. Parallelism can reduce elapsed time but increases concurrent memory. Resampling callbacks can have costs that the wrapper cannot infer; record their budget separately. The existing two-source quantized bootstrap recomputes same-sample quantization on each resample; it does not hold a separately trained transform fixed. A fixed-transform workflow needs an appropriate callback and its own assumptions. A faster replicate is not evidence that its null, block scheme or calibration assumptions hold.

## Task evaluation, learning and online use

A task that only needs MI, conditional MI or a subset-MI objective need not be formulated as a full PID problem. The current general categorical PID result already contains the nonempty subset MI values, but requesting that result still pays for full PID. Its subset-only helper is private. A dedicated public, budgeted Rust route that obtains only the required subset MI values remains implementation work; a cheaper mathematical objective is not a completed API. See the [alternatives guide](PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md) and [sensor/Galadriel guide](PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md) for application assumptions and comparison boundaries.

For a frozen predictor, exhaustive missing-sensor evaluation has at most $2^s$ conditions per prediction landmark. If one condition costs $C_{\rm model}$, an uncached implementation costs up to $2^sC_{\rm model}$ per landmark. Image/audio encoding, repeated episode landmarks and simulator rollouts add costs. Cache only computations unchanged by the mask. Training a separate predictor for each mask has a separate training multiplier and model-storage cost.

For $U$ optimizer updates with bounded step cost $C_{\rm step}$, the training component is $O(UC_{\rm step})$. Parameters, optimizer state, minibatches and any differentiation graph contribute separately to peak memory. This is accounting for a specified training procedure, not an implemented PID learning system or a convergence result. Repeating training across folds, seeds or resamples repeats that cost.

The [finite-prefix mean](audit/formal/lean-prefix-mgw-mean/PUBLICATION.md), [bias](audit/formal/lean-prefix-mgw-bias/PUBLICATION.md) and [gradient](audit/formal/lean-prefix-mgw-gradient/PUBLICATION.md) packages describe mathematical objects and proof tooling. They do not provide Rust prefix simulation or a gradient optimizer. A prospective horizon-$h$ score block needs $h+1$ complete draws and all $h+1$ scores, including the anchor. Simulation, encoding, event updates and derivative computation must all be measured. A proof written over a full block does not establish a constant-memory streaming implementation, and differentiating hard empirical bin labels does not satisfy the papers' population-score assumptions.

Use bounded offline diagnosis and held-out task-loss comparisons first. Recomputing full four-source PID for every camera frame or optimizer step requires separate end-to-end latency, memory and statistical evidence. A validated small-table calculation could later run online; existing APIs or passing fixtures alone do not establish a deadline or control benefit.

## Inputs, dimensionality and useful reductions

For categorical sources with alphabet sizes $q_1,\ldots,q_s$ and target size $q_Y$,

$$
K\leq\min\!\left(N,q_Y\prod_{i=1}^s q_i\right).
$$

With eight categories per source and a binary target, the complete capacities are 128, 1,024 and 8,192 for two, three and four sources. These are capacities, not promised occupied counts or required sample sizes. Independently binning every coordinate of a large camera/audio embedding can make nearly every complete row distinct, bringing $K$ close to $N$. Sparse occupancy also weakens population estimation even when a computation finishes.

Use a task-defined, training-fitted representation with an explicit held-out target and retained fit identity. Coarsening can reduce compute and variance while discarding information and changing the estimand. A Euclidean or hyperbolic embedding does not remove this tradeoff. Report sensitivity to the representation instead of silently treating a cheaper representation as the original sensor variable.

## Measurement and improvement plan

The repository has [Criterion benchmarks](crates/pid-core/benches/estimators.rs) for continuous kernels, quantization and small categorical cases. They are a starting point, not an end-to-end robotics qualification. Record an exact release build and its source revision, compiler/features, hardware, $N,K,D,s$, alphabets and occupancy, selected API, preprocessing cost, thread count, resource limits, warm-up, repetitions, elapsed-time distribution, peak memory and refused or cancelled cases. Keep estimator time separate from model inference, compilation and Lean/checker execution. No current timing number is asserted in this note.

The first optimization candidates are caching the fixed lattice and its predecessor relation, reusing exact integer event counts, and computing only the MI quantities required by the task. For a fixed lattice and a common finite PMF, Möbius inversion is linear, so averaging cumulative values before inversion is valid in exact arithmetic. It changes the current floating-point evaluation order and it needs an explicit numerical contract and comparison before adoption. Sample or prefix approximations also need bias, variance and stopping-cost evidence. No optimization is marked implemented by being listed here.
