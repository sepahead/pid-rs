# Mathematical results guide for November 2026

**Sepehr Mahmoudian · 21 November 2026**

What can sampling, optimization and arithmetic establish from a categorical count table? The [foundation guide](MATHEMATICAL_RESULTS_GUIDE.md) and its [28-page PDF](output/pdf/mathematical-results-guide.pdf) cover nine result families.

## Reading the results

A **law** gives outcome probabilities. An **empirical law** uses relative counts. **Coverage** is the probability, over repeated original samples, that an interval contains the population value. Partial information decomposition (PID) assigns information from **sources** about a **target**. In categorical shared exclusions, each node lists one or more nonempty source sets, none containing another. The **matching event** matches all labels in at least one set. At each outcome with target value $t$ and matching event $A$, the pointwise value is $\ln[P(T=t\mid A)/P(T=t)]$. Redundancy is its probability-weighted average. Natural logarithms give **nats**. [Defining categorical paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Method catalog](METHODS.md)

## Why the nominal 95% range has coverage 64/81

Draw four independent binary targets with probability $p=1/3$ of one. Both sources copy the target. Either source reveals its label, so the average information is the binary entropy

$$
H(p)=-p\ln p-(1-p)\ln(1-p),\qquad H(1/3)=\tfrac13\ln(27/4)\ \text{nats}.
$$

Set $0\ln0=0$. Each **bootstrap resample** draws four original rows with replacement. With $k$ ones it gives $H(k/4)$. For each original sample, seed 7 and block length one give 200 resamples. Sort their entropies in increasing order. Entries 5 and 194, counting from zero, give the nominal 95% range. [Derivation and software scope](FINITE_COPY_BOOTSTRAP_COVERAGE.md)

Both constant samples give $[0,0]$. Their total probability is $(1-p)^4+p^4=17/81$. Each of the other 14 ordered samples gave endpoints zero and approximately $\ln2$ nats, enclosing $H(1/3)$. The covered probability is $1-17/81=64/81$. [Exact table and stored endpoints](audit/evidence/finite-copy-bootstrap-coverage/README.md)

---

## What a fitted quantizer fixes

A **quantizer** assigns each raw observation a categorical label. A fitted quantizer depends on the training data. The map must be measurable using only the training information and its current raw input. After conditioning on training, this fixes the map. The evaluation rows must then be conditionally independent and identically distributed for the stated convergence result. Independent held-out rows are one way to meet the premise. Pooling outputs from different fitted maps leads to a different question. [Convergence theorem and conditional counterexamples](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md)

Let $Q$ be the fitted map, $W$ one raw evaluation row and $P_Q$ the conditional law of $Q(W)$ given training. The categorical estimate targets the chosen quantity of $P_Q$. Nonlinearity matters. For example, if separate training outcomes select opposite constant labels for every variable, each conditional law has zero entropy. An equally weighted mixture of the two point masses has entropy $\ln 2$ nats.

The policy for out-of-range rows matters too. Write $\eta$ for the conditional probability of rejection on one row. Conditional independence gives $(1-\eta)^n$ for success on all $n$ rows. When $\eta>0$, that probability tends to zero. A declared rejection-sampling rule can target the conditional law of successful rows. Clamping is a different specified map. At identical fitted edges both policies give exactly the same labels whenever the evaluation row lies in range, including the endpoints. [Fitted-map and policy assumptions](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md)

## When an absolute-value optimization clips its answer

Before and after a change of source labels, the study compares the information assigned to each node. Let $d$ be its signed change in nats. The optimizer maximizes a sum of modeled magnitudes $t\geq0$. A binary variable chooses a sign. For $|d|\leq M$, the two bounds at that sign give $t\leq|d|$ and $t\leq M-|d|$. Here $M$ is a nonnegative constant in nats. The true magnitude fits exactly when $M\geq 2|d|$.

Let source two copy a target uniform on four symbols. Sources one and three are constant. Before recoding, the only nonzero atom is $\ln4$ nats at the node whose only group is source two. Five cumulative values contain this atom. In each of their nodes, every group includes source two. A group of constant sources would match all four rows.

Recode all sources to constants. All cumulatives and atoms are then zero. Thus the only nonzero magnitude is $|d|=\ln4$. The old rule used $M=\ln4+1$ nats, so its second bound forces $t\leq1$ nat. This explains how the modeled maximum falls below $\ln4$.

