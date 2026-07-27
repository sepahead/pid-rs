# Fable 5 Max adversarial advisory — binary64 / compiled-refinement lens

**Standing disclaimer:** this output is advisory attack input. Nothing below verifies, certifies, or gates anything. Where I say "verified" I mean "I independently re-derived it from first principles inside this review and found agreement"; that is corroboration, not proof of the repository's execution behavior.

---

## 0. Independently reconstructed claim and exact scope

The claim under my lens, as I reconstruct it from `stats.rs`, `ksg.rs`, `isx.rs`, `pid3.rs`, the tests, the two Python numerical checkers, and `active-packet-v4.json`:

1. **Production expression.** For eligible `(+1,+1,−1,−1)` four-term digamma combinations at positive-integer arguments, production Rust evaluates `psi(k)+psi(n)−psi(x)−psi(y)` as `(table[n] − table[max(x,y)]) − (table[min(x,y)] − table[k])`, where `table[m] = H_(m−1)` is a running Neumaier-compensated prefix snapshot (`stats.rs:181-237`). Exclusive KSG callers pass `nx+1, ny+1` (4 call sites in `ksg.rs`); anchor-inclusive Ehrlich/PID3 callers pass `(n_alpha, n_t)` directly (1 site each in `isx.rs`, `pid3.rs`); the heuristic sketch stays on general digamma.
2. **Finite-corpus binary64 facts** on the frozen 8,198-row schema-2 corpus: rounded-reference max exactly `8ε` with 40 ties, first at zero-based row 7598 = (4096,1,2048,2048); unique exact-rational max at row 7673 = (4096,4,2049,2049), enclosed strictly below `9.761311ε`; ceiling `32ε`; endpoint partition 354/0/0; full-corpus partition 354/0/7844; selected-prefix ordinary-left 150/354, naive-prefix 121/354, both with zero `−0`.
3. **Behavioral bridges** W0/W1/W2/W2b with exact rational targets `107/210`, `71/840`, pinned bit patterns, and an 8-ordered-position public/exact separation; brute/kd-tree bit parity; serial/parallel bit identity pinned by 13 KSG-only u64 constants over 12 tests.
4. Scope limited to local integer arithmetic on stated domains; no ULP, portability, estimator, support, or PID transfer; integration NO-GO with 13 open gates.

I inspected only the bytes in the provided context. `nn.rs` (`strict_radius`, `validate_kth_neighbor_shell`), `kdtree.rs`, `par.rs`, the revision self-test (90 KB), the Lean sources, and the fixture/certificate bodies were **not** provided; conclusions touching them are marked accordingly.

---

## 1. Finding table

