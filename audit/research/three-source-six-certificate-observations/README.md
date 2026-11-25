# Reading six three-source categorical shared-exclusion certificates

**Sepehr Mahmoudian · 20 November 2026**

How much information does each combination of sources supply about a target? From six counted tables we recovered 108 rational products per table. Comparing a product with one gives the sign of its logarithm. A second calculation bounded each logarithm divided by the table total. **All 648 values agreed with the records.** [Paired bytes](cases) · [Case identities](panel.json) · [Shared-exclusions definition](https://arxiv.org/abs/2002.03356v5)

## Terms and sources

| Term | Meaning here |
|---|---|
| Source, target, joint state | One row $z$ records three input variables $X_1,X_2,X_3$ and the variable of interest $Y$. Each column contains an ordered array of categorical labels. Compare labels for equality within their own column. |
| Count, occupied support, empirical distribution | The $r$ distinct rows with positive counts form the occupied support. The count $c_z$ tells how often row $z$ occurs. The table has total $N=\sum_z c_z$ and empirical probabilities $c_z/N$. |
| Partial information decomposition (PID) | PID divides the information that sources give about a target into contributions indexed by source sets. Here those contributions use the definition of Makkeh, Gutknecht and Wibral. |
| Mask, antichain, node | Masks 1, 2 and 4 identify sources one, two and three. Sums identify larger sets. A node is a nonempty family $\alpha$ of nonempty source sets with no member properly containing another. Such a family is an antichain. |
| Event and mass | At a given row $z$, $E_\alpha(z)$ contains the rows that agree on all sources in at least one set of $\alpha$. $U_{\alpha,z}$ counts those rows with multiplicities, $T_z$ counts the target matches, and $V_{\alpha,z}$ counts both. |
| Cumulative, atom and component | A cumulative sums the atoms at and below its node. Surprise is minus the natural logarithm of a probability. The informative part ($+$) uses the source event, the misinformative part ($-$) uses it given the target, and the net is their difference. |
| Product, natural logarithm, nat | A positive rational product $Q$ gives one value $\ln(Q)/N$ in nats, the information unit for natural logarithms. One bit equals $\ln2$ nats. |
| Certificate and dyadic interval | B encodes the input table with one prescribed spelling. C records the products and intervals. Each endpoint is an integer times an integer power of two. The pair bounds the value. |

### The defining papers

In *Introducing a Differentiable Measure of Pointwise Shared Information* (2021, arXiv:2002.03356v5), Makkeh, Gutknecht and Wibral define the information at one observed state and its average over states. Equation (4) requires a match on at least one individual source. Equations (6)–(8) require agreement on every source within at least one of the chosen sets. See also Eqs. (12)–(15) and (17), and Theorems IV.2–IV.3. Those theorems give monotone component cumulatives and nonnegative component atoms. The net is their signed difference. A bit-valued result is multiplied by $\ln 2$ to obtain nats. The exact product representation, byte grammar, resource counters and reader are project constructions. Williams and Beer introduced the ordering of source sets in *Nonnegative Decomposition of Multivariate Information* (2010, arXiv:1004.2515v1). The construction below fixes the matrix entries. [Makkeh, Gutknecht and Wibral, version 5](https://arxiv.org/abs/2002.03356v5) · [Version of record](https://doi.org/10.1103/PhysRevE.103.032149) · [Williams and Beer, 2010](https://arxiv.org/abs/1004.2515v1) · [Project conventions](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md)

If the question is only how much the whole source tuple tells us about the target, ordinary mutual information gives a single number. It averages the natural logarithm of joint probability divided by the product of the source and target marginal probabilities. This study asks which named source combinations carry the informative and misinformative components and which signed contributions survive subtraction. That question fixes the shared-exclusions functional and the 18-node decomposition. The simple count-ratio calculation below provides a direct check on one of its coordinates.

## From counts to coordinates

Fix a supported row $z$ and a node $\alpha$. Matching all sources inside a mask means taking the intersection of their equality events. Matching at least one mask means taking the union of these intersections. The anchor row contributes to both $U_{\alpha,z}$ and $V_{\alpha,z}$, so every denominator below is positive. Multiplicity matters. The exact cumulative products are

$$
Q^+_\alpha=\prod_z (N/U_{\alpha,z})^{c_z},\qquad
Q^-_\alpha=\prod_z (T_z/V_{\alpha,z})^{c_z},\qquad
Q^{\mathrm{net}}_\alpha=Q^+_\alpha/Q^-_\alpha .
$$

The products run over the occupied support. Write $\widehat P(E)$ for the sum of $c_z/N$ over the rows in an event $E$. For example, taking $\ln(Q^+_\alpha)/N$ gives the empirical mean of the pointwise informative value $-\ln\widehat P(E_\alpha(z))$. The misinformative analogue uses the event probability conditional on the observed value of $Y$. Their difference is signed.

For two nodes $\beta,\alpha$, write $\beta\preceq\alpha$ when every mask of $\alpha$ contains some mask of $\beta$. The zeta matrix has one row for each cumulative and one column for each atom, with $Z_{\alpha\beta}=1$ if $\beta\preceq\alpha$ and zero otherwise. Its inverse $\mu=Z^{-1}$ gives the atom product at $\alpha$ as $\prod_\beta (Q^u_\beta)^{\mu_{\alpha\beta}}$ for component $u$. Here $u$ is informative, misinformative or net. This finite inversion is the rule for subtracting strictly lower contributions. Rota described the general finite-order inversion in 1964 (DOI 10.1007/BF00531932). Each key lists its masks in increasing order as two-digit hexadecimal numbers. For example, `02+04` is a union of two one-source events, whereas `06` requires both source matches. The reader checks each key and mask tuple against the registered sequence. Two scopes times three components times 18 nodes give **108 named coordinates per table**. A product below, equal to, or above one gives the corresponding negative, zero, or positive sign exactly. [Registry and product construction](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md) · [Executable arithmetic](arithmetic.py)

## The six input tables and all 18 node keys

In the following rows the four positions are $X_1,X_2,X_3,Y$, in that order. A digit denotes the one-token label with that spelling. A pair such as $(1011,1)$ means the state $(1,0,1,1)$ occurs once. Each unlisted state has count zero. The name “unit” labels the table and does not specify all its counts.

| Base table | Pairs (four labels, count), in input order |
|---|---|
| Negative | $(1011,1),\ (1101,1),\ (1110,1)$ |
| Unit | $(0100,1),\ (0101,1),\ (1000,1),\ (1001,4),\ (1100,1)$ |
| Weighted | $(0000,2),\ (0100,1)$ |

The other three tables follow exactly from these rows. For the relabeled negative table, prefix the four labels by the letters A, B, C and T, respectively. For example $(1,0,1,1)$ becomes $(\mathrm{A1},\mathrm{B0},\mathrm{C1},\mathrm{T1})$. For the permuted negative table, put the four entries in the order $X_2,X_3,X_1,Y$. Preserve each count and sort the resulting rows in increasing label order. For the doubled unit table, keep each label and multiply every count by two.

The following lists give all node keys in certificate order. The plus sign in a key joins alternative matching events. Each mask inside a key requires a match on all its sources.

| Number of masks | Keys |
|---|---|
| One | `01`, `02`, `03`, `04`, `05`, `06`, `07` |
| Two | `01+02`, `01+04`, `01+06`, `02+04`, `02+05`, `03+04`, `03+05`, `03+06`, `05+06` |
| Three | `01+02+04`, `03+05+06` |

**Inversion without a matrix.** For a node $\alpha$, its strictly lower nodes are those $\beta\ne\alpha$ for which every source set in $\alpha$ contains at least one source set in $\beta$. For each component $u$, visit nodes in increasing order of their number of strictly lower nodes. Start with the cumulative product $Q^u_\alpha$ and divide by the atom products already found at all strictly lower nodes. An empty product is one. The following expression gives each atom product $A^u_\alpha$ in terms of its strictly lower nodes.
$$
 A^u_\alpha = Q^u_\alpha \bigg/ \prod_{\beta\prec\alpha} A^u_\beta .
$$
The six coordinate blocks are cumulative informative, cumulative misinformative, cumulative net, atom informative, atom misinformative and atom net. Each block uses the 18 keys above. This gives the printed names and their values without an external matrix.

**Exact values in nats.** For $x=\ln(Q)/N$, $Q=1$ gives $x=0$. Otherwise $e^{N|x|}=\max(Q,1/Q)$ is rational. If $|x|=a/b$ for positive integers $a,b$, raising that rational to the power $b$ would give $e^{Na}$. Every positive integer power of $e$ is irrational. Thus every nonzero coordinate, including a negative atom, is irrational in nats and cannot equal a midpoint between adjacent finite values of binary64, the 64-bit floating-point format. Those midpoints are rational. This conclusion gives no lower bound on its distance from a midpoint. [Hermite (1873), §III](https://doi.org/10.3931/e-rara-101019) · [Count tables and rounding](../normalized-shannon-arithmetic/README.md)

### Bounding the logarithm

The reader also bounds the magnitude without relying on a floating-point logarithm. For $Q=2^e a/b$ with integer $e$, positive integers $a,b$ and $1\le a/b<2$, set $t=(a-b)/(a+b)$. Then $\ln(a/b)=2\sum_{j\ge0}t^{2j+1}/(2j+1)$. The integer index $j$ starts at zero. After an integer number $m\ge1$ of terms, the omitted tail is at most $2t^{2m+1}/[(2m+1)(1-t^2)]$. Here $0\le t\le1/3$, including the separate $\ln 2$ evaluation at $t=1/3$. The implementation rounds fixed-point lower operations down and upper operations up, adds a tail allowance, and combines bounds with $e\ln 2$ in the order required by the sign of $e$. It then divides by $N$ with directed rounding. It requires the **entire independent enclosure** to lie inside the producer's interval and requires the producer width to be at most $2^{-160}$ nats. For $Q=1$ the independent interval is exactly $[0,0]$. For all 648 coordinates, the first precision tested by the second routine, 256 bits, sufficed for containment. [Interval implementation](arithmetic.py) · [Original width and schedules](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

## Six observations and a worked example

The final three columns count signs over all 108 coordinates. The support tuple gives the **number** of distinct values of $X_1,X_2,X_3,Y$ in that order. Related cases share source data by construction.

| Table | Rows $r$ | Total $N$ | Support tuple | Negative | Zero | Positive |
|---|---:|---:|---|---:|---:|---:|
| [negative](cases/negative/B.json) | 3 | 3 | (1,2,2,2) | 6 | 60 | 42 |
| [unit](cases/unit/B.json) | 5 | 8 | (2,2,1,2) | 0 | 58 | 50 |
| [weighted](cases/weighted/B.json) | 2 | 3 | (1,2,1,1) | 0 | 96 | 12 |
| [relabel_negative](cases/relabel_negative/B.json) | 3 | 3 | (1,2,2,2) | 6 | 60 | 42 |
| [permute_negative](cases/permute_negative/B.json) | 3 | 3 | (2,2,1,2) | 6 | 60 | 42 |
| [replicate_unit](cases/replicate_unit/B.json) | 5 | 16 | (2,2,1,2) | 0 | 58 | 50 |

In the **weighted** table $X_1=X_3=Y=0$ everywhere. The two $X_2$ states have counts two and one. At node `02`, which requires the second source alone, the event masses are therefore two and one at the respective rows. Since the target is constant, $T_z=3$ and $V_{02,z}=U_{02,z}$. Both cumulative products equal $(3/2)^2(3/1)=27/4$. Both informative and misinformative values are $\ln(27/4)/3$ nats. The divisor is the total count three, since the more common state appears twice. Giving the two original local values equal weight would instead give $[\ln(3/2)+\ln 3]/2=\ln(9/2)/2$. Setting both counts to one and recomputing the probabilities would define a different distribution and give $\ln 2$ nats. In the recorded table the net product is one and the signed net value is zero. The same equality of informative and misinformative products holds at every node for this table. All 18 net cumulatives and 18 net atoms vanish. [Input](cases/weighted/B.json) · [Exact certificate](cases/weighted/C.json)

In the **negative** table, node `02+04` matches source two **or** source three. In file order its three event counts are 2, 2 and 3. The matching target counts are 2, 2 and 1, and the joint event-and-target counts are all one. The informative and misinformative products are therefore $9/4$ and $4$. Its only strictly lower node is `01+02+04`. That lower event is certain because source one is constant, so its two component products are one. At `02+04`, the signed atom consequently has product $(9/4)/4=9/16<1$ and value $\ln(9/16)/3<0$ nats. The case name `unit` is a fixture identifier. Its fourth row has multiplicity four. [Negative case output](cases/negative/C.json) · [Unit case input](cases/unit/B.json)

### Recovering every printed enclosure

A comparison on 21 November 2026 gives this equivalent description of all interval endpoints in the six stored reports. Write $x=\ln(Q)/N$ in nats and $g=2^{164}$. When $Q=1$, the recorded interval is $[0,0]$. For $Q\ne1$, put $j=\lfloor gx\rfloor$, the greatest integer at most $gx$. The reported interval is
$$
    [(j-1)/g,\ (j+2)/g] .
$$
This describes the six retained reports. It places no requirement on an output for another table. Of the 648 coordinates, 392 had zero width. The other 256 had width $3/g<2^{-160}$ nats.

**Calculate $j$ with rational arithmetic.** Write $Q=2^e r$ with integer $e$ and $1\le r<2$. Set $t=(r-1)/(r+1)$, sum the first 110 terms of the series on the previous page, and place the stated tail bound above that sum. Do the same for $\ln2$ with $t=1/3$. Multiply the two bounds for $\ln2$ by $e$, reversing their order if $e<0$. Add the corresponding bounds for $\ln r$ and divide both by $N$. For all the products here the floors of these two rational numbers times $g$ agree. In the negative example the value is about $-0.1917880483$ nats. Its grid integer is
$$
 j=-4\,484\,776\,745\,802\,936\,173\,941\,066\,594\,674\,027\,196\,002\,151\,703\,757 .
$$
The three printed rows, their event counts, division by the single lower atom and this pair of endpoints complete the calculation from the input to the interval.

**Reproduce the independent 256-bit test.** The output grid spacing is $2^{-p}$ with $p=256$. Internally set $S=2^{p+24}$, $m=\lceil(p+24)/3\rceil+1$. For each of the two series arguments $t$, return integer bounds $(0,0)$ if $t=0$. Otherwise let $\ell=\lfloor St\rfloor$, $h=\lceil St\rceil$, $a=\lfloor\ell^2/S\rfloor$, $b=\lceil h^2/S\rceil$. Start sums $L=U=0$. For $i=0,\ldots,m-1$ add $\lfloor2\ell/(2i+1)\rfloor$ to $L$ and $\lceil2h/(2i+1)\rceil$ to $U$. Then replace $\ell,h$ by $\lfloor\ell a/S\rfloor,\lceil hb/S\rceil$. Return $(L,U+1)$ to cover the omitted positive tail. Here the ceiling of a number is the smallest integer at least that number.

Call the two returned pairs $(L_r,U_r)$ for $\ln r$ and $(L_2,U_2)$ for $\ln2$. For $e\ge0$, combine them as $(L_r+eL_2,U_r+eU_2)$; for $e<0$, exchange $L_2$ and $U_2$ in that expression. Divide by $N2^{24}$, round the lower integer down and the upper integer up, and multiply each by $2^{-p}$. Use $[0,0]$ directly if $Q=1$. The resulting interval lies inside the recorded interval for every one of the 648 coordinates. The next page examines different inputs to this same numerical rule.

### Two inputs to the logarithm routine

**Added 21 November 2026.** Can the seven scheduled precisions fit an independently computed interval inside any correct reported interval? The six tables met the subset test at 256 bits. To test the arithmetic alone, supply the positive rational $Q=1+x$ and divisor $N=1$ directly, where $x=2^{-k}$ for $k=2048$ or $4096$. For both, $[0,x]$ contains the true value strictly in its interior because
$$
0<\ln(1+x)=\int_0^x\frac{du}{1+u}<x .
$$

Let $p$ be the output precision in bits. In schedule order $p=256,384,512,768,1024,1536,2048$, the computed lower endpoint is always zero. In units of $2^{-p}$, the upper numerators for $k=2048$ are $(1,1,1,1,1,1,2)$. For $k=4096$ all seven are one. In each case every computed upper endpoint exceeds $x$. When $k=4096$ even the finest output grid has no positive point in $[0,x]$. When $k=2048$ the last grid contains $x$ exactly and the rounding inside the routine matters. [Pinned logarithm routine](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/audit/research/three-source-six-certificate-observations/arithmetic.py#L214-L258)

The series argument is $t=(Q-1)/(Q+1)=1/(2^{k+1}+1)$. At internal scale $2^{p+24}$ and for the listed $p<k$, rounding $t$ down and up gives integers 0 and 1. Later powers have the same bounds. With $m=\lceil(p+24)/3\rceil+1$ terms, the upper sum is $2+(m-1)+1=m+2$ including its tail allowance. This lies strictly between 0 and $2^{24}$, so rounding up after division by $2^{24}$ gives one. At $p=k=2048$ the starting integers are $2^{23}-1$ and $2^{23}$. The first term doubles each. The other 691 terms each add 0 below and 1 above. The tail adds 1 above. The final integers are $2^{24}-2$ and $2^{24}+692$, which round out to 0 and 2 on the output grid.

The normalized upper endpoint has coefficient one and exponent $-k$. The six-table reader permits $-2048$ and rejects $-4096$. The original wire format permits both, and both intervals meet its width limit. A valid table with total one has a single occupied state. Its event, target and intersection counts are all one. Every cumulative and atom product is therefore one. Neither scalar example can be such an empirical coordinate. The proposed claim requires correct intervals for **accepted** tables and specifies rejection when the schedule ends without containment. The 648 observed coordinates and the general claim keep their respective evidence scopes. [Endpoint reader](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/audit/research/three-source-six-certificate-observations/check.py#L139-L146) · [Original claim](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md) · [Width, exponent and schedule rules](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

An earlier project study covers a different checker and a producer that adds at least $2^{-176}$ nats on each side. That study also gives an unpadded first-stage counterexample. Here the whole external interval is narrower than its one-sided margin. The exact integer calculation uses the published Python routine offline and has no estimator timing or application result. [Earlier containment study](https://github.com/sepahead/pid-rs/blob/4b35dd94cf0b4a5a081d9f864611d80203e1ca4c/audit/archive/retained-worktree-fragments-20261113/payload/shared-pending-v1/output/SXPID3_FIRST_STAGE_CONTAINMENT_2026_10_12.md.txt)

### Transformations of the six tables

The secondary check reconstructed the declared transformations on the B tables and compared exact products by component, scope and transformed mask key. It covers **360 relations**.

- **One relabeling, 108 coordinate comparisons.** The new source and target labels preserve equality in each column. The underlying row weights and every equality event are preserved.
- **One source permutation, 108 coordinate comparisons.** Reordering $(X_1,X_2,X_3)$ to $(X_2,X_3,X_1)$ sends the original source masks $(1,2,4)$ to $(4,1,2)$. Sorting the remapped masks within each key identifies the same event and corresponding atom.
- **One count doubling, 108 coordinate comparisons.** Every event-count ratio stays fixed and each multiplicity doubles, so the product becomes $Q^2$. The coordinate is unchanged because the total becomes $2N$.
- **36 constant-target cancellations.** Both net scopes at all 18 nodes have product one in the weighted table.

## Running the readback

With Python 3.10 or later and its standard library, run these commands from this package directory.

~~~sh
python3 -I -B check.py
python3 -I -B -O check.py
python3 -I -B check.py --coordinates weighted
python3 -I -B controls.py
python3 -I -B -O controls.py
python3 -I -B check_schedule.py
python3 -I -B -O check_schedule.py
~~~

The final two commands check the seven upper numerators per scalar input, the last internal integer sums, the panel exponent rule and the 648 empirical precisions. [Schedule example reader](check_schedule.py)

The first command reports the six cases, 648 coordinates and the four relation counts. The third writes the weighted table's 108 mathematical records to standard output. Each includes the stable name and masks, reduced numerator and denominator, exact sign, both pairs of normalized endpoints, chosen precision and containment result. The command checks the complete six-case panel before returning the requested case. All fixed-file hashes include the terminal newline. A failure exits nonzero. [Reader](check.py) · [Case, original-run and observation digest register](panel.json) · [Schema and resource limits](profile.json)

**Reading the input and output files.** Both use JavaScript Object Notation (JSON), a structured text format. The schema prescribes the fields and their meanings. B gives the definition revision, three sources, units and positive rows ordered by their four label arrays. Each row stores its count as decimal text. C gives the report version, eight estimates of resource use, and 108 coordinates. Each coordinate identifies the input, claim, ordered registry of names, policy and source-file list by SHA-256, a 256-bit digest of the corresponding bytes. It gives a reduced positive fraction as two decimal integer strings. A nonzero endpoint has an odd integer coefficient. Zero has coefficient `"0"` and exponent zero. Field names follow the American Standard Code for Information Interchange (ASCII) in a prescribed order. Each file ends with one line feed. The six-table reader admits at most 4,096 input bytes, 131,072 report bytes, eight occupied rows, three decimal digits per count, and endpoint exponents of absolute value at most 2,048. [Wire rules](profile.json) · [Canonical input proof](../categorical-count-table-encoding/README.md) · [JSON Canonicalization Scheme, RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785)

### Checks on altered records

The control program constructs a new two-row table, obtains 108 admissible test records, then checks the reasons for 20 refusals. These include missing or replaced original files, a valid reduced fraction with the wrong value, a sign error, excess width, interval overlap without containment, negative or non-normalized zero, swapped or missing coordinates, duplicate or missing input rows, changed source binding or work counter, and duplicate JSON fields. Testing the mathematical predicate on deliberately altered synthetic records allows its own failure reasons to be observed after the original-file digest check. The synthetic control uses this package's arithmetic to create its input report. It tests rejection behavior and contributes zero cases to the six original observations. [Control source](controls.py)

## Rust implementation and computational cost

In Rust, `discrete_sxpid3_averaged` is available in `pid_core::stable::categorical` with default features. Its three discrete source matrices and target matrix have the same $N$ observation rows. To represent these tables, repeat each encoded complete row $c_z$ times. The call returns 18 averaged atoms keyed by source masks. The certificate has both cumulative and atom coordinates. Budgeted and cancellation-aware variants are available. With $D$ categorical coordinates across the four matrices, materializing the Rust inputs requires space of order $ND$. After grouping $r$ occupied states, event scans compare the fixed 18 nodes at each anchor against all occupied states, including the anchor, with at most order $r^2 D$ coordinate comparisons. Subset-information histograms and grouping add separate work. The averaged route returns floating-point values in nats. The research certificate producer used exact integer/rational products and directed multiprecision logarithms; its executable and full source manifest are outside this public package. Software that compares the stable estimator with these observations must map explicit source masks and keys, respect each row's multiplicity and compare the same mathematical quantity. This package makes no binary64 refinement claim. [Rust function source](../../../crates/pid-core/src/sxpid.rs) · [Engineering cost reference](../../../RUST_IMPLEMENTATION_AND_COST.md) · [Method catalog](../../../METHODS.md) · [Source-order caution](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

The portable calculation operates offline on the distinct counted states. It reads at most eight rows under the panel envelope. With three fixed sources and 18 fixed nodes, direct comparisons across anchors and support rows take quadratic work in $r$ for bounded token lengths. The reader keeps row sets for one anchor, keeps normalized rational factors across the nodes, and processes one coordinate product at a time. Integer arithmetic depends on the factors' bit lengths and exponents. The logarithm series iteration count grows linearly in requested precision and uses integer multiplications and divisions at that precision. The reader checks projected coordinate and aggregate bit costs before exponentiating. Across the six records, the producer declared 221–305 event comparisons, 13–186 maximum projected bits per coordinate, 348–5,172 aggregate projected bits, and 42,212,880–42,611,592 planned heap bytes. These are reconstructed **producer-plan quantities**, not elapsed time, observed memory or an upper bound for an arbitrary Python process. A separate program may use a different plan. Training, holdout scoring and resampling are outside this offline calculation. No release-estimator timing is reported. [Exact producer budget definitions](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md) · [Readback source](check.py)

## Evidence and open obligations

The source evidence supports the paper-defined categorical functional on the empirical distributions shown here. The original six fixed B identities and coordinate roster were bound before the paired run. A separately registered check fixed the three transformations and constant-target test. This public package is a subsequent, deterministic dissemination of those already inspected results. Its arithmetic reuses the earlier independent reference routine, using explicit row sets, integer Möbius inversion and directed-series enclosures. The earlier Rust producer used a separate implementation. They share the mathematical conventions, input data and parts of their software and review environment. The public reader also checks the raw B/C identities, all 108 names per case, five per-record digest fields, eight planned resource quantities, and an independently retained digest of the full 108-record projection for each case. Model-assisted implementation and review contributed to these records. No separately acquired human or institutional review is claimed. [Claim and premises](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md) · [Decision 3](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md)

The public files expose the recorded identity of the original source manifest. They do not contain its raw members, the writer executable, or the complete toolchain. Full source provenance and release/first-result custody remain open under obligation P1. The unresolved dependencies include the source of the native arithmetic build and the complete independent runtime. The general construction/verifier implication, formal source-to-executable correspondence, external custody, estimator calibration and population or application claims require separate evidence. The six bounded observations do not give a pass to any untested input. [Outstanding obligations](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/obligations.md)

**Checking the printed tables.** Run both commands from the study directory.

~~~sh
python3 -I -S -B check_printed.py
python3 -O -I -S -B check_printed.py
~~~

The program reads the printed base rows and node names, applies the stated transformations, and checks the six stored inputs. It uses rational series bounds to check the endpoint formula for every stored coordinate. [Print calculation](check_printed.py)

The three public file names and expected digests in the `digest_domains` section of the profile allow a reader with the repository to check the claim, mathematical registry and resource-policy sources independently. The standalone reader compares their expected digest fields in every C coordinate; readback of the complete manifest's source bytes requires a separate custody record. The profile preserves the status language from its earlier synthetic preparation. The 648 later paired observations are dated execution evidence for the six tables, with their own register. [Original profile](profile.json) · [Observed panel](panel.json)

On 25 November 2026, a separate study used the same paired reader on these six complete input and certificate pairs and four additional pairs. It also checked an altered rational product and a valid second certificate with wider intervals for the same input. Thus a certificate can enclose the same true values in more than one way. These observations concern ten named inputs. The universal relation between an accepted input and all its certificate coordinates remains open. [Ten-pair calculation and altered certificates](../categorical-state-token/README.md) · [Print edition](../../../output/pdf/categorical-state-token.pdf)

**Citation.** Sepehr Mahmoudian (2026), *Reading six three-source categorical shared-exclusion certificates*. Include the exact repository commit or release used and cite the defining paper separately. The project citation metadata applies to the software. [CITATION.cff](../../../CITATION.cff) · [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Print edition](../../../output/pdf/three-source-six-certificate-observations.pdf)
