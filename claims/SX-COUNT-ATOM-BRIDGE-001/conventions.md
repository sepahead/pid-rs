# Conventions for SX-COUNT-ATOM-BRIDGE-001 revision 2

## Scope notation

Let `count : CategoricalKey (Fin 2) sourceValue targetValue → Nat` be a total function on the
complete finite key type. Write

- `N = totalCount count`;
- `Z+ = positiveSupport count`;
- `c(z) = count z` for `z ∈ Z+`;
- `E_alpha(z)` for the source event at node `alpha` and anchor `z`;
- `T(z)` for the target branch at `z`; and
- `E_alpha,t(z) = E_alpha(z) ∩ T(z)`.

Write the corresponding event counts as `C_alpha(z)`, `C_t(z)`, and `C_alpha,t(z)`. The inherited
count/event bridge proves these counts are positive for every `z ∈ Z+`; their positivity is not
added as a separate axiom.

## Cumulative nodes

The exact node order is:

| Position | Lean constructor | Source-event meaning | Informal symbol |
|---:|---|---|---|
| 1 | `sourceOne` | source one matches the anchor | `C_1` |
| 2 | `sourceTwo` | source two matches the anchor | `C_2` |
| 3 | `jointSources` | both sources match the anchor | `C_12` |
| 4 | `redundancy` | source one or source two matches the anchor | `C_R` |

The final column names cumulative quantities, not atoms. In particular, `sourceOne` is not the
unique-one atom, `sourceTwo` is not the unique-two atom, and `jointSources` is not synergy.

The correspondence to Rust `NODES2` is an intended semantic alignment only. No theorem in this
packet relates the Lean definitions to Rust source code or executable values.

## Components

The exact component order is:

| Position | Lean constructor | Local count argument `q` | Local value |
|---:|---|---|---|
| 1 | `informative` | `N / C_alpha(z)` | `log q` |
| 2 | `misinformative` | `C_t(z) / C_alpha,t(z)` | `log q` |
| 3 | `net` | `N C_alpha,t(z) / (C_alpha(z) C_t(z))` | `log q` |

On positive support,

```text
q_net = q_informative / q_misinformative
i_net = i_informative - i_misinformative.
```

“Misinformative” is the established component label. The signed net subtracts that component; no
silent clamping is permitted.

## Atoms and the concrete Möbius transform

The exact atom order is:

| Position | Lean constructor | Formula from cumulatives |
|---:|---|---|
| 1 | `uniqueOne` | `C_1 - C_R` |
| 2 | `uniqueTwo` | `C_2 - C_R` |
| 3 | `synergy` | `C_12 - C_1 - C_2 + C_R` |
| 4 | `redundancy` | `C_R` |

With cumulative column order `[C_1, C_2, C_12, C_R]` and atom row order `[U1, U2, S, R]`, the
integer Möbius matrix is

```text
[ 1  0  0 -1 ]
[ 0  1  0 -1 ]
[-1 -1  1  1 ]
[ 0  0  0  1 ].
```

The inverse zeta transform reconstructs `[C_1,C_2,C_12,C_R]` from `[U1,U2,S,R]` by

```text
C_1  = U1 + R
C_2  = U2 + R
C_12 = U1 + U2 + S + R
C_R  = R.
```

The same transform is applied separately to informative, misinformative, and net cumulatives.

## Coordinate order

The checked ordered coordinate list is grouped first by kind, then component, then lattice
position:

```text
cumulative informative:     C1+, C2+, C12+, CR+
cumulative misinformative:  C1-, C2-, C12-, CR-
cumulative net:             C1n, C2n, C12n, CRn
atom informative:           U1+, U2+, S+, R+
atom misinformative:        U1-, U2-, S-, R-
atom net:                   U1n, U2n, Sn, Rn
```

This is a project-defined ordering contract over paper-defined quantities. It is not yet a proved
serialization or result-field refinement.

## Averaging convention

For any local component value `i_component(alpha,z)`, the averaged cumulative is

```text
sum over z in Z+ of (c(z) / N) * i_component(alpha,z).
```

The averaged pointwise atom uses the same weights after local Möbius inversion. The checked module
proves that finite weighted averaging commutes with the concrete Möbius transform. It inserts no
pseudo-count, smoothing, renormalization, or alternate weight.

## Exact products

For one cumulative, the product is

```text
R_component,alpha = product over z in Z+ of q_component(alpha,z) ^ c(z).
```

Atom products apply the Möbius coefficients multiplicatively:

```text
R_U1 = R_C1 / R_CR
R_U2 = R_C2 / R_CR
R_S  = (R_C12 * R_CR) / (R_C1 * R_C2)
R_R  = R_CR.
```

Every local argument and every resulting real product is positive. Exact rational counterparts
are retained before casting to real numbers. The mathematical value is `(1/N) * log R`.

## Proof and scope discipline

- Natural logarithms imply nats.
- Zero-count complete keys are permitted but excluded from `Z+`.
- `N > 0` is required for all main empirical and product theorems.
- The coordinate-exchange map swaps source-one/unique-one with source-two/unique-two and fixes
  joint, synergy, and redundancy. It is formula equivariance for an arbitrary cumulative function,
  not a transported permutation of heterogeneous source types, keys, counts, laws, or events.
- A sign equivalence is not a universal sign theorem.
- Acceptance is limited to the exact SHA-bound source and the revision-2 residual boundary.
- Paper-defined mathematics and project-defined formalization must remain separately labeled.
