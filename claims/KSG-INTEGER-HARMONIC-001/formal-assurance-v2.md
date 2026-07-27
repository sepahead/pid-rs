# Scoped formal assurance for `KSG-INTEGER-HARMONIC-001` revision 2

## Disposition and evidence class

Evidence label: **theorem proved under stated assumptions** for the pinned Lean route, with an
independently solver-checked exact SMT route for the overlapping conditional cancellation,
integer index-map, min/max range, and source-exchange obligations.

This evidence closes formal sub-obligations `L1`, `Z1`, and `N1` in `obligations-v2.md`. It does
not change the overall **active** disposition. In particular, the analytic positive-integer
digamma theorem is a typed premise at the formal boundary, and compiled count production,
binary64 behavior, final feature replay, and release integration remain separate obligations.

## Exact object and theorem map

| Claim object | Lean object | SMT object | Domain and direction |
|---|---|---|---|
| Natural index | `ℕ` | mathematical integers constrained by `>= 0` consequences of the declared bounds | Lean-to-SMT carrier correspondence is a reviewed prose map, not a proved cross-tool equivalence |
| $H_m$ | `harmonic m : ℚ := ∑_{i=0}^{m-1}(i+1)^{-1}` | `harmonic : Int -> Real`, uninterpreted | Lean verifies the finite sum and successor recurrence; SMT range/index results hold for arbitrary values |
| Exact-real $H_m$ | `harmonicReal m : ℝ` by coercion from `ℚ` | value of the uninterpreted `harmonic` function | no binary64 operation is represented |
| Digamma bridge | `PositiveIntegerDigammaPremise psi eulerConstant` | four explicit equations at `k,n,x,y` | premise: for each used positive integer $m$, $\psi(m)=H_{m-1}-\gamma$; neither route proves analytic digamma truth |
| Direct term | `directHarmonicTerm k n x y` | `direct_harmonic` / `direct_xy` | coefficient vector exactly $(+1,+1,-1,-1)$ |
| Symmetric range | `symmetricRangeTerm k n x y` | `range_xy` | maximum in the upper-tail endpoint; minimum in the lower-tail endpoint |
| Source exchange | theorem arguments `x,y` exchanged | independently defined `min_xy/max_xy` and `min_yx/max_yx` | proves arithmetic symmetry only, not enclosing-estimator permutation equivariance |
| KSG exclusive count | `exclusiveArgument count = count + 1` | `exclusive_x = nx + 1`, similarly for `y` | $k-1\leq n_x,n_y<n$ maps to $k\leq x,y\leq n$ |
| Ehrlich anchor-inclusive count | `inclusiveArgument count = count` | `inclusive_argument_x = inclusive_x`, similarly for `y` | $k\leq x,y\leq n$ is passed directly; this does not prove the runtime generated such a count |

The common estimator domain is

```text
n >= 2
1 <= k < n
```

with either the exclusive KSG count domain

```text
k - 1 <= nx < n
k - 1 <= ny < n
x = nx + 1
y = ny + 1
```

or the anchor-inclusive Ehrlich domain

```text
k <= x <= n
k <= y <= n.
```

The SMT scripts use mathematical `Int` and exact `Real`; their assertions imply nonnegative
indices in the displayed domains. They contain no quantifier, floating-point sort, array,
recursive function, generated fixture, Rust source, or PID object.

## Lean route `R-LEAN-FORMAL`

Source:
`../../audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean`.

Pinned environment:

| Artifact | Identity |
|---|---|
| Lean toolchain | `leanprover/lean4:v4.32.0` |
| Lean runtime | `Lean 4.32.0`, commit `8c9756b28d64dab099da31a4c09229a9e6a2ef35` |
| `audit/formal/lean/lean-toolchain` | `2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e` |
| `audit/formal/lean/lakefile.toml` | `1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1` |
| `audit/formal/lean/lake-manifest.json` | `e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd` |
| proof source | `812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943` |

The checker compiles the source and audits these 14 theorem declarations:

| Theorem | Checked conclusion |
|---|---|
| `harmonic_zero` | $H_0=0$ from the exact finite-sum definition |
| `harmonic_succ` | $H_{m+1}=H_m+1/(m+1)$ for every natural $m$ |
| `direct_eq_symmetric_range` | exact direct-to-min/max range identity in the declared positive domain |
| `direct_source_swap` | direct four-harmonic source exchange |
| `symmetric_range_source_swap` | min/max range source exchange |
| `digamma_four_term_cancellation` | cancellation conditional on `PositiveIntegerDigammaPremise` |
| `exclusive_argument_predecessor` | `(count + 1) - 1 = count` |
| `exclusive_argument_bounds` | exclusive domain maps into $[k,n]$ |
| `inclusive_argument_identity` | anchor-inclusive argument is unchanged |
| `inclusive_argument_bounds` | inclusive domain remains in $[k,n]$ |
| `exclusive_direct_index_map` | `x=nx+1,y=ny+1` yields harmonic indices `nx,ny` |
| `exclusive_symmetric_range` | KSG exclusive formula has the exact source-symmetric range form |
| `inclusive_direct_index_map` | direct anchor-inclusive arguments have indices `x-1,y-1` |
| `inclusive_symmetric_range` | anchor-inclusive formula has the same exact range form |

