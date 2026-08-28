# Decision record 2 for SX-CERTIFIED-AVERAGED-PID3-001, unchanged claim revision 1

## Revision relationship

This record adjudicates evidence produced after the revision-1 specification was frozen. It does
not change [claim-v1.md](claim-v1.md), [conventions.md](conventions.md), the coordinate registry,
an acceptance rule, a schema, a resource policy, or the mathematical target. The historical
[decision.md](decision.md), [evidence-matrix.md](evidence-matrix.md), and
[bindings.md](bindings.md) remain preserved. No `claim-v2.md` is created because the frozen claim
has not changed.

The historical [revision-index.md](revision-index.md) is also left unchanged. The
[`sxpid3-packet-revision-index` artifact record](../../audit/evidence/primegaps-to-pid-transfer-ledger-v1.json)
in the source-bound PrimeGaps-to-PID transfer ledger pins its exact bytes as part of the original
packet intake. This later decision is inventoried in the machine-checked method catalog; leaving
the historical index untouched preserves provenance and does not give the complete target any
additional credit. The current two-dimensional pointer is
[evidence-adjudication-index.md](evidence-adjudication-index.md).

## Decision

**Disposition: proposed/open.**

**Complete target-implication evidence label: no accepted end-to-end evidence.**

Decision record 2 accepts two scoped results:

1. Under the assumptions below, the averaged informative cumulatives for one supplied source-only
   event family factor through the complete joint source marginal. Equality of that marginal
   preserves the informative vector and any one literally fixed finite linear transform of it.
2. On exactly three ordered binary sources, one binary target, and every labelled 16-cell
   nonnegative integer count vector with total $1\le N\le5$, two separately implemented Python
   routes recomputed 108 keyed scalar audit expressions per table. They emitted the same
   neutral-v2 stream digest and the same complete six-block exact sign/zero census.

Neither result closes the prospective certificate implication. All five closure programs and
every load-bearing end-to-end cut remain open.

## Exact factorization result and assumptions

Let $P$ be a probability law on a finite source alphabet

$$
\mathcal S=\mathcal S_1\times\mathcal S_2\times\mathcal S_3
$$

and a finite target alphabet. Write $P_S(s)=\sum_t P(s,t)$ for the complete joint source marginal.
Fix one supplied source-only event family
$E_\alpha(s)\subseteq\mathcal S$. Require $s\in E_\alpha(s)$ for every supported source state, so
the event mass inside the logarithm is positive. Use natural logarithms and sum only over supported
source states. Then the averaged informative cumulative is

$$
I^+_\alpha(P)
=\sum_{s:P_S(s)>0}P_S(s)
  \left[-\log\!\left(\sum_{s'\in E_\alpha(s)}P_S(s')\right)\right].
$$

Thus $I^+_\alpha(P)$ depends only on the complete joint source marginal $P_S$. If two laws have
the same complete joint source marginal, the same source alphabet, the same supplied event family,
and the same logarithm base, their informative cumulative vectors agree. Their finite target
alphabets and their allocations of probability across target states can differ. Applying one
literally fixed finite matrix to both vectors preserves this equality.

“Complete joint source marginal” means the law of the tuple $(S_1,S_2,S_3)$. It does not mean the
three separate one-source marginals. Retained exact counterexamples show that separate marginals
do not determine the informative vector and that the factorization does not extend in general to
the misinformative or signed-net components. Calling the supplied fixed matrix the intended
Möbius inverse still requires an independent proof of the concrete carrier, order, orientation,
and inverse.

This is an exact finite-law statement for a supplied event transcription. Publication-to-local
correspondence remains an external premise. The generic Lean lane corroborates the supplied-event
and fixed-transform algebra; it does not formalize the complete concrete SxPID3 semantics.

## What the 108 objects are

