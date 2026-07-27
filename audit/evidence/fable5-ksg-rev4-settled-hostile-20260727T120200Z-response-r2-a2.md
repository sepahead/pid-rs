# Fable 5 Max adversarial advisory — KSG rev-4 M1a settled-hostile review (checker-hostile formal-methods lens)

**Advisory only. Nothing below verifies anything; every allegation carries its falsifier and reproduction design. Search failure proves nothing.**

---

## 0. Independently reconstructed claim and exact scope

**Object:** For integers `n ≥ 2`, `1 ≤ k < n`, `k ≤ x,y ≤ n` (rectangular helper outer box; Lean variant admits `k = n`), under the *typed, unproved* premise `ψ(m) = H_{m−1} − γ` at the four used arguments, the four-term local quantity with coefficient vector `(+1,+1,−1,−1)` satisfies exactly
`T = H_{k−1} + H_{n−1} − H_{x−1} − H_{y−1} = (H_{n−1} − H_{max(x,y)−1}) − (H_{min(x,y)−1} − H_{k−1})`, with `−D ≤ T ≤ D`, `D = H_{n−1} − H_{k−1}`, sharp **only on that box**, in nats, negative values legitimate, no clamping. Exclusive KSG maps `k−1 ≤ nx,ny < n → x = nx+1`; anchor-inclusive Ehrlich/PID3 counts pass directly. The runtime unique-shell image is *not* asserted to equal the box; `x+y ≤ n+k` remains an explicitly unpromoted follow-up.

**Bounded evidence (finite-corpus only):** frozen schema-2 corpus of 8,198 ordered rows (6,920 exhaustive ≤ n=16; 1,278 stress); 354 structural endpoints (240/114) with corpus-only zero-iff via three selected primes (1000033/1000037/1000081) plus rejected-prime 1000003 negative control (4 collisions = indices 8045/8049/8069/8093); binary64-rounded-reference max `8ε` with 40 ties first at row 7598 `(4096,1,2048,2048)`; exact-rational max unique at row 7673 `(4096,4,2049,2049)`, `< 9.761311ε`, both `< 32ε`; signed-zero partitions 354/0/7844 selected, 150/0 selected-prefix-left, 121/0 naive-prefix-left; W0/W1/W2/W2b behavioral bridges; Lean 19 theorems/14 mutants; Z3 4 obligations (sat-preflight + unsat) /12 mutants.

**Disposition under review:** bounded core GO on stated domains; M1a repository/publication integration NO-GO with exactly 13 open gates; M1c authority only after a pushed M1a commit. Ten-object firewall: no transfer to KSG estimator, Ehrlich ISX, PID2/PID3, MGW SxPID, I_min, quantized, heuristics, wrappers, consumers.

---

## 1. Finding table

