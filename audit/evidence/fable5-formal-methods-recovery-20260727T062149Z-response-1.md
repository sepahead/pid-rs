# Hostile review — proof/SMT correspondence audit

Scope note: I audit statements, bridges, proof objects, trust bases, shared cuts, and mutations. I treat nothing in the prompt as established except where a kernel-checked object or an exact finite computation is claimed, and I attack those too.

## Headline findings (sharpest first)

1. **Lean statement hazard: truncated `Nat` subtraction.** If the theorems are stated with `H (x-1)` over `ℕ`, hypothesis deletion or weakening (`1 ≤ k` → `0 ≤ k`) can leave a theorem *provable but different* via `0 - 1 = 0` truncation — vacuous truth the mutation suite may not catch if the 14 mutations only touch proofs. Restate subtraction-free over exclusive indices (`T = H j + H (n-1) - H nx - H ny` with `j+1 = k`, hypotheses `j ≤ nx`, `nx < n`). This kills the entire off-by-one class at the statement level instead of guarding it.
2. **Production can violate the proven hypotheses.** The derivation of `k-1 ≤ nx` assumes distinct distances. Duplicate/tied points give `ε = 0` and `nx = 0 < k-1`, i.e., `x = 1 < k`, outside the theorem's domain. Real (quantized) data produces ties. W1 must assert `k-1 ≤ nx,ny ≤ n-1` at runtime and fail closed — no silent jitter, per your own "added noise changes the estimand" rule. If the corpus has no tie-adjacent rows and W1 has no domain assertion, the bound theorem is being applied outside its hypotheses in production.
3. **Z3 layer is an order skeleton and can be vacuous.** With uninterpreted `H` and explicit ground order premises, `unsat` of `premises ∧ ¬bound` is only meaningful if the premise conjunction is itself `sat`. Freeze a `sat` witness for the premises of each of the four obligations. Also emit unsat cores and require every order premise to appear; a premise missing from the core is either redundant or a transcription hole relative to the Lean proof structure.
4. **No proof objects on the SMT side.** Z3's verdict is a trusted oracle. Fixable cheaply (Section 2).
5. **Modular certificate has an undefinedness hole.** Residue of `a/b mod p` requires `p ∤ b`. Harmonic denominators absorb every prime `< n`. With primes ≈ 10⁶ and any corpus row approaching that scale, the map is undefined and a sloppy implementation silently computes garbage. Mandate `gcd(reduced_denominator, p) = 1` per row per prime, fail closed, and state the boundedness (`n < p` sufficient condition) in the certificate's scope.
6. **Statement transcription is likely a shared cut across Lean, SMT, corpus, and Rust.** If one generator emits all four, the three-language agreement is one route wearing four coats. Either declare the canonical spec file as the (small, hashed, hostile-reviewed) trusted cut, or diversify authorship and bind by corpus differential. Say which; currently ambiguous.
7. **The floating-point claims are not auditable as stated.** "Exactly `8*EPSILON`" needs: the definition of EPSILON (2⁻⁵² vs 2⁻⁵³), the metric (absolute vs relative vs ulp-at-value), and the magnitude range of `T` on the corpus. `D ≈ ln n` can reach ~14; an *absolute* difference of 8·2⁻⁵² is below one ulp at that magnitude, so either corpus `T` values are small or the metric is relative. Publish the formula or the number means nothing.
8. **Categorical MGW exactness is achievable without floats.** Atoms are ℚ-linear combinations of logs of positive rationals. `{ln p : p prime}` is ℚ-linearly independent by unique factorization alone (clear denominators; `Π pᵢ^{nᵢ} = 1 ⇒ nᵢ = 0`). So represent every categorical PID quantity as a vector in the free ℚ-vector space on primes: zero-testing and identity-checking become exact and decidable, negative atoms are preserved exactly, and your 3-prime residue machinery extends to the rational coefficients. This closes the exactness gap for SxPID3 that floats cannot.

