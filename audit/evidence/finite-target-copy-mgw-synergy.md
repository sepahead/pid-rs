# Finite target-copy identities and entropy bounds for categorical MGW synergy

## Result, scope, and evidence status

This note gives an exact finite-law calculation for the categorical shared-exclusions PID of
Makkeh, Gutknecht, and Wibral (MGW). The target copies source one and can contain an arbitrary
residual coordinate:

$$
S_1\in A,\qquad S_2\in C,\qquad U\in B,\qquad T=(S_1,U)\in A\times B,
$$

where $A$, $C$, and $B$ are finite alphabets. No independence or full-support premise is imposed.
For every positive-mass realization with source values $(x,y)$, define

$$
a=P(S_1=x),\qquad c=P(S_2=y),\qquad
j=P(S_1=x,S_2=y),\qquad d=a+c-j.
$$

The local signed-net two-source MGW synergy is

$$
\boxed{
s(x,y,u)=\log\frac{ac}{j(a+c-j)}
}
\tag{1}
$$

in nats. It does not depend on $u$ or on the conditional law of $U$ after the complete source
joint law is fixed. If

$$
q(x,y)=P(S_1=x,S_2=y),\quad
q_1(x)=\sum_y q(x,y),\quad q_2(y)=\sum_x q(x,y),
$$

then the averaged synergy is

$$
\boxed{
S(P)=\sum_{q(x,y)>0}q(x,y)
\log\frac{q_1(x)q_2(y)}
{q(x,y)\,[q_1(x)+q_2(y)-q(x,y)]}
}
\tag{2}
$$

and the exact bounds are

$$
0\le s(x,y,u)\le \log\frac{c}{j},\qquad
0\le s(x,y,u)\le \log\frac{a}{j},
\tag{3}
$$

$$
\boxed{
0\le S(P)\le
\min\{H(S_1\mid S_2),H(S_2\mid S_1)\}.
}
\tag{4}
$$

These are law-level identities for the paper-defined categorical MGW functional. The finite-law
derivation and its Lean formalization are repository work. This note makes no claim that the
identity, bounds, or formalization have novel scientific priority. Source correspondence and
priority require their own literature adjudication.

**Evidence status.** All eleven original targets have local Lean acceptance under the declared
imports and axiom policy. The [source graph](../formal/lean-mgw-target-copy/SOURCE_GRAPH.json)
binds their exact definitions, proofs, and judges. The
[execution record](../formal/lean-mgw-target-copy/HISTORICAL_EXECUTION.json) separates
those observations from replay and publication status. The table at the end of this note states
which conclusions belong to those eleven targets. The additional Shannon consequences and
worked examples are written derivations; they are not additional exported Lean theorems. The
[fresh replay acceptance record](../formal/lean-mgw-target-copy/REPLAY_ACCEPTANCE.json) reports
18 successful commands, including 17 exact source compilations and one same-kernel replay; its
private driver and result preimages remain outside the published tree.

## The finite law and the global copy premise

A complete categorical key is

