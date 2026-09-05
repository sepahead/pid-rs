# MGW v5 source correspondence and Program A semantic bridge

## Disposition

**Owner-controlled source review recorded; Program A remains partial/open; Programs A--E closed:
0 of 5.**

This document maps the categorical shared-exclusions definitions in Makkeh, Gutknecht, and Wibral
(MGW) to the frozen three-source certificate conventions in this repository. It also derives the
finite three-source carrier, order, event truth table, target intersection, count inequalities,
Möbius matrix, and source-label symmetries from small definitions. The accompanying checker
reconstructs those finite objects without importing the Rust implementation or the earlier bounded
audit's generated tables.

This is a substantive advance on obligation S1 and the source-blind parts of D2, L1, and L2. It is
not independent human custody, a machine interpretation of the paper, a concrete Lean proof, a
second-solver proof, a parser proof, a logarithm certificate, or a Rust refinement proof. For those
reasons it does not close Program A or the complete SxPID3 certificate.

## 1. Scientific identity and source custody

The mathematical object is the finite categorical shared-exclusions functional
$i^{\mathrm{sx}}_\cap$ introduced by:

> Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral, "Introducing a differentiable measure
> of pointwise shared information," *Physical Review E* 103, 032149 (2021),
> [DOI](https://doi.org/10.1103/PhysRevE.103.032149),
> [arXiv v5](https://arxiv.org/abs/2002.03356v5).

The audited source identities are:

| Object | Exact identity | Custody boundary |
|---|---|---|
| arXiv v5 PDF | 1,002,114 bytes; SHA-256 `5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6` | Hash-only observation; the PDF is not copied into this repository |
| arXiv v5 source archive | 489,040 bytes; SHA-256 `6420b90ccd5c1e971e19b41c24676b0ed3276aa47f1b3ceadc49bac219bf9584` | Hash-only observation; the archive is not copied into this repository |
| `apstemplate.tex` within that archive | 142,869 bytes; SHA-256 `60ac061c9874149d65d6fab21e627ca66f96d9e4d4990d1ee243632776faaf61` | Reviewed source member; its bytes are not copied into this repository |

A digest can show equality to bytes seen during this review. It does not authenticate arXiv, the
authors, the reviewer, a time, or the mathematical interpretation. The versioned DOI and arXiv
locations provide retrieval routes; they are not an external transparency or independent-custody
record.

### Reproducible owner-controlled acquisition replay

On 2026-09-03 UTC, a fresh HTTPS replay downloaded the revision-5 PDF and source archive into a
new temporary directory. The new bytes matched every size and SHA-256 value above. The archive
contained exactly one top-level member named `apstemplate.tex`, and streaming that member produced
the recorded 142,869-byte digest. The commands, with the temporary-directory prefix omitted, were:

```text
curl --proto '=https' --tlsv1.2 -fL --retry 2 --connect-timeout 15 --max-time 120 -o 2002.03356v5.pdf https://arxiv.org/pdf/2002.03356v5
curl --proto '=https' --tlsv1.2 -fL --retry 2 --connect-timeout 15 --max-time 120 -o 2002.03356v5-source.tar https://export.arxiv.org/e-print/2002.03356v5
shasum -a 256 2002.03356v5.pdf 2002.03356v5-source.tar
wc -c 2002.03356v5.pdf 2002.03356v5-source.tar
test "$(tar -tf 2002.03356v5-source.tar | grep -Fxc 'apstemplate.tex')" -eq 1
tar -xOf 2002.03356v5-source.tar apstemplate.tex | shasum -a 256
tar -xOf 2002.03356v5-source.tar apstemplate.tex | wc -c
```

This is reproducible local acquisition evidence, not independent custody, authenticated transport
history, or trusted time. The temporary downloads are deliberately outside the repository; the
machine record retains the commands, results, exact identities, and this limitation.

### Provenance vocabulary

- **Paper-defined:** the MGW event, local shared information, informative/misinformative split,
  redundancy-lattice relation, component atoms, and joint-law average.
- **Paper-derived:** replacing probabilities by empirical counts and changing bits to nats.
- **Classical:** finite-poset zeta and Möbius inversion. The repository uses the standard incidence
  algebra construction; see Gian-Carlo Rota, "On the foundations of combinatorial theory I. Theory
  of Möbius functions," *Zeitschrift für Wahrscheinlichkeitstheorie* 2 (1964),
  [DOI](https://doi.org/10.1007/BF00531932).
- **Project-defined:** stable hexadecimal keys, the 108-expression audit registry, this source map,
  deterministic digests, executable reconstruction, and hostile mutation suite.

"New in pid-rs" below means new project analysis or assurance. It is not a claim that pid-rs
invented MGW shared exclusions, the redundancy lattice, or Möbius inversion, and it is not a
scientific-priority claim.

## 2. The notation trap: Equation (4) is not Equation (6)

This is the most important semantic distinction in the bridge.

MGW first asks for information shared by a set $a$ of *individual* source realizations. In PDF
Equation (4), source member $i\in a$ contributes the elementary statement $S_i=s_i$, and these
statements are joined by OR:

$$
\mathcal W_a
=
\bigvee_{i\in a}(S_i=s_i).
\tag{2.1}
$$

For example, if $a=\{1,2\}$, Equation (2.1) is

$$
(S_1=s_1)\lor(S_2=s_2).
$$

MGW then asks for information shared by *multiple collections* of source realizations. If a
collection $a_j$ is observed jointly, its elementary statement is a conjunction. PDF Equation (6)
therefore gives the disjunctive normal form

$$
\mathcal W_{a_1,\ldots,a_m}
=
\bigvee_{j=1}^{m}
\bigwedge_{i\in a_j}(S_i=s_i).
\tag{2.2}
$$

Consequently, the following two redundancy-lattice nodes are different:

$$
\alpha_{\mathrm{shared}}=\{\{1\},\{2\}\},
\qquad
\alpha_{\mathrm{joint}}=\{\{1,2\}\}.
$$

Their events are

$$
E_{\alpha_{\mathrm{shared}}}(z)
=
\{S_1=s_1\}\cup\{S_2=s_2\},
$$

and

$$
E_{\alpha_{\mathrm{joint}}}(z)
=
\{S_1=s_1\}\cap\{S_2=s_2\}.
$$

The first event corresponds to MGW Equation (4) with $a=\{1,2\}$, or equivalently Equation (6)
with two singleton collections. The second corresponds to Equation (6) with one joint collection.
Reusing one symbol $a$ for both roles would silently exchange redundancy between two sources with
self-information of their joint source. The repository therefore encodes a collection as a
nonzero source mask and an antichain as a collection of masks.

### Minimal distinguishing example

Fix the keyed source realization $(s_1,s_2,s_3)=(1,1,0)$ and inspect a row with
$(s'_1,s'_2,s'_3)=(1,0,1)$. Its equality bits are `100` in source order $1,2,3$. Then

$$
1\lor0=1,
\qquad
1\land0=0.
$$

Thus key `01+02` includes the row, while key `03` excludes it. No probability calculation is
needed to distinguish the semantics.

## 3. Exact source anchors and local meanings

Line numbers refer to the audited `apstemplate.tex` source member. PDF page numbers refer to the
19-page arXiv v5 file and include its first displayed page as page 1.

| ID | Primary anchor | Audited source lines | Local meaning | Inference that is not permitted |
|---|---|---:|---|---|
| `MGW-SUBSET-OR` | PDF page 2, Equation (4) | 67--71 | OR among individual source statements; represented by an antichain of singleton masks | Do not replace AND inside a collection in Equation (6) |
| `MGW-DNF-EVENT` | PDF page 3, Equations (5)--(8) | 73--87 | AND inside each source collection; OR across collections | Permuting collections is not the same statement as relabeling sources |
| `MGW-EXCLUSION-FORM` | PDF page 4, Equation (12) | 121--138 | Equivalent shared-exclusion expression for the same local quantity | Formula equivalence is not an implementation-refinement proof |
| `MGW-ZETA-RELATION` | PDF page 5, Equation (13) | 143--154 | A cumulative at $\alpha$ is the sum of atoms at $\beta\preceq\alpha$ | The displayed relation alone does not choose array orientation |
| `MGW-COMPONENT-SPLIT` | PDF page 5, Equations (14a), (15a), and (15b) | 158--174 | Net equals informative minus misinformative; each local component is nonnegative | Component nonnegativity does not imply net nonnegativity |
| `MGW-AVERAGING` | PDF page 8, Equation (17) | 248--266 | Average local values with the complete joint source-target law | Do not use event probability or equal supported-key weights |
| `MGW-ANTICHAIN-ORDER` | PDF page 13, Appendix A order display | 562--570 | $\alpha\preceq\beta$ iff every collection in $\beta$ contains one collection in $\alpha$ | Do not reverse the order and compensate with a transposed matrix |
| `MGW-MOBIUS` | PDF page 14, Appendix Equation (A1) and Theorem A.1 | 597--607 | Invert the down-set sum separately for informative and misinformative components | An inverse matrix does not establish event or code correspondence |
| `MGW-COMPONENT-LATTICE-MONOTONICITY` | PDF page 6, Theorem IV.2; proof in Appendix A | 208--211, 638--652 | Informative and misinformative cumulative functions increase monotonically on the redundancy lattice | Do not infer atom nonnegativity or signed-net monotonicity from this theorem |
| `MGW-COMPONENT-ATOM-NONNEGATIVITY` | PDF page 6, Theorem IV.3; proof in Appendix A | 212--215, 797--806 | Pointwise informative and misinformative atoms on the full lattice are nonnegative | Do not transfer to signed-net atoms, truncated carriers, or another PID |

The source contains occasional notation and index inconsistencies, such as using $n$ where the
number of collections is $m$ in the prose around the general event. The surrounding definition,
expanded formulas, appendix, and examples consistently determine Equation (2.2). This bridge uses
that semantic statement, not the typographical index. It does not claim a mathematical flaw in the
published functional.

### Semantic-transfer ledger

The preceding table records the source meaning, repository analogue, and forbidden inference.
The following table records the remaining three transfer obligations explicitly. “Preserved”
means an assumption is carried unchanged into the local statement. “Changed” names a declared
representation or unit change, not an implicit theorem transfer. “Required evidence” is the next
evidence needed before the local statement can support a stronger implementation or formal claim.

| ID | Preserved assumptions | Changed conventions | Required evidence |
|---|---|---|---|
| `MGW-SUBSET-OR` | Finite categorical sources; equality statements for individual realized values | A paper subset becomes singleton bit masks; bits-to-nats occurs only later | Independent source review and formal event/parser-to-Rust refinement |
| `MGW-DNF-EVENT` | Nonempty finite source collections at one realized tuple | Collections become sorted nonzero masks and a stable hexadecimal key | Formal event semantics and compiled refinement; the truth table covers only the Fin-3 equality kernel |
| `MGW-EXCLUSION-FORM` | Same source event, realized target, and positive log-ratio probabilities | The exclusion form is a mathematical cross-check, not this checker's event implementation | Algebraic correspondence and numerical/compiled comparison if used operationally |
| `MGW-ZETA-RELATION` | Complete finite carrier and published redundancy order | Cumulatives are rows, atoms columns, in a declared stable key order | Concrete carrier completeness and order-orientation evidence |
| `MGW-COMPONENT-SPLIT` | Paper-defined pointwise plus/minus split on supported events | Bits become nats by the positive factor $\ln2$ | Componentwise correspondence and a separate analysis for signed-net claims |
| `MGW-AVERAGING` | Complete joint source-target expectation over positive-mass keys | Population masses become empirical weights $c_z/N$ for the declared plug-in law | Producer/parser refinement for the same complete-joint weighting |
| `MGW-ANTICHAIN-ORDER` | Full carrier and published subset quantifiers | Subsets become masks and nodes use a project-defined serialization | Carrier completeness and an independently encoded order check tied to the source |
| `MGW-MOBIUS` | Finite-poset inversion on the complete order, separately by component | Exact rational elimination uses the declared matrix orientation | Two-sided inverse plus an independently established carrier/order/implementation link |
| `MGW-COMPONENT-LATTICE-MONOTONICITY` | Full lattice, finite categorical law, and separate plus/minus cumulatives | Notation and positive unit scale only; no strengthening | Source-to-formal theorem correspondence before mechanized-proof credit |
| `MGW-COMPONENT-ATOM-NONNEGATIVITY` | Complete lattice and pointwise plus/minus atoms | Notation and positive unit scale only; signed net remains outside the theorem | Publication-to-formal correspondence on the complete carrier |

## 4. Local event and empirical count map

Fix exactly three ordered categorical sources $S_1,S_2,S_3$, a finite categorical target $T$, and
a supported key

$$
z=(s_1,s_2,s_3,t).
$$

For a nonzero bit mask $a\in\{1,\ldots,7\}$, define

$$
E_a(z)
=
\bigcap_{i:\,a_i=1}\{z':s'_i=s_i\}.
\tag{4.1}
$$

For a nonempty antichain $\alpha$ of such masks, define

$$
E_\alpha(z)
=
\bigcup_{a\in\alpha}E_a(z).
\tag{4.2}
$$

Equation (4.2) is exactly the logical shape in MGW Equation (6). The source masks `01`, `02`, and
`04` denote $S_1$, $S_2$, and $S_3$. For example,

$$
E_{\mathtt{03+04}}(z)
=
(\{S_1=s_1\}\cap\{S_2=s_2\})
\cup
\{S_3=s_3\}.
$$

Let a finite empirical table have nonnegative integer row counts $c_x$ and a positive count at the
keyed row $c_z>0$. Define

$$
N=\sum_x c_x,
\qquad
U_{\alpha,z}=\sum_xc_x\mathbf 1\{x\in E_\alpha(z)\},
$$

$$
T_z=\sum_xc_x\mathbf 1\{t_x=t\},
\qquad
V_{\alpha,z}=\sum_xc_x\mathbf 1\{x\in E_\alpha(z),\ t_x=t\}.
\tag{4.3}
$$

These are integer forms of $N\widehat P(E_\alpha)$, $N\widehat P(T=t)$, and
$N\widehat P(E_\alpha\cap\{T=t\})$.

### Generic count lemma

For every finite categorical row set and every antichain $\alpha$,

$$
0<c_z\le V_{\alpha,z}\le U_{\alpha,z}\le N,
\qquad
V_{\alpha,z}\le T_z\le N.
\tag{4.4}
$$

**Proof.** At the keyed row, every selected equality statement in every branch is true, and its
target equals $t$. Hence that row contributes $c_z$ to $V$, $U$, $T_z$, and $N$. For any other
row,

$$
\mathbf1\{E_\alpha\land(T=t)\}
\le
\mathbf1\{E_\alpha\},
$$

and

$$
\mathbf1\{E_\alpha\land(T=t)\}
\le
\mathbf1\{T=t\}.
$$

Multiplying these indicator inequalities by $c_x\ge0$ and summing proves Equation (4.4). This
argument is independent of alphabet labels and cardinalities: a comparison row is compressed to
three source-equality bits and one target-equality bit. It is not a proof that arbitrary input bytes
decode to such a table; canonical decoding remains obligation D1. $\square$

### Why target intersection is indispensable

Suppose the source event is true on a comparison row but the comparison target differs from the
keyed target. The row contributes to $U$ and does not contribute to $V$. A mutant that computes
$V=U$ on this row changes

$$
\widehat P(T=t\mid E_\alpha)
=
\frac{V}{U}
$$

and therefore changes both the misinformative and signed-net terms. The checker explicitly covers
all 288 combinations of 18 antichains, eight source-equality patterns, and two target-equality
values.

## 5. From MGW probabilities to count-cleared local formulas

MGW uses base-2 logarithms. Substituting the empirical masses from Equation (4.3) gives local
values in bits:

$$
i^+_\alpha(z)=\log_2\frac{N}{U_{\alpha,z}},
\tag{5.1}
$$

$$
i^-_\alpha(z)=\log_2\frac{T_z}{V_{\alpha,z}},
\tag{5.2}
$$

and

$$
i^{\mathrm{sx}}_\alpha(z)
=i^+_\alpha(z)-i^-_\alpha(z)
=\log_2\frac{NV_{\alpha,z}}{U_{\alpha,z}T_z}.
\tag{5.3}
$$

The repository uses natural logarithms, so the corresponding values in nats are

$$
i^{u,\mathrm{nat}}_\alpha(z)
=(\ln2)i^{u,\mathrm{bit}}_\alpha(z),
\qquad u\in\{+,-,\mathrm{sx}\}.
\tag{5.4}
$$

Because $\ln2>0$, this unit conversion preserves exact zeros, strict signs, and every finite linear
identity. It changes magnitudes and must never be omitted from a numerical comparison.

The variable-level average is

$$
C^u_\alpha
=
\sum_{z:\,c_z>0}\frac{c_z}{N}i^u_\alpha(z).
\tag{5.5}
$$

Equation (5.5) follows from MGW Equation (17). It is not

$$
\frac1{|\{z:c_z>0\}|}\sum_{z:c_z>0}i^u_\alpha(z).
$$

For example, counts $(2,1)$ and local values $(0,1)$ give the correct average $1/3$ but the
equal-supported-key mutant gives $1/2$.

## 6. Complete three-source carrier

The nonempty subsets of three ordered sources are the seven nonzero masks

$$
\{1,2,3,4,5,6,7\}.
$$

A candidate is an antichain when no two distinct masks encode comparable source subsets. The
checker enumerates all $2^7-1=127$ nonempty mask families and filters by that definition. It does
not start from the expected list. The result contains exactly 18 antichains:

| Key | Collections |
|---|---|
| `01` | $\{\{1\}\}$ |
| `02` | $\{\{2\}\}$ |
| `03` | $\{\{1,2\}\}$ |
| `04` | $\{\{3\}\}$ |
| `05` | $\{\{1,3\}\}$ |
| `06` | $\{\{2,3\}\}$ |
| `07` | $\{\{1,2,3\}\}$ |
| `01+02` | $\{\{1\},\{2\}\}$ |
| `01+04` | $\{\{1\},\{3\}\}$ |
| `01+06` | $\{\{1\},\{2,3\}\}$ |
| `02+04` | $\{\{2\},\{3\}\}$ |
| `02+05` | $\{\{2\},\{1,3\}\}$ |
| `03+04` | $\{\{1,2\},\{3\}\}$ |
| `03+05` | $\{\{1,2\},\{1,3\}\}$ |
| `03+06` | $\{\{1,2\},\{2,3\}\}$ |
| `05+06` | $\{\{1,3\},\{2,3\}\}$ |
| `01+02+04` | $\{\{1\},\{2\},\{3\}\}$ |
| `03+05+06` | $\{\{1,2\},\{1,3\},\{2,3\}\}$ |

The count 18 is also $M(3)-2$, where $M(3)=20$ is the third Dedekind number and the excluded
objects are the empty antichain and the antichain containing the empty source subset. This identity
is a cross-check, not the enumeration proof.

The 166 cited elsewhere is $M(4)-2$, the corresponding count for **four** sources. It does not
describe three-source atoms or the 108-expression audit.

## 7. Order, zeta orientation, and Möbius inversion

For antichains $\alpha$ and $\beta$, MGW Appendix A states

$$
\alpha\preceq\beta
\quad\Longleftrightarrow\quad
\forall b\in\beta\ \exists a\in\alpha:\ a\subseteq b.
\tag{7.1}
$$

With rows indexed by cumulative node $\alpha_i$ and columns indexed by atom node $\alpha_j$, the
repository convention is

$$
Z_{ij}=\mathbf1\{\alpha_j\preceq\alpha_i\},
\tag{7.2}
$$

so MGW Equation (13) becomes

$$
c=Z\pi.
\tag{7.3}
$$

The executable reconstruction finds 129 ones among all $18^2=324$ entries. Exact rational Gaussian
elimination gives an integer inverse

$$
M=Z^{-1}
$$

with 65 nonzero entries and verifies both

$$
MZ=I_{18}
\qquad\text{and}\qquad
ZM=I_{18}.
\tag{7.4}
$$

For each component $u\in\{+,-,\mathrm{sx}\}$,

$$
\pi^u=Mc^u.
\tag{7.5}
$$

The plus and minus inversions are separate. Linearity then gives

$$
\pi^{\mathrm{sx}}=\pi^+-\pi^-.
\tag{7.6}
$$

An inverse identity alone is insufficient: reversing Equation (7.1), transposing $Z$, and inverting
the transposed matrix would still produce a mathematically invertible pair. The semantic row/column
meaning in Equations (7.1)--(7.3) is therefore part of the checked record.

### Self-redundancy and the full joint node

At a single collection $a$, MGW self-redundancy reduces shared information to the ordinary local
mutual information of the joint source $S_a$. At key `07`, the event fixes all three sources, so
the cumulative net quantity is the local mutual information of $(S_1,S_2,S_3)$ about $T$. These
facts follow from the event definition. They do not identify any particular atom with the complete
mutual information; the latter is the zeta sum of the appropriate down-set atoms.

## 8. Source-label permutations

There are $3!=6$ permutations of the ordered source labels. A permutation maps each bit in a mask,
sorts the mapped masks inside an antichain, and therefore induces a bijection on the 18 keys. The
checker derives every map and verifies:

1. antichains map to antichains;
2. the map is a bijection of the carrier;
3. Equation (7.1) is preserved for all 324 ordered pairs; and
4. event truth is preserved for every key and every source-equality pattern when the pattern is
   relabeled by the same permutation.

This is source-label equivariance derived from subset and equality semantics. It is not MGW's
symmetry axiom by itself. That axiom permits reordering the collections presented at one node; it
does not by itself state invariance under renaming the source variables and their data columns.

## 9. What the executable bridge checks

The canonical checker
[`check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py`](../../scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py)
uses only the Python standard library. From the three source bits and the definitions above, it
reconstructs:

| Reconstructed object | Exact census |
|---|---:|
| Nonzero source masks | 7 |
| Nonempty antichains | 18 |
| Ordered antichain comparisons | 324 |
| True zeta/order entries | 129 |
| Nonzero integer Möbius entries | 65 |
| Source-label permutations | 6 |
| Source-event truth cases | $18\times8=144$ |
| Source-event/target truth cases | $18\times8\times2=288$ |

For the generic count lemma, the executable part checks every Boolean coefficient premise in the
three-source equality kernel: intersection is bounded by each parent indicator, and the all-equal
keyed pattern belongs to every event. The written proof then multiplies those pointwise facts by
arbitrary coefficients $c_x\ge0$ and sums them. The checker does not enumerate every possible
finite alphabet or arbitrary real/count vector, and it must not be cited as though it did.

It then requires fixed digests for the derived key sequence, complete zeta matrix, complete Möbius
matrix, event truth table, and all six permutation maps. These fixed digests are regression
anchors. The proof-relevant checks are the reconstructions and identities executed before the
digest comparison.

As a separate compatibility edge, the checker reads three exact, hash-bound repository files: the
frozen conventions, the primary bounded route, and the separately implemented bounded route. It
parses only literal registries from the two Python files and the carrier, zeta, and Möbius tables
from the conventions document. It requires the newly derived 18 keys, every zeta entry, and every
Möbius coefficient to match the frozen conventions and the primary route; it also requires the
second route's key registry and its 129/65 censuses to match. No route computation is imported into
the reconstruction. This closes an unrecorded-registry-drift risk. It does **not** make the routes
logically independent, compare the event implementation, execute either bounded audit, or compare
compiled Rust.

The checker accepts no alternate record path, source-map path, root, or command-line option. That
restriction closes the exact input-redirection weakness preserved in the historical v1/v2
false-green archive. The self-test operates on isolated copies with explicitly mutated canonical
files; no production option is added merely to make mutation testing convenient.

The checker compares every decoded record field and each of its six parsed compatibility-registry
objects by exact type, shape, and value, recursively. This is necessary because ordinary Python
equality makes `False == 0`, `5.0 == 5`, and the corresponding tuple and census substitutions
compare equal. The pre-correction committed v4 checker accepted two coherently resealed JSON status
substitutions and two coherently resealed Python-literal substitutions. The retained
[typed-equality failure record](failures/python-status-type-coercion.md) gives the exact old
identities, four minimal reproductions, impact, and repair. These were real verification-chain
defects, not changes to the reconstructed mathematics or the open Program disposition.

### Historical false-green coverage and the remaining reseal boundary

The [inert historical-checker disposition](../../audit/archive/sxpid3-s1-historical-checkers-v1/DISPOSITION.md)
retains seven mutation recipes and fourteen mode-specific observations from two superseded
checkers. It is non-authoritative negative evidence, is not executed by the current gate, and earns
zero closure credit. The current self-test maps each historical identifier to a current control
rather than treating a generic passing mutation suite as sufficient evidence:

| Historical identifier | Current control |
|---|---|
| `V1-FG-INPUT-ROUTE` | Reject the former `--record` alternate-input route in normal and optimized execution |
| `V1-FG-SCOPE-CUTS` | Mutate and coherently reseal the canonical record after deleting a boundary; semantic validation rejects it |
| `V1-FG-ANCHOR-SEMANTICS` | Mutate and reseal an anchor role; the exact anchor registry rejects it |
| `V1-FG-CLAIM-SEMANTICS` | Escalate and reseal the target status; the exact open-status registry rejects it |
| `V1-FG-ROLE-TITLE` | Change and reseal the primary-source title; the source-identity registry rejects it |
| `V2-FG-INPUT-ROUTE-VIA-SOURCE-RECORD` | Reject the former `--source-record` alternate-input route in normal and optimized execution |
| `V2-FG-SCOPE-CUTS-VIA-SOURCE-RECORD` | Use the same canonical-record boundary mutation after the alternate route has been removed; semantic validation rejects it |

The production checker uses a closed, duplicate-key-rejecting, canonical-JSON validator and an
exact byte binding for this record. It requires recursive equality of type, shape, and value for
every expected record field and for the parsed carrier, zeta, and Möbius registries. The hostile
suite rejects Boolean `false` substituted for JSON integer `0`, floating `5.0` substituted for JSON
integer `5`, Boolean `False` substituted for integer `0` inside a Möbius tuple, and floating `129.0`
substituted for integer census `129`. Each substitution is exercised in normal and optimized
Python after the corresponding owner-controlled bindings are coherently resealed. It does not
claim a reusable schema for arbitrary untrusted certificate input or arbitrary Python source. That
parser and schema belong to the still-open Program C boundary; adding a decorative schema that no
production gate consumes would not close it.

One hostile test is intentionally a **passing negative control**. It changes `AND within a mask`
to `OR within a mask` in the prose, updates the prose binding in the record, and updates both
owner-controlled digest literals in an isolated copy. The checker then passes. This is the
expected result because a byte-binding checker cannot interpret natural-language mathematical
meaning or prevent a coordinated owner from resealing all owner-controlled files. The accepted
mutation receives zero source-correspondence, independent-review, authenticity, or mathematical
credit. Independent source review and external custody remain open controls.

The required local replay commands are:

```text
python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py
python3 -I -S -B -O scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py
python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py
python3 -I -S -B -O scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py
```

## 10. Counterexamples and fault model

The bridge retains the following minimal or small witnesses:

| Fault | Distinguishing witness | Why it matters |
|---|---|---|
| Use OR inside a joint collection | Key `03`, equality pattern `100`: correct false, mutant true | Separates joint $(S_1,S_2)$ from individual-source redundancy |
| Use AND across antichain branches | Key `01+02`, equality pattern `010`: correct true, mutant false | Preserves the inclusive shared-event union |
| Substitute Equation (4) for every Equation (6) collection | Same joint-collection witness as above | Prevents a notation-based semantic collapse |
| Omit target intersection in $V$ | Key `01`, source pattern `100`, target mismatch | Prevents $V$ from silently becoming $U$ |
| Average supported keys uniformly | counts $(2,1)$ and local values $(0,1)$: $1/3\ne1/2$ | Preserves MGW Equation (17) weighting |
| Reverse the antichain order | `01` and `03`: one direction holds and the other does not | Prevents a self-consistent transposed lattice |
| Delete or duplicate a carrier node | Regenerated 127-family filter no longer equals 18 unique keys | Prevents a hard-coded count from masking registry drift |
| Change one Möbius entry | At least one of $MZ=I$ or $ZM=I$ fails | Prevents one-sided inverse or orientation drift |
| Relabel only keys but not data columns | Event-equivariance check fails | Prevents superficial permutation agreement |

These witnesses show that the named mutants differ. They do not prove that the mutation list is
complete.

## 11. Relationship to the 108-coordinate audit

The 18 lattice positions expand into

$$
18\ \text{positions}
\times
2\ \text{stages (cumulative, atom)}
\times
3\ \text{components (plus, minus, net)}
=108
$$

keyed scalar audit expressions. They are not 108 atoms, nodes, or independent degrees of freedom.
The net stage is plus minus minus, and the atom stage is the fixed transform in Equation (7.5).

The existing repository bounded audit already recomputed all 108 expressions by two
implementation-disjoint-under-shared-semantics Python routes on 20,348 labelled binary count
tables with total one through five. The present bridge attacks a different shared cut: it explains
and executable-checks the event and lattice semantics that both arithmetic routes could have
mistranscribed together. It does not retroactively make those routes logically independent, and it
does not add a retained per-coordinate product stream.

## 12. Program A credit and residual obligations

| Obligation | New evidence | Status after this bridge | What remains |
|---|---|---|---|
| S1 source identity and definitions | Versioned PDF/source identities, exact anchors, semantic cards, and prohibited inferences | Owner-controlled review recorded; external independent review open | Independent acquisition, reading, objections, and durable external custody |
| D1 canonical input | None; D1 is the upstream complete-certificate byte-decoding boundary, not a rule created by Program A | Open | Unique accepted certificate bytes-to-table decoding, canonical reserialization, hostile parser tests, and resource limits |
| D2 event and count bridge | Generic indicator/count proof plus all 288 finite truth cases and mutants | Strong partial | Concrete formal semantics and parser/implementation refinement |
| L1 carrier | Definition-generated 18-node reconstruction from all 127 nonempty mask families | Exact executable Fin-3 result; formal completeness open | Concrete Lean and independently encoded solver construction |
| L2 order/zeta/Möbius | All 324 order entries, exact two-sided inverse, six automorphisms | Exact executable Fin-3 result; dual formal routes open | Lean and solver-neutral dual construction tied to the same semantics |

Program A remains **partial/open** because its frozen closure rule requires independent source
correspondence, concrete formal carrier completeness, and the canonical input boundary. Programs
A--E closed remains **0 of 5**. The complete certificate disposition remains **proposed/open**.

## 13. Twenty-lens adversarial council

This is an integrator-owned review, not a vote and not independent custody.

| Lens | Question | Resolution |
|---|---|---|
| Scientific identity | Is this MGW categorical Sx rather than another PID? | The scope names only MGW categorical shared exclusions and prohibits transfer from BROJA, $I_{\min}$, CCS, or continuous Sx |
| Source identity | Can the reviewed bytes be identified? | PDF, archive, and TeX-member sizes and SHA-256 values are recorded; authenticity remains open |
| Notation | Does one symbol play two semantic roles? | Equation (4) individual-source subset is explicitly separated from Equation (6) joint collection |
| Logic | Are AND and OR placed correctly? | AND within a mask, OR across antichain branches, with minimal witnesses for both swaps |
| Target | Is the target restriction part of the event count? | $V$ uses $E\cap\{T=t\}$ and all target-equality truth cases are reconstructed |
| Boundary | Can a denominator be zero at a supported key? | The keyed row establishes $c_z\le V,U,T,N$; invalid decoded inputs remain outside this result |
| Weighting | Is the average over keys or observations? | MGW Equation (17) yields $c_z/N$ weights; a $(2,1)$ witness rejects equal key weights |
| Units | Are paper bits and repository nats conflated? | Multiplication by positive $\ln2$ is explicit and its preserved properties are bounded |
| Carrier | Is 18 assumed from a table? | All 127 nonempty families of seven masks are filtered by the antichain definition |
| Arity | Is 166 mistakenly used? | 166 is labeled as the four-source carrier $M(4)-2$, outside this Fin-3 bridge |
| Order | Could a reversed order pass? | Semantic Equation (7.1) is checked separately from both inverse products |
| Orientation | Are row and column roles explicit? | $Z_{ij}=1[\alpha_j\preceq\alpha_i]$ is stated before $c=Z\pi$ |
| Algebra | Is the inverse only checked one way? | Both $MZ=I$ and $ZM=I$ are required in exact rational/integer arithmetic |
| Components | Are plus/minus/net signs conflated? | Plus and minus are inverted separately; net is their difference and may be negative |
| Symmetry | Is collection order confused with source relabeling? | The distinction is explicit; six source automorphisms are derived independently |
| Generality | Does eight-bit truth enumeration prove arbitrary alphabets? | It proves the Boolean equality-kernel step; the count lemma separately lifts it to arbitrary finite rows |
| Implementation | Does the bridge claim Rust parity? | Rust, binary64, parser, and binary refinement remain explicit nonclaims |
| Independence | Do multiple model roles count as independent review? | No; this owner-controlled record leaves H1 open |
| Fault sensitivity | Can an alternate input bypass the canonical record? | The production checker has no alternate-path option; the self-test mutates isolated canonical copies |
| Governance | Does useful partial evidence silently close Program A? | Status fields require Program A partial/open and Programs closed 0/5 |

## 14. Exact nonclaims

This bridge does not establish:

- a defect in MGW shared exclusions;
- a new PID measure or scientific-priority claim;
- source authenticity, trusted time, authorship, or independent review;
- a reusable parser or schema for arbitrary untrusted count-table or certificate input; the bound Program A record itself does have one closed canonical-JSON encoding;
- a general proof-assistant formalization of the paper;
- a second-solver reconstruction;
- exact logarithm magnitude or directed rounding;
- current Rust, binary64, Python producer, or verifier refinement;
- the complete 108-coordinate certificate implication;
- estimator consistency, bias, variance, calibration, or confidence coverage;
- population-support discovery, independence, stationarity, or causal meaning;
- fitted quantization or a changing alphabet;
- continuous, singular, mixed-dimensional, or hyperbolic PID;
- transfer to Williams--Beer $I_{\min}$, BROJA, CCS, MMI, or another redundancy measure; or
- downstream sensor-placement, Galadriel, Prisoma, Crebain, or deployment validity.

Those are separate mathematical, executable, statistical, and application obligations. A later
claim may cite this bridge only for the exact definitions and finite derivations stated here.
