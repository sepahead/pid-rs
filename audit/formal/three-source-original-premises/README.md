# Do the premises of the 22 original three-source checks have examples?

**Sepehr Mahmoudian · 2026**

Yes. Each first assertion in source files W01 through W22 admits two different complete assignments. In 19 files a further assignment makes the first assertion false. W14 has three such assignments. The first assertions of W01, W02 and W15 are the literal word `true`, so no assignment makes them false. The total is 44 satisfying assignments and 21 rejecting assignments, counted separately for each file. The same assignment can occur in different files. [Source identities](SOURCES.json) · [All assignments and expected outputs](observations.json)

These examples answer a question about a proof by implication. When a premise is impossible, an implication from that premise is true for every conclusion. In each of these 22 files the original solver checked a premise together with the **negation** of a conclusion. Failure to satisfy both does not by itself show that the premise can hold. This companion evaluates the premise separately at explicit inputs. It leaves the original files, their solver returns and their later proof records intact. [Original verification tool](../finite-smt39-qualification-v1/README.md) · [Current three-source decision](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md)

## Terms and inputs

**Satisfiability modulo theories (SMT)** asks whether values of specified types can satisfy a logical formula. Here the types are Boolean values, fixed-width sequences of bits and mathematical integers. SMT-LIB is the input language. A **valuation** gives each declared name a value of its type. A **ground** calculation fixes all these names. A solver reports `sat` when a model exists for the assertions it received. It reports `unsat` when they have no model. A report of `unknown` does not decide the question. A timeout, an interrupted process or a missing reply gives no completed check. An original solver status alone supplies no independently checked proof. [SMT-LIB reference, version 2.7](https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf)

Each source file declares the same 25 names. The seven-bit words `a,b,c` encode families. The three-bit words `q,h,x` range from 0 to 7. The four-bit words `k,r` range from 0 to 15. The name `tau` is Boolean. The 16 weights `w0` to `w15` are arbitrary integers until a premise restricts them. The terms in these files describe symbolic inputs. They do not describe sampled trials, independent observations or an estimated population. [Original encoder](../finite-smt39-qualification-v1/fin3_smt.py)

A **branch** is a nonempty subset of the three labelled source positions 0, 1 and 2. A **family** is a set of branches. Its seven bits select among the seven nonempty subsets. A branch with source mask value `j`, from 1 to 7, uses family bit `j−1`, with the lowest bit numbered 0. For example, family code 1 selects the single branch containing source 0. A **valid family** is nonempty and has no two distinct branches with one contained in the other. Such a family is an **antichain**. The source relation `leq(a,b)` says that every branch of `b` contains at least one branch of `a`. [Source definitions](../finite-smt39-qualification-v1/raw/W12-order-event-inclusion/generator.stdout.smt2) · [Set-based reader](../finite-smt39-qualification-v1/model_checker.py)

