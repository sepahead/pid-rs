# Obligations for SX-SUPPORT-FREE-CONTINUITY-001

## Status terms

- **Closed:** retained evidence completes the stated obligation.
- **Closed analytically:** the exact prose proof completes the mathematical obligation; this does
  not assert that the same path is machine checked.
- **Partial:** retained evidence proves only listed subclaims.
- **Open:** no retained evidence completes the obligation.
- **Out of scope:** another claim packet is required.

## Obligation graph

```text
P1 primary-source provenance
  -> S1 exact event and lattice semantics
  -> N1 component nonnegativity scope

B1 boundary totalization
  -> A1 averaged cumulative continuity

R1 overlap and residual algebra
E1 residual entropy control
G1 common-overlap event control
  -> A1 averaged cumulative continuity

S1 + N1 + R1 + E1 + G1
  -> A2 averaged component-atom continuity

M1 fixed Möbius and averaging commutation
  -> A2 averaged component-atom continuity

A2
  -> A3 averaged net-atom continuity

A1 + A2 + A3 + C1 exact counterexample audit
  -> Z1 exact-real analytic adjudication

Z1 + O1 exact leading-order lower constructions
  -> Z2 revision-3 asymptotic adjudication

F1 complete machine-checked semantic closure
  -> parallel formal-strengthening claim, not a prerequisite for Z1 or Z2
```

## Detailed obligations

| ID | Obligation | Status | Completion evidence |
|---|---|---|---|
| P1 | Identify immutable primary sources for event semantics, the lattice, averaging, Möbius inversion, and component nonnegativity. | Closed for source mapping | [route-memos/provenance.md](route-memos/provenance.md) and source hashes |
| S1 | Identify the theorem's fixed event predicate with the published union of source-collection conjunctions, including target intersection semantics. | Closed analytically | Primary-source map and Section 4 of the exact prose derivation; Rust identification remains I1 |
| N1 | Transfer Makkeh et al. Theorem IV.3 to every supported key on the fixed full lattice and then to averaged component atoms. | Closed analytically | Primary theorem, top-node reconstruction, and component residual argument in Sections 5 and 6 |
| B1 | Define the averaged functional on the closed simplex without evaluating a local logarithm at a zero-mass key. | Closed analytically | Fixed ambient event map, anchor condition, and support-restricted sums in Sections 2 and 4 |
| R1 | Prove exact overlap and residual identities for two probability vectors. | Closed | Exact prose identities and checked Lean finite-vector subclaims |
| E1 | Bound residual-weighted component and signed terms by residual entropy, with the exact zero convention. | Closed analytically | Theorems 1, 3, and 4; Lean checks the abstract conditional transfer |
| G1 | Bound the common-overlap change for each paper-defined antichain event. | Closed analytically | Residual-plus-load theorem, fractional-cover lemma, endpoints, and paper-semantic equality witness |
| A1 | Prove closed-simplex continuity of every averaged informative, misinformative, and net cumulative. | Closed analytically | Theorem 3 and finite-alphabet residual envelopes |
| M1 | Prove the fixed zeta/Möbius orientation, row identities used by the proof, and commutation of finite inversion with averaging. | Closed analytically | Full-lattice least-node argument, finite linearity, Lean generic row identity, and exact two-to-four-source replay |
| A2 | Prove closed-simplex continuity of every averaged informative and misinformative atom. | Closed analytically | Theorem 4, using N1, A1, and M1 |
| A3 | Prove closed-simplex continuity of every averaged net atom without asserting net nonnegativity. | Closed analytically | Theorem 4 and the component difference identity |
| C1 | Retain exact falsifiers and scope guards for invalid stronger claims and proof shortcuts. | Closed for the committed constructions | [failures/exact-counterexamples.md](failures/exact-counterexamples.md), generator, and bounded Rust replay |
| O1 | Prove with fixed-system witnesses that a family of covered fixed-system bounds cannot use a common leading $\eta\log(1/\eta)$ coefficient below one for components or two for net atoms, even when its $O_{\mathcal F}(\eta)$ remainder is system-dependent. | Closed analytically | Exact fixed-system law paths and symbolic limits in [`claim-v3.md`](claim-v3.md) and Section 9.6 of the prose derivation |
| Z2 | Adjudicate the Revision 3 exact-real asymptotic extension without promoting lower-order sharpness. | Closed analytically | O1 plus the Revision 2 upper envelopes; explicit sharpness-scope guard in [`claim-v3.md`](claim-v3.md) |
| F1 | Machine-check the complete categorical SxPID semantic path used by the theorem. | Partial | Lean checks exact heterogeneous keyed Sx events, their anchors and target intersection, law independence, positive event masses, and the finite equivalence-union load bound. Probability-law bundling, the logarithmic transfer to $g_J$, the concrete lattice and published sign theorem, averaging, complete composition, and Rust refinement remain open |
| I1 | Connect exact-real quantities to the Rust categorical implementation and binary64 outputs. | Out of scope | Separate implementation-refinement and numerical-error claims |
| T1 | Prove estimator consistency, concentration, or uncertainty calibration. | Out of scope | Separate probabilistic or statistical claim |
| Z1 | Adjudicate the quantitative revision-2 exact-real analytic claim while retaining revision 1 as history. | Closed analytically | Exact derivation, primary semantics, retained falsifiers, Lean scope map, implementation-separated generator, bounded Rust replay, and manuscript red-team review agree |

## Required formal scope statement

The analytic proof closes the listed mathematical obligations. The current formal artifact does
not. It checks the fixed finite event predicates and their fractional-cover load route, but must
continue to state which probability-law, logarithmic-transfer, concrete-lattice, published-sign,
averaging, and implementation premises remain outside the checked composition.

## Required counterexample checks

The Z1 evidence includes:

- support creation and deletion;
- a cell with mass tending to zero;
- constant and copied sources;
- $T=S_1$ with a constant second source;
- XOR and the published RndErr example;
- every lattice coordinate for each claimed source count;
- informative, misinformative, and net output;
- both endpoints $\eta=0$ and $\eta=1$ for any quantitative modulus.

The tracked support-change oracle covers support creation/deletion, vanishing cells, constant and
copied sources, the $T=S_1$ family, every returned lattice coordinate for its two-to-four-source
tables, component and net outputs, and modulus endpoint records. Existing reference tests retain
XOR and the paper's nonuniform RndErr example; the RndErr test explicitly checks its negative
averaged unique-$S_2$ net atom. These bounded cases challenge the analytic proof. They do not
replace it or extend it beyond the fixed objects in revision 2.
