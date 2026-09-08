# Categorical prefix expectations and the MGW mean

Three exact Lean targets connect a statistic of independent complete categorical rows to the joint-law mean of an MGW shared-exclusions atom. The result gives an exact finite-horizon expectation formula and convergence of those expectations. It supplies no finite-horizon unbiasedness, error rate or confidence coverage.

Read the [mathematical exposition](EXPOSITION.md), [statement and source correspondence](SOURCE_CORRESPONDENCE.md), and [dependency graph](DEPENDENCIES.md). The complete accepted graph is under [sources](sources/PrefixMgwMeanCandidateRoot.lean). Its selected candidate is [Candidate.lean](sources/PidPrefixMgwMean/Candidate.lean), with SHA-256 `17fc2d8fce5ad0ba28cc8348e9348911c393e6eb00515c8139fbd27b85331b6a`.

The original local proof campaign was accepted on 8 September 2026. The [evidence record](../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/RESULTS.md) retains the four positive runs, actual wrong-final-target rejection, development failures and earlier expired attempt.

**Public packaging status: source proposal, not replayed.** The proposed [adapter](replay-proposed.py), [manifest](replay-proposed-v1.json), [replay design](REPLAY_DESIGN.md) and [control plan](CONTROL_PLAN.md) are concrete review inputs. Their new route needs its own checks and registration before public replay can be reported. The existing public DNF package and the pending generic, MGW and probability packages keep their separate statuses.

The theorem's law is a fixed finite PMF on complete source-and-target rows. Coordinates within a row may depend on one another; different experiment rows are iid. Information units are nats. This is the categorical MGW functional, distinct from continuous Ehrlich shared exclusions, other PIDs, a Rust/Python implementation, and an application-performance claim.
