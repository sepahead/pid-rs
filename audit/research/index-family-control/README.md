# A constructive finite-index calibration

Sepehr Mahmoudian

This procedure asks whether stock Lean 4.34.1 can check every branch of an invented, guarded function on 83 positions under the ordinary restricted proof language. The previous original run failed while constructing a decision for a disjunction of 82 or 76 position equalities. It retained useful earlier checks and produced no final original assertion pairs. [Original run](https://github.com/sepahead/pid-rs/actions/runs/44847287927) · [Original registration](https://github.com/sepahead/pid-rs/tree/37e0913096e2d1fdf136278c18161ed8ede1d5e7/audit/research/three-source-original-reachable-v3)

## What the checker asks

A finite index is a natural number smaller than its stated bound. The readiness flag has two values. The argument is any natural number. A *leaf* is the proof for one index. An empty finite index set has no leaves. For a positive size, the stock finite-case rule splits index zero from the successor of an index in the next smaller set. The repetition ends at size zero. [Stock finite cases](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Init/Data/Fin/Lemmas.lean#L942-L955)

The index k is an integer from 0 through 82. The argument x is a nonnegative integer. The left value is 3k + 2 + x. The right-hand table lists its entries as integer literals. It begins with 37 at index zero. For each positive index its entry is 3k + 2. The right calculation adds x, then adds one if readiness is false. All values are counts in this invented model. When readiness is true and the index is positive, the theorem requires equality for every argument. At index 1 and argument 7 the two ready values are both 12. The unready right value is 13. At index zero and argument 7 the left and ready right values are 9 and 44.

One proof connects 83 named leaves by finite elimination. The zero leaf uses its contradictory index premise. Each of the 82 later leaves must close. A second proof contains every elimination and closing step in a single input to the original restricted tactic parser. Its consumer states the quantified equality directly. The first proof cannot supply a lemma to the second. The judge also compares two arguments at every index for both readiness values, producing 332 ordered numerical checks, then tests three false conclusions. These finite comparisons exercise the inputs. The formal claim about an arbitrary natural argument has its own two fixed consumer types.

## How to read the outcome

For each ordinary module, the job compiles the new source and runs the separate stock fresh checker on the resulting object. A subsequent observer records 170 named theorems, complete type and value representations, the local owner, direct constant use and transitive axioms. The accepted axiom policy permits the stock principles of propositional extensionality, quotient soundness and classical choice. A separate listing must agree for every theorem. The typed dependency check requires 254 edges. It includes each named leaf and the explicitly empty tail. The artificial assumptions and data have been visible since preparation. Shared source and tools limit the independence of all these checks.

The operator compares the hosted artifact and run metadata with the first creation of its registered ref. Run `verify.py --help` for the run, job, artifact and complete exact-branch run listing, archive and repository arguments. Preserve every unsuccessful command, archive and attempt. An incomplete trace or missing negative control ends this qualification. A complete result would qualify this construction on the invented table. Each original typed valuation, closure and argument list would still need its own checks. [Stock fresh-check specification](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean)

## Rust implementation and computational cost

This qualification uses stock Lean and a standard-library Python observer. There is no estimator input or public Rust API for this proof test. Doubling the number of table entries approximately doubles the number of named branches and trace rows. The explicit single-slot construction repeats a successor expression at each index, so its source length grows quadratically with the index bound. The number of stock kernel reductions depends on the elaborated terms. The Linux job uses one logical CPU, a 2,700-second total clock, at most 900 seconds per native command, 4 GiB direct or sampled process-group memory and 1 GiB for retained native evidence. The 55-minute workflow gives time to preserve failures. The extracted stock supplier is separate from the evidence-byte bound. No new timing is reported at registration.

Suggested citation: Sepehr Mahmoudian, “A constructive finite-index calibration,” 2026. Include the exact registration commit, run number and artifact digest when citing an execution. [Software citation](../../../CITATION.cff)
