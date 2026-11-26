# Nested categorical source events in Lean

Sepehr Mahmoudian · 2026

At one outcome and each source level, an event states that the reading matches the observed value. A match at a finer level must imply a match at every coarser level. A branch requires all of its matches. A node requires a match on at least one of its branches. Each branch and each node is finite and nonempty. They can contain repeated indices or repeated branches. Level zero and equal adjacent events are allowed.

The six named propositions in `Proof.lean` have the following meanings.

1. A branch contains an index at least as large as a threshold exactly when its largest index reaches the threshold.
2. Every branch contains such an index exactly when the smallest of their largest indices reaches the threshold.
3. At one outcome, all matches in a branch hold exactly when its finest match holds.
4. At one outcome, a node holds exactly when its match at the smallest of the branch levels holds.
5. Over any outcome type, the node and that one level have equal event predicates if the matches are nested at every outcome.
6. The sum of successive differences in any integer sequence through the node level is the value there minus the level-zero value.

For a categorical antichain, form one conjunction for each nonempty set of indices. Form their disjunction. This gives the tree in the model. For three ordered sources, its level is the minimum of the branch maxima. The formal model contains no probability measure, real logarithm or empirical estimator. The probability identities, real-valued atom sums and sharp split bound have separate written proofs and rational tests. The original count table and the order of its columns have to satisfy the stated map assumptions.

## Reproduce the stock check

Use Python 3.14 and the official Apple arm64 Lean 4.34.1 release at revision `5045d0056413266e57c625dcd7c365b10e377c52`. Supply the path to its unpacked directory and a new output directory. Other platforms can compile the four Lean source files with matching Lean source, but this byte-for-byte replay checks the recorded Apple arm64 tools and libraries. [Lean 4.34.1 release](https://github.com/leanprover/lean4/releases/tag/v4.34.1)

```sh
python3.14 -I -S -B replay.py --toolchain /path/to/lean-4.34.1 --out fresh-run
```

The public judge accepts an explicit release directory. All protected source inputs except that locator change in the judge retain their original bytes. The two distinct judge and manifest hashes are in `public-source-identity.json`. The original receipts identify the original predicate. The public run separately compares the native outcomes.

The judge checks hashes of 3,257 release files. It compiles the model, proofs and observer with one compiler worker and treats warnings as errors. It runs the stock fresh checker on each module. The observer includes twenty typed or concrete examples. In one case the source predicate fails the nesting assumption and the reduction fails. In another case the computed node level is two. The compiler must reject a separate assertion that its level is three for that exact reason. The named statements, printed terms and individual transitive axiom queries are in `observed/r02/Observer-compile.stdout`. Named auxiliary terms from tactics are checked in the replay. One earlier payload failed at the induction syntax. Its source and compiler messages remain in `candidate/r01.json` and `observed/r01`.

The two incidence proofs use propositional extensionality, classical choice and quotient soundness. The two match proofs use propositional extensionality. Event equality and integer telescoping use propositional extensionality and quotient soundness. Propositional extensionality identifies logically equivalent propositions. Classical choice selects a witness from a nonempty type. Quotient soundness identifies equivalence classes of related representatives.

The compiler loads compiled imports. The fresh checker loads the compiled environment with the release's default trust level zero. It then gives the eligible declarations to a fresh kernel environment, also at trust level zero. The compiled imports and the code that reads them belong to the trusted software. It submits axioms as axioms, checks theorem declarations and skips unsafe and partial declarations. The submitted project sources use no extra axiom, unfinished proof or native evaluation principle. The review, compiler and stock replay share the Lean implementation. [Stock checker](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean) · [Kernel replay](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean)

A separate reader wrote four strict source fibres on five outcomes, a failure when nesting is removed, and a signed sequence with baseline seven and prefix change minus six. The extra examples and their independent stock replay are in `additional`.
