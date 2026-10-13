# Binary shared-exclusions allocation: a uniform entropy bound

Sepehr Mahmoudian - 13 October 2026.

Replacing one of two binary categorical sources by a constant moves the
four signed averaged shared-exclusions atoms by at most $(3+\beta)H(C)$,
where $\beta=\ln(3/2)/\ln2$. A uniform coefficient below three is impossible.
The optimal coefficient lies in $[3,3+\beta]$; its exact value is open.

Status: independently reviewed hand derivation. No formal proof, certified
numerical evaluation, bound implementation, population confidence or
application gain is established. Scientific priority is unestablished.
SxPID3 Programs A-E remain 0/5 fully closed. Matching PDF: pending.

## 1. Measure, question and assumptions

The question is allocation stability after removing an input, not predictive
loss. Use categorical Makkeh-Gutknecht-Wibral (MGW) shared exclusions,
[*Introducing a differentiable measure of pointwise shared information*
(2021)](https://doi.org/10.1103/PhysRevE.103.032149).
Its [v5 source](https://arxiv.org/html/2002.03356v5) defines OR events and
separate informative/misinformative inversion. This report derives a bound,
not a new PID definition. Convert the paper's bits to nats by multiplying by
$\ln2$; $\ln$ denotes the natural logarithm.

Assumptions:

- $X$ is the retained source and $C$ the replaced source. Both have fixed
  alphabet $\{0,1\}$; a label may have zero probability.
- $T$ is the ORIGINAL target, with any nonempty finite alphabet.
- $p$ is a normalized nonnegative joint probability mass function of
  $(X,C,T)$. Dependence, deterministic relations and zero cells are allowed.
- $q$ replaces every $C$ value by an allowed constant $c_\star$, preserving
  the ENTIRE $(X,T)$ marginal and original target labels. It neither filters
  rows nor recomputes a target originally derived from $C$.
- A supplied law needs no sampling premise. Empirical probabilities use
  count weights, not equal weights over occupied cells. Population inference
  requires a separate valid sampling argument.
- Average first, then take absolute values; keep negative net atoms.

No continuous Ehrlich PID, Williams-Beer $I_{\min}$, other redundancy measure,
pointwise norm, causal intervention or task-loss transfer is made.
Regrouping original source positions changes the decomposition's carrier.

## 2. Variables, components and the quantity being bounded

For a finite variable $V$, $p_V(v)$ is its marginal probability and
$H(V)=-\sum_v p_V(v)\ln p_V(v)$, with zero summands zero.
$H(V\mid W)$ averages supported conditional entropies.
$I(V;W)=H(V)-H(V\mid W)$ is mutual information;
$I(V;W\mid Z)=H(V\mid Z)-H(V\mid W,Z)$ is conditional mutual information.
All quantities use $p$ unless marked $q$.

At a supported outcome $(x,c,t)$ define the inclusive-OR event
$E_{xc}=\{X=x\}\cup\{C=c\}$. Its unconditional and target-conditioned
probabilities are positive because the anchor belongs to it. Define

$$
L=\sum_{p(x,c,t)>0}p(x,c,t)[-\ln p(E_{xc})],\qquad
M=\sum_{p(x,c,t)>0}p(x,c,t)[-\ln p(E_{xc}\mid T=t)].
$$

$L$ and $M$ are the informative and misinformative OR cumulatives.
Put

$$
h=H(C),\quad h_T=H(C\mid T),\quad i=I(C;X),\quad j=I(C;X\mid T),
\quad A=h-i=H(C\mid X),\quad B=h_T-j=H(C\mid X,T).
$$

In order $(R,U_X,U_C,S)$, meaning redundancy, unique information of $X$,
unique information of $C$, and synergy, component inversion gives

$$
\Pi^+(p)=(L,H(X)-L,h-L,L-i),\quad
\Pi^-(p)=(M,H(X\mid T)-M,h_T-M,M-j).
$$

The signed net vector is $\Pi=\Pi^+-\Pi^-$ coordinate by coordinate.
For example, $R+U_X=I(X;T)$, $R+U_C=I(C;T)$ and the four atoms
sum to $I(X,C;T)$.

Under $q$, the OR is certain: $L(q)=M(q)=0$. All entropies and information
terms involving constant $C$ vanish. Hence

$$
\Pi(q)=(0,I(X;T),0,0),\qquad
D=\sum_{k=1}^{4}|\Pi_k(p)-\Pi_k(q)|.
$$

Here $k$ indexes the four coordinates. $D$ is an $L^1$ norm, a sum of
absolute values. It is not a maximum, an average of pointwise norms, or the
sum of all 108 three-source audit expressions. Retained information can survive.

## 3. Binary OR lemma: positivity and logarithmic ceiling

Take any law $P$ of $(X,C)$, such as the prior or a conditional law given $T$.
Write

$$
a=P(0,0),\ b=P(0,1),\ c=P(1,0),\ d=P(1,1),\quad a+b+c+d=1,
$$

and $q_0=a+c,\ q_1=b+d,\ w_0=a+b,\ w_1=c+d$.
These are $C$ and $X$ marginal probabilities; $q_0,q_1$ are not the
collapsed joint law $q$. Let $r_{xc}=w_xq_c$ and
$u_{xc}=1-P(1-x,1-c)$ be the product marginal and OR probability.
Define

$$
F(P)=\sum_{P(x,c)>0}P(x,c)[-\ln u_{xc}],\qquad
J(P)=F(P)-I_P(C;X).
$$

$I_P$ means information computed in law $P$.
If $H_P(C)=0$, all supported OR events are certain and $F=I_P=J=0$.
Otherwise $q_0,q_1>0$, no cell equals one, and all four $u_{xc}>0$.
Occupied cells also have $r_{xc}>0$.

### Step 1: two-source component positivity

At an occupied cell let $s$ be its mass and $v_1,v_2$ its adjacent cell
masses. Its OR mass is $u=s+v_1+v_2$, and the product of its marginals is
$(s+v_1)(s+v_2)=su+v_1v_2$. Thus

$$
J(P)=\sum_{\text{occupied cells}}s\ln\left(1+\frac{v_1v_2}{su}\right)\ge0.
$$

Event inclusion gives $0\le F(P)\le\min(H_P(X),H_P(C))$.
The four plus components are therefore nonnegative; apply the same proof
to supported conditional laws and average for the minus components.
No positivity of the signed net atoms or net synergy follows.

### Step 2: Jensen's inequality and exact algebra

Concavity of $\ln$, with the occupied-cell probabilities as weights, gives

$$
J(P)=\sum_{P(x,c)>0}P(x,c)\ln\frac{r_{xc}}{P(x,c)u_{xc}}
\le\ln\sum_{P(x,c)>0}\frac{r_{xc}}{u_{xc}}
\le\ln Z,\qquad Z=\sum_{x,c\in\{0,1\}}\frac{r_{xc}}{u_{xc}}.
$$

The last step adds nonnegative terms, not undefined zero-cell logarithms.
Substitute the four OR probabilities:

$$
Z=w_0\left(\frac{q_0}{q_0+b}+\frac{q_1}{q_1+a}\right)
+w_1\left(\frac{q_0}{q_0+d}+\frac{q_1}{q_1+c}\right)=2-K_0-K_1,
$$

where $K_0=w_0a/(1-c)+w_1c/(1-a)$ and
$K_1=w_0b/(1-d)+w_1d/(1-b)$.
For this equality write each fraction as one minus its excluded-mass
fraction, then use $w_0+w_1=1$. Next,

$$
K_0=q_0^2+q_1\left(\frac{ab}{1-a}+\frac{cd}{1-c}\right),\qquad
K_1=q_1^2+q_0\left(\frac{ab}{1-b}+\frac{cd}{1-d}\right).
$$

For the first identity multiply by the positive $(1-a)(1-c)$:

$$
a(a+b)(1-a)+c(c+d)(1-c)-(a+c)^2(1-a)(1-c)
=(b+d)[ab(1-c)+cd(1-a)].
$$

Substitute $d=1-a-b-c$ and expand. The second identity swaps $C$ labels:
$(a,b,c,d)\mapsto(b,a,d,c)$. Nonnegative remainders imply

$$
Z\le2-q_0^2-q_1^2=1+2q_0q_1,\qquad
0\le J(P)\le\ln(1+2q_0q_1).
$$

## 4. Entropy envelopes: rational and sharper exact coefficients

Let $\theta=q_1$, $v=\theta(1-\theta)$ and
$h_2(\theta)=-\theta\ln\theta-(1-\theta)\ln(1-\theta)$.
$v$ is a product of label probabilities, not a vector or velocity.
$h_2$ is binary entropy in nats, with zero endpoint values.

For $0<u<1$, integrating $1/(1-u)\ge1+u+u^2$ gives
$-\ln(1-u)\ge u+u^2/2+u^3/3$. Apply this at $\theta$ and $1-\theta$,
multiply by the other probability, and add:

$$
h_2(\theta)\ge2v+\frac v2+\frac v3[\theta^2+(1-\theta)^2]
=\frac{17v}{6}-\frac{2v^2}{3}\ge\frac{8v}{3}.
$$

The last step uses $v\le1/4$. Since $\ln(1+2v)\le2v$,
$\ln(1+2v)\le3h_2(\theta)/4$. Continuity handles $\theta=0,1$.

For a sharper envelope define

$$
\beta=\frac{\ln(3/2)}{\ln2},\quad z=|1-2\theta|,\quad
\mathcal H(z)=h_2((1-z)/2),\quad
f(z)=\ln((3-z^2)/2),\quad g(z)=\beta\mathcal H(z)-f(z).
$$

$z$ measures probability imbalance, not an angle.
Symmetry reduces the problem to $z\in[0,1]$.
Continuity gives $g(0)=g(1)=0$.
For $0<z<1$, define the inverse hyperbolic tangent by
$\mathrm{atanh}z=\int_0^z du/(1-u^2)$.
Its name makes no hyperbolic-data assumption. Differentiation gives

$$
g'(z)=\mathrm{atanh}z[k(z)-\beta],\qquad
k(z)=\frac{2z}{(3-z^2)\mathrm{atanh}z}.
$$

A prime denotes derivative. Logarithmic differentiation gives

$$
\frac{k'(z)}{k(z)}
=\frac{3+z^2}{z(3-z^2)}
-\frac1{(1-z^2)\mathrm{atanh}z}<0.
$$

The strict sign follows from the integral bound

$$
\mathrm{atanh}z
=z+\int_0^z\frac{u^2}{1-u^2}\,du
<z+\frac{z^3}{3(1-z^2)}
\le\frac{z(3-z^2)}{(1-z^2)(3+z^2)}.
$$

The first denominator inequality is strict inside the integral.
Positive cross multiplication for the second reduces to
$(3-2z^2)(3+z^2)\le3(3-z^2)$; subtraction leaves $-2z^4\le0$.
Hence $k$ strictly decreases, with $k(0+)=2/3,\ k(1-)=0$.
Also $0<\beta<2/3$, since $(3/2)^3<2^2$.
There is exactly one crossing $k=\beta$. Therefore $g$ increases then
decreases to zero; it cannot be negative between its zero endpoints.
We have proved, without an optimization experiment,

$$
J(P)\le\ln(1+2\theta(1-\theta))\le\beta H_P(C).
$$

## 5. Movement bound: both maximum branches

Apply the lemma to the prior and separately to every supported conditional
law. With $J_+=L-i$ and $J_-=M-j$, conditional averaging gives
$J_+\le\beta h,\ J_-\le\beta h_T$, including constant-$C$ conditional cases.
Event inclusion and entropy conditioning give
$L\le h,\ M\le h_T,\ A\le h,\ B\le h,\ h_T\le h$.

The retained unique-$X$ component changes are $-L$ and $-M$.
The other three plus components sum to $A+L$; their minus counterparts
sum to $B+M$. Their collapsed values vanish. For nonnegative component
values $u,v$, $|u-v|\le u+v$, so

$$
D\le|L-M|+A+B+L+M=A+B+2\max(L,M).
$$

Here the elementary inequality's $u,v$ are not the probability product $v$
above. Retaining the coupling between entropy and the OR means gives

$$
A+2L=h+L+J_+\le(2+\beta)h,\qquad
B+2M=h_T+M+J_-\le(2+\beta)h_T.
$$

If $L\ge M$, add $B\le h$ to the first inequality.
If $M\ge L$, add $A\le h$ to the second and use $h_T\le h$.
Both branches yield $D\le(3+\beta)H(C)$.
The rational envelope gives the separate fallback $D\le15H(C)/4$.

If $h=0$, the component formulas give $D=0$ directly.
For $h>0$, no fixed-binary sequence has $D/h\to4$.
Since $h\le\ln2$, the absolute ceiling is
$(3+\beta)\ln2=\ln12$ nats. This does not establish the optimal coefficient.

## 6. Worked count law and the necessary coefficient three

Take a fair $X$ and an independent $C$ with $\Pr(C=1)=\epsilon$,
where $0<\epsilon\le1/2$. Keep the ORIGINAL target
$T=X\mathbin{\mathrm{XOR}}C$; XOR means addition modulo two.
Supported rows have probability $\Pr(C=c)/2$. Set $h=h_2(\epsilon)$ and

$$
L=(1-\epsilon)[-\ln(1-\epsilon/2)]
+\epsilon\ln\frac2{1+\epsilon}.
$$

Given $T$, one source determines the other, so $M=h$.
Also $i=0,\ j=h,\ H(X)=\ln2,\ H(X\mid T)=h$. Hence

$$
\Pi(p)=(L-h,\ln2-L,h-L,L),\qquad
\Pi(q)=(0,\ln2-h,0,0),\qquad D=3h-2L.
$$

$0\le L\le h$ justifies each absolute-value sign.
For $\epsilon=1/4$, this law is an eight-row count table:

| $X$ | $C$ | original $T$ | count |
|---|---|---|---|
| 0 | 0 | 0 | 3 |
| 0 | 1 | 1 | 1 |
| 1 | 0 | 1 | 3 |
| 1 | 1 | 0 | 1 |

Divide counts by eight.
Then $h=-\tfrac14\ln\tfrac14-\tfrac34\ln\tfrac34$ and
$L=\tfrac34\ln(8/7)+\tfrac14\ln(8/5)$.
Before-atoms sum to $\ln2$, the target entropy.
After-atoms sum to $\ln2-h$, NOT zero.
Lost joint information is $h$; allocation movement is $3h-2L$.
These are exact expressions, not newly run binary64 benchmark values.

For the lower limit, $-\ln(1-\epsilon/2)\le\epsilon/(2-\epsilon)$.
Its product with $1-\epsilon$ is at most $\epsilon/2$; the other term
is at most $\epsilon\ln2$.
Therefore $L\le\epsilon(1/2+\ln2)$ and $h\ge\epsilon\ln(1/\epsilon)$.
It follows that $L/h\to0$ and $D/h\to3$ as $\epsilon\downarrow0$.
For integer $m\ge2$, $\epsilon=1/m$ has $2m$ rows, common-row counts
$m-1$ and rare-row counts one, on the SAME binary alphabets.

Let $K_\star$ be the supremum of $D/H(C)$ over admissible laws with
$H(C)>0$. Thus $3\le K_\star\le3+\beta$. A uniform bound of three is unproved.
Controls: constant $T$ gives $D=0$; copied fair $X=C=T$ gives $D=2\ln2$.
For independent fair $X,C$ and $T=X$, define $\rho=\ln(4/3)$.
Then $\Pi(p)=(\rho,\ln2-\rho,-\rho,\rho)$ and $D=4\rho$,
refuting any universal nonpositive-redundancy shortcut.

## 7. Failed routes, review and unresolved claims

The proposed helper $L\le h-A/2$ is false. For the near-copy law
$a=d=(1-\epsilon)/2,\ b=c=\epsilon/2$, $h=\ln2,\ A=h_2(\epsilon)$ and

$$
L=(1-\epsilon)\ln\frac2{1+\epsilon}
+\epsilon[-\ln(1-\epsilon/2)],\qquad
0\le h-L\le\epsilon(1+\ln2).
$$

Since $A\ge\epsilon\ln(1/\epsilon)$, $(h-L)/A\to0$.
This defeats every fixed positive multiple of $A$ as an entropy gap;
equivalently $J/A\to1$.
The discarded phrase "I(C;X complement)" defines no quantity:
the rejected inequality is exactly $L\le h-A/2$.
Reopen it only with additional proved restrictions.

[The companion](BINARY_SXPID_BOUND_ALTERNATIVES_2026_10_13.md) retains the
rare-boundary/finite-target route, conditional original-carrier extension,
and suitable applications. Compactness alone misses $H(C)\to0$.
Interior stationarity, deterministic-target coarsening, global concavity
of $J$, and nonnegative net synergy lack the required proofs and are unused.
Growing-alphabet four-limit examples do not transfer.
Shannon-only or direct-loss methods answer simpler questions, not this norm.
To resolve the optimum, prove a global upper three or exhibit a realizable
ratio above three; an uncertified finite scan cannot suffice.

Two routes sealed FIRST before reading one another; a third critic derived
controls before exposed full review. The coordinator read all full sources
and inspected algebra, endpoints and conditional steps.
They share model, host, paper dependencies and prior project context:
ordering independence is not institutional or human independence.
Fifty named lenses count coverage, not reviewers.
One author exceeded its 8,192-byte cap; the actual 9,155-byte predecessor was
preserved. Two later stream disconnects and service-limited unfinished
reviews are process failures, not mathematical refutations or successes.
No kernel, judge, numerical flag, tolerance or accepted claim was changed.

## 8. Rust implementation and computational cost

The bound, norm API and certified logarithm are UNIMPLEMENTED.
The default API is `stable::categorical::discrete_sxpid2_averaged_with_budget`
in [crates/pid-core/src/sxpid.rs](../crates/pid-core/src/sxpid.rs).
Its cancellation variant adds cooperative cancellation, not a hard deadline.
Neither supplies a certified real-number bound certificate.

For $N$ aligned rows and $K$ target labels, at most $4K$ triple cells
are occupied. Proposed deterministic tree counting costs
$O(N\log(K+1)+K)$ time and $O(K)$ memory; validated dense codes permit
$O(N+K)$. Prevalidated count laws need $O(K)$ work/memory.
Computing only the entropy ceiling needs two $C$ counts:
$O(N)$ time, constant storage and scalar work.
$O(\cdot)$ denotes asymptotic cost, not measured latency.
No training/resampling is needed for the empirical-law identity;
fitted encodings and predictive comparisons have separate costs.

Implementation needs checked totals, normalization, finite/shape checks,
fallible allocation, resource preflight, cooperative cancellation and outward
logarithm arithmetic. Near-zero entropy and signed cancellation challenge
binary64 evaluation; exact zero needs its own branch.
No clamping, silent smoothing, overflow saturation or looser tolerance is
permitted. No timing, hard-deadline, online suitability, Rust refinement,
generic calibration, real-data advantage or programme closure is reported.

Cite: Sepehr Mahmoudian, *Binary shared-exclusions allocation: a uniform entropy
bound* (2026), with the exact repository commit or release.
Use [CITATION.cff](../CITATION.cff) for software and cite MGW separately.
