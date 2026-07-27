# Independently reconstructed claim and exact scope

**Claim under audit (as I reconstruct it from the bytes, not from trust):**

1. *Exact object.* For integers `n ≥ 2`, `1 ≤ k < n`, `k ≤ x,y ≤ n` (rectangular helper box; the Lean pure theorem admits the superset `n ≥ 1, 1 ≤ k ≤ n`), under the **typed premise** `ψ(m) = H_(m−1) − γ` at the four used positive-integer arguments, `T = ψ(k)+ψ(n)−ψ(x)−ψ(y) = H_(k−1)+H_(n−1)−H_(x−1)−H_(y−1) = (H_(n−1)−H_(max−1)) − (H_(min−1)−H_(k−1))`, with `−D ≤ T ≤ D`, `D = H_(n−1)−H_(k−1)`, sharp **only on the box** (`x=y=k → +D`, `x=y=n → −D`), in nats, negative values legitimate.
2. *Bounded corpora only.* 8,198 = 6,920 + 1,278 frozen rows; 354 = 240 + 114 structural endpoints; 8·ε rounded-reference comparator with 40 ties (first row 7598); a **distinct** exact-rational maximum uniquely at row 7673 `< 9.761311·ε`; both `< 32·ε`; corpus-only modular iff (3 selected fields, one-way implication only, 28 mutants); 150/121 prefix discriminators.
3. *Formal.* 19 Lean theorems / 14 mutants; 4 Z3 QF_UFLIRA obligations (sat-preflight then unsat) / 12 mutants; both conditional on the analytic premise and sharing human signs/maps/statements.
4. *Disposition.* Bounded core GO on those domains; **repository/publication integration NO-GO with exactly 13 open gates**; no `evidence-matrix-v4.md`/`decision-v4.md` may exist; M1c only after a pushed M1a commit.

Anything stronger than this in any artifact would be a defect. I found none in the inspected bytes. My output verifies nothing; it is advisory attack input.

---

## 1. Finding table

Legend: sev = Blocker-to-close (BC), High (H), Medium (M), Low (L), Info (I). "Shared cuts" = premises my allegation shares with the candidate.

