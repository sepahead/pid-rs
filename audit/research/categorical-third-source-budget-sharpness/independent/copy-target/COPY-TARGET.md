# An exact support test when the first source copies the target

Sepehr Mahmoudian, 2026. Cite the title, author, year and exact repository commit or release. This note derives a special case of the finite categorical shared-exclusions measure. [Defining paper by Makkeh, Gutknecht and Wibral](https://doi.org/10.1103/PhysRevE.103.032149)

## Question and assumptions

The published RndErr example already has this cancellation. Makkeh, Gutknecht and Wibral use the binary distribution of Finn and Lizier. Each agreeing cell has probability 3/8 and each disagreement 1/8. The target copies the first source. Their noisy source has negative unique information balanced by positive synergy. The September project report had already derived the local and average joint-only terms for two sources with a copied target coordinate and arbitrary residual. Its equation (19) gives the factorization used below. Equations (28)–(29) evaluate the same noisy-copy distribution. We place these terms in the constant-middle three-source order, then use the factorization to decide when all five selected means vanish individually. [September target-copy report, equations (1), (2), (19), (28) and (29)](https://github.com/sepahead/pid-rs/blob/6a9f087be84bc21a89ff51e7da8e626e6883d73e/audit/evidence/finite-target-copy-mgw-synergy.md) · [Makkeh, Gutknecht and Wibral, §VI.C and Table III](https://arxiv.org/pdf/2002.03356v5#page=11) · [Finn and Lizier, §5.4](https://doi.org/10.3390/e20040297) · [Pointwise source comparison](PRIOR-EXAMPLE.md)

Which combinations of two sensor labels can produce cancelling signed contributions when one sensor already gives the target? A *support* is the set of label tuples with positive probability. A *signed contribution* or *atom* is the difference between two components of the categorical information decomposition. Each component at a source event is the sum of its atoms below that event in the source order. These relations uniquely specify all atoms by subtraction. A *nat* is the unit obtained with the natural logarithm.

Let $X,W$ be any two finite categorical variables. The three sources are $S_1=X$, constant $S_2$, and $S_3=W$. The target is $T=X$. A cell $(x,w)$ has probability $p$. Write $r=P(X=x)$ for its row probability and $c=P(W=w)$ for its column probability. All sums below use cells with $p>0$. Let $M$ be the sum of the absolute values of the mean signed atoms at the five positions where every alternative group contains source 3. A group requires all its source labels to match the reference tuple. A collection of groups requires at least one group to match. For example, $\{13\}$ requires both 1 and 3 to match, whereas $\{1\}\{3\}$ permits either match. The five positions are $\{3\},\{13\},\{23\},\{13\}\{23\},\{123\}$. These definitions concern the finite distribution itself. The numerical examples use integer counts to specify such a distribution exactly. Let $N$ be the sum of these counts. [Earlier definition of the five-position budget](https://github.com/sepahead/pid-rs/blob/927e5138d23e0bd24b70f8df0fd38e610456a244/audit/archive/shared-exclusions-research-findings-20261001/source-redundancy.md.txt#L69-L88)

## Formula

For the stated sources and target,
$$
 M=2\sum_{p>0}p\ln\!\left(\frac{rc}{p(r+c-p)}\right).
$$
Its value is zero exactly when every occupied cell is the only occupied cell in its row or in its column. This gives a test based on support alone. Positive values also depend on the probabilities.

At a reference cell, a match in $X$ or $W$ has probability $u=r+c-p$. It is certain given the target $T=x$. Its signed shared information is consequently $R=-\ln u$. Write $i=\ln[p/(rc)]$ for the local mutual information of $X,W$ in this cell. This is also the local information provided by $W$ about $T=X$. Both $X$ alone and the ordered pair $(X,W)$ provide $-\ln r$ about the observed target. Subtraction of the four two-source cumulatives gives the following local atoms.

| Position | Local signed atom |
|---|---:|
| $\{1\}\{3\}$ | $R$ |
| $\{1\}$ | $-\ln r-R$ |
| $\{3\}$ | $i-R$ |
| $\{13\}$ | $R-i$ |

These values extend to the original three-source order. At any original position that contains $\{2\}$, the source event is certain. Its signed cumulative is zero and none of the four displayed positions lies below it. At each other original position, delete 2 from all groups and remove redundant supersets. This preserves the source event. It also preserves which of the four displayed positions lie below it, since their own groups contain only 1 and 3. The four displayed signed atoms can be nonzero. The other fourteen signed atoms are zero. At each of the 18 original positions, summing the atoms at or below it gives its signed cumulative. Uniqueness of the finite subtraction proves the reduction.

The five selected signed atoms sum to zero at each cell and after averaging. Only the last two displayed entries can contribute to $M$. In each occupied cell,
$$
 R-i=\ln\!\left(\frac{rc}{p(r+c-p)}\right)\ge0,
 \qquad rc-p(r+c-p)=(r-p)(c-p)\ge0.
$$
Each signed atom therefore has a fixed sign across the occupied cells, and $M=2\sum p(R-i)$. Equality to zero requires every term to vanish. This holds exactly when $r=p$ or $c=p$ at each cell. In a graph that joins each row to its occupied columns, the same condition says that each connected component is a star, including a single edge. To see this, take any vertex with two or more neighbors. Each of its neighbors must have one edge only. These neighbors and the vertex form the entire component. A component in which every vertex has one edge is a single edge. Components may have different orientations.

## Controls

If $X$ and $W$ are independent fair bits, the four cell probabilities are $1/4$. Each term $R-i$ is $\ln(4/3)$ and $M=2\ln(4/3)>0$. A decoder that returns $X$ has zero error for $T$. Changing the target to a constant gives $M=0$. Replacing $S_2$ by $W$ also gives $M=0$, since the first two now determine the third. These changes show why both input conditions matter. Two further four-cell tables have the same 16 Shannon subset entropies and give $M=0$ and $M=\tfrac12\ln(4/3)$. The latter two values are the endpoints at their common observation count $N=4$, three occupied third labels, and vector of entropies. [Paired calculation](paired_counts.py) · [Exact paired results](PAIRED-COUNTS.json)

For any two-source decomposition with four nonnegative mean parts satisfying the usual redundancy, unique and joint information equations, the unique part of $W$ plus the joint-only part equals $I(W;T\mid X)=0$. Here $I(W;T\mid X)$ is the conditional mutual information between $W$ and $T$ given $X$. Both terms must vanish. In the categorical signed measure they can be nonzero with opposite signs. The duplicated target is important for this comparison. Different definitions of which information the target and its sources share give different interpretations. [Deterministic target–source dependencies](https://doi.org/10.3390/e20030169) · [Earlier examples with equal Shannon information diagrams](https://doi.org/10.3390/e19100531)

## Rust implementation and computational cost

The default Rust route `pid_core::stable::categorical::discrete_sxpid3_averaged` accepts four row-aligned categorical inputs and reports mean atoms for the induced empirical distribution. This note supplies a separate exact Python reference and an input family for testing those means. Its checks concern integer count inputs and rational products. Testing the Rust binary on those inputs requires a separate controlled run and an explicit rounding allowance. [Rust implementation](https://github.com/sepahead/pid-rs/blob/927e5138d23e0bd24b70f8df0fd38e610456a244/crates/pid-core/src/sxpid.rs)

Given the list of $d$ occupied cells, one pass obtains row and column totals. A second checks the zero condition or accumulates the exact product whose logarithm gives $NM$. Both scans use order $d$ dictionary operations and order $d$ storage. If the input is a dense matrix, reading it also requires inspection of the zero cells. Exact arithmetic cost increases with integer and exponent sizes. The independent finite implementation forms the source-group events directly for all 18 positions. For these three fixed sources its direct scans use order $d^2$ row comparisons and store order $18d$ local rational pairs. Neither calculation uses training, resampling or a measured robot or neural data set.

Three finite checks cover all nonempty two-by-two and two-by-three matrices with counts 0, 1 or 2, and all nonempty three-by-three matrices with counts 0 or 1. They cover 80, 728 and 511 labelled matrices respectively. Their 3,888, 52,488 and 41,472 local signed comparisons agree with the full order. Some matrices represent the same distribution after unused labels are deleted. Ordinary and optimized Python returned the same exact factors. The process used a shared serial guard with a 60-second wall limit and a 256-mebibyte memory limit. These checks also exercised the wrong target and middle-source roles, equal margins, different weights on the same support and invalid counts. With independent fair bits as the first and third source, changing the constant middle source into a copy of the third changes the five means from two opposite nonzero terms and three zeros to five zeros. [Four-row worked control and published duplication example](PRIOR-EXAMPLE.md) Their scope is synthetic finite arithmetic. The general result follows from the event calculation and the cell identity above. [Full-node comparison](copy_support.py) · [Exact results](COPY-SUPPORT.json)

The three-source placement and the equal-entropy pair are project derivations of the cited functional. The support test is a consequence of the earlier two-source identity and that placement. The tables and their predicted outcomes predate the finite checks. Model assistance contributed to the derivation and checks. Scientific priority, a human review, kernel verification of the theorem and an improvement in task performance remain unestablished.
