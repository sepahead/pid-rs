# Revision-2 retained negative controls for SX-CERTIFIED-AVERAGED-PID2-001

These controls extend, rather than replace,
[retained-negative-controls.md](retained-negative-controls.md).

## V2-NC1: nonempty logarithms can cancel exactly

In canonical binary state order, counts

```text
[0,0,1,1,1,4,1,0]
```

have total count eight. The net `unique_one` atom has the nonempty five-term expression

$$
-\frac18\log\frac8{15}
+\frac18\log\frac45
+\frac18\log\frac89
+\frac18\log\frac43
-\frac18\log\frac{16}{9}.
$$

After denominator clearing, its product is exactly one. The dyadic interval contains zero but
remains `unresolved_sign`; the separate product record is `certified_exact_zero`. This falsifies
the stronger claim “canonical expression is zero if and only if its term map is empty.”

## V2-NC2: product evidence cannot be trusted from certificate text

The mutation suite changes product status, decision, witness, term count, exponent, projected
bits, and aggregate admission while resealing the payload. The independent verifier reconstructs
all fields from the input and rejects the registered forgeries.

## V2-NC3: preflight must precede powering

An accepted parser can represent counts far larger than the product comparator permits as
exponents. A mutant that powers first can allocate an enormous integer before discovering a
policy violation. The reviewed route computes exponent and bit-growth evidence first and leaves
powered values unmaterialized for rejected plans. Two self-test sentinels replace the auxiliary
checker's power primitive with a fail-on-call function. One locally inadmissible plan and one
aggregate-inadmissible plan both reject while the sentinel records zero calls. This tests the
reviewed control-flow order; it is not a universal runtime cost proof.

## V2-NC4: aggregate admission is not per-coordinate admission

Every coordinate can satisfy its local ceilings while their sum exceeds the aggregate projected
bit limit. The aggregate decision is computed across all locally admissible plans. A report may
not mark a nonempty coordinate `compared` when aggregate admission fails.

## V2-NC5: exact sign does not replace magnitude enclosure

The inequality $R>1$ proves $F>0$ but does not provide a narrow value interval. Conversely, a
dyadic interval containing zero can enclose the correct value without deciding its sign. The
certificate retains both records, and the verifier rejects sign/enclosure contradictions without
rewriting either decision lane.

## V2-NC6: evolutionary failure to find is not proof

A deterministic bounded evolutionary search attempted to find a negative informative or
misinformative partial atom at total count 64. It evaluated 5,921 unique tables and found no
counterexample. This is useful adversarial evidence only. It is not a universal nonnegativity
theorem, and no such theorem enters the claim.

## V2-NC7: old schemas cannot inherit new semantics

Revision 1 explicitly required re-adjudication after schema, resource-policy, source-manifest,
verifier, or sign-semantics changes. Treating a version-1 decision as authority for a version-2
certificate would violate that rule even if the underlying mathematical functional is unchanged.
The revision index and repository gate therefore require distinct claims, decisions, and bindings.

## Boundary

Passing these controls shows sensitivity to named faults. It does not prove absence of unnamed
faults, runtime correctness, public immutable custody, statistical validity, or downstream safety.
