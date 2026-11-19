# Weighted event counts for three categorical sources

**Sepehr Mahmoudian · 19 November 2026**

Two rows can agree on a source event without agreeing on every source. Which inclusions and positive denominators survive when three categorical sources have different alphabets? The proof covers arbitrary source and target label types, a finite set of row indices and natural multiplicities. It gives 22 statements about events and integer counts. These statements justify exact preprocessing steps for empirical shared exclusions. An elementary weighted contingency table suffices if only those counts are needed. [Makkeh, Gutknecht and Wibral](https://doi.org/10.1103/PhysRevE.103.032149) · [Part–whole order](https://doi.org/10.1098/rspa.2021.0110)

## Objects and notation

A **key** is the reference row. A **branch** lists source coordinates that must all match the key. A **family** accepts a match on any of its branches. **Disjunctive normal form** (DNF) expresses this “any of these groups, all coordinates in a group” rule. **Mass** is the sum of natural row multiplicities satisfying a predicate. All four counts below have units of multiplicity. The proof's formal objects are project-defined. [Family and order](lean/Contract.lean) · [Event and count definitions](lean/AlphabetCounts.lean)

Let $I=\{0,1,2\}$ index the source types $\alpha_i$. The target type is $\beta$, the index type is $J$, and $K\subseteq J$ is finite. Row $j$ has labels $s_{ji}\in\alpha_i$, target $t_j\in\beta$ and weight $w_j\in\mathbb N$, including zero. A key $k\in J$ need not belong to $K$ unless specified. Fix a finite family $A$ of subsets of $I$. Write $E_A(j)$ for the source event at $k$ and $G(j)$ for the target event.

$$
E_A(j)\iff\exists a\in A\;\forall i\in a:\ s_{ji}=s_{ki},
\qquad G(j)\iff t_j=t_k.
$$

Let $M(F)=\sum_{j\in K:\,F(j)}w_j$. The total, source, joint and target counts are respectively

$$
 N=\sum_{j\in K}w_j,\qquad U_A=M(E_A),\qquad
 V_A=M(E_A\wedge G),\qquad T=M(G).
$$

---

## From equality patterns to weighted events

The three source coordinates are fixed. The index type and the label types may be infinite. Filters use decidable predicates. The Boolean equality pattern requires decidable equality in each source type. The target filter also needs decidable target equality. The formal mass and total definitions carry decidable index equality. The exact binders for each name are in the source. [Proof terms](lean/AlphabetCounts.lean) · [Raw propositions](lean/CountRaw.lean)

The family order is $A\preceq B$ when every branch of $B$ contains some branch of $A$. A row matching a branch of $B$ also matches its selected subbranch in $A$. This fixes the implication direction even for families outside the usual redundancy lattice.

| Lean theorem | Exact implication or equivalence |
|:--|:--|
| `sourceEvent_antitone` | $A\preceq B$ implies $E_B(j)\Rightarrow E_A(j)$. |
| `sourceEvent_key_iff` | $E_A(k)$ holds exactly when $A$ is nonempty. |
| `sourceEvent_data_congr` | If two source assignments agree at $k$ and $j$, their events at $j$ are equivalent. |
| `dnf_eq_sourceEvent` | Put $e_i=\mathbf1\{s_{ji}=s_{ki}\}$. DNF of $A$ on the three equality bits holds exactly when $E_A(j)$ holds. |
| `mass_mono` | If $E(j)\Rightarrow F(j)$ on $K$, then $M(E)\le M(F)$. |
| `mass_le_total` | For every decidable $E$, $M(E)\le N$. |
| `key_weight_le_mass` | If $k\in K$ and $E(k)$, then $w_k\le M(E)$. |
| `mass_congr` | Agreement of weights and equivalence of events on $K$ preserve the filtered mass. |
| `total_congr` | Agreement of weights on $K$ preserves its total. |

The mass proofs use set inclusion, nonnegative summands and equality of finite sums. Distinct indices in $K$ may repeat labels. The conclusions hold for deterministic tables and require no independent draws or population law.

---

## Membership, bounds and support

For this table, “source filter” means the indices in $K$ satisfying $E_A$. “Joint filter” adds $G$, and “target filter” imposes $G$ alone. Every name has a matching independently stated type and a typed consumer with the same stem. [All 22 typed consumers](lean/CountEvidence.lean)

| Lean theorem | Premises and conclusion |
|:--|:--|
| `supported_key_source_mem` | $k\in K$ and $A\ne\varnothing$ place $k$ in the source filter. |
| `supported_key_joint_mem` | The same two premises place $k$ in the joint filter. |
| `supported_key_target_mem` | $k\in K$ suffices for target-filter membership. |
| `V_le_U` | $V_A\le U_A$ since joint membership implies source membership. |
| `U_le_N` | $U_A\le N$. |
| `V_le_T` | $V_A\le T$ since joint membership implies target membership. |
| `T_le_N` | $T\le N$. |
| `key_le_V` | $k\in K$ and $A\ne\varnothing$ imply $w_k\le V_A$. |
| `supported_key_bounds` | Add $w_k>0$ to these premises. Then $w_k\le V_A\le U_A\le N$, $V_A\le T\le N$ and $V_A>0$. |
| `counts_positive` | The same three premises imply $V_A,U_A,T,N>0$. |
| `U_antitone` | $A\preceq B$ implies $U_B\le U_A$. |
| `V_antitone` | $A\preceq B$ implies $V_B\le V_A$. |
| `counts_congr_on_support` | For $k\in K$, agreement of weights, source observations and target labels throughout $K$ preserves $U_A,V_A,T,N$. |

“Throughout $K$” includes its zero-weight indices. Values off $K$ may change freely under the stated premise. An empty family has a false source event; an empty branch inside a family makes that family's event true everywhere. An empty index set gives four zero counts.

---

## Worked example

Take the first row as key. Source 0 is a color, source 1 an integer and source 2 a Boolean. The target records a sign. These four indices represent ten observations counted with multiplicity.

| Key or row | Color | Integer | Boolean | Target | Weight |
|:--|:--|--:|:--|:--:|--:|
| Key | red | 0 | false | $+$ | 2 |
| 1 | red | 1 | true | $-$ | 3 |
| 2 | blue | 0 | true | $+$ | 1 |
| 3 | blue | 1 | false | $+$ | 4 |

Let $A=\{\{0\},\{1\}\}$ and $B=\{\{0,1\}\}$. Then $A\preceq B$. In $A$ the key and rows 1 and 2 match. In $B$ only the key matches. The target mass is $2+1+4=7$. Thus $(U_A,V_A)=(6,3)$, $(U_B,V_B)=(2,2)$, and $N=10$. Both counts decrease even as the ratio $NV/(UT)$ increases from $5/7$ to $10/7$. The proved antitonicity orders counts. Establishing a claim about a downstream logarithm or a partial information decomposition (PID) atom requires additional mathematics.

## Rust implementation and computational cost

For one fixed elementary event, a straightforward offline scan over $m=|K|$ records uses $O(m(1+|A|+\sum_{a\in A}|a|))$ comparisons and additions under unit-cost labels and weights. Four accumulators suffice, with $O(\log(2+N))$ bits per count. Arbitrary-size weights or expensive equality change the bit cost. The proof introduces no runtime API.

The stable `discrete_sxpid3_averaged` API accepts four equal-length `DiscreteMatRef` matrices of integer-coded observations, with no optional feature or fitting step. The public algorithm groups equal rows. For $q$ occupied joint states, its complete 18-node event scans visit $37q^2$ joint-state entries before inversion and averaging. Row encoding and sorting depend on the input width. The Rust path materializes row labels, subset histograms and the occupied joint table. The averaged call omits the per-state output table. The call with budget and cancellation can stop before producing an estimate. Counts above $2^{53}$ exceed the conversion contract. The report adds no timing, training, resampling or latency result. A weight in the Lean model need not fit a machine count. A proof connecting the Rust implementation, rounded logarithms and binary64 atoms to these natural numbers remains open. [Stable exports](../../../crates/pid-core/src/lib.rs) · [Implementation](../../../crates/pid-core/src/sxpid.rs) · [Time and memory by stage](../../../RUST_IMPLEMENTATION_AND_COST.md)

---

## What the original stock check established

Four immutable modules contain the shared family vocabulary, scalar specifications, proofs and typed consumers. The candidate retains its original source-only header from before compilation. The dated execution receipts below supply the later status. Nine matching definition pairs cover `Observation`, `sourceEvent`, `eqPattern`, `sourceEventDecidable`, `mass`, `N`, `U`, `V` and `T`. A tenth pair covers the generated helper for decidable source events. The observer checked its kind, owning module, two ordered universe levels, exact mapped type and body, and the exact helper reference in each parent. The helper's three permitted public predecessors are `Observation`, `sourceEvent` and `eqPattern`. [Exact specifications](lean/CountRaw.lean) · [Observer and typed consumers](lean/CountEvidence.lean)

For all 22 theorems the observer matched the type against the raw proposition, checked kinds and ownership, and collected transitive axioms. Each consumer uses the candidate theorem at its raw proposition type. The declarations `Observation` and `eqPattern` use no axioms. The paired definitions `mass`, `N` and `T` use `Quot.sound` and `propext`. The other definition pairs and helper use those axioms plus `Classical.choice`, as do all 22 proofs and consumers. The dependency table records the actual direct type and body references and transitive axiom list for each of 86 named objects, including every raw proposition. [Original declaration stream](declarations.txt) · [Supplementary dependency table](portable-run/dependencies.json)

Ordinary compilation on stock Lean 4.34.1 reported header trust **1025**, 2,292 modules and 11,448 regions. The reported lengths matched the bound disk files and their SHA-256 identities. Of these regions 11,430 reported file backing and 18 reported another backing. The original packet also bound 16,395 provider files and 19 runtime files. A separate stock `leanchecker --fresh CountEvidence` exited zero with empty streams in 59.788 seconds. It imports the named module's transitive environment and rechecks safe, nonpartial compiled declarations in a fresh kernel environment. The import header belongs to the earlier elaboration. Disk checks do not compare relocated memory bytes. The release, imported compiled inputs, kernel and observer are shared trust dependencies. [Original step observations and hashes](observations.json) · [Compact disk inventory](original-disk-inputs.json.gz) · [Stock checker](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean) · [Kernel replay](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean)

---

## Earlier outcomes and portable replay

Revision 1 stopped at three unused `DecidableEq J` instances under warnings-as-errors. These membership statements do not use that instance. Revision 2 stopped on different fully qualified names for the generated decidability helper during strict definition-body comparison. Revision 3 emitted its semantic rows but its rule required every region to report file backing. There were 21 exceptions among 11,448, and it stopped before fresh replay. Each revision retains zero accepted exports under its own rules. Revision 4 admitted both stock backing modes, required matching lengths and bound disk hashes, and completed fresh replay. The distinct historical demands for zero ordinary import trust and whole-module and intermediate-representation custody remain open. [Earlier outcomes](observations.json) · [Stock region interface](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/CompactedRegion.lean)

For an ordinary replay use Python 3.11 or later, an unmodified Lean 4.34.1 release and a prebuilt Mathlib checkout at the exact revision listed in the observations, with its recorded dependency commits. Run the following from this study's directory. Supply a new output directory. [Release](https://github.com/leanprover/lean4/releases/tag/v4.34.1) · [Pinned Mathlib](https://github.com/leanprover-community/mathlib4/tree/d13f23b723b8a846827a245b89c10fc7d3f11612) · [Replay program](replay.py)

```text
python3 -I -S -B replay_checks.py
python3 -I -S -B replay.py --lean-bin "$LEAN_BIN" \
    --mathlib "$MATHLIB" --output fresh-count-replay
```

The supplementary run reproduced the semantic stream, four compiled outputs, two executables and complete provider digest map. It recorded **11,427 file-backed and 21 other** regions. All reported sizes and disk bytes passed the same checks. On a different platform even the binary or provider digests can change. The reader reports those comparisons and requires the specified source revisions, declaration stream, module owners and checked local disk inputs. Provider acquisition is outside the command. A failure supplies no completed replay receipt. [Run receipt](portable-run/receipt.json) · [Read-only dependency query](inspection/Dependencies.lean) · [Projection controls](replay_checks.py)

The proof and raw specification share their family contract, sources and stock implementation. Model-assisted review traced definitions, premises, dependencies and failure records. No independent human or institutional adjudication was recorded. The mathematical result covers these 22 integer-count propositions. Paper correspondence, compiled Rust refinement, calibration, Programs A–E and the full estimator certificate remain separate obligations. [Full-certificate decision](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md) · [Related finite-registry controls](../finite-three-source-controls/README.md)

**Citation.** Sepehr Mahmoudian (2026), *Weighted event counts for three categorical sources*. Include the exact repository commit or release. Cite Makkeh, Gutknecht and Wibral separately for categorical shared exclusions. [Software citation](../../../CITATION.cff)