| ID | Sev | Object | Location | Proposition | Minimal witness / derivation | Independent reproduction | Shared cuts | Falsifier of my allegation |
|---|---|---|---|---|---|---|---|---|
| KSG4-F01 | BC (expected) | Git phase custody | `scripts/check-ksg-phase-isolation.py:354-411, 2355-2369`; Git-state block | The snapshot tree **cannot** pass phase validation: git status lists 5 untracked `audit/evidence/fable5-ksg-rev4-settled-hostile-*` files absent from `EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES` (56 paths) and from the 93-path policy (`ksg-rev4-phase-path-policy.json`). Any phase-green claim on these bytes is false. | Set difference: status `??` list minus policy/untracked tuple = the 5 fable5-settled-hostile paths. | `python3 scripts/check-ksg-phase-isolation.py` → expect exit 1, "precommit untracked-deliverable partition changed". | Same Git snapshot; same `.gitignore` semantics (`:990-1007`). | Checker exits 0 on this tree. (That outcome would itself expose a worse hole: `.gitignore` hiding review evidence — test with `git check-ignore -v audit/evidence/fable5-ksg-rev4-settled-hostile-*`.) |
| KSG4-F02 | I | Review-context custody | "Git state" vs "Complete changed-path byte manifest" | The snapshot is time-skewed: manifest hashes only 2 of 5 settled-hostile files (`-prompt.md`, `-runner.mjs`); `-context.md`, `-receipt.json`, `-oversize-negative-receipt.json` are listed untracked but unhashed. The manifest, not the status list, is the hash authority. | Direct diff of the two sections. | Recompute `git status` inventory vs manifest on the archived checkout. | None. | Manifest actually contains the 3 files (it does not, in these bytes). |
| KSG4-F03 | M (hardening) | Z3 checker shape model | `scripts/check-z3-ksg-integer-harmonic.py:144-156` | Design vacuity gap: `validate_proof_source` does not forbid a smuggled `(assert theorem_holds)` in the *original* file. Such a file yields trivial `unsat` (baked contradiction) yet passes shape checks and the positive preflight. **Mitigated on current bytes** by SHA pins and by the 12-mutant suite (premise-reversal mutants would then return `unsat` and go red). | Construct `X' = X + "(assert theorem_holds)"`; run shape checks standalone → pass; run negated → unsat regardless of encoding. | Scratch copy with rebased digest; observe main checker green on shape, self-test red on mutants. | Same solver, same file grammar. | The checker already rejects any extra `(assert theorem_holds)` (no such rule at :144-170). |
| KSG4-F04 | L (hardening) | Z3 command firewall | same file `:157-170` | Substring bans (`(forall`, `(push`, `(check-sat-assuming` …) are whitespace-bypassable (`( forall`, `( push 1 )`); SMT-LIB tokenizes across whitespace. Digest pins dominate; matters only for future rebases/mutation robustness. | `"( forall"` not matched by `"(forall" in source`. | Feed a whitespace-variant file to `validate_proof_source` under a rebased digest. | SMT-LIB lexing. | Regex/tokenizer-based ban already present (it is plain substring). |
| KSG4-F05 | L / open | Lean premise nonvacuity | `audit/formal/lean-ksg-harmonic/v4/…` (bytes **not in context**); `check-lean…py:60-80` | No machine check that `PositiveIntegerDigammaPremise ψ γ` is instantiable; contradictory hypotheses would make the 10+ conditional theorems vacuous. Mathematically satisfiable (`ψ m := H_(m−1) − γ`), and vacuity would flip Lean mutants to *compiling* (self-test red), so mitigated — but not directly checked. | If premise ⊥ then every mutated conclusion still compiles → 14-mutant suite fails; hence green mutants are the de-facto nonvacuity witness. | Verify at replay that the Lean source contains (or add) an `example`/instance witnessing the premise for the concrete rational model. | Kernel soundness; pinned toolchain. | Source already contains an instantiation witness (cannot confirm — bytes absent). |
| KSG4-F06 | L | Axiom-inventory parsing | `check-lean…py:162-176` | `parse_axiom_inventory` uses a tolerant `re.DOTALL` findall into a dict (silent de-dup); a format drift or interleaved info line could mis-bucket. Backstopped by returncode-0 + empty-stderr + exact 19-name set equality. | Regex admits multi-line captures via `.*?` DOTALL. | Feed synthetic `#print axioms` transcripts to the parser. | Lean message format. | Strict per-line parse with count==19 already present (it is not). |
| KSG4-F07 | L | Doc/count binding | `AGENTS.md:189-194` vs `task-dispositions.json` T138 scope note | AGENTS comments assert "110 claim mutations" / "170 integration mutations" while T138 states the main-checker totals are deliberately **not** final. Unbound prose count = drift risk (mirrors the resolved 26→28 modular episode). | Textual comparison. | Run both self-test routes; diff printed totals against AGENTS comments. | Self-test bytes (`9c62ff14…`, not provided). | Replay prints exactly 110/170. |
| KSG4-F08 | L | Chronology / M1a identity | `completion-active-resume.md:250` vs `:90-94` and obligations G1 | A superseded 2026-07-26 checkpoint calls `afc45ff2…` "the M1a implementation commit," while live authority holds M1a not yet created (gate `unsigned_main_commit_and_receipt` open). Two commits could later both claim "M1a." | Direct quote conflict across sections. | n/a (documentation). | Supersede policy (declared). | The eventual M1c receipt names the M1a commit and explicitly retires the `afc45ff2` label. |
| KSG4-F09 | Open (replay) | Embedded digests in absent sources | `check-ecosystem-capabilities.py`, `check-review-evidence.py`, both revision/enclosure/modular/lean/z3 **self-tests**, catalog/release projection pins (`check-ksg-harmonic-revision.py:254-337`) | Second-order staleness after the assurance-registry digest correction cannot be excluded inside sources whose bytes are not in this context; all *inspectable* embeddings are current (see §4/R9). | 45+ digest cross-checks performed; 0 mismatches; residual set enumerated. | `python3 [-O] scripts/check-ecosystem-capabilities.py`, `check-review-evidence.py`, all seven `--*-only` routes + self-tests. | Manifest hashes as ground truth. | Any red among those replays, or a hash mismatch inside those sources. |