| ID | Severity | Object | Location | Proposition | Minimal witness / derivation | Independent reproduction | Shared cuts | What would falsify my allegation |
|---|---|---|---|---|---|---|---|---|
| B64-001 | MEDIUM (claim/evidence wording; arithmetic unaffected) | Correction ledger C23 vs compiled test | `claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md:127-137` vs `crates/pid-core/src/stats.rs:493-612` | C23 states the **full-corpus** selected partition `+0/−0/nonzero = 354/0/7844` is derived "in both Python and compiled Rust". The compiled corpus test derives the endpoint triple, 150/0, 121/0, swap, max/tie facts — but has **no full-corpus zero/nonzero counters**. The fact is only *transitively* enforced in Rust: any non-endpoint computed zero forces error ≥ min nonzero \|T\| (≥ `1/999999` at row (1e6,1,0,999998), ≈ 4.5×10⁹ε ≫ 32ε), tripping the `==8ε`/`≤32ε` asserts. Obligations N2 correctly marks compiled replay open; the ledger sentence overstates shipped bytes. | Grep `stats.rs` test for `selected_full` counters: absent. Compare with `check-ksg-harmonic-revision.py:2164-2170` and enclosure `:836-840`, which assert the triple directly. | `grep -n "selected_full" crates/pid-core/src/stats.rs` (empty); run both Python routes (assert present). | Ledger prose and Rust test share the reviewed-prose custody envelope; correcting either requires reseal. | A compiled assertion of the 354/0/7844 triple existing in a file I was not shown, or a reading of C23 restricted to the two prefix counts. |
| B64-002 | MEDIUM (context/custody integrity) | Review-context manifest completeness | Context "Git state" block vs "Complete changed-path byte manifest" header | The context asserts "The manifest covers every tracked modification and untracked file," yet `git status` lists five untracked `fable5-...-settled-hostile-...` files while the manifest contains only `-prompt.md` and `-runner.mjs`. Three untracked inputs (`-context.md`, `-receipt.json`, `-oversize-negative-receipt.json`) are **unpinned**, and the receipt's pre-call existence is a chronology anomaly. The snapshot's own completeness statement is false on its face. | Count: 61 `??` paths vs 59 manifest untracked-class entries; the delta is exactly `{context.md, receipt.json, oversize-negative-receipt.json}`. | `git status --porcelain \| grep '^??'` vs manifest path list diff. | Context generator is the same authority producing both blocks. | Evidence that the three files were created between manifest emission and status capture **and** the completeness sentence is scoped to manifest time — which would still be a wording defect. |
| B64-003 | LOW (fail-closed as designed; must not be misread) | Phase gate on this exact snapshot | `scripts/check-ksg-phase-isolation.py:188-314, 354-411, 1589-1592, 2356-2364` | The generated `EXPECTED_CHANGED_PATHS` / `EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES` exclude the five settled-hostile evidence files; on this exact tree the phase checker must exit nonzero at the untracked-partition and policy-delta equalities. No packet document claims it passes (P1/R-PHASE open), so this is consistent — but any narrative citing a green phase run on these bytes would be false, and admitting the new evidence requires a manually reviewed policy revision 2 plus fact regeneration (mechanical resealing forbidden). | 61 untracked ≠ 56 policy `A` entries; policy delta ≠ actual delta by exactly 5 paths. | `python3 scripts/check-ksg-phase-isolation.py` → expect `ERROR: ... precommit untracked-deliverable partition changed` (or policy-delta mismatch). | Policy digest is byte-pinned inside the checker (`PHASE_PATH_POLICY_SHA256`). | The checker exiting 0 on this tree. |
| B64-004 | LOW | Error-message label drift | `scripts/check-ksg-harmonic-revision.py:2052-2054` | Failure message for generator custody says "reviewed **revision-3** digest"; the same digest is elsewhere labeled the reviewed schema-2 revision-4 digest (`stats.rs:472`). Digest value identical; label stale. If ever triggered it mislabels the revision in evidence. | String inspection. | grep. | Byte-pinned checker; fix costs a reseal. | The string being intentional historical labeling documented somewhere. |
| B64-005 | INFO / open | Unbound mutation-count comments | `AGENTS.md:191-194`; superseded resume text | AGENTS comments assert "110 claim mutations" / "170 integration mutations" for the revision self-test; the packet deliberately binds no such totals; earlier narrative said 49/161. The counts are free-floating relative to any pinned fact and unverifiable from provided bytes (self-test not included). | Text comparison. | Run `check-ksg-harmonic-revision-self-test.py --claim-only` and count. | AGENTS is in the changed-projection digest; edits reseal. | The self-test source demonstrating exactly 110/170 registered mutations. |
| B64-006 | INFO | Release-profile corpus coverage | `.github/workflows/ci.yml` (ksg job), `justfile` | The provided CI excerpt runs W1/W2/W2b witnesses and the parallel-bit suite in debug **and** release, but the 8,198-row `stats.rs` corpus test appears only under the generic workspace `cargo test` (debug) in the shown lines; release-profile corpus replay rests on `just test-release` (not shown). Consistent with the open compiled-replay gate; record explicitly. | CI text. | Run `cargo test --release -p pid-core ksg_integer_harmonic_range_matches_decimal_oracle`. | — | A CI job in unshown bytes running the corpus test in release. |
| B64-007 | INFO (verified, note tightness) | `9.761311ε` strict threshold | `active-packet-v4.json:73-74`; enclosure `:100, 883-906` | I recomputed U/ε from the pinned upper string: U×2⁵² ≈ **9.7613109**, i.e. the strict bound holds by margin ≈ 1.0×10⁻⁷ ε ≈ 2.2×10⁻²³ nats — exactly `ceil(ratio, 6dp)`. Sound (downward-rounded threshold preserves it) but knife-edge; the measured ratio should be recorded beside the threshold so nobody "rounds" the constant later. | Long-division of pinned decimal strings (shown in §4). | Python: `Decimal(U)/Decimal(2)**-52`. | Both operands are pinned strings. | An arithmetic error in my division. |
| B64-008 | INFO | `i as u32` index casts | `ksg.rs:2282-2300` | kd-tree exclusion ids truncate for `n > u32::MAX`; unreachable under any realistic budget and outside claimed domains, but the bound is implicit, not asserted. | Code inspection. | — | — | An explicit `n ≤ u32::MAX` guard elsewhere. |

