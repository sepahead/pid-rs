# Terminology

Status: reference list, 31 October 2026. It changes no theorem, estimator, evidence class or
publication. It gives the standard term for each name that earlier pid-rs documents coined, so
that a reader outside the project can follow them, and it fixes the terms that new and
republished documents use.

## Why this list exists

Earlier pid-rs reports used short names of their own for standard objects, for example *law* for
a probability distribution and *cumulative* for a redundancy value. A reader who knows the
mathematics but not the project cannot look these names up, and search engines and AI tools do
not know them. New documents therefore use the standard terms below, or define a project term in
plain words where it first appears. An existing report keeps its words until its next
republication, which adopts this list. Code identifiers and file names keep their spelling.

## Mathematical terms

| Earlier pid-rs name | Standard term used now | Meaning |
|---|---|---|
| law, finite law | probability distribution, distribution | Probabilities $p(z)\ge0$ that sum to one over the outcomes $z$ of finitely many variables, each with finitely many values unless continuous variables are stated. |
| anchor | reference outcome; for the k-nearest-neighbour estimator, the query point | The one joint outcome at which a pointwise quantity is evaluated. In the KSG estimator it is the sample point whose neighbours are counted. |
| cumulative | redundancy value | The value attached to a node of the redundancy lattice before Möbius inversion; it equals the sum of the atoms at and below that node. |
| net atom, net cumulative, net value | signed atom, signed redundancy value, signed value | The informative quantity minus the misinformative one. It can be negative. |
| informative block, misinformative block | informative part, misinformative part | The informative (misinformative) atoms of the whole decomposition taken together. Makkeh, Gutknecht and Wibral (2021) define the split; the informative part depends only on the joint distribution of the sources, because its events involve the sources alone. |
| component atom | informative atom or misinformative atom | One of the two nonnegative atoms whose difference is a signed atom (MGW Theorem IV.3). |
| carrier | redundancy lattice | The antichains of nonempty source sets ordered as by Williams and Beer (2010); 4, 18 and 166 nodes for two, three and four sources. |
| collapse, constant-channel reduction | replacement by a constant | The distribution obtained by giving some inputs one fixed value in every outcome while the joint distribution of the other variables is kept. |
| total movement, allocation movement | total change of the atoms | The sum of the absolute differences of the signed atoms between two distributions, in nats. |
| dependency colouring, colour, colour class | independence grouping, group | A partition of the rows, fixed before any value is seen, into groups whose rows are mutually independent. In graph terms it is a proper colouring of a dependency graph (Janson 2004). |
| radius (of an estimate) | error bound, half-width | A bound on the distance between an estimate and its target. A nearest-neighbour radius, a ball radius and a spectral radius keep their standard meaning. |
| row experiment, prefix experiment | sampling procedure | A procedure that draws rows and averages a statistic of them; the report that uses it defines it. |
| witness | example, counterexample | An exact object that proves an existence statement or refutes a universal one. In logic and model checking *witness* is standard; documents for a general reader say which is meant. |

## Process terms

| Earlier pid-rs name | Standard term used now | Meaning |
|---|---|---|
| claim packet, packet | claim record | One proposition written down before work starts, with its objects, the order of its quantifiers, its assumptions, units, the weaker statements that would not count and the observations that would refute it. |
| route | approach (or method, path) | One way of reaching or checking a claim. Several approaches count as independent only if they share no premise that can fail for all of them. |
| gate | required check | A check that must pass before a claim is made or a release published. |
| receipt | check record | A file that records which check ran, on which exact inputs and with what result. |
| custody | file record, provenance | A record of which exact files, identified by cryptographic hashes, were used, produced and kept, and where. |
| council, lens | structured review, review criterion | A review in which each reviewer writes a critique under a named criterion before seeing the others; agreement is not evidence. |
| judge, proposer | fixed check, proposing agent | A fixed check is chosen before any candidate exists and decides whether to accept it; a proposing agent, here an AI agent, produces candidates that are untrusted until a fixed check accepts them. |
| fixture | test case, fixed test data | A fixed input with its expected output, used by a test. |
| pinned | fixed to an exact version | A dependency, toolchain or commit identified exactly, for example by a version number and digest. |
| abstain, abstention | refuse, refusal | A function returns no value and states why. |
| fails closed | refuses on failure | When a check cannot be completed, the step stops instead of passing a default or a guess. |
| firewall | no-transfer rule | No result, proof or validity claim passes from one scientific object to another without a stated mapping theorem or a scoped comparison. |
| evidence class | kind of evidence | A label for what a piece of evidence establishes, such as a formal proof, an execution record or a review; [AGENTS.md](AGENTS.md) lists the kinds, which are not interchangeable. |

## Terms that keep their meaning

Some project documents use words in their standard sense, which this list does not change: a
*logic gate* (AND, exclusive or), the *validation gate* of a target tracker, a *Hamming ball*, a
*spectral radius*, a mechanical *fixture*, a network *route* and a *descriptor* in the sense of
Lyu, Clark and Raviv (2026), whose theorem concerns atoms that are functions of a recoverability
descriptor.
