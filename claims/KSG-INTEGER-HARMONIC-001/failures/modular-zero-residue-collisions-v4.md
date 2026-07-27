# Retained negative control: modular zero-residue collisions

## Refuted inference

The inference

```text
T mod p = 0  =>  exact rational T = 0
```

is false even when prime `p` exceeds every reciprocal-summand denominator/index occurring in the
frozen row.

## Counterexamples

For rejected prime `p=1000003`, the ordered u32 big-endian residue-vector digest is

```text
d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111.
```

Four nonendpoint rows have zero residue:

```text
index 8045: (1000000,3,2,3),         T =  H_999999 - H_3 > 0
index 8049: (1000000,3,3,2),         T =  H_999999 - H_3 > 0
index 8069: (1000000,4,3,3),         T =  H_999999 - H_3 > 0
index 8093: (1000000,4,999999,999999), T = H_3 - H_999999 < 0.
```

The strict signs follow because `sum_(j=4)^999999 1/j` is a nonempty sum of positive rationals.
These are exact counterexamples, not binary64 observations.

## Elementary reflection mechanism

For an odd prime `p` and the field-valued harmonic prefix

```text
H_j = sum_(r=1)^j r^(-1) mod p,
```

pairing `r` with `p-r` gives `H_(p-1)=0`. The last `t` summands are
`sum_(u=1)^t (p-u)^(-1) = -H_t`, hence

```text
H_(p-1-t) = H_t mod p.
```

For the rejected `p=1000003`, the maximum frozen index is `999999=p-4`, so
`H_999999=H_3 mod p`. The first three counterexamples equal
`H_999999-H_3` and the fourth is its negative. They are four signed/order copies of one reflected
field event, not four independent collisions. This elementary identity is sufficient; no stronger
number-theoretic theorem is being invoked.

## Accepted implication

If `p` exceeds the maximum reciprocal-summand denominator/index, then every `1/j` summand
denominator is invertible in the field. Exact rational zero must reduce to residue zero. Therefore
the contrapositive is sound:

```text
nonzero residue => exact rational nonzero.
```

The converse is not sound. Selected primes `1000033`, `1000037`, and `1000081` happen to have
nonzero residue at all 7,844 frozen nonendpoints. Combining that bounded separation with pairwise
structural cancellation proves an iff only for the exact ordered 8,198-row corpus.

The selected fields share the same reflection mechanism:

```text
p=1000033: H_999999 = H_33 mod p
p=1000037: H_999999 = H_37 mod p
p=1000081: H_999999 = H_81 mod p.
```

Index 33 occurs in the frozen corpus. Even where a reflected index is absent from a simple index
inventory, absence alone does not establish that every four-term residue is nonzero. Therefore
neither index co-occurrence nor its absence is the selected-prime proof. Exact exhaustive replay of
the canonical certificate is the authority for finite-corpus separation.

## Certificate-type firewall

An adversarial replay also found that Python scalar equality could treat
`certificate_revision: 1` as equal to `true` and
`residue_encoding.include_zero_residues: true` as equal to `1`. After rebasing the certificate,
sidecar, and checker digest, both substitutions passed the former checker. The repaired route uses
recursive path-aware equality of JSON shape, scalar type, and value for static sections and
replayed selected/rejected records. These type-firewall controls are separate from the 28
registered modular scientific/custody mutations. Normal and optimized replay rejects both `2/2`
controls while retaining `28/28` registered modular mutation kills.

The registered composite-modulus mutation uses `1000001=101*9901`. It is above `999999` and is
not divisible by the checker's small-prime prefilter set 2 through 37, so its expected rejection
reaches the deterministic u32 Miller--Rabin witness loop. This replaced the former `1000035`
control, which stopped at divisibility by 5; it does not increase the 28-mutation inventory.

## Independence and non-implications

The selected triple provides redundant fault diversity. It is not CRT reconstruction and the
three fields are not three independent mathematical proofs: they share the row corpus, exact
formula, human index map, generator class, and reflection structure. Strict JSON typing supplies
local representation custody, not authenticity or arithmetic proof. The result classifies no
harmonic zeros outside the corpus and proves nothing about KSG neighbor geometry, MI estimation,
Ehrlich shared exclusions, MGW SxPID, any PID atom, support, calibration, or applications.

The pre-artifact digest
`1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc`
is retained only as a first observation. Canonical current custody is
`5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f`.