No mathematical, indexing, sign, vacuity, model-evaluation, or custody **error** was found in the inspected bytes. F01/F02 are settledness facts consistent with the declared NO-GO; F03–F08 are hardening/consistency items.

---

## 2. Dispositions

**Genuine blockers (to closing gates; none contradict the packet):**
- KSG4-F01 — tree unsettled; policy/facts/packet must be resealed after this review's artifacts land; no phase, claim-custody, or "settled replay" credit may attach to these bytes. This is the operational content of open gates `git_phase_isolation` and `claim_custody_final_replay`.

**Hardening, valuable but non-blocking:** F03, F04, F05 (add witness), F06, F07 (bind or mark counts illustrative), F08 (one clarifying line / receipt language). None weakens a gate.

**Already-closed concerns I re-verified independently (spot proofs in §3/§5):**
- C30 non-gap witness: `(n,k,x,y)=(8,2,3,5)` → `T = 503/140 − 3/2 − 25/12 = 4/420 = 1/105`, and `0 < 1/105 < 1/7` — exact. ✔
- C17/W5 converse failure: all four rejected-prime collisions reduce to `±(H_999999 − H_3)` (one divisibility event); signs as stated. ✔
- C14 prefix naming (150 selected vs 121 naive) consistently qualified everywhere inspected. ✔
- C18/C20 metric separation: 8·ε (binary64-rounded-reference) vs `<9.761311·ε` (exact-rational) kept distinct in claim, witnesses, packet, registry, METHODS, checkers; I verified `9.761311·ε ≈ 2.16744650e−15 >` enclosed upper `2.16744642…e−15` — the strict-multiplier statement is arithmetically coherent. ✔
- C31: "maximum reciprocal summand denominator/index = 999999" is the correct object; every `1/j` invertible mod each selected prime (checker enforces `maximum < prime`, `check-…modular…py:177-205`); Miller–Rabin with bases {2,3,5,7,11} is genuinely deterministic for all u32 moduli. ✔
- C24/C27/C28/C29/C22/C25 lifecycle-red default, exact tuple set, hardlink `st_nlink==1`, strict JSON typing, prose-byte binding — all present in `check-ksg-harmonic-revision.py` as described. ✔

**Rejected / ill-posed attacks (with reasons):**
- R1 CRT smuggling — absent; every artifact says "redundant fault diversity, not CRT"; converse explicitly denied.
- R2 runtime `−D` attainability — never claimed; and provably impossible: on both routes `x+y ≤ n+k` (derivation §3), while `−D` needs `x+y = 2n > n+k` for `k<n`.
- R3 promotion of `x+y ≤ n+k` — recorded as `runtime_candidate_status: unpromoted_follow_up…` (packet:59); claim-v4 refuses promotion. Correct restraint.
- R4 Z3 vacuity via inconsistent premises — excluded by design: `sat` on (premises ∧ theorem) entails premise consistency (`:202-213`). (F03 is the *different*, smuggled-positive-assert shape gap.)
- R5 Lean `k=n`/`n=1` superset domain leaking into runtime — explicitly disclaimed (claim-v4:62-64; formal-assurance-v4:73-77); a superset theorem covers the box; harmless.
- R6 "two independent monotonicity proofs" — explicitly forbidden wording (formal-assurance-v4:106-108); no artifact violates it.
- R7 stale `26` modular count — only in a **superseded, dated** resume section; all active v4 artifacts say 28. Consistent with append/supersede policy.
- R8 primes below a summand index — impossible: max index 999999 < 1000003 < all selected primes.
- R9 second-order stale digest from the assurance-registry correction — **searched and not found** in inspectable bytes: `ecosystem-capabilities.json:1829` = `5aa34f1d…` ✔ current; `ECOSYSTEM_CAPABILITIES.md:17-20` ✔; `software-identity-reference-v1.json` binds `d2ad2e22…`/`4fe9e5e4…` ✔; all 33 `EXPECTED_BOUND_ALLOWED_BLOBS` in the phase checker match the manifest ✔; the `63a843b4…` base projection substitutes historical values *by design* (not stale). Residual risk confined to F09's absent sources.

