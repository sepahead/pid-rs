# Conventions for SX-CERTIFIED-AVERAGED-PID3-001

## Scientific identity and domain

This packet concerns only the finite categorical shared-exclusions functional of Makkeh,
Gutknecht, and Wibral. It does not import a redundancy value, atom sign, axiom, or estimator
property from Williams--Beer $I_{\min}$, BROJA, CCS, MMI, SID, continuous KSG, or any other PID.

There are exactly three ordered categorical sources $S_1,S_2,S_3$ and one categorical target
$T$. The positive empirical support is

$$
\mathcal Z_+
=
\{z=(s_1,s_2,s_3,t):c_z>0\},
\qquad
c_z\in\mathbb N_{>0},
$$

with

$$
N=\sum_{z\in\mathcal Z_+}c_z>0,
\qquad
\widehat P(z)=\frac{c_z}{N}.
$$

One complete supported joint state occurs exactly once. A byte decoder must reject duplicate
complete states rather than relying on a later aggregation. Categorical values are compared only
for exact equality; numeric distance or ordering has no meaning.

The table defines one empirical law. It does not assert that observed support is population
support, that rows were independent, or that this plug-in law estimates an unquantized or
continuous population functional.

## Source masks and the shared-exclusion event

The fixed source-mask convention is

| Mask bit | Source |
|---:|---|
| `0x01` | $S_1$ |
| `0x02` | $S_2$ |
| `0x04` | $S_3$ |

For a nonzero mask $a\in\{1,\ldots,7\}$ and keyed realization $z$, define the source
conjunction

$$
E_a(z)
=
\bigcap_{i:\,a_i=1}\{z':s'_i=s_i\}.
$$

A source antichain $\alpha$ is a nonempty collection of nonzero masks with no two distinct
members related by set inclusion. Its Makkeh--Gutknecht--Wibral shared source event is the
disjunctive normal form

$$
E_\alpha(z)
=
\bigcup_{a\in\alpha}E_a(z)
=
\bigcup_{a\in\alpha}
\bigcap_{i:\,a_i=1}\{z':s'_i=s_i\}.
$$

Thus the connective is **OR across antichain branches and AND within one source mask**. Define the
target event

$$
T(z)=\{z':t'=t\}.
$$

The exact masses used by every coordinate are

$$
\begin{aligned}
U_{\alpha,z}
&=\sum_{z'\in E_\alpha(z)}c_{z'},\\
V_{\alpha,z}
&=\sum_{z'\in E_\alpha(z)\cap T(z)}c_{z'},\\
T_z
&=\sum_{z'\in T(z)}c_{z'}.
\end{aligned}
$$

Because $z$ itself lies in every keyed branch and in its target event,

$$
0<c_z\le V_{\alpha,z}\le U_{\alpha,z}\le N,
\qquad
V_{\alpha,z}\le T_z\le N.
$$

Every rational and logarithm argument below is therefore strictly positive on the positive
empirical support. Zero-count cells are absent from $\mathcal Z_+$ and contribute no informal
$0\log0$ term.

## Pointwise and averaged cumulatives

For a supported realization $z$, the local informative, misinformative, and signed-net
cumulatives are

$$
\begin{aligned}
i^+_\alpha(z)
&=-\ln\widehat P(E_\alpha(z))
=\ln\frac{N}{U_{\alpha,z}},\\
i^-_\alpha(z)
&=-\ln\widehat P(E_\alpha(z)\mid T=t)
=\ln\frac{T_z}{V_{\alpha,z}},\\
i^{\mathrm{sx}}_\alpha(z)
&=i^+_\alpha(z)-i^-_\alpha(z)
=\ln\frac{N V_{\alpha,z}}{U_{\alpha,z}T_z}.
\end{aligned}
$$

The averaged cumulatives use empirical-count weights, not equal weight over distinct supported
keys:

$$
C^u_\alpha
=
\frac1N\sum_{z\in\mathcal Z_+}c_z i^u_\alpha(z),
\qquad
u\in\{+,-,\mathrm{sx}\}.
$$

All logarithms are natural logarithms, so all quantities are in nats. Replacing $\ln$ by
$\log_2$ multiplies every value by $1/\ln2$; a bit-valued reference is converted to nats by
multiplication by $\ln2$.

## The complete 18-node carrier

Within a key, masks are strictly increasing. The certificate order is first by antichain
cardinality and then lexicographically by the ascending mask tuple. A two-digit hexadecimal mask
is used in the stable key.