| Object | Count | Meaning |
|---|---:|---|
| SxPID3 antichain/lattice positions | 18 | Three-source redundancy-lattice positions |
| Usual SxPID3 signed-net atoms | 18 | One signed-net atom per position |
| Cumulative component expressions | $18\times3=54$ | Informative, misinformative, and signed net |
| Atom component expressions | $18\times3=54$ | Informative, misinformative, and signed net |
| Audit registry | $18\times2\times3=108$ | Position times stage times component |
| SxPID4 lattice positions | 166 | Separate four-source carrier, outside this audit |

The 108 objects are keyed scalar audit expressions. They are not 108 PID atoms, lattice nodes, or
independent degrees of freedom. The signed-net block is informative minus misinformative, and each
atom block is a fixed transform of its cumulative block. The number 166 belongs to the separate
four-source lattice.

## Bounded audit result

The bounded corpus contains 20,348 labelled count vectors. Of these, 20,164 represent primitive
rational laws and 184 are integer rescalings retained as executable regression cases. Because
$N\le5$, the corpus contains no full-support 16-cell table. Each route computed

$$
20{,}348\times108=2{,}197{,}584
$$

strictly positive exact rational products.

Within each sign/zero census block, every labelled-table/antichain-key pair has unit weight. Each
table therefore contributes 18 classifications to a block, for 366,264 classifications per block.
This is not prevalence or probability weighting over empirical laws or datasets.

The immutable receipt field `findings.domain.census_weighting` calls this
`one_vote_per_labelled_count_vector_not_prevalence_or_probability`. That value is historical
shorthand for giving every labelled table equal weight in the exhaustive loop. It does not mean
that a table contributes only one scalar census observation. The six census arrays classify all 18
antichain keys for each table, exactly as the totals above show. This decision narrows the reading
of the field without rewriting the source-bound receipt.

The primary route uses recursive weak compositions, Python `Fraction`, direct event scans, and
exact Gaussian elimination of the declared zeta matrix. The second route uses stars-and-bars
unranking, prime-exponent vectors over 2, 3, and 5, cylinder marginals with inclusion--exclusion,
and recursive subtraction on the
declared poset. The prime-exponent representation is exact here because all positive masses are at
most five. A larger total-count bound would require a different factor domain or a general integer
factorization route.

The routes are **implementation-disjoint under shared semantics**, not logically independent.
They share the human publication transcription, the declared key registry, a Python runtime class,
the host, the neutral framing specification, and other premises recorded in the receipt.

## Retention and comparison boundary

The receipt does not retain a per-record product archive and does not record a direct
record-by-record comparison of two retained streams. Each route recomputed every table-expression
pair and fed its freshly computed result into the same neutral-v2 framing protocol. The retained
agreement evidence is:

- the matching neutral-v2 SHA-256 digest
  `20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8`; and
- the matching complete six-block exact sign/zero census.

Thus the audit **computed** all exact products. The receipt retained a digest commitment, aggregate
census, and exact source bindings; the repository retained the bound source bytes. Neither retained
the individual product records. Reinspection of an individual record requires replay. SHA-256
agreement is bounded fault-detection evidence under the recorded host and framing assumptions. It
is not a mathematical proof, an authenticity proof, or a substitute for a retained streaming
comparator.

Source inspection and hostile tests found no per-table answer table, endpoint-specific
forced-value branch, or cross-route import of numerical output. Those controls reduce named risks;
they do not prove the absence of all shortcuts, shared mistranscriptions, framing faults, or
coordinated resealing.

## Effect on the five closure programs

| Program | Decision-record-2 credit | Remaining decisive cut |
|---|---|---|
| A: source and combinatorial semantics | Partial | Independent paper correspondence, arbitrary accepted-row event/count bridge, and complete carrier/order derivation |
| B: dual formal semantics | Partial at the generic algebra layer | Concrete `Fin 3` semantics in Lean and a mask-generated solver-neutral route under two solvers |
| C: certified numerics | Bounded exact sign/zero partial result | Canonical parser, general product preflight, directed nonzero magnitude, and untrusted-report verifier |
| D: compiled Rust refinement | Lexical routing observation only | Compiled keyed numerical comparison; the lexical lane computed zero Rust values |
| E: replay, provenance, and adjudication | Source-bound local receipt and partial mutation evidence | Complete manifest, per-record or streaming comparison, fresh independent acquisition, external custody, and final adjudication |

