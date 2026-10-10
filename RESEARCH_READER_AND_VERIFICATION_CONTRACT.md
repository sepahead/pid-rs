# Research reader and verification contract

Sepehr Mahmoudian · 10 October 2026.

Project-defined process guidance, not a PID result or proof. This contract
extends the existing mathematical workflow without replacing its claim packets,
negative records or historical publications. Any portable document format (PDF)
version follows the same evidence boundaries.

The [v2 PDF in output](output/pdf/research-reader-contract-v2-draft/STATUS.md) is
an **UNQUALIFIED FAILED-BUILD DRAFT**, not a projection of this revised text.
Its failure remains recorded. Qualified publication of the current text is open.

## Question and strategy

The research question is: which statements about a named shared-exclusions
functional can be derived correctly, computed reliably, and used for a justified
decision? These are separate questions. Name the defining publication before
using its PID (partial information decomposition). Categorical
Makkeh–Gutknecht–Wibral shared exclusions and continuous Ehrlich shared exclusions
remain distinct. See the existing [source-pinned vocabulary](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md#primary-source-pins-for-pid-vocabulary-and-routing).

Every study opens with five short answers:

1. What exact question is being answered, and why does its answer matter?
2. Which law, functional, inputs, outputs and assumptions define the question?
3. Which strategy was actually used, whether artificial intelligence (AI) assisted
   or not? State AI's actual role or its absence, and explain the choice against
   the nearest alternatives: direct algebra, finite enumeration, ordinary tests,
   a solver, a simpler non-PID analysis or no action.
4. Which valuable result survives checking, which evidence supports it, and what
   application decision follows—or does not follow?
5. What failed, what remains open, and what evidence would justify reconsideration?

Record the actual strategy, not an ideal strategy retrospectively assigned to
the run. AI may generate candidates, reconstruct arguments, find counterexamples,
inspect sources or review exposition. For decisive claims, an independent-first
route freezes its initial derivation before seeing another route's candidate.
After exposure, it is an adversarial review, not an unexposed reconstruction.
Keep shared source, model, parser, runtime and custody dependencies visible.
State separately what is useful now and what is only a conjectural future use.
Name the future test needed; do not count it as present application evidence.

## Selection and review accounting

For candidate selection, use the existing attempt ledger. Define `N` as the
nonnegative integer number of candidate attempts in the declared pool, including
failed or withdrawn attempts. For best-of-N, state what makes the selected
candidate best. Record planned and actual N, generation method, evaluated and
eligible counts, selection criterion, stopping and adaptations. Retain failures
and valid unselected candidates, plus test or judge-feedback reuse. Report
per-candidate and total resource limits and use, comparator allocations, matched
measures and remaining differences; distinguish allocation matching from
actual-use matching. For review, record actual reviewers, named lenses,
exposure timing, shared dependencies, disagreements and evidence-based
dispositions. Unknown fields stay unknown. Candidate or lens counts supply no
correctness or independence credit.

For a partial proof used to support a claim or select a search route, list its
exact unresolved propositions, premises and dependencies. State whether a
helper merely restates the target. A compiling draft with placeholders or
unverified citations remains open. Compare a direct library-lemma route before
adding search machinery. Candidate, episode, generator and problem counts are
different units. See the [current process evidence report](RESEARCH_PROCESS_EVIDENCE_2026_10_10.md)
for the source comparison and actual checked examples.

Use the existing claim packet and route memo to map an external method's
premises to the named pid-rs need, identify adaptations and broken premises,
compare the simplest applicable alternative, and specify a falsifiable acceptance
test. Preserve rejected transfers. A source's benchmark, reviewer score or
different-domain success gives no PID correctness, calibration, novelty or
application credit.

## Cited glossary

Use this compact process glossary alongside each study's own complete notation.
Its definitions follow the linked existing repository contracts; no new method
is introduced.

| Term | Meaning and defining reference |
|---|---|
| Estimand | The exact quantity a procedure aims to estimate; [method boundaries](AGENTS.md#method-provenance-and-novelty-claims) |
| Functional | A map from a declared probability law to a quantity; [reading conventions](MATHEMATICAL_RESULTS_GUIDE.md#1-reading-conventions-and-semantic-firewall) |
| Empirical law | Relative frequencies of complete observed categories; not automatically the population law; [finite-law contract](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) |
| Independent-first route | An initial reconstruction frozen before exposure to another candidate; not statistical or institutional independence; [route dependencies](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md) |
| Shared cut | A dependency whose failure can defeat several nominally different routes; [evidence architecture](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md#layered-assurance-architecture) |
| Semantic correspondence | The justified link between intended meaning and a formula, formal statement or executable; [formal boundaries](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md#formal-methods-as-bounded-instruments) |
| Calibration | Agreement between stated statistical guarantees and performance under the declared repeated-sampling model; [sampling boundaries](KNOWN_LIMITATIONS.md) |
| Nonclaim | A conclusion the evidence must not be used to support; [evidence card](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md#evidence-card-template) |
| Negative control | A deliberate alteration with a predeclared disconfirming or refusal outcome; expected satisfiability can be successful control execution without accepting the altered claim; [attack matrix](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md#attack-matrix-and-required-negative-controls) |
| Counterexample | An admissible example that satisfies a claim's premises but violates its conclusion; not merely an invalid input; [falsification workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md) |
| Proof kernel | The component that checks encoded proofs under the permitted axioms; not an estimator's neighbourhood rule; [tool boundaries](FORMAL_TOOL_ADOPTION_AUDIT.md) |
| Custody | Recorded preservation and recovery of identified evidence; not its truth or authorship; [durability rules](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md#repository-durability-and-promotion) |

## Explain a formula before asking the reader to use it

Before each central formula, define its symbols locally. Give each variable's
meaning, domain, index set and units. Identify source and target roles, the law
used by each expectation, support and sampling conditions, and every required
positive denominator. Define abbreviations at first use. A glossary and a
bibliography do not replace local definitions.

For example, let $n$ be a positive integer counting complete observed rows. Let $z$
be one joint source-and-target category in a declared finite alphabet, and let
$c_z$ be its nonnegative integer row count. The empirical probability of that
category is $\widehat p_n(z)=c_z/n$. Its unit is dimensionless, and the counts
must sum to $n$. If $n=4$ and $c_z=1$, the probability is $1/4$.
This arithmetic evaluates an empirical law; it does not show how well that law
estimates a population law. A new equation needs its own local meanings when a
symbol's role changes.

Show the intermediate steps that carry the conclusion: substitutions,
normalizations, signs, index changes, inequalities, cancellations and error
aggregation. Use a small exact example that a reader can recompute. Separate
an observed physical input from a synthetic mathematical example. An angle
in radians does not establish a particular angular density model.

## Evidence and trust

For each important conclusion, record the narrow supported statement and its
strongest nonclaim. Keep these evidence classes separate:

| Evidence | What it supports | What it does not supply |
|---|---|---|
| Published definition | The named source's mathematical object | Correct local transcription or implementation |
| Analytic derivation | The displayed implication under its stated premises | Proof-kernel acceptance, runtime behavior or calibration |
| Formal replay | The recorded encoded statement under its imports and axioms | Intended scientific meaning or unrecorded descendants |
| Exact finite check | The stated finite predicate on the checked domain | A universal analytic or sampling theorem |
| Executable comparison | The bound implementations agree on the workload | Correctness outside the workload |
| Statistical evaluation | The recorded study under its design and uncertainty assumptions | Deployment, causal value or an untested population |
| Actual PDF review | The viewed pages at the recorded sizes | Mathematical truth or unviewed page approval |
| Human verification | Only the named person's recorded checks | Review that was never performed |

Do not label a model's manual algebra as human verification. When no human
verification receipt exists, state that it is absent. Trust follows the
load-bearing evidence and its shared dependencies, not confidence, votes,
reviewer counts, polished language or a green build. The [current stock-Lean
promotion hold](SESSION_HANDOFF.md#formal-integrity-checkpoint-of-2-october-2026)
remains applicable; a new process document cannot remove it. Historical
receipts are not thereby erased or disproved.

## Failure and originality records

Preserve positive and negative results with exact assumptions, decisive examples,
evidence, rejection reasons and conditions for reconsideration. Correct an active
claim without erasing its false predecessor. Link a dated erratum or successor
from the current result map. Keep immutable receipts immutable.

Before claiming an advance, search for equivalent statements, reparameterizations,
special cases and compositions of known results. Record the search date, sources,
queries or theorem locators, nearest prior result and the exact additional claim.
“No equivalent found within this search” is not proof of global novelty.

A small searched publication corpus does not establish what a model encountered
during training. Training exposure is unknown unless independently evidenced.
A locally withheld example is not necessarily unseen in pretraining. Model
agreement cannot answer whether an intermediate result was recalled or derived.
Reconstruction, counterexamples and correspondence checks address correctness;
dated equivalent-theorem searches address the narrower originality question.

## Extension precedence for retained wording

This extension supersedes only the following two retained sentences in
[the mathematical workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md). All other
claim packets, mathematical meanings, evidence requirements and historical
receipts retain their existing authority. No new formal, numerical or
application credit follows.

- Under “Codex goal, plan, and tool lifecycle,” the retained sentence is:
  “A paused, hard, slow, or partially complete goal stays active.”
  Correct its paused-goal case: an explicit user request to pause requires
  `update_goal(status="paused")` when that tool is available, reporting its
  returned state and stopping goal work. Use this transition only at the
  user's explicit request. Difficulty, slowness or partial progress alone is
  not a pause request. A resumed blocked goal starts a fresh blocked audit.
  Use plan or goal tools only when actually available; never invent a
  successful call.
- Under “Optional explicit mapping-check rule,” the retained sentence is:
  “Every categorical claim must answer five questions in its claim packet:”
  Here “categorical claim” means a **category-theoretic claim**. It does not
  mean a claim about finite category-valued data. The five questions and their
  existing mathematical obligations are unchanged.

The older publication remains a dated preserved artifact. Updating its complete
Markdown/TeX/PDF projection and visual receipt is a separate publication task;
this contract does not claim that task is done.

## Validation and implementation

A structural checker can verify row counts, declared line/page coverage,
links, byte hashes and declared source/PDF projection bindings. These checks
establish record consistency; they cannot prove that a reported reading
actually happened, that every symbol is meaningful, that the projection
preserves meaning or that every premise is scientifically true. Semantic review,
mathematical checks, qualified formal replay, statistical evaluation and actual
page inspection retain separate receipts. Test missing premises, undefined
domains, stale bindings, erased negatives and unjustified review labels, with
harmless valid changes as positive controls. A finite mutation suite remains
finite.

This process contract changes no Rust API, PID estimator, proof kernel, toolchain,
tolerance or scientific acceptance predicate. No timing or application benefit
is reported. New scientific studies still require the existing “Rust
implementation and computational cost” section.

Suggested citation: Sepehr Mahmoudian, *Research reader and verification contract*
(2026). Include the exact repository commit or release when citing an accepted
publication. For the software, use [CITATION.cff](CITATION.cff).
