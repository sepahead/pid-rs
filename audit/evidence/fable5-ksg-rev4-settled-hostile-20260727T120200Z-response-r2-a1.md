# Settled-hostile review — KSG revision-4 M1a candidate (source-blind algebra audit)

**Standing disclaimer:** this document is advisory falsification input. Nothing below is verification, authority, or a release decision, and nothing below claims that my own output proves anything. Where I write "confirmed," read "consistent with my independent derivation on the provided bytes."

---

## Independently reconstructed claim and exact scope

Before reading the repository's wording, I reconstructed the candidate's core claim from first principles as:

> **Arithmetic core.** For integers `n ≥ 2`, `1 ≤ k < n`, `k ≤ x,y ≤ n`, under the *typed premise* `psi(m) = H_(m-1) − gamma` at the four arguments only, the four-term local quantity `T = psi(k)+psi(n)−psi(x)−psi(y)` equals the exact rational `H_(k−1)+H_(n−1)−H_(x−1)−H_(y−1) = (H_(n−1)−H_(max−1))−(H_(min−1)−H_(k−1))`, in nats, and satisfies `−D ≤ T ≤ D` with `D = H_(n−1)−H_(k−1)`, **sharp on that rectangle only** (`+D` at `x=y=k`, `−D` at `x=y=n`), with no assertion that the rectangle equals the runtime unique-shell image.
> **Corpus core.** On the frozen 8,198-row corpus (6,920 exhaustive box rows through `n=16` plus 1,278 declared stress rows), `T=0` **iff** `{x−1,y−1}={k−1,n−1}` (354 endpoints = 240 + 114), the "only if" direction certified per-row by nonzero residues in each of three prime fields exceeding the maximum reciprocal-summand index 999,999; plus finite-corpus binary64 facts (8·ε rounded-reference max, 40 ties, first at row 7598; unique exact-rational max at row 7673 strictly below 9.761311·ε; both below 32·ε; signed partition 354/0/7844; 150 vs 121 association discriminators) and finite bridges W0–W2b.
> **Disposition.** Bounded core GO on stated domains only; repository/publication integration NO-GO with 13 open conjunctive gates; M1c authority only after a pushed M1a implementation commit.

Everything below audits the candidate against this reconstruction. Scope of this review = exactly the bytes supplied in the context (several load-bearing artifacts are digest-pinned but byte-absent; these are listed as unverifiable, not as passed).

---

## Derivation ledger (computed before comparison)

