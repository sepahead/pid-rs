# Source correspondence and thirteen proposed statements

This table accompanies [the exposition](EXPOSITION.md). All thirteen candidate declarations
compiled. Complete semantic, axiom, and fresh-kernel acceptance is pending. The correspondence
to prose in published papers is a human source review; Lean does not interpret those papers.

## Primary sources and exact locators

| Key | Exact source and revision | Relevant locator | Use in this packet |
|---|---|---|---|
| WB | Williams and Beer, *Nonnegative Decomposition of Multivariate Information*, [arXiv:1004.2515v1](https://arxiv.org/pdf/1004.2515v1) | PDF page 3, Eqs. (4)–(5) | Nonempty antichains of nonempty collections; redundancy order. Eq. (3) defines the distinct numerical quantity \(I_{\min}\). |
| GWM | Gutknecht, Wibral, and Makkeh, *Bits and Pieces: Understanding Information Decomposition from Part-whole Relationships and Formal Logic*, [arXiv:2008.09535v2](https://arxiv.org/pdf/2008.09535v2); [journal DOI](https://doi.org/10.1098/rspa.2021.0110) | PDF page 18, Eq. (4.1), Theorem 1; Appendix 8(b), PDF pages 28–29, Eqs. (8.2)–(8.6) | OR-of-ANDs semantics; reverse implication; the characteristic-pattern argument. Eq. (8.5) identifies minimal true sets. |
| MGW | Makkeh, Gutknecht, and Wibral, *Introducing a differentiable measure of pointwise shared information*, [arXiv:2002.03356v5](https://arxiv.org/pdf/2002.03356v5); [journal DOI](https://doi.org/10.1103/PhysRevE.103.032149) | PDF page 3, Eqs. (5)–(8); Appendix A.1, PDF page 13, unnumbered order display; PDF page 5, Eq. (13) | Categorical joint-collection AND, across-collection OR, pointwise probability ratio, and separate cumulative atom relation. |

Page numbers above are one-based physical PDF pages. Equation locators refer to the named
arXiv revisions; they must not be silently transferred to another revision or the journal
layout. Retrieved PDFs and byte hashes are retained in `sources/RETRIEVAL.json` for this local
review. They are reference evidence, not proposed redistributable publication assets.

GWM's paper carrier follows the PID exclusions of the two constant functions. The generic
contract in this packet permits the empty family and empty collection. Its explicit constant
cases therefore extend the domain of the displayed logical equivalence; they do not enlarge
the paper-defined PID carrier. No novel mathematical theorem is claimed for this classical
extension or for antichain uniqueness.

## Formal definitions and representation

The proposed candidate's namespace is `PidSxDnfOrderCandidate`. It imports exactly `Contract`.
The frozen contract imports `PidFiniteConvergence.SxEventBridge` and defines `DNF`,
`RedundancyLE`, `IsInclusionAntichain`, `EqualityPattern`, and `RealizesAllPatterns` in namespace
`PidSxDnfOrderContract`.

The target of each public theorem is the corresponding receiver-free `<name>_target` alias.
No obligation-structure receiver or assumed instance of the desired theorem is part of these
targets. The table below describes those aliases, not the earlier checklist structures.

| Exposition object | Exact repository representation | Correspondence boundary |
|---|---|---|
| Source index \(I\) | `sourceIndex : Type u` | Generic targets require decidable equality; categorical targets also require `Fintype`. |
| Family \(\alpha\) of finite collections | `Finset (Finset sourceIndex)` | Finite sets have no duplicate entries. Generic families may contain the empty collection or be empty. |
| \(F_\alpha(e)\) | `DNF alpha pattern` | `Bool.true` denotes 1. This is a proposition about a pattern, not a probability. |
| \(\alpha\preceq\beta\) | `RedundancyLE alpha beta` | The quantifiers are over `b ∈ beta` and then `a ∈ alpha`, with `a ⊆ b`. |
| Antichain | `IsInclusionAntichain alpha` | Inclusion of two members forces equality. |
| Complete key \(x\) | `PidFiniteConvergence.CategoricalKey sourceIndex sourceValue targetValue` | Dependent source tuple paired with one target value; source alphabets can differ. |
| Equality pattern \(e_z(x)\) | `EqualityPattern anchor candidate` | Compares source coordinates only. |
| Collection event \(B_a(z)\) | `PidFiniteConvergence.sourceBranchEvent a anchor` | Finite set obtained by filtering all complete keys using `sourceCollectionEquivalent`. |
| Family event \(E_\alpha(z)\) | `PidFiniteConvergence.sxSourceEvent alpha anchor` | Finite union of collection events, not an empirical count map. |
| Target event \(T_z\) | `PidFiniteConvergence.targetBranchEvent anchor` | Compares the target coordinate to the same anchor's target. |
| \(E_\alpha(z)\cap T_z\) | `PidFiniteConvergence.sxTargetRestrictedEvent alpha anchor` | Existing theorem `sx_target_restricted_event_eq_inter` supplies this equality. |
| Domain \(D\) | `Set (CategoricalKey ...)` | Arbitrary subset of the finite ambient key type; a support interpretation must be supplied separately. |
| Full-pattern realization at \(z\) | `RealizesAllPatterns anchor domain` | Every Boolean source pattern has a representative key in the specified domain. |

The existing source is `audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean`.
Its event definitions are noncomputable finite-set specifications using classical decision
instances. Reuse of this specification is not a proof of correspondence to Rust or a claim
about runtime enumeration costs.

## The exact thirteen-target map

Every name below has prefix `PidSxDnfOrderCandidate.`. “Generic” means finite families of finite
collections on an index type with decidable equality. “Categorical” adds finite source index,
finite source alphabets, finite target alphabet, and the stated decidable equalities.

| No. / exposition label | Exact public theorem name | Assumptions and conclusion | Provenance and proof idea |
|---|---|---|---|
| 1 / G1 | `order_iff_dnf` | Generic. \(\alpha\preceq\beta\) iff every pattern accepted by \(\beta\) is accepted by \(\alpha\). No antichain or nonemptiness premise. | WB order; GWM Theorem 1 and Eq. (8.6). A collection's characteristic pattern proves the converse. |
| 2 / G2 | `antichain_antisymm` | Generic. Both families are antichains; mutual order implies equality. | Classical antichain representation. Successive witnesses give \(c\subseteq b\subseteq a\); the antichain premise makes them equal. |
| 3 / G3 | `dnf_injective_on_antichains` | Generic. Both families are antichains; equality of DNF truth on all patterns implies equality of families. | GWM representation, including minimal true sets in Eq. (8.5). Apply G1 in both directions, then G2. |
| 4 / C1 | `source_event_iff_dnf` | Categorical. Membership in `sxSourceEvent` iff DNF accepts the key's equality pattern. | MGW Eq. (6) mapped to the existing finite-event specification. Unfold finite union, collection matching, and Boolean equality. |
| 5 / C2 | `order_implies_source_event_subset` | Categorical. Order implies reverse source-event inclusion at the same anchor. No realizability premise. | Compose G1 and C1. This direction remains true after any domain restriction. |
| 6 / C3 | `order_iff_implication_on_realizing_domain` | Categorical. Under `RealizesAllPatterns anchor domain`, order iff reverse membership implication for every key in that domain. | Explicit sufficient realization premise for the source-to-event converse. Lift an arbitrary pattern to a representative key. |
| 7 / C4 | `alternate_values_realize_all_patterns` | Categorical. Given one alternate unequal to each anchor source value, the full ambient domain realizes all patterns. | Direct construction: select anchor or alternate by the desired Boolean flag; retain the anchor target. No assertion about restricted support. |
| 8 / C5 | `source_event_injective_on_realizing_domain` | Categorical. Two antichains, full pattern realization, and equal event membership on the domain imply equal families. | C1 and G3 with representative keys. Both the antichain and realization premises are explicit. |
| 9 / C6 | `order_implies_target_restricted_subset` | Categorical. Order implies reverse inclusion of target-restricted events at the same anchor. | C2 and the existing `sx_target_restricted_event_eq_inter`. Intersect both sides with the same target event. |
| 10 / B1 | `singleton_event_collision` | Fixed three-source, one-value alphabets. Two distinct singleton families are antichains, incomparable in order, and have equal source events. | Explicit negative control against unconditional categorical event injectivity. All complete keys match every source. |
| 11 / B2 | `singleton_not_all_patterns` | The same one-value setting does not realize all patterns, even on the full ambient domain. | Explicit negative control against automatic realizability. The all-false pattern has no key. |
| 12 / B3 | `binary_diagonal_collision` | Fixed three Boolean sources, one-value target, anchor 000. The two singleton events agree on the diagonal domain, differ on the full domain, and the diagonal does not realize all patterns. | Explicit negative control against inferring support realization from binary alphabets. Raw row 011 distinguishes the ambient events. |
| 13 / B4 | `antichain_premise_is_load_bearing` | The absorbed family is not an antichain, differs from the singleton family, precedes it in both directions, and has the same DNF on every pattern. | Classical absorption identity \(e_1\lor(e_1\land e_2)=e_1\). Refutes antisymmetry and semantic injectivity on unrestricted families. |

The four boundary exports are compound propositions. In particular, B1 includes both
non-order directions as well as event equality; B3 includes all three restricted/ambient/
realizability claims; and B4 includes failure of the antichain condition, inequality, both
orders, and semantic equivalence. The exposition retains all of these clauses.

## Evidence classes and open correspondences

| Edge or assertion | Status for this packet |
|---|---|
| Named source revisions to displayed definitions and orientation | Human source correspondence review, with exact locators. |
| Displayed definitions to existing event specification | Explicit mathematical and type-level map above; compiled candidate C1 connects the two formal representations. Complete candidate acceptance pending. |
| Candidate declarations to frozen thirteen receiver-free targets | Development compilation passed. Full exact target-type and axiom reporting gate pending. |
| Fresh source closure checked by the separate kernel route | Pending; the failed frozen judge did not reach it. |
| Rust, Python, certificate producer, or floating-point correspondence | No new evidence from these thirteen statements. |
| Probability ratios, averages, Möbius inversion, atom signs | Outside the thirteen targets. Equation (10) in the exposition is source-defined orientation material. |
| Statistical consistency, uncertainty calibration, support inference | Outside scope. |
| Practical sensor or robotics performance | Outside scope; only an explicitly synthetic category analogy is supplied. |
| Support-quotient atom compression | Separate proposed task, still unproved here. Generic order/adjunction and Möbius results have established predecessors. |

The exact development candidate SHA-256 is
`76298a9baaad74f831b5254ccdeb5eeda019ac67769df9fabf2a317694fc4a65`.
The contract SHA-256 is
`569bf11314d02ff599309bfcfa0d80109bf0f121032d5d665e8519513219a5c0`.
These identities locate reviewed bytes. They are not evidence of mathematical novelty,
independent custody, or completed formal acceptance.

The adopted candidate policy permits only the transitive axiom subset
`propext`, `Classical.choice`, and `Quot.sound`. The actual axiom set must be reported for each
export by the complete judge. Compilation alone is not that report. No new axiom, `sorry`,
`admit`, native-evaluation oracle, or added proof premise is permitted by the candidate policy.
