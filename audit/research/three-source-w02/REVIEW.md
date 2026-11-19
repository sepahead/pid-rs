# Scope and review of the eighteen-family count test

**Sepehr Mahmoudian · 19 November 2026**

The question is whether the two assertions in a particular archived input can both hold. A *valuation* assigns typed values to its declared constants. A *model* here means a valuation that makes both assertions true. The input encodes a finite classification with sixteen additional arbitrary mathematical integers in its declarations. The study has no observations, probability law, information units, statistical target or production API. [Mathematical statement, hand count and proof](README.md)

## Objects, evidence and correspondence

| Object or transfer | Evidence and remaining assumptions |
| --- | --- |
| Published node concept | Williams and Beer define the redundancy lattice using nonempty antichains of nonempty source subsets. Gutknecht, Wibral and Makkeh give a related formal-logic account. Here only the three-source combinatorial domain is used. Neither paper defines this solver input. [Williams and Beer, 2010](https://arxiv.org/abs/1004.2515v1) · [Gutknecht, Wibral and Makkeh, 2021](https://doi.org/10.1098/rspa.2021.0110) |
| Repository source | The original file at commit `5b60576d81cbf2862f8f44d3ff18036e23488bda` is Git blob `4c7e620a94f614e2fff3a0bedd939b58a21b8d46`. Its SHA-256 is `e503d85f5b6fe842c0900043283147f23055a4c5f4cf19e2914080cfbab692a0`. The solver responses comprise two observations of one formula. [Original package](../../formal/finite-smt39-qualification-v1/README.md) |
| Bytes to formal object | Two separately written programs consume all lexical spans and compare every typed command. A third reader parses the literal Lean constructors back into the typed tree. These finite comparisons include unused definitions and the two assertions in their original order. A verified general parser and an equivalence theorem with the full SMT-LIB language remain open. [Constructor writer](source_writer.py) · [Second reader](source_reader.py) · [Literal reader](lean_literals.py) · [SMT-LIB 2.6](https://smt-lib.org/papers/smt-lib-reference-v2.6-r2024-09-20.pdf) |
| Formal object to theorem | Four proofs and four separate uses have complete stored types, proof expressions, names, owning modules and transitive axioms. The formal rules distinguish evaluation failure from a Boolean result. A constructive inhabitant supplies a valuation. The proof quantifies over all valuations, including unbounded integers. [Model](lean/W02Semantics.lean) · [Theorems](lean/W02Candidate.lean) · [Typed uses](lean/W02Consumer.lean) · [Declaration records](declarations.jsonl) |
| Kernel and execution | The original host used stock Lean 4.34.1. The original compilation, fresh replay and later portable reproduction retain separate measurements. Both paths depend on the stock kernel, compiled imports and operating environment. [Recorded observations](observations.json) · [Reproduction](replay.py) |
| Interpretation | Counting all valid codes and checking pairwise distinctness of the listed codes does not test their membership. A distinct invalid replacement exhibits the gap. Neither a probability nor a PID coordinate appears in the claim. Scientific refinement, runtime and application conclusions would require different objects and evidence. [Exact second assertion](../../formal/finite-smt39-qualification-v1/raw/W02-exactly-18-distinct/generator.stdout.smt2) |

## Alternatives considered before the scientific attempt

| Route | Premise and decision | Failure condition or evidence for reconsideration |
| --- | --- | --- |
| Keep the historical status | Selected for the account of the two original solvers. | Recovering a historical proof requires contemporaneous proof bytes and their custody. |
| Count the families by hand | Selected to explain the finite set using inclusion alone. | The hand count cannot establish the semantics of the source bytes. A separate source comparison is required. |
| Rerun two solvers | Gives new status reports under their respective implementations. | Status agreement leaves the derivation unchecked. A statement-bound proof format would change that conclusion. |
| Enumerate all assigned constants directly | Exhaustive enumeration works on a finite domain. | The sixteen integers are unrestricted. A proved elimination of unused values would license an appropriate finite projection. |
| Reuse a lattice-cardinality theorem | Can prove eighteen for its own carrier. | It omits the exact listed codes and the second assertion. A typed correspondence theorem would connect the two objects. |
| Check a propositional refutation | An LRAT proof could certify a Boolean translation. | The route needs a checked connection from the unchanged bit-vector and integer input to that formula. |
| Check an Alethe proof | Could bind a proof to a raw SMT problem using a separately implemented checker. | The preparation retained unsupported or incompletely checked steps. A fully checked terminal contradiction with no such step would qualify for a new attempt. |
| Check a CPC proof | A reference reader and terminal contradiction check could connect the calculus to the source problem. | Frozen synthetic qualification did not establish the required coverage. A supported proof and fixed compatible rule set would reopen it. |
| Discard unused commands | Could reduce kernel evaluation cost. | The deletion needs a preserved-denotation argument for the actual assertions. The chosen route retains every command. |
| Represent the full typed input in Lean | Selected. Source comparisons, positive evaluation results, nonempty valuations and a stock-checked no-model theorem answer the stated question. | A byte discrepancy, ill-typed reading, wrong assertion results, undeclared axiom, failed fresh replay or wrong declaration record rejects this route. |
| Verify a general byte parser | Could extend source correspondence across the specified fragment. | Requires a language definition, full parser proof and matching lexical and operational rules. It remains a separately registerable program. |
| Use a PID or a statistical score | Requires a target, joint law or task loss. The statements supply none. | A separately posed application with a declared estimand and baseline would permit a different comparison. |

## Review, selection and remaining disagreements

The formal-source reviewer wrote a first opinion from the original 39 inputs and the documented proof formats. The finite-mathematics and statistical reviewers separately examined how to replay previously checked, named finite statements on another host. Their written first opinions required exact theorem sources, input identities and separate host and scientific claims. Those reviews concerned other named finite statements. Those critiques informed the dependency checks and supplied no theorem about W02. The subsequent custodian compared the exact bytes and checked the candidate with the frozen judge. These were model-assisted roles, with a common input and infrastructure. No independent human or institutional disposition is recorded. [Historical review and scope](../../formal/finite-smt39-qualification-v1/REVIEW.md)

The historical status was visible. The single later attempt used the frozen predicate and one candidate proposal. There was no best-of-several selection and no empirical holdout. The candidate supplied four proof bodies. The source, interpretation, declaration types, separate typed uses and checking environment were fixed before that proposal. An earlier declaration-observer build failed during preparation. A corrected observer and a deliberately false synthetic proposal were checked before the original attempt. The native run and its resource limits appear in the observation record. The different readings do not establish independent semantics or independent data. [Command outcomes, commitments and preparation outcomes](observations.json)

The following lenses name questions used in reviewing the source and its interpretation. Each group records the conclusion it affected. They count questions, not reviewers or independent confirmations.

| Questions considered | Disposition |
| --- | --- |
| Source identity, immutable revision, raw byte coverage, final newline, comment coverage, token order, unused declarations, echo identity | The two readers agree on all 89 commands. The echo is a label. |
| Source labelling, nonempty branches, empty family, branch comparability, one-member families, incomparable pairs, three-member families, maximum family size | Seven singletons, nine pairs and two triples give the hand count. |
| Family bit order, admissible family codes, printed code count, literal distinctness, list membership, conjunction polarity, assertion order, source versus target role | Distinct literals and the cardinality result have separate meanings. No target distribution was supplied. |
| Rank scope, parameter binding, forward references, unused constant dependence, unbounded integers, bit-vector widths, unsigned arithmetic, conditional branches | Structural and synthetic checks cover the finite source fragment. |
| Semantic failure, false Boolean result, conjunction satisfaction, empty-domain vacuity, existential countermodel, all-valuations quantifier, execution budget, source-to-AST correspondence | Require successful evaluation and inhabited assignments; compare the complete source tree. |
| Import trust, fresh module replay, admitted foundational axioms, omitted unsafe declarations, omitted partial declarations, theorem-owner binding, full proof expressions, typed use dependence | Preserve complete declared terms and both trust routes. |
| Historical status provenance, repeated solver observations, observer attrition, candidate exposure, proposer write scope, shared implementation, human independence, artifact custody | Attribute the single later checked artifact to the new run. Historical denominators remain separate. |
| MI or conditional MI, fixed-model ablation, retrained ablation, direct task loss, failure utility, coverage, Bayesian design, Fisher design | These alternatives require data, probability or utility; none is defined in this finite logic question. |

## Publication inspection

The four-page study PDF is 56,125 bytes with SHA-256 `ccf0413b501b2402d624eccfdbcb21204c8fb01d74e15fa46c05b11ed88c5b67`. Separate native builds using ordinary and optimized Python reproduced the shipped bytes. Each page was rendered at 105 dpi and in grayscale. Details of the count equation on page 1, the mixed-pair exclusion on page 2, the four propositions on page 3 and the replay commands on page 4 were examined at 200 dpi. [Study PDF](../../../output/pdf/three-source-w02.pdf)

| Publication lenses | Observation |
| --- | --- |
| Hierarchy, typography, grid, spacing and rhythm | A lapis title, distinct byline, single-column prose, readable indices and a separate command block fit within the margins. The display on page 1 shows both conjuncts on the same line. |
| Narrative order, motif provenance, motif coherence, ornamental restraint | The pages proceed from the asserted formula to the count, its source and the kernel. The repository's running headers and low-contrast geometric marks remain outside the argument. |
| Palette identity, pattern and data separation, color-redundant labels, grayscale | The shared style distinguishes titles from text and link accents. Counts, quantifiers, commands and statuses are written as searchable glyphs. The grayscale renders preserve their distinctions. |
| Real-text extraction and logical reading order, print fidelity, A4 profile and fonts, link and action safety | Poppler extracted the body and commands in order, found four A4 pages with eight embedded, subsetted, Unicode-mapped font entries, and reported HTTPS destinations matching the Markdown. The pages were inspected on screen. Physical print and assistive-technology use have no separate observations. |
| Deterministic reproduction, source and derived files, portable dependencies, normal-size and high-resolution review | Two fresh native reproductions matched the committed PDF. The Markdown, local TeX and Lua files are source; the PDF is derived. The publication depends on the stated local design and external typesetting tools. High-resolution crops and full pages were inspected separately. |

Cite Sepehr Mahmoudian (2026), *The eighteen families in the original three-source count test*, with the exact repository commit or release. [Software citation](../../../CITATION.cff)
