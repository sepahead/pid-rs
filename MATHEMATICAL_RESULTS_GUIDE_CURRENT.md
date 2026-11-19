# Mathematical results guide for November 2026

**Sepehr Mahmoudian · 19 November 2026**

Which conclusions can a reader carry from a categorical count table into a statistical or computational claim? This edition follows that question through sampling, fitted transforms, optimization and three-source counts. The [foundation guide](MATHEMATICAL_RESULTS_GUIDE.md) and its [28-page PDF](output/pdf/mathematical-results-guide.pdf) give the full map of nine result families and six earlier companion packages. The linked studies specify the individual claims.

## Reading the results

A **law** specifies outcome probabilities. An **empirical law** divides each observed count by the total. **Coverage** is the probability, across original samples from a specified law, that a reported interval contains the population quantity. A **source** supplies information about a designated target. **Shared redundancy** here means the average information from the union of the specified source events in finite categorical shared-exclusions PID. The logarithms are natural and the information unit is the **nat**. [Defining categorical paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Method catalog](METHODS.md)

## Why the nominal 95% range has coverage 64/81

One exact coverage calculation uses four independent rows, each consisting of a binary target and two copies of that target. The population probability of one is one third. Using seed 7, 200 resamples of four rows, block length one and a nominal 95% level, the public percentile summary covered the population entropy with probability 64/81. Both constant samples missed. Their probability alone gives an upper bound for every seed with the same constant-sample behavior. [Derivation, software scope and finite verification](FINITE_COPY_BOOTSTRAP_COVERAGE.md)

Here either source reveals the target. Population redundancy therefore equals binary entropy. Write $p=1/3$ for the probability of one and $H(p)$ for entropy in nats. The two constant samples return the range $[0,0]$, which excludes the positive value $H(1/3)$. Their total probability is

$$
(1-p)^4+p^4=16/81+1/81=17/81.
$$

At seed 7 all 14 other ordered samples cover. This establishes the stated coverage for that law, rank rule and seed. The 200 resamples determine an interval for each original sample. They do not supply 200 independent observations of coverage. [Exact table and stored endpoints](audit/evidence/finite-copy-bootstrap-coverage/README.md)

---

## What a fitted quantizer fixes

A **quantizer** assigns each raw observation a categorical label. A fitted quantizer depends on the training data. The map must be measurable using only the training information and its current raw input. After conditioning on training, this fixes the map. The evaluation rows must then be conditionally independent and identically distributed for the stated convergence result. Independent held-out rows are one way to meet the premise. Pooling outputs from different fitted maps leads to a different question. [Convergence theorem and conditional counterexamples](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md)

Let $Q$ be the fitted map, $W$ one raw evaluation row and $P_Q$ the conditional law of $Q(W)$ given training. The categorical estimate targets the chosen quantity of $P_Q$. Nonlinearity matters. For example, if separate training outcomes select opposite constant labels for every variable, each conditional law has zero entropy. An equally weighted mixture of the two point masses has entropy $\ln 2$ nats.

The policy for out-of-range rows matters too. Write $\eta$ for the conditional probability of rejection on one row. Conditional independence gives $(1-\eta)^n$ for success on all $n$ rows. When $\eta>0$, that probability tends to zero. A declared rejection-sampling rule can target the conditional law of successful rows. Clamping is a different specified map. At identical fitted edges both policies give exactly the same labels whenever the evaluation row lies in range, including the endpoints. [Fitted-map and policy assumptions](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md)

## When an absolute-value optimization clips its answer

The source-partition study compares finite shared-exclusions atoms before and after recoding. A signed coordinate difference $d$ and its modeled magnitude $t$ are measured in nats. A binary sign choice selects one of two pairs of linear bounds. The parameter $M$ is their finite upper-bound constant. For a fixed feasible $d$, the selected sign allows $t\le |d|$ and $t\le M-|d|$. Both limits must admit $t=|d|$, which gives the pointwise criterion

$$
M\ge 2|d|.
$$

A bound on $|d|$ alone can clip the objective. In the study's four-symbol copy example, the true maximum is $\ln 4$ nats and the old sign rule yields 1 nat. Let $B$ be the sum of the four nonnegative entropy totals and $L$ the signed change in target mutual information. The full feasible product admits the sufficient choice $M=B+|L|$. The 30 original finite tables satisfy $|L|<0.106$ nat, so their historical choice $M=B+1$ in nats suffices. The reported numerical optima still lack exact optimization certificates. [Corrected source-partition proof and finite scope](audit/research/source-coupling-compression/EXPOSITION.md)

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

There are three named sources. The source and target labels can have arbitrary types with decidable equality. The table has a finite set of row indices, a natural-number weight per index, and a target label. Fix a key and a family of source collections. The **source event** holds at a row when all sources in at least one collection match their labels at the key. A Boolean disjunction of these conjunctions tests the same event. [Formal definitions, declarations and replay](audit/research/three-source-alphabet-counts/README.md)

Write $N$ for the total weight, $U$ for the source-event weight, $T$ for the target-match weight and $V$ for the weight of their intersection. These symbols denote counts on this page. Nonnegative weights and event inclusion give

$$
V\le U\le N,\qquad V\le T\le N.
$$

A key in the table matches itself on every source and on the target. With a nonempty family its source event, target match and their intersection all contain it. If the key has positive weight, all three counts are positive. The formal package also checks order properties, equality of data on the counted support, and the correspondence between the Boolean and event descriptions. A stock Lean 4.34.1 compilation and a fresh kernel-checker invocation passed for the 22 theorem types. The definition comparison covered nine pairs and one auxiliary definition. The recorded run relies on its pinned imports and the ordinary Lean trust path. Paper correspondence, refinement of Rust or binary64 execution, the original Lean 4.33 protocol and independent human disposition remain open. [Exact checked scope](audit/research/three-source-alphabet-counts/README.md)

## Rust implementation and computational cost

The bootstrap entry point is `experimental::pipelines::block_bootstrap`. The study enabled the Cargo feature `experimental-pipelines` and disabled default features. Each replicate calls the stable categorical function `discrete_sxpid2_averaged`. The driver evaluated the statistic on 3,200 four-row replicates across 16 ordered samples. Fitted-quantizer cost includes fitting and applying the map before computing the categorical functional. The reference byte reader is written in Python, and the arbitrary-alphabet statements are Lean proofs. The source-partition optimizer is an exploratory offline Python calculation. These proofs and finite observations provide no production latency or sampling-calibration guarantee. The reports give exact inputs, limits and source routes. [Copy-study cost](FINITE_COPY_BOOTSTRAP_COVERAGE.md) · [Engineering cost reference](RUST_IMPLEMENTATION_AND_COST.md)

Model assistance supported source comparison, drafting and checking. Cite Sepehr Mahmoudian (2026), *Mathematical results guide for November 2026*, with the exact repository commit or release. [Software citation](CITATION.cff)
