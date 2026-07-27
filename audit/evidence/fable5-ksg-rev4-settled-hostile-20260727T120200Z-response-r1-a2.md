# Fable 5 Max adversarial advisory — binary64 / compiled-refinement lens, KSG revision-4 M1a

**Standing disclaimer:** this is advisory falsification input only. Nothing below verifies, certifies, or gates anything. Search failure proves nothing.

---

## 0. Independently reconstructed claim and exact scope

I reconstruct the candidate's binary64/compiled claim as the conjunction of:

1. **Helper arithmetic.** `stats.rs::shifted_harmonic_table(n)` computes `table[m] = H_(m-1)` by a serial Neumaier-compensated prefix (`sum`, `correction`, store `sum + correction` per step); `ksg_local_harmonic_term(table, k, n, x, y)` evaluates `(table[n] − table[max(x,y)]) − (table[min(x,y)] − table[k])` in pure binary64, valid only for `1 ≤ k ≤ x,y ≤ n < table.len()`, with debug-only asserts.
2. **Frozen-corpus numerics.** On the exact 8,198-row schema-2 corpus (6,920 outer-box + 1,278 stress; 354 structural endpoints split 240/114): (a) the *binary64-rounded-reference* comparator `abs(selected − binary64(stored Decimal text))` has maximum exactly `8·ε` with 40 ties, first at zero-based row 7,598 `(4096,1,2048,2048)`; (b) the *exact-rational* error has a unique maximum at row 7,673 `(4096,4,2049,2049)`, selected value `-0x1.6b52fe6a01407p+2`, enclosed strictly below `9.761311·ε` (160-digit directed Decimal, downward-rounded strict thresholds); (c) both are below the `32·ε` finite-corpus ceiling; (d) endpoint partition `+0/−0/nonzero = 354/0/0`, full-corpus `354/0/7844`, selected-Neumaier-prefix ordinary-left `150/0`, naive-prefix ordinary-left `121/0`, swap-bit asymmetries `0`.
3. **Production dataflow.** Exactly four eligible KSG call sites pass `nx+1, ny+1` (exclusive), one ISX and one PID3 site pass anchor-inclusive counts directly; the non-cancelling heuristic stays on general digamma; unique-shell validation precedes every count; W1 `(radius 79, (4,1), bits 0x3fe04e04e04e04e0)`, W2 `((5,2), same bits; public mean 0x3fb5a35a35a35a3e ≠ correctly rounded 71/840 = …5a36, eight ordered-binary64 positions)`, W2b `(n_alpha,n_t)=(k,n)=(1,3)` on all-unique inputs with `+0` outputs.
4. **Profile/backend claims.** Brute/kd-tree bit-identity or identical typed errors; serial==parallel bit identity pinned by 13 KSG-relevant u64 constants in a 12-test file with a non-zero-test-capable crate gate; thread budgets 1–4/max identical.

Scope of my inspection: exactly the bytes supplied in the context (full files and pattern excerpts). `nn.rs`, `kdtree.rs`, `par.rs`, `metric.rs`, `support.rs`, all self-tests, the Lean/Z3/generator/fixture/certificate bytes are **not** in the context and are assessed only via digest pins, the protected-path projection (baseline-identical custody), and compiled tests that are in the context.

---

## 1. Finding table

