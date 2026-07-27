# Hostile review — statistical-methods lens

**Scope note.** I audit what each artifact *binds statistically*: estimand, support, identifiability, finite-sample behavior, dependence, UQ, multiplicity, and transfer between objects. Lean/Z3 kernel internals belong to the formal-methods reviewer; I attack the *semantic bridges* of every formal artifact regardless.

**Top-line verdicts.**

- Your strongest unexploited asset is the exact bound `-D <= T <= D`. Read correctly, it is a **theorem-grade impossibility result**: the KSG estimate can never exceed `D = H_(n-1) - H_(k-1) ≈ ln((n-1)/(k-1))`, so for any joint with `I > D` the error is at least `I - D` **deterministically**. Formalize this saturation corollary; it is the only distribution-free statistical statement you can currently prove.
- There is **no distribution-free finite-sample error bound for MI estimation** — provably (checkerboard construction below). Any request for "smallest useful bounds" without a declared distribution class is ill-posed. I supply the two honest bounds that exist.
- The most dangerous latent overclaim is drift: corpus-max `8*EPSILON` → input-space float claim; categorical SxPID → continuous Ehrlich object; three primes → "three proofs." Your text disclaims all three; your *schema* must make the disclaimers machine-enforced.
- The premise `k-1 <= nx` is a free continuity alarm: it fails exactly when the declared-continuous support assumption fails (ties/duplicates). Make it a fail-closed runtime assertion, not a silent clamp.
- Recovery discipline: match **content hashes of exact objects, never summary statistics**. Any "reconstruct until 354/7844 and the 40-row max reappear" behavior is Clever-Hans contamination.

**Ill-posed / overclaim flags (requested):** (a) universal float bounds from a frozen corpus; (b) any independence framing of the three primes (they share the entire upstream pipeline; they detect residue-arithmetic and transcription faults only); (c) estimation claims for continuous Ehrlich PID3 before an existence/invariance/quantization-limit theorem for that estimand; (d) "mutation-resistant invariants" — surviving search is not truth; (e) crediting transcript-matched reconstruction as the same scientific object before settled-byte rerun (your policy forbids this; enforce it structurally).

---

## 1. First-principles reconstruction audit

Ways to silently rebuild the wrong object, each with a fail-closed check:

1. **Fuzzy-patch replay.** `git apply` with hunk offsets lands a patch in a neighboring function with identical local names; it compiles and passes weak tests. *Check:* apply with zero fuzz against a pinned base **tree hash**; post-apply, require full-tree hash equality with the recorded snapshot ref — never per-touched-file hashes (the "untouched files unchanged" assumption is exactly what fuzz violates).
2. **Wrong-base ambient diff.** Replaying diffs onto an ambient checkout that drifted since the transcript. *Check:* every recorded patch carries `(base_tree, result_tree)`; refuse if base mismatches.
3. **Generated-view laundering.** Hashing a *rounded* corpus view while the exact-rational object regenerated differently (`2/4` vs `1/2`, sign of zero, row order). *Check:* the primary hash is over a canonical exact-rational serialization (lowest terms, normalized sign, fixed sort key, Merkle root over rows); rounded views are derived and hash-bound to the exact parent.
4. **Sufficient-statistic matching.** Reconstructing until `354/7844`, the `8*EPSILON` max, or the 40 attaining rows reappear. Matching statistics ≠ matching objects; the reconstructor knows the targets. *Check:* ban statistic-targeted iteration; acceptance criterion is byte hash of the exact object or the object is declared *new* and every downstream gate status resets to open.
5. **Seed-vs-stream drift.** Transcripts record seeds; replay uses a different RNG stream/version and produces different rows that pass shape checks. *Check:* the **drawn values are the object**; seeds are provenance. Seed-replay equality is a check, never the definition.
6. **Tie-policy nondeterminism.** A rational corpus can contain *exact* distance ties; serial vs parallel kd-tree tie-breaking then changes counts while endpoint totals coincidentally match. *Check:* corpus records the tie policy; assert zero ties or a deterministic total order; recount ties on reconstruction.
7. **Snapshot refs omitting gitignored inputs.** Large frozen corpora are exactly what `.gitignore` hides; a snapshot ref then reconstructs code without data. *Check:* gate runner consumes only manifest-listed inputs by hash and refuses to run on any absence. Bundles verified by `git bundle verify` from a **fresh clone on a clean machine**; the clean-room rebuild must reproduce all gate outputs.
8. **Ambient contamination.** Adjacent worktree sharing `.git` with the preserved ambient checkout can depend on reflog-only objects. *Check:* CI builds from pushed commits + bundles only.
9. **Threshold leakage from pre-loss runs.** Thresholds must derive from spec; corpus-descriptive numbers (40 rows, `9.761311*EPSILON`) are labeled descriptive and regenerated, never asserted as targets.