**Flags on ill-posed / overclaim-risk requests:** (a) "108 coordinates" is unfalsifiable until the canonical indexing (atom × realization, presumably 18-node PID3 lattice × 6 events, or whatever it is) is published in the ledger — binding claims without the index definition are not checkable; (b) "mutation-resistant invariants" is the wrong target — an invariant surviving all mutations is at risk of being a tautology; the target is high-kill oracles plus adjudicated survivors; (c) any probabilistic collision-rate language for the three primes is void because they were selected after rejecting 1,000,003 — the certificate is a deterministic corpus fact, which you already say; hold that line; (d) proving KSG statistical consistency in Lean is out of feasible scope — it must remain a cited assumption with explicit hypotheses, not an obligation.

---

## 1. First-principles reconstruction audit

The lost object was **uncommitted**, so every recovery source under-determines it. Attacks and fail-closed checks:

**A1. Fuzzy/3-way patch drift.** Replaying recorded edits onto a base that has moved (ambient advanced, or wrong parent commit chosen) lets hunks apply at textually similar but semantically wrong locations. `git apply -3` is especially dangerous: it *merges*, silently. — **C1:** forbid `-3` and `patch -F`; require the recorded preimage blob OID per file before each hunk wave and the recorded postimage OID after; any mismatch quarantines the wave.

**A2. Normalization laundering.** macOS filename NFD/NFC, CRLF filters, trailing-whitespace "fixes," and Unicode lookalikes in Lean identifiers (ψ variants) can make hashes "almost match," tempting normalization that changes semantics. — **C2:** byte-exact hashing only; `core.autocrlf=false`; `.gitattributes -text`; audit filenames as byte strings.

**A3. Wrong-revision reconstruction.** Transcripts contain many intermediate states, including abandoned rev-3-like states that pass old gates. Picking "a state that passes" is not picking "the state that was lost." — **C4:** the reconstructed tree's hash must equal the *last recorded post-edit state hash in the transcript*; anything else is NO-GO, even if all gates pass.

**A4. Worktree confusion.** Transcripts interleave ambient and isolated worktrees; an ambient edit replayed into the reconstruction is a silent object swap. — **C5:** every replayed tool call must carry a recorded cwd/worktree identity; ambiguous calls are quarantined for human adjudication, never auto-applied.

**A5. Generated-view inversion.** Reconstructing a "source" from a surviving generated view (SMT file, corpus CSV, olean) reverses the provenance arrow; many sources project to the same view. — **C6:** every generated artifact carries generator commit + inputs + replay command; the settled-byte gate regenerates and byte-compares; if the generator is lost, the artifact is demoted to opaque frozen evidence that can gate nothing new. **C11:** never restore build caches; rebuild clean.

**A6. Snapshot blind spots.** Alternate-index snapshot refs capture what was added to the temp index; untracked and ignored files — precisely the uncommitted work — are the likely misses. Repo-local refs under `/private/tmp` died with the directory. — **C9:** snapshots must record `git status --porcelain -uall --ignored` output; snapshot refs must be pushed to a remote namespace or bundled to durable storage; **C8:** a bundle is Schrödinger backup until a restore drill on a clean host clones it, rebuilds, and reruns gates (record time and hashes).

**A7. Hash-alone identification.** Two artifacts with identical bytes but different roles (truncated corpora, twin config files) collapse under hash-only matching. — **C10:** the manifest binds (role, path, blob OID), not OID alone.

**A8. Transcript gate laundering.** "The transcript shows the gate passed" is evidence of *intent*, not of the reconstructed object. — **C7:** zero pre-loss gate credit; rerun everything, **including mutation kill matrices**, which are state-dependent and are the most tempting thing to skip.

**C3 (manifest core):** every file in the recovered tree is tagged with provenance class ∈ {pushed-commit, snapshot-ref, bundle, transcript-patch, regenerated, human-memory}. Human-memory entries are quarantined behind independent re-derivation. The manifest itself is hashed, signed, and referenced by the recovery report.

---

## 2. Formal-method portfolio (ranked by distinct obligation closed)