No finding above contradicts a bounded-core arithmetic fact. I found **no numerical, association, signed-zero, count-map, or backend-parity counterexample**.

---

## 2. Dispositions

### 2a. Genuine blockers (for the stated NO-GO closure path, not for the bounded core)
- **B64-001** — C23's "in both Python and compiled Rust" must be made true (add compiled full-corpus partition counters — preferred, it strengthens) or the ledger corrected via a new entry; either path is a reseal event because the prose bytes are pinned in the packet and `EXPECTED_REVIEWED_V4_PROSE_SHA256`.
- **B64-002** — the review context's completeness statement is false; the three unmanifested files must be pinned (receipt via the follow-up-receipt pattern) before this snapshot is cited as the hostile-review basis.

### 2b. Valuable non-blocking hardening
1. Promote the endpoint `+0` observation to a stated structural property: at endpoints the selected expression degenerates to `(t[n]−t[n]) − (t[k]−t[k]) = (+0)−(+0) = +0` under RN for any finite table — independent of table contents. Likewise `−0` is impossible for the selected route given a nonnegative table (differences of equal finite values yield `+0`; operands are nonnegative). This converts two "tripwires" into tiny theorems.
2. Add a compiled assertion `min nonzero |T| ≥ 1/(n_max−1) ≫ 32ε` (or simply the full-corpus triple), closing B64-001 constructively.
3. Record the measured ratio 9.7613109 next to the 9.761311 constant (B64-007).
4. Bind the final claim/integration mutation totals into the packet at settled replay (B64-005).
5. Fix the "revision-3" message label in the same reseal window (B64-004).
6. Document the implicit `n ≤ u32::MAX` bound (B64-008).

### 2c. Already-closed concerns I re-attacked and found genuinely closed
- **C20 metric conflation** — the two comparators are now distinct in code (`stats.rs:265-270` comment + separate enclosure route) and in every generated view I checked; the `assert_ne!` in `tests/isx.rs:65-70` blocks re-conflation of W2's two bit patterns.
- **C14 prefix naming** — both 150 (Neumaier prefix) and 121 (separately built naive prefix) are computed side-by-side in Rust and Python with byte-identical loop transcriptions (`stats.rs:487-491,536-549` vs revision checker `:1712-1745`).
- **Preclosure findings 7/8** — endpoint split 240/114 is row-derived in both consumers; the ordered W1 diagnostic is production-private and pinned in both backends (`ksg.rs:2863-2880`).
- **C30/C31/C22/C29** — `1/105 < 1/7` re-derived exactly (below); `MAXIMUM_RECIPROCAL_SUMMAND_INDEX = 999999` naming consistent; strict JSON typing and `st_nlink == 1` present in the checker.

