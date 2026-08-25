# Fable 5 Max first-principles completion triage

Role: independent information-theory mathematician, statistical-methods referee, exact-numerics
designer, and hostile theorem auditor.

This is a read-only advisory review. Do not edit any file. Do not trust the prior GPT-5.6 Pro
handoff, existing pid-rs claims, existing model reviews, or this prompt's suggested work packages.
Reconstruct and attack the problem from first principles. Do not expose private chain-of-thought;
give concise, checkable arguments, exact equations/counterexamples, and explicit uncertainty.

## Frozen review context

- Review date: 2026-07-25 (Europe/Berlin).
- Model and effort to state in the response: `claude-fable-5`, `max`.
- Current pid-rs commit: `ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7`.
- Handoff Markdown SHA-256:
  `7df374bedee2e3792f8f2f51634801bf9df18ac6f305e57a9edf60c291748d36`.
- The handoff's audited commit is
  `d4bb0e741ea71ecddfdd414920e3874825fefc2d`; it is locally available and is the direct parent of
  the current prompt-only commit.
- Model output is advisory only and cannot close a pid-rs obligation.
- Observed current-main replay failure: `cargo test --locked -p pid-core --test
  sxpid_relation_witness` aborts in `crates/pid-core/build.rs` because the current
  `method-catalog.json` SHA-256 begins `eb428177` while the embedded forensic digest begins
  `7746f84`; `python3 scripts/check-method-catalog.py` nevertheless passes. Treat the exact root
  cause and required proof/build-identity repair as an open finding, not as a prompt assertion.

Read in full before deciding:

1. `AGENTS.md`;
2. `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`;
3. `/Users/torusprime/Downloads/first_pid_rs_audit_gpt5-6pro/pid-rs-first-principles-audit-handoff.md`;
4. every CSV in that handoff directory;
5. `README.md`, `METHODS.md`, `KNOWN_LIMITATIONS.md`, `RELEASE_AUDIT.md`;
6. current `crates/pid-core/src/sxpid.rs`, `discrete_pid.rs`, `ksg.rs`, and `stats.rs` plus their
   relevant integration tests;
7. `audit/formal/**`, the two current claim dossiers under `claims/`, and
   `audit/tools/certified-sxpid/**` where relevant; and
8. `audit/evidence/completion-run-ledger-2026-07-25.md` only as process/context, never as evidence.

## Decision problem

Determine which handoff recommendations are mathematically correct, already closed at the exact
current revision, invalid or overstated, and worth implementing now. In particular, independently
adjudicate:

- F-004/W2.1: separate plus/minus binary64 cancellation versus a direct-net, exact-product, and/or
  interval-certified categorical SxPID path;
- F-005/W2.2: exact empirical `I_min` branch/tie comparison and a canonical permutation-equivariant
  tie policy;
- F-006/W2.3: exact harmonic-rational KSG count arithmetic versus the current approximate digamma
  path, without pretending this validates geometry or population consistency;
- F-007/W2.4: whether a dependency/innovation-set coloring compiler has a sufficiently precise
  theorem and API contract to implement now;
- F-003/W2.6: whether any continuous PID3 expansion is scientifically defensible, or whether an
  enforced research-only/abstention boundary is the only complete result;
- W1.2/W1.4/W4.2: the smallest genuinely load-bearing categorical SxPID semantic/refinement theorem
  that can be completely closed now rather than creating a decorative partial formalization; and
- whether extending the offline certified tool is superior to changing stable `pid-core` scalar
  semantics.

Use at least these independent lenses: definition/estimand identity, exact algebra, boundary and
counterexample analysis, numerical certification, sampling/statistical meaning, formal statement
scope, executable refinement, and downstream blast radius. Identify shared critical cut sets.

## Required output

1. A recommendation matrix for every F/W item above with `accept`, `reject`, `already_closed`, or
   `defer_with_exact_blocker`; give the exact proposition and evidence needed.
2. The strongest three complete implementation waves, ordered by assurance gain per complexity.
   Each wave must have a frozen claim, non-solutions, minimal falsifiers, at least two
   method-independent routes, exact files likely affected, and mechanical exit criteria.
3. At least five ways the handoff could be wrong or misleading even if its bounded examples are
   correct.
4. At least five attacks on your own preferred wave, including one definition mismatch, one
   exact-zero/near-zero issue, one resource-bound issue, one formal-to-code mismatch, and one
   statistical overclaim.
5. A final disposition: `implement_now`, `implement_narrower_claim`, or `do_not_implement`, with the
   single most important reason.

Do not invent a new PID measure. Do not conflate SxPID with `I_min`, KSG, quantized SxPID, or
continuous PID. Do not label a bounded exhaustive result universal. Do not recommend epsilon
clamping. Do not treat model consensus as evidence.