---

## 2. Formal-method portfolio (ranked; only where a distinct obligation closes)

Distinguish **independent routes** (different semantic bridge) from **correlated re-encodings** (same statement, different engine). Lean+Z3 already share the statement-transcription cut; three primes share everything upstream of residue arithmetic.

1. **Proof-producing SMT + independent checker** (cvc5 → Alethe/LFSC, checked by carcara). *Obligation closed:* "Z3 as oracle." *Trust base:* small checker + SMT-LIB semantics. *Bridge:* same encodings — this is deliberately a solver-diversity move only; to diversify statements, auto-print the SMT from the Lean statements via an independent printer and diff. *Mutation:* the 12 countermodel mutants must yield models verifiable by a trivial evaluator. *Reject if* proofs exceed checker capacity — then shrink obligations, don't trust unchecked output. **Must.**
2. **Gappa/Flocq (Rocq)** for the binary64 helper. *Obligation:* upgrade "corpus max `8*EPSILON`" to a **universal, range-conditioned** rounding theorem (`for all in-domain n,k,x,y ≤ N0: |T_float - T| ≤ c*EPSILON`). This is the only route to a non-corpus float claim. *Trust base:* Rocq kernel + IEEE-754 model + the expression bridge to compiled code. *Rejection rule:* if you cannot pin the compiled expression (FMA contraction, reassociation, libm calls), the theorem binds the wrong object — compile with contraction off, audit IR, or abandon the universal claim. *Mutation:* enable FMA / permute association → obligation constants must change or fail. **High-value.**
3. **Kani/CBMC bounded equivalence** of brute vs kd-tree counting on integer/rational grids (e.g., `n ≤ 6`, coords in a small grid), plus overflow/NaN-absence. *Boundedness explicit and honest.* *Mutation:* seeded off-by-one and W1/W2-swap mutants must be caught. *Reject* float kd-tree model checking if bounds collapse below `n=4`. **High-value.**
4. **MPFR/Arb ball arithmetic** as the *reference*, replacing Decimal for measurement rows: certified enclosures per row, radius below gate granularity. *Obligation:* remove the unproved "Decimal digits suffice / no double-rounding flip" assumption in the rounded-reference route. *Boundedness:* per-input only; never universal. **High-value now; must for any future continuous-Ehrlich runtime claims (log/digamma of reals).** Note: Arb closes *nothing* for `T` itself — `T` is rational and γ cancels; do not spend there.
5. **SAT + DRAT (drat-trim / cake_lpr)** for PID lattice combinatorics: antichain enumeration completeness ("no 19th atom"), bijection certificates for the 108-coordinate manifest. *Trust base:* verified proof checker. **High-value for §5.**
6. **TLA+/Alloy** for the phase/custody/NO-GO machine and the recovery protocol. *Check:* no reachable state with `released ∧ open_gate`; deleting the "rerun settled-byte after reconstruction" guard must produce a violating trace. Process obligation, not math. **High-value.**
7. **Verus/Creusot** functional proofs of production count/harmonic kernels against the Lean spec. Closes the spec-to-binary gap more strongly than tests+Kani, at high cost. **Optional.**
8. **Exact rational LP/SOS certificates** for simplex inequalities arising in PID identities; certificates re-checked by a trivial rational evaluator. **Optional.**
9. **Schema formalism** (JSON Schema/CUE + property tests) for §7. Not a proof method; classify separately. **Must.**
10. **Rejected:** CRT reconstruction claims; adding more primes (correlated); more Decimal digits (correlated with the route being replaced); generic fuzzing marketed as verification.

On existing artifacts: 14 mutants for 19 Lean theorems is a thin kill matrix. Require ≥1 killing mutant per theorem **and per hypothesis** (drop each hypothesis; if the proof survives, the advertised premise list is wrong — record the minimal premise set). Publish surviving mutants. Mutation kill-rates are bounded evidence about your mutant distribution, not semantic coverage.