For each: obligation / trust base / semantic bridge / boundedness / mutation plan / rejection rule. Correlation warnings are explicit.

**M1. cvc5 with proof production + independent checker (carcara/Alethe or LFSC/ethos).** *Closes:* solver-as-oracle for the four SMT obligations; produces checkable proof objects. *Trust:* the small checker + SMT-LIB semantics; the solver drops out. *Bridge:* the existing `.smt2` files, hashed. *Bounded:* exactly those obligations. *Mutations:* rerun the 12 countermodel mutations under cvc5; additionally corrupt one proof step in a stored Alethe file — checker must reject (checker-of-checker drill). *Reject if:* proofs don't replay; do not weaken statements to make them replay. *Correlation note:* Z3+cvc5 on the same files diversifies solver bugs, not statements. **Must.**

**M2. Frozen countermodels + tiny independent evaluator.** The 12 `sat` mutations currently rest on Z3's word. UF+LIRA models are finite function graphs; a ~100-line evaluator (second author, second language) checks each frozen model satisfies the mutated formula. *Closes:* the SAT direction with proof-object-grade evidence. **Must** (trivially cheap).

**M3. Premise-consistency witnesses + unsat cores (K3).** Per obligation: `sat` of the premise conjunction, frozen model; core must name every order premise. *Closes:* vacuity. **Must.**

**M4. Kani/CBMC bounded refinement of W1/W2.** *Closes:* the exclusive→inclusive index map on the *shipped* Rust: for all in-range `(n,k,nx,ny)` with `n ≤ N₀`, `W1(nx,ny) ≡ W2(nx+1,ny+1)` bit-for-bit; plus panic-freedom, overflow, and the runtime domain assertion (K8). CBMC's bit-precise FP can optionally verify the 4-term error bound exhaustively for small `N₀` — an independent check on M6. *Trust:* Kani/CBMC + Rust-to-MIR semantics. *Bounded:* explicit `N₀`; state it. *Mutation:* delete the `+1` — must fail. *Reject if:* harness models a copy of the code rather than the shipped function. **High-value.**

**M5. Second-prover port (Rocq or Isabelle) of the harmonic identity and bound.** The theorem is tiny; a port authored fresh from the canonical spec (not from the Lean file) removes Lean-kernel+Mathlib as the sole kernel and, more importantly, kills statement-transcription monoculture *if authored independently*. If mechanically translated from the Lean source, it is a correlated re-encoding — say so honestly and count it as one route. **High-value** (independent authorship), **optional** (translation).