* **D1 — Identity & cancellation.** Coefficients `(+1,+1,−1,−1)` sum to zero ⇒ all four `gamma` cancel. Range form verified by expansion. ✓ matches `claim-v4.md:44–60`, `stats.rs:213–237`.
* **D2 — Bound & sharpness.** `T + D = (H_(n−1)−H_(a−1)) + (H_(n−1)−H_(b−1)) ≥ 0`, equality iff `x=y=n`; `D − T ≥ 0`, equality iff `x=y=k`. So `−D` is attained **only** at `x=y=n` on the box. At `n=2,k=1`: values `(+1, 0, 0, −1)` — exactly W0.
* **D3 — Runtime image.** Under validated unique shell (`k−1` strict-interior joint points, one boundary), strict-interior points lie in both strict marginals and `|A∩B| = k−1` exactly for both the KSG Chebyshev max-composition and the ISX disjunction/target composition. Inclusion–exclusion gives `x + y = |A∪B| + k + 1 ≤ n + k` in the inclusive parametrization, identical for the exclusive map. Consequently `x=y=n` needs `2n ≤ n+k`, impossible for `k<n`: **`−D` is never runtime-attainable**, while `+D` passes the count constraint. The balanced-argument minimizer at `x+y=n+k` is `H_(k−1)+H_(n−1)−H_(⌊(n+k)/2⌋−1)−H_(⌈(n+k)/2⌉−1)` (concavity of `H`). This reproduces exactly the packet's *unpromoted* candidate constraint and lower bound — I found no place where it is promoted. ✓
* **D4 — Corpus combinatorics.** Exhaustive rows: `Σ_{n=2}^{16} Σ_{k=1}^{n−1} (n−k+1)² = Σ (S(n) − 1) = 6,935 − 15 = 6,920`. Stress rows: `129 + 154 + 179 + 4·204 = 1,278`. Endpoints: `2·120 = 240` exhaustive, `2·57 = 114` stress, total 354; nonendpoints 7,844; splits 240/6,680 and 114/1,164. All counts **rederived exactly**.
* **D5 — Row-index arithmetic.** Independently reconstructing the row order: block `n=4096` starts at 7586; offset 12 ⇒ `(4096,1,2048,2048)` at **7598**; offset 87 ⇒ `(4096,4,2049,2049)` at **7673**; `n=65536` block offset 162 ⇒ `(65536,64,32799,32799)` at **7952**; `n=10⁶` block offsets 51/55/75/99 ⇒ **8045 = (10⁶,3,2,3)**, **8049 = (10⁶,3,3,2)**, **8069 = (10⁶,4,3,3)**, **8093 = (10⁶,4,999999,999999)**. All five frozen indices reproduce exactly.
* **D6 — Key rationals.** `(k,n,x,y)=(2,8,5,2)`: `T = H_7 − H_4 = 107/210` (W1/W2 local target). `(n,k,x,y)=(8,2,3,5)`: `T = 1/105 < 1/7` (C30 counterexample; it is literally row 6 of the W1 fixture with sources swapped). Recomputing all eight ISX rows of the W2 fixture from the committed expected `(radius, n_α, n_t)` table gives exact mean `284/3360 = 71/840` — the public-mean claim's exact reference **rederives from the committed per-row counts**. Boundary triple `11/6, 5/6, −1/3` at `n=4` also rederives. `-0x1.6b52fe6a01407p+2 ≈ −5.6769` matches `H_3 + H_4095 − 2H_2049 ≈ −5.677`.
* **D7 — W2b.** For `k=1,n=3`, targets `[0,0.4,0.8]`, `s1=[0,1,3]`, `s2=[0,10,30]`: per-row joints `{1,3},{1,2},{2,3}` ⇒ radii `1,1,2`, unique shells, `n_t=3`, `n_α=1`, `T=+0` at each row; `0.8f64 − 0.4f64 = 0.4f64` exactly (same mantissa, exponent shift), so no hidden representability tie. Matches the packet, the private `isx.rs` array, and the public `tests/isx.rs` assertions. It genuinely refutes `n_α ≥ k+1`.
* **D8 — Modular implications.** With `p > 999,999`, every `1/j` summand is invertible; exact zero ⇒ zero residue; hence nonzero residue ⇒ exact nonzero (one-way only). **Structural explanation of the rejected prime (new):** for any prime `p`, `H_(p−1) ≡ 0 (mod p)` and therefore `H_(p−1−t) ≡ H_t (mod p)`. For `p = 1000003`, `999999 = p−4`, so `H_999999 ≡ H_3 (mod p)` **identically**, forcing zero residues at exactly the rows whose exact value is `±(H_999999 − H_3)` — precisely rows 8045/8049/8069 (`+`) and 8093 (`−`). I verified the congruence by hand (`H_999999 ≡ 1+inv2+inv3 ≡ 166669 ≡ H_3 mod 1000003`). For the selected primes the analogous reductions are `H_999999 ≡ H_33, H_37, H_81` respectively, and indices 33/37/81 occur nowhere in the corpus index set — so this class of structural collision cannot occur there. This *confirms* the certificate's negative control and shows the four collisions are one algebraically forced event, exactly as the failure memo says.
* **D9 — Signed-zero facts are forced, not lucky.** In RN binary64, `u − v` rounds to zero iff `u = v` (then `+0`). Hence: (i) the selected range association gives `(+0)−(+0) = +0` at every structural endpoint algebraically — the 354/0/0 partition is a small theorem of the association, and (ii) **no** four-term association of finite table entries can produce `−0`. The "0 negative-zeros" counters are therefore vacuously satisfied guards (see F7).
* **D10 — Directed-rounding soundness.** ROUND_FLOOR accumulation of lower prefixes / ROUND_CEILING upper, with cross-signed subtraction, yields valid enclosures; symbolic endpoint zeros are exact; strict comparison against a floor-rounded `9.761311·ε` threshold is the sound direction. Note the exact-rational max (≈9.7613·ε) **exceeds** the 8·ε rounded-reference comparator — which is precisely why C20's separation matters; both < 32·ε.

