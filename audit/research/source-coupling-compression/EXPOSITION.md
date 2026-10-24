# Source partitions and shared-exclusions information

Sepehr Mahmoudian · 24 October 2026

Development report: written derivations, model critiques and exact finite checks.
Z3 checked event/linear algebra, not the complete probability theorem.
New Lean 4.33.0 deductive acceptance remains held. Priority, calibration,
deployment benefit and complete SxPID3 closure are not claimed.

## 1. Question, definitions and assumptions

Which cheap quantities bound allocation movement when a representation changes,
even if its total predictive information stays unchanged?

The object is categorical Makkeh–Gutknecht–Wibral (MGW) shared exclusions,
[arXiv:2002.03356v5](https://arxiv.org/html/2002.03356v5).
Use natural logarithms and nats; the defining paper uses bits.
Keep every original source position and its complete redundancy carrier.
Signed net atoms may be negative. This is not continuous Ehrlich PID or another
redundancy measure.

Variables are finite categorical variables with normalized nonnegative laws.
Zero cells are allowed. No Gaussian statistics, independent rows, stationarity
or positive minimum probability is needed for a supplied-law calculation.
Statistical inference from observations would require a separate sampling model.

An antichain is a nonempty family of nonempty source-index subsets, none
containing another. Its members are branches. A node event matches every coordinate within at
least one branch. Write \(\beta\preceq\alpha\) when every branch of \(\alpha\)
contains a branch of \(\beta\). Cumulatives sum lower atoms; inversion recovers them.

| Symbol | Meaning and domain |
|---|---|
| \(r,[r],i\) | Positive number of original sources, indices \(\{1,\ldots,r\}\), one index |
| \(S,S',T\) | Old and new source vectors, with the same finite target |
| \(P\) | One joint law of \((S,S',T)\), called a coupling |
| \(B,S_B\) | Nonempty original index subset and its joint source subvector |
| \(\alpha,\beta,\mathcal L\) | Antichains and their complete original carrier |
| \(E_\beta^S(s)\) | Source-match event at anchor \(s\) |
| \(G_\beta,C_\beta,\Pi_\alpha\) | Mean event surprise, net cumulative, net atom; all in nats |
| \(U_{\alpha\beta}\) | Fixed inverse entry, output atom row and input cumulative column |
| \(H,I\) | Shannon entropy and mutual/conditional information, in nats |
| \(V_B,w_B\) | Conditional-entropy cost and its nonnegative integer weight |
| \(\Delta_\alpha,D\) | Old-minus-new atom change and its total absolute movement, in nats |

Let \(A,B\) here be any finite variables; this \(B\) is not an index subset.
Entropy is \(H(A)=-\sum_{a:P(a)>0}P(a)\ln P(a)\).
Conditional entropy \(H(A\mid B)\) averages the entropy of \(P(A\mid B=b)\)
over positive-mass \(b\). Mutual information is
\(I(A;T)=H(T)-H(T\mid A)\). Null anchors are omitted; \(0\ln0=0\) is the
equivalent convention. Every evaluated log argument is positive.

We use the finite entropy chain rule and
\(H(A\mid B,T)\le H(A\mid B)\).
The latter difference is conditional mutual information, an average of
\(\sum p\ln(p/q)\), with \(q\) the product of conditional marginals.
For \(x>0\), \(-\ln x\ge1-x\), so
\(\sum p\ln(p/q)\ge\sum_{p>0}(p-q)\ge0\).
Expanding finite conditional probabilities gives the chain rule.
These steps do not assume independent source pairs.

## 2. Main upper certificate

The coupling must realize BOTH specified marginals \(P(S,T)\) and \(P(S',T)\).
An arbitrary matching of source histograms that ignores their targets is not
enough. For each collection \(B\), define variation of information
\[
V_B=H(S'_B\mid S_B)+H(S_B\mid S'_B).
\]
It measures changes between partitions under the specified paired source law;
see [Meilă (2005)](https://icml.cc/Conferences/2005/proceedings/papers/073_ComparingClustering_Meila.pdf).
It is target-free for that coupling, not a marginal-histogram distance.

For the fixed inverse \(U\), set
\[
c_\beta=\sum_\alpha|U_{\alpha\beta}|,\qquad
w_B=\sum_{\beta:B\in\beta}c_\beta,\qquad
D=\sum_\alpha|\Pi_\alpha(S;T)-\Pi_\alpha(S';T)|.
\]
Here \(B\in\beta\) means actual branch membership. Then
\[
\boxed{D\le\sum_{\varnothing\ne B\subseteq[r]}w_BV_B.}\tag{1}
\]
For three original sources the exact coefficients give
\[
\boxed{D\le22\sum_{|B|\in\{1,2\}}V_B+V_{\{1,2,3\}}
       \le67\sum_{i=1}^3V_{\{i\}}.}\tag{2}
\]
No net-atom positivity, component-atom positivity, target-size factor or
cell-probability floor is needed. Coefficients grow with the carrier, and
entropic costs can grow with alphabet complexity. This is not a
source-count-free or optimal bound.

### Proof 1: the event functional

At supported source \(s\), define
\[
E_\beta^S(s)=\bigcup_{B\in\beta}\{u:u_i=s_i\text{ for all }i\in B\},\qquad
G_\beta(S)=\sum_{s:P(s)>0}P(s)[-\ln P(E_\beta^S(s))].
\]
The event contains the anchor. At each positive source–target cell both its
unconditional and conditional event probabilities are positive.
Define \(G_\beta(S\mid T)\) by repeating this functional in each positive
target stratum and averaging with \(P(T=t)\).
Expanding the defining MGW log ratio gives
\[
C_\beta(S;T)=G_\beta(S)-G_\beta(S\mid T).\tag{3}
\]
The unconditional term marginalizes over \(t\); the conditional term retains
the actual source–target-law weights.

### Proof 2: nested unions

Take \(m\) pairs of events \(C_j\subseteq D_j\), with \(P(C_j)>0\).
Here \(j=1,\ldots,m\) labels branches.
Write \(c_j=P(C_j)\), \(d_j=P(D_j)\),
\(c=P(\bigcup_jC_j)\), \(d=P(\bigcup_jD_j)\).
Set difference and the union bound give
\[
d-c\le\sum_j(d_j-c_j).
\]
Because \(c\ge c_j>0\),
\[
\frac dc\le1+\sum_j\frac{d_j-c_j}{c}
 \le1+\sum_j\left(\frac{d_j}{c_j}-1\right)
 \le\prod_j\frac{d_j}{c_j}.\tag{4}
\]
For the last step expand a product of \(1+a_j\), where \(a_j=d_j/c_j-1\ge0\);
the omitted cross terms are nonnegative. Thus
\(0\le\ln(d/c)\le\sum_j\ln(d_j/c_j)\).
Overlapping or dependent branches are allowed.

### Proof 3: deterministic refinement

Let a fine vector \(F\) be coarsened coordinatewise to \(A\), keeping the
same original positions. At supported \(f\), its coarse value is \(a\).
For branch \(B\), use \(C_B=\{F_B=f_B\}\subseteq D_B=\{A_B=a_B\}\).
Apply (4), take logs and average:
\[
0\le G_\beta(F)-G_\beta(A)
 \le\sum_{B\in\beta}H(F_B\mid A_B).\tag{5}
\]
Indeed the mean branch log ratio is
\[
\sum_fP(f)\ln\frac{P(A_B=a_B)}{P(F_B=f_B)}
=\sum_{f_B}P(f_B)[-\ln P(F_B=f_B\mid A_B=a_B)].
\]
Unused coordinates sum out, and the deterministic coarse projection supplies
the correct coarse-law average. The right side is conditional entropy.

Repeat within each positive \(T=t\) stratum, then average over \(t\).
The conditional increment is between zero and
\(\sum_{B\in\beta}H(F_B\mid A_B,T)\), hence no larger than the
unconditional bound in (5). No null-stratum ratio is formed.

### Proof 4: a common refinement

Put \(Z_i=(S_i,S'_i)\) at ONE original position \(i\).
The paired vector \(Z\) still has \(r\) sources.
It projects coordinatewise to \(S\) and \(S'\). Set
\[
a_\beta=\sum_{B\in\beta}H(S'_B\mid S_B),\qquad
b_\beta=\sum_{B\in\beta}H(S_B\mid S'_B).
\]
Both \(G_\beta(Z)-G_\beta(S)\) and its conditional counterpart lie in
\([0,a_\beta]\). Their difference, by (3), has absolute value at most
\(a_\beta\). Two numbers in this same interval differ by at most its length;
there is no extra factor two. The reverse projection gives \(b_\beta\), so
\[
|C_\beta(S;T)-C_\beta(S';T)|
 \le a_\beta+b_\beta=\sum_{B\in\beta}V_B.\tag{6}
\]
Only Shannon entropy was conditioned; no monotonicity of signed PID was used.

### Proof 5: unchanged-carrier inversion

Order lower nodes first. Let the incidence matrix be \(M\), with
\(M_{\alpha\beta}=1\) when \(\beta\preceq\alpha\), zero otherwise.
It is lower triangular with unit diagonal. In the next recurrence \(i,j,k\)
index ordered nodes, not sources; \(\mathbf1_{i=j}\) is one if \(i=j\), zero otherwise.
Its inverse satisfies
\[
U_{ij}=\mathbf1_{i=j}-\sum_{k<i}M_{ik}U_{kj}.\tag{7}
\]
Finite averaging commutes with this fixed linear map, so \(\Pi=UC\).
Define \(\Delta C_\beta=C_\beta(S;T)-C_\beta(S';T)\).
Triangle inequalities now give
\[
D\le\sum_{\alpha,\beta}|U_{\alpha\beta}|\,|\Delta C_\beta|
 \le\sum_\beta c_\beta\sum_{B\in\beta}V_B
 =\sum_Bw_BV_B.
\]
This proves (1).

The three-source integer matrix was checked in both directions:
\(MU=UM=I\). Its column weights are:

| Original-node family | Number | \(c_\beta\) each |
|---|---:|---:|
| Three singleton branches | 1 | 8 |
| Two singleton branches | 3 | 4 |
| Singleton plus complementary pair | 3 | 4 |
| Three pair branches | 1 | 8 |
| Two pair branches | 3 | 4 |
| One singleton | 3 | 2 |
| One pair | 3 | 2 |
| Full branch | 1 | 1 |

A fixed singleton appears in columns weighted \(8+4+4+4+2=22\);
the same holds for a fixed pair. The full branch appears only at the top.
By the entropy chain rule,
\(V_B\le\sum_{i\in B}V_{\{i\}}\).
Each source belongs to one singleton, two pairs and the full collection:
\(22+22+22+1=67\), proving (2).

## 3. A cheaper lower certificate

Define coalition and full mutual-information changes
\[
L_B=I(S_B;T)-I(S'_B;T),\quad L=L_{[r]},\quad
\Delta_\alpha=\Pi_\alpha(S;T)-\Pi_\alpha(S';T).
\]
Let \(J_B=\{\alpha\in\mathcal L:\alpha\preceq\{B\}\}\).
The sole-branch cumulative is \(I(S_B;T)\). Reconstruction therefore
partitions atom positions into \(J_B\) and its complement:
\[
L_B=\sum_{\alpha\in J_B}\Delta_\alpha,\qquad
L-L_B=\sum_{\alpha\notin J_B}\Delta_\alpha.
\]
Applying the triangle inequality to the two disjoint sums proves
\[
\boxed{\max_{\varnothing\ne B\subseteq[r]}
 (|L_B|+|L-L_B|)\le D.}\tag{8}
\]
Seven old/new coalition comparisons use fourteen MI values for three sources. A certified lower bound
above an allocation tolerance rejects fidelity; a small lower bound cannot
accept it. For arbitrary coupling \(L\) may be signed.

For deterministic compression \(S'=f(S)\),
\(L=I(S;T\mid S')\ge0\). Set
\(R=\sum_\alpha\max(-\Delta_\alpha,0)\).
Positive-minus-negative and positive-plus-negative sums give
\[
\sum_\alpha\Delta_\alpha=L,\qquad D=L+2R.\tag{9}
\]
Thus allocation movement includes redistribution, not just lost prediction.

For outward intervals, use interval distance from zero to lower-bound an
absolute value; subtract endpoints outward before the second absolute value.
Midpoint absolute values are unsafe. Exact rational products identify zero;
an interval overlapping zero is not permission to clamp an atom.

## 4. Exact invariance and a recoverable-tuple counterexample

For a fixed deterministic map \(f\) on occupied source states, these are
equivalent:

1. Every coordinate equality partition is preserved:
   \(s_i=u_i\) if and only if \(f_i(s)=f_i(u)\) on occupied pairs.
2. All original net atoms are unchanged for every finite target kernel.
   Binary targets already suffice.

For sufficiency, preserve coordinate matches, then branch ANDs and node ORs.
All event masses, conditional masses, inversion and averages are unchanged.
Each new coordinate is equivalently a bijection of its old occupied values.
This is the known re-encoding premise in
[Matthias et al., v2, Property 2](https://arxiv.org/html/2512.16662v2).

For necessity, if an old value merges two states that the new coordinate
separates, choose the binary target indicating one of those new values.
The new coordinate determines the target, but the old one has positive
conditional entropy at the merged value. Singleton MI changes.
For the reverse partition violation use an indicator of one old value.
A fixed sum of original atoms therefore differs, contradicting complete
invariance. It is not an invariance test for one actual target, nor a converse for arbitrary
stochastic recodings. A constant target can make all net atoms zero.

For an exact counterexample let \(S_1=X=0\), \(Y=(S_2,S_3)\) be \(01\)
with probability \(\delta\), \(11\) with probability \(1-\delta\),
\(0<\delta<1\), and \(T=S_2\).
Fix heads \(00,11\) and map \(01\) to \(00\), keeping \(X,T\).
Training counts \(00:50,11:49,01:1\) could freeze those heads;
they are not reselected on evaluation.

Originally only \(S_2=T\) varies; afterward \(S'_2=S'_3=T\).
The tuple remains invertible on this support:
\(H(Y\mid Y')=H(Y\mid X,Y')=L=0\).
The old informative cumulatives are the incidence column above node
\(\{\{2\}\}\), scaled by target entropy; the new ones use
\(\{\{2\},\{3\}\}\). All misinformative terms vanish because \(T\)
determines every source. Define \(h_2(x)=-x\ln x-(1-x)\ln(1-x)\). Inversion gives
\[
\Pi_{\{\{2\}\}}=h_2(\delta),\qquad
\Pi'_{\{\{2\},\{3\}\}}=h_2(\delta),\qquad
D=2h_2(\delta)>0,
\]
Other net atoms are zero.
The source-3 lower cut attains this value. Exact controls covered
\(\delta=1/2,1/100,1/10000\).
Joint recoverability therefore cannot force zero original allocation movement,
even for arbitrarily small positive tails.

## 5. A conditional exact eighteen-position comparison

Suppose complete dropped tuple \(Y=(S_2,S_3)\) has two occupied values and
\(g(Y)\) is injective on them, keeping \(X=S_1,T\).
Let \(J\subseteq\{2,3\}\) contain coordinates differing between the old values,
and \(J'\) the corresponding new set. They are nonempty.
At a positive anchor put \(E=\{X=x\}\), \(F=\{Y=y\}\).

Every varying coordinate-match event equals \(F\); a constant one is true.
No assumption that all four Boolean match patterns occur is used.
Node events reduce to true, \(E\cup F,E,F,E\cap F\).
Their signed averages are \(0,R_2,A,B,C\), with
\(A=I(X;T),B=I(Y;T),C=I(X,Y;T)\).
Set \(U_X=A-R_2,U_Y=B-R_2,Q=C-A-B+R_2\).
These are four intermediate MGW scalars, not a regrouped final estimand.

Define literal original nodes
\[
R_J=\{\{1\}\}\cup\{\{j\}:j\in J\},\quad X_0=\{\{1\}\},\quad
C_J=\{\{j\}:j\in J\},\quad K_J=\{\{1,j\}:j\in J\}.
\]
In the order \(R_J,X_0,C_J,K_J\), the five event forms have incidence
\[
0000,\quad1000,\quad1100,\quad1010,\quad1111.
\]
These four incidences mean,
respectively: every branch contains 1 or meets \(J\); every branch contains 1;
every branch meets \(J\); every branch does both.
Placing \(R_2,U_X,U_Y,Q\) there reconstructs every original cumulative:
\(0,R_2,A,B,C\). Unit-triangular inversion makes this the full vector.

An injective tuple recoding preserves these scalars. If \(J=J'\), all original
atoms agree. Otherwise only the \(X_0\) position overlaps; the other three
values move to disjoint original nodes, proving
\[
\boxed{D=2(|R_2|+|U_Y|+|Q|),\quad J\ne J'.}\tag{10}
\]
One occupied tuple gives only the retained-source atom and \(D=0\).
Noninjective maps or three tuples cannot inherit (10).
Keep the global carrier in target strata containing one tuple and average
before taking absolute values. This is a written conditional result;
full source-to-formal correspondence remains open.

## 6. Recorded-data design and exact arithmetic

Use exposed [UCI864 Room Occupancy Estimation](https://archive.ics.uci.edu/dataset/864/room+occupancy+estimation)
(DOI 10.24432/C5P605) and
[UCI357 Occupancy Detection](https://archive.ics.uci.edu/dataset/357/occupancy+detection)
(DOI 10.24432/C5X01N), both CC BY 4.0. Labels are unaudited; timezone is unknown.

| Recording | Original source order | Original target | Training; validation; test |
|---|---|---|---|
| Room | S1_Light, S6_PIR, S7_PIR | Count 0,1,2,3 | 22–25 Dec 2017; 26 Dec; 10–11 Jan 2018 |
| Office | Light, CO2, Temperature | Occupancy 0,1 | 2–8 Feb 2015; 9–10 Feb; 11–18 Feb |

Sort the \(n\) training values; use one-based rank \(\lfloor(n+1)/2\rfloor\),
encoding 1 strictly above that lower median, ties 0.
Room light threshold is 1 lux; passive infrared (PIR) inputs are native bits.
Office thresholds are 0 lux, 455 parts per million (ppm), 20.745 °C.
This defines categorical inputs, not PID of the original continuous readings.
Reject invalid/missing rows, duplicate timestamps and unexpected dates; do not
drop or repair them. Retain room's seven local dates despite four-day provider prose.

Rank complete training \(Y\) tuples by count, lexical ties. Keep the top two,
mapping every other legal tuple to the first. Both recordings select 00/11.
Preserve each row's \(X,T\) and add collision counts; complete \(X,T\) law is
unchanged and total variation equals tail mass.
Maps, encoders and predictors stay training-frozen.
There are 24 daily and 6 overlapping pooled laws: two recordings, not 30 datasets.

For \(N\) rows, \(c_z\) counts positive joint anchor \(z\). Let \(u_z\) be its
source-event count, \(v_z\) the target-restricted event count, \(t_z\) its target
count. These are positive at evaluated anchors. Net cumulatives equal
\[
N^{-1}\ln\prod_{z:c_z>0}
 \left(\frac{Nv_z}{u_zt_z}\right)^{c_z}.
\]
Informative/misinformative factors use \(N/u_z,t_z/v_z\).
Integer inversion preserves exact rational products; compare with one for
signs and zeros. All 108 stage/component keys hold paired before/after
records, hence 216 numerical values, not 108 atoms.

For rational \(x>0\), reduce \(x=2^ky,\ 1\le y<2\), integer \(k\), and
\(z=(y-1)/(y+1)\). Then \(0\le z<1/3\), and
\[
\ln y=2\sum_{i=0}^{63}\frac{z^{2i+1}}{2i+1}+R_{64},\qquad
0\le R_{64}\le\frac{2z^{129}}{129(1-z^2)}.
\]
Replace later denominators by 129 and sum the geometric tail to obtain this
remainder. The same series at \(z=1/3\) encloses \(\ln2\).
Negative \(k\) swaps scaled endpoints. Round outward onto denominator
\(2^{80}\), propagate signed coefficients, require width at most
\(10^{-12}\) nats. Float values are display only. PID laws are unsmoothed;
nothing is clamped and no accuracy/guard/kernel/default is changed.

Separate implementations compare exact keyed products. Prime exponents defer
arithmetic; ordinary normalized Fractions remain. Old/new controls agree.
Two 180-second timeouts remain failed. Full runs took 22.29/22.19 seconds on
M4 Max/128 GiB, with 80.4/82.9 MB process peaks. All 121 artifacts match
across ordinary/optimized modes, as do 29 earlier partial laws. Timing is descriptive, not a controlled speedup.

### Models and actual byte costs

Fit Laplace-1 lookup models: full \(F(T\mid X,Y)\), compressed-refit
\(G(T\mid X,g(Y))\), retained-source-only and target-only.
Also evaluate unchanged \(F\) at remapped inputs.
Probability is \((a_t+1)/(a+m)\), with training target count \(a_t\),
training context total \(a\), and fixed original class count \(m=4\) or 2.
Unseen contexts are uniform; there is no tuning or model selection.

Scores are mean negative log probability and multiclass Brier score (squared
probability error)
\(\sum_t(q_t-\mathbf1_{t=T})^2\), with predicted probabilities \(q_t\).
This differs from known-law \(L=H(T\mid X,g(Y))-H(T\mid X,Y)\).
Absent evaluation classes have unavailable class losses.

Containers encode binary sources: one retained bit plus fixed two-bit tuple,
lossless dictionary or lossy one-bit tuple. Count header, codebook, names,
thresholds, row count and padding; check decoding. Exclude target, timestamps,
raw readings, shared software and acquisition costs. The test-stream dictionary
is offline feature-only coding with transmitted overhead, not a fitted map.

## 7. Results and limitations

Numbers below are rounded nats; exact counts, products and outward intervals
remain in the machine records. The new upper-bound check is explicitly
post-study: all 30 laws and 2,700 node inequalities were checked, not selected.

| Recording/role | Rows | Tail | \(D\) | Lost MI \(L\) | MI lower cut |
|---|---:|---:|---:|---:|---:|
| Room train | 7021 | 585/7021 | 0.309875 | 0.097702 | 0.224412 |
| Room validation | 1063 | 0 | 0 | 0 | 0 |
| Room test | 2045 | 92/2045 | 0.341754 | 0.044689 | 0.210829 |
| Office train | 8794 | 707/4397 | 0.421590 | 0.020949 | 0.136466 |
| Office validation | 2014 | 549/1007 | 1.336128 | 0 | 0.402366 |
| Office test | 9752 | 4783/9752 | 0.582280 | 0 | 0.291415 |

![Pooled-test allocation movement, cheaper MI lower certificate and lost joint information. All are in nats but answer different questions.](figures/allocation-comparison.pdf)

A fair range comparator uses the extra published premise in MGW Theorem IV.3:
component atoms are nonnegative, summing to \(H(S)\) and \(H(S\mid T)\).
Triangle inequalities therefore give
\[
D\le H(S)+H(S\mid T)+H(S')+H(S'\mid T)
 \le2[H(S)+H(S')].\tag{11}
\]

| Recording/role | Coupling upper(1) | Component-range upper(11) |
|---|---:|---:|
| Room train | 26.956702 | 3.408395 |
| Room validation | 0 | 1.911905 |
| Room test | 16.650180 | 2.311007 |
| Office train | 49.429024 | 5.059041 |
| Office validation | 43.983542 | 3.359736 |
| Office test | 27.776867 | 4.354175 |

The range wins on every nonzero pooled law. Bound (1) supplies no useful small
positive-error certificate here: its value is partition-sensitive continuity
and the exact zero endpoint. Numerical superiority or optimality is not shown.

Mean log-loss below is in nats per row; Brier scores in the full output are dimensionless.

| Pooled test | Full loss | Fixed remap | Compressed refit | Retained only |
|---|---:|---:|---:|---:|
| Room | 0.204922 | 0.288580 | 0.258447 | 0.320536 |
| Office | 0.312825 | 0.272705 | 0.267742 | 0.270571 |

![Frozen predictors have different loss trade-offs; lower is better. Target-only and all class scores remain in the full output.](figures/prediction-comparison-v2.pdf)

Room test has zero rows for target class 1; all four classes stay in the output.
Refitting harms room average test loss and improves office average test loss.
Office occupied-class loss nevertheless worsens from 0.148113 to 0.188528.
Room validation contains only target 0: its empirical NET atoms and \(D,L\)
are zero, yet refit loss worsens from 0.057204 to 0.094076.
An evaluation-law invariance statement does not freeze a predictor fitted on
a differently transformed training law. There are no population, causal,
calibration or statistical-superiority conclusions.

### A real two-tuple example

Office test has tuple 10 on 4783 rows and tuple 11 on 4969 rows.
The CO2 bit is always 1; physical CO2 need not be constant.
The map 10→00, 11→11 makes the new CO2-position bit copy temperature.
It is injective on this observed support: joint predictive information is
unchanged, but source attribution moves.

![Observed office test recoding. The light bit and target stay unchanged; joint recovery does not preserve individual source partitions.](figures/office-recoding.pdf)

In (10), \(J=\{3\}\) changes to \(J'=\{2,3\}\).

| Scalar | Old original node | New original node | Signed value, nats |
|---|---|---|---:|
| \(R_2\) | \(\{\{1\},\{3\}\}\) | \(\{\{1\},\{2\},\{3\}\}\) | 0.178414142 |
| \(U_X\) | \(\{\{1\}\}\) | same | 0.069388796 |
| \(U_Y\) | \(\{\{3\}\}\) | \(\{\{2\},\{3\}\}\) | -.032706479 |
| \(Q\) | \(\{\{1,3\}\}\) | \(\{\{1,2\},\{1,3\}\}\) | 0.080019167 |

Other net atoms are zero. Using unrounded values in (10) gives
\(D\approx0.582279577\).
The negative atom stays; it is not causal sensor importance.

Fixed/lossless/lossy test containers use 3949/2721/2718 bytes.
Lossless coding costs only three extra header bytes over lossy, at the same
payload width. After decoding original \(y\), a receiver can still evaluate
the identical \(G(x,g(y))\). It obtains the same predictor probabilities while
retaining original coordinates for attribution and audit.
This is a derived software alternative, not another deployed experiment.
It depends on the stated offline codebook, not unknown future support.
Model choice need not require discarding the original representation.

## 8. Evidence, failures and research process

Independent-first model critiques and root inspection reviewed the written
proofs; no named human verification receipt exists. Nested-union and
one-branch-refinement routes agree. FIRST records preceded cross-member
conclusions. Root checked premises and artifacts rather than voting.
Routes included no action, MI/CMI, direct loss, lossless coding and full-carrier
evaluation; named hostile lenses are coverage, not independent people.

Stock Z3 5.3.1 accepted 46 unsat and 3 sat outcomes for explicit event
congruences, coalition/sign inequalities and missing-premise controls.
The 28 sign cases reduce to 14 coefficient forms. Exact matrices give 22/67.
These are algebra checks, not a formal probability theorem.
Old 4.16 gates and Lean pins were unchanged.

Prior data/results were exposed. Algorithmic revisions preserved failed
attempts and fixed scientific predicates; no best-of-N scientific winner was
selected. Model family, defining paper, interpreter, host, owner and custody
are common failure cuts. Training exposure is unknown; agreement cannot
establish originality or an absence of publications from training.
Bounded searches found related invariance/partition work, not global priority.

Retained false routes include marginal equality or whole-vector recovery as
fidelity certificates, unrestricted one-direction costs, pointwise extensions,
changed targets/mismatched couplings and alphabet-free disagreement bounds.
Event surprise is not generally concave: masses 1/2 on 00/11 give \(G=\ln2\),
a point mass at 01 gives zero, but their equal mixture gives
\(\tfrac12\ln(4/3)<\tfrac12\ln2\).
A source-format draft and two figure-export attempts also failed and remain.
Corrections changed no scientific kernel, default, precision or expected outcome.

Probability formalization, source/Rust correspondence, sampling calibration,
public/main admission and general SxPID3 A–E closure remain open.

## 9. Rust implementation and computational cost

Existing default `stable::categorical::discrete_sxpid_n` supports 2–4 sources.
The new bounds/comparison have no production Rust API. Exact Python references
use 3 binary sources, up to 4 targets, \(N\le32768\) rows and occupied support
\(Q_{\rm occ}\le32\).

Medians cost \(O(N\log N)\); counting/scoring cost \(O(N)\).
Direct events cost \(O(18Q_{\rm occ}^2\cdot3)\).
Dense inversion needs quadratic storage and cubic arithmetic.
Integer powers, gcds and series have bit-dependent costs, with a
1,048,576-bit per-integer limit. Preflight, deadline or unresolved intervals
fail; accuracy is not relaxed.

Source costs and seven coalition MIs can bracket fidelity before full atom
evaluation. Neural/imaging/embodied uses require their own categorical mapping,
paired transformation, target and validation. No neural inference, resampling,
online-control, sensor-removal or energy experiment occurred.

## 10. Reproduction and citation

[summary.csv](summary.csv) covers all 30 laws. Exact records retain counts,
products, intervals, class losses, matrices and failed/successful attempts.
This local development draft has not passed public/mainline admission.

Method: Makkeh, Gutknecht and Wibral (2021), *Introducing a differentiable
measure of pointwise shared information*,
[v5](https://arxiv.org/abs/2002.03356v5),
[version of record](https://doi.org/10.1103/PhysRevE.103.032149).
Meilă's partition source is linked in Section 2.
Re-encoding context: Matthias, Makkeh, Wibral and Gutknecht (2026),
*[Novel Inconsistency Results for Partial Information Decomposition](https://arxiv.org/html/2512.16662v2)*,
Property 2. Data sources and DOIs are in Section 6.
Software: [CITATION.cff](../../../CITATION.cff).

Suggested citation: Sepehr Mahmoudian, *Source partitions and shared-exclusions
information* (2026), with the exact containing commit/release. Cite MGW separately.