### 2d. Rejected / ill-posed attacks (with the reason each fails)
| Attack | Why rejected |
|---|---|
| "Endpoint `+0` counts could hide a `−0`" | Structurally impossible for the selected association (x−x = +0; (+0)−(+0) = +0). |
| "`select_nth_unstable` permutation corrupts marginal counts" | Counting is order-independent; counts are integers. |
| "Brute vs kd-tree could disagree on `eps_raw` under ties" | Unique-shell validation (interior = k−1, boundary = 1, per the error-signature tests) makes the kth joint distance unique; `max` is exact in binary64, so joint distances are bit-identical across paths, including xblocks (Chebyshev only, enforced). |
| "Tie counter inflated by zero-error endpoint rows" | Both implementations reset ties on each new maximum; final max is 8ε > 0, so only true 8ε rows count. |
| "Double rounding through the 80-digit exact-rounded strings poisons the bound" | The load-bearing exact bound uses directed intervals against the exact rational, not the rounded strings; the string comparison is a separate, honestly-scoped observation. |
| "Rust/Python decimal→binary64 parse divergence" | Both are correctly rounded conversions; the comparator is therefore the same function of the same pinned bytes. |
| "W2b violates the helper precondition k ≤ x" | For validated shells, anchor-inclusive counts satisfy `n_alpha, n_t ≥ k` (the k−1 joint-interior points lie inside both balls, plus the anchor); W2b attains equality, not violation. |
| "`8ε` exact equality is numerically meaningless" | Differences of same-binade binary64 values are ulp multiples; at \|T\| ≈ 7.51 (row 7598) 8ε = 2 ulp exactly; equality is well-posed. |
| "Exact max 9.76ε contradicts rounded-reference max 8ε" | They may differ by ≤ ½ conversion-ulp + stored-vs-exact decimal gap ≤ 2ε; 9.76 − 8 = 1.76ε fits. |
| "The x+y ≤ n+k set argument was transferred across routes without checking each predicate" | I checked each production predicate (§4.6): in all four (KSG brute/tree, xblocks, ISX, PID3) the joint distance is the max of exactly the counted coordinates, so A∩B equals the validated interior (= k−1) exactly, giving x+y = \|A∪B\|+k+1 ≤ n+k in every case. Correctly still **unpromoted**. |
| "Runtime wording claims −D attainable" | It does not; W0 is typed `rectangular_arithmetic_helper` with `runtime_unique_shell_attainability_claim: false`; I additionally confirmed +D *is* runtime-attainable (exact diagonal neighbor) and no document claims otherwise, so no overclaim either way. |

### 2e. Open questions (context insufficient)
1. `strict_radius` and `validate_kth_neighbor_shell` bodies (nn.rs absent). My hand-recomputation of W1 (`ny = 1` requires strict `<` at 79) and W2b (`n_alpha = 1` requires `1 > nextDown(1)`) *behaviorally corroborates* next-down semantics, but I could not read the code.
2. The corpus-scale scans (8ε/40/7598 set, 150/121, 7844 nonzeros, residue digests) — arithmetic structure verified, values not hand-replayable. Repro: `cargo test -p pid-core ksg_integer_harmonic_range_matches_decimal_oracle`; `python3 scripts/check-ksg-harmonic-revision.py --binary64-only|--enclosure-only`; `python3 scripts/check-ksg-harmonic-modular-certificate.py` (all also with `-O`).
3. B64-005/006 above.
4. `map_index_ordered` / `with_thread_budget` internals (par.rs absent) — bit-identity rests on the 12-test suite plus thread-budget report equality, which the provided bytes do contain.

---

## 3. Correspondence matrix

✓ = independently re-derived here; C = consistent across artifacts, not independently recomputed; ⊘ = intentionally out of scope; ? = unverifiable from provided bytes.

