# Terminology

This guide explains terms used in pid-rs reports. It includes established mathematical
terms such as *probability law*, *witness* and *graph colouring*, as well as local expressions
such as *allocation movement*. The middle column gives wording a report can use with a
reader outside the field. Define a technical term on first use. Keep its usual meaning when
the mathematical argument depends on it. Code identifiers and file names retain their spelling.

## Mathematical terms

In partial information decomposition (PID), sources are the variables that supply information
about a target variable. A node identifies a collection of source sets. Its redundancy value
is the information shared by those sets about the target under a specified measure. In the
finite categorical construction of Makkeh, Gutknecht and Wibral (MGW), that value and the atoms
have informative and misinformative parts. [Williams and Beer, §III](https://arxiv.org/abs/1004.2515v1) · [Makkeh, Gutknecht and Wibral, §§III–IV](https://arxiv.org/abs/2002.03356v5)

| Term in reports | Wording for readers | Meaning here |
|---|---|---|
| law, finite law | probability distribution, finite distribution | The law of a random variable $X$ assigns each measurable set of values $B$ the probability $P(X\in B)$. On a finite set of outcomes it is described by nonnegative masses $p(z)=P(X=z)$ that sum to one. For a uniform draw on the real interval $[0,1]$, each point has probability zero and the interval has probability one. [Durrett, §1.2](https://services.math.duke.edu/~rtd/PTE/PTE5_011119.pdf) |
| anchor | reference outcome or query point | For pointwise information this is the observed joint outcome where the quantity is evaluated. In the Kraskov–Stögbauer–Grassberger (KSG) estimator the query is the sample point about which neighbours are counted. [KSG](https://doi.org/10.1103/PhysRevE.69.066138) |
| cumulative | redundancy value | The redundancy value at a node is the sum of the atoms at that node and all nodes below it. Möbius inversion recovers each node’s atom by subtracting the contributions from strictly lower nodes. [Williams and Beer, §IV, Eq. (6)](https://arxiv.org/abs/1004.2515v1) |
| net atom, net cumulative, net value | signed atom, signed redundancy value, signed value | In categorical shared exclusions, subtract the misinformative part from the corresponding informative part. A signed redundancy value or atom can be negative. |
| informative block, misinformative block | informative part, misinformative part | All informative atoms, or all misinformative atoms, of a decomposition considered together. In categorical shared exclusions the informative part uses only source-event probabilities. At a fixed source outcome, and after averaging, it is determined by the joint distribution of the sources. [MGW, Eqs. (6)–(8)](https://arxiv.org/abs/2002.03356v5) |
| component atom | informative atom or misinformative atom | Each part has its own atoms. In categorical shared exclusions both component atoms are nonnegative at every joint outcome of positive probability. Their difference is the signed atom. [MGW, Theorem IV.3](https://arxiv.org/abs/2002.03356v5) |
| carrier | underlying set of lattice nodes | A node is a nonempty family of nonempty source sets in which no distinct member contains another. These families form the carrier. The redundancy lattice also specifies their order. Write $\alpha\preceq\beta$ when each set in $\beta$ contains some set in $\alpha$. There are 4, 18 and 166 nodes for two, three and four sources, respectively. [Williams and Beer, §III, Eq. (5)](https://arxiv.org/abs/1004.2515v1) · [Order and its carrier](https://www.isabelle.in.tum.de/website-Isabelle2021/dist/library/HOL/HOL-Algebra/Order.html) · [Node counts](MATHEMATICAL_RESULTS_GUIDE.md#lattice-positions-versus-audit-coordinates) · [Source positions and maximal uncovered agreement patterns](audit/research/finite-three-source-controls/README.md#how-many-agreement-patterns-can-remain-maximal) |
| collapse, constant-channel reduction | replacement by a constant | The distribution obtained by giving some inputs one fixed value in every outcome while the joint distribution of the other variables is kept. |
| total movement, allocation movement | total change of the atoms | Match the same lattice nodes in two distributions, take the absolute difference of their signed atoms at each node and add the differences. With natural logarithms the total is in nats. [Source-partition calculation](audit/research/source-coupling-compression/EXPOSITION.md) |
| dependency colouring, colour, colour class | grouping of mutually independent rows, group | A proper colouring of a valid dependency graph assigns different colours to adjacent rows. Within each colour class the rows are mutually independent. Rows of different colours can depend on each other. The repository’s concentration bound specifies when the grouping must be fixed and which row distributions it covers. [Janson, §2](https://www2.math.uu.se/~svantejs/papers/sj150.pdf) · [Sampling assumptions](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md) |
| radius (of an estimate) | error radius or interval half-width | A radius gives a distance from the estimate. An interval symmetric about the estimate has that radius as its half-width. For a statistical error bound, state the sampling assumptions and the probability with which the error is within the radius. Nearest-neighbour radii, ball radii and spectral radii have their usual meanings. [Sampling bound](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md) |
| row experiment, prefix experiment | sampling procedure on observation rows | A row is one joint observation. A prefix consists of the first specified number of rows in their sampling order. The finite-prefix study draws an anchor and later rows, computes one statistic from the block and studies its expectation under repeated draws. [Definition of the statistic](audit/formal/lean-prefix-mgw-mean/EXPOSITION.current.md) |
| witness | witness or counterexample | A witness to $\exists x\,P(x)$ is a particular $x$ for which one can establish $P(x)$. A counterexample to a universal claim meets its assumptions and violates its conclusion. State which claim the example settles. [Theorem Proving in Lean 4, §4.4](https://lean-lang.org/theorem_proving_in_lean4/Quantifiers-and-Equality/) |

## Process terms

| Term in reports | Wording for readers | Meaning here |
|---|---|---|
| claim packet, packet | claim record | One proposition written down before work starts, with its objects, the order of its quantifiers, its assumptions, units, the weaker statements that would not count and the observations that would refute it. |
| route | approach to checking a claim | State which aspects of two approaches are independent. Separately written programs can check the same data against the same mistaken specification. Report how the meaning was specified, who supplied the implementation and data, who controlled the evidence, and the reviewers’ institutional relationship. Identify any shared input or assumption that could invalidate both results. [Review contract](RESEARCH_READER_AND_VERIFICATION_CONTRACT.md#cited-glossary) · [Knight and Leveson](https://doi.org/10.1109/TSE.1986.6312924) |
| gate | required check | A check that must pass before a claim is made or a release published. |
| receipt | check record | A file that records which check ran, on which exact inputs and with what result. |
| custody | control and preservation of the evidence | Record who held or transferred the evidence, which version they held and how its recovery was checked. A digest can identify particular bytes. Provenance describes how the evidence came into being, including the inputs, people and processes involved. [Repository durability rules](AGENTS.md#branchworktree-durability-and-closure-mandatory) · [W3C PROV](https://www.w3.org/TR/prov-dm/) |
| council, lens | structured review, review criterion | A council is a group of reviewers. A lens is one question a reviewer applies, such as whether a theorem includes its support assumptions. Record each initial critique before sharing conclusions, and cite the evidence that resolves disagreements. One reviewer can apply several criteria. |
| judge, proposer | check, candidate author | The proposer supplies a candidate. The judge checks a stated acceptance rule and records the outcome, including an incomplete check. For a prospective attempt, fix the rule and protect the judge before the proposer sees the task. When checking an existing proof, disclose prior exposure and state exactly what the later check establishes. [Research-integrity controls](AGENTS.md#ai-assisted-candidatejudge-isolation-and-research-integrity-controls-mandatory) |
| fixture | test data or test setup | A fixture supplies repeatable inputs or setup for a test. A test can compare its output with an expected value, check a property or expect a specified error. [Python testing terminology](https://docs.python.org/3/library/unittest.html) |
| pinned | fixed to an exact version | A dependency, toolchain or commit identified exactly, for example by a version number and digest. |
| abstain, abstention | withhold an estimate or decision | The procedure withholds the requested scientific value and reports the reason. For example, a run-log result can contain an abstention status and its reason. [Structured scientific outcomes](crates/pid-runlog/src/scientific.rs) |
| fails closed | refuses on failure | When a check cannot be completed, the step stops instead of passing a default or a guess. |
| firewall | no-transfer rule | No result, proof or validity claim passes from one scientific object to another without a stated mapping theorem or a scoped comparison. |
| evidence class | kind of evidence | A label for what a piece of evidence establishes, such as a formal proof, an execution record or a review; [AGENTS.md](AGENTS.md) lists the kinds, which are not interchangeable. |

## Terms that keep their meaning

Some project documents use words in their standard sense, which this list does not change: a
*logic gate* (AND, exclusive or), the *validation gate* of a target tracker, a *Hamming ball*, a
*spectral radius*, a mechanical *fixture*, a network *route* and a *descriptor* in the sense of
Lyu, Clark and Raviv (2026), whose theorem concerns atoms that are functions of a recoverability
descriptor.
