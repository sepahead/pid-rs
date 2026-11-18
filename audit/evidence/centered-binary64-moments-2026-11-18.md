# Standard deviation and fitted centering of adjacent binary64 values

Sepehr Mahmoudian, 2026. Cite this record with the exact repository commit or release. [Software citation](../../CITATION.cff).

Can a fitted standardizer preserve a separation of one unit near the largest exactly consecutive binary64 integers? The public mean can round to an endpoint. Using that rounded value as the center changes resampling spreads and the coordinates passed to downstream estimators.

## Recomputable discrepancy

Let the two equally weighted observations be the exactly represented integers $2^{53}-1$ and $2^{53}$, measured in the same units. Their exact mean is $2^{53}-1/2$. The two deviations are $-1/2$ and $+1/2$. Dividing their sum of squares by two gives population variance $1/4$. Dividing by one gives sample variance $1/2$.

At revision `1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20`, centering on the rounded normalized mean gave population standard deviation $1/\sqrt{2}$ and sample standard deviation 1, up to binary64 rounding. Standardizing those training rows gave approximately $(-\sqrt 2,0)$. The corrected population and sample standard deviations are $1/2$ and $1/\sqrt 2$, respectively. The corrected training scores are $(-1,1)$. The held-out represented value $2^{53}+2$ has score 5 using this fit. Reflecting all values about zero reflects their scores.

## Rust implementation and computational cost

The stable Rust `Standardizer` fits each finite training column in a coordinate system whose origin is the point in its observed range nearest zero. It retains the origin, a positive scale for a varying column, the mean offset and the standard deviation in scaled coordinates. It reconstructs the display mean in input units. Transforming held-out values reuses the fitted coordinates, including the part of the center lost from the display mean. Constant columns follow the declared `Drop`, `Error`, `Zero` or `LeaveCentered` policy. The parameter hash domain changes to `pid-rs-standardizer-parameters-sha256-v2` and covers these coordinates, public means, policy and retained column order. The training-data hash still identifies the represented training matrix. [Fitted implementation](../../crates/pid-core/src/preprocess.rs), [moment calculation](../../crates/pid-core/src/stats.rs).

For $n$ training rows and $d$ columns, fitting takes three moment passes plus a training identity pass, $O(nd)$ work and (O$d$) fitted storage. The aggregate fit estimate allows five binary64 values and one column index per column, 48 bytes per column on a 64-bit target. A transform of $m$ evaluation rows to $r$ retained columns allocates $8mr$ output bytes and takes $O(mr)$ element work. The separate fit-and-transform budget accounts for both allocations. The API checks limits before allocation and returns an error for an unrepresentable transformed value. No runtime timing is reported.

Under `experimental-pipelines`, the scalar, paired and row-bootstrap reports and the research PID3 bootstrap use centered sample standard deviations of the complete replicate values with divisor $B-1$ for $B\ge 2$. Computing moments is linear in $B$ per reported scalar. Sorting the complete values for percentiles costs $O(B\log B)$. The optional row-bootstrap perturbation scales also use the centered population spread of each input column. The reports retain their sampling assumptions and the outcomes of failed replicates. Neither numerical agreement nor deterministic replay establishes statistical coverage. [Scalar and paired bootstrap](../../crates/pid-core/src/bootstrap.rs), [row pipeline](../../crates/pid-core/src/pipeline.rs).

## Verification and reconsideration

The public Rust regression checks exactly represented training and held-out scores of both signs. A second regression calls the actual scalar block bootstrap with a first-row callback and reads its retained outcomes. For $k$ high values among $B$ replicates, it compares the returned spread with the square root of $\frac{k(B-k)}{B(B-1)}$, the sample variance of two unit-spaced outcomes with those counts. Both tests run with `cargo test --locked -p pid-core --all-features --test centered_moments`. The stable fit test also runs with `--no-default-features`. [Regression source](../../crates/pid-core/tests/centered_moments.rs).

The old rounded-center construction is rejected by this represented input. The frozen two-file repair had SHA-256 `37d55b8db44ea885656339c98bf37f75205958f1e3de1cff2065b1830ca150d3`. A separate fresh extraction checked it in debug and release builds. These are finite executions by model-assisted reviewers on a shared host. The examples supply no universal error bound, correctly rounded square-root theorem, downstream PID calibration or independent human review. Reopen for a finite input with spurious zero spread, an avoidably non-finite result, an incorrect held-out score, an inconsistent parameter identity, or a fit/transform allocation beyond its advertised budget.
