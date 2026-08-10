# Retained failure note: abandoned `native_decide` prototype

## Prototype context

During scratch development, the asymmetric eight-key enumeration was first closed with a native
evaluator in `/tmp/TwoSourceCountEventBridge.lean`:

```lean
namespace PidFiniteConvergence.SemanticScratch

theorem binary_key_univ_eq :
    (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
      allBinaryKeys := by
  native_decide

#print axioms PidFiniteConvergence.SemanticScratch.binary_key_univ_eq
```

The scratch file was checked from `audit/formal/lean` with the pinned project environment:

```text
lake env lean /tmp/TwoSourceCountEventBridge.lean
```

The axiom print included the generated assumption

```text
PidFiniteConvergence.SemanticScratch.binary_key_univ_eq._native.native_decide.ax_1_1
```

in addition to the package's permitted basis.

## Disposition

The proof was replaced by kernel reduction:

```lean
theorem binary_key_univ_eq :
    (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
      allBinaryKeys := by
  decide
```

The same finite proposition compiled with `decide`, after which its axiom print contained only
`propext`, `Classical.choice`, and `Quot.sound`. The production semantic contract uses local kernel
`decide` proofs. The checker rejects the `native_decide` token in executable Lean source, and its
self-test injects that token into the semantic contract and requires fail-closed rejection.

## Evidence boundary

The `/tmp` prototype and its terminal output were not promoted to immutable repository artifacts.
This note is therefore retained **historical process evidence**, not independently replayable raw
evidence for the observed scratch output. The replayable present-tense evidence is narrower:

- the checked production source contains kernel `decide`, not `native_decide`;
- the source scanner rejects a native-evaluator mutation;
- the semantic contract is SHA-256 bound; and
- every inventoried production theorem passes `collectAxioms` against the permitted basis.

This note must not be cited as proof that every possible native evaluator invocation has the same
generated name or assumption surface.