The complete obligation-by-obligation status is in
[evidence-matrix-v2.md](evidence-matrix-v2.md). D1 remains an upstream requirement even though no
Program A--E “Current obligations” row in the frozen route file names it. For future planning, D1
belongs with Program A's canonical semantic input boundary and Program C's untrusted parser
boundary. This coordination note does not weaken or change the frozen obligation.

## Permitted wording

> For a declared local categorical SxPID3 transcription, two
> implementation-disjoint-under-shared-semantics Python routes recomputed all 108 keyed scalar
> audit expressions on every labelled count table for three ordered binary sources and one binary
> target with total one through five. Under a source-bound local receipt, their neutral-v2 stream
> digests and six exact sign/zero census blocks matched. Separately, a finite-law theorem shows that
> the averaged informative cumulatives for a supplied anchored source-only event family factor
> through the complete joint source marginal, and that one literally fixed linear transform
> preserves this invariance. The prospective 108-expression certificate claim remains
> proposed/open.

## Prohibited inferences

This decision does not establish:

- 108 PID atoms, lattice nodes, or independent degrees of freedom;
- the 166-position SxPID4 lattice;
- arbitrary alphabets, totals, or full-support tables;
- a pointwise audit;
- a per-record product archive or direct record-by-record comparison;
- logical independence or an independent proof;
- publication-to-code correspondence;
- concrete `Fin 3` formal verification or dual-proof-system closure;
- exact nonzero logarithm magnitude or directed interval containment;
- canonical parser correctness or unique bytes-to-count semantics;
- compiled Rust, binary64, public-API, or release-binary refinement;
- a general resource, performance, memory, or denial-of-service theorem;
- general informative/misinformative atom nonnegativity from the finite census;
- a population, sampling, calibration, confidence, permutation-null, causal, or application
  theorem;
- a transfer to BROJA, Williams--Beer $I_{\min}$, KSG, continuous shared exclusions, quantized
  shared exclusions, or another PID definition; or
- scientific priority, authenticity, authorship, attestation, external custody, independent human
  review, or release authority.

## Historical-byte preservation

The revision-1 packet files introduced at commit
`5b4f3758d688dfd06d6072374922b00abad27ecf`, tree
`9eda16049d0cea7bca4ce558fe24389dcd65d3f7`, remain byte-identical when this decision is written.

| Historical file | SHA-256 |
|---|---|
| `claim-v1.md` | `3c0ce09a17d1925a01f54d35733c6f01effbdd6ae3d081d194a7fadf6e04b31b` |
| `conventions.md` | `2d14bea9d6f0a2d07493ddaf7d89a130f4ad62680319cb9efba465590c2250c7` |
| `obligations.md` | `054bfc40bc18bdbc86918b1b47f169aa69b7e6343d5faa85e4940933583269fe` |
| `routes.md` | `609b737d494da09cc1e47410c1c318661a46fd417549e98d21033eeaedbf967b` |
| `bindings.md` | `bffd5f422b109335070011fd315034d4d4aa7bed54032a4c9426d43dd2a6507b` |
| `evidence-matrix.md` | `ee3db98b1eca36616f0eb28f97a7c478a6d49b56bbd97c769d14b292f0fc4c4a` |
| `decision.md` | `122c17693ada4dea23e1757f99d9aec9b0970317435b16de944668ebb751211b` |
| `revision-index.md` | `cf33f912f12793739b3e7a4a4b41b974709ead47df59fcfca37f8de443d4719e` |

No assurance percentage is assigned to the complete target. Partial obligation credit cannot be
averaged into `verified`.