| ID | Sev | Object | Location | Proposition | Minimal witness / derivation | Independent reproduction | Shared cuts | What would falsify me |
|---|---|---|---|---|---|---|---|---|
| **F1** | **BLOCKER (M1a process; confirms NO-GO)** | Git phase gate vs. live tree | context `## Git state` (`??` block); `scripts/check-ksg-phase-isolation.py:188` (`EXPECTED_CHANGED_PATHS`), `:354` (`EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES`), `:2297–2305`, `:2355–2364`; `audit/evidence/ksg-rev4-phase-path-policy.json:12–478` | This exact snapshot **cannot pass its own phase gate**: five untracked `fable5-ksg-rev4-settled-hostile-*` files (prompt, runner, context, receipt, oversize-receipt) are outside the 93-path policy, outside the precommit untracked partition (56 expected vs 61 present), and outside the baseline allowlist; policy/facts/policy-digest/checker-constant/manifest resealing cascade is now mandatory before M1a | `git status` shows 5 `??` paths absent from policy entries and from the two generated tuples | `python3 scripts/check-ksg-phase-isolation.py` → nonzero at "candidate changed-path set differs from the exact KSG allowlist" / policy-delta mismatch | policy digest `53e49674…` is pinned both in the checker and manifest (both current) | The five files being ignored by the pinned root `.gitignore` (then they'd not be `??`), or a policy revision already covering them |
| **F2** | Minor (context custody) | Review-context self-binding | context header ("manifest covers every tracked modification and untracked file"); `Diff check: clean` block | The manifest's completeness claim is false for 3 self-referential untracked files (`…-context.md`, `…-receipt.json`, `…-oversize-negative-receipt.json` have no digests); and `Diff check: clean` is ambiguous/misleading given 37 worktree-modified tracked files (`git diff` cannot be empty; only `git diff --cached` can) | Count manifest entries (95) vs `??`+`M` (98) | Recompute manifest coverage against `git status --porcelain` | none | A definition of "diff check" as index-vs-HEAD, plus a follow-up receipt binding the 3 files |
| **F3** | Major hardening (checker model) | Modular-certificate checker JSON semantics | `scripts/check-ksg-harmonic-modular-certificate.py:672–676, 699–703, 718–721, 269–272`; contrast `scripts/check-ksg-harmonic-revision.py:888–931` (`require_strict_json_equal`); same class at `scripts/check-ksg-phase-isolation.py:1478–1482, 1495–1503` | Plain `==` comparison is bool/int coercive (`True == 1`). A **hash-rebased** semantic mutation flipping JSON booleans↔0/1 in the certificate (e.g., `"certificate_revision": 1 → true`, `"include_zero_residues": true → 1`) passes canonical-JSON and all semantic comparisons; only the digest pin (which the rebase protocol legitimately updates) stands between it and green. This contradicts the project's own C22 strict-typing standard, applied only to the claim route | Python: `{"a": True} == {"a": 1}` is `True`; canonical rendering of both forms is self-consistent | Mutation M-F3 below | shielded today by `EXPECTED_CERTIFICATE_SHA256`; phase-policy scalar checks shielded by policy digest | The 28-mutation modular self-test (bytes `7ced696f…`, uninspected) already containing a rebased bool/int type mutation |
| **F4** | Minor (doc staleness risk) | Mutation-total assertions | `AGENTS.md:189–194` ("110 claim mutations", "170 integration mutations") vs `audit/evidence/completion-active-resume.md:53–57` ("mutation totals … must be regenerated and replayed after all edits stop") | AGENTS.md asserts specific totals with no in-context receipt, while the live resume declares totals unsettled. If a settled replay yields different totals, AGENTS.md (blob-pinned at `1b63c772…` in phase constants) forces another reseal cascade | textual contradiction between two pinned authorities | run both self-tests, diff registered totals against AGENTS text | AGENTS digest inside phase `EXPECTED_BOUND_ALLOWED_BLOBS` | A replay receipt showing exactly 110/170 |
| **F5** | Info (context limit) | Formal statement adequacy | `active-packet-v4.json:338–347` (Lean/Z3 paths+digests); Lean/Z3 sources absent from context | The 19 Lean statements, the four `.smt2` obligation bodies, the fixture bytes, and **all seven self-test suites** are digest-bound but uninspectable here. Prose↔formal symbol-by-symbol equivalence cannot be confirmed from this context; it rests on `formal-assurance-v4.md` + digests + the pinned checkers | omission | inspect `audit/formal/lean-ksg-harmonic/v4/…` at `32b5d5e1…`, four `.smt2` at pinned digests, self-tests at pinned digests | analytic premise, human signs/maps (declared) | Providing those bytes; they either match the prose inventory or they don't |
| **F6** | Minor (metric hygiene) | Stored-vs-exact "maximum discrepancy" | `scripts/check-ksg-harmonic-exact-enclosure.py:536` (`comparison_context` 160-digit HALF_EVEN), `:572–581`, `:600–604` | The `8.18e-77 @ row 7952` equality tripwire is computed in a rounding context, not proven exact. For this row (value ≈ −5.56, last-ulp = 1e-79, 818·ulp) the subtraction happens to be exact, but the checker doesn't enforce exactness (`Inexact` trap absent); on a changed corpus the "numeric difference" fact could silently be a rounded value | operand/ulp analysis: both 80-sig-digit decimals near exponent 0 ⇒ difference is an integer multiple of 1e-79 ⇒ exact here | enable `Inexact` trap in `comparison_context`, rerun; or recompute via `Fraction` | shares fixture bytes/row order with all numeric lanes | Trap enabled and no exception raised across corpus |
| **F7** | Minor | Untracked-enumeration semantics | `scripts/check-ksg-phase-isolation.py:990–1007` (`--exclude-from=.gitignore`) | `--exclude-from` and per-directory root `.gitignore` share pattern syntax but anchoring corner cases (leading `/`) are not demonstrably identical; `.gitignore` bytes (pinned `918f4cf1…`) are uninspected here | doc-level semantic gap | fixture test: leading-slash pattern + nested same-name path; compare `git status --porcelain` vs checker enumeration | root .gitignore is a pinned protected blob | An added self-test demonstrating equivalence for the exact pinned patterns |
| **F8** | Minor (robustness) | Worktree permission canon | `scripts/check-ksg-phase-isolation.py:950–955` | Permissions restricted to `{0644,0755}`; a `0664` umask environment yields false-red (fail-closed, but operationally brittle) | code read | `chmod 664` on one deliverable; run checker | none | Intentional-strictness note already reviewed (then it's by design) |
| **F9** | Info | Lean escape lexicon | `scripts/check-lean-ksg-integer-harmonic.py:82–84` | `PROHIBITED_SOURCE` omits `opaque` (Lean 4). Soundness still guarded by the per-theorem `#print axioms` inventory (the real gate), so this is lexicon hygiene only | code read | add `opaque` to regex; confirm baseline still passes | axiom-inventory gate | n/a (hardening) |
| **F10** | Info | Swap-asymmetry assertion is tautological | `crates/pid-core/src/stats.rs:551, 573`; `check-ksg-harmonic-exact-enclosure.py:796–801` | `ksg_local_harmonic_term` reads only `min/max(x,y)`, so `swap_bit_asymmetries == 0` is true by construction; it is a tripwire against a *changed* helper, not evidence | expression is symmetric syntactically | inspect helper | acknowledged in routes-v4 shared-cut wording | already correctly labeled; no action needed |
| **F11** | Result of directed hunt (negative) | Second-order stale digest after assurance-registry correction | `ecosystem-capabilities.json:1823–1848`; `ECOSYSTEM_CAPABILITIES.md:9–20`; `crates/pid-core/identity/software-identity-reference-v1.json:26,35`; `check-ksg-phase-isolation.py:417–451`; `assurance-registry.json:9020`; `README.md:56–59` | Every **inspectable** embedding of the corrected digest chain is current: assurance `5aa34f1d…`, catalog `d2ad2e22…`, release `4fe9e5e4…`, ecosystem `3728ab84…`, base projection `63a843b4…` all mutually consistent. Residual second-order risk is confined to four *uninspected* pinned files: `scripts/check-ecosystem-capabilities.py` (+self-test), `scripts/README.md`, `KNOWN_LIMITATIONS.md` | digest cross-walk (§3 matrix) | `grep -n '5aa34f1d\|3728ab84\|63a843b4\|aa88850c\|4afa8719\|51404d5f' scripts/check-ecosystem-capabilities*.py scripts/README.md KNOWN_LIMITATIONS.md` — any hit on a superseded digest (`aa88850c`, `4afa8719`, `51404d5f`) outside historical sections is the stale find | generated-view regeneration shares one generator | a stale hit from that grep |

---

## 2. Dispositions of attacks

### 2a. Genuine blockers (for M1a progression; none against the bounded core)
- **B1 = F1.** The tree cannot be phase-green as-is; policy/facts/manifest resealing plus full settled replay are prerequisites the packet itself already lists (`git_phase_isolation`, `settled_full_ci`, …). My addition is the concrete demonstration that current phase constants are *already invalidated* by this review's own receipts — i.e., no one may credit any prior phase pass to these bytes.
- **B2 (evidentiary, not new).** No gate receipts exist in this context showing the scoped routes ran green on these exact corrected bytes; all green statements are labeled pre-correction diagnostics. Consistent with NO-GO; must not be upgraded.

### 2b. Hardening (valuable, non-blocking)
F3 (strict-typed JSON comparator + rebased bool/int mutations in modular and phase-policy lanes), F4 (bind mutation totals to a receipt), F6 (Inexact trap / Fraction-exact discrepancy), F7 (.gitignore-semantics self-test), F8 (permission-canon note), F9 (`opaque`), plus: relocate future model-review receipts to a policy-planned or ignored directory to end the reseal churn (without weakening the exact allowlist).

### 2c. Already-closed concerns — independently recomputed here (not trusted from frozen outputs)
- **W0**: `(2,1)`: `(1,1)→+1=+D`, `(2,2)→−1=−D`, mixed→0. Box-sharp; runtime `−D` denied — and my set derivation *confirms* runtime `x+y ≤ n+k` for KSG-exclusive, ISX-inclusive, and PID3 branches (unique shell ⇒ `|A∩B| = k−1` exactly ⇒ `x+y ≤ n+k`; `−D` needs `2n ≤ n+k`, impossible). Claim's refusal to promote it is correct.
- **C30**: `(8,2,3,5)` ⇒ `T = 1 + 363/140 − 3/2 − 25/12 = 1/105 < 1/7`. Recomputed exactly.
- **W1**: full recomputation of query 5 from raw rows: joint radius 79, unique shell (1 interior, 1 boundary), ordered `(nx,ny)=(4,1)`, `T = H_7−H_4 = 107/210`. Matches production test and helper map.
- **W2**: all eight inclusive local terms recomputed (`109/420, −5/14, 83/140, −4/21, −31/420, 107/210, 1/105, −31/420`); mean = **71/840** exactly; bit gap `0x…a3e` vs `0x…a36` = 8 ordered positions, correctly *not* called ULPs.
- **W2b**: all three rows traced through the compiled predicate semantics (strict `≤ nextdown(radius)` counts): `(radius,n_α,n_t,T) = (1,1,3,+0),(1,1,3,+0),(2,1,3,+0)`. Refutes `n_α ≥ k+1`; my derivation also confirms `n_α ≥ k`, `n_t ≥ k` hold at runtime (interior-shell argument), so the helper domain is respected by all five call sites.
- **Corpus structure**: exhaustive endpoints `2·Σ_{n=2}^{16}(n−1)=240`; stress `(n,k)` pairs 6+7+8+9+9+9+9=57 ⇒ 114; stress row totals 129+154+179+204·4 = 1,278. **Row indices independently derived from the generator grammar**: 7598 = `(4096,1,2048,2048)`, 7673 = `(4096,4,2049,2049)`, 7952 = `(65536,64,32799,32799)`, and collision indices 8045/8049/8069/8093 land exactly on `(10^6,3,2,3)`, `(10^6,3,3,2)`, `(10^6,4,3,3)`, `(10^6,4,999999,999999)`. All match every document.
- **Collision algebra**: the four rejected-prime rows reduce to `±(H_999999 − H_3)`; "four collisions = one divisibility event" is exactly right; converse denial and non-CRT wording present everywhere.
- **Exact max value**: `H_3 + H_4095 − 2H_2049 ≈ −5.67694` matches `-0x1.6b52fe6a01407p+2`; `9.761311ε ≈ 2.16745e−15 >` the enclosed upper `2.1674464…e−15 > 8ε = 1.7764e−15` — the two metrics are coherent and correctly separated.
- **40-tie inventory** in the erratum counts to exactly 40 and every tuple lies on the reconstructed stress grid.
- **26→28 modular count correction** propagated everywhere inspected (packet, claim, ledger C31, impl-v4, registry, checker).
- **Formal inventories**: 19 = 14(rev2)+5; Lean mutants 14 = 9(rev2, listed in formal-seams-v2)+5; Z3 mutants 12 = 8+4; obligations 4 with sat-preflight anti-vacuity (correct pattern: inconsistent premises would fail the positive `sat`).
- **13 open gates** enumerated identically in packet, checker constant, obligations, disposition, ledger C24/C27.
- **Enclosure checker soundness**: directed prefixes, floor/ceiling subtraction directions, monotone HALF_EVEN co-rounding argument, interval error branches, strict downward-rounded thresholds, and uniqueness-by-separation are all mathematically correct as written.
- **Phase-envelope logic**: first-parent walk with exact single-parent+tree pins closes the monotone-history loophole; replace-refs/grafts/alternates/attributes/config/symlink/hardlink/case-collision attacks are each addressed; the two self-unhashed scripts are honestly declared and externally bindable.

### 2d. Rejected / ill-posed attacks
- "`−D` runtime attainability contradiction" — explicitly denied everywhere; my derivation confirms impossibility. 
- "CRT or converse smuggled into prose" — absent; the certificate encodes the one-way direction as a typed field.
- "8ε conflated with exact-rational error" — the separation is enforced in prose, packet fields, Rust comments, and both checkers.
- "shared-config family over-bumped" — deliberate negative identity control (`ksg-chebyshev-config-v1` retained), consistently explained in registry F013.
- "kd-tree/brute divergence hides count-domain violations" — parity tests pin bit-identical terms and identical structured shell errors in both backends.
- "swap-asymmetry as evidence" — already labeled tripwire (F10).
- "bool/int laxity in catalog/release routes" — real class, but *shielded there* by `projection_sha256` (json.dumps distinguishes `true` vs `1`); only the modular/phase scalar spots (F3) lack a semantic backstop.
- "`k=n` Lean domain licenses runtime `k=n`" — claim-v4 explicitly forbids that inference.

### 2e. Open questions (exactly what is missing)
1. Bytes of Lean v4 source, four `.smt2` files, fixture JSON, all self-tests, `KNOWN_LIMITATIONS.md`, `MIGRATION.md`, `scripts/README.md`, eco checker — needed to close F5/F11 and to confirm 29/28/14/12/110/170 mutation inventories and README marker presence.
2. Meaning of context `Diff check: clean` (index-vs-HEAD?).
3. `EXPECTED_BASELINE_PATH_COUNT/PROTECTED_PATH_COUNT = 437/402` (recomputed live by the checker; unverifiable statically here).
4. Selected/rejected residue-vector digests (require machine replay; my hand-check covers only the collision algebra).
5. Whether the modular/phase self-tests already contain a rebased JSON-type mutation (would downgrade F3 to closed).

---

## 3. Correspondence matrix (✓ = byte/value-consistent across all inspected carriers; ◐ = consistent where inspectable, some carrier uninspected; ✗ = mismatch)

| Fact | Prose (claim/witness/ledger) | Packet JSON | Checker consts | Rust src/tests | Generated views (METHODS/RELEASE md/registry/dispositions/README) | Git/phase custody |
|---|---|---|---|---|---|---|
| Exact term, `(+1,+1,−1,−1)`, `−D≤T≤D` box-sharp only | ✓ | ✓ | ✓ | ✓ (helper + comments) | ✓ | ✓ |
| Domains/maps; box ≠ runtime image; `x+y≤n+k` unpromoted | ✓ | ✓ (`runtime_shell_image_equals_outer_box:false`) | ✓ (README markers enforced) | ✓ | ✓ | ✓ |
| 8,198 = 6,920+1,278; endpoints 354 = 240+114 row-derived | ✓ | ✓ | ✓ | ✓ (row-derived in stats.rs test) | ✓ | ✓ |
| 8ε / 40 ties / first row 7598 `(4096,1,2048,2048)` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Exact max unique row 7673, `<9.761311ε`, `<32ε`, hex value | ✓ | ✓ | ✓ | (Python lane) ✓ | ✓ | ✓ |
| 6,509/5,934/0 mismatches; 8.18e-77 @7952 | ✓ | ✓ | ✓ | n/a | ✓ | ✓ (but see F6) |
| Signed zeros 354/0/7844; 150 vs 121 prefix-named | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| W1 (79,(4,1),107/210,bits) | ✓ | ✓ | ✓ (source markers) | ✓ | ✓ | ✓ |
| W2 (5,2 / 71/840 / 8 positions, no ULP) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| W2b three-row array | ✓ | ✓ | ✓ (exact array marker) | ✓ | ✓ | ✓ |
| Modular: primes, one-way direction, non-CRT, 28 mutants, collisions | ✓ | ✓ | ✓ | n/a | ✓ | ✓ (digests ◐ — replay needed) |
| Lean 19/14, typed premise, axioms `{propext,choice,Quot.sound}` | ✓ | ✓ | ✓ | n/a | ✓ | ◐ (source bytes absent — F5) |
| Z3 4/12, sat-preflight, uninterpreted harmonic | ✓ | ✓ | ✓ | n/a | ✓ | ◐ (smt2 bytes absent — F5) |
| Ten-object firewall; no MGW/estimator transfer | ✓ | ✓ | ✓ (forbidden markers) | ✓ (doc boundaries) | ✓ | ✓ |
| Lifecycle NO-GO, 13 gates, no v4 decision/matrix | ✓ | ✓ | ✓ (default route red) | n/a | ✓ | ✓ |
| Release 15/20; catalog 20/49 (21-closure minus shared-config) | ✓ | n/a | ✓ | n/a | ✓ | ✓ |
| Identity two forensic digests current | n/a | n/a | ✓ (phase firewall recompute) | n/a | ✓ | ✓ |
| Anchor `a9aa60c9`/tree `88a8dd7a`; 93-path policy = 37M+56A | ✓ (resume) | n/a | ✓ | n/a | n/a | **✗ vs live tree (F1: +5 receipts)** |
| Assurance-digest correction chain (2nd-order hunt) | ✓ | ✓ | ✓ | n/a | ✓ | ◐ (four uninspected files — F11 grep) |

No inspected carrier disagrees with another on any scientific value. The single ✗ is F1 (Git-visible tree vs phase constants), which is fail-closed and consistent with NO-GO.

---

## 4. Hostile tests / mutations for blockers (and key hardening)

**B1/F1 — phase-gate invalidation**
1. *Confirm red now:* `python3 scripts/check-ksg-phase-isolation.py` and `-O` on this tree ⇒ must exit nonzero citing allowlist/policy-delta or untracked-partition mismatch. If it exits 0, my finding is false **and** the checker has a hole (either outcome is decisive).
2. *Fail-closed control:* add one benign untracked file `audit/evidence/zz-probe.txt` ⇒ still red with the same class of message.
3. *Resolution probe:* relocate the five receipts outside the candidate (or regenerate policy to include them + reseal `PHASE_PATH_POLICY_SHA256` + `--emit-current-facts-python` block + manifest), rerun both modes plus the phase self-test; only exact-match green counts.

**F3 — coercive JSON equality (hash-rebased mutation, per the project's own C-series protocol)**
1. In the certificate flip `"certificate_revision": 1` → `true` and `"include_zero_residues": true` → `1`; regenerate sidecar; rebase `EXPECTED_CERTIFICATE_SHA256` only. Predicted: checker **passes** (defect). 
2. Fix: introduce `require_strict_json_equal` (copy from revision checker) for `expected_static_certificate_parts`, selected/rejected records, and fixture scalar fields; rerun mutation ⇒ must fail with a type-path message; register both mutants (normal and `-O`) in the 28→30 suite.
3. Same-class probe on `ksg-rev4-phase-path-policy.json` (`"schema_revision": 1 → true`, digest rebased in checker): predicted pass today; must fail after strict typing.

**F6 — rounded tripwire:** set `comparison_context.traps[decimal.Inexact] = True`; full-corpus run must not raise; if it raises anywhere, replace with `Fraction(stored) − Fraction(rounded)` exact comparison.

**F4 — totals:** run `check-ksg-harmonic-revision-self-test.py [--claim-only]` normal/`-O`; parse registered-mutation totals; assert equality with AGENTS.md text or amend AGENTS before the phase reseal (AGENTS blob is pinned).

---

## 5. Ranked repair / replay plan (no gate weakened, no evidence overstated)

1. **Receipt quarantine + phase reseal (F1).** Decide a durable location/policy row for model-review receipts; regenerate the A/M policy, human-review it (policy forbids mechanical resealing — honor that), update `PHASE_PATH_POLICY_SHA256`, regenerate the generated-facts block, re-emit the manifest. Do **not** loosen the allowlist or add ignore rules that could hide future paths.
2. **Strict-typing propagation (F3) + two new rebased mutations** in the modular suite (28→30) and one in the phase self-test; update packet `mutation_count` and every prose "28/28" accordingly (new revision-consistent edit, not a rewrite of frozen bytes).
3. **Reconcile AGENTS totals (F4)** against a fresh self-test run *before* step 1's reseal (AGENTS digest feeds phase constants).
4. **Micro-hardening batch:** F6 (Inexact trap/Fraction), F7 self-test, F9 lexicon; optional F8 note.
5. **Targeted stale-digest grep (F11)** over the four uninspected files for `aa88850c|4afa8719|51404d5f|ae4645c3` outside explicitly historical sections; fix any hit and reseal.
6. **Settled-byte replay** exactly as the packet prescribes: all seven scoped routes + self-tests normal/`-O`; generator no-write; Lean (19/14) and Z3 (4+4/12) both modes; W1/W2/W2b debug+release; 12-test parity ×4 profiles; fmt/clippy/rustdoc/feature matrix; ecosystem/review/identity/catalog/release gates; then phase normal/`-O` with `--expected-candidate-tree/--checkpoint-commit`; capture receipts.
7. **Final hostile review on the resealed bytes**, then M1a unsigned commit + push + receipt; only then M1c artifacts (D1 ordering preserved).

**CEGIS framing used:** search space = single-token JSON scalar type flips, one-line lifecycle/status flips, single-path policy insertions, single-digit residue perturbations; oracle = each checker's exit status after the protocol-permitted single-hash rebase; minimizer = one file/one token; accepted mutant ⇒ exact checker-adequacy counterexample. My static search found exactly the F3 acceptance class; **failure to find more proves nothing.**

---

## 6. Final disposition (limited to the bytes and domains actually inspected)

- **Bounded arithmetic core:** no counterexample found. Independent recomputation of W0/W1/W2/W2b, `1/105 < 1/7`, endpoint splits 240/114, the 40-tie inventory, all four claimed row indices, the collision algebra, the `−5.6769…` maximizer value, and the `8ε < 9.761311ε < 32ε` ordering is **consistent** with the packet on its stated exact/helper and finite-corpus domains. The declared "GO on stated domains" is *not falsified here*; it is also *not certified here* — Lean/Z3/fixture/self-test bytes are outside this context (F5), and residue digests require machine replay.
- **M1a integration:** NO-GO stands and is **independently reinforced**: this snapshot cannot pass its own phase gate (F1), and no settled-replay receipts for the corrected bytes exist in-context. Any claim of phase or full-gate green on these exact bytes would be false.
- **Second-order stale-digest hunt:** negative on all inspectable carriers; residual risk confined to four named uninspected files with an exact grep to close it (F11).
- **No stronger statement is licensed:** nothing here bears on KSG estimator consistency, Ehrlich ISX, PID2/PID3, MGW SxPID, `I_min`, support, calibration, portability, or consumers.

This document is adversarial advisory input only; it verifies nothing, including itself.