| Claim | Prose (claim/witnesses v4) | Packet JSON | Exact algebra (this review) | Lean | Z3 | Modular cert | Rust helper (`stats.rs`) | Production callers | Python routes | Generated views (catalog/scope/registry/METHODS) | Git custody (phase/manifest) |
|---|---|---|---|---|---|---|---|---|---|---|
| Identity `T = H_(k−1)+H_(n−1)−H_(x−1)−H_(y−1)`, range form | ✓ | ✓ | ✓ | C | C | C | ✓ (`:222-237`) | ✓ | ✓ | C | C |
| Exclusive `nx+1,ny+1` (4 sites), inclusive direct (1+1) | ✓ | ✓ | ✓ | C | C | ⊘ | — | ✓ (`ksg.rs:2302,2382,2731,2811`; `isx.rs:1128`; `pid3.rs:1297`) | ✓ (source route markers) | C | C |
| Corpus counts 6920/1278/240/114/354/7844; max index 999999 | ✓ | ✓ | ✓ (recounted from enumeration) | ⊘ | ⊘ | ✓ (structure) | ✓ (row-derived) | ⊘ | ✓ | C | C |
| Row indices 7598/7673/7952/8045/8049/8069/8093 ↔ tuples | ✓ | ✓ | ✓ (positional re-derivation) | ⊘ | ⊘ | ✓ | C | ⊘ | C | C | — |
| 8ε / 40 ties / first (4096,1,2048,2048) | ✓ | ✓ | plausibility + tie-list count/membership ✓; scan ? | ⊘ | ⊘ | ⊘ | C (asserted) | ⊘ | C (asserted) | C | — |
| Exact max < 9.761311ε, unique, `-0x1.6b52fe6a01407p+2` | ✓ | ✓ | ratio ✓ (9.7613109); hex↔decimal ✓; interval directions ✓ | ⊘ | ⊘ | ⊘ | ⊘ | ⊘ | ✓ (logic) / C (values) | C | — |
| 6509/5934/0 stored-vs-exact facts | ✓ | ✓ | metric well-posedness ✓; counts ? | ⊘ | ⊘ | ⊘ | ⊘ | ⊘ | C | C | — |
| Endpoint 354/+0 structural; −0 impossible | ✓ | ✓ | ✓ (proved for expression) | ⊘ | ⊘ | ✓ (exact zero) | ✓ | C | ✓ | C | — |
| 150/121 prefix discriminator | ✓ | ✓ | transcription equality ✓; values ? | ⊘ | ⊘ | ⊘ | ✓ (asserted) | ⊘ | ✓ (asserted) | C | — |
| W1 radius 79, counts (4,1), bits = RN(107/210) | ✓ | ✓ | ✓ (distances, counts, 107/210, bit pattern all re-derived) | C (index maps) | C | ⊘ | — | ✓ (both backends) | C | C | — |
| W2 mean 71/840; public bits 8 positions off RN | ✓ | ✓ | ✓ (exact mean and both bit patterns re-derived; gap = 8) | ⊘ | ⊘ | ⊘ | — | ✓ | C | C | — |
| W2b all-unique (k,n) endpoint, +0 mean | ✓ | ✓ | ✓ (full recomputation incl. fl(0.4)/fl(0.8)) | ⊘ | ⊘ | ⊘ | — | ✓ | C | C | — |
| `x+y ≤ n+k` candidate (unpromoted) | ✓ | ✓ | ✓ per-predicate (all 4 routes) | ⊘ | ⊘ | ⊘ | — | ✓ | ⊘ | ⊘ | — |
| Modular one-way implication; primes > 999999; MR determinism; batch inverse | ✓ | ✓ | ✓ | ⊘ | ⊘ | ✓ (code) | ⊘ | ⊘ | ✓ | C | C |
| 13 serial constants / 12 parallel tests | ✓ | ⊘ | count ✓ | ⊘ | ⊘ | ⊘ | — | ✓ (file) | — | C | ✓ (pins match file) |
| 15/20/35 release families; estimator-revision strings in code | ✓ | ⊘ | count ✓ | ⊘ | ⊘ | ⊘ | — | ✓ (`ksg.rs:968`, `isx.rs:648`) | ✓ (checker) | ✓ (JSON↔MD spot-checked) | ✓ |
| Digest web (packet ↔ manifest ↔ phase pins ↔ identity) | C | ✓ | — | C | C | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ except **B64-002/003** |

