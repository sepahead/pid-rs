# Opus 5 Max assurance audit: mathematical problem-solving workflow

Role: independent formal-methods architect, scientific-software verifier, statistics reviewer,
human-factors auditor, and publication editor. Review both supplied frozen artifacts:

1. `mathematical-problem-solving-workflow.tex`; and
2. `mathematical-problem-solving-workflow.pdf`.

This is a read-only adversarial review. Do not edit files and do not trust prior model reviews. The
workflow is project-defined process guidance, not a proof that `pid-rs`, SxPID, or a downstream
application is correct.

Use a lens deliberately different from a pure theorem referee. Inspect the end-to-end assurance
architecture:

- requirements and claim freezing;
- source custody, citation-edge typing, source-to-local correspondence, and ambiguity handling;
- prose-to-formal refinement and proof-assistant scope;
- executable refinement, compiler/library/native-code trust, and reproducible builds;
- exact, interval, floating-point, mutation, model-checking, property, exhaustive, randomized,
  evolutionary, and statistical evidence;
- calibration, holdout, dependence, adaptive selection, distribution shift, and abstention;
- independence accounting across people, models, prompts, proof routes, checkers, and shared
  artifacts;
- governance, role separation, stopping rules, change control, failure retention, and review
  incentives;
- PID-specific definition compatibility, estimator/estimand identity, and downstream authority
  boundaries; and
- PDF/LaTeX parity, navigability, table usability, citation durability, and defense-readiness.

Question every operational assumption. In particular, seek circular checkers, shared-oracle
failures, source drift hidden behind stable URLs, false reproducibility from regenerated PDFs,
proof-kernel success on the wrong statement, mutation suites that only test anticipated errors,
holdout leakage, researcher degrees of freedom, dependence violations, and process steps whose
cost makes them likely to be skipped in practice.

For every finding with confidence at least 0.80, give severity, PDF page, LaTeX anchor, concrete
failure trace, smallest sound repair, and a fail-closed regression gate. Separate:

- correctness defects;
- ambiguity or missing-premise defects;
- impractical requirements that undermine compliance;
- source/rendering defects;
- useful but non-independent evidence;
- work that is formally valid but scientifically insufficient; and
- proposals that are promising but not yet proved or calibrated.

Produce these additional outputs:

1. a threat model for the workflow itself;
2. a minimal auditable claim-packet schema and transition-state machine;
3. a coverage matrix mapping claim classes to necessary and insufficient evidence;
4. five red-team scenarios spanning pure mathematics, floating point, statistical estimation,
   source custody, and downstream decision use;
5. a prioritized improvement plan limited to changes justified by this supplied snapshot; and
6. a final disposition: `block`, `approve_with_fixes`, or `approve_narrow_claim`.

Do not expose private chain-of-thought. Use concise checkable reasoning, explicit counterexamples,
and exact scope labels. Do not invent a new PID measure or conflate other PID definitions with the
Makkeh--Gutknecht--Wibral shared-exclusions functional. State model `claude-opus-5`, effort `max`,
and review date `2026-07-25`.
