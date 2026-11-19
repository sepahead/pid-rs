# The eighteen families in the original three-source count test

**Sepehr Mahmoudian · 19 November 2026**

Could any assignment satisfy the two assertions in the archived count test labelled W02? Both solvers reported that none could. Their original output contains a status word, without a proof. A later check with the stock Lean 4.34.1 kernel establishes unsatisfiability for the formal reading of this particular input. This matters because even a correct count can test a weaker property than a reader expects. [Original input](../../formal/finite-smt39-qualification-v1/raw/W02-exactly-18-distinct/generator.stdout.smt2) · [Historical solver observations](../../formal/finite-smt39-qualification-v1/README.md)

## What the count means

A **source** is one of three labelled input variables. A **branch** is a nonempty subset of their positions. A **family** is a collection of branches. An **antichain** has no two distinct members for which one contains the other. In partial information decomposition (PID), the redundancy lattice of Williams and Beer uses nonempty antichains of nonempty branches as its nodes. The source file represents a family by seven bits, one for each branch. This is a finite combinatorial question. It uses no target variable, probabilities, samples, estimator or information units. The cited papers supply the node concept and its logical interpretation. The numerical encoding and test are project-defined. [Williams and Beer, Section III](https://arxiv.org/abs/1004.2515v1) · [Gutknecht, Wibral and Makkeh](https://doi.org/10.1098/rspa.2021.0110) · [Project registry](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md)

Let $m$ be a seven-bit family code, written as an integer from 0 to 127. Write $v(m)=1$ if its family is nonempty and is an antichain, and $v(m)=0$ otherwise. Write $c_1,\ldots,c_{18}$ for the eighteen literal codes printed in the input. The first assertion is true. The second asserts the negation of

$$
\left(\sum_{m=0}^{127}v(m)=18\right)
\quad\text{and}\quad
\left(c_i\ne c_j\ \text{for every }1\le i<j\le18\right).
$$

These are two different conditions. Pairwise distinctness says that the listed codes differ. Identifying this list with all valid families would also require showing $v(c_i)=1$ for each index. A list with one replaced by a distinct invalid code could still pass both conditions. The check should be cited for the conjunction it contains. [Exact second assertion](../../formal/finite-smt39-qualification-v1/raw/W02-exactly-18-distinct/generator.stdout.smt2)

---

## Counting by hand

There are seven one-member antichains, one for each nonempty subset. Of the 21 unordered pairs of distinct nonempty subsets, twelve are comparable. Six pair a singleton with a containing doubleton, three pair a singleton with the three-element set, and three pair a doubleton with that set. The remaining nine pairs form antichains.

A singleton and an incomparable doubleton must be complements. Every other singleton is contained in that doubleton. Every other doubleton contains the first singleton. The full three-element set contains them both. Such a mixed pair therefore admits no third member. There are exactly two three-member antichains, the three singletons and the three doubletons, and neither admits another member. The total is $7+9+2=18$. This direct count can be checked without choosing a PID functional. It supplies the first conjunct. Comparing the eighteen literals supplies the second.

## Reading the file

Here **SMT** stands for satisfiability modulo theories. An assertion is a Boolean condition. A **valuation** assigns a value of the declared type to each constant. An input is **unsatisfiable** if every valuation fails at least one asserted condition. The accepted source fragment uses Boolean values, mathematical integers and fixed-width bit vectors. A rank specifies a symbol's input and output types. [SMT-LIB 2.6 language reference, 20 September 2024](https://smt-lib.org/papers/smt-lib-reference-v2.6-r2024-09-20.pdf)

Two source readers matched all 43,261 bytes and all 29,795 consecutive token, comment and whitespace spans. They recovered the same 89 commands, including 25 constant declarations, 57 nonrecursive function definitions and the two assertions. One writer produced the literal Lean declaration. A different reader parsed that declaration back into the same complete typed tree. Fixed-width arithmetic and integer arithmetic retain their separate meanings. Thirteen synthetic inputs were accepted and twelve malformed inputs were refused. These checks establish a translation comparison for this file. A general proof of the readers' correctness would be a separate result. [Source reader](source_reader.py) · [Constructor writer](source_writer.py) · [Lean literal readback](lean_literals.py)

---

## What Lean checked

The model represents an unsuccessful evaluation separately from either Boolean answer. Sixteen of the 25 declared constants range over all mathematical integers. One constant is Boolean and eight are bit vectors (three seven-bit, three three-bit and two four-bit). Neither assertion depends on the values assigned to those constants. The checker rejects a repeated formal parameter or an ill-typed operation. It accepts a well-typed assertion that evaluates to false. The checker retained the complete script, including definitions the assertions do not call. [Typed data](lean/W02OriginalData.lean) · [Evaluator and satisfaction](lean/W02Semantics.lean)

The four named propositions say that the script is well formed, every valuation evaluates the two assertions successfully to true followed by false, no valuation satisfies both, and at least one valuation exists. The last statement rules out an empty assignment domain. In the proof of the second statement, introducing an arbitrary valuation leaves an equality that the kernel checks by reduction. The third statement applies the proved rule that a successful result list containing false cannot satisfy the conjunction. [Proofs](lean/W02Candidate.lean) · [Four typed uses](lean/W02Consumer.lean)

The original run compiled five modules and replayed each with the stock fresh checker. An eleventh call recorded the full types and proof expressions, their declaration names, module owners, direct references and transitive axiom sets for the four theorems and their four typed uses. The nonempty-domain theorem and its typed use depend only on propositional extensionality. The other six also depend on classical choice and quotient soundness. [Eight complete declaration records](declarations.jsonl) · [Measured command outcomes](observations.json)

Ordinary elaboration loaded compiled imports. Its observed import trust field was 1025. The fresh checker loaded the compiled environment and replayed its eligible declarations in an empty kernel environment. It admits declared axioms as assumptions, omits unsafe and partial declarations, checks new theorem bodies, and compares regenerated constructors and recursors. These operations share the stock kernel, binary distribution and host. File hashes identify the bytes inspected. Source meaning and the execution environment remain separate assumptions. [Stock checker at the executing revision](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean) · [Kernel replay](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean)

---

## Rust implementation and computational cost

This study checks a fixed formula offline. There is no Rust production API, feature flag, statistical estimand, fitted state or sampling step for this proof. For the hand count there are seven branches and 128 possible families. Testing each family's nonempty membership and its pairs requires at most 21 branch comparisons per family. That bound describes a simple enumeration. The measured Lean run also reads and checks the original definitions and imported declarations.

On the recorded arm64 Darwin host the eleven native commands and their surrounding checks took 242.51 seconds. Peak observed process memory was 3,754,885,120 bytes. The run permitted 900 seconds per native command, 5,400 seconds overall and 4 GiB of observed process-group memory. A native error, a missing declaration or unsuccessful replay prevented acceptance. These measurements describe proof checking on this workload. They give no estimator runtime or application-performance result. [Command-level resources and compiler hashes](observations.json)

To repeat the source checks, run the following command at the repository root. For native replay supply the bin directory of an official stock Lean 4.34.1 release to the same script with the option shown below. The portable run includes three additional synthetic modules and checks the complete stored terms. The recorded portable reproduction used the same Darwin host and a different command sequence. [Replay entry point](replay.py)

~~~text
cd audit/research/three-source-w02
python3 -I -S -B replay.py --check-sources
python3 -I -S -B replay.py --lean-bin LEAN_BIN
~~~

The original two solvers' status reports remain historical observations. This later proof covers one of 22 inputs the original solvers reported as unsatisfiable. It leaves the other 21 source formulas, the complete lattice-to-count correspondence, all numerical PID coordinates and the scientific acceptance programs to their own checks. A synthetic satisfiable example rejected the proposed false result on stock Lean. An earlier term-observer build failed and its corrected version passed on synthetic inputs before the one original proof proposal was admitted. The source readers, model reviewers and candidate shared published mathematics, machine infrastructure and the known historical status. The checks document the use of model assistance and the absence of an independent human disposition. [Preparation record and comparison scope](REVIEW.md)

Cite Sepehr Mahmoudian (2026), *The eighteen families in the original three-source count test*, with the exact repository commit or release. Cite Williams and Beer for the lattice and the SMT-LIB reference for the language. [Software citation](../../../CITATION.cff)