| ID | Sev | Object | Location | Proposition | Minimal witness / derivation | Independent reproduction | Shared cuts | What falsifies my allegation |
|---|---|---|---|---|---|---|---|---|
| B64-01 | **Major (prose-accuracy; blocks prose freeze, not the bounded core)** | correction-ledger C23 vs compiled corpus test | `claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md:127–137` vs `crates/pid-core/src/stats.rs:493–611` | C23 states the **full-corpus** selected partition `+0/−0/nonzero = 354/0/7844` is derived "in both Python and compiled Rust". The provided Rust corpus test derives only the endpoint partition (`stats.rs:497, 526–550, 574–577`) and the two association counts; it has **no full-corpus zero/nonzero counters**. Enforcement in Rust is only *indirect*: a spurious `+0` at any non-endpoint would violate the frozen `8·ε` max because the smallest nonzero \|T\| in the corpus is `1/999999 ≈ 1e-6 ≫ 32·ε` (e.g., row `(1000000,999999,999998,999998)` reduces to `H_999999−H_999998 = 1/999999`). | Inventory: `stats.rs` counters are exactly `{swap, endpoint_positive_zero, endpoint_direct_left_*, naive_prefix_direct_left_*}`; contrast `check-ksg-harmonic-revision.py:2121–2123, 2164–2169` and `check-ksg-harmonic-exact-enclosure.py:802–808, 836–840`, which do count the full partition. | `grep -n "nonzero" crates/pid-core/src/stats.rs` on the candidate tree; confirm absence of a non-endpoint counter. | C23 prose bytes are pinned by the claim checker (`EXPECTED_REVIEWED_V4_PROSE_SHA256`), so the defect is frozen into reviewed custody. | A compiled test elsewhere in the candidate tree (not in this context) that counts 7,844 non-endpoint nonzeros and 0 negative zeros over the fixture. |
| B64-02 | Minor (expected process state; must close before M1a) | phase gate vs current snapshot | `## Git state` block vs `scripts/check-ksg-phase-isolation.py:354–411, 990–1007, 2356–2364` | The snapshot cannot pass its own phase gate: five untracked settled-hostile files (`…-context.md`, `…-prompt.md`, `…-receipt.json`, `…-oversize-negative-receipt.json`, `…-runner.mjs`) are absent from `EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES` and the phase policy; two of them are even in the byte manifest. `parse_untracked()` will enumerate them ⇒ partition mismatch ⇒ fail-closed. | Git status lists 5 `??` paths not in the 56-entry untracked tuple. | `python3 scripts/check-ksg-phase-isolation.py` on this exact tree ⇒ nonzero exit, "precommit untracked-deliverable partition changed" (or allowlist mismatch). | Facts were generated before the review artifacts existed; the resume already schedules a reseal. | A run of the phase checker on this exact tree that exits 0. |
| B64-03 | Boundary (no defect asserted) | strict-radius/kd-count/parallel-ordering semantics | `ksg.rs:2299–2306, 2368–2380`; `isx.rs:1096–1125`; `pid3.rs:1283–1295` (call sites only) | Claims "strict counting via next-down predecessor", "kd `count_within` inclusive on strict radius", "`map_index_ordered` deterministic index order" rest on `nn.rs/kdtree.rs/par.rs/metric.rs/support.rs`, whose bytes are **not** in this context. Within this delta they are protected paths (baseline-identical by projection), and parity/error tests in-context pin behavior empirically. | `EXPECTED_PROTECTED_PROJECTION_SHA256` covers them; `kdtree_parity_tests` (ksg.rs:2996–3143) pin bit identity and identical shell-error signatures. | Recompute protected projection; rerun the four parity tests. | Protected-projection custody + prior baseline review is the only chain; not re-derivable here. | Providing those file bytes and finding, e.g., `strict_radius` ≠ next-down or non-inclusive `count_within`. |
| B64-04 | Hardening | Python FP evaluation mode | `check-ksg-harmonic-exact-enclosure.py:772–776` (format check only) | `sys.float_info` guards the *type* (radix/mantissa/exponent), not the evaluation mode (x87 double-rounding / `FLT_EVAL_METHOD≠0`). The exact-equality gates would very likely fail loudly on such a host, but the failure mode is undiagnosed divergence rather than a targeted sentinel. Declared premise already covers this ("this host's Python binary64 operations"), so no overclaim — only a diagnosability gap. | — | Add an operation-level discriminator (a known sum whose double-rounded result differs) and assert it. | Both Python numerical routes share this premise. | Demonstration that the existing exact gates provably fail on every non-strict-binary64 host (they likely do, but it is not proved). |
| B64-05 | Hardening / documentation | swap-asymmetry counter semantics | `stats.rs:233–236, 518–524, 573`; `check-…-enclosure.py:796–801, 831` | The 0-swap-asymmetry result is **structural** for the selected range expression (min/max canonicalizes `(x,y)`), not an empirical corpus fact; as a tripwire it detects only removal of canonicalization. Prose calls it an observation ("zero swap asymmetries"), which is true but under-explains its evidential weight. | Symmetry proof: `min/max` of unordered pair invariant under swap ⇒ identical operand sequence ⇒ identical bits. | Mutation: replace the range body with the left-associated form; the counter must fire (verify the self-test contains such a mutation — self-test bytes absent). | Both Python and Rust share the same canonicalized expression, so the two "routes" cannot disagree here. | Self-test bytes showing an association-decanonicalization mutation already registered. |
| B64-06 | Info (custody design fact) | Rust fixture pin is sidecar-relative | `stats.rs:352–370` vs `check-ksg-harmonic-revision.py:49–54, 1806–1813` | The compiled test binds fixture bytes to the *included sidecar* and pins only the generator digest as a constant; the fixture SHA-256 constant lives in the Python checkers and phase blob pins. A consistent fixture+sidecar reseal passes Rust alone. Layered custody is adequate (Python + phase pin bytes), but the Rust route should not be described as constant-pinning the fixture. | Direct code reading. | Mutate fixture+sidecar consistently (keep generator metadata): Rust corpus test passes; `--binary64-only` and phase fail. | Sidecar and fixture are `include_*` from the same tree. | A Rust constant equal to `560e36…147c` somewhere in the candidate tree. |
| B64-07 | Info | mutation totals in AGENTS | `AGENTS.md:191–194` ("110 claim mutations", "170 integration mutations") | These totals appear only in AGENTS; no typed packet fact or provided self-test byte binds them. Cross-doc drift risk (revision-3 history shows exactly this failure class, C13/mutation-count-drift). | Packet has counts for enclosure (29), modular (28), Lean (14), Z3 (12) but no 110/170. | Run both self-tests and count registered mutations. | AGENTS is blob-pinned in the phase facts, so drift is at least byte-detected. | Self-test bytes whose registries sum to 110/170. |
| B64-08 | Open (negative search) | second-order stale digest after registry-digest correction | `ecosystem-capabilities.json:1823–1848`; `ECOSYSTEM_CAPABILITIES.md:9–21`; `assurance-registry.json:9020`; identity JSON; phase `EXPECTED_BOUND_ALLOWED_BLOBS` | I searched for a stale digest *caused by* refreshing the assurance-registry binding: registry binding `5aa34f…` current ✓; method-catalog `d2ad2e…` ✓; release-scope `4fe9e5…` ✓ in eco JSON, eco MD, identity JSON, registry's own `release_scope_sha256`, and phase blob pins. The semantic projection `63a843b4…` is *deliberately* base-frozen (documented substitution rule), not stale. The consumer-records digest `ccc5ba…` and any digests inside `check-ecosystem-capabilities*.py` are not recomputable from provided bytes. **Failure to find is not absence.** | — | Recompute `ccc5ba…` per the documented projection; open the eco checker's constants. | Eco checker bytes absent. | A recomputation showing any of the above digests mismatch current canonical bytes. |

