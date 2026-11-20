# Reading six three-source categorical shared-exclusion certificates

**Sepehr Mahmoudian · 20 November 2026**

Can a reader recover each shared-information value from its count table? For six constructed tables, the reader reconstructs 108 positive rational products per table. Comparing each product with one gives the sign of its information value. A second routine bounds its natural logarithm divided by the total count. **All 648 reconstructions agreed with the records.** [Paired bytes](cases) · [Case identities](panel.json) · [Shared-exclusions definition](https://arxiv.org/abs/2002.03356v5)

## Terms and sources

| Term | Meaning here |
|---|---|
| Source, target, joint state | The three categorical sources $X_1,X_2,X_3$ and target $Y$ are the four columns of a joint state $z$. Each column entry is an ordered array of categorical tokens. Only equality within the same column matters. |
| Count, occupied support, empirical distribution | The positive integer $c_z$ is the multiplicity of state $z$. The occupied support consists of the $r$ distinct rows with positive counts. Their counts sum to the total $N$. A row has probability $c_z/N$. |
| Partial information decomposition (PID) | PID assigns contributions to combinations of sources. This study uses Makkeh, Gutknecht and Wibral’s categorical shared exclusions. Williams and Beer introduced the lattice with a different redundancy measure. |
| Mask, antichain, node | Masks 1, 2 and 4 denote the individual sources. Sums of those masks denote other nonempty subsets. A node is an antichain $\alpha$, a nonempty family of masks in which no mask properly contains another. |
| Event and mass | $E_\alpha(z)$ is the set of rows that match $z$ on every source in at least one mask of $\alpha$. $U_{\alpha,z}$ is its count, $T_z$ is the count with the same target as $z$, and $V_{\alpha,z}$ is the count meeting both requirements. |
| Cumulative, atom and component | A cumulative value is the total assigned to a node and the nodes below it. Its atom is the contribution left at that node after subtracting the atoms at all strictly lower nodes. Each has an informative ($+$), misinformative ($-$), and signed net ($\mathrm{net}$) component. |
| Product, natural logarithm, nat | $Q$ is an exact positive rational product. Its coordinate value is $\ln(Q)/N$, measured in nats. One bit equals $\ln 2$ nats. |
| Certificate and dyadic interval | B is the canonical input table. C is the producer's structured report, called a certificate in the file format. An interval endpoint is an integer coefficient times an integral power of two. The interval bounds the real-valued coordinate. |

### The defining papers

Makkeh, Gutknecht and Wibral define the pointwise exclusions, the informative and misinformative split, and the averaged quantities. Equation (4) joins individual-source matches by OR. Equations (6)–(8) allow a collection of source sets, with AND inside each set and OR across sets. See also Eqs. (12)–(15) and (17), and Theorems IV.2–IV.3. Those theorems give monotone component cumulatives and nonnegative component atoms. The net is their signed difference. A bit-valued result is multiplied by $\ln 2$ to obtain nats. The exact product representation, byte grammar, resource counters and reader are project constructions. The repository gives the mask order and each matrix entry used for these observations. [Makkeh, Gutknecht and Wibral, version 5](https://arxiv.org/abs/2002.03356v5) · [Version of record](https://doi.org/10.1103/PhysRevE.103.032149) · [Williams and Beer, 2010](https://arxiv.org/abs/1004.2515v1) · [Project conventions](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md)

If the question is only how much the whole source tuple tells us about the target, ordinary mutual information gives a single scalar directly from the counts. This study asks which named source combinations carry the informative and misinformative components and which signed contributions survive subtraction. That question fixes the shared-exclusions functional and the 18-node decomposition. The simple count-ratio calculation below provides a direct check on one of its coordinates.

## From counts to coordinates

Fix a supported row $z$ and a node $\alpha$. Matching all sources inside a mask means taking the intersection of their equality events. Matching at least one mask means taking the union of these intersections. The anchor row contributes to both $U_{\alpha,z}$ and $V_{\alpha,z}$, so every denominator below is positive. Multiplicity matters. The exact cumulative products are

$$
Q^+_\alpha=\prod_z (N/U_{\alpha,z})^{c_z},\qquad
Q^-_\alpha=\prod_z (T_z/V_{\alpha,z})^{c_z},\qquad
Q^{\mathrm{net}}_\alpha=Q^+_\alpha/Q^-_\alpha .
$$

The products run over the occupied support. Zero-count cells supply no terms. For example, taking $\ln(Q^+_\alpha)/N$ gives the empirical mean of the pointwise informative value $-\ln\widehat P(E_\alpha(z))$. The misinformative analogue uses the event probability conditional on the observed value of $Y$. Their difference is signed.

For two nodes $\beta,\alpha$, write $\beta\preceq\alpha$ when every mask of $\alpha$ contains some mask of $\beta$. The zeta matrix has one row for each cumulative and one column for each atom, with $Z_{\alpha\beta}=1$ if $\beta\preceq\alpha$ and zero otherwise. Its inverse $\mu=Z^{-1}$ gives the atom product at $\alpha$ as $\prod_\beta (Q^u_\beta)^{\mu_{\alpha\beta}}$ for component $u$. The reader derives the 18-node order from sets of Boolean agreement patterns and checks both inverse identities. Each key lists its masks in increasing order as two-digit hexadecimal numbers. For example, `02+04` is a union of two one-source events, whereas `06` requires both source matches. The reader checks each key and mask tuple against the registered sequence. Two scopes times three components times 18 nodes give **108 named coordinates per table**. A product below, equal to, or above one gives the corresponding negative, zero, or positive sign exactly. [Registry and product construction](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md) · [Executable arithmetic](arithmetic.py)

**Exact values in nats.** For $x=\ln(Q)/N$, $Q=1$ gives $x=0$. Otherwise $e^{N|x|}=\max(Q,1/Q)$ is rational. If $|x|=a/b$ for positive integers $a,b$, raising that rational to the power $b$ would give $e^{Na}$. Every positive integer power of $e$ is irrational. Thus every nonzero coordinate, including a negative atom, is irrational in nats and cannot equal a binary64 rounding midpoint. This conclusion gives no lower bound on its distance from a midpoint. [Hermite (1873), §III](https://doi.org/10.3931/e-rara-101019) · [Count tables and rounding](../normalized-shannon-arithmetic/README.md)

### Bounding the logarithm

The reader also bounds the magnitude without relying on a floating-point logarithm. For $Q=2^e a/b$ with $1\le a/b<2$, set $t=(a-b)/(a+b)$. Then $\ln(a/b)=2\sum_{j\ge0}t^{2j+1}/(2j+1)$. After $m$ terms, the omitted tail is at most $2t^{2m+1}/[(2m+1)(1-t^2)]$. Here $0\le t\le1/3$, including the separate $\ln 2$ evaluation at $t=1/3$. The implementation rounds fixed-point lower operations down and upper operations up, adds a tail allowance, and combines bounds with $e\ln 2$ in the order required by the sign of $e$. It then divides by $N$ with directed rounding. It requires the **entire independent enclosure** to lie inside the producer's interval and requires the producer width to be at most $2^{-160}$ nats. For $Q=1$ the independent interval is exactly $[0,0]$. For all 648 coordinates, the first precision tested by the second routine, 256 bits, sufficed for containment. [Interval implementation](arithmetic.py) · [Original width and schedules](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

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
~~~

The first command reports the six cases, 648 coordinates and the four relation counts. The third writes the weighted table's 108 mathematical records to standard output. Each includes the stable name and masks, reduced numerator and denominator, exact sign, both pairs of normalized endpoints, chosen precision and containment result. The command checks the complete six-case panel before returning the requested case. All fixed-file hashes include the terminal newline. A failure exits nonzero. [Reader](check.py) · [Case, original-run and observation digest register](panel.json) · [Schema and resource limits](profile.json)

**Reading the input and output files.** B contains the input schema, definition revision, three sources, units and lexicographically ordered positive rows. Each row identifies three ordered token arrays, one target array and one positive, minimally written decimal count string. C names the report schema and contains a payload of version/registry identifiers, eight planned resource counters, and its 108 coordinates. Each coordinate repeats its input, claim, registry, policy and source-manifest SHA-256 bindings. Its strictly positive reduced product is encoded with decimal strings. A normalized nonzero dyadic endpoint has an odd coefficient. Zero has coefficient `"0"` and exponent zero. The fixed ASCII property names have canonical order and each file ends with exactly one line feed. The portable reader also imposes a small envelope specific to this panel: B at most 4,096 bytes, C at most 131,072 bytes, eight occupied rows, three decimal digits per count, and an endpoint exponent of absolute value at most 2,048. The project has a separate proof of the canonical input encoding. [Wire rules](profile.json) · [Canonical count-table encoding](../categorical-count-table-encoding/README.md) · [JSON Canonicalization Scheme, RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785)

### Checks on altered records

The control program constructs a new two-row table, obtains 108 admissible test records, then checks the reasons for 20 refusals. These include missing or replaced original files, a valid reduced fraction with the wrong value, a sign error, excess width, interval overlap without containment, negative or non-normalized zero, swapped or missing coordinates, duplicate or missing input rows, changed source binding or work counter, and duplicate JSON fields. Testing the mathematical predicate on deliberately altered synthetic records allows its own failure reasons to be observed after the original-file digest check. The synthetic control uses this package's arithmetic to create its input report. It tests rejection behavior and contributes zero cases to the six original observations. [Control source](controls.py)

## Rust implementation and computational cost

In Rust, `discrete_sxpid3_averaged` is available in `pid_core::stable::categorical` with default features. Its three discrete source matrices and target matrix have the same $N$ observation rows. To represent these tables, repeat each encoded complete row $c_z$ times. The call returns 18 averaged atoms keyed by source masks. The certificate has both cumulative and atom coordinates. Budgeted and cancellation-aware variants are available. With $D$ categorical coordinates across the four matrices, materializing the Rust inputs requires space of order $ND$. After grouping $r$ occupied states, event scans compare the fixed 18 nodes at each anchor against all occupied states, including the anchor, with at most order $r^2 D$ coordinate comparisons. Subset-information histograms and grouping add separate work. The averaged route returns floating-point values in nats. The research certificate producer used exact integer/rational products and directed multiprecision logarithms; its executable and full source manifest are outside this public package. Software that compares the stable estimator with these observations must map explicit source masks and keys, respect each row's multiplicity and compare the same mathematical quantity. This package makes no binary64 refinement claim. [Rust API implementation](../../../crates/pid-core/src/sxpid.rs) · [Engineering cost reference](../../../RUST_IMPLEMENTATION_AND_COST.md) · [Method catalog](../../../METHODS.md) · [Source-order caution](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

The portable calculation operates offline on the distinct counted states. It reads at most eight rows under the panel envelope. With three fixed sources and 18 fixed nodes, direct comparisons across anchors and support rows take quadratic work in $r$ for bounded token lengths. The reader keeps row sets for one anchor, keeps normalized rational factors across the nodes, and processes one coordinate product at a time. Integer arithmetic depends on the factors' bit lengths and exponents. The logarithm series iteration count grows linearly in requested precision and uses integer multiplications and divisions at that precision. The reader checks projected coordinate and aggregate bit costs before exponentiating. Across the six records, the producer declared 221–305 event comparisons, 13–186 maximum projected bits per coordinate, 348–5,172 aggregate projected bits, and 42,212,880–42,611,592 planned heap bytes. These are reconstructed **producer-plan quantities**, not elapsed time, observed memory or an upper bound for an arbitrary Python process. A separate program may use a different plan. Training, holdout scoring and resampling are outside this offline calculation. No release-estimator timing is reported. [Exact producer budget definitions](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md) · [Readback source](check.py)

## Evidence and open obligations

The source evidence supports the paper-defined categorical functional on the empirical distributions shown here. The original six fixed B identities and coordinate roster were bound before the paired run. A separately registered check fixed the three transformations and constant-target test. This public package is a subsequent, deterministic dissemination of those already inspected results. Its arithmetic reuses the earlier independent reference routine, using explicit row sets, integer Möbius inversion and directed-series enclosures. The earlier Rust producer used a separate implementation. They share the mathematical conventions, input data and parts of their software and review environment. The public reader also checks the raw B/C identities, all 108 names per case, five per-record digest fields, eight planned resource quantities, and an independently retained digest of the full 108-record projection for each case. AI-assisted implementation and review contributed to these records. No separately acquired human or institutional review is claimed. [Claim and premises](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md) · [Decision 3](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md)

The public files expose the recorded identity of the original source manifest. They do not contain its raw members, the writer executable, or the complete toolchain. Full source provenance and release/first-result custody remain open under obligation P1. The unresolved dependencies include the source of the native arithmetic build and the complete independent runtime. The general construction/verifier implication, formal source-to-executable correspondence, external custody, estimator calibration and population or application claims require separate evidence. The six bounded observations do not give a pass to any untested input. [Outstanding obligations](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/obligations.md)

The three public file names and expected digests in the `digest_domains` section of the profile allow a reader with the repository to check the claim, mathematical registry and resource-policy sources independently. The standalone reader compares their expected digest fields in every C coordinate; readback of the complete manifest's source bytes requires a separate custody record. The profile preserves the status language from its earlier synthetic preparation. The 648 later paired observations are dated execution evidence for the six tables, with their own register. [Original profile](profile.json) · [Observed panel](panel.json)

**Citation.** Sepehr Mahmoudian (2026), *Reading six three-source categorical shared-exclusion certificates*. Include the exact repository commit or release used and cite the defining paper separately. The project citation metadata applies to the software. [CITATION.cff](../../../CITATION.cff) · [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Print edition](../../../output/pdf/three-source-six-certificate-observations.pdf)
