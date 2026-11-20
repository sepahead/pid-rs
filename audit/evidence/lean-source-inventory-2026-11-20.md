# What changed in the Lean source inventory?

Sepehr Mahmoudian, 20 November 2026

A Lean source inventory counts tracked files and records their identities. To determine which earlier inspections still apply, we compared the Git file modes and blob identifiers at two revisions. A blob identifier names the stored bytes of a file. All 301 previously inventoried paths retain their mode and blob. At revision `8709ee545c9cec9f29f66129bda48aef49adedcd` the tree contains 330 Lean paths and 190 distinct blobs. The 29 added paths comprise five files on weighted count tables, fifteen on artificial formulas and nine on the original eighteen-family count. [Earlier inventory and actual axiom queries](lean-stock-axioms-2026-11-19/README.md)

The two revisions and the complete path and object records can be inspected from a Git checkout with the following commands.

```sh
git ls-tree -r --full-tree 15d9bd89b4b41303fd18addb68b1e9d1995132eb
git ls-tree -r --full-tree 8709ee545c9cec9f29f66129bda48aef49adedcd
git diff --raw --no-abbrev --no-renames 15d9bd89b4b41303fd18addb68b1e9d1995132eb 8709ee545c9cec9f29f66129bda48aef49adedcd -- '*.lean'
```

## What does an occurrence of `constant` mean here?

The source review masked comments and quoted strings while preserving line numbers. Two implementations agreed on the positions of the selected words related to unproved assumptions, unsafe definitions and compiled decisions. Every match in the 29 additions was the word `constant`. In the formal interpreter, `Cmd` represents a command in the input language. Its constructor `constant` stores a symbol's name and type. A line such as `Cmd.constant "w0" Ty.int` describes a declaration in the interpreted script. The Lean declaration that introduces `Cmd` defines an inductive data type.

| Added W02 source | Occurrences of this constructor or its uses |
|---|---:|
| [Original input representation](../research/three-source-w02/lean/W02OriginalData.lean) | 25 |
| [Interpreter and command type](../research/three-source-w02/lean/W02Semantics.lean) | 4 |
| [Artificial test data](../research/three-source-w02/lean/W02SyntheticData.lean) | 6 |
| [Rejection cases](../research/three-source-w02/lean/W02SyntheticRejection.lean) | 2 |

All 37 occurrences were checked against the constructor and its uses. Four explicit blocks beginning with `run_cmd` or `run_elab` inspect named declarations, proof terms or module information and print evidence. The source options control implicit variables, warnings, recursion depth and computation limits. Earlier negative test fixtures still contain the previously reported three axiom declarations and one proof placeholder. [Weighted-count evidence code](../research/three-source-alphabet-counts/lean/CountEvidence.lean) · [Declaration dependency query](../research/three-source-alphabet-counts/inspection/Dependencies.lean) · [W02 proof-term inspection](../research/three-source-w02/lean/W02Inspect.lean)

A text scan cannot establish what imported binary modules contain or which axioms a proof uses transitively. For the 22 weighted-count statements and for W02, the respective replay records identify the definitions, theorem statements, typed uses, imports, allowed assumptions and stock checker. The artificial formulas have their own results and resource limits. Model-assisted source inspections shared the same Git bytes. [Weighted-count proof and limits](../research/three-source-alphabet-counts/README.md) · [W02 proof and limits](../research/three-source-w02/README.md) · [Artificial example procedures](../research/three-source-synthetic-projection/README.md)

Cite Sepehr Mahmoudian (2026), *What changed in the Lean source inventory?*, with the exact repository commit or release. [Software citation](../../CITATION.cff)