---

## 3. Evolutionary/genetic/CEGIS route

Search is a **lower-bound machine**: it can only exhibit counterexamples/extremizers. Search failure proves nothing beyond "budget B over proposal distribution Q found nothing" — record exactly that, never a safety claim.

Useful spaces, each with minimization and certification:

- **Float-error extremizers.** Genome: `(n, k, x, y)` in-domain plus **association tree** for the summation (Catalan space; you already witness association order). Fitness: exact `|T_float − T|` via rationals. Minimize by delta-debugging to smallest `n`. Certify: exact rational witness row; optionally a Gappa check that the claimed error is attained. Purpose: probe the corpus/domain gap under the `32*EPSILON` gate.
- **Corpus-hole search.** Same space restricted to rows *not* in the frozen corpus. Expected outcome: values above `8*EPSILON` exist. Forcing function: you must **pre-register the gate's scope** (corpus-max vs domain-max) and the breach protocol *before* running. Finding `> 32*EPSILON` in-domain is a gate breach, not a footnote.
- **Estimator-failure families (statistical).** Checkerboard/permutation copulas (below) parameterized by `m` and block masses; fitness `|KSG(n,k) − I|` with the estimand **exact by construction**. This converts the identifiability impossibility into an executable artifact family.
- **Tie/degeneracy configurations.** Maximize count divergence between tie policies and between serial/parallel builds; feeds §1 and §4 domain assertions.
- **PID pmf search.** Small alphabets, rational pmfs. Objectives: most-negative pointwise sx atoms (numerical stress); worst float conditioning of the Möbius solve; maximum divergence between two independent implementations; `|Σ atoms − MI|` in float as a bug detector. Minimize alphabet by symbol deletion + renormalization preserving the property; certify in exact rationals (log-sign decisions by interval escalation).
- **Invariant CEGIS.** Templates over `(n,k,x,y,T)` with harmonic terms; verify candidates against the Z3 order axioms; counterexample-refine; survivors become **Lean proof obligations**, never shipped facts. Co-evolve the mutant zoo against the test suite and report the kill matrix.

Every found artifact enters a **new** frozen corpus with adversarial provenance; silently merging into the old corpus changes the measured object (corpus id must change).

---

## 4. KSG closure attacks

- **The theorem itself.** `T = H_(k-1)+H_(n-1)-H_(x-1)-H_(y-1)` with endpoints at `(x,y)=(k,k)` giving `+D` and `(n,n)` giving `−D` is sharp and fine. Two required additions: (i) the *average* of locals inherits `[-D, D]` (trivial, but state it — the estimator-level bound is the useful one); (ii) the **saturation corollary** (§6, Thm S1). Without (ii) the theorem is statistically undersold.
- **Domain premise attack.** `k-1 <= nx` holds only for tie-free data. Duplicated points give `ε=0`; discrete/quantized marginals give ties; then `nx < k-1` is reachable and the typed domain is violated. Production must **fail closed** on domain violation (this doubles as the continuity alarm). Add witnesses: duplicate-point rejection, exact-tie rejection, NaN rejection.
- **Inclusive index-map attainability (sharp catch).** Stated range `k <= x,y <= n`, passed directly. Under self-*inclusive* counting, the joint inclusive count is `k+1` (self + k neighbors at `≤ ε`), so `x ≥ k+1` and the lower endpoint `k` is unattainable; under self-*exclusive* counting, `x ≤ n-1` and the upper endpoint `n` is unattainable. The declared `[k, n]` cannot have **both** endpoints attainable under one convention. Obligation: state the convention; exhibit endpoint-attaining witness rows for whichever endpoints you claim; tighten the range otherwise. Audit whether any of the 354 endpoint rows mix routes/conventions. A mutation swapping `x=nx+1` vs `x=nx` must be killed by rows that pin **raw counts → mapped arguments** per route, not just final `T`.
- **Modular certificate asymmetry.** Nonzero residue with invertible denominator ⇒ nonzero rational: sound, unconditional. Zero residue ⇒ endpoint: sound **only with** a numerator-bound lemma `|num(T ∓ D)| < p1·p2·p3` plus denominator-coprimality checks (fail closed if `den ≡ 0 mod p`). The rejected prime's four collisions prove ~10^6-scale factors occur, so single-prime certificates are demonstrably insufficient — good narrative, but without the bound lemma the three-prime artifact is a strong regression separator, not a corpus-level proof. Say which one it is, in the schema. Independence framing stays banned: a wrong-`T`-upstream bug passes all three primes identically.
- **Float measurement language.** Define `EPSILON` (2^-52 vs 2^-53) in the schema. The `8*EPSILON` figure is a difference against a *rounded reference*; the reference's own correctness (Decimal precision, double rounding at comparison granularity) is an unstated obligation — close it via Arb enclosures (§2.4) or a precision-sufficiency lemma. Gated outputs must use a deterministic reduction order (serial or fixed tree); parallel nondeterministic reduction under the association-order witness is a contradiction waiting to be found.
- **W1/W2 refinement and custody.** The witness matrix is a set of existence proofs, one per configuration cell — no probabilistic coverage claim is licensed. Add negative controls: a deliberately broken build must fail *every* cell, proving the harness is sensitive. Transcripts prove what was typed, not what executed; your rerun policy is correct — add a third-party fresh-clone replay receipt as the closing artifact. Kill stale caches (`target/`, incremental fingerprints) via clean-room rebuild hash equality.