---

## 2. Operation-DAG and production-dataflow reconstruction (role deliverable)

**Table DAG (both languages, bit-identical op sequence):** for `m = 2..n`: `v = 1.0/((m−1) as f64)` → `next = sum + v` → branch on `|sum| ≥ |v|` → `corr += (sum−next)+v` or `(v−next)+sum` → `sum = next` → `store sum + corr`. No FMA, no reordering; Rust IEEE semantics and CPython doubles coincide under the declared strict-binary64 premise. **Truncation-invariance:** production builds the table per call to size `n`; corpus routes build to 10⁶; the prefix scan makes entries `≤ n` identical, so cross-scale comparisons are valid (I checked this explicitly; it is a necessary lemma the prose leaves implicit).

**Term DAG:** `(T[n] − T[max]) − (T[min] − T[k])`; swap-invariant by canonicalization; endpoint rows hit `a−a` twice ⇒ `(+0) − (+0) = +0` under RN — the 354/0/0 endpoint partition is an IEEE structural consequence, and both routes assert it bitwise.

**Call-site DAG (counts → helper):**
- KSG pair tree `ksg.rs:2302` and brute `:2382`; xblocks tree `:2731–2737`, brute `:2811–2817` — all `nx+1, ny+1` after `validate_kth_neighbor_shell` (`:2290–2297, 2360–2367, 2717–2724, 2790–2797`).
- ISX `isx.rs:1128` (`n_alpha, n_t`, anchor-inclusive, after `:1088–1095`); PID3 `pid3.rs:1297–1303` (after `:1282`).
- Heuristic `isx.rs:1533–1545` retains `digamma`/`digamma_int_table`; coefficients sum to 2 ⇒ γ does not cancel ⇒ correctly excluded.

