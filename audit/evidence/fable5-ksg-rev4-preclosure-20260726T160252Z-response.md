# Hostile review — KSG-INTEGER-HARMONIC-001 revision 4, preclosure

Scope respected: only the positive-integer local arithmetic `T = psi(k)+psi(n)-psi(x)-psi(y)` under the typed premise, its maps, its bounded corpus, its formal/modular/custody lanes. I attempted falsification by independent re-derivation before reading the packet's own conclusions. Everything below that says "verified" means I recomputed it, not that I believed it.

---

## 0. Independent falsification attempts that failed (the load-bearing checks)

These are the attacks I ran by hand; each was an attempt to break the packet, and each instead confirmed it.

1. **Identity and bound.** `T = H_(k-1)+H_(n-1)-H_(x-1)-H_(y-1) = (H_(n-1)-H_(max-1)) - (H_(min-1)-H_(k-1))` is exact multiset rearrangement; with `k ≤ min ≤ max ≤ n` both parenthesized tails lie in `[0, D]`, giving `-D ≤ T ≤ D`. Attained at `x=y=k` (+D) and `x=y=n` (−D), both inside the runtime count domain (`nx=ny=k-1`, `nx=ny=n-1`), so the bound is sharp not only at W0 but for every `(n,k)`. W0 recomputed: `n=2,k=1` gives `+1,-1,0`. No counterexample exists; I looked for one via the ℕ-truncated-subtraction seam in Lean and found none (`k-1 ≤ max x y - 1` etc. are valid under the stated hypotheses).
2. **Corpus structure.** Exhaustive count: `Σ_{n=2..16} [Σ_{m=2..n} m²] − 15 = 6935 − 15 = 6920` ✓. Exhaustive endpoints: `2·Σ_{n=2..16}(n−1) = 240` ✓. Stress endpoints per generator rule: `12+14+16+18+18+18+18 = 114` ✓. Stress rows: `129+154+179+204·4 = 1278` ✓. Totals 8,198 / 354 / 7,844 ✓.
3. **Rejected-prime collision indices.** Deriving block offsets for the `n=10⁶` stress segment (starts at index 7994; k-blocks of 25, final k=999999 block of 4) places `(10⁶,3,2,3)` at **8045**, `(10⁶,3,3,2)` at **8049**, `(10⁶,4,3,3)` at **8069**, `(10⁶,4,999999,999999)` at **8093** — exactly the certificate's indices. Reductions `±(H_999999 − H_3)` and strict signs verified.
4. **W1.** Recomputed row-5 geometry from the fixed rows: joint distances `{33,79,129,151,156,182,197}`, k=2 radius **79**, interior/boundary (1,1), strict marginal counts **(nx,ny)=(4,1)**, helper args `(2,8,5,2)`, exact `H_7−H_4 = 107/210` ✓.
5. **W2.** Recomputed all eight ISX inclusive local terms from the expected `(n_α,n_t)` table: `109/420, −5/14, 83/140, −4/21, −31/420, 107/210, 1/105, −31/420`; sum `284/420 = 71/105`; mean **71/840** ✓. Encodings `0x…3a36` vs `0x…3a3e` differ by exactly **8** unsigned positions ✓. Domination construction `s2=1000·s1+i` verified strict (min nonzero `|Δs1| = 2`).
6. **Call-site maps.** ksg.rs: exactly 4 `ksg_local_harmonic_term(` sites, all `nx+1, ny+1`; isx.rs: 1 site, inclusive `(n_α, n_t)`; pid3.rs: 1 site, inclusive; heuristic retains general digamma. Matches the exclusive/inclusive contract and the checker's counts.
7. **Modular soundness.** Prime > 999,999 (the true max harmonic index in the corpus) ⟹ all denominators invertible ⟹ exact zero ⟹ residue zero ⟹ contrapositive as claimed. Batch-inverse route in the checker (factorial products + one extended-Euclid + downward sweep) recovers `d⁻¹` correctly; Miller–Rabin with bases {2,3,5,7,11} is genuinely deterministic below 2.15×10¹², covering u32 moduli.
8. **Signed-zero facts.** For the range association, endpoints compute `(a−a)−(b−b) = +0` structurally; swap symmetry is structural via min/max. So `354 +0 / 0 −0 / 0 swap-asymmetries` are forced, and the checks are live (mutations kill).
9. **Custody arithmetic.** 65 mapped files and 35 historical hashes independently counted ✓; mutation partitions recounted: modular 3+3+3+2+5+5+5=26 ✓; claim lane 3+9+15=27 ✓; full suite 8+2+3+20+73+36=142 ✓. Every one of the 15 resealed semantic mutations maps onto an actually-enforced marker or fact — I checked each pair.
10. **Formal statements.** All 19 Lean names present exactly once as `theorem`; the Z3 bound file's `direct=range` is UF-congruence + linear arithmetic under the three explicit order premises; the sat-preflight excludes vacuity; reversing any order premise demonstrably admits a countermodel. Lean/Z3 division of labor (universal monotonicity vs. local order premises) is stated, not blurred.