---

## 4. Selected independent derivations (evidence for the ✓ cells)

1. **Counts.** Exhaustive = Σₙ₌₂..₁₆ (Σₘ₌₂..ₙ m²) = Σ S(n) − 15 = 6935 − 15 = **6920**. Endpoints = 2·Σ(n−1) = **240**. Stress per-n: 129+154+179+204·4 = **1278**; endpoints 12+14+16+18·4 = **114**. Totals 8198/354/7844; max summand index 999999.
2. **Row indices.** n=4096 block starts 7586; k=1 count-values {0,1,2048,4094,4095} ⇒ offset 12 ⇒ **7598 = (4096,1,2048,2048)**; k=4 block 7661, values {3,4,2049,4094,4095} ⇒ **7673 = (4096,4,2049,2049)**; n=65536 k=64 block 7940, values {63,64,32799,65534,65535} ⇒ **7952 = (65536,64,32799,32799)**; n=10⁶ k=3 block 8044 ⇒ 8045=(2,3), 8049=(3,2); k=4 block 8069 ⇒ 8069=(3,3), 8093=(999999,999999). All match pinned tuples.
3. **W1.** From raw coordinates, point 5 joint distances {33,79,129,151,156,182,197} ⇒ radius 79, interior 1, boundary 1; strict marginals give (nx,ny)=(4,1). 107/210 = ½ + 1/105; RN mantissa = ⌊2⁵³/105⌉ = 85782850045152 = 0x04e04e04e04e0 ⇒ **0x3fe04e04e04e04e0**. The C30 row (8,2,3,5) then gives T = 107/210 − ½ = **1/105 < 1/7** exactly.
4. **W2.** Eight exact terms sum to 284/420 = 71/105; mean **71/840**. RN(71/840): exponent 0x3fb, mantissa ⌈37·2⁵²/105⌉ (remainder 67/105 > ½) = 1586982725835318 = 0x5a35a35a35a36; public 0x...3e differs by mantissa **+8**, same binade ⇒ 8 ordered positions.
5. **W2b.** dt uses fl(0.4), fl(0.8) with fl(0.8) = 2·fl(0.4) exactly ⇒ dt gaps exact; joints {1,3},{1,2},{2,3}; each row (n_alpha,n_t) = (1,3) = (k,n); helper (1,3,1,3) ⇒ structural endpoint ⇒ +0; mean of three +0 through Neumaier = +0.
6. **Set bound per predicate.** In each route, `joint = max(coordinate distances counted)`; hence j ∈ A∩B ⇔ joint ≤ eps ⇔ strict interior, so |A∩B| = k−1 exactly (validated), giving x+y = |A∪B|+k+1 ≤ n+k for KSG(±tree), xblocks, ISX, PID3 alike. At (n,k)=(2,1) this excludes (2,2) ⇒ runtime −D unattainable, as claimed; +D is attainable via an exact-diagonal neighbor (no document claims otherwise).
7. **Threshold tightness.** U×2⁵² = 9.007199254740992 + 0.754111644 = **9.7613109** < 9.761311 = ceil(ratio, 6 dp); downward-rounded threshold preserves strictness (interval width ≈ 8×10⁻¹⁵⁶ nats is negligible).
8. **Ceiling coherence.** Corpus |T| < H_999999 < 16 ⇒ exact error ≤ rounded-reference 8ε + ½ ulp(≤8ε) ≤ 12ε < 32ε globally — the ceiling cannot be threatened by metric choice.
9. **Transcription equality.** The Neumaier table loop, naive loop, range expression, and left-associated endpoint expression are token-for-token equivalent between `stats.rs` (production + test) and both Python routes; both languages use correctly-rounded decimal→binary64 parsing, so "same row, same expression" holds across exact-rational, directed-Decimal, host-binary64, naive-prefix, and production paths. Their correlation (shared corpus/association) is honestly declared in routes-v4.

---

## 5. Hostile tests / mutations for each claimed blocker