**Per-predicate domain proof (high-value attack answered per path, no set-argument transfer):** unique-shell validation forces exactly `k−1` strict-interior joint neighbors and one boundary point. Since `d_marginal ≤ d_joint` for the same neighbor and comparisons are exact in binary64, each interior neighbor is strictly inside both marginals, so exclusive `nx,ny ≥ k−1` ⇒ `x,y ≥ k`; ceilings `nx,ny ≤ n−1` ⇒ `x,y ≤ n`. Inclusive paths: `n_alpha,n_t ≥ 1+(k−1)=k`, `≤ 1+(n−1)=n`. Moreover `A∩B` (both-strict sets) equals the interior set *exactly* (both-strict ⇒ joint-strict), so `x+y = |A∪B| + (k−1) + 2 ≤ n+k` holds separately for each of the four exclusive predicates and (with the anchor) `n_alpha+n_t ≤ n+k` for both inclusive predicates, with equality attained by W2b at `(k,n)`. This *supports* the deliberately unpromoted runtime hypothesis; I found no illegitimate transfer. Release builds cannot silently violate the helper box: an out-of-range index panics on the bounds check (fail-closed), and `k=n` is rejected by `InvalidK`.

**Backend/profile parity:** brute vs kd-tree pinned bit-identical or error-identical on smooth/tie-heavy/quantized/duplicate/overflow fixtures (`ksg.rs:2996–3143`); W1 pinned on **both** backends (`:2864–2880`). Zero-radius rejection catches `−0.0` (`== 0.0` is sign-blind). The parallel file's crate gate is the zero-test-safe `experimental-pipelines`-only form, with the false-zero `all(…, parallel)` gate explicitly forbidden and 12 exact test names + 13 u64 constants pinned by the phase checker (`check-ksg-phase-isolation.py:454–484, 1796–1863`). Bootstrap constants (5) are correctly outside the "13 KSG-only" set — the bootstrap statistic is a mean over dyadic-rational data, untouched by the harmonic change; the whole file is still blob-pinned.

---

## 3. Independent re-derivations (exact/counterexample lens; all confirmed)