---

## 1. Finding table

| ID | Severity | Affected object | Location | Proposition | Minimal witness / derivation | Independent reproduction | Shared cuts | What would falsify my allegation |
|---|---|---|---|---|---|---|---|---|
| **F1** | **Major** (concretizes the already-open `git_phase_isolation` gate; fail-closed) | Phase gate vs. live worktree | `audit/evidence/ksg-rev4-phase-path-policy.json:12–478`; `scripts/check-ksg-phase-isolation.py:354–411, 990–1007, 1583–1594, 2355–2364`; context Git state (`??` block) | The worktree contains **5 untracked paths not in the 93-path policy** (`audit/evidence/fable5-ksg-rev4-settled-hostile-…{context.md, prompt.md, receipt.json, oversize-negative-receipt.json, runner.mjs}`), so `check-ksg-phase-isolation.py` must currently fail both the precommit untracked partition and the policy-delta equality; the M1a commit cannot include them without policy reseal | `?? = 61` untracked = 56 policy-A + 5 review artifacts; prior `fable5-*` receipts are tracked in `EXPECTED_CHANGED_PATHS`, so `.gitignore` (pinned baseline blob `918f4cf…`) does not exclude the prefix | `python3 scripts/check-ksg-phase-isolation.py` → expect nonzero with delta/partition mismatch naming the 5 paths; relocate the 5 files → expect the untracked-partition check to pass | Git untracked enumeration semantics; root `.gitignore` as sole visibility source | Root `.gitignore` actually matching `audit/evidence/fable5-*`, or the checker passing on the live snapshot |
| **F2** | Info | Review snapshot manifest | Context "Complete changed-path byte manifest" vs Git state | The manifest's claim to cover "every tracked modification and untracked file" is unmet for 3 files (`…context.md`, `…receipt.json`, `…oversize-negative-receipt.json`); self-reference makes the context file inherently unpinnable | Set difference of `??` list vs manifest paths | Diff the two lists | Same snapshot tooling | Those digests appearing in a companion receipt |
| **F3** | Info / hardening (confirmation with recommendation) | Modular route documentation | `failures/modular-zero-residue-collisions-v4.md:22–46`; certificate/checker collision constants (`check-ksg-harmonic-modular-certificate.py:78`) | The 4 rejected-prime collisions are **structurally forced** by `H_(p−1−t) ≡ H_t (mod p)` with `p−4 = 999999`; selected primes avoid it only because indices 33/37/81 are absent from the corpus. The three selected lanes therefore share *more* structure than "redundant fault diversity" suggests (though the one-way implication is unaffected) | D8 above (hand-checked `166669 ≡ 166669`) | One-line Python: compare `H_999999 mod p` with `H_3/H_33/H_37/H_81 mod p` for the four primes | Same corpus/index set | The congruence failing numerically |
| **F4** | Minor | Chronology wording | `completion-active-resume.md:249–250` ("The M1a implementation commit is the unsigned `afc45ff…`") vs `obligations-v4.md:72` (G1 open) and packet gate `unsigned_main_commit_and_receipt` | A superseded-but-retained section names `afc45ff` "the M1a implementation commit" while the live gates treat M1a as future; a reader can conflate the earlier partial commit with the pending final M1a | Direct byte comparison | Read both sections | Retained-history convention | A dated clarifying line in the next live-resume update |
| **F5** | Info | Local release automation | `justfile:137–139, 336` | `just release-audit` embeds the deliberately-red `ksg-integration-decision`; expected-red must remain documented so a red result is never "fixed" by gate weakening (currently it is documented; keep it) | Direct read | `just release-audit` at M1a → nonzero at the decision step, all scoped steps green | Lifecycle design | — (observation) |
| **F6** | Minor | Packet key naming | `active-packet-v4.json:207–222` (`w1.helper_arguments` = `(k,n,x,y)`) vs `:157–169` (`c30…_n_k_x_y`) | Two witness keys use different argument orders; each is prose-disambiguated but a machine consumer can misread `w1`/`w2` | Compare `[2,8,5,2]` vs `[8,2,3,5]` labeling | JSON read | Manifest regeneration at M1c | Renaming keys with explicit order suffix at the planned M1c regeneration |
| **F7** | Info | Signed-zero "tripwires" | `stats.rs:499–501, 541–549, 590–593`; `check-ksg-harmonic-revision.py:2172–2192`; prose "regression tripwires" | Per D9, `−0` cannot arise from any of these subtractive associations in RN; the negative-zero counters are provably always 0 and hence have zero mutation-detection power for association changes (they only catch a sign-negation-style mutation). No claim is contradicted — but the prose slightly overstates their discriminating value | Sterbenz-adjacent fact: `u−v = 0` in RN ⇔ `u=v`, result `+0` | Attempt to construct `−0` from any 4-term association over the table — impossible by IEEE-754 RN | IEEE semantics premise shared with all binary64 routes | An IEEE-754 RN mode producing `−0` from `u−v` with `u≠v` or `u=v` |

