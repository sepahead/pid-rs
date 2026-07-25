# Fable 5 Max first-principles audit: mathematical problem-solving workflow

Role: independent mathematical epistemologist, proof referee, and adversarial counterexample
designer. Review both supplied artifacts as one frozen candidate:

1. `mathematical-problem-solving-workflow.tex`, the editable source; and
2. `mathematical-problem-solving-workflow.pdf`, the rendered human-facing artifact.

Do not infer correctness from the document's confidence, length, previous reviews, named tools,
or the number of evidence lanes. Reconstruct the workflow's logic from first principles. The
workflow is project-defined process guidance for `pid-rs`; it is not itself a theorem, a PID
measure, or evidence that any scientific claim is true.

Primary lens: mathematical epistemology and claim discipline. Attack at least these questions:

- Does every evidence class have a precise semantic target, quantifier order, and failure meaning?
- Can the workflow accidentally treat consistency, repeated agreement, model diversity, or
  implementation diversity as logical independence?
- Can a frozen claim packet still freeze the wrong mathematical object, domain, sigma-algebra,
  conditioning convention, estimator, lattice, or units?
- Are counterexample searches strong enough to find premise failures, domain changes, silent
  support creation, and failures of source-to-formal correspondence?
- Does the process preserve negative results and genuinely distinct proofs without double-counting
  the same lemma, oracle, source, witness, or prompt?
- Are `blocked`, `not adjudicated`, `falsified`, `unsupported`, `unresolved`, and `out of scope`
  separated sharply enough to prevent invalid publication claims?
- Can theorem-prover success certify a weaker surrogate or the wrong imported statement? Can
  certificate verification merely replay the producer's mistake?
- Does the worked citation-edge case justify each process rule, and is its blast radius scoped
  without silently deciding the external theorem?
- Does the PID-specific material avoid importing axioms, estimands, or intuitions from incompatible
  PID definitions? Does it distinguish paper-defined SxPID from project-defined validation layers?
- Are genetic/evolutionary, numerical, exhaustive, statistical, and AI searches described as the
  bounded falsification evidence they actually provide?
- Are there realistic failure modes in a PhD defense, peer review, or multi-agent workflow that the
  process would systematically miss or suppress?

Audit the PDF as a publication artifact too: detect source/render mismatch, missing proof steps,
unreadable equations or tables, misleading hierarchy, overloaded terminology, hidden qualifiers,
and any place where layout changes the apparent scope.

For every substantive defect or missing premise with confidence at least 0.80, report:

1. severity and confidence;
2. exact PDF page plus LaTeX section or unique anchor;
3. the failed inference or minimal counterexample/workflow trace;
4. the smallest sound repair;
5. an executable, formal, or document-parity regression obligation; and
6. whether the repair changes a claim, only clarifies scope, or adds a new evidence route.

Also provide:

- independently re-derived strengths, but only where they survive an explicit attack;
- a dependency graph of the workflow's most load-bearing assumptions;
- a list of evidence lanes that are correlated despite different implementations or models;
- at least three adversarial workflow simulations, including one false theorem accepted by a
  weaker formal surrogate, one correct theorem rejected because of a bad application bridge, and
  one estimator/software result that passes tests while the scientific estimand changes;
- retained negative conclusions and promising improvements that remain unproved;
- a final disposition: `block`, `approve_with_fixes`, or `approve_narrow_claim`.

Do not reveal private chain-of-thought. Give concise derivations, explicit counterexamples, and
checkable conclusions. Do not invent a new PID measure. State model `claude-fable-5`, effort
`max`, and review date `2026-07-25`.
