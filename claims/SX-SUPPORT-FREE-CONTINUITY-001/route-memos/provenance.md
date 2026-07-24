# Provenance route memo

## Route record

| Field | Value |
|---|---|
| Route ID | `SX-SUPPORT-FREE-CONTINUITY-001-PROVENANCE-01` |
| Claim revision | 1 |
| Date | 2026-07-24 |
| Mathematical family | Primary-source provenance, finite lattice semantics, and boundary audit |
| Independent starting point | Final primary papers and versioned author manuscripts |
| Current obligation | P1, with inputs to S1, N1, B1, M1, and C1 |
| Evidence label | `CHECKED-EXACTLY` for source locations and hashes only |
| Route status | P1 closed; at this revision-1 route checkpoint, theorem obligations remained open |

This memo is retrospective. The source review and claim drafting occurred after exploratory project
work had started. The route was not preregistered. The source checker also drafted this packet, so
this is not an independent final audit.

## Strongest established result

The immutable primary sources establish all of the following:

1. The source-collection event is a conjunction.
2. An antichain event is the disjunction, or event union, of those conjunctions.
3. The local shared-exclusions cumulative is a local mutual-information expression.
4. It separates into informative and misinformative logarithmic components.
5. Pointwise atoms are the Möbius inverse on the full finite redundancy lattice.
6. Informative and misinformative pointwise atoms are nonnegative.
7. Variable-level cumulatives and atoms are joint-law averages of local quantities.

The sources do not establish continuity across support faces or a total-variation modulus without a
positive cell-mass floor.

## Exact primary-source locations

### Makkeh, Gutknecht, and Wibral

Primary record:

- [Physical Review E DOI](https://doi.org/10.1103/PhysRevE.103.032149)
- [final arXiv v5](https://arxiv.org/pdf/2002.03356v5)
- audited PDF SHA-256:
  `5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6`

Relevant locations:

- Eqs. (4), (6)–(8): branch events, union-of-conjunctions statement, and local cumulative.
- Eq. (12): shared-exclusion probability expression.
- Eq. (13): pointwise zeta relation.
- Eqs. (14a), (15a), and (15b): informative, misinformative, and net split.
- Theorem IV.2: component monotonicity in the redundancy-lattice order.
- Theorem IV.3: nonnegative informative and misinformative component atoms.
- Section IV.B: differentiability only over the simplex interior.
- Eq. (17): joint-law average of local cumulatives.
- Appendix Eq. (A1) and Theorem A.1: component Möbius inversion.
- Appendix Proposition A.2 and the proof of Theorem IV.3: cumulative and atom nonnegativity.
- Section VI.B and Table III: negative net shared and unique examples.

### Gutknecht, Wibral, and Makkeh

Primary record:

- [Royal Society DOI](https://doi.org/10.1098/rspa.2021.0110)
- [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC8261229/)
- [arXiv v2](https://arxiv.org/pdf/2008.09535v2)
- audited arXiv PDF SHA-256:
  `dc65320690c85aa9617a0af469692200f991f24784aac5d7399fa2c6854533d3`
- audited [Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8261229/fullTextXML)
  SHA-256:
  `c3c6f6882e37105856843c3abdd74a11e77c25abe3b9fd20e02673865f0fe652`

Relevant locations:

- Definition 1 and Eq. (2.8): parthood distributions and their order.
- Eqs. (2.9)–(2.10): redundancy coordinates and Möbius system.
- Eq. (3.3): averaged variable-level atoms.
- Eq. (3.7): logical union-of-conjunctions definition.
- Eq. (3.8): pointwise Möbius inversion followed by averaging.
- Theorem 1 and Corollary 1: isomorphic logical, antichain, and parthood lattices.

## Counterexamples attempted

1. The published XOR example confirms that net local shared information can be negative.
2. The published RndErr example gives a negative averaged net unique atom despite nonnegative
   informative and misinformative components.
3. A rare-cell construction shows that pointwise boundary continuity is false.
4. The corrected $T=S_1$ construction shows that no global linear modulus can hold for averaged
   component or net atoms.

The exact constructions and one rejected variant are retained in
[../failures/provenance-boundaries.md](../failures/provenance-boundaries.md).

## Exceptional cases

- A local logarithm is defined only for a positive-mass key.
- A zero-mass key must be omitted or totalized by a separate proved convention.
- Paper component nonnegativity does not apply to net atoms.
- Lattice monotonicity is not monotonicity as the probability law changes.
- The source theorem uses the full paper-defined lattice.
- The papers use bits; pid-rs uses nats.
- The source papers do not cover a changing alphabet, adaptive quantizer, continuous estimator,
  sample concentration, or binary64 error.

## Missing lemmas and bridges

1. Exact identification of project events with the published event predicate.
2. Exact identification of project node order and Möbius matrix with the full finite lattice.
3. A boundary-totalization lemma for averaged terms.
4. A common-overlap perturbation bound for every antichain event.
5. A proof that component pointwise inversion and averaging commute with direct averaged
   inversion.
6. Formal instantiation of published component nonnegativity, rather than importing it as a
   premise.
7. An end-to-end theorem from the categorical functional to Rust arithmetic.

## Likely failure mode

The main likely failure is a silent scope change: proving an abstract entropy or matrix inequality
and reporting it as an SxPID theorem without proving the event, lattice, boundary, and averaging
identifications.

## Novelty status

The route did not find a prior primary result with the exact closed-simplex, support-change,
finite-alphabet total-variation scope. This is not proof of priority. The claim must remain
project-defined and novelty-safe.