No finding above alleges a mathematical error in the bounded core. I searched for one and failed (see rejected attacks and the CEGIS note).

---

## 2. Classified lists

### Genuine blockers (for M1a; all fail-closed, none newly semantic)
1. **The 13 declared open integration gates stand.** Nothing in this snapshot closes any of them; several (settled full CI, serial/parallel recapture, final hostile review, claim-custody final replay) are execution obligations that cannot be discharged from static bytes.
2. **F1** — the current concrete content of the `git_phase_isolation` gate failure: the 5 review-artifact paths must enter the policy (and the phase facts must be regenerated) or be relocated before any gate run or M1a synthesis can succeed. Note the reseal cascade: policy bytes → `PHASE_PATH_POLICY_SHA256` constant → generated phase facts; the phase scripts are self-unhashed by design so the cascade terminates there.

### Hardening — valuable, non-blocking
- **F3**: record the `H_(p−1−t) ≡ H_t` mechanism in the next modular memo revision (M1c-era artifact, not a frozen-byte edit), and add a one-line negative control asserting indices 33/37/81 are absent from the corpus index set.
- **F7**: reword "regression tripwires" for the `−0` counters, or add a mutation the counters *can* catch (e.g., a negated-term mutant asserting the counter fires).
- **F6**: rename witness keys with explicit argument-order suffixes at the planned M1c packet regeneration.
- **F4**, **F5**: one-line clarifications in mutable process docs.
- Correlation note: the three selected primes share the `p−m` reduction structure (F3); the routes-v4 "redundant fault diversity, not independent proofs" wording is already correct — consider citing the mechanism explicitly so nobody later upgrades the triple to independence.