**Open questions:** O1 Lean v4 source + 14-mutant suite bytes unseen (statement adequacy is digest- and mutation-mediated here); O2 the four `.smt2` bodies unseen (same); O3 eco/review checker internal pins (F09); O4 revision self-test totals (F07); O5 catalog/release projection digests (`a0c7f7f6…`, `3596fc98…`, `24e2f99f…`, `1e49ba7f…`, `7dcad03d…`, `dfa02422…`, `14cc8ece…`) require machine recomputation; O6 `nn.rs` (`validate_kth_neighbor_shell`, `strict_radius`) bytes unseen — count-domain guarantees checked structurally and via W2b only; O7 generator no-write stdout contract under `-O` unverified from bytes.

---

## 3. Independent derivations performed (falsification attempts that failed)

- **Bound & sharpness.** With `a=min,b=max`, both `(H_(n−1)−H_(b−1))` and `(H_(a−1)−H_(k−1))` lie in `[0,D]` ⇒ `T∈[−D,D]`; endpoints at `x=y=k` / `x=y=n`. W0 at `n=2,k=1` gives `(+1, 0, 0, −1)` exactly as stated.
- **W1/W2/W2b.** `H_7−H_4 = 1089/420 − 875/420 = 107/210` ✔. From the eight isx diagnostics `(nα,nt)` (isx.rs:1579-1588) the exact mean is `(1/8)·Σ = 284/(420·8) = 71/840` ✔ — the eight local terms are `109/420, −5/14, 83/140, −4/21, −31/420, 107/210, 1/105, −31/420`. W2b: joint disjunction distances at row 0 are `{1,3}` ⇒ unique shell radius 1; strict counting gives `(nα,nt)=(1,3)=(k,n)` ⇒ structural `+0`; rows 1/2 likewise `(1,3)` with radii 1, 2 — matching the packet's `row_diagnostics` bit-for-bit intent. The kth joint neighbour fails the strict source count via its disjunction coordinate ⇒ `nα ≥ k+1` is indeed false. ✔
- **Corpus combinatorics from first principles.** Exhaustive: `Σ_{n=2}^{16} Σ_{k=1}^{n−1}(n−k+1)² = 6936 − 16 = 6,920` ✔. Stress per-n: 129, 154, 179, 204×4 = **1,278** ✔. Endpoints: `2·Σ(n−1)=240` and `2·57=114` ✔ (both `k−1` and `n−1` always occur in `count_values`, and `k−1≠n−1`).
- **Row-index reconstruction.** Stress blocks start at 6920/7049/7203/7382/7586/7790/7994. Offset arithmetic yields: 7598 → `(4096,1,2048,2048)` ✔; 7673 → `(4096,4,2049,2049)` ✔; 7952 → `(65536,64,32799,32799)` ✔; 8045/8049/8069/8093 → `(1000000,3,2,3)/(3,2)/(4,3,3)/(4,999999,999999)` ✔. This independently confirms generator↔checker↔certificate row-order correspondence at every named row.
- **Runtime count-set argument (both routes).** KSG exclusive: strict-interior set = `A∩B` exactly (`|A∩B|=k−1`), `|A∪B| ≤ n−1` ⇒ `x+y = |A∪B|+|A∩B|+2 ≤ n+k`; Ehrlich inclusive: anchored sets give `|A′∩B′| = k`, `x+y = |A′∪B′|+k ≤ n+k`. So the "set argument" **does** transfer to each specific production predicate with the correct anchor adjustment — and the candidate correctly keeps it *unpromoted*. Also `x,y ≥ k` and `≤ n` on valid unique shells ⇒ the helper's `debug_assert` domain (stats.rs:229-232) is implied on runtime paths.
- **Formal inventories.** Checker `THEOREMS` (check-lean…py:60-80) = 19 names decomposing exactly as 14 retained (v2 list) + 5 new (`harmonic_monotone`, `symmetric_range_term_cast`, `symmetric_range_components_bounded`, `symmetric_range_term_bounded`, `digamma_four_term_symmetric_range_bounded`) matching formal-assurance-v4:55-63; Lean mutants 9+5=14 map one-to-one onto the v2 table plus the five new kills; Z3 mutants 8+4=12 (three order-premise reversals + tightened lower conclusion) — I checked each reversal admits a genuine countermodel (e.g., `Hk=10, Ha=Hb=Hn=0` breaks `T ≤ D`), so none is a dead mutant. The three chained order premises are exactly sufficient for the bound in QF-LRA — no hidden monotonicity is smuggled into Z3.
- **Digest web.** Every digest that is embedded in a provided source *and* recomputable against the manifest matches: 33 phase blob pins, packet ↔ manifest (11 v4 prose files, fixture/sidecar/generator, certificate + sidecar, enclosure pair, Lean/Z3 sources, z3 self-test), stats.rs generator pin, eco/identity bindings. **0 mismatches in ~45 comparisons.** (Search failure proves nothing beyond this enumerated set — see CEGIS note.)