$$
z=((x,y),(x',u))\in (A\times C)\times(A\times B).
$$

Let $p(z)\ge0$ and $\sum_zp(z)=1$. The target-copy premise is global on the nonzero support:

$$
p((x,y),(x',u))>0\quad\Longrightarrow\quad x'=x.
\tag{5}
$$

It is not enough for (5) to hold only at the key being evaluated. It must hold at every
positive-mass key because all event probabilities below sum over the whole law.

This law has an equivalent ordinary-world construction. Given any normalized nonnegative law
$w(x,y,u)$ on $A\times C\times B$, define

$$
p((x,y),(x',u))=
\begin{cases}
w(x,y,u),&x'=x,\\
0,&x'\ne x.
\end{cases}
\tag{6}
$$

Then

$$
\sum_{x,y,x',u}p((x,y),(x',u))
=\sum_{x,y,u}w(x,y,u)=1,
$$

and every nonzero key satisfies (5). The observation map

$$
(x,y,u)\longmapsto ((x,y),(x,u))
$$

is injective, so it preserves each world's mass and turns every finite keyed event into its exact
preimage sum. Conversely, a law $p$ satisfying (5) is recovered by
$w(x,y,u)=p((x,y),(x,u))$. Thus the theorem covers every finite law for which $T=(S_1,U)$ almost
surely, including arbitrary dependence of $U$ on both sources.

For a positive anchor

$$
z=((x,y),(x,u)),\qquad \rho=p(z)>0,
$$

write

$$
\tau=P(T=(x,u)).
$$

All named quantities are actual sums from this one law. In particular,

$$
j=\sum_{u'\in B}p((x,y),(x,u')),\quad
a=\sum_{y'\in C}q(x,y'),\quad
c=\sum_{x'\in A}q(x',y).
\tag{7}
$$

The positive anchor gives

$$
0<\rho\le j\le a,\qquad 0<\rho\le j\le c,
\qquad 0<\rho\le\tau.
\tag{8}
$$

These relations establish the positive logarithm domains used below.

## Actual OR/AND events and positive-mass local cumulatives

MGW source-event syntax is an OR across source collections and an AND within a collection. For an
antichain $\alpha$ of source-index sets, the event at $(x,y)$ is

$$
E_\alpha(x,y)
=\bigcup_{J\in\alpha}\ \bigcap_{i\in J}\{S_i=s_i\}.
\tag{9}
$$

The four two-source cumulative nodes therefore use

$$
E_1=\{S_1=x\},\qquad E_2=\{S_2=y\},\qquad
E_{12}=E_1\cap E_2,\qquad E_{\mathrm{red}}=E_1\cup E_2.
\tag{10}
$$

The joint-source node is the within-collection AND. The redundancy node is the across-collection
OR. Inclusion-exclusion gives the actual redundancy-event mass

$$
P(E_{\mathrm{red}})=P(E_1)+P(E_2)-P(E_1\cap E_2)=a+c-j=d.
\tag{11}
$$

Let $F=\{T=(x,u)\}$ be the actual target event. On positive support, $F$ already implies
$S_1=x$ by (5). Consequently $E_1\cap F=F$ and
$E_{\mathrm{red}}\cap F=F$ up to zero-mass keys. The event $E_2\cap F$ fixes $S_2=y$, while $F$
and (5) fix $S_1=x$ and the complete target $(x,u)$, so it selects the anchor itself. The same is
true of $E_{12}\cap F$. Hence the exact event masses are

| cumulative node | source event | $P(E)$ | $P(E\cap F)$ |
|---|---|---:|---:|
| source one | $E_1$ | $a$ | $\tau$ |
| source two | $E_2$ | $c$ | $\rho$ |
| joint sources | $E_{12}$ | $j$ | $\rho$ |
| redundancy | $E_{\mathrm{red}}$ | $d=a+c-j$ | $\tau$ |

Every entry in the last two columns is positive: the relevant event contains the positive anchor.
Also $d\le1$ because it is a probability.

For any one of these source events, the MGW informative and misinformative local cumulatives in
nats are

$$
K^+(E)=-\log P(E),\qquad
K^-(E;F)=\log\frac{P(F)}{P(E\cap F)}
=-\log P(E\mid F),
\tag{12}
$$

and the signed net cumulative is

$$
K^{\mathrm{net}}(E;F)=K^+(E)-K^-(E;F)
=\log\frac{P(E\cap F)}{P(E)P(F)}.
\tag{13}
$$

The event masses are positive, so no totalized value such as $\log0$ enters the local
information. Both $K^+$ and $K^-$ are nonnegative because $P(E)\le1$ and
$0<P(E\cap F)\le P(F)$. Their signed difference need not be nonnegative. Substitution gives

| node | $K^+$ | $K^-$ | $K^{\mathrm{net}}$ |
|---|---:|---:|---:|
| source one | $-\log a$ | $0$ | $-\log a$ |
| source two | $-\log c$ | $\log(\tau/\rho)$ | $\log[\rho/(c\tau)]$ |
| joint sources | $-\log j$ | $\log(\tau/\rho)$ | $\log[\rho/(j\tau)]$ |
| redundancy | $-\log d$ | $0$ | $-\log d$ |

This table is the probability step that prevents the symbols $a,c,j,d,\rho,\tau$ from becoming
unconstrained algebra parameters.

## Local identity

The two-source Möbius row for the signed-net synergy atom is joint minus source one minus source
two plus redundancy. Using the last column of the table,

$$
\begin{aligned}
s(z)
&=K^{\mathrm{net}}_{12}-K^{\mathrm{net}}_1
  -K^{\mathrm{net}}_2+K^{\mathrm{net}}_{\mathrm{red}}\\
&=\log\frac{\rho}{j\tau}-(-\log a)
  -\log\frac{\rho}{c\tau}-\log d\\
&=(\log\rho-\log j-\log\tau)+\log a
  -(\log\rho-\log c-\log\tau)-\log d\\
&=\log a+\log c-\log j-\log d\\
&=\log\frac{ac}{jd}
=\log\frac{ac}{j(a+c-j)}.
\end{aligned}
\tag{14}
$$

All logarithm rules in (14) apply to positive quantities by (8) and the positive event-mass
argument. Both the anchor mass $\rho$ and target-event mass $\tau$ cancel. This proves (1) and
shows locally why the residual target coordinate drops out.

## Averaging, marginalization, and invariance

The averaged pointwise atom is the positive-support sum

$$
S(P)=\sum_{z:p(z)>0}p(z)s(z).
\tag{15}
$$

Equation (14) is constant over all positive target residuals at a fixed source row $(x,y)$. Since
$p$ is nonnegative and the alphabets are finite,

$$
\sum_{u:p((x,y),(x,u))>0}p((x,y),(x,u))=q(x,y).
\tag{16}
$$

Moreover, $q(x,y)>0$ exactly when at least one such residual-target cell has positive mass.
Regrouping (15) by source row and using $a=q_1(x)$, $c=q_2(y)$, and $j=q(x,y)$ gives (2) exactly.

Therefore two target-copy laws with the same complete source joint law $q$ have the same averaged
signed-net synergy. Equality of the separate marginals $q_1$ and $q_2$ is insufficient because
both $j=q(x,y)$ and $d=q_1(x)+q_2(y)-q(x,y)$ retain source dependence.

The current formal comparison quantifies two laws over one common residual alphabet $B$. It does
not export cross-type invariance between unrelated residual alphabets. Unused values of that
common $B$ are allowed, so constant and nonconstant residual channels can still be compared
without changing the formal target type.

There is also a useful written corollary, not a separate Lean export in this package.
The averaged redundancy in this family is

$$
R=-\sum_{q(x,y)>0}q(x,y)\log d(x,y),
$$

while

$$
I(S_1;S_2)=\sum_{q(x,y)>0}q(x,y)
\log\frac{q(x,y)}{q_1(x)q_2(y)}.
$$

Termwise subtraction yields

$$
S=R-I(S_1;S_2).
\tag{17}
$$

This is another statement about this exact target-copy family, not a general identity for MGW
synergy under arbitrary target channels.

## Local and averaged bounds

For a positive source cell, $j\le a$ and $j\le c$. Thus $a>0$, $c>0$, and

$$
d=a+c-j\ge a>0,\qquad d\ge c>0.
\tag{18}
$$

The lower bound follows from one exact factorization:

$$
ac-jd
=ac-j(a+c-j)
=ac-aj-cj+j^2
=(a-j)(c-j)\ge0.
\tag{19}
$$

Because $jd>0$, equation (19) gives $ac/(jd)\ge1$. The logarithm is increasing, so
$s\ge\log1=0$.

For the first upper bound, use $a/d\le1$ from $d\ge a$:

$$
\frac{ac}{jd}=\frac{c}{j}\frac{a}{d}\le\frac{c}{j},
\qquad
s\le\log\frac{c}{j}.
\tag{20}
$$

For the other bound, use $c/d\le1$ from $d\ge c$:

$$
\frac{ac}{jd}=\frac{a}{j}\frac{c}{d}\le\frac{a}{j},
\qquad
s\le\log\frac{a}{j}.
\tag{21}
$$

The right sides are the two local conditional surprisals:

$$
\log\frac{c}{j}=-\log P(S_1=x\mid S_2=y),\qquad
\log\frac{a}{j}=-\log P(S_2=y\mid S_1=x).
\tag{22}
$$

Multiply each resulting logarithmic bound, $0\le s$, (20), and (21), by
$q(x,y)\ge0$ and sum only over $q(x,y)>0$. The lower bounds sum to
$S\ge0$, and the upper bounds give

$$
S\le\sum_{q(x,y)>0}q(x,y)\log\frac{q_2(y)}{q(x,y)}
=H(S_1\mid S_2),
\tag{23}
$$

$$
S\le\sum_{q(x,y)>0}q(x,y)\log\frac{q_1(x)}{q(x,y)}
=H(S_2\mid S_1).
\tag{24}
$$

Equations (23) and (24) prove (4). The right sides are the usual finite conditional
entropies: averages of conditional surprisal under the actual joint law. This convention follows
[Shannon's conditional-entropy definition](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf),
Section 6, item 5. The Lean interface defines these positive-support sums explicitly; this
package does not claim a separate identification theorem with another entropy library.
A positive $q(x,y)$ makes both relevant marginals positive, so the sums have no zero denominator.

## Three exact examples

These are written specializations and consequences of the formulas above. Their arithmetic is
shown explicitly; they are not separate named exports in the eleven-target Lean roster.

### 1. Fair independent sources and an arbitrary residual target

Let $A=C=B=\{0,1\}$, and let $S_1$ and $S_2$ be independent fair bits. Keep any conditional
kernel $P(U=u\mid S_1=x,S_2=y)$; it can depend arbitrarily on both sources. For every source pair,

$$
a=c=\frac12,\qquad j=\frac14,\qquad d=\frac34.
$$

Therefore every positive target-copy key has

$$
s=\log\frac{(1/2)(1/2)}{(1/4)(3/4)}=\log\frac43,
$$

and the weights in (15) sum to one, so

$$
S=\log\frac43
\tag{25}
$$

for every residual channel. This already proves that synergy cannot rank residual-target task
gain while the source joint law stays fixed. Two channels over the same formal alphabet $B$ make
the point exact:

* If $U=0$ almost surely, then $T=(S_1,0)$ and
  $I(S_2;T\mid S_1)=0$.
* If $U=S_2$, then $T=(S_1,S_2)$ and
  $I(S_2;T\mid S_1)=H(S_2\mid S_1)=\log 2$.

Both channels have the same synergy (25). They have different information increments.
This comparison changes the residual target channel and thus changes the prediction task.
Ordinary sensor selection instead fixes a world and target while comparing available sources.
The [fixed-world example](mgw-fixed-world-added-information-2026-09-09.md)
makes that latter comparison: target $(A,B)$, baseline $A$, and additions consisting of either
an independent bit or $B$. Both additions have the same categorical MGW synergy, but only $B$
adds target information. The two examples address distinct experimental designs.

The signed two-source reconstruction explains the cancellation. If $U_2$ is source two's unique
atom and $R$ is redundancy, then

$$
I(S_2;T\mid S_1)=U_2+S.
\tag{26}
$$

Here $R=\log(4/3)$. For constant $U$, $I(S_2;T)=0$, hence
$U_2=-\log(4/3)$ and $U_2+S=0$. For $U=S_2$,
$U_2=\log 2-\log(4/3)$ and $U_2+S=\log 2$. The negative unique atom in the first channel is a
valid signed MGW contribution. Clamping it would break (26).

### 2. Copied sources give zero synergy

Let the sources share one finite alphabet and suppose $S_2=S_1$ almost surely. For every supported
value $x$, put $\mu_x=P(S_1=x)>0$. Then

$$
a=c=j=d=\mu_x,
$$

so

$$
s=\log\frac{\mu_x^2}{\mu_x^2}=0,
\qquad S=0.
\tag{27}
$$

For fair copied bits, the only positive source cells are $(0,0)$ and $(1,1)$, each with mass
$1/2$; the two off-diagonal zero cells are simply absent from the support sum. The conclusion is
unchanged for any residual channel compatible with the copied sources.

### 3. A dependent $2\times2$ source law

Let $A=C=\{0,1\}$, take a singleton residual alphabet, and use the source law

$$
\begin{array}{c|cc}
q(x,y)&y=0&y=1\\ \hline
x=0&3/8&1/8\\
x=1&1/8&3/8
\end{array}
\tag{28}
$$

with $T=(S_1,*)$. Both marginals are fair. On a diagonal cell,

$$
j=\frac38,\qquad d=\frac58,\qquad
s_{\mathrm{diag}}=\log\frac{1/4}{(3/8)(5/8)}=\log\frac{16}{15}.
$$

On an off-diagonal cell,

$$
j=\frac18,\qquad d=\frac78,\qquad
s_{\mathrm{off}}=\log\frac{1/4}{(1/8)(7/8)}=\log\frac{16}{7}.
$$

The two diagonal cells have total weight $3/4$, and the two off-diagonal cells have total weight
$1/4$. Thus

$$
S=\frac34\log\frac{16}{15}+\frac14\log\frac{16}{7}.
\tag{29}
$$

This differs from the independent fair-source value despite identical separate marginals. In
fact it is strictly smaller, without using a decimal approximation. Multiplying by four and
exponentiating reduces the comparison to

$$
\frac{16^4}{15^3\,7}<\frac{4^4}{3^4},
$$

which is equivalent to

$$
4^4\cdot3^4=20736<23625=15^3\cdot7.
$$

The example isolates why the invariance theorem requires the exact joint source law $q$, not only
$q_1$ and $q_2$.

![The complete source joint law determines target-copy synergy. Shading shows the OR event, and the inner frame marks the anchor cell. The two grids use the same joint law; changing the anchor changes its intersection mass and union mass. The lower calculation shows why positive target masses cancel.](../formal/latex/figures/mgw-target-copy/event-union.svg)

## The CMI complement and practical use

For this categorical MGW two-source decomposition, the reconstruction identities are

$$
\begin{aligned}
I(S_1;T)&=R+U_1,\\
I(S_2;T)&=R+U_2,\\
I(S_1,S_2;T)&=R+U_1+U_2+S.
\end{aligned}
$$

For finite variables, define $I(X;Y)=H(Y)-H(Y\mid X)$ and
$I(X;Y\mid Z)=H(Y\mid Z)-H(Y\mid X,Z)$. Subtracting the two MI expressions cancels
$H(Y)$, which gives the conditional-MI identity below. Subtracting the first MGW
reconstruction line from the third then gives (26):

$$
I(S_2;T\mid S_1)
=I(S_1,S_2;T)-I(S_1;T)=U_2+S.
\tag{30}
$$

In the target-copy family, this increment is also

$$
I(S_2;T\mid S_1)=I(S_2;U\mid S_1).
\tag{31}
$$

Equations (26), (30), and (31) are written Shannon/reconstruction consequences, not
additional formal exports. In (31), conditioning on $S_1$ fixes the copied coordinate of $T$;
only $U$ remains uncertain, before and after observing $S_2$.

The synergy atom separates one definition-specific part of the increment; it is not the increment
itself. A positive $S$ can be exactly cancelled by negative $U_2$. This is the correct signed
interpretation and is the main safeguard for analysis, training, and sensor selection.

For analysis, equations (1) and (2) provide an exact reference calculation for a declared finite
law. They can expose which source cells produce large signed-net synergy and can test a future
implementation after a separate code-to-formal-object mapping is established. Equation (17)
clarifies the mechanism in this family: source dependence and the shared-exclusion union mass
fully determine the result.

For training, include the fair-source example as a negative control when the proposed objective
fits this target-copy setting. If a learner controls a residual target representation $U$, it can
change that channel from constant to fully revealing while $S$ remains $\log(4/3)$ and the source
law stays fixed. This comparison changes the represented prediction task. It does not establish
failure for every learning method with a fixed target. When the objective is added predictive
information, compare CMI or the complete signed sum $U_2+S$; for an actual trained predictor, also
measure held-out task loss. A different atom weighting defines a different objective and needs
its own benefit evidence.

For sensor selection, the formula can diagnose a proposed source grouping, but it does not include
acquisition cost, failure cost, latency, coverage, causal effect, or learned-predictor error. A
selection claim must compare the relevant CMI or task-risk change, fixed-model and retrained
ablations, and the chosen decision cost. Positive synergy alone does not establish that adding a
sensor improves the task.

## Boundary cases and nonclaims

Zero probability cells are allowed. Local quantities are asserted only at $p(z)>0$, and averaged
quantities sum only over positive support. Thus the result never assigns scientific meaning to
totalized division by zero or $\log0$. Singleton alphabets are also allowed.

If the complete key space is empty, the sum of every nonnegative law over it is zero, so no
normalized law exists. The all-zero mass function likewise fails normalization. The theorem is
therefore vacuous for an empty law rather than an extension that assigns it information values.

An exact finite PMF needs no IID premise for these probability identities. If rows are used to form
an empirical PMF, the result describes that empirical law exactly. It does not turn the rows into
IID observations, prove that an observed copy relation holds in the population, control unseen or
rare cells, establish convergence or confidence coverage, or calibrate a finite-sample estimator.
Those claims require a sampling model and their own theorems.

The result also does not establish Rust or Python refinement, binary64 logarithm error, resource
bounds, continuous-variable shared exclusions, another PID functional, approximate-copy
stability, cross-residual-alphabet formal invariance, or downstream performance. It does not close
the three-source program or the wider pid-rs program.

## Formal target map

The frozen Lean interface divides the argument into eleven unchanged propositions:

| targets | mathematical role |
|---|---|
| `WorldBridgeTarget` | Push a normalized finite world law through the injective target-copy observation and preserve event preimages. |
| `CopyEventMassesTarget` | Prove the four target-restricted masses $\tau,\rho,\rho,\tau$ from global support copying. |
| `SourceUnionMassTarget` | Prove $d+j=a+c$ by exact finite inclusion-exclusion. |
| `LocalCumulativesTarget` | Derive the four signed-net cumulative formulas from actual positive event masses. |
| `SourceProjectionTarget` | Identify $a,c,j$ with the true source marginal and regroup every source-row integrand. |
| `LocalIdentityTarget`, `WorldLocalIdentityTarget` | Establish (1) for the imported MGW signed-net synergy at a positive key and at an observed world. |
| `AveragedIdentityTarget`, `SameSourceLawTarget` | Establish (2) and same-$q$ invariance for two laws over one common $B$. |
| `LocalBoundsTarget`, `AveragedBoundsTarget` | Establish (3) and (4). |

A checked theorem proves only its exact proposition under its imported definitions, axioms, and
toolchain. It does not by itself prove publication-to-Lean correspondence, executable refinement,
statistical calibration, application value, independent replay, or publication on the project
mainline.

## References

Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral, “Introducing a Differentiable Measure of
Pointwise Shared Information,” *Physical Review E* **103**, 032149 (2021),
[doi:10.1103/PhysRevE.103.032149](https://doi.org/10.1103/PhysRevE.103.032149),
[arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5). The paper defines the categorical
shared-exclusions construction, including the OR-of-AND source event, the
informative/misinformative split, the pointwise functional, the lower-cumulative atom relation,
and joint-law averaging. This note uses natural logarithms and therefore reports nats; bit-valued
expressions scale by the positive factor $\log 2$.

Claude E. Shannon, “A Mathematical Theory of Communication,” *Bell System Technical Journal*
**27**, 379–423 and 623–656 (1948), Section 6, item 5 and its entropy addition rule.
[Reprint](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf).
This is the classical entropy source, not the definition of categorical MGW PID.