| Index | Stable key | Mask tuple | Source collections |
|---:|---|---|---|
| 0 | `01` | `(1)` | $\{\{1\}\}$ |
| 1 | `02` | `(2)` | $\{\{2\}\}$ |
| 2 | `03` | `(3)` | $\{\{1,2\}\}$ |
| 3 | `04` | `(4)` | $\{\{3\}\}$ |
| 4 | `05` | `(5)` | $\{\{1,3\}\}$ |
| 5 | `06` | `(6)` | $\{\{2,3\}\}$ |
| 6 | `07` | `(7)` | $\{\{1,2,3\}\}$ |
| 7 | `01+02` | `(1,2)` | $\{\{1\},\{2\}\}$ |
| 8 | `01+04` | `(1,4)` | $\{\{1\},\{3\}\}$ |
| 9 | `01+06` | `(1,6)` | $\{\{1\},\{2,3\}\}$ |
| 10 | `02+04` | `(2,4)` | $\{\{2\},\{3\}\}$ |
| 11 | `02+05` | `(2,5)` | $\{\{2\},\{1,3\}\}$ |
| 12 | `03+04` | `(3,4)` | $\{\{1,2\},\{3\}\}$ |
| 13 | `03+05` | `(3,5)` | $\{\{1,2\},\{1,3\}\}$ |
| 14 | `03+06` | `(3,6)` | $\{\{1,2\},\{2,3\}\}$ |
| 15 | `05+06` | `(5,6)` | $\{\{1,3\},\{2,3\}\}$ |
| 16 | `01+02+04` | `(1,2,4)` | $\{\{1\},\{2\},\{3\}\}$ |
| 17 | `03+05+06` | `(3,5,6)` | $\{\{1,2\},\{1,3\},\{2,3\}\}$ |

This certificate order is not a license to compare implementation arrays positionally. The
specialized current Rust three-source array places `(4)` before `(3)`, whereas this registry places
`(3)` before `(4)`. The general $n$-source Rust enumeration has another order. Refinement must
canonicalize each antichain as a sorted set of masks and compare by stable key.

## Redundancy order and zeta orientation

The fixed redundancy order is

$$
\alpha\preceq\beta
\quad\Longleftrightarrow\quad
\forall b\in\beta\;\exists a\in\alpha:\ a\subseteq b.
$$

In particular, key `01+02+04` is the bottom node and key `07` is the top node. For the node order
above, the zeta matrix has **cumulatives as rows and atoms as columns**:

$$
Z_{ij}=\mathbf 1[\alpha_j\preceq\alpha_i],
\qquad
C^u_i=\sum_{j=0}^{17}Z_{ij}\Pi^u_j.
$$

The following row signatures bind every entry. Each 18-character string lists columns $0$
through $17$, in that order.

| Row $i$ | Stable key | $Z_{i,0}\ldots Z_{i,17}$ |
|---:|---|---|
| 0 | `01` | `100000011100000010` |
| 1 | `02` | `010000010011000010` |
| 2 | `03` | `111000011111111011` |
| 3 | `04` | `000100001010100010` |
| 4 | `05` | `100110011111110111` |
| 5 | `06` | `010101011111101111` |
| 6 | `07` | `111111111111111111` |
| 7 | `01+02` | `000000010000000010` |
| 8 | `01+04` | `000000001000000010` |
| 9 | `01+06` | `000000011100000010` |
| 10 | `02+04` | `000000000010000010` |
| 11 | `02+05` | `000000010011000010` |
| 12 | `03+04` | `000000001010100010` |
| 13 | `03+05` | `100000011111110011` |
| 14 | `03+06` | `010000011111101011` |
| 15 | `05+06` | `000100011111100111` |
| 16 | `01+02+04` | `000000000000000010` |
| 17 | `03+05+06` | `000000011111100011` |

This $Z$ has 129 ones. A transposed matrix is not an equivalent serialization: it changes which
coordinate is a cumulative and which is an atom.

## Exact Möbius inverse

Let $M=Z^{-1}$, with atom rows and cumulative columns:

$$
\Pi^u_i=\sum_{j=0}^{17}M_{ij}C^u_j.
$$

The nonzero rows are pinned sparsely below; `C[j]` means the cumulative at certificate index $j$.

```text
Pi[ 0] =  C[0] - C[9]
Pi[ 1] =  C[1] - C[11]
Pi[ 2] =  C[2] - C[13] - C[14] + C[17]
Pi[ 3] =  C[3] - C[12]
Pi[ 4] =  C[4] - C[13] - C[15] + C[17]
Pi[ 5] =  C[5] - C[14] - C[15] + C[17]
Pi[ 6] = -C[2] - C[4] - C[5] + C[6] + C[13] + C[14] + C[15] - C[17]
Pi[ 7] =  C[7] - C[16]
Pi[ 8] =  C[8] - C[16]
Pi[ 9] = -C[7] - C[8] + C[9] + C[16]
Pi[10] =  C[10] - C[16]
Pi[11] = -C[7] - C[10] + C[11] + C[16]
Pi[12] = -C[8] - C[10] + C[12] + C[16]
Pi[13] = -C[0] + C[9] + C[13] - C[17]
Pi[14] = -C[1] + C[11] + C[14] - C[17]
Pi[15] = -C[3] + C[12] + C[15] - C[17]
Pi[16] =  C[16]
Pi[17] =  C[7] + C[8] - C[9] + C[10] - C[11] - C[12] - C[16] + C[17]
```

The matrix has 65 nonzero entries, every entry lies in $\{-1,0,1\}$, and the maximum nonzero
support of a row or column is eight. Both $MZ=I_{18}$ and $ZM=I_{18}$ are required checks.
Those matrix identities are necessary but do not prove that the rows encode the declared event
semantics.