In general, let $B$ be the sum of four entropies: the joint source entropy and its conditional entropy given the target, both before and after recoding. Let $L$ be the original joint source–target mutual information minus its recoded value. Then $M=B+|L|$ suffices throughout the optimization. On the 30 archived distributions $|L|<0.106$ nat, so their choice $M=B+1$ nat suffices. Exact certificates for the reported numerical maxima remain open. [Sign constraints, example and proof](audit/evidence/source-partition-sign-margin-2026-11-19.md) · [Source-partition study](audit/research/source-coupling-compression/EXPOSITION.md)

---

## Reconstructing integer counts from one byte string

A **key** contains three labeled source states and one target state. A state is an ordered array of tokens. A **canonical** encoding assigns one spelling to each admitted table. The input rows have positive integer counts, distinct keys and the specified increasing order. An encoder $E$ writes the table $T$. A reader $D$ parses a byte string $b$ that obeys the grammar. [Original input specification](claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

Each state has one to 64 tokens from the specified ASCII alphabet. The grammar admits one to 1,024 occupied rows. A count has at most 4,096 decimal digits and the total count has at most 8,192 binary digits. The complete input, including its terminal line feed, has at most four mebibytes. These are mathematical domain restrictions and file limits.

The project proof gives both identities

$$
D(E(T))=T,\qquad E(D(b))=b.
$$

Each token excludes quote and backslash, so the closing quote marks its end. A decimal count has a nonzero leading digit and a unique expansion in base ten. The remaining punctuation and fixed member order locate every array, field and row. Finally the reader verifies distinct increasing keys, the declared bounds, and the single terminating line feed. Reading equal encoded words therefore returns equal labeled integer tables. These facts concern this particular grammar. JSON by itself allows multiple spellings for equivalent data. [Proof and reference reader](audit/research/categorical-count-table-encoding/README.md) · [JSON standard](https://www.rfc-editor.org/rfc/rfc8259)

A proper prefix precedes its longer state. For example, `["A"]` comes before `["A","A"]` in the required table order. Comparing these arrays after encoding instead compares a closing bracket with a comma. The comma has the smaller ASCII value, so this byte comparison reverses the intended order.

For the separate finite check, each of the four state positions takes one of three values: `["A"]`, `["A","A"]` or `["AA"]`. This gives $3^4=81$ keys. A table uses one or two distinct keys, and each count is 1, 9 or 10. The number of labeled tables is

$$
81\cdot 3+\binom{81}{2}\cdot 3^2=29{,}403.
$$

All 29,403 emitted words were distinct and the tested readers recovered the corresponding tables. Prefixes and the transition from one decimal digit to two are both exercised. The written two-sided argument applies to the specified positive-input language. The examples cover neither all input bytes nor all field values. The full three-source certificate additionally requires an output schema and its scientific correspondence. [Certificate obligations](claims/SX-CERTIFIED-AVERAGED-PID3-001/obligations.md)

---

## What the 22 checked count statements establish

There are three named sources. The source and target labels can have arbitrary types with decidable equality. The counts sum over a finite set of row indices. Each index has a natural-number weight, three source labels and a target label. Choose any reference index (the key) and a family of source collections. The **source event** holds at a row when all sources in at least one collection match their labels at the key. A Boolean disjunction of these conjunctions tests the same event. [Formal definitions, declarations and replay](audit/research/three-source-alphabet-counts/README.md)

Write $N$ for the total weight, $U$ for the source-event weight, $T$ for the target-match weight and $V$ for the weight of their intersection. These symbols denote counts on this page. Nonnegative weights and event inclusion give

$$
V\le U\le N,\qquad V\le T\le N.
$$

If the family is nonempty and the key belongs to the summed index set, its row contributes its own weight to $V$. A positive weight at that key therefore makes all four counts positive. Stock Lean 4.34.1 compiled and replayed 22 theorem types about counts, order and the Boolean representation. The definition comparison covered nine pairs and one auxiliary definition. Paper correspondence, Rust and floating-point refinement, the original Lean 4.33 protocol and human review remain open. [Exact checked scope](audit/research/three-source-alphabet-counts/README.md)

A separate proof checks both assertions in the archived count test W02. The first is the literal true. The second denies that exactly 18 of the 128 families of the seven possible branches are valid **and** that 18 listed codes are distinct. Both conditions hold, so the second assertion is false on every assignment. The test omits the separate check that every listed code represents a valid family. [Count, source and checked proof](audit/research/three-source-w02/README.md)

## Rust implementation and computational cost

The bootstrap entry point is `experimental::pipelines::block_bootstrap`. The study enabled the Cargo feature `experimental-pipelines` and disabled default features. Each replicate calls the stable categorical function `discrete_sxpid2_averaged`. The driver evaluated the statistic on 3,200 four-row replicates across 16 ordered samples. Fitted-quantizer cost includes fitting and applying the map before computing the categorical functional. The reference byte reader is written in Python, and the arbitrary-alphabet statements are Lean proofs. The source-partition optimizer is an exploratory offline Python calculation. These proofs and finite observations provide no production latency or sampling-calibration guarantee. The reports give exact inputs, limits and source routes. [Copy-study cost](FINITE_COPY_BOOTSTRAP_COVERAGE.md) · [Engineering cost reference](RUST_IMPLEMENTATION_AND_COST.md)

---

## When rounding changes a normalized degree

Mutual information measures how much observing sources reduces uncertainty about a target on average. Let $m$ be the number of sources and $J>0$ their joint mutual information with the target, in nats. The average degree of redundancy sums the mutual information from each source alone and divides by $J$. The average degree of vulnerability sums the losses in joint information when each source is removed and divides by $J$. For one common finite distribution, including an empirical one, both degrees lie in $[0,m]$. Using the whole source tuple as target gives the two source-only entropy ratios when the joint entropy is positive. Binary64 is the 64-bit floating-point format. Rounding each exact mutual information once to its nearest binary64 value, with ties to even, preserves order and nonnegativity, though $J$ can round to zero. A limit above the numerical floor can still round to it. Separately fitted estimates can violate the bounds. [Defining equations](https://arxiv.org/abs/2504.15779v1)

Three marginal inputs of $1/16$ nat and $J=10/16$ nats give the exact redundancy degree $3/10$. Earlier Rust code returned the next binary64 value above its nearest representation. The corrected functions round the ratio and its original-unit numerator independently. On a 64-bit target, each fixed accumulator array has 34 words and work grows linearly with $m$. Across 184 fixed calls, the earlier code differed on 41 reports. The corrected code matched all seven fields on every call. These calls test supplied numbers. A population law realizes the worked inputs. Exact finite-table mutual information in nats is zero or irrational, although one table can reproduce all the once-rounded inputs. [Arithmetic, examples and Rust cost](audit/research/normalized-shannon-arithmetic/README.md) · [Hosted observations](audit/evidence/normalized-shannon-reports-2026-11-20/receipt.json) · [Integer-exponential proof](https://doi.org/10.3931/e-rara-101019)

## What six three-source certificates establish

The six tables are the negative, unit and weighted cases, the negative case after relabeling or source permutation, and the unit case after doubling its counts. Each table has two to five occupied rows. Dividing their counts by the total gives its empirical distribution. The decomposition uses the 18 nonempty families of pairwise incomparable nonempty source subsets. One family asks whether source two or source three matches the row. A family’s cumulative value includes contributions from all families below it in the shared-exclusions order. Subtracting those contributions gives its atom. Each cumulative value and atom has informative, misinformative and signed net components. For all 648 named coordinates (108 per table), a second calculation recovered the exact rational product $Q$ and enclosed its value $\ln(Q)/N$ in the reported interval, where $N$ is the total count. Every nonzero such coordinate is irrational in nats. Each interval was at most $2^{-160}$ nats wide.

In the negative case, the atom for a match on source two or three has $Q=9/16$ and signed value $\ln(9/16)/3$ nats. The weighted table has a constant target and all 36 net values are zero. The transformation and constant-target checks covered 360 relations. Direct event comparisons grow quadratically in the occupied row count. Product and logarithm costs also depend on bit length and precision. The producer declared heap plans of 42,212,880 to 42,611,592 bytes for these six tables. The general construction and verification obligation (D1) and complete source custody (P1) remain open. [Tables, exact values, resource bounds and scope](audit/research/three-source-six-certificate-observations/README.md)

Model assistance supported source comparison, drafting and checking. Cite Sepehr Mahmoudian (2026), *Mathematical results guide for November 2026*, with the exact repository commit or release. [Software citation](CITATION.cff)
