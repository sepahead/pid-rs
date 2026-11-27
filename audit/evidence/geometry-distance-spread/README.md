# A regression in the spread of nearby distances

Sepehr Mahmoudian, 2026. Cite this correction with the exact pid-rs commit or release and the [software citation](../../../CITATION.cff).

The Chebyshev distance of two rows is the largest absolute coordinate difference. For three rows, the distance-concentration diagnostic summarizes three pairwise distances and three nearest-neighbor distances, one per row. The population standard deviation divides the sum of squared deviations by three before taking the square root. The coefficient of variation divides that standard deviation by the mean.

Let $p=1-2^{-53}$, the binary64 value immediately below one. The rows $(0,0)$, $(p,0)$ and $(0,1)$ have pairwise distances $(p,1,1)$ and nearest-neighbor distances $(p,p,1)$. Both population standard deviations equal $2^{-53}\sqrt{2}/3$, approximately $5.233641528945917\times10^{-17}$. The original public implementation returned zero pairwise spread for this row order. Exchanging the last two rows gave approximately $6.409875621278546\times10^{-17}$. A rounded intermediate mean had erased or distorted the represented difference. The original program returned a nonnegative variance increment in each case. [Three-row input](three_rows.rs) · [Original output](three-rows-original.stdout)

The correction subtracts a represented common offset before updating the scaled mean and sum of squared deviations. When an input extends the range, it moves the stored coordinates to the new origin and scale. The update also serves the standard error of the mean of the sampled four-point values. The seeded sample and its historical reported-mean recurrence retain their original definitions. [Four-point input calculation](four_point_reference.py) · [Checked sample counts](four-point.json)

## Replay

From the repository root, the first command checks the saved original and corrected readings, their rational comparisons and the negative controls. The second builds the selected public Rust library with default features disabled and reads all 102 inputs through its public entry point. It needs the locked Cargo dependencies in the offline cache and a matching Rust toolchain.

```sh
python3 -B audit/evidence/geometry-distance-spread/replay.py --recorded
python3 -B audit/evidence/geometry-distance-spread/replay.py --build
cargo test --offline --locked --no-default-features -p pid-core --test geometry
```

An independently written receiver fixed 17 small designs and all six permutations of each before seeing the replacement. Across the 90 admitted inputs, it compared 990 fields. All extrema had to match exactly. The remaining outputs had to lie within six steps between adjacent binary64 numbers. The original failed on 228 fields. The replacement passed all fields with a largest observed error of two steps. Twelve further inputs returned an error for a zero mean or an unrepresentable distance. The tests use represented distances and dyadic arithmetic together with high-precision square roots. The tested tolerances apply to these inputs. [Exact finite criterion](CRITERION.md) · [Source-specific receipt](INDEPENDENT.json)

## Rust implementation and computational cost

`pid_core::diagnostics::distance_concentration_stats` accepts a matrix of finite coordinates and a distance configuration. The ordinary public metric is Chebyshev. For $n$ rows of dimension $d$, the routine evaluates $n(n-1)/2$ pairs, takes $O(n^2d)$ time and uses $O(n)$ nearest-neighbor storage. The moment update uses constant time and fixed storage per value. The feature-gated Lorentz variant shares the reduction and applies separate checks to its coordinates. The four-point test uses sixteen deterministic draws on five rows.

The recorded build, core and geometry tests, Lorentz diagnostic tests, formatting check and strict lint ran in about 35 seconds on one host with a one-GiB process-group limit. The peak sampled process-group size was 516,440,064 bytes. These figures include compilation. The finite checks supply no standalone runtime benchmark or population calibration. [Native test and resource record](NATIVE-CHECKS.json)