No theorem uses a custom declaration-level assumption. The actual `#print axioms` inventory is:

- `inclusive_argument_identity` and `inclusive_argument_bounds`: empty;
- `exclusive_argument_bounds`: `propext`, `Quot.sound`;
- the remaining 11 theorems: `propext`, `Classical.choice`, `Quot.sound`.

The analytic identity is a theorem parameter packaged as the proposition
`PositiveIntegerDigammaPremise`; an empty custom-assumption inventory does not prove that
parameter. The checker pins the exact source bytes and four imports, rejects `sorry`, `admit`,
the source token `axiom`, and `unsafe`, and permits only the three listed Mathlib/Lean axioms in
the reported theorem inventories.

## SMT route `R-Z3-FORMAL`

The Z3 route was written independently of the Lean term structure. It uses pinned
`Z3 version 4.16.0 - 64 bit` and three quantifier-free `QF_UFLIRA` obligations:

| Script | Exact statement | SHA-256 |
|---|---|---|
| `ksg-digamma-cancellation.smt2` | no counterexample to four-term cancellation under four explicitly asserted digamma instances | `8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4` |
| `ksg-index-maps.smt2` | no counterexample to exclusive successor, inclusive identity, their bounds, and the induced harmonic indices | `71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1` |
| `ksg-symmetric-range.smt2` | no counterexample to min/max range reassociation or source exchange for arbitrary harmonic values | `add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9` |

For every script the checker first replaces the negated-obligation assertion by the positive
theorem assertion and requires exact `sat`. This rejects vacuous `unsat` from an inconsistent
domain. It then requires exact `unsat` for the negated obligation. No proof certificate is
independently kernel-checked; this is a pinned solver result diversified by the Lean kernel route.

## Baseline-first negative controls

`check-lean-ksg-integer-harmonic-self-test.py` compiles the unmodified baseline before requiring
all nine theorem mutations to fail in Lean. The mutations target:

1. the harmonic denominator;
2. the range maximum;
3. the range minimum;
4. the fourth digamma coefficient;
5. a doubled exclusive shift;
6. an erroneous inclusive shift;
7. an impossible strict exclusive upper bound;
8. a corrupted exclusive harmonic index; and
9. a corrupted source-swap conclusion.

`check-z3-ksg-integer-harmonic-self-test.py` runs the complete positive/negative baseline before
requiring exact `sat` from eight semantic mutants: nonzero cancellation and range offsets,
misbinding the `y` digamma premise, replacing either min or max by the left argument, a nonzero
exclusive predecessor offset, a doubled exclusive shift, and an inclusive shift.

The exact failure interpretations and residuals are retained in
`failures/formal-seams-and-negative-controls-v2.md`.

## Commands and observed result

```text
python3 scripts/check-lean-ksg-integer-harmonic.py
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 scripts/check-z3-ksg-integer-harmonic.py
python3 -O scripts/check-z3-ksg-integer-harmonic.py
python3 scripts/check-z3-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py
```

The settled replay requires 14 Lean theorems, 9/9 killed Lean mutations, three SMT positive
preflights returning exact `sat`, three negated SMT obligations returning exact `unsat`, and 8/8
SMT mutants returning exact `sat`. The final command results and hashes must be replayed on the
settled integration tree before release.

## Independence and critical cut sets

Lean and SMT have different object representations, proof mechanisms, dependencies, and failure
modes. Lean defines the universal rational finite sum and checks proof terms in its kernel. SMT
does not import that definition: it proves the cancellation/range/index algebra for arbitrary
harmonic values using a separately encoded quantifier-free formula and a pinned decision
procedure. They share no generated table, fixture, source parser, or Rust implementation.

They are not fully independent evidence for every upstream statement:

- `{positive-integer digamma premise and its source correspondence}` is the shared critical cut
  for analytic digamma truth; neither formal route closes it.
- `{human claim-to-formal object/sign/index map}` is a common-cause semantic cut. The encodings
  independently check the consequences after that map.
- `{runtime count production and compiled call-site behavior}` is the cut from exact index
  arithmetic to the estimator. Neither formal route closes it.
- `{selected binary64 prefix/range implementation}` is the cut from exact arithmetic to numerical
  behavior. Neither formal route represents it.

The same worker prepared both encodings and their integration map. Kernel/solver and encoding
diversity reduce implementation-correlated risk but do not create independent source review or
specialist human adjudication.

## Prohibited promotions

This packet supplies no evidence for:

- neighbor search, strict-interior or shell-count correctness;
- zero-radius, tie, quantized, singular, mixed-dimensional, or support behavior;
- binary64 prefix construction, reassociation error, correct rounding, or platform identity;
- KSG consistency, bias, variance, calibration, or uncertainty;
- Makkeh--Gutknecht--Wibral categorical event semantics or PID atoms;
- Ehrlich continuous shared-exclusions estimator consistency;
- Rust, Python, serial/parallel, resource, release, or consumer refinement.

The formal result is exact arithmetic used by inventoried KSG/Ehrlich paths. It is not a theorem
about another PID, and it is not a validation theorem for Wibral shared-exclusions PID.