### Already-closed concerns (independently reproduced here; not trusting frozen outputs)
- W0 values `(+1,0,0,−1)`; box sharpness with `−D` unique at `x=y=n`; runtime `−D` denial (D2/D3).
- 6,920 / 1,278 / 8,198 / 354 = 240+114 / 7,844 / 6,680 / 1,164 — all rederived (D4).
- Frozen row indices 7598, 7673, 7952, 8045, 8049, 8069, 8093 — all rederived from the reconstruction order (D5).
- `107/210`, `1/105 < 1/7` (C30), `71/840` from committed per-row counts, `11/6, 5/6, −1/3`, selected value ≈ −5.677 (D6).
- W2b `(n_α,n_t)=(1,3)`, radii `1,1,2`, `+0` per row; both compiled predicates (private diagnostics + public mean) bind production dataflow (`isx_local_diagnostics` is the production path).
- Rejected-prime collision set = one structural event; sign claims (`>0,>0,>0,<0`) verified (D8).
- One-way modular direction sound; no CRT and no converse used anywhere in the inspected prose; corpus-only iff correctly assembled from cancellation + separation.
- x+y ≤ n+k derivation valid for *both* KSG and ISX/PID3 parametrizations under unique-shell semantics — no cross-route set-argument transfer error found, and the constraint is nowhere promoted (D3).
- Per-call-site helper preconditions (`k ≤ x,y ≤ n`) hold at all six production sites given shell validation (`ksg.rs:2302,2382,2731,2811`; `isx.rs:1128`; `pid3.rs:1297`).
- Two "8"s (8·ε vs eight ordered positions) and 8/9.761311/32 multipliers kept distinct in every inspected artifact.
- Sidecar byte lengths arithmetically consistent with their format (99 = 64+2+32+1; 107 = 64+2+40+1).
- Digest cross-bindings: ~40 visible embeddings (packet ↔ checker constants ↔ phase blob pins ↔ manifest ↔ identity ↔ ecosystem ↔ registry ↔ release scope) all mutually consistent, including the corrected assurance-registry digest `5aa34f1d…` in both `ecosystem-capabilities.json:1829` and `ECOSYSTEM_CAPABILITIES.md:17`, and identity's repin to catalog `d2ad2e22…` / release `4fe9e5e4…`. **I searched for a second-order stale digest caused by that correction and found none in the provided bytes** (see open questions for the projections I could not recompute).
- Baseline path arithmetic: 437 − 402 = 35 modified-baseline paths, and the changed-path taxonomy reproduces exactly 35.

### Rejected / ill-posed attacks
- "Universal `|T| ≥ 1/(n−1)` gap" — refuted; `1/105` rederived (and it is row 6 of the W1 fixture).
- "`n_α ≥ k+1`" — refuted by W2b, rederived.
- "`−D` claimed runtime-attainable" — no inspected artifact claims it; W0 and C32 explicitly deny it.
- "Zero residue ⇒ exact zero" or CRT credit — nowhere used; explicitly disclaimed.
- "Left/naive association could emit `−0`" — impossible in RN (D9); the observed 0-counts are necessary.
- "Z3 receives credit for analytic digamma or harmonic monotonicity" — the boundary strings, sat-preflights, and formal-assurance division-of-labor statement preclude this in the inspected bytes.
- "Vacuous UNSAT" — excluded by the positive `sat` preflight design.

### Open questions (context insufficient — these are *not* passes)
1. Self-test byte contents and totals (110 claim / 170 integration / 29 / 28 / 14 / 12 mutation kills) — digest-pinned, not replayable here.
2. Lean v4 / Z3 source bytes (`32b5d5e1…`, four `.smt2`) — statements unverified beyond checker-declared inventories.
3. Ecosystem projections `ccc5ba5a…` / `63a843b4…` and the API-signature registry digest `30c32e6c…` (`release-scope-1.0.json:2036`) — not recomputable from context.
4. Generator no-write behavior (`a4ef8a87…`) — declared, bytes absent.
5. Whether root `.gitignore` hides any load-bearing path (documented as out-of-snapshot; unverified).
6. `KNOWN_LIMITATIONS.md`, `MIGRATION.md`, `scripts/README.md`, `crates/pid-core/README.md` full contents (pattern excerpt for the crate README matched nothing, which is unremarkable but leaves it uninspected).

**CEGIS note.** Search design used: space = box tuples `(n,k,x,y)` with `n ≤ 20` plus stress shapes; counterexample predicates = `|T| > D`, structural-zero misclassification, nonendpoint zero, `x+y > n+k` under constructed unique-shell point sets; minimizer = lexicographic; conversion = exact `Fraction`; mutation = ±1 coordinate steps. No violation found. **Search failure proves nothing.**

---

## 3. Correspondence matrix

Legend: ✓ = cross-consistent in provided bytes; ✓\* = additionally rederived independently here; D = declared only (bytes absent); — = not applicable.