---

## 1. Findings

**F1 — The naive-prefix `121/354` constant is custody-pinned but not executably replayed. (minor)**
- Locus: `active-packet-v4.json` `facts.binary64_corpus.naive_prefix_ordinary_left_nonzero_count: 121`; `claim-v4.md` "The naive prefix has a different 121/354 result"; `behavioral-witnesses-v4.md` W3.
- Attack: no route in `check-ksg-harmonic-revision.py` (binary64 route builds only the Neumaier table), the Rust tests, or the modular lane recomputes a naive-prefix table. If the true naive count were, e.g., 119, every gate stays green and the packet pins a falsehood.
- Impact: invalidates nothing load-bearing — the number is explicitly "not the stated discriminator," and the discriminating 150/354 *is* replayed in Python and Rust. Survives: everything.
- Classification: real (small) evidence gap; fix is an assurance enhancement (add a naive-prefix recomputation to the binary64 route or demote 121 out of `facts`).

**F2 — Semantic reseal coverage omits four v4 prose files. (minor)**
- Locus: `check-ksg-harmonic-revision.py` `REQUIRED_V4_PROSE_MARKERS` covers `claim-v4.md`, `behavioral-witnesses-v4.md`, `failures/modular-zero-residue-collisions-v4.md`, `formal-assurance-v4.md`, `integration-disposition-v4.md`, `revision-index.md` — but **not** `routes-v4.md`, `obligations-v4.md`, `implementation-v4.md`, `correction-ledger-v4.md`.
- Concrete mutation: reseal `routes-v4.md` changing "triple is not CRT" (Independence accounting) to "triple is CRT," update its leaf hash in the manifest and the unavoidable envelope digest in the checker. `--claim-only` stays green: no marker, no fact, no structural invariant touches `routes-v4.md` content. (The same statement in `claim-v4.md`, `failures/…v4.md`, and `facts` **is** guarded, so authority isn't transferred — only internal inconsistency is injectable.)
- Impact: does not invalidate the demonstrated fail-closed behavior for the 15 registered reseals; weakens the generality of "resealed semantic mutations are rejected."
- Classification: real gap at the margin of the declared envelope; remedy is marker extension, not gate weakening.

**F3 — The four rejected-prime collisions are one modular event, not four. (nit)**
- Locus: `failures/modular-zero-residue-collisions-v4.md`, certificate `rejected_prime_negative_control`.
- Fact: rows 8045/8049/8069 all reduce to `H_999999 − H_3` and 8093 to its negative; all four collisions are the single divisibility fact `1000003 | numerator(H_999999 − H_3)`. The artifacts list the exact reductions (so no false independence is asserted), but "four … collisions" invites over-reading. One sentence would close it. Invalidates nothing; the negative control needs only one exact-nonzero zero-residue witness.

**F4 — Negative-zero assertions are vacuously-true sentinels. (nit)**
- Locus: W3, `stats.rs` test, Python binary64 route.
- In round-to-nearest with nonnegative table entries, neither `((a+b)−a)−b` nor the range form can produce `−0`; the `= 0` counts are structurally forced. Mutations prove the checks are live, but the quantities carry no discriminating power. Fine as regression tripwires; do not present them as findings about the arithmetic.

**F5 — Pinned-but-unshown bytes limit this review's reach. (residual, not a defect)**
- `generate-ksg-local-arithmetic-oracle.py`, `generate-ksg-harmonic-modular-certificate.py`, the fixture itself, `ksg-digamma-cancellation.smt2`, `ksg-index-maps.smt2`, `ksg-symmetric-range.smt2`, `call-site-map.md`, `revision-index.md` are digest-pinned but not in the retained bytes. Their properties rest on digests, prior-revision review, and behavioral replay (row reconstruction, sat/unsat pattern, mutation anchors). Additionally, no route compares the fixture's nonendpoint Decimal strings against exact `Fraction` values with correct rounding per row; the 8·ε gate plus the exactly-pinned max/tie signature makes a hidden Decimal-route error very likely to trip red, but an exact per-row comparison is the clean closure.

**F6 — Catalog lane still binds claim-v3 evidence. (minor, integration lane only)**
- Locus: `KSG_REQUIRED_CATALOG_EVIDENCE` cites `claim-v3.md` / `formal-assurance-v3.md` while revision 3 is `frozen_preclosure_no_go`. Declared: constants regenerate at M1c; catalog lane is NO-GO. Consistent staging, but note the *default* checker currently enforces the stale bindings as expected state; must not survive into M1c.

No blocker or major was found in the bounded exact/formal/certificate core or in the preclosure claim/custody lane.

---

## 2. Lens-by-lens adjudication

1. **Object/domain/seam:** exact; runtime `1≤k<n` vs. pure `1≤k≤n` cleanly separated; at `k=n`, `D=0`, `T=0`, bound degenerately holds; no artifact authorizes runtime `k=n`. Units-as-nats is a labeled convention post-bridge, correctly firewalled from MI.
2. **Algebra/monotonicity/bound:** verified (§0.1); sharpness attained at both extremes on the count domain; smallest boundary W0 exact.
3. **Maps/call sites:** verified (§0.4–0.6). Ordered `(4,1)` diagnostic correctly defeats source-symmetric masking; inclusive `(5,2)` bridge exact.
4. **Lean/Z3:** premise correspondence exact; 19/14 and 4+4/12 inventories consistent across packet, claim, checker; shared cuts honestly enumerated; monotonicity division deliberate and correctly not double-counted. Mutation anchors verified unique where checkable.
5. **Modular:** implication direction sound; invertibility argument correct; selected-prime role correctly demoted from CRT; corpus-only iff and nothing more (F3 nit).
6. **Binary64:** `8·ε` correctly labeled absolute nats; 150 vs 121 prefix distinction correctly worded, with F1's replay gap on 121; ordered-positions vs ULP disambiguation (C18) correct; signed-zero facts structural (F4).
7. **W1/W2/serial/parallel:** candidate-present, final-replay-open status is truthful; 13 KSG-affected serial constants recounted from `parallel_bit_identity.rs` (4+1+4+4) ✓; `ISX_REDUNDANCY_BITS == PID2_RED_BITS` internal coherence ✓. No false-green: nothing credits compiled lanes as settled.
8. **Custody:** canonical-JSON, duplicate/nonfinite key, path-escape, symlink, regular-file, cycle-exclusion checks all present and mutation-exercised; 65/35 counts verified; historical bytes doubly bound (map + historical set); preclosure→final lifecycle enforced including refusal of premature `evidence-matrix-v4.md`/`decision-v4.md`.
9. **Checker/self-test:** normal and `-O` modes both exercised with child-optimization preflight; hash-first then resealed-semantic two-stage honestly described as one envelope operation; copied roots isolate mutations; scope-isolation preflights prove route independence; F2 is the marginal gap.
10. **Firewall/downstream:** ten-object firewall consistently repeated; estimator-revision strings are identity labels, not validity claims; W2 explicitly "not a validation of an Ehrlich estimator"; catalog forbids claim-binding on the unchanged shared-config method. No silent transfer found.

---

## 3. Explicit answers

1. **Exact identity and two-sided bound correct on the declared domain?** Yes. Independently re-derived; sharp; attained; the `k=n` seam is handled correctly (pure-domain theorem, runtime exclusion, degenerate `D=0` case sound).
2. **Does the modular evidence justify exactly the frozen-corpus iff and no more?** Yes. Endpoints by universal pairwise cancellation (sufficiency is genuinely universal); nonendpoints by nonzero residues under invertible denominators, per selected prime independently; converse correctly refuted by prime 1000003; no CRT, no universal classification asserted. Nit F3: the four collision rows encode one modular coincidence.
3. **Fail-closed against an unresealed edit and a leaf+manifest resealed semantic edit?** Unresealed: yes, unconditionally (digest map covers all 65 files). Resealed semantic: yes for the demonstrated 15 classes and for any edit touching facts, markers, structure, linked digests, or the certificate; residual F2 for four uncovered prose files, and the checker/self-test bytes themselves remain unanchored until the open Git-commit gate — which the packet itself states.
4. **Can `--claim-only` be green while the default checker is truthfully red?** Yes, by construction — e.g., edit `release-scope-1.0.json` (outside `packet_files`): claim route green, default red via the release route. This is partitioning, not false-green: the claim-only success line embeds `integration_no_go`, help text disclaims integration GO, and the stop conditions forbid promotion from partial routes. No artifact treats claim-only green as broader evidence.
5. **Any prose silently transferring KSG local arithmetic to Ehrlich/MGW/PID validity?** None found. The closest surfaces (estimator-revision strings, catalog evidence bindings to estimator method IDs, W2's Ehrlich construction) are each explicitly framed as identity/arithmetic-conformance, and the guarded statements ("no estimator theorem," "not a validation," ten-object firewall) are themselves under mutation coverage (`claim-mgw-nontransfer-firewall`).
6. **Strongest remaining counterexample or mutation not already covered?** (a) The F2 reseal of `routes-v4.md`/`obligations-v4.md` semantic content (concrete exemplar above) — passes today's claim route; (b) falsification of the unreplayed 121 constant (F1); (c) an exact-`Fraction` correctly-rounded per-row comparison against the fixture's Decimal strings, closing the only shared-cut residual on the corpus values (F5); (d) a joint checker+manifest rewrite, which is outside the declared envelope and is exactly what the open Git-anchor gate exists to close.

---

## 4. Shared cuts and open falsifiers (required even for a clean verdict)

**Shared cuts:** the analytic digamma identity is a typed premise everywhere (Lean, Z3, code, corpus — by design, never proven); human transcription of signs `(+1,+1,-1,-1)`, index maps, and theorem statements is shared by both formal routes and the code; Decimal, binary64, Rust, and modular routes share one frozen row specification and generator class; the binary64 route shares host IEEE-754 semantics with the fixture; checker/self-test bytes are pinned only by their own constants until the Git anchor lands; three of four SMT files and both generators enter this review only via digest plus behavioral replay.

**Strongest open falsifiers:** replay the pinned Lean 4.32.0/Z3 4.16.0 runs on the exact bytes; run the F2 exemplar reseal (should succeed today — extend markers); recompute the naive-prefix 121; exact-rational per-row fixture comparison; independent primality confirmation of the four moduli; then the entire open integration ladder (phase isolation, compiled debug/release, serial recapture, catalog/release closure, M1c manifest regeneration, Git anchoring), none of which this review credits.

Do not weaken any gate. F1/F2 are closed by adding replay/markers, not by relaxing anything.

---

## 5. Verdicts

```text
bounded exact/formal/certificate core: GO
preclosure claim/custody lane: GO
repository/publication integration: must remain NO-GO
```

GO in both bounded lanes is issued with zero unresolved blockers or majors; findings F1–F4 are minor/nit and non-load-bearing; F5/F6 are residual visibility and integration-lane staging, respectively, and are already truthfully declared open by the packet.