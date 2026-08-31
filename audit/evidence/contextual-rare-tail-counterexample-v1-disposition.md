# Contextual rare-tail counterexample disposition

Status: **retained conditional numerical negative result; not a PID-theorem defect**.

The evidence JSON and its two checkers are exact bytes from snapshot
`df22846a66bf439b5ee8642166b0599de03a7835` (tree
`77cf10062d9dce6fcf123187c10ac288694185e0`). They establish one narrow
conditional statement:

| Retained artifact | Bytes | SHA-256 | Source blob |
|---|---:|---|---|
| `audit/evidence/contextual-rare-tail-counterexample-v1.json` | 2,869 | `7c8b0dc372cbbe1f9844887750a5726965c5115ba5f61e1a8ee2f47b4a673795` | `aef14c2f8929ad75640744ed29a5114869cea6c9` |
| `scripts/check-contextual-rare-tail-counterexample.py` | 12,891 | `f81ee023efb32855985c787bc428f98ddb880dbf02e08abb11d6fa76af6aa796` | `c3dba9edbd0bd93aab94167be50444a9555e2744` |
| `scripts/check-contextual-rare-tail-counterexample-self-test.py` | 7,400 | `565ea55eb0f8a7306b65631ff73f839b94460c4c1b053cdc7ef5387b75d3f290` | `d7ffa775f873ad79371fe4bb9ae262f57ce5cc4f` |

1. take `q=222493/250000`, source-cell mass `q/2`, and `r=c=2`;
2. use exactly `A_m=(r/2)(1+exp(rc))` and `A_b=A_m+c`;
3. interpret the analytical logistic zero-response tails in exact real arithmetic;
4. implement the displayed runtime route as IEEE-754 binary64 round-to-nearest,
   ties-to-even, computing the zero-response probability as `1.0 - p`; and
5. use the stated Taylor enclosures and positive-tail bounds.

Under only those premises, both analytical zero-response cells are strictly positive
but below the binary64 half-gap at one, while the displayed binary64 route rounds
`p` to `1.0` and erases each tail to `0.0`. This is an implementation-level
support-loss witness for those formulas and bytes. Units are probability mass, not
bits or nats.

It does **not** refute or validate categorical MGW SxPID, the Schick-Poland
measure-theoretic construction, Ehrlich continuous shared exclusions, BROJA, any
Wibral-coauthored theorem, rounded headline atom values, support-change continuity,
or a current pid-rs estimator. The external source hashes are observations of dirty
working bytes; they do not authenticate authorship, publication status, or provenance.

The source snapshot also added `pid-publication-result-ledger-v1.json`. That ledger is
deliberately rejected from integration: it aggregates stale publication-state claims
and is not needed to verify this self-contained numerical counterexample. Its source
identity is retained only as a rejection record: 107,376 bytes, SHA-256
`049d121c05d7f1e4a43ab9be4fefa1d23867edf9758088b7455e95d23f1a4f58`,
Git blob `f7a6975329b9a471fabb1090c66ec68f389b1b4e` at the snapshot above.

Run all four checks:

```text
python3 -I -S -B scripts/check-contextual-rare-tail-counterexample.py
python3 -O -I -S -B scripts/check-contextual-rare-tail-counterexample.py
python3 -I -S -B scripts/check-contextual-rare-tail-counterexample-self-test.py
python3 -O -I -S -B scripts/check-contextual-rare-tail-counterexample-self-test.py
```

A passing check proves only the exact bounded statement encoded by the evidence. It
does not supply source authenticity, general logistic stability, estimator validity,
or application fitness.