**CEGIS note.** Finite search spaces used: (i) digest set {embedded pin} × {manifest} with counterexample predicate "≠" — 0 hits; (ii) stress-constructor space with predicate "endpoint pair missing/degenerate" — empty by construction; (iii) named-row index space under the reconstructed order — all 7 witnesses land. Minimizers were exact (integer arithmetic); no conversion gap. These exhaustions certify only their enumerated domains; absence of counterexample elsewhere is **not** evidence.

---

## 4. Correspondence matrix

✓ = byte-verified here; ✓a = re-derived exactly by this audit; D = digest-bound only (bytes unseen); R = replay-required; — = not applicable; ✗ = fails on this snapshot.

| Fact | Prose (claim/witn./assur.) | Packet JSON | Exact algebra (audit) | Lean | Z3 | Mod. certificate | Rust helper | Prod. callers/tests | Release/catalog/registry views | Git custody |
|---|---|---|---|---|---|---|---|---|---|---|
| Identity + range form | ✓ | ✓ | ✓a | D(19 thms) | D(4 oblig.) | ✓ (statement block) | ✓ stats.rs:222-237 | ✓ 4+1+1 call sites | ✓ boilerplate | ✓ blob pins |
| Box bound sharp; ±D box-only; no runtime −D | ✓ | ✓ (`w0…attainability=false`) | ✓a (+ impossibility proof) | D | D | — | — | — | ✓ | ✓ |
| Maps: exclusive `+1` / inclusive direct | ✓ | ✓ | ✓a | D | D | ✓ | ✓ | ✓ (`nx+1,ny+1`×4; `n_alpha,n_t`) | ✓ | ✓ |
| 8198/6920/1278; 354=240+114 | ✓ | ✓ | ✓a (derived) | — | — | ✓ segments | ✓ row-derived | ✓ | ✓ | ✓ fixture pin |
| Named rows 7598/7673/7952/8045-8093 | ✓ | ✓ | ✓a (index reconstruction) | — | — | ✓ | ✓(7598 tuple) | — | ✓ | ✓ |
| 8·ε / 40 ties comparator | ✓ | ✓ | R (float replay) | — | — | — | ✓ constants | — | ✓ | ✓ |
| `<9.761311·ε` unique max; 6509/5934/0 | ✓ | ✓ | ✓a (multiplier check) + R | — | — | — | — | — | ✓ | ✓ |
| 150/121; 354 `+0`; 7844 nonzero | ✓ | ✓ | ✓a (structural `+0` from range assoc.) | — | — | — | ✓ | ✓ | ✓ | ✓ |
| Corpus-only iff; one-way residue; 28 mutants | ✓ | ✓ | ✓a (implication logic; collisions) | — | — | ✓ + R (residue digests) | — | — | ✓ | ✓ cert pin |
| W1 (79,(4,1),107/210,bits) | ✓ | ✓ | ✓a | — | — | — | — | ✓ ksg.rs:2864-2880; tests/ksg.rs | ✓ | ✓ |
| W2 71/840, 8 positions; W2b `(k,n)` | ✓ | ✓ | ✓a (mean recomputed) | — | — | — | — | ✓ isx.rs tests | ✓ | ✓ |
| Lean 19/14, axioms {propext,choice,Quot.sound} | ✓ | ✓ | — | D + R | — | — | — | — | ✓ | ✓ src pins |
| Z3 4 sat-preflight/4 unsat/12 mutants | ✓ | ✓ | ✓a (mutant liveness) | — | D + R | — | — | — | ✓ | ✓ |
| Estimator revisions v4/v2 (15 fam.) / protected 20; catalog 20/49 | ✓ | — | — | — | — | — | ✓ strings :969/:648 | ✓ tests assert | ✓ scope/registry/METHODS | ✓ + R (projections) |
| NO-GO, 13 gates, no final artifacts | ✓ | ✓ | — | — | — | — | — | — | ✓ | ✓ (lifecycle-red default) |
| Anchor `a9aa60c9…`, 93-path policy, 37M+56A | ✓ | — | — | — | — | — | — | — | — | ✗ on snapshot (F01); ✓ facts internally |

