# Stock Linux checks of two real logarithm bounds

Sepehr Mahmoudian · 25 November 2026

A certificate for a logarithm must account for the terms omitted from a finite sum. This check reads two existing inequalities in Mathlib, a library of mathematics for the Lean proof assistant. The inequalities apply to the natural logarithm and to a real argument between zero and one, including zero and excluding one. The number of retained terms can be any natural number, including zero. [Statements and source](README.md) · [Pinned Mathlib source](https://github.com/leanprover-community/mathlib4/blob/d13f23b723b8a846827a245b89c10fc7d3f11612/Mathlib/Analysis/SpecialFunctions/Log/Deriv.lean#L320-L347)

The lower bound is the sum of the retained odd powers, each divided by its positive exponent. The upper bound adds the next odd power divided by one minus the square of the argument. Both bound one half of the logarithm of the ratio of one plus the argument to one minus the argument. For example, take argument one third and retain one term. The lower bound is one third. The extra upper amount is one twenty-fourth. The resulting interval from one third through three eighths contains one half of the natural logarithm of two.

The Linux job reads the Lean 4.34.1 compiler archive and checks its hash. It uses the pinned Mathlib source, checks eight package revisions and inventories the compiled library objects. The stock compiler builds two declarations that apply the two existing library theorems directly. A separate checker process reads the new module and checks its declarations. Loading the compiled dependencies uses the compiler’s regular trust rules. Each numerical exit status below belongs to its own command. Zero means the command succeeded. [Official sources and version identities](identities.json) · [The two declarations](Read.lean)

| GitHub run | Compile | Fresh checker | Deliberately false source | Complete field result |
|---|---:|---:|---:|---|
| [45548866600](https://github.com/sepahead/pid-rs/actions/runs/45548866600) | 1 | Not run | Not run | The compiler refused an unknown print option. |
| [45550896292](https://github.com/sepahead/pid-rs/actions/runs/45550896292) | 0 | 0 | 1 | The output checker refused an additional line of explanation from the compiler. |
| [45552656882](https://github.com/sepahead/pid-rs/actions/runs/45552656882) | 0 | 0 | 1 | The complete statements, proof terms, axiom lists and specified false-source diagnostic passed. |

The false source supplied a proof that zero is less than one where a proof that one is less than zero was required. The third output checker accepts the stock explanatory note only when its full recorded text follows the exact error at the specified line. Its test suite rejects 38 altered transcripts. In the third run, the fresh checker took 247.057 seconds. The largest sampled resident memory for that process group was 2,883,604,480 bytes. These measurements describe the proof check. [False source](False.lean) · [Original records and archive hashes](observed-2026-11-25.json)

Each of the four declarations, two original names and two new names, depends on three standard Lean axioms. Propositional extensionality identifies logically equivalent propositions. Classical choice selects a member of a nonempty type. Quotient soundness identifies equivalent representatives in a quotient. No candidate for a stronger mathematical theorem was submitted in these runs. A proof of a sharper omitted-tail factor and a proof connecting the real inequalities to an integer certificate each need their own record. [Source and run conditions](README.md)

Cite Sepehr Mahmoudian (2026), *Stock Linux checks of two real logarithm bounds*, and give the exact repository commit or release. Cite the pinned Mathlib definition for the inequalities. [Software citation](../../../CITATION.cff)
