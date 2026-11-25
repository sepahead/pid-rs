# Sources, formal scope and reproduction

**Sepehr Mahmoudian · 25 November 2026**

## Scientific object and scope

The primary object is one finite-sample harmonic term in the continuous shared-exclusions estimator of Ehrlich et al. It has two scalar sources, a scalar target, an identity transform, raw common numerical scales, a source minimum and a joint maximum. The comparator is the scalar source and scalar target version of KSG estimator 1 for mutual information. The common strict count arithmetic applies separately to these two distance constructions. Their population meanings and support conditions differ. The source revision used for the first paper is arXiv:2311.06373v3, PDF SHA-256 `cf785c96d24a49d793e835d70e26d94ffe67b9c71251265e6e4040753ec8f563`. The KSG source is arXiv:cond-mat/0305641v1, PDF SHA-256 `bfebb709bc76f62527f618d026f4b775801c25482b96daf78859806cd92346c4`. The density argument uses the Lebesgue differentiation theorem in the row dimension. [Ehrlich et al.](https://doi.org/10.1103/PhysRevE.110.014115) · [Kraskov et al.](https://doi.org/10.1103/PhysRevE.69.066138) · [Tao, Theorem 1.6.19](https://terrytao.wordpress.com/wp-content/uploads/2012/12/gsm-126-tao5-measure-book.pdf)

The existing W7 calculation gave a conditional count inequality and optimized the harmonic terms on an integer outer domain. This study gives constructive realizations in the two stated scalar geometries, their open-set classification, positive probability under a common independent row density, both sample-mean upper extrema, the exact three-row first-neighbour sample minimum, and a strictly stronger lower mean bound whenever the first neighbour is used and the sample size is three more than a multiple of four. It does not supply a general law for all sample-mean minima or a source-to-machine refinement theorem. A report from fixed test rows exercises the program. It does not fit an empirical categorical law, train a classifier or measure sensor performance. [Earlier W7](../../../claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md#w7--conditional-runtime-count-set-lemma) · [Worked derivation](README.md)

## What the kernel checked

The formal model uses finite lists of nonnegative integer distance triples, the minimum of two source distances, the maximum of that result and the target distance, and Boolean strict comparisons. The anchor is implicit at zero. A positive radius has exactly one row on its shell and exactly one fewer interior row than its rank. The public sources contain five named declarations.

An **axiom** is a statement the proof checker accepts without a proof. The table names three axioms used by these declarations or their dependencies. Propositional extensionality (`propext`) makes two propositions equal if each implies the other. Classical choice (`Classical.choice`) supplies an element of a type when the type is known to have an element. Quotient soundness (`Quot.sound`) makes the classes of two representatives equal if the specified relation holds between them. [Propositional extensionality](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Init/Core.lean#L1607) · [Classical choice](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Init/Prelude.lean#L809) · [Quotient soundness](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Init/Prelude.lean#L4776)

| Declaration | Predicate | Transitive axioms printed by Lean |
|---|---|---|
| `W7.inner_pair` | The strict joint event is the conjunction of both strict marginal events. | `propext`, `Quot.sound` |
| `W7.counts` | On every finite list, count both Boolean tests, compare with each count, and bound their sum by the list size plus their joint count. | `propext`, `Classical.choice`, `Quot.sound` |
| `W7.necessary` | The counts of every admitted integer list satisfy the triangle inequalities. | Same three axioms |
| `W7.constructed` | The four prescribed group sizes produce a witness of the stated length and counts at radius two. | Same three axioms |
| `W7.attainable_iff` | For every positive rank below the sample size, a list and radius exist exactly for the integer pairs in the triangle. | Same three axioms |

The stock compiler and `leanchecker --fresh` checked the model, proof and typed observer. Three typed uses consume the general statements. Eight additional examples test inhabited and rejected configurations with `decide +kernel`. A separate source asserts a false count for a valid single-row shell. The stock compiler must refuse that precise assertion. An empty sample, zero radius, tied shell and wrong count are explicit adverse cases. The concrete examples include each of the three possible pairs for two observations, and the first anchor of the five-row two-source example. The witness lemma treats every admissible class size, so the general existence statement has actual witnesses. [Model](lean/Model.lean) · [Proof](lean/Proof.lean) · [Typed uses and examples](lean/Observer.lean) · [False statement](lean/Contradiction.lean)

The fixed system was unmodified stock Lean 4.34.1, source revision `5045d0056413266e57c625dcd7c365b10e377c52`. The first run used 3,257 fixed runtime files. The selected proof source SHA-256 is `d7d69e2fba69115b87aff44c548dfed554cc6dc75e0099a3e103a442a3ed998b`. The selected proof object on that host has SHA-256 `aec2e05b295a0cf8331915961e73cc81614ef7bde68c70685e319bc29273c6d9`. The compiler loads the supplied built imports. The stock fresh reader imports the complete module, opens a fresh kernel environment and replays the safe, nonpartial constants in its map. An axiom supplies its declared type, not a proof. Axiom inventories for the five named theorems are given above. Reproduction trusts the stock binaries, the supplied runtime, the platform and ordinary file access. [Stock fresh reader](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean#L36-L38) · [Declaration replay](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean#L176-L188)

The initial display of the five proofs contains eleven omission symbols in the witness proof. A second stock consumer turns on deep-term and proof printing. Its output has 381,708 bytes, contains all five declaration displays and has no omission symbol. The compiled proof object and kernel recheck bind the formal terms. A printed display can still omit ordinary implicit arguments under Lean's normal notation. The portable replay checks both distinct outputs and the explicitly printed axiom lists. The second reader cannot change any theorem. [Original display](proof-display.txt) · [Expanded display](expanded-proof-display.txt) · [Expanded reader](lean/FullDisplay.lean) · [Bound source hashes](proof-inputs.json)

Two development launches used one frozen task and one stock judge. The first stopped because the proof gave a redundant simplification argument and the compiler treated that warning as an error. Removing only that argument gave the second proof. The judge stopped on its first full pass. This formalization followed the known ordinary argument. AI-assisted readers prepared separate first accounts before comparing their individual geometric arguments. Later readers used common publications, model classes, theorem statements, local hardware and software. Separate implementations and stock replays can reveal specific errors. Multiple model reviews do not establish human, institutional, data, custody or complete semantic independence. There is no claim of independent human scientific review or formal verification of all conclusions in the article.

## Exact finite programs

| Data or computation | Scope |
|---|---|
| `finite.py` | The radius-two grid contains every multiset of up to four nonanchor rows in two or three dimensions with coordinates in {1,2,3}. It checks both allowed ties and the case with no same-row boundary equality. |
| `integer-witnesses/construction.py` | One finite construction for each of 486 allowed labels at sizes 2 through 9. The independent judge reads exact row arrays for scalar KSG and two-source Ehrlich, including the other anchors. There are 36 exceptional and 450 open labels. |
| `integer-witnesses/upper-mean.py` | The separate producer gives 28 integer arrays at sizes 2 through 15. The judge checks 420 means and 4,480 row contributions over both objects and both upper constructions. |
| `whole_upper.py` | A second exact all-rank calculation uses a different perturbation with the same powers-of-two mechanism. It checks 572 row and rank combinations and 66 means per object and construction for sizes 2 through 12. |
| `three_rows.py` | Checks two separately derived three-row experiments in two geometries. All 27 assignments of less than, equal or greater than to the three undirected edges have at most two vertices incident to both strict signs. |
| `two_arm.py` | Reconstructs each of five raw rows, exact ranks, counts, local terms and mean. Compares six quantiles for each of twelve series, both counts of undefined slopes, the mean and the two reported refusals with the native output. |

The original 2-through-9 finite task source has SHA-256 `69932d372f52dcd94a8bff9799ad275112028e5b75aa1d6970325c38e366341f`. It specified the sample sizes, ranks, source/target scores, label coverage, finite inputs and scope. The subsequent constructed arrays and formal proof are different objects. Both array studies had one candidate each, followed by deterministic checks. The triangle producer, upper producer and original shared judge have hashes `9f0f4ebd0c4295c23410016b003652769396206d7e5915cc77b0a0f73c87dc69`, `c390139cbc4441edfa6450cc667121179e4d9a819484038efed172e92ceb8db7` and `f29556f2645580b61d613bb6c492d8909b8647fd49aa3ca7c49042644a804bc4`. The generated array SHA-256 values are `4b8ca3f4d57b8578dcdf3aa8d769f3d4350ebee9d4ee79e20c531f4dfd3e810d` and `251a82da3494b386bd94d46d9bf58fd427c71e2eec3cb1c00638e42103b38749`. Both finite outputs are supplied. [Construction](integer-witnesses/construction.py) · [Upper samples](integer-witnesses/upper-mean.py) · [Original judge](integer-witnesses/geometry-judge.py) · [Triangle result](integer-witnesses/triangle-result.json) · [Upper result](integer-witnesses/upper-result.json)

The sample checks were developed after exposure to the count classification. They test deterministic predicates on their covered inputs. The whole-mean arguments and three-row witnesses were examined independently before their written derivations were compared. The five-row exact reader uses the same statistical object and observations as the native call. It checks integer arithmetic independently of the Rust calculation. The reported binary64 mean differs slightly from the exact rational value. No new estimator, hypothesis test, bias comparison, or validation dataset was selected here.

## The five-row diagnostic record

For these five rows the report gives six order statistics in each of twelve series. They cover the joint radius, the union and target counts, each source count, the overlap count and ratio at the full and half radius, both source slopes, and the local term in nats. The reader calculates all 72 values from the input coordinates. It also checks the two counts of undefined slopes, the sample size, the rank, the mean and the two refusal flags. A slope is defined only when both of its source counts are positive. Each defined slope in this example is zero.

The original reader checked seven series. Five altered inputs passed its comparison. These used a Boolean for a count, a noninteger count close to an integer, two different types for a refusal flag, or two conflicting values for the mean. A control with a wrong mean was rejected. The replacement requires each field to have its declared type, each property to occur once, and each numerical value to be finite. The count, radius, ratio and slope comparisons are exact for these five rows. The local terms and the sample mean must agree with their rational values within an absolute tolerance of one trillionth of a nat. The original native report passes. These checks do not bound numerical error on other samples.

## Reproduce

Run the existing finite readers and their invalid-input controls from this directory. Each command must finish successfully. The two outputs must match. Python uses only its standard library. A call with `--self-test` requires the actual array judge to refuse eight altered inputs with the specified errors. It also requires the five-row report reader to refuse 18 altered reports.

~~~sh
python3 -I -S -B check.py --self-test
python3 -O -I -S -B check.py --self-test
~~~

Use a stock Lean 4.34.1 installation for the formal proof. Substitute its unpacked directory for `LEAN_ROOT`. Optional `--evidence` requires a new output directory. It preserves sources, compiled objects and separate standard output and error.

~~~sh
python3 -I -S -B replay.py --toolchain LEAN_ROOT --evidence new-lean-evidence --self-test
~~~

In a complete repository checkout the native client uses the public `pid-core` crate and the locked Rust dependencies. An offline build requires these dependencies in the local Cargo cache. The example uses one build job and one Rayon worker. Native source and locked dependencies are given. Separate normal and optimized Python runs can check the immutable supplied output without installing Rust.

~~~sh
CARGO_BUILD_JOBS=1 CARGO_INCREMENTAL=0 CARGO_PROFILE_DEV_DEBUG=0 RAYON_NUM_THREADS=1 \
  cargo run --manifest-path native/Cargo.toml --locked --offline -j 1 --quiet > represented-new.json
python3 -I -S -B two_arm.py represented-new.json
~~~

Using the public library at source revision `ef705d1ed3410fd9fbbf4920cb4643f6a5140a2f` the portable native client reproduced the full returned diagnostic record byte for byte. The clean native build-and-run took 20.61 seconds with sampled maximum process-group memory 518,242,304 bytes on an Apple arm64 host. This includes building dependencies and starting the binary. No isolated estimator runtime was measured. Proof, numerical and program performance evidence apply to their own workloads.

Generate the figure as a text-bearing vector. The source fixes each coordinate, graph mark, scale and legend of the two panels. A vector PDF can be produced with librsvg.

~~~sh
python3 -I -S -B figures/draw.py --output counts-and-distances.svg
SOURCE_DATE_EPOCH=1795564800 TZ=UTC rsvg-convert -f pdf -o counts-and-distances.pdf counts-and-distances.svg
~~~

**Citation.** Sepehr Mahmoudian (2026), *Which strict neighbour counts can occur?* Include the exact repository commit or release. [Study](README.md) · [Software citation](../../../CITATION.cff)