---

## 5. PID2 and MGW SxPID3 forward design (two failure-diverse routes per obligation)

Failure-diverse means different semantic bridge and different plausible failure mode, not two engines on one encoding.

- **O1 Lattice/antichain enumeration** (PID2: 4 atoms; PID3: 18). Route A: derive the finite poset from definitions in Lean and decide properties by `decide`/finite enumeration. Route B: independent generator in another language, frozen canonical table, byte-compared; SAT+DRAT certificate that no further antichain exists. Literature counts (4, 18) are sanity, not proof.
- **O2 Möbius inversion.** Route A: exact rational inverse shipped **with** the `M·M⁻¹ = I` product as a certificate anyone can re-multiply. Route B: instantiate a generic Möbius-inversion theorem on this finite poset in Lean. Mutation: perturb one zeta-matrix entry → both routes must fail.
- **O3 Pointwise sx atoms with negativity preserved.** Route A: exact rational exclusion probabilities; sign decisions on `Σ q_i log r_i` by interval arithmetic with precision escalation, exact-tie detection via integer log-lattice identities. Route B: independent implementation cross-checked on exact inputs. Ship a canonical distribution+realization with a provably negative atom, verified by both routes; **clamp-injection mutation** anywhere in the pipeline must break the identity checks on that witness. Same for unclamped negative MI inputs.
- **O4 108-coordinate binding.** One canonical, hashed coordinate manifest `id ↔ (program A–E, atom, component)`. Route A: manifest generated from lattice definitions. Route B: frozen hand-audited table; byte equality required. Binding test: 108 end-to-end runs, each perturbing exactly one coordinate at the source and asserting the delta appears at exactly that coordinate in every program's output; a two-coordinate permutation mutation in any single program must fail all downstream identity checks. Programs read the manifest; private re-derivation is a CI error.
- **O5 Consistency identities** (Σ atoms = MI; self-redundancy = MI; lattice cumulatives). Route A: exact rational property tests over random rational pmfs. Route B: Lean symbolic proof for small alphabets (general if feasible).
- **O6 Continuous Ehrlich firewall.** Until (existence of the continuous estimand on declared support, invariance under declared transformations, quantization-limit theorem with rate class) are closed, **no estimation claim**. Constructive reframing: "fitted quantized compositions" legitimately estimate the PID **of the quantized law at a fixed, declared quantizer** — a well-defined categorical estimand per quantizer. The ill-posed part is only the limit claim; type-tag accordingly. MI has a sup-over-partitions characterization; PID atoms do not — quantized atoms need not converge even when every MI does. Cross-type comparison must be a schema type error, enforced by a CI mutation that attempts one.
- **O7 Estimation layer (categorical).** Route A: plug-in from empirical pmf with the §6 deviation bound. Route B: sample-split/debiased variant. UQ by m-out-of-n subsampling with pre-registered coverage validation; flag nonregular points (§6 E2).

---

## 6. Statistical theorem discipline (core)