| Claim | Prose (claim/witness/failures) | Packet JSON | Py checkers (constants) | Rust src/tests | Generated views (METHODS/registry/RS/eco) | Git custody (manifest/policy/phase) |
|---|---|---|---|---|---|---|
| Identity, `(+1,+1,−1,−1)`, range form | ✓\* | ✓\* | ✓ | ✓ (`stats.rs:222–237`) | ✓ | ✓ |
| `−D ≤ T ≤ D` sharp on box only; runtime `−D` denied | ✓\* | ✓\* (`w0`) | ✓ (markers) | — (no runtime claim) | ✓ | — |
| Exclusive/inclusive maps; Lean `k ≤ n` note | ✓ | ✓ | ✓ | ✓\* (call sites) | ✓ | — |
| `x+y ≤ n+k` unpromoted candidate | ✓\* | ✓ (`domains`) | ✓ | — | — | — |
| 8,198 = 6,920 + 1,278; uniqueness | ✓\* | ✓\* | ✓\* (reconstruction) | ✓ (constants) | ✓ | ✓ (fixture digest) |
| 354 = 240 + 114; predicate | ✓\* | ✓\* | ✓\* | ✓ (row-derived) | ✓ | ✓ |
| Corpus-only iff; one-way residue direction | ✓ | ✓ | ✓ | — | ✓ | ✓ (cert digest) |
| Rejected prime, 4 collisions at 8045/8049/8069/8093 | ✓\* (signs too) | ✓\* | ✓\* (indices) | — | ✓ | ✓ |
| 8·ε, 40 ties, first row 7598 | ✓ | ✓\* (index) | ✓\* (index) | ✓ (constants) | ✓ | — |
| Unique exact max row 7673 < 9.761311·ε; 32·ε ceiling | ✓ | ✓\* (index/value) | ✓ (interval, threshold direction sound per D10) | ✓ (comment-scoped) | ✓ | — |
| 6,509/5,934/0; 8.18e-77 @ 7952 | ✓ | ✓\* (index) | ✓ | — | ✓ | — |
| Signed partition 354/0/7844; 150/121 | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| W1 (79, (4,1), 107/210, bits) | ✓\* | ✓\* | ✓ (source markers) | ✓ (both backends) | ✓ | ✓ (CI step) |
| W2 (5,2); mean 71/840; 8 positions | ✓\* | ✓\* | ✓ | ✓\* (mean rederived from committed counts) | ✓ | ✓ |
| W2b all-unique endpoint | ✓\* | ✓\* | ✓ (exact array marker) | ✓\* | ✓ | ✓ |
| Lean 19/14; Z3 4+4/12; premises & shared cuts | ✓ | ✓ | ✓ (inventories) | — | ✓ | D (source bytes absent) |
| Release 15/20; catalog 20/49; 21-node closure | ✓ | — | ✓ (15/20/35 counted) | ✓ (estimator-revision strings) | ✓ | ✓ (projections declared) |
| NO-GO, 13 gates, no final artifacts | ✓ | ✓ | ✓ (default red; final-absence checks) | — | ✓ | ✓ (no decision-v4 paths anywhere) |
| Cross-artifact digests (packet/checker/phase/identity/eco) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (33 blob pins match manifest) |
| Mutation totals / self-test behavior | D | D | D | — | D | D |

---

## 4. Hostile tests / mutations for the claimed blockers

**For F1 (current phase-delta mismatch):**
1. `python3 scripts/check-ksg-phase-isolation.py` on the live worktree → must fail naming either the untracked partition or the anchor-delta mismatch; the failing set must be exactly the 5 `fable5-…settled-hostile…` paths. Any other failing path indicates an additional undeclared delta.
2. Mutation A (falsifier for my mechanism): temporarily add `audit/evidence/fable5-ksg-rev4-settled-hostile-*` to a scratch copy of `.gitignore` and rerun — the checker must *still* fail (it forbids a modified `.gitignore` via protected-blob pinning), demonstrating no ignore-based bypass exists.
3. Mutation B (reseal correctness): extend the policy with the 5 paths + rationale class, regenerate facts via `--emit-current-facts-python`, update `PHASE_PATH_POLICY_SHA256`, rerun normal and `-O`; then run the phase *self-test* both modes — the self-test must still kill a policy-tamper mutant (i.e., resealing must not have weakened the tamper detection).
4. Mutation C (deletion firewall): delete one of the 5 files instead of adding to policy → the precommit run must fail on partition mismatch, never silently pass (deletions_permitted=false pathway).