Semantic (not merely hash) consistency across the regenerated views was checked for every number/wording pair visible in METHODS.md, release-scope, assurance-registry, task-dispositions, ecosystem files: no divergence found.

---

## 5. Hostile tests / mutations

**For KSG4-F01 (blocker):**
- T1: `python3 scripts/check-ksg-phase-isolation.py` on the snapshot → must exit 1 citing the untracked partition. Exit 0 falsifies F01 *and* triggers T1b: `git check-ignore -v audit/evidence/fable5-ksg-rev4-settled-hostile-*` (any match = review evidence invisible to candidate enumeration — escalate).
- M1: append the five fable5 paths to `EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES` **without** touching the policy JSON → checker must still fail (policy delta vs snapshot delta mismatch at `validate_phase_path_policy`), proving the facts cannot be silently rebased around the reviewed policy.
- M2: add the five paths to the policy JSON without updating `PHASE_PATH_POLICY_SHA256` → must fail at the digest gate (`:1459-1462`).

**For KSG4-F03 (design demo, scratch only):** copy `ksg-local-bound-v4.smt2`, append `(assert theorem_holds)`, rebase the digest in a scratch checker copy → shape validation passes (demonstrates the gap); then run the 12 documented mutants against it → premise-reversal mutants return `unsat` → suite red (demonstrates the mitigation). Repair: add `required_counts["(assert theorem_holds)"] = 0` for the original, or pin exact total assert counts per file.

**For KSG4-F04:** feed `( forall ((x Int)) true)` variant under a scratch digest → currently passes the forbidden scan; a token-aware ban must reject it.