## Exact positive-rational products

For every node, define the count-cleared cumulative products

$$
\begin{aligned}
Q^+_\alpha
&=\prod_{z\in\mathcal Z_+}
\left(\frac{N}{U_{\alpha,z}}\right)^{c_z},\\
Q^-_\alpha
&=\prod_{z\in\mathcal Z_+}
\left(\frac{T_z}{V_{\alpha,z}}\right)^{c_z},\\
Q^{\mathrm{sx}}_\alpha
&=\frac{Q^+_\alpha}{Q^-_\alpha}.
\end{aligned}
$$

All three are positive rationals and

$$
C^u_\alpha=\frac1N\ln Q^u_\alpha.
$$

For every atom index $i$, define

$$
R^u_i=\prod_{j=0}^{17}(Q^u_{\alpha_j})^{M_{ij}},
\qquad
\Pi^u_i=\frac1N\ln R^u_i.
$$

Negative Möbius coefficients move a positive rational factor to the denominator. The net products
must also satisfy

$$
Q^{\mathrm{sx}}_\alpha=Q^+_\alpha/Q^-_\alpha,
\qquad
R^{\mathrm{sx}}_i=R^+_i/R^-_i.
$$

Because $N>0$ and $\ln$ is strictly increasing,

$$
\Pi^u_i=0\iff R^u_i=1,
\quad
\Pi^u_i>0\iff R^u_i>1,
\quad
\Pi^u_i<0\iff R^u_i<1,
$$

and the same equivalences hold for each cumulative $Q^u_\alpha$. Exact zero and strict sign are
decided by exact integer cross multiplication, not a floating tolerance and not interval sign
alone. A nonempty factor list may still multiply to one.

Informative and misinformative atoms are separate coordinates. The signed-net atom is their
difference and may be negative. No coordinate is clamped or replaced by its absolute value.

## The exact 108-coordinate order

The fixed coordinate registry is six consecutive blocks, each using antichain indices $0$
through $17$:

1. `cumulative.informative.<key>`: indices 0--17;
2. `cumulative.misinformative.<key>`: indices 18--35;
3. `cumulative.net.<key>`: indices 36--53;
4. `atom.informative.<key>`: indices 54--71;
5. `atom.misinformative.<key>`: indices 72--89; and
6. `atom.net.<key>`: indices 90--107.

Duplicate, missing, reordered, or relabeled identities fail verification. A report with only the
54 atom coordinates is not a 108-coordinate certificate.

## Magnitude intervals and exact decisions

Each coordinate carries two separate lanes:

- a normalized outward dyadic interval enclosing $(1/N)\ln R$; and
- an exact product record comparing the reconstructed positive rational $R$ with one.

The independent interval must be a subset of the producer interval. Mere overlap is insufficient.
The exact-product lane, not an interval touching zero, decides exact zero. If resource preflight
does not admit the exact comparison or either interval route cannot complete its fixed precision
schedule, the complete 108-coordinate status is not `verified`.

The independent logarithm route uses

$$
\ln y
=2\sum_{k=0}^{m-1}\frac{z^{2k+1}}{2k+1}+R_m,
\qquad
z=\frac{y-1}{y+1},
\quad
1\le y<2,
$$

with

$$
0\le R_m
\le\frac{2z^{2m+1}}{(2m+1)(1-z^2)}
\le\frac{9z^{2m+1}}{4(2m+1)}.
$$

Every arithmetic operation is performed with exact rational endpoints or explicit integer
floor/ceiling rounding. Range reduction $x=2^e y$, multiplication by $1/N$, and negative
coefficients must swap interval endpoints when required. The exact executable recurrence and
precision schedule are versioned in [bindings.md](bindings.md); a generic high-precision decimal
match is not a certificate.

## Binary qualification corpus

For the bounded binary corpus only, cells use

$$
\mathrm{cell}(s_1,s_2,s_3,t)=8s_1+4s_2+2s_3+t.
$$

All nonzero weak count vectors over the 16 cells with totals $1\le N\le5$ number

$$
\sum_{N=1}^5\binom{N+15}{15}
=\binom{21}{16}-1
=20{,}348.
$$

These are labeled count vectors, not distinct probability laws. Dividing by the gcd leaves
20,164 primitive rational laws. A complete 108-coordinate replay over all count vectors would
evaluate

$$
20{,}348\times108=2{,}197{,}584
$$

averaged coordinates. Replicated count vectors remain in the corpus because replication
invariance and count-handling bugs are separate executable obligations.

Across the same count-vector corpus, the exact number of supported table--realization pairs is

$$
16\sum_{N=1}^5\binom{N+14}{15}=77{,}520.
$$

Evaluating 54 informative/misinformative/net atom coordinates at each such pair would give
4,186,080 pointwise-coordinate evaluations. Those counts explain an external differential scope;
pointwise certification is not part of this 108-coordinate averaged claim.

Pointwise coordinates, continuous laws, fitted quantizers, and population sampling statements are
outside this claim.