**For the standing open-gate blocker set (execution obligations):** the required hostile replay is exactly the resume's matrix; the specific adversarial additions I recommend: (a) run `--claim-only` after flipping a single scalar deep in `facts.exact_rational_enclosure.maximum_error_lower_nats` (last digit) with resealed leaf+manifest — must fail on typed-fact equality; (b) rebuild the fixture with rows 8045 and 8049 swapped (order-preserving digest reseal) — reconstruction equality in *both* the enclosure and modular checkers must fail; (c) run the W1 witness with a build where `kd-tree` is forced and counts swapped `(1,4)` — CI witness step must fail with exactly-one-test accounting intact.

---

## 5. Ranked repair / replay plan (no gate weakening, no evidence promotion)

1. **Reseal phase custody for the review artifacts (F1).** Add the 5 receipt paths to the policy as `A` under a receipts-appropriate review class; regenerate the generated phase-facts block; update the policy digest constant; human-review the diff; rerun phase checker + self-test, normal and `-O`. Do **not** add these paths to the claim packet (claim-tree inventory must stay unchanged).
2. **Freeze writers, then run the full settled-byte matrix** exactly as `completion-active-resume.md:78–94` sequences it (scoped Python routes both modes; generator no-write; Lean/Z3 + mutation suites; modular + enclosure + self-tests; Rust debug/release incl. the four 12-test parallel profiles; witness harness; fmt/clippy/rustdoc/feature matrix; review/eco/identity/release gates). Any byte change afterwards restarts this step.
3. **Alternate-index tree + detached checkpoint**; run phase gate in committed-descendant form with `--expected-candidate-tree`/`--checkpoint-commit`, plus self-tests.
4. **Final hostile review on the settled tree**; independently adjudicate; then synthesize the unsigned M1a commit containing exactly the (resealed) policy paths; push; verify remote SHA + CI receipt.
5. **Only then** create M1c artifacts in a re-anchored milestone (regenerating the packet to the immutable-final tuple with 13 content-bound receipts). Fold in the non-blocking hardening (F3 note + 33/37/81 control, F6 key rename, F7 wording, F4 clarifier) at M1c-era regeneration points rather than by editing frozen bytes.

---

## 6. Final disposition (limited to the bytes and domains actually inspected)

* **Bounded arithmetic/corpus core:** I could not falsify any inspected claim. Independent rederivation reproduced the identity, the box-only sharp bound, the runtime-image non-attainability of `−D`, all corpus/endpoint counts, all five frozen extremal/collision row indices, the exact rationals `107/210`, `71/840`, `1/105`, and — via a Wolstenholme-type congruence — the exact structural mechanism of the rejected-prime collisions. The one-way modular direction, the two-metric (8·ε vs 9.761311·ε) separation, and the non-implication firewalls are stated correctly in every inspected artifact. This supports (but does not verify) the packet's "GO on stated exact/helper and finite-corpus domains only," **conditional on** the declared-but-uninspected executions (self-test totals, Lean/Z3 source bytes, projection digests) listed under open questions.
* **Repository/publication integration:** **NO-GO stands**, exactly as the packet says — 13 gates open, and the live snapshot additionally cannot pass its own phase gate until the review-receipt paths are resealed into the policy (F1, fail-closed). No final decision or receipt is smuggled in anywhere I inspected; M1a-before-M1c ordering is encoded in the obligations graph.
* **Nothing here transfers** to KSG estimator consistency, Ehrlich shared-exclusions validity, MGW categorical PID, `I_min`, support, calibration, Rust refinement, or any consumer claim — and nothing in this review constitutes verification of anything.