To interpret a source event, let a bit equal 1 when a source coordinate matches the selected cell. Require all bits named by a branch to equal 1. Accept a match when at least one branch meets this requirement. This **disjunctive normal form (DNF)** uses AND within a branch and OR across branches. It is **monotone** because changing a match bit from 0 to 1 cannot undo acceptance. Its **canonical** form keeps exactly the minimal sets of matching coordinates that give acceptance. For example, “source 0 matches, or both sources 0 and 1 match” has the same truth table as “source 0 matches.” The latter is its canonical form. The empty family gives constant false. A family containing an empty branch gives constant true. A nonconstant monotone Boolean function has a unique family of nonempty minimal true sets. Any accepted set contains a minimal one because the source set is finite. The 18 valid families for three sources represent exactly these nonconstant functions. The two constants are outside this carrier. The uniqueness statement uses all eight abstract matching patterns. If an observed support omits patterns, two different families can agree on every observed row. This is the family logic used here. An algorithm to estimate information is a different object. [Logical construction of Gutknecht, Wibral and Makkeh](https://doi.org/10.1098/rspa.2021.0110) · [Project derivation](../lean-sx-dnf-order/EXPOSITION.md) · [Exact original W02 result](../../research/three-source-w02/README.md)

## What each first assertion requires

The identifiers W01 through W22 name original source files. A mask is a word whose set bits select elements. A family with code zero has no branches. The table groups only identical first assertions or cases with the same order rule. Each row's complete, separate registration includes its original second assertion digest. [Original input paths and SHA-256 digests](SOURCES.json) · [Per-file premise text and valuations](observations.json)

| Original files | Requirement | Retained rejecting case |
|---|---|---|
| W01, W02, W15 | Literal true | Impossible for this premise |
| W03, W09–W11, W13 | Valid family `a` | Empty family |
| W04 | Valid `a,b`, with each below the other | Order holds in one direction only |
| W05 | Valid `a,b,c`, with `a` below `b` and `b` below `c` | Reversed order |
| W06–W08, W17–W22 | Valid `a,b` | Empty family |
| W12 | Valid `a,b`, with `a` below `b` | Reversed order |
| W14 | Valid `a`, all weights nonnegative, positive weight at key `k` | Empty family, unoccupied key, or a negative weight |
| W16 | Nonzero three-bit mask `q` | Zero mask |

## Worked example for W14

Let `s0,s1,s2` be three binary source coordinates and let `t` be a binary target. The cell index is `8s0 + 4s1 + 2s2 + t`. A **key** is a selected cell. Fix family `a=1` and key `k=0`. A cell matches the source event when `s0=0`. Its target matches the key when `t=0`. In the sparse recorded example the occupied cells 0, 1, 2 and 8 have counts 2, 1, 3 and 4. All other counts are zero. An occupied cell has positive count. [Original W14 premise and definitions](../finite-smt39-qualification-v1/raw/W14-supported-mass-bounds/generator.stdout.smt2)

| Quantity | Cells or counts to add | Value in counts |
|---|---|---:|
| `N`, total weight | 2 + 1 + 3 + 4 | 10 |
| `U`, weight matching the source event | Cells 0, 1 and 2 give 2 + 1 + 3 | 6 |
| `V`, weight matching source and target | Cells 0 and 2 give 2 + 3 | 5 |
| `Tmass`, weight matching the target | Cells 0, 2 and 8 give 2 + 3 + 4 | 9 |
| `weight(k)`, count at the key | Cell 0 | 2 |

The key is occupied, every count is nonnegative and the family is valid. In the three separate rejected assignments, change only the family to 0, only the key to the unoccupied cell 3, or only `w9` to −1. The last value is a signed logical input. It has no count interpretation. A second calculation uses counts 2, 3, 5 and 7 at cells 0, 1, 8 and 9 with the same key and family. The five quantities become 17, 5, 2, 7 and 2. These examples exhibit the assumptions in a finite count calculation. They add no conclusion about a sensor, a population or a PID estimate. [Complete typed assignments](observations.json) · [Independent example and checker](replay.py)

## How to reproduce the result

Run these commands from the repository root with Python 3.11 or later. The first command requires only the Python standard library and the registered source files. For the second command install stock Z3 4.16.0, 64-bit, and make its `z3` executable available on the command path. The third command repeats the native checks with Python optimization enabled. Each successful command writes one JSON result and exits with status zero.

```sh
python3 -I -S -B audit/formal/three-source-original-premises/replay.py --self-test
python3 -I -S -B audit/formal/three-source-original-premises/replay.py --self-test --z3 z3
python3 -I -S -B -O audit/formal/three-source-original-premises/replay.py --self-test --z3 z3
```

The checker binds every source file to its digest. It reads the fixed definitions, the first assertion and the separate second assertion in their original order. It binds every one of the 25 names in each test, including unused names. For each source row it checks two distinct positive valuations. For each nonliteral premise it also checks the required rejection. It interprets the first assertion with the original set-based reader. In native mode it sends the original definitions, the first assertion as a named Boolean expression and all 25 fixed assignments to Z3. The solver first reports `sat` for the fixed assignments. The **separate value** of the named expression then gives `true` or `false`. An assignment that makes the premise false can therefore have the native pair `sat, false`. The 65 original query digests and native output digests must match the capture. Four further native queries test the second W14 example and three changes to its assumptions. [Exact checker](replay.py) · [Exact projected captures](observations.json)

The named refusal tests include altered source bytes, exchanged assertions, duplicate declarations, a missing weight, a wrong type, a missing native reply and an `unknown` response. Keep the successful source check, the historical solver response, and a stock proof-assistant check of any separate theorem as distinct evidence. The original 39-case package contains 34 retained SAT witness projections and its own controls. This companion addresses only the first assertion of each of the 22 original W rows. [Original tool and evidence boundary](../finite-smt39-qualification-v1/README.md) · [Separate W02 proof](../../research/three-source-w02/README.md)

## Rust implementation and computational cost

This is an offline, project-defined verification tool. The inputs are finite symbolic assignments, not a fitted or evaluated count dataset. The executable route uses Python integer arithmetic, a pinned set interpreter and optional stock Z3. There is no Rust API, feature gate, estimator, training step or resampling procedure for this check. The original model has three binary sources, one binary target and 16 cells. A valid nonnegative table can occupy at most 16 cells. Arbitrary signed integer assignments have no sample size. For fixed three-source dimensions, evaluating a table sum reads at most 16 weights. Integer operand size affects arithmetic time and memory. There are 22 source parses, 65 captured assignments and four extra W14 evaluations. The solver is started once for each native query. It has a 17-second internal limit and a 20-second process timeout per query. Its version check has an eight-second timeout. A failed query aborts the run. The checker loads each original file and the small capture in memory. No portable memory ceiling or runtime benchmark is claimed. [Implementation](replay.py) · [Original tool cost and limits](../finite-smt39-qualification-v1/README.md)

## Sources and contribution

The new contribution is a source-bound collection of explicit premise examples and failures for 22 retained files, with a native replay and a worked count table. The first-assertion study uses known source inputs and reported totals. A separate implementation reproduced the typed queries from the original files and checked the complete native replies. Both implementations share the original solver semantics and source data. These are finite execution observations. They add no proof of the 22 original conclusions and no human or institutional review.

Cite Sepehr Mahmoudian (2026), *Do the premises of the 22 original three-source checks have examples?* Include the exact repository commit or release. Cite the software separately. [Software citation](../../../CITATION.cff) · [Original source registration](SOURCES.json) · [Public claim decision](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md)
