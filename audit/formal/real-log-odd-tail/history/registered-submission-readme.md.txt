# A real error bound for the logarithm of an exact count product

Sepehr Mahmoudian, 2026

A finite categorical calculation can return a positive rational product. Its logarithm can require approximation. This study asks how much of that logarithm can remain after truncating its odd power series. A separately checked integer implementation rounds the finite sum. This study concerns the real truncation error. [Six categorical tables](../../research/three-source-six-certificate-observations/README.md)

A *partial sum* adds a prescribed number of terms. A *remainder* is the exact value minus that sum. Let $n$ be the number of terms and $x$ the real argument. Both are nonnegative, $n$ is an integer, and $x<1$. The logarithm is natural. The two expressions below are dimensionless. For an information value the count calculation supplies the scale in nats.

$$
H_n(x)=\tfrac12\log\frac{1+x}{1-x}-
       \sum_{i=0}^{n-1}\frac{x^{2i+1}}{2i+1},
\qquad
U_n(x)=\frac{x^{2n+1}}{(2n+1)(1-x^2)}.
$$

The frozen statement requires $0\le H_n(x)\le U_n(x)$ for every such pair. It requires both inequalities to be strict when $x>0$. At $x=0$ both expressions vanish, including when $n=0$. At $x=1/2,n=1$, replacing the factor 3 in the denominator by 4 would give $1/24$. The first three terms of the series give $H_1(1/2)\ge 1/24+1/160$. This is an exact counterexample to that smaller upper estimate. The odd-power expansion is classical. The work specific to this project is the selected formal statement and its test for the count calculation. [NIST series](https://dlmf.nist.gov/4.38.E5) · [Pinned Mathlib derivative and bounds](https://github.com/leanprover-community/mathlib4/blob/d13f23b723b8a846827a245b89c10fc7d3f11612/Mathlib/Analysis/SpecialFunctions/Log/Deriv.lean#L261-L347)

## What the check requires

The first submitted body failed the limited source grammar before Lean ran. The original body and refusal are in the history directory. The next enrolled body uses the same statement and judge. A separate operator must retrieve the actual Linux return before this attempt receives formal credit. The parent observation compiled and replayed two existing Mathlib bounds. Its upper remainder omits the factor $1/(2n+1)$. [Recorded parent run](https://github.com/sepahead/pid-rs/actions/runs/45552656882)

The judge binds the source of the statement, proof, independent check and false control. It uses the stock Lean 4.34.1 release and a pinned compiled Mathlib cache. It compiles each of three modules and invokes the stock fresh checker on each module separately. It inventories the axioms of the named propositions. The judge permits three standard axioms. Propositional extensionality identifies logically equivalent propositions. Quotient soundness identifies equivalent representatives in a quotient. Classical choice selects an element of a nonempty type. The original stock fresh checker loads the compiled environment and replays eligible declarations into an empty kernel environment. It retains axioms and skips unsafe and partial declarations according to its implementation. No local changes to that checker form part of this procedure. [Original stock checker](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean) · [Original declaration replay](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean)

## Rust implementation and computational cost

This study has no Rust estimator API. The stable categorical shared-exclusions routines of Makkeh, Gutknecht and Wibral in pid-rs accept discrete observation columns. They have their own numerical policy. This formal real expression has no sample rows, dimensions, alphabets, preprocessing, training or resampling. Evaluating the displayed partial sum uses $n$ terms. A program can update consecutive powers with one multiplication by $x^2$ and keep a fixed number of numeric accumulators. The cost of each arithmetic operation depends on the required precision. A remainder bound alone gives no runtime or floating-point error guarantee. No runtime is reported for an estimator here. The formal job allows one Lean worker, four gibibytes (4 × 2³⁰ bytes) of sampled process-group memory and 600 seconds per native command. A resource stop records a failed attempt. Applying the result to a categorical atom also requires a nonempty finite count table of positive total, a positive rational product and separate checks of argument reduction and integer rounding. [Finite categorical shared exclusions](https://doi.org/10.1103/PhysRevE.103.032149)

Cite Sepehr Mahmoudian, *A real error bound for the logarithm of an exact count product* (2026). Include the exact repository commit or release. [Software citation](../../../CITATION.cff)
