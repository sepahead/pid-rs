# Binary allocation: proof routes and application limits

Sepehr Mahmoudian - 13 October 2026

Use the [main report's definitions](BINARY_SXPID_ALLOCATION_BOUND_2026_10_13.md).
Hand arguments only; formal/numerical/application/PDF acceptance pending.

## 1. A uniform rare-source boundary bound

Let $m=\min(\Pr(C=0),\Pr(C=1))$; relabel so $\Pr(C=1)=m$.
For $m=0$, $D=0$. Assume $0<m\le1/2$.
Define $b_T=I(C;T)$, $d_T=I(C;T\mid X)$ and
$S=J(P)-\sum_t p_T(t)J(P_t)$, the NET synergy.
$P$ is the prior $(X,C)$ law and $P_t$ its supported conditional law.
The report's $J$ is the nonnegative component synergy, not net $S$.

For an occupied cell of mass $s$, adjacent masses $v_1,v_2$ and
OR mass $u=s+v_1+v_2$, $\ln(1+y)\le y$ for $y\ge0$ gives

$$
s\ln(1+v_1v_2/(su))\le v_1v_2/u\le\min(v_1,v_2).
$$

In anchor order $00,01,10,11$, bound these terms respectively by
$P(0,1),P(1,1),P(1,1),P(0,1)$.
Adding gives $0\le J(P)\le2m$.
Apply the SAME label-1 bound conditionally, even when label 1 is not rare
given $T=t$, and average. Both $J(P)$ and $\sum_t p_T(t)J(P_t)$
lie in $[0,2m]$; hence $|S|\le2m$, not $4m$.

Writing $R=L-M=b_T-d_T+S$, the exact norm is

$$
D=2|R|+|b_T-R|+|S|
 =2|b_T-d_T+S|+|d_T-S|+|S|.
$$

The triangle inequality gives
$D\le2|b_T-d_T|+d_T+4|S|$.
Since $0\le b_T,d_T\le h=H(C)$,
$2|b_T-d_T|+d_T\le3h$ (split at $b_T=d_T$).
As $h\ge m\ln(1/m)$,

$$
D\le3h+8m,\qquad D/h\le3+8/\ln(1/m).
$$

Uniform over conditional laws and finite targets; this handles the boundary
missed by compactness. Not every rare source attains three.

## 2. Seven target labels suffice for optimization

This existence reduction is NOT a target encoder.
Let $z=(z_{00},z_{01},z_{10},z_{11})$ be a four-cell probability vector,
not the main report's scalar imbalance. Define

$$
\phi(z)=(z_{00},z_{01},z_{10},H_z(C),H_z(C\mid X),F(z)).
$$

Subscripts mean entropy in $z$. Positive target weights $w_t=p_T(t)$
mix posteriors $z_t=P_t$. Means of the six coordinates determine prior $P$,
$H(C\mid T),H(C\mid X,T),M$, hence $b_T,d_T,L,R,S,D,h$.

For more than seven weights, $(1,\phi(z_t))$ in seven-dimensional space
are linearly dependent. Nonzero coefficients $\alpha_t$ satisfy
$\sum_t\alpha_t=0$ and $\sum_t\alpha_t\phi(z_t)=0$.
Both signs occur. Set $\lambda=\min_{\alpha_t>0}w_t/\alpha_t$ and
$w'_t=w_t-\lambda\alpha_t$. Weights stay nonnegative, sum to one,
preserve all needed means and eliminate at least one target.
Repeat to obtain at most seven labels.

The new law preserves $D/h$, NOT necessarily original $(X,T)$, target labels
or rational counts. It is not deterministic coarsening.
Each collapse comparison preserves its OWN $(X,T)$ marginal.
This is a proof parameterization, not a deployment transform.

## 3. Compactness supplies another gap below four

Entropy extends continuously to zero cells.
For an OR term, the anchor mass satisfies $s\le u$.
At the only singular boundary $u\downarrow0$,
$0\le s\ln(1/u)\le u\ln(1/u)\to0$.
Thus $F$, its conditional mixture and $D$ are continuous on the closed
four-cell simplex.

With seven posteriors, their nonnegative weights and a prior rare mass
$m\in[\delta,1/2]$, where $\delta>0$, the parameter set is compact.
Here $h>0$, so $D/h$ is continuous and attains its maximum.
To exclude an attained value four, keep the finer master inequality

$$
D\le4h-2i-d_T,\qquad i=I(C;X).
$$

From $D\le A+B+2\max(L,M)$, use $A=h-i$,
$B=h_T-j$, $h_T=h-b_T$ and $d_T=b_T-i+j$.
If $L\ge M$, use $L\le h$ to get the displayed ceiling.
If $M\ge L$, use $M\le h_T$ to get that ceiling minus $2b_T$.
Equality $D/h=4$ would force $i=d_T=0$.
Then $I(C;X,T)=i+d_T=0$, so $C$ is independent of $(X,T)$:
prior and posterior source laws are products with the same $C$ marginal.

For a product law write $u=\Pr(X=0)$ and let $q_c=\Pr(C=c)$.
For $q_c>0$ define $g_{q_c}(v)=-v\ln(q_c+(1-q_c)v)$, for $0\le v\le1$.
The label's OR contribution is
$q_c[g_{q_c}(u)+g_{q_c}(1-u)]$.
Differentiation yields

$$
g_{q_c}''(v)
=-\frac{(1-q_c)[2q_c+(1-q_c)v]}{[q_c+(1-q_c)v]^2}\le0.
$$

Concavity and symmetry maximize the sum at $u=1/2$.
Since $(1+q_c)/2\ge\sqrt{q_c}$, that contribution is at most
$-q_c\ln(q_c)/2$. Zero-probability labels contribute zero.
Therefore $F\le h/2$ for product laws.
The prior and conditional products give $A=B=h,\ L,M\le h/2$,
hence $D\le3h$, contradicting four.

Choose $\delta=\exp(-16)$.
Section 1 gives $D/h\le7/2$ below $\delta$; the attained interior
maximum is strictly below four. Together they prove an existential
uniform coefficient below four.
The explicit main bound is stronger.
No numerical value of the interior maximum or optimality was computed.

## 4. Conditional original full-carrier extension

Retain $X=S_j$, one binary source among $r\ge2$ positions; $j$ is its index.
Set $\mathcal I=\{1,\ldots,r\}$ and $C=(S_i)_{i\ne j}$, the COMPLETE
dropped tuple. Require at most two positive JOINT labels, not merely
binary individual channels. No regrouping is allowed.

Use the original antichain carrier: nonempty families of nonempty source
subsets, with no branch containing another. Events OR together branch-wise
equality ANDs. Order $\alpha\preceq\gamma$ means each branch of $\gamma$
contains a branch of $\alpha$; cumulatives satisfy
$F_\gamma^\pm=\sum_{\alpha\preceq\gamma}\Pi_\alpha^\pm$.
Assume [MGW v5 Theorem IV.3](https://arxiv.org/html/2002.03356v5)
full-carrier component positivity; it is not re-proved here.

Set $a_0=\{\{j\}\}$, $g_0=\{\{j\},\mathcal I\setminus\{j\}\}$.
Strict predecessors of $a_0$ are exactly nodes below $g_0$:
branch $\{j\}$ plus a branch avoiding $j$. Therefore
$\Pi_{a_0}^+=H(X)-L$, $\Pi_{a_0}^-=H(X\mid T)-M$.
Total component sums are $H(X,C)$ and $H(X,C\mid T)$,
so off-$a_0$ sums are $A+L,B+M$.

Under collapse a branch avoiding $j$ is certain; otherwise it becomes $X=x$.
The cumulative vector is the reconstruction column of $a_0$.
Unique inversion leaves only that atom, net $I(X;T)$.
Positivity gives the main master inequality; the binary $(X,C)$ law gives
$D_{\rm full}\le(3+\beta)H(C)$ for ALL original signed averaged atoms.
Three sources give 18 atoms, not 108 expressions.
Auxiliary $J$ is not a full-carrier atom. Adding constants embeds the lower
XOR family at fixed $r$.

## 5. Applications: unrun protocols

[UCI room occupancy](https://archive.ics.uci.edu/dataset/864/room%2Boccupancy%2Bestimation)
permits NEW $X=$PIR6, $C=$PIR7, original $T=$count $0,1,2,3$.
Train December 22-25, 2017; validate December 26; evaluate January 10-11, 2018.
Seven dates and a gap defeat the provider's four-day protocol description.
The old complete dropped PIR tuple has FOUR labels and fails Section 4.

[UCI office occupancy](https://archive.ics.uci.edu/dataset/357/occupancy%2Bdetection)
needs NEW binary light/carbon-dioxide maps, not old four-bin results.
Train February 2-8, 2015; validate February 9-10; evaluate February 11-18.
Use timestamp order, not filenames. Freeze each training lower median
$\theta$; map measurement $V$ to $1\{V>\theta\}$, ties to zero.
Reject malformed values; original $T$ remains the occupancy bit.

Both exposed recordings are development. Neither protocol ran.
Report date-wise counts, entropy, atoms, norm and conditional mutual information.
Compare full, retrained-ablation and fixed-mask predictive losses on SAME rows;
keep losers and do not smooth PID counts. Direct loss may suffice for utility.
Zeros do not prove population support; date blocks do not prove coverage.
Neural/imaging pairs need fixed binary encodings and observed aligned targets.
A third missingness label exits scope; generated futures are not ground truth.
No forced model integration, benchmark, population/task/SOTA gain is claimed.

## 6. Rust implementation and computational cost

Norm, bounds, reduction and protocols are UNIMPLEMENTED.
[Categorical code](../crates/pid-core/src/sxpid.rs) supplies empirical atoms.
Main-report $N$-row/$K$-target costs and numerical limits apply.
Seven-label reduction is no optimizer; full-carrier cost depends on lattice size.
Median/date sorting can need $O(N\log N)$ time/$O(N)$ storage.
No timing/formal/refinement/calibration credit.
Cite title/year/exact commit; software [citation](../CITATION.cff).
