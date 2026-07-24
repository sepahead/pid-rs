# Evidence matrix for SX-SUPPORT-FREE-CONTINUITY-001

This matrix describes revision 3. Revisions 1 and 2 remain retained as historical claim
boundaries and are not silently rewritten.

## Evidence rule

A paper citation establishes provenance for a paper-defined object. It does not prove the new
closed-simplex theorem. An abstract formal lemma establishes only its stated algebra. It does not
identify that algebra with SxPID.

| Statement | Origin | Retained evidence | Evidence status | Remaining boundary |
|---|---|---|---|---|
| An antichain event is a union of source-collection conjunctions. | Paper-defined | Makkeh et al. Eqs. (4), (6)–(8); Gutknecht et al. Eq. (3.7); the checked heterogeneous finite event bridge | Source and project event predicate checked | Machine-checked bibliographic identification and Rust implementation map |
| The local informative and misinformative cumulatives have the formulas in conventions.md. | Paper-defined | Makkeh et al. Eqs. (14a), (15a), and (15b) | Source checked | Zero-mass keys are outside the local formula |
| Pointwise cumulatives and atoms obey the down-set zeta relation. | Paper-defined | Makkeh et al. Eq. (13), Appendix Eq. (A1), Theorem A.1; Gutknecht et al. Eq. (3.8) | Source checked | Concrete matrix orientation in project artifacts |
| The antichain, parthood, and logical structures are isomorphic lattices. | Paper-defined | Gutknecht et al. Definition 1, Eqs. (2.8)–(2.10), Theorem 1, Corollary 1 | Source checked | Full project lattice and node-order equivalence |
| Pointwise informative and misinformative component atoms are nonnegative. | Paper-defined | Makkeh et al. Theorem IV.3 and Appendix A | Source checked | Only the exact full-lattice SxPID components |
| Averaged cumulatives use the original joint-law weights. | Paper-defined | Makkeh et al. Eq. (17) and its discussion | Source checked | Rigorous support-boundary totalization |
| Variable-level atoms average pointwise atoms. | Paper-defined | Gutknecht et al. Eq. (3.3) | Source checked | Commutation with direct averaged inversion |
| Averaged component atoms are nonnegative. | Paper-derived corollary | Pointwise nonnegativity plus nonnegative law weights | Exact prose inference | Boundary convention and semantic identification |
| Net atoms can be negative. | Paper-defined consequence and example | Makkeh et al. Table III RndErr example | Source checked | None; this limits the new theorem’s wording |
| The defining paper proves differentiability on the simplex interior. | Paper-defined | Makkeh et al. Section IV.B | Source checked | It does not cover support faces |
| Averaged categorical SxPID is quantitatively continuous across support changes on a fixed finite alphabet. | Project theorem | [`claim-v3.md`](claim-v3.md), incorporated [`claim-v2.md`](claim-v2.md), the exact prose derivation, and the reproducible standalone PDF | Analytically proved and manuscript-red-team checked | End-to-end formal Sx semantic closure remains open |
| The equivalence-union common load is at most $J\eta$. | Project theorem | Generic fractional-cover proof, exact equality witness, and `FractionalCover.lean` | Checked analytically and in Lean for the stated finite-event map | The logarithmic transfer from $T_N$ to $g_J$ and identification with every paper-defined common term remain unformalized |
| A global linear modulus is false. | Project counterexample | Corrected $T=S_1$ construction in [`failures/exact-counterexamples.md`](failures/exact-counterexamples.md) | Checked exactly and replayed | Does not by itself prove an upper modulus |
| The required boundary order is at least $\eta\log(1/\eta)$. | Project lower obstruction | Binary-entropy value in the corrected construction | Checked symbolically | This order-only witness alone does not determine a common leading coefficient; the separate fixed-system family obstruction is stated next |
| A family of covered fixed-system bounds with a common leading coefficient and system-dependent $O_{\mathcal F}(\eta)$ remainder cannot use component and net coefficients below one and two, respectively. | Project worst-case lower obstruction | Exact fixed-system copied-source, constant-target, and unique-net formulas in [`claim-v3.md`](claim-v3.md) and the exact prose derivation | Checked symbolically | Not an alphabet-independent modulus; not every system or atom attains the coefficients; lower-order constants and individual full bounds are not claimed sharp |
| Finite-vector, entropy, generic matrix, scalar-modulus, heterogeneous keyed Sx event, and finite fractional-cover lemmas are machine checked. | Project formal evidence | `SupportChangeContinuity.lean`, `SxEventBridge.lean`, `FractionalCover.lean`, the theorem map, and the pinned checker and axiom-basis gate | Checked partial evidence | Probability-law bundling, logarithmic transfer, concrete lattice and published sign theorem, averaged Sx composition, and Rust identification |
| Exact witnesses and a bounded public-API replay are reproducible. | Project executable evidence | Tracked generator, immutable fixture and digest, and `support_change_tolerant_sxpid_oracle.rs` | Checked for the committed bounded domain | Not a universal proof, authorship-independent audit, refinement theorem, or binary64 enclosure |
| Rust returns the exact-real functional with a certified error. | Separate implementation claim | None in this packet | Out of scope | Executable refinement and transcendental error |
| The theorem has scientific priority. | No claim | No priority evidence | Not asserted | Independent scholarly review would be required |

## Source pins

1. Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral, “Introducing a differentiable measure
   of pointwise shared information,” *Physical Review E* 103, 032149 (2021):
   [DOI](https://doi.org/10.1103/PhysRevE.103.032149),
   [arXiv v5](https://arxiv.org/pdf/2002.03356v5).
   Audited arXiv PDF SHA-256:
   `5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6`.
2. Aaron J. Gutknecht, Michael Wibral, and Abdullah Makkeh, “Bits and pieces: understanding
   information decomposition from part-whole relationships and formal logic,”
   *Proceedings of the Royal Society A* 477, 20210110 (2021):
   [DOI](https://doi.org/10.1098/rspa.2021.0110),
   [PMC8261229](https://pmc.ncbi.nlm.nih.gov/articles/PMC8261229/),
   [arXiv v2](https://arxiv.org/pdf/2008.09535v2).
   Audited arXiv PDF SHA-256:
   `dc65320690c85aa9617a0af469692200f991f24784aac5d7399fa2c6854533d3`.
3. The audited Europe PMC XML for PMC8261229 came from
   [the full-text endpoint](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8261229/fullTextXML).
   SHA-256: `c3c6f6882e37105856843c3abdd74a11e77c25abe3b9fd20e02673865f0fe652`.

## Related primary sources that do not close the claim

- Kyle Schick-Poland et al., “A partial information decomposition for discrete and continuous
  variables,” [arXiv v2](https://arxiv.org/pdf/2106.12393v2), gives a measure-theoretic extension
  and density differentiability. It does not state this fixed-finite-alphabet total-variation
  theorem.
- David A. Ehrlich et al., “Partial Information Decomposition for Continuous Variables based on
  Shared Exclusions: Analytical Formulation and Estimation,”
  [DOI](https://doi.org/10.1103/PhysRevE.110.014115),
  [arXiv v3](https://arxiv.org/pdf/2311.06373v3), concerns a continuous analytical functional and
  estimator. It is outside this claim.

## Literature-search status

A primary-literature and citing-corpus search was performed through 2026-07-24. It did not identify
an explicit categorical SxPID total-variation modulus on the closed finite simplex that permits
support changes. This negative search result does not establish priority.