**For KSG4-F05:** `#check` / `example` instantiating `PositiveIntegerDigammaPremise` with the concrete rational model in the v4 source; mutation control: replace the premise with `False` — all 14 mutants must then *compile* and the self-test must go red (verifying the suite's vacuity-detection property empirically).

**For KSG4-F07:** run both self-test routes normal/`-O`; assert printed registered-mutation totals equal AGENTS comments or amend AGENTS.

---

## 6. Ranked repair / replay plan (no gate weakening, no evidence inflation)

1. **Settle the tree** (closes F01/F02): commit-or-relocate the settled-hostile artifacts per an explicit human decision; regenerate `--emit-current-facts-python`, human-review the diff (policy is `mechanical_resealing_permitted: false`), reseal policy → facts → packet in hash-first-then-semantic order (C21/C25 discipline).
2. **Full normal/`-O` replay on the settled bytes** (closes F09/O3-O5/O7): oracle generator; enclosure + 29 mutants; modular gen/checker + 28 mutants; Lean checker + 14 mutants; Z3 checker + 12 mutants; all seven `--*-only` revision routes + both self-test routes; phase checker with `--expected-candidate-tree/--checkpoint-commit` + self-test; eco/review/catalog/release/identity gates; focused Rust debug/release, W1/W2/W2b single-test harness, 12-test serial/parallel parity; fmt/clippy/rustdoc.
3. **Archive Lean/Z3 source and self-test bytes in the next hostile context** (closes O1/O2) so statement adequacy stops being digest-mediated for external review.
4. **Apply F03/F04/F06 hardening** to the Z3/Lean checkers (additive checks only), and add the F05 instantiation witness if absent; extend mutation suites accordingly (counts go up, never down).
5. **Bind or de-assert AGENTS counts (F07)**; add one clarifying sentence resolving the `afc45ff2` "M1a" label (F08) — ideally in the eventual M1a/M1c receipts.
6. Only after 1–5: unsigned M1a commit, push, remote-SHA + CI receipt; then M1c evidence/decision in a separate re-anchored milestone with the checker's final-lifecycle constants updated and resealed.

---

## 7. Final disposition (limited to inspected bytes and domains)

- **Bounded arithmetic core:** no counterexample found. Every recomputable identity, witness, count, index, and reduction (`107/210`, `71/840`, `1/105 < 1/7`, W0/W2b, 6,920/1,278/240/114, rows 7598/7673/7952/8045-8093, collision reductions, the `x+y ≤ n+k` set argument for both routes, `9.761311·ε` enclosure coherence) checks exactly. Consistent with GO **only** on the declared exact/helper and finite-corpus domains.
- **Proof/SMT correspondence (assigned focus):** counts (19/14, 4+4/12), theorem-name decomposition, premise placement (typed digamma; three explicit Z3 order instances), vacuity protections (Z3 sat-preflight; mutation suites as de-facto nonvacuity detectors in both systems), trust bases (kernel + 3 axioms; solver-not-kernel for Z3), and shared-cut declarations are **internally consistent and match independent derivation**. Statement-level adequacy of the Lean/Z3 bytes themselves remains digest- and mutation-mediated in this context (O1/O2) — an evidentiary boundary, not a detected defect.
- **Custody:** ~45 digest cross-checks, 0 mismatches; no second-order stale digest from the assurance-registry correction found in inspectable bytes; residual risk enumerated (F09). The snapshot tree is demonstrably **unsettled** (F01/F02), exactly as the packet's open gates assert.
- **Disposition:** the narrow intended disposition is supported by these bytes — bounded core GO on stated domains; **repository/publication integration remains NO-GO** with all 13 gates open; no artifact inspected smuggles a final decision, a runtime `−D`, a CRT converse, an ULP claim, or a transfer to KSG consistency, Ehrlich/MGW/PID, support, calibration, or consumers.
- This review is advisory falsification input. It verifies nothing by itself; every allegation above carries its own falsifier and must be independently reproduced or rejected on the settled tree.