**Estimand identifiability.**
- Registry: every number carries an estimand id — `MI(P)`, `MI(P_σ)` (noise-added law), `WB_Imin(P)`, `MGW_sx(P)`, `PID(quantizer Q # P)`, `Ehrlich_cont(P)` (status: *undefined pending O6*) — keyed by definition version, support declaration, base measure.
- Declared-continuous support is an **assumption, not an inference**; all measured data are quantized (ADC/binary64 grid), so it is literally false at fine scale. The honest statement: the estimand is MI of a latent continuous law under a declared measurement model — untestable identifiability assumption; must appear in every paper.
- Ties alarm: exact ties are a calibrated alarm for support violation (model expected float-grid collisions under a density bound; alarm, don't "prove").
- Noise: for independent `ε,δ`, DPI gives `I(X+ε;Y+δ) ≤ I(X;Y)` — direction provable, magnitude not, absent a class-conditional continuity modulus (MI is not continuous under weak convergence; it is lower semicontinuous). No modulus theorem ⇒ noise pipelines stay firewalled as different estimands.

**Impossibility E1 (kills universal bounds).** Let `C_σ` put density `m` on blocks `(i, σ(i))` of the `m×m` grid: marginals uniform, `MI = ln m` exactly. Mix over random `σ`: the n-sample law is within total variation `O(n²/m)` of iid uniform (birthday coupling). Le Cam two-point: for any estimator and any `n`, choosing `m ≫ n²` forces error `≥ (ln m)/2` with probability `→ 1/2` on some continuous(-after-mollification) joint. Hence minimax MI-estimation risk over all continuous joints is **infinite**; every finite-sample claim must carry a class (e.g., dependence ratio `f/(f_X f_Y) ≤ C`, which caps the estimand at `ln C` and is exactly what the construction saturates). Deliver this as an executable generator + a short rigorous lemma.

**The two honest bounds ("smallest useful").**
- **Thm S1 (saturation; formalize in Lean now).** `|Î| ≤ D = H_(n-1) − H_(k-1)` for every dataset in-domain. Corollary: if `I > D`, error `≥ I − D` deterministically; a necessary condition to even reach `I` is `H_(n-1) − H_(k-1) ≥ I`, i.e. roughly `n ≳ 1 + (k−1)·e^I` (for `k=1`, `ln(n−1) + γ ≥ I`). This is the rigorous face of the known exponential-sample-complexity phenomenon for strongly dependent variables, and it must be stated wherever KSG outputs are reported.
- **Thm S3 (categorical PID deviation bound; paper-grade, mechanizable with effort).** On the δ-interior class `Δ_δ = {p : p_i ≥ δ}` over alphabet size `A`: with probability `≥ 1−α`, `|Q(p̂) − Q(p)| ≤ L(δ/2, A) · sqrt(2(A ln 2 + ln(1/α))/n)` for each MGW atom `Q`, via the `L1` concentration `P(‖p̂−p‖₁ ≥ t) ≤ (2^A − 2)e^{−nt²/2}` (Weissman et al.) plus an explicit Lipschitz modulus of the atom on `Δ_{δ/2}` (log-ratios of sums of coordinates; bounded partials; the constant must be *produced*, not asserted). Report where the bound is non-vacuous (expect n in the 10^4–10^5 range for modest `A`, `δ`); the blow-up as `δ→0` is unavoidable and is the identifiability boundary, not a flaw. **No transfer to continuous Ehrlich** — no density lower bound exists there.
- **Thm S2 (exact level).** Under iid rows and `H0: X ⊥ Y`, the permutation p-value `(1 + #{π: T_π ≥ T_obs})/(M+1)` is super-uniform — finite-sample, distribution-free, provable (finite exchangeability; plausibly Lean-able). This licenses independence *testing*; it says nothing about MI magnitude or power.

**Bias/variance.** KSG consistency/efficiency statements are class-conditional (smoothness, bounded ratio, boundary conditions); cite-and-assume or simulate — never assert. Locals `T_i` are dependent (neighborhood overlap): sample-variance-of-locals error bars are invalid without a CLT for these statistics under stated conditions. Popoviciu gives only `Var ≤ D²`.

**Dependence.** iid is a declared design property per dataset. Time series: Theiler exclusion windows, block subsampling; permutation nulls are invalid under serial dependence (circular-shift surrogates test a *different* null — say which). The estimand under stationarity is marginal-pair MI, not the process information rate; do not conflate.

**Resampling class taxonomy (with validity preconditions).** Permutation: exact level, exchangeable iid only. Naive iid bootstrap: **rejected for kNN statistics** — duplicated points create zero distances and corrupt counts; this must be a design-level rejection, not a user discovery. m-out-of-n subsampling: workhorse, needs rate choice + coverage validation. Parametric bootstrap: class-conditional. Smoothed bootstrap: changes the estimand (your own noise rule) — rejected as default.

**Calibration/UQ.** Every interval carries `(class, resampling method, nominal level)`. Pre-registered coverage grid: distributions × n × k × dependence × quantizers; simultaneous binomial bands across cells (Bonferroni), Monte Carlo repetitions sized so MC error < the margin being judged; failures published as first-class negative results.

**Nonregularity E2.** `I_min` and min-type atoms are nondifferentiable at ties in the minimum; any source-swap-symmetric distribution (canonical gates: AND, XOR) sits **exactly on the tie set**, where the delta method fails and the naive bootstrap is inconsistent. Concrete attack: your showcase gates are precisely where naive CIs under-cover. Demonstrate the coverage collapse by simulation; use m-out-of-n or directional-derivative methods there.

**Non-transfer among PID objects.** `I_min ≥ 0` always; sx pointwise atoms can be negative; the two-independent-bits COPY gate is the classic separator (I_min assigns full redundancy where "same amount ≠ same content"); XOR is synergy-dominant (`ln 2` nats). Maintain a frozen **disagreement witness table** (gate × object × atom values, exact) with CI asserting the disagreements persist — this is the executable firewall against "they're all PID, close enough."

**Multiplicity.** Conjunctive pass/fail gates (all 108 coordinates must match) need no correction — intersection tests are conservative. Discovery claims ("coordinate 37 is significantly negative in data") need max-statistic permutation or Bonferroni over 108. Corpus-descriptive statistics (354, 40 rows) carry zero inferential content — schema-tag them `descriptive`.

**Formalizable vs empirical.** Theorems: S1, S2, S3, DPI direction, MI invariance under strictly monotone marginal transforms (estimand invariant; the *estimator* is not — measure that gap, keep the statements separate), E1 impossibility, `[-D,D]`. Simulation-only: consistency in practice, bias magnitude, power, coverage, quantizer sensitivity. Real-data-only: application validity (sampling design, preprocessing, support declaration disclosed). Simulations never promote to theorems; each is bounded evidence with a config hash.

---

## 7. Machine/human/PDF parity

**Ledger schema (machine-readable, single source of truth).** Per obligation: `obligation_id`, `estimand_id` (typed; cross-type ops are schema errors), `statement_hash`, `status ∈ {open, bounded-evidence, theorem, refuted}`, evidence records each with: `type` (lean-thm | smt+proof | exact-rational | modular | corpus | simulation | search-negative | witness), `trust_base[]`, `shared_cut_ids[]` (to compute genuine failure diversity — three primes list the same cuts), `boundedness_scope` (domain/class/corpus id — "universal" requires a theorem record), `input_hashes[]`, `replay_cmd`, `resource_cost`, `tool_versions`. Negative results and failed routes are first-class records, as are open gates and the NO-GO status.

**Human/PDF projection.** Generated *from* the ledger; no hand-written numbers. Mandatory sections: assumptions per claim (auto-pulled), open-obligations table, failed-routes table, shared-cut matrix (so correlated evidence cannot masquerade as independent), hashes, replay commands, resource costs. Linter rules: **no naked numbers** (every numeral binds to `estimand_id` + uncertainty type ∈ {theorem-bound, class-CI, corpus-max, descriptive, none-declared}); unit field (nats) checked; canonical decimal strings must match ledger exactly.

**Semantic-parity mutations (build must fail):** flip one `status` in the ledger → PDF diff + assertion failure; delete one assumption from a theorem record → PDF assumption list check fails; swap nats→bits in one number → unit linter fails; truncate one hash → parity check fails; delete a failed-route record → "route count" cross-check fails; reorder the 108-coordinate manifest → manifest hash embedded in PDF mismatches. **Page-review protocol:** each review samples k random ledger rows and verifies verbatim presence in the PDF, plus one adversarial planted omission per cycle that the reviewer must catch (tests the reviewer, not just the pipeline).

---

## 8. Decision table

| # | Recommendation | Verdict | Falsifiable completion check |
|---|---|---|---|
| 1 | Saturation corollary S1 (`|Î| ≤ D`; `n ≳ k·e^I` necessity) proved in Lean, cited in all docs | **must** | Lean theorem hash in ledger; doc linter finds the statement adjacent to every KSG result |
| 2 | Checkerboard impossibility E1 as lemma + executable generator | **must** | Generator + proof artifact; simulation shows every in-repo estimator failing on the family at pre-registered margins |
| 3 | Categorical δ-interior deviation bound S3 with explicit constants | **must** | Written proof with computable `L(δ,A)`; numerical table of non-vacuity thresholds |
| 4 | Permutation-level theorem S2 + implementation | **must** | Exact-level verified by simulation at multiple `n, M` within binomial MC bands |
| 5 | Estimand registry + type firewall (incl. quantizer-indexed PID estimands) | **must** | CI mutation comparing across types fails the build |
| 6 | Ties/duplicates/NaN fail-closed domain assertions + witnesses | **must** | Injected duplicate/tie/NaN datasets abort with the declared error, in all W1/W2 cells |
| 7 | Inclusive index-map endpoint attainability audit (self-count convention) | **must** | Convention documented; attaining witness rows exist for exactly the claimed endpoints, or range tightened |
| 8 | Numerator-bound lemma + denominator checks for modular certificate; asymmetry documented | **must** | Lemma proved for corpus; docs state zero-residue direction is conditional; downgrade otherwise |
| 9 | Reconstruction manifest: hash-only acceptance, statistic-matching ban, fresh-clone clean-room rebuild | **must** | Clean-room rebuild reproduces all gates; a planted statistic-matched fake object is rejected |
| 10 | Proof-producing SMT + independent checker | **must** | All 4 obligations re-verified; 12 mutants yield independently evaluated countermodels |
| 11 | Ledger/PDF parity system + mutations | **must** | All listed parity mutations fail the build; planted omission caught in review |
| 12 | Gappa/Flocq universal range-conditioned float bound for helper | high-value | Theorem `≤ c·EPSILON` for all in-domain inputs `≤ N0`; FMA/reassociation mutations break it |
| 13 | Arb/MPFR certified enclosures replacing Decimal reference | high-value | Per-row enclosures with radius < gate granularity; poisoned-constant mutation caught |
| 14 | Kani/CBMC bounded brute-vs-kd equivalence on grids | high-value | Exhaustive within stated bounds; seeded count mutants killed |
| 15 | Disagreement witness table (COPY/XOR/AND; I_min vs sx; negative atoms) + clamp-injection mutation | high-value | Exact values frozen; clamp mutation anywhere fails CI |
| 16 | Pre-registered coverage grid + m-out-of-n UQ; nonregular-point (tie) coverage-collapse demo | high-value | Coverage report with simultaneous bands; documented under-coverage at symmetric gates |
| 17 | TLA+/Alloy phase & recovery machine | high-value | Guard-deletion mutation produces a violating trace |
| 18 | 108-coordinate manifest with dual routes + per-coordinate delta propagation | **must** | 108 delta runs pass; coordinate-permutation mutant fails all Programs A–E |
| 19 | CEGIS invariant miner feeding Lean obligations; adversarial corpus with new corpus ids | optional | Mined invariant either proved or logged as refuted-with-counterexample; no unproved invariant in docs |
| 20 | Verus/Creusot full functional proofs | optional | Verified crate behind same API with proof artifact in CI |
| 21 | Naive iid bootstrap for kNN statistics; smoothed bootstrap as default | **reject** | Design-level rejection documented with the duplicate-distance failure demo |
| 22 | Any clamping of MI inputs or atoms; promotion of corpus float max to input-space claim; independence framing of three primes; continuous-Ehrlich estimation claims before O6 | **reject** | Linter/schema make each unrepresentable; attempted insertion fails the build |

**Bottom line.** Close the saturation corollary, the impossibility artifact, the δ-interior bound, and the permutation-level theorem, and your statistical claims become exactly as strong as they can honestly be — everything else must live in the ledger as bounded, class-tagged evidence. The two sharpest open cracks I found are the inclusive-count endpoint attainability (item 7) and the unproved rounded-reference sufficiency behind `8*EPSILON` (item 13). Fix those before anything is called settled.