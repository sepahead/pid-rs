# Sign constraints for the source-partition upper bound

Sepehr Mahmoudian · 19 November 2026

Does the mixed-integer program used in Section 7 of *Source partitions and
shared-exclusions information* allow the full absolute change of each atom?
A sign constraint that cuts off a large change can make a reported maximum
too small. The historical sign constant suffices for the exact entropy
models of all 30 recorded distributions. A four-symbol distribution shows
why the same rule can fail on a different distribution. The numerical
maxima remain exploratory. [Current report](../research/source-coupling-compression/EXPOSITION.md#7-results-and-limitations) · [Paired PDF](../../output/pdf/source-coupling-compression.pdf) · [Earlier correction](source-partition-bounds-correction-2026-11-18.md).

## Terms and assumptions

A **component atom** is an averaged informative or misinformative
shared-exclusions contribution at a node of the redundancy lattice. Each
component is nonnegative under the finite categorical construction of
Makkeh, Gutknecht and Wibral. Its signed atom is the informative component
minus the misinformative component. A **coalition** is a nonempty subset
of the three sources. A node is a nonempty family of coalitions. No distinct member contains another. The finite study uses three categorical
sources, a common categorical target, and natural logarithms. Each daily
or pooled table defines its own empirical probability law.
[Makkeh, Gutknecht and Wibral, arXiv:2002.03356v5, Theorem IV.3](https://arxiv.org/abs/2002.03356v5) · [Study design](../research/source-coupling-compression/EXPOSITION.md#6-recorded-data-design-and-exact-arithmetic).

| Symbol | Meaning |
|---|---|
| $S,S',T$ | Original source tuple, recoded source tuple and common target |
| $H,I$ | Shannon entropy and mutual information, in nats |
| $p^+,p^-,q^+,q^-$ | Original informative and misinformative atom vectors, followed by the two recoded vectors |
| $A,h$ | Seven coalition rows on 18 nodes, and the seven entropies for one component vector |
| $d,t,z$ | Signed change at one node, its modeled magnitude in nats and its binary sign variable |
| $a,b,c,e$ | Full-source entropies $H(S),H(S\mid T),H(S'),H(S'\mid T)$, respectively |
| $B,L,M$ | Sum of the four full-source entropies, change in joint mutual information, and nonnegative sign constant, all in nats |

## Which sign constant suffices?

Each of the four component vectors satisfies $A\pi=h$ and $\pi\ge0$. The
full-coalition row of $A$ consists of ones. Its entry of $h$ therefore gives
the total mass of that vector. The four totals are $a,b,c,e$. The signed
difference $d=p^+_j-p^-_j-q^+_j+q^-_j$ at each node $j$ satisfies

$$
-(b+c)\le d\le a+e.
$$

This interval holds at every point in the product of the four polytopes.
The true MGW component vectors give one point in that product. The
nonnegative full-source totals bound every coordinate, so the feasible
product is compact and its continuous absolute-sum objective has extrema.

The two rows at lines 84–87 of the retained optimizer are
$-d+t+Mz\le M$ and $d+t-Mz\le0$, with $t\ge0$ and $z\in\{0,1\}$.
When $z=1$ they require $0\le t\le\min(d,M-d)$.
When $z=0$ they require $0\le t\le\min(-d,M+d)$.
Thus for $|d|\le M$ the largest allowed $t$ is
$\min(|d|,M-|d|)$. A value $|d|>M$ admits no feasible $t$. At $d=0$
either sign permits $t=0$. At a fixed coordinate the true magnitude
$t=|d|$ is feasible exactly when $2|d|\le M$.
[Historical optimizer, lines 69–94](../research/source-coupling-compression/verification/component-sandwich-exploratory.py.txt#L69-L94).

Put $B=a+b+c+e$ and $L=(a-b)-(c-e)=I(S;T)-I(S';T)$. A sufficient
choice on the entire product is

$$
 M\ge 2\max(a+e,b+c)=B+|L|.
$$

The coarser choice $M=2B$ also suffices. A smaller constant can work when
the coalition constraints give a smaller coordinate range. Even when some
points are clipped, a surviving true maximizer can give the correct global
optimum. Checking the single observed MGW four-tuple supplies no such
guarantee. The historical program used $M=B+1$ when entropies were in nats.
The sufficient condition above holds whenever $|L|\le1$ nat. A conversion
to another logarithm base must also convert the one-nat margin.

## A finite counterexample to the general rule

Let source two be uniform on four symbols and take the target equal to that
source. Sources one and three are constant. Recode all sources to constants.
The only nonzero vector can be $p^+$, of total $a=\ln4$. The row for the
singleton coalition $\{2\}$ sums to $a$, just as the full row does. Thus
every positive entry must have a node containing the branch $\{2\}$.
The row for $\{1,3\}$ has total zero. It excludes every positive entry at
a node containing a branch made solely from the constant sources. Every
remaining branch other than $\{2\}$ would contain 2 and would be comparable
with $\{2\}$. This leaves only the one-branch node $\{\{2\}\}$ with a nonzero signed atom. Its value also appears in five cumulative sums. In each of those nodes every branch contains source two. A constant-only branch would make the matching event certain at every row.

The product of the four polytopes is therefore a single point. Its true
maximum is $\ln4$ nats, whereas $M=\ln4+1$ allows $t$ at most 1 nat at
the only nonzero coordinate. The inequality $\ln4>1$ follows by integrating
$1/x>1/2$ from 1 to 2, except at the right endpoint. Here $M$ exceeds $B$
and the exact optimum still changes. This example uses a four-symbol source
outside the recorded study's three binary sources.

## Exact margin on the thirty fixed laws

For the full-coalition signed redundancy, the study stores the original
and recoded joint mutual information as outward rational intervals.
If these are $[u,v]$ and $[r,s]$, their difference lies in
$[u-s,v-r]$. The greater absolute endpoint bounds $|L|$. Across all
30 hash-identified laws, the largest such bound occurred for the room
recording of 22 December 2017. In nats it is

$$
\frac{46409377455095502808402137}{441862387069146963355107328}<0.106<1.
$$

A separate direct interval for the full-coalition change intersects this
difference enclosure and stays within one nat on every law. The conclusion
uses the archived rational enclosures. HiGHS used binary64 logarithms,
entropy constraints and optimizer arithmetic. Its own comparison value for $D$
also uses floating-point logarithms. Section 6 of the study derives the
separate log-product enclosures for $D$. Exact feasibility and
optimality of its reported floating-point solutions remain open.
[Campaign index](../research/source-coupling-compression/evidence/campaign/REPORT.json) · [Room law](../research/source-coupling-compression/evidence/campaign/laws/room-2017-12-22.json) · [Historical study addendum](../research/source-coupling-compression/ADDENDUM-2026-10-30.md).

The fixed reference program takes the absolute path of the campaign directory.
From the repository root, run both modes with the same inputs.

```sh
study=audit/research/source-coupling-compression
python3 -I -S -B "$study/verification/check_partition_sign_margin.py" "$PWD/$study/evidence/campaign"
python3 -O -I -S -B "$study/verification/check_partition_sign_margin.py" "$PWD/$study/evidence/campaign"
```

One registered candidate was frozen before execution. A separate checker
verified 30 law results and 49 ordered pairs of signed coordinates and sign
constants under normal and optimized CPython 3.15.0. It checked both binary
signs against the two original inequalities. At zero both signs are
admissible. Each mode returned the same 8,609 output bytes, SHA-256
`c62c2bc2254a04890e8b41e9496623ac250b98cfe3eed33bb93b31b40f4825de`.
The program SHA-256 is
`5a42cda889e7068ca022cd902f27e6bbb51143e2613819f974b65dbc0656127a`,
and the local execution receipt has SHA-256
`e2b4a2bc82912066914af61738db2ab6a07ff34371325d43c21aeb99ef441a62`.
The study index and data were already available to the proposer and checker.
The original raw optimizer and its reported results retain their historical
scope. The first readback of the open data was retrospective.
[Reference program](../research/source-coupling-compression/verification/check_partition_sign_margin.py) · [Index](../research/source-coupling-compression/evidence/campaign/REPORT.json).

## Rust implementation and computational cost

The stable categorical Rust API computes signed MGW atoms. This sign-margin
reference is a Python verification program for the fixed three-source study.
The two target alphabets have four and two labels, and some tables occupy
fewer labels. The sign calculation has no Rust estimator or Python
binding. It hashes the 30 saved law files, scans up to 108 coordinate records
and seven coalition changes per law, and compares 49 rational sign pairs.
Its time grows with the bytes read and the bit cost of parsing, subtracting
and comparing rational numbers. Working memory holds one parsed law at a
time plus output proportional to the number of laws and sign pairs.
Invalid roster, digest or interval checks stop the program. The registered
executor bounded each process to 60 seconds and each output stream to 1 MiB.
No solver, fitting, resampling or production timing is reported. The
project's source-specific note estimates the separate costs of computing
the atoms themselves. [Implementation and cost](../research/source-coupling-compression/EXPOSITION.md#9-rust-implementation-and-computational-cost).

## Publication checks

The reviewed source PDF has 17 A4 pages and 209,894 bytes. The existing
native publication checker reproduced it twice in normal Python and twice
in optimized Python. Both full control runs and both dispatch-only runs
passed. Both cross-toolchain calls returned the required refusal status 2.
The author metadata and byline name Sepehr Mahmoudian. The three updated
producer bindings identify the Markdown, derived TeX and PDF. The 13 font
files, six notices and 13 figure source, data and derivative files reproduced
their preceding identities. [Publication checker](../../scripts/build-source-coupling-compression-pdf.py) · [Hostile controls](../../scripts/check-source-coupling-compression-pdf-self-test.py).

| Reviewed object | SHA-256 |
|---|---|
| Report Markdown | `ee0d62d900594703c615ee3918860dca61be0b1d0956e2fe20046469b79c6eec` |
| Projected TeX | `5a2ed645129b40ee47aca136898f69f454d18f05b3095bbbd0f0452a49377a89` |
| Report PDF | `e19cd850bdb39beffca53dd1281612edf632236cb057617c40245d2379b6964e` |
| Publication checker | `b6b0f66e716666f6dec7da927f15871330d39f89392e8746ec15d67ee51bc5df` |
| Normal and optimized exact-run receipts | `901a7c2ef971920bd6f4dad290c806e40d4e4c1245a23874f4140b78a259332c` and `f94e8a4b5f41fc641368b5ed7e5e22c374023ecbf4611638e9412764ec45e9ee` |

All 17 pages were rendered at 100 dpi in color and grayscale. Pages 12,
13 and 17 differed from the preceding PDF in both render sets. Each
received individual inspection in both modes and a 300 dpi detail check.
An earlier layout occupied an 18th page. A later layout split the small
prediction table across a page break. Both were superseded.

| Visual review lens | Observation on the selected rendering |
|---|---|
| Hierarchy | The sign argument sits under the refinement heading. The numerical interpretation precedes its table. |
| Typography | Magnitudes, subscripts, the factor of two and the cutoff render as mathematical text. |
| Grid | Values align under all four headings of the six-row table on page 13. |
| Spacing and rhythm | The exact sign-margin conclusion ends on page 12. The prediction table stays together on page 14. |
| Narrative order | The argument proceeds from the 28 constraints to the sign margin, numerical solver, results and replay. |
| Motif provenance | The existing local wrapper supplies the corner rosettes. |
| Motif coherence | Corners and page bands match the other sheets. |
| Ornamental restraint | Light decoration occupies the outer margins. |
| Palette identity | Section titles remain lapis, and secondary headings, links and captions use turquoise. |
| Pattern and data semantics | Corner geometry encodes no plotted value. |
| Color-redundant labels | The comparison chart gives values and legend labels, and the prediction table identifies the models by name. |
| Grayscale legibility | Mathematical signs, column headings and rows remain distinct. The prediction model bars share similar gray values and can be read by their order and the accompanying table. |
| Searchability and reading order | Text extraction preserves the sign argument, numerical qualifier and replay command in order. |
| Print fidelity | Vector text and rules remained sharp in the rendered details. A physical proof was unavailable. |
| A4 profile and embedded fonts | The checker observed PDF 1.7, 17 unrotated A4 pages and 20 embedded Unicode-mapped fonts. The PDF is untagged. |
| Link and action safety | The semantic checker admitted 46 actions. The new link names the derivation and the short archival link labels the exploratory program. |
| Deterministic reproduction | Four exact native builds generated the referenced bytes. |
| Source and derived assets | The Markdown generated the TeX body and the PDF. |
| Portable dependencies | The registered tools and existing local wrapper, filter, fonts and figures produced the result. |
| Normal and high-resolution inspection | All changed pages were reviewed at 100 dpi in both modes and in 300 dpi details. A contact sheet covered the complete document. |

The derivation, counterexample and publication review are model-assisted.
The proposer and checker share the recorded data and original mathematical
definitions. No independent human scientific or visual review was available.

Cite Sepehr Mahmoudian, *Source partitions and shared-exclusions information*
(2026), with this 19 November supplement and the containing repository commit
or release. Cite the defining MGW paper and software separately.
[CITATION.cff](../../CITATION.cff) · [Makkeh, Gutknecht and Wibral](https://doi.org/10.1103/PhysRevE.103.032149).