- **W1:** `T = H_1+H_7−H_4−H_1 = H_7−H_4 = 363/140 − 25/12 = 107/210` ✓.
- **W2 mean:** from the isx expected table `(α,t) ∈ {(3,4),(3,7),(3,3),(6,3),(4,4),(5,2),(5,3),(4,4)}` with `k=2,n=8`: exact terms `109/420, −5/14, 83/140, −4/21, −31/420, 107/210, 1/105, −31/420`; sum `= 284/420 = 71/105`; mean `= 71/840` ✓. Division of the compensated sum by 8 is exact (power-of-two scaling), so the eight-position gap lives entirely in the sum — dimensionally consistent (~1 ulp of ≈0.676).
- **W2b:** full trace with `eps = pred(1)` reproduces radii/counts `(1,1,3),(1,1,3),(2,1,3)` and `+0` terms; refutes `n_alpha ≥ k+1` exactly as C30 records.
- **C30 gap counterexample:** `(8,2,3,5) ⇒ T = 1/105 < 1/7` ✓ non-endpoint ✓.
- **W0:** `(2,1)` box values `+1, 0, 0, −1` ✓; runtime exclusion of `(2,2)` via `x+y=4>3` ✓.
- **Rejected-prime collisions:** rows 8045/8049/8069 reduce to `H_999999 − H_3` (one divisibility event) and 8093 to its negative ✓; strict tail signs ✓; Miller–Rabin base set deterministic at this magnitude ✓.
- **Tie set:** the erratum's 40-tuple list counts to exactly 40; every listed tuple is constructible from the stress `k`/count grammar (e.g., `(4096,16,2055,2055)` via `(k+n−1)//2 = 2055`).
- **Magnitudes:** row 7673 exact `T = H_3 + H_4095 − 2H_2049 ≈ −5.677` matching `-0x1.6b52fe6a01407p+2`; `9.761311·ε ≈ 2.16744654e−15 >` enclosed upper `2.16744642…e−15` with ~8e−22 margin; `8.18e−77 = 818` units in the 80-digit last place — exactly a two-figure Decimal, explaining the crisp constant.
- **Reference parsing parity:** Rust `str::parse::<f64>`, Python `float(str)`, `float(Decimal)` are all correctly rounded ⇒ identical comparator reference; tie/max logic in Rust and both Python routes computes identical multiplicity semantics (I traced the `>`/`==` seeding cases, including the degenerate all-zero branch).

---

## 4. Correspondence matrix (inspected surfaces)

Legend: ✓ consistent as written; ◐ digest-pinned only (bytes absent); ✗ discrepancy; — n/a.

| Fact | Prose (claim/witness/ledger) | Packet JSON | Python checkers | Rust code/tests | Formal/cert | Generated views (registry/METHODS/release/eco/dispositions) | Git custody (phase) |
|---|---|---|---|---|---|---|---|
| Exact identity, sharp box bound, W0 non-attainability | ✓ | ✓ | ✓ (`--exact-only`) | ✓ (boundary test 11/6,5/6,−1/3) | ◐ (Lean/Z3 digests) | ✓ | ✓ |
| Exclusive/inclusive maps at all 6 call sites | ✓ | ✓ | ✓ (source route, counts 4/1/1) | ✓ (lines cited §2) | ◐ | ✓ | ✓ (blob pins) |
| 8,198/6,920/1,278; 354=240/114 row-derived | ✓ | ✓ | ✓ (both routes reconstruct rows) | ✓ (row-derived split) | ✓ (modular checker reconstructs) | ✓ | ✓ |
| 8·ε comparator, 40 ties, row 7598 | ✓ | ✓ | ✓ (both) | ✓ (max/first-tuple/ties) | — | ✓ | ✓ |
| Unique exact max row 7673 < 9.761311·ε; 32·ε ceiling | ✓ | ✓ | ✓ (directed, strict-floor thresholds, uniqueness predicate) | — (explicitly Python-only; correctly stated) | — | ✓ | ✓ |
| 6,509/5,934/0 stored-vs-exact separation; 8.18e−77 @7952 | ✓ | ✓ | ✓ | — | — | ✓ | ✓ |
| Endpoint 354/0/0; 150/0; 121/0 | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| **Full-corpus 354/0/7844 "in compiled Rust"** | **✗ (C23 overstates)** | ✓ (facts don't claim Rust) | ✓ | indirect only | — | ✓ (views don't claim Rust) | ✓ |
| W1/W2/W2b bits & counts | ✓ | ✓ | ✓ (source markers) | ✓ (private+public, both backends) | — | ✓ | ✓ |
| Modular: primes, digests, 28 mutants, collisions, one-way implication | ✓ | ✓ | ✓ (independent batch-inverse replay) | — | ◐ (certificate bytes) | ✓ | ✓ |
| Lean 19/14, Z3 4/12, shared cuts | ✓ | ✓ | ◐ (checker bytes provided; sources absent) | — | ◐ | ✓ | ✓ |
| Estimator revision strings v4 | ✓ | — | ✓ (enforced) | ✓ (`ksg.rs:969`, `isx.rs:648`) | — | ✓ (release/registry/eco) | ✓ |
| 15/20 release; 20/49 catalog; identity digests | ✓ | — | ✓ (routes) | — | — | ✓ (all current, incl. corrected registry digest) | ✓ |
| Serial/parallel 12 tests, 13 constants, forbidden PID2 value | ✓ | — | — | ✓ | — | — | ✓ (AST + constant pins) |
| Phase facts vs live tree | ✓ (NO-GO) | ✓ | — | — | — | — | **✗ transient (B64-02, expected)** |

