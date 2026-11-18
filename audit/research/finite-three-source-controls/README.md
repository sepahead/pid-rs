# Twelve controls for a finite three-source registry

**Sepehr Mahmoudian · 18 November 2026**

Can the proof distinguish the specified 18-node information-decomposition registry from a registry that accepts an invalid family, silently exchanges two labels or reverses the order? A count of nodes alone misses several such errors. On stock Lean 4.34.1 the third revision checked both sides of twelve comparisons. Each comparison pairs a theorem about the original definition with a proof that the complete corresponding altered proposition is false. The twelve comparisons exercise **eight distinct original targets**. The emitted record contains 24 declarations. [Observation and source identities](observations.json) · [Exact declaration stream](declarations.txt)

## Mathematical object

The three labels are 0, 1 and 2. A **branch** is a subset of the labels. A **family** is a set of branches. A valid family has at least one branch, every branch is nonempty, and no distinct branches contain one another. Such a family is called an **antichain**. A **registry** gives the valid families fixed integer indices. A **mask** represents a branch by setting one bit per label. A **Boolean pattern** says which labels agree with a given reference. A **zeta entry** records whether the family at one index lies below the one at another. Williams and Beer introduced the redundancy lattice. Gutknecht, Wibral and Makkeh give its part–whole and logical interpretation. The particular numbered registry, targets and controls here are project-defined. [Williams and Beer](https://arxiv.org/abs/1004.2515v1) · [Gutknecht, Wibral and Makkeh](https://doi.org/10.1098/rspa.2021.0110)

Write $A\preceq B$ when every branch in $B$ contains some branch in $A$. The Boolean formula for a family is true if one of its branches has all its labels true. The original implication target compares these formulas on every Boolean pattern, in the direction from $B$ to $A$. The zeta matrix at row $i$, column $j$ records $\mathrm{registry}(j)\preceq\mathrm{registry}(i)$. There are eight masks, eight Boolean patterns and 18 registry entries. The propositions concern finite labels and truth values. They require no probability distribution, observed rows or units of information. [Definitions and complete targets](lean/Contract.lean) · [Original theorem statements](lean/RawTargets.lean)

## The twelve comparisons

The original theorem in each row has namespace PidFin3Candidate. The final column gives a witness to the failure of the **whole altered statement**. A changed definition is allowed to compile successfully. The negative result is the checked theorem about that definition. [Original proofs](lean/Candidate.lean) · [Control proofs and their typed examples](lean/SemanticFaults.lean)

| Case | Alteration | Original theorem | Decisive witness |
|---|---|---|---|
| 01 | Admit the empty family | carrier_membership | The empty family enters the carrier and fails validity. |
| 02 | Admit a family containing the empty branch | carrier_membership | The family consisting solely of the empty branch is nonempty, but its branch fails validity. |
| 03 | Remove a valid node | carrier_membership | The family containing just the branch {0} satisfies validity and is missing. |
| 04 | Admit comparable branches | carrier_membership | The distinct branches {0} and {0,1} occur together and the first is contained in the second. |
| 05 | Exchange bit positions 0 and 1 consistently in encoding and decoding | codec_anchors | Encoding the singleton {0} breaks its specified mask of 1. A round-trip test alone would miss the exchange. |
| 06 | Extend the mask round trip from three-bit masks to all natural numbers | encode_decode | Mask 8 decodes to the empty branch and re-encodes to 0. |
| 07 | Exchange registry entries 0 and 1, keeping the prescribed mask list fixed | registry_pointwise | Re-encoding the family at index 0 fails to recover its prescribed list of masks. |
| 08 | Duplicate the family at distinct indices | registry_injective | Indices 0 and 1 now yield the same family. |
| 09 | Reverse the order | extremes | Index 0 must be below index 2. These are the singleton families of {0} and {0,1}. |
| 10 | Transpose the zeta matrix | zeta_entries | The entry at row 0, column 2 distinguishes the two orientations. |
| 11 | Change one diagonal zeta entry | zeta_entries | The entry at row 0, column 0 contradicts reflexivity. The row still has 18 characters. |
| 12 | Replace comparison on every Boolean pattern by comparison on the all-false pattern | reverse_dnf | For $A$ at index 2 and $B$ at index 0, the restricted implication is vacuous. The pattern with just label 0 true separates the original formulas. |

## What was checked

The four base files are Contract, RawTargets, Candidate and JudgeCore. The twelve Fault modules each introduce a changed definition in a separate namespace. SemanticFaults imports the base files and all twelve altered modules. For each case it reuses the named original proof and proves a negation using a concrete witness. Two Lean examples present each of the 24 theorems at its raw and alias type, making 48 typed examples. The judge requires theorem declarations, checks definitional equality with the complete recorded type at full transparency, rejects universe parameters and metavariables, and inventories the axioms used by each exported theorem. The permitted set is propext, Classical.choice and Quot.sound. The equality check examines the complete types even when the printed record shows an alias. [Judge source](lean/JudgeCore.lean) · [Complete emitted rows](declarations.txt)

| Revision | Observed result |
|---|---|
| 1 | The first altered module failed at field notation for finite-set insertion. One primary step ran and zero declarations were admitted. |
| 2 | Prefix insertion syntax allowed all twelve altered modules to compile. In primary step 13 the combined module lacked computable decidability instances for four closed witnesses. The axiom guard rejected a placeholder introduced by error recovery. Zero declarations were admitted. |
| 3 | The four affected proof terms unfolded the order definition and, in case 12, the Boolean formula definition before ordinary kernel decision. The twelve altered modules and the combined module compiled. The combined output contained 24 ordered declaration rows and its completion marker. A separate stock process ran **leanchecker --fresh SemanticFaults**, exited successfully and emitted zero bytes on either stream. |

Revision 3 recorded 14 primary steps, 15 process-registry observations and a before/after comparison of 11,060 backing files. These counts describe the 18 November run. In the stock 4.34.1 implementation, the fresh operation loads the named module and replays the imported environment's constants into a fresh kernel environment. It shares Lean's kernel and the supplied compiled dependencies with the compile route. The 12 controls were selected from known material and share original definitions, proofs and toolchain. This is finite development evidence with shared implementation and custody. The observation supplies no external human review, general kernel soundness result, universal mutation-detection rate, check of another toolchain, refinement to a Rust registry, probability theorem or PID atom calculation. [Immutable stock source](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean)

## Reproduce from the public sources

Use a trusted local installation of stock Lean **4.34.1**, revision **5045d0056413266e57c625dcd7c365b10e377c52**, containing both lean and leanchecker. Provide a local Mathlib Git checkout at **d13f23b723b8a846827a245b89c10fc7d3f11612** with its recorded Lake manifest, dependency checkouts and already-built imports. The 18 November system was Darwin arm64. Its archive hash and the eight dependency revisions are recorded in the observation. The replay checks the reported compiler revision, version, checkout revisions, manifest, source roster, source bytes and expected output. The provenance of the installed binaries and compiled library bytes remains a local prerequisite. [Version and dependency identities](observations.json) · [Mathlib revision](https://github.com/leanprover-community/mathlib4/tree/d13f23b723b8a846827a245b89c10fc7d3f11612)

Set LEAN_BIN to the directory containing the two stock executables and MATHLIB to the checkout described above. From the repository root, run

~~~sh
python3 -I -S -B audit/research/finite-three-source-controls/replay.py \
  --lean-bin "$LEAN_BIN" --mathlib "$MATHLIB"
~~~

The Python standard-library driver verifies the 17 sources against the manifest, creates a new temporary directory and copies those verified bytes. It compiles Contract, RawTargets, Candidate, JudgeCore, Fault01 through Fault12 and SemanticFaults there. It compares the entire final standard output with declarations.txt, including the final newline, and requires a quiet successful fresh check. A compiler or checker diagnostic, timeout, altered source or byte mismatch causes failure. The temporary build products are removed on return. The helper uses one Lean worker, allows 120 seconds per compilation and 600 seconds for fresh checking. Dependency acquisition and compilation from the Mathlib source tree are outside this command. It reproduces the published finite predicate. A new run adds no blind validation or historical custody observation. [Portable replay helper](replay.py)

## Route and review limits

Read the result against the simplest alternatives. Counting 18 nodes misses an exchange of labels. Internal mask round trips miss a consistent permutation. Comparing registries as unordered sets misses the index exchange. Counting ones or checking matrix shape misses the transpose or the altered diagonal. Exercising only a single pattern misses the restricted-implication error. A hand enumeration gives a useful independent mathematical route for three labels. An untyped test can catch a particular counterexample but does not verify the exact proposition. Reviewing the sources alone gives no execution record. Replaying the same proof gives no independent logic implementation. A second proof assistant or a separate human source-to-specification review could address different residual questions. Retaining the prior result unchanged would add no evidence about these specific defects.

Review therefore distinguished carrier membership, antichain validity, empty family and empty branch, mask range, singleton anchors, external registry order, injectivity, strict order direction, matrix axes, diagonal reflexivity, pattern quantification, exact target binding, axiom collection, byte-level parsing, source custody and toolchain dependence. Reconsider this conclusion if a source or import differs, a type or axiom check changes, a witness survives its alteration, the emitted stream differs, or a relevant stock kernel issue affects these terms. Other source counts, unseen defect classes and scientific correspondence require their own evidence.

**Citation.** Sepehr Mahmoudian (2026), *Twelve controls for a finite three-source registry*. Include the exact repository commit or release. [Software citation](../../../CITATION.cff)
