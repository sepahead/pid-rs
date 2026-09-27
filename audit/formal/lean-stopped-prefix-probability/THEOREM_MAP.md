# Finite first-hit laws and exact MGW prefix cancellation: theorem map

Author: Sepehr Mahmoudian · 27 September 2026.

This package records [local acceptance](LOCAL_FORMAL_ACCEPTANCE.json) at 21:28:05 UTC on 26 September 2026 for exactly three theorem exports. F1/F2 were newly accepted; F4 was freshly rechecked under the repaired joint closure. The 41 records also include controls and causal comparisons; they are not 41 theorems. No new portable or hosted theorem replay is inferred from publication.

The [contract](sources/PidStoppedPrefixStageA/Contract.lean), [raw targets](sources/PidStoppedPrefixStageA/RawTargets.lean) and [aliases](sources/PidStoppedPrefixStageA/AliasTargets.lean) retain all three universes $u,v,w$, finite coordinate and target alphabets, decidable equality and a finite nonempty source-index type. F1/F2 additionally require `Law p`: nonnegative real masses with total one. Zero-mass keys are allowed. F4 has no law or independence premise.

| Result and exact export | Premises and conclusion | Proof route and source |
|---|---|---|
| F1: `PidStoppedPrefixF1F2Candidate.first_hit_factorization` | For a finite law $p$, arbitrary event $A$ and nonnegative integer $n$, split the actual IID $(n+1)$-row law restricted to $n$ misses followed by one hit. The pushforward equals the product of the $n$-fold unnormalized miss measure and the unnormalized hit measure. | The [F1/F2 candidate](sources/PidStoppedPrefixF1F2/Candidate.lean), lines 20–151, gives singleton and total masses, event bounds, mask products, the split preimage and restriction. `proof_first_hit_factorization`, line 153, equates both singleton masses and applies finite-measure extensionality. Export at line 206. |
| F2: `PidStoppedPrefixF1F2Candidate.first_hit_mass` | For the same law and event, $a=\sum_{x\in A}p(x)$ lies in $[0,1]$ and first-hit mass is `ENNReal.ofReal ((1-a)^n*a)`. This includes $n=0$, $a=0$ and $a=1$. | `f12_event_mass_bounds`, line 76, uses nonnegativity and normalization. `proof_first_hit_mass`, line 180, evaluates F1 on the whole space and multiplies factor totals. Export at line 210. |
| F4: `PidStoppedPrefixF4Candidate.native_return_kills` | For any supplied complete anchor $z$, valid node $\alpha$ and finite comparison list containing $z$, both actual native prefix terms equal zero. No PMF, support, IID, positivity or differentiability premise is used. | The [F4 candidate](sources/PidStoppedPrefixF4/Candidate.lean), line 11, uses empty self mismatch to falsify the raw prefix predicate. Complete-key equality retains $z$ under target filtering, so the same contradiction kills the negative branch; the proof splits the last-row cases. |

The [inherited native definitions](../lean-prefix-mgw-gradient/sources/PidPrefixProbability/Contract.lean) specify finite weighted Dirac/product measures, the prefix fold and both terms. The negative denominator is retained-target rank. Within-row source/target dependence is unrestricted; IID concerns complete comparison draws only. F4 is deterministic. Probability masses and reciprocal prefix weights are dimensionless; the surrounding information construction uses natural logarithms and nats.

## Exact execution and trust boundary

The [source map](SOURCE_MAP.json) selects 25 modules: seven exact public dependencies and 18 package files. The exact semantic judges compare full raw/alias/candidate types and export rosters. All three actual exports reported universes `u`, `v` and `w` and precisely `Classical.choice`, `Quot.sound` and `propext` as axioms. The [raw records](evidence/RECORDS.json) preserve 19 F1/F2 controls, two F1/F2 exports, 12 F4 controls, one F4 export, six exact Boolean causal comparisons and one forbidden-axiom rejection.

`PidStoppedPrefixCausal.AxiomControls` was compiled to observe rejection but is excluded from `StoppedPrefixProbabilityRoot` and its fresh-kernel closure. The retained `leanchecker --fresh StoppedPrefixProbabilityRoot` call returned zero. The [command evidence](evidence/COMMANDS.json) binds 29 completed commands and 58 selected streams to the original acceptance. Expected rosters remain expected inputs.

The [verbatim expanded raw propositions](THEOREM_STATEMENTS.md) are separate from the [actual printed export types](evidence/EXPORTED_TYPES.json). F1/F2 printed target abbreviations; those strings were not replaced by expansions. Source comments saying “uncompiled” or “source proposal” retain their preexecution wording. The later acceptance projection supplies the result without modifying accepted proof bytes.

The legacy comparison modules preserve the previous decision-term mismatch; they are not adopted F1/F2 targets. [Historical F4](evidence/historical-f4-v4/DISPOSITION.md) used older shared StageA target bytes, so its acceptance did not substitute for the fresh joint verification. [History](HISTORY.md) retains the failed F1/F2 semantic check and the separate stale-inventory refusal.

## What is not in the three-export result

F4 is sufficient cancellation, not an earliest-stopping equivalence. No F3/cycle law, infinite stopping theorem, stopped-gradient unbiasedness, exchange of infinite sums and expectations, variance bound, expected-runtime theorem, seeded sampler refinement, Rust implementation or useful training result follows. The proposed $O(n|I|)$ equality cost in the [exposition](EXPOSITION.md#6-rust-implementation-and-computational-cost) is a source-derived engineering count, not a Lean export or benchmark. In the accumulated-prefix times stopped-path-score construction, zero terminal increment does not remove the terminal score's effect.

F1/F2 are classical finite probability identities. F4 is an invariant of the project prefix construction in the context of Makkeh, Gutknecht and Wibral, *Introducing a differentiable measure of pointwise shared information*, [arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5), [doi:10.1103/PhysRevE.103.032149](https://doi.org/10.1103/PhysRevE.103.032149). No scientific-priority claim is made. [REPLAY.md](REPLAY.md) states the open portability, hosted execution and custody edges.