---

## 5. Lists

**Genuine blockers (my findings):**
- **B64-01** — C23 compiled-scope wording vs `stats.rs` (blocks prose freeze; the numerical facts themselves are unaffected and indirectly Rust-enforced).
- (The 13 declared open integration gates remain blockers by the candidate's own design; I confirm, not add, them. B64-02 is a concrete instance of the `git_phase_isolation` gate on this snapshot.)

**Hardening, valuable but non-blocking:** B64-04 (FP-mode sentinel), B64-05 (canonicalization mutation / documentation), B64-06 (document sidecar-relative Rust custody), B64-07 (bind or drop 110/170 totals).

**Already-closed / independently confirmed:** the two-metric separation (C18/C20) is cleanly maintained in every inspected surface including registry, METHODS boilerplate, README markers, and checker output strings; C30 (`n_alpha ≥ k+1` refuted — re-verified numerically); C31 (reciprocal-summand naming — max index 999,999 re-verified against the row grammar); C32 (`x+y ≤ n+k` — re-derived per production predicate incl. exact `|A∩B|=k−1`); C14 (prefix-qualified 150 vs 121 — both routes implement both prefixes with matching operand orders); endpoint `+0` structurality; W1/W2/W2b/mean-71/840 exact web; ISX↔KSG count coherence (`+1` shift across the two witness tables); prefix-truncation invariance.

**Rejected / ill-posed attacks:** "8·ε is an ULP claim" (measure is explicitly defined and absolute); "−0 possible at endpoints" (`a−a=+0` under RN, asserted bitwise); "table-length mismatch between production and corpus" (prefix invariance); "mean-by-8 rounding hides bits" (exact dyadic scaling); "swap asymmetry could hide a defect" (structural symmetry — see B64-05 for the honest residue); "kd/brute tie divergence" (identical typed shell errors pinned on both backends); "release-mode helper OOB is silent" (bounds-check panic, fail-closed); "Python cannot reproduce Rust bits" (identical op DAG under the *declared* strict-binary64 premise; see B64-04).

**Open questions:** self-test mutation registries (29/28/14/12/110/170) unverifiable from bytes; generator's no-write property (only its expected stdout is pinned); `.smt2` premise sufficiency for `ksg-local-bound-v4`; kd `count_within` inclusivity and `strict_radius` next-down (B64-03); eco-checker internal digests (B64-08); whether the 32·ε multiplier's provenance is documented anywhere beyond "reviewed ceiling" (I found no derivation — acceptable as a frozen review constant, but worth one sentence).

---

## 6. Hostile tests / mutations

**For B64-01 (required):**
1. *Gap demonstration:* scratch-mutate `stats.rs` corpus loop: `let actual = if is_endpoint { actual } else { 0.0_f64 };`. Prediction: the mutant is killed **only** by the max-error/tie assertions (indirectly), never by a partition assertion, because none exists; `check-ksg-harmonic-revision.py --binary64-only` kills it directly at "selected full-corpus signed-zero/nonzero partition changed". Record both failure messages as the witness of asymmetric coverage.
2. *Repair verification:* add `selected_full_{positive_zero,negative_zero,nonzero}` counters + `assert_eq!(…, (354,0,7844))` to the corpus test; rerun the same mutant — it must now die at the partition assertion in debug **and** release; then reseal `implementation/ledger` prose (new C33 or amended wording), packet digests, checker prose pins, and the phase blob for `stats.rs`.

**For B64-02:** `python3 scripts/check-ksg-phase-isolation.py` (and `-O`) on this exact tree ⇒ must fail closed naming the untracked partition; after policy/facts reseal including the settled-hostile evidence set, rerun plus `check-ksg-phase-isolation-self-test.py` in both modes.

**For B64-04/05 (hardening):** add (a) a double-rounding sentinel assertion to both Python numerical checkers; (b) confirm or add an association-decanonicalization mutation (`(T[n]−T[x])−(T[y]−T[k])` without min/max) in the enclosure self-test and verify the swap counter and/or max-error gate kills it.

**CEGIS framing:** search space = {row-level exact identities on sampled corpus rows, count-domain implications per call site, single-line semantic mutations of the corpus test and helpers}; fitness = any route disagreeing with a pinned constant; minimizer = smallest row/mutation; conversion = exact `Fraction` re-derivation. My searches found only B64-01; **search failure proves nothing** about unsampled rows or unprovided bytes.

---

## 7. Ranked repair / replay plan (no gate weakening)

1. **B64-01:** add the compiled full-corpus partition counters (preferred) *and* a ledger precision entry; never edit frozen C23 bytes in place — extend per the project's own correction rule. Reseal: prose SHA map → packet → `EXPECTED_ACTIVE_PACKET_SHA256` → phase blob pins → generated views if any boilerplate quotes change. Replay `--claim-only`, `--binary64-only`, `--enclosure-only`, full self-tests, normal and `-O`, plus focused Rust debug/release.
2. **B64-02:** extend the phase policy with the settled-hostile evidence set (context, prompt, runner, receipts) under a `claim_evidence`/`durable_process_state`-style class; regenerate phase facts only after all writers stop; rerun phase + self-test both modes. Keep M1a ordering (implementation commit before any M1c authority) exactly as obligated (G1→D1).
3. **Hardening batch (optional, before reseal to avoid double resealing):** B64-04 sentinel, B64-05 mutation/doc note, B64-06 one-line custody note in implementation-v4, B64-07 bind or delete the 110/170 totals.
4. **Then** the already-required full settled-byte matrix per `implementation-v4.md:114–123` (all scoped routes, W1/W2/W2b debug+release both backends, four 12-test parity profiles, Lean/Z3 both modes, modular, catalogs/release/identity/eco, CI mirrors), final hostile review on the exact resealed tree, M1a unsigned commit + receipt, M1c separately.

---

## 8. Final disposition (limited to inspected bytes and domains)

Within the bytes I inspected: the binary64 helper, its Python reproductions, the two deliberately distinct error metrics, the signed-zero and association counts, the six production call sites with their per-predicate domain guarantees, the witness web (W0–W2b, c30, modular collisions), and the backend/parallel pinning are **mutually consistent**, and every exact quantity I could re-derive from first principles checks out. I found **no counterexample to the bounded arithmetic core on its stated exact/helper and finite-corpus domains**. I found one Major prose-accuracy defect (B64-01) that should block the revision-4 prose freeze until corrected under the project's own correction discipline, one expected-but-real phase-gate failure on this exact snapshot (B64-02), and several bounded-scope items where the load-bearing bytes were not provided (B64-03, B64-08). Nothing I saw supports any statement stronger than the candidate's own: **bounded core GO on its stated domains; repository/publication integration NO-GO with the 13 gates open; M1c only after a verified, pushed M1a.** This review is advisory input only and verifies nothing by itself.