# Corrected Python typed-equality false greens

## Disposition

**Real verification-chain defects; corrected in the current candidate before any integration to
`main`; no mathematical result or Program status changed.**

The pre-correction committed Program-A-v4 checker at commit
`ee93b97fc779191306e34efc02c5ff2c78bc4162` used ordinary Python equality at two acceptance
boundaries:

1. decoded JSON record objects were compared with their expected objects; and
2. literals parsed from two frozen Python compatibility files were compared with the
   definition-generated carrier, zeta, and Möbius objects; a third compatibility input is the
   Markdown convention ledger rather than a Python file.

Python makes Boolean values a subtype of integers and compares equal-valued integers and
floating-point numbers numerically. Consequently,

```text
False == 0       -> True
True == 1        -> True
5.0 == 5         -> True
129.0 == 129     -> True
```

Those pairs have the same Python value under `==`, but they do not have the same JSON or Python
literal type. This distinction matters because the evidence contract requires integer Program
counts and claims exact compatibility with typed frozen registries.

## Minimal reproductions

Four isolated fixtures started from the exact pre-correction v4 packet. Each fixture changed one
typed value and coherently resealed every owner-controlled digest and byte-count field that covered
the changed input:

| Boundary | Required value | Mutant value | Pre-correction result | Correct result |
|---|---:|---:|---|---|
| JSON `programs_closed` | integer `0` | Boolean `false` | Accepted | Rejected |
| JSON `programs_total` | integer `5` | floating `5.0` | Accepted | Rejected |
| Primary-route Möbius tuple index | integer `0` in `(0, 1)` | Boolean `False` in `(False, 1)` | Accepted | Rejected |
| Independent-route zeta census | integer `129` | floating `129.0` | Accepted | Rejected |

For a JSON mutation, the fixture updated the record binding in the checker. For a compatibility
mutation, it updated that Python file's binding in both the checker and record, then updated the
record binding in the checker. This models a coherent owner-controlled reseal; an unresealed byte
change was already rejected earlier by the digest checks.

The old checker still printed fixed success text containing `Programs closed 0/5`, `129 order
pairs`, and `65 nonzero Mobius entries`. Thus its stdout could conceal a decoded or parsed type
drift. The fixtures did not change any numeric value, reconstructed carrier, order, Möbius inverse,
event truth table, source permutation, equation, or accepted/open scientific disposition.

## Cause and repair

The cause was reliance on Python value equality where the evidence claim required equality of type,
shape, and value. Checking only the four discovered leaves would leave the same coercion mechanism
available elsewhere. The corrected checker therefore uses one recursive comparator with this rule
at every supported node:

```text
type(actual) is type(expected), and then keys/elements/values agree recursively
```

The comparator covers all ten verdict-bearing decoded-record fields and all six parsed
compatibility-registry comparisons. The hostile self-test now exercises all four substitutions in
normal and optimized isolated Python. The two JSON substitutions contribute four record-reseal
executions. The two frozen-literal substitutions contribute four separately counted
compatibility-reseal executions. The PDF publication wrapper retains its independent exact JSON
status check as defense in depth; that wrapper does not replace the authoritative Program-A
checker and does not parse the Python compatibility registries.

## Exact pre-correction evidence retained

The pre-correction objects remain recoverable from commit
`ee93b97fc779191306e34efc02c5ff2c78bc4162`:

| Object | Bytes | SHA-256 | Disposition |
|---|---:|---|---|
| Source correspondence v4 | 33,942 | `b4e6fbcdc289e7a8e6c3af42509b568606e61b8908b59661b895bd9ca5eb72cb` | Superseded evidence narrative |
| Semantic-bridge record v4 | 17,458 | `dbc43a78e88d5e35cce5e01ec69f676eef8c68bda2f5eae5994f61d21fe5db24` | Superseded validation contract |
| Production checker v4 | 41,953 | `394361524372710179aea41f95f4ddf9559700082a80e02ac0d0a34fbe08ce4a` | Rejected as acceptance evidence for typed equality |
| Hostile self-test v4 | 20,348 | `fadd73671fca24f7300c690d430db2f0caff893aa5b837698ba739f578749be8` | Incomplete for both fault classes |

These bytes remain useful negative evidence. They must not be restored over the corrected current
files or cited as proving exact typed record or registry equality.

## Scope and nonimplications

This correction proves rejection of the four named substitutions and removes the same Python
numeric-coercion mechanism from the compared record and registry structures. It does not prove that
the mutation set is complete, that arbitrary Python literals are accepted input, that the JSON
record is a reusable untrusted certificate schema, that the publication correspondence is correct,
or that the checker is independent of its owner. It also does not close Program A, Programs B--E,
canonical-input obligation D1, formal Fin-3 semantics, logarithm enclosures, Rust refinement,
statistical inference, or application validity.