**B64-001 (compiled full-corpus partition):**
- *Mutation M1:* in `stats.rs`, force `actual = 0.0` for one non-endpoint row (e.g., row index 100). Expected: Python routes fail the 7844-nonzero assertion **and** the Rust test fails the `== 8ε` assertion (error jumps to |T| ≫ 32ε) — demonstrating transitive coverage.
- *Mutation M2 (the gap):* additionally delete the Rust `== 8ε` and `≤ 32ε` asserts; M1 then survives compiled testing while Python still catches it — proving the compiled route has **no direct** partition guard, i.e., C23's sentence is not implemented as written.
- *Fix-validation test:* add `selected_full_{pos_zero,neg_zero,nonzero}` counters to the Rust test asserting 354/0/7844; rerun M1 with M2's deletions — must now fail in Rust.

**B64-002 (manifest completeness):**
- *Test:* script that hashes every `git status --porcelain` path and diffs against the manifest path set; on this snapshot it must report exactly `{...-context.md, ...-receipt.json, ...-oversize-negative-receipt.json}` missing. Regenerate the context; the diff must be empty or the completeness sentence must be scoped.

**B64-003 (phase red):**
- *Test:* `python3 scripts/check-ksg-phase-isolation.py` and `-O` on this tree; both must exit 1 at the untracked-partition/policy-delta gates (61 vs 56; 5-path delta). A zero exit falsifies my analysis and would itself be a severe checker defect.

---

## 6. Ranked repair/replay plan (no gate weakening, no evidence promotion)

1. **Pin the review evidence** (B64-002): regenerate the context manifest to cover all untracked paths, or scope the completeness sentence; bind `receipt.json` via the follow-up-receipt pattern (it cannot pin itself).
2. **Close B64-001 constructively:** add the full-corpus partition counters to `stats.rs` (strengthens compiled coverage), or append a new ledger entry correcting C23's wording; never edit C23 in place. Reseal prose digests, packet, checker constants; replay `--claim-only`, `--binary64-only`, `--enclosure-only`, self-tests, normal and `-O`.
3. **Phase policy revision 2** (B64-003): manually review and add the settled-hostile evidence paths (and any receipt-commit artifacts), regenerate `--emit-current-facts-python`, human-review the block, rerun phase checker + self-test normal/`-O`, then the external tree/commit-bound variants at commit time.
4. In the same reseal window: fix the "revision-3" message label (B64-004); record the 9.7613109 measured ratio beside the threshold (B64-007); document the `u32` bound (B64-008).
5. **At settled replay:** bind the final self-test mutation totals into the packet and align AGENTS/justfile comments (B64-005); demonstrate release-profile corpus replay explicitly in CI or the receipt (B64-006).
6. Only after all writers stop: full settled-byte matrix per `implementation-v4.md`, then M1a commit, then M1c — unchanged from the packet's own ordering. Nothing here authorizes upgrading any bounded observation to a universal, portability, estimator, support, or PID claim.

---

## 7. Final disposition (limited to the bytes and domains actually inspected)

- **Bounded positive-integer arithmetic core:** under the binary64/compiled-refinement lens I found **no counterexample**. The exhaustive/stress row counts, endpoint splits, tie-list membership, W0/W1/W2/W2b targets and bit patterns, the `1/105` witness, the structural endpoint `+0`, the per-predicate `x+y ≤ n+k` set argument, the metric separation, the interval-arithmetic directions, and the digest web were independently re-derived or reconstructed and agree. The corpus-scale scan values and residue digests remain machine-replay facts I could not hand-verify; repro commands are listed. **Concur with GO on the stated exact/helper and finite-corpus domains**, with B64-001's wording defect noted against the ledger, not the arithmetic.
- **Repository/publication integration:** **concur with NO-GO.** Additionally: the exact snapshot is phase-red by construction (B64-003), and the review context's own manifest-completeness claim is false (B64-002), so this snapshot cannot serve as the settled hostile-review basis without the repairs above.
- Nothing in this review is a verification, and search failure (mine included) proves nothing.