**M6. Gappa (or Flocq/Rocq) universal FP bound for the binary64 helper.** *Closes:* the one thing the corpus cannot: a ∀-over-domain rounding bound. Model: table entries `Ĥᵢ` correctly rounded (provable exactly, entry-by-entry, from rationals — a finite decidable theorem, even `decide`-able in Lean for modest tables), then three roundings in the 4-term combination, magnitude-bucketed by `n`. *Bridge risk:* Gappa model vs actual codegen — pin evaluation order, forbid fast-math, verify no FMA fusion (Rust won't fuse without `mul_add`, but check aarch64 asm in CI); empirically bind by recomputing corpus rows in MPFR with the identical association and comparing bitwise. *Mutation:* permute association in the model only — divergence from code must be detected by the bitwise binding. *Reject if:* the bound is quoted without its domain bucket. **High-value.**

**M7. Arb/MPFR ball certificates for the digamma premise instances.** The premise `ψ(m) = H_{m-1} - γ` is your largest analytic cut; nothing in the portfolio touches it. Arb enclosures of `ψ(m)` vs exact `H_{m-1} - γ` (γ as a ball) at, say, 10⁴ sampled `m` up to large values is instance evidence with rigorous error bars — not a proof, and must be labeled evidence. *Mutation:* swap `H_{m-1} → H_m` in the checked identity — every instance must fail. **High-value** (it is the only failure-diverse pressure on the premise transcription itself).

**M8. Twin independent certificate checkers.** Two minimal implementations (different authors/models/languages/OS) that re-verify: residues, endpoint classification (354/7,844 split), gcd conditions (K6), hashes. *Closes:* single-evaluator shared cut in the modular route — the three primes currently share one evaluation pipeline; primes diversify *moduli*, not *code*. **Must.**

**M9. TLA+/Alloy model of the phase/custody state machine.** *Closes:* the NO-GO discipline, currently informal prose. Prove: no trace reaches `released` with an open gate; recovery re-entry forces settled-byte rerun (your new policy, as a checked invariant). *Mutation:* delete a guard — model checker must produce a counterexample trace. **High-value**, cheap.

**M10. lean-smt reconstruction of the SMT obligations inside Lean.** Eliminates solver trust by kernel-checking cvc5 proofs — but *re-correlates* the SMT layer with Lean. Choose M1 (independent toolchain) for diversity; choose M10 only if you want a single-kernel story. **Optional.**

**M11. Verus/Creusot functional proofs of the kd-tree.** Real obligation (tie handling, strict `<` at `ε`), but the cost is high and M4 + adversarial differential fuzzing (Section 3) covers it with better failure diversity per unit effort. **Optional.**

**M12. Gröbner/CAD algebraic procedures.** No polynomial obligations exist in the KSG bound (pure order reasoning) or in MGW (log-linear, handled by M-P1 below). **Reject** until a concrete polynomial identity appears.

**M13. Proof-producing SAT/DRAT.** No native SAT obligations; revisit only if lattice/antichain enumeration for PID3 is discharged by SAT. **Reject for now.**

**Shared-cut matrix (publish this).** Rows = routes; columns = cuts: {digamma premise, canonical spec/statement generator, corpus generator, Lean kernel+Mathlib, solver binary, checker binary, FP model+compiler, Python/Rust runtime, OS/filesystem}. A claim's residual trust is the union of cuts of *all* routes supporting it; two routes sharing the spec generator must never be counted as two.

---

## 3. Evolutionary / genetic / CEGIS route

Search spaces worth funding, each with a minimization→certification pipeline:

1. **FP association adversaries.** GA over (input row, summation permutation, reduction-tree shape) maximizing |computed − exact-rational|. Conversion: shrink `(n,k,x,y)` by bisection preserving error above threshold; freeze as a rational-truth corpus row. Semantics: a find above `8ε` *updates the corpus max* (that number was never a bound); a find above `32ε` fails the gate — that is the falsification path, keep it live.
2. **Tie-cluster point sets for kd-tree vs brute.** Search over multisets with heavy coordinate/distance ties (including exact duplicates → the `ε=0` domain violation of finding #2); fitness = count discrepancy or domain-assertion trigger. Delta-debug to the smallest witness; freeze as a W-series witness with rational coordinates.
3. **CEGIS on index-map invariants.** Candidate invariants over `(n,k,nx,ny)` checked against a model of the code path; counterexamples become corpus rows; repaired invariant goes to Lean/Kani, not to a test comment.
4. **Extremizer search for PID atoms.** Distributions maximizing negativity of MGW atoms and gaps between MGW/WB/Ehrlich objects — these become the negative-atom corpus (P3) and firewall canaries.
5. **Identity discovery.** Symbolic regression over a small grammar (harmonic sums, lattice Möbius sums) fitted on exact rationals. Firewall: a fitted identity is a *conjecture* with a recorded counterexample-search budget until proved in Lean; it may never be load-bearing while fitted.
6. **Oracle strengthening, not "mutation-resistant invariants."** Evolve *test inputs* to maximize mutant kill rate. Each surviving mutant is adjudicated: prove equivalence, or add an oracle. An invariant that no mutant can falsify must be vacuity-checked (does it fail on at least one intentionally wrong artifact?).

**Why search failure proves nothing:** GA coverage carries no measure; the fitness landscape can hide isolated needles (FP error extrema are notoriously spiky); absence of a found counterexample yields no bound of any kind. Record negative searches as effort receipts (seeds, generations, wall-clock) in the ledger's negative-results section — evidence of diligence, never of safety. Only exhaustive bounded enumeration (M4-style) converts absence into a theorem, and only up to `N₀`.

---

## 4. KSG closure attacks

**Exact theorem.** The mathematics is right: with `ψ(m) = H_{m-1} − γ`, the two γ's cancel pairwise, `T = H_{k-1}+H_{n-1}−H_{x-1}−H_{y-1}`, and monotone `H` gives `−D ≤ T ≤ D`, tight at `(x,y)=(k,k)` and `(n,n)`. Attacks that remain: (i) the `Nat`-subtraction restatement (finding #1) — demand statement-level mutations covering hypothesis deletion, `<`↔`≤`, index shift ±1, and `H_{m-1}`↔`H_m` in the premise, with a published kill matrix; 14 mutations over 19 declarations is thin if any class is uncovered; (ii) `#print axioms` on every theorem with a whitelist {premise, propext, Classical.choice, Quot.sound}; a stray axiom or `native_decide` must trip the gate (K2); (iii) algorithm identity: confirm the four-term object is KSG-alg-1's local term (`ψ(k)`, not `ψ(k)−1/k`); if any downstream doc says "KSG estimator" generically, that is an overclaim on the statement's scope; (iv) confirm no downstream text quotes the digamma form as *proved* — it is premise-conditional; the unconditional theorem is the harmonic one.

**Index maps.** `k−1 ≤ nx,ny ≤ n−1 ↦ x = nx+1 ∈ [k,n]` is coherent. Attacks: double increment by a caller passing inclusive counts to W1 (fix with newtypes `ExclusiveCount`/`InclusiveCount`; one conversion site; M4 proves it); the degenerate corner `n=2, k=1` (`H₀=0`, `D=1`) — if the corpus lacks it, add it; and the tie violation of finding #2 — the map's *precondition* is not production-guaranteed, so K8's runtime assertion is part of the theorem's applicability, not hygiene.

**Modular implication.** Correctly framed as fault diversity. Remaining holes: K6 (denominator invertibility) is mandatory; the checked quantity must be exact-rational end-to-end (a float anywhere upstream and the residues certify the wrong object); the three primes share one evaluator (M8); post-hoc prime selection forbids probabilistic language forever — the honest claim is "zero collisions on this frozen corpus for these three primes," full stop. Also verify the endpoint classifier itself: rows with `T = 0` (e.g., `x=k, y=n`) are nonendpoints with nonzero defect `D²`; assert the classifier distinguishes `T=0` from `|T|=D` — a plausible implementation bug the primes would faithfully certify in the wrong direction.

**Floating-point language.** Publish the metric formula (K7): EPSILON's value, absolute/relative/ulp, reference definition (correctly rounded binary64 of the exact rational?), and the magnitude distribution of `T` on the corpus. The two routes having different maximizers (8ε rounded-reference vs <9.761311ε exact) is expected — different metrics — and must stay separate in prose; any sentence letting a reader infer a universal ULP or correct-rounding property is an overclaim. The 32ε gate is a policy threshold; label it so.

**W1/W2 production refinement.** Attacks: parallel reduction reassociation (demand a fixed reduction tree or per-mode frozen maxima, K10); witness comparisons must be bitwise (`to_bits`), or ±0 coverage is illusory since `+0.0 == -0.0` (K9); compiler/platform drift (aarch64 FMA, libm leakage — the helper must be table+arithmetic only, asm-grepped in CI); and the tie assertion (K8).

**Release/custody.** Sign the *manifest of blob OIDs + gate outcomes*, not artifacts individually, or a regenerated view can be swapped post-signing. The NO-GO logic itself should be a checked object (M9). Drill the fail-closed path: seed a known-bad artifact; the pipeline must go red — a gate that has never failed is untested.

---

## 5. PID2 and MGW SxPID3 forward design

Two failure-diverse routes per obligation; correlation flagged.

**O1 — PID2 represented-sum consistency** (`I(S₁;T)=R+U₁`, `I(S₂;T)=R+U₂`, `I(S₁S₂;T)=R+U₁+U₂+S`). *Route 1:* Lean theorem over ℚ: given the redundancy value, the atom solution exists, is unique, and is linear in inputs (kernel-checked linear algebra). *Route 2:* two independent exact evaluators (different authors) on frozen inputs + 3-prime residues on the atoms. Independent: yes, different failure modes (statement vs evaluation).

**O2 — composition from MI inputs, no clamping.** *Route 1:* type-level: MI inputs enter as signed exact objects; no `max(0,·)` exists in the code path (grep-gate + code review). *Route 2:* clamp-mutation kill — insert clamping; corpus rows with negative atoms must fail. This requires **P3: the corpus must contain negative-atom rows** (XOR-type synergy alone won't do it; use MGW pointwise negativity extremizers from Section 3.4). Without P3, the clamp mutant survives and O2 is untested.

**O3 — MGW SxPID3 lattice and Möbius correctness.** *Route 1:* generate the PID3 redundancy lattice by fresh antichain enumeration with a checked antichain predicate; Lean-verify the Möbius matrix by kernel-checked exact inverse of ζ over ℚ. *Route 2:* hard-code the literature lattice and prove isomorphism to Route 1's (P2). These are independent in the transcription dimension, which is the dominant risk for an 18-node combinatorial object.

**O4 — pointwise atom exactness.** *Route 1:* the formal log-vector representation (headline #8): every `i^sx` value is `Σ qᵢ ln pᵢ` with `qᵢ ∈ ℚ` over prime `pᵢ` via factorization of the rational masses; equality/zero tests are exact; negative atoms are exact signed objects. Extend the 3-prime residue certificate to the ℚ-coefficient vectors (K6 applies). *Route 2:* Arb ball enclosures of the same atoms; every exact value must lie in its ball. Independent: yes (symbolic vs numeric). Inequality decisions (and any `min`/argmin, including WB `I_min`) are certified by interval separation, with exact ties caught first by the vector test — this terminates precisely because the equal case is decidable.

**O5 — 108-coordinate binding (Programs A–E).** Ill-posed until the canonical index (which atoms × which realizations/instances) is published in the ledger (P5); then bind each coordinate by ≥2 routes drawn from: {formal log-vector exact value, Arb enclosure, independent second implementation, Möbius/consistency-sum identity (atoms summing to pointwise mutual informations at the designated lattice cuts), source-permutation orbit equivariance (S₃ action; one computed coordinate binds its orbit), residue certificate on ℚ-coefficients}. Publish a 108-row binding matrix; any coordinate with <2 *uncorrelated* routes is an open gate. Routes sharing the lattice table are correlated — that is exactly why O3 has two lattice generations.

**O6 — object firewall.** Six estimands, zero mapping theorems. *Route 1:* estimand type tags in code and schema (`ContinuousEhrlich`, `CategoricalMGW`, `WilliamsBeer`, …); the schema validator rejects any evidence record whose claim object mismatches its estimand tag (P4). *Route 2:* semantic canaries — assertions valid for one object and false for another (WB nonnegativity holds for `I_min`; asserting it on MGW atoms must be *rejected by type*, not silently pass; a nats/bits canary distribution catches ln 2 scale smuggling). Mutation: mislabel one artifact's estimand — the validator must go red. Note the trap in the other direction: any test asserting nonnegativity on MGW/Ehrlich atoms is itself a specification bug; your "negative atoms are valid" rule must be enforced against well-meaning test authors.

---

## 6. Statistical theorem discipline

Separate the ledger's claim classes; each has a different strongest achievable artifact:

- **Estimand identifiability** (continuous MI under declared support; noise changes the estimand): cited assumptions with explicit hypothesis lists. Not formalizable at feasible cost; never phrase as proved.
- **Deterministic estimator algebra**: formalizable and worth it. E.g., the global estimate is a mean of local `T`'s, hence `|Î| ≤ D` — a cheap Lean corollary of the bound theorem, and a useful a-priori runtime range check.
- **Bias/variance**: simulation only. Closed-form ground truth families (Gaussian `I = −½ln(1−ρ²)`, copula constructions); grids over `(n,k,ρ,dim)`; seeds, CIs, and multiplicity control (BH or FWER) whenever pass/fail language is used (S3). Deterministic corpus gates need no multiplicity; statistical claims do.
- **Resampling class — a concrete trap:** naive nonparametric bootstrap duplicates points, creating ties that violate KSG's distinct-distance premise (see finding #2) and inflate neighbor counts; bootstrap CIs on KSG are therefore measuring a perturbed estimand. Use subsampling without replacement, or a smoothed/parametric bootstrap *with the estimand change declared* (S2).
- **Dependence**: iid is an application-validity assumption; serial data needs block subsampling and a declared validity domain.
- **Promotion rule**: schema field `claim_scope ∈ {kernel-theorem, solver-checked, corpus-fact, bounded-exhaustive, simulation, assumption}` (S1); the parity projection must render scope adjacent to every number. "Corpus max 8ε" and "simulated bias ≤ b" can never migrate classes by paraphrase.

---

## 7. Machine/human/PDF parity

**Ledger schema (machine-readable, one record per obligation):** `id; object (one of the six estimands); canonical statement (hash of pretty-printed normal form); claim_scope; bounds/domain; trust_base (list of shared-cut IDs from the M-matrix); evidence[] (blob OID, replay command, environment lock, resource cost); mutations[] (id, class, kill status, adjudication for survivors); negative_results[] (failed routes with reasons — the 1,000,003 rejection lives here, permanently); open_gates[]; signatures`. Validate in CI against a strict schema (unknown fields rejected, required fields non-optional).

**Projection:** LaTeX/PDF generated *only* from the ledger by a total projection function — every ledger section maps to a mandatory document section, so omission requires deleting ledger content, which breaks hashes. The ledger hash is printed in the PDF footer; CI recomputes ledger→PDF and byte-compares extracted text against the canonical projection (D1). Hand edits to LaTeX are forbidden.

**Semantic-parity mutations (D3):** delete one assumption record → build must fail or PDF must visibly change and parity hash break; drop an open gate → same; flip a `claim_scope` from corpus-fact to theorem → schema validator rejects; reorder evidence → canonical ordering makes the diff detectable; strip a resource-cost field → schema rejects.

**Page-review mutations (D2):** human review is itself a gate, so calibrate it: insert K seeded defects (wrong index in a formula, dropped hypothesis, swapped 8ε/32ε) into review copies; a review that finds < threshold·K is invalid and redone. This turns "hostile review happened" into a measured, falsifiable event.

---

## 8. Decision table

| # | Recommendation | Class | Falsifiable completion check |
|---|---|---|---|
| 1 | Subtraction-free restatement over exclusive indices (K1) | must | New Lean file; hypothesis-deletion mutants now unprovable (not vacuously true); kill matrix published |
| 2 | Statement-level mutation classes + published kill matrix | must | ≥1 statement mutation per theorem across classes {index±1, `<`↔`≤`, hyp-drop, `H_m`↔`H_{m−1}`}; all killed or adjudicated |
| 3 | `#print axioms` whitelist gate; ban `native_decide` (K2) | must | CI log per theorem; seeded stray-axiom mutant trips gate |
| 4 | Premise-`sat` witnesses + unsat-core coverage (K3/M3) | must | Frozen models; cores name every order premise |
| 5 | Freeze countermodels + independent evaluator (M2) | must | 12 models re-verified by second-author evaluator |
| 6 | cvc5 + carcara/LFSC proof checking (M1) | must | Proofs replay; corrupted-proof drill rejected |
| 7 | `gcd(denominator, p)=1` fail-closed + boundedness note (K6) | must | Check runs on all 8,198×3; seeded divisible-denominator row goes red |
| 8 | Twin independent certificate checkers (M8) | must | Both reproduce 354/7,844 split and all residues; disagree on a seeded fault |
| 9 | Runtime domain assertion in W1; tie ⇒ fail closed (K8) | must | Duplicate-point input aborts with diagnostic; no silent jitter path exists |
| 10 | FP metric formula publication (K7) | must | Ledger record defines EPSILON, metric, reference, magnitude buckets; numbers recomputed from it |
| 11 | Recovery manifest with provenance classes + full gate rerun (C1–C11) | must | Manifest validates; final hash = last transcript state; zero pre-loss credit; mutation matrices rerun |
| 12 | Bundle/snapshot restore drill on clean host (C8/C9) | must | Fresh clone + fetch refs + rebuild + gates green; cost recorded |
| 13 | Negative-atom corpus rows to kill clamp mutants (P3) | must | Clamp mutant fails on ≥1 frozen row |
| 14 | Estimand type tags + mislabel-rejection (P4/O6) | must | Mislabeled artifact rejected by validator |
| 15 | Ledger schema + PDF projection + parity mutations (D1–D3) | must | All omission mutants break the build; seeded-defect review meets threshold |
| 16 | Kani/CBMC bounded W1/W2 refinement (M4) | high-value | Harness on shipped code, `N₀` stated; `+1`-deletion mutant fails |
| 17 | Gappa/Flocq domain-bounded FP theorem + code binding (M6) | high-value | Bound ≥ corpus max; MPFR same-association bitwise binding on corpus |
| 18 | Arb instance evidence for digamma premise (M7) | high-value | 10⁴ enclosures pass; `H_m` off-by-one mutant fails all |
| 19 | Independent second-prover port of harmonic theorem (M5) | high-value | Authored from canonical spec, not the Lean file; declared in cut matrix |
| 20 | TLA+/Alloy phase-gate model (M9) | high-value | Guard-deletion mutant yields counterexample trace |
| 21 | Formal log-vector exactness for MGW + coefficient residues (P1) | high-value | 108 coordinates exact; zero-tests via factorization; Arb balls contain values |
| 22 | Dual lattice generation + isomorphism (P2); coordinate index publication (P5) | high-value | Isomorphism checked; 108-row binding matrix with ≥2 uncorrelated routes each |
| 23 | Tie-cluster GA + delta-debugged W-series witnesses (§3) | high-value | ≥1 minimized tie witness frozen; kd/brute agree post-fix |
| 24 | Subsampling-not-bootstrap policy for KSG resampling (S2) | high-value | Written policy; a bootstrap-tie demonstration recorded as negative result |
| 25 | lean-smt reconstruction (M10) | optional | Only with correlation disclosure vs M1 |
| 26 | Verus/Creusot kd-tree proofs (M11) | optional | Only if M4+fuzzing leaves a named residual obligation |
| 27 | Symbolic-regression identity discovery (§3.5) | optional | Any fitted identity marked conjecture until Lean-proved |
| 28 | CRT reconstruction / probabilistic prime-collision claims | reject | Any such sentence is a defect; primes are deterministic corpus facts |
| 29 | Universal promotion of corpus FP maxima | reject | Grep-gate for "ULP"/"correctly rounded" outside scoped records |
| 30 | Clamping PID MI inputs; silent noise/jitter; MGW reference repo as authority; "mutation-resistant invariants" as a goal; Lean proof of KSG consistency | reject | Presence anywhere = NO-GO finding |

**Bottom line.** The harmonic-bound core is sound and nearly closed; the live risks are at the seams: statement transcription monoculture, `Nat` truncation vacuity, an SMT layer without proof objects or vacuity witnesses, a modular certificate with an undefinedness hole and a single evaluator, unpublished FP metrics, and production inputs that can leave the theorem's domain via ties. Every one of these has a cheap fail-closed check listed above. The recovery policy is sound if — and only if — reconstruction is validated exclusively by forward-run gates against the last transcript state hash, with pre-loss runs stripped of all credit including mutation matrices.