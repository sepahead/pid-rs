# Conventions for SX-COUNT-EVENT-BRIDGE-001 revision 2

## Complete key and counts

For heterogeneous source alphabets `sourceValue : Fin 2 → Type` and target alphabet
`targetValue`, a complete categorical key is

```text
((source : Fin 2) → sourceValue source) × targetValue.
```

`count : CategoricalKey ... → Nat` is total on that finite type. `Nat` supplies nonnegativity;
individual values may be zero. `totalCount count > 0` is required for scientific use of the
empirical law. Lean's division is total at zero, but no normalization, logarithm, or main theorem
interprets a zero-total table as an empirical distribution.

## Positive support

```text
positiveSupport count = {key | 0 < count key}.
```

Only this support is averaged and passed to a logarithm. A supported anchor belongs to its source,
target, and target-restricted events, so every associated event count is at least the positive
anchor count.

## Fixed cumulative node semantics

| Lean node | Source collections | Rust cumulative analogue |
|---|---|---|
| `sourceOne` | `{{0}}` | `NODES2[0]` |
| `sourceTwo` | `{{1}}` | `NODES2[1]` |
| `jointSources` | `{{0,1}}` | `NODES2[2]` |
| `redundancy` | `{{0},{1}}` | `NODES2[3]` |

This table is a mathematical semantic correspondence, not a formal Rust refinement. Cumulative
`sourceOne` and `sourceTwo` are not unique-information atoms, and cumulative `jointSources` is not
the synergy atom.

## Event and count notation

For node `alpha` and anchor `x`:

- `E_alpha(x)` is its source event;
- `T(x)` is the target-matching event;
- `E_alpha,t(x) = E_alpha(x) ∩ T(x)` is its target-restricted event;
- `C_alpha(x)`, `C_t(x)`, and `C_alpha,t(x)` are exact natural event counts; and
- `N` is total count.

Redundancy is an event union. Its exact natural count is handled first as

```text
C_red + C_joint = C_source_one + C_source_two,
```

then as the natural-subtraction corollary

```text
C_red = C_source_one + C_source_two - C_joint.
```

The joint-source target-restricted event is the anchor singleton.

## Local and averaged quantities

The informative and misinformative cumulatives are

```text
i_plus  = -log P(E_alpha(x)),
i_minus =  log(P(T(x)) / P(E_alpha,t(x))).
```

Their signed net is `i_plus - i_minus`, hence

```text
log(P(E_alpha,t(x)) / (P(E_alpha(x)) * P(T(x))))
  = log(N * C_alpha,t(x) / (C_alpha(x) * C_t(x))).
```

`countNetArgument` is an exact rational value. The formal result claims equality of values, not a
canonical numerator/denominator syntax or serialized exact-expression format. Logs are natural
logs, so all information quantities are in nats.

## Proof and scope discipline

- Kernel `decide` may discharge finite closed propositions.
- `native_decide` is forbidden because its generated evaluator axiom lies outside the permitted
  source-theorem assumption basis and semantic examples are checked separately.
- The only permitted audited assumptions are `propext`, `Classical.choice`, and `Quot.sound`.
- The Lean theorem begins from a supplied exact count function. All representation, Rust,
  executable, numerical, and statistical refinement edges listed in `claim-v2.md` remain open.
