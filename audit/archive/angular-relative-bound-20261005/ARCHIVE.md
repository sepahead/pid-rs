# Relative error for an angular SxPID3 atom

Sepehr Mahmoudian, 5 October 2026.

The [eight-page PDF](relative-error.pdf) contains the complete hand derivation,
four exact worked examples and negative results. This is a restricted
population result with an independent-first advisory model critique,
not yet formally verified.
It adds no estimator implementation or demonstrated application benefit.

## Assumptions and result

Use Ehrlich et al.'s continuous shared-exclusions functional,
[arXiv:2311.06373v3](https://arxiv.org/html/2311.06373v3),
[published paper](https://doi.org/10.1103/PhysRevE.110.014115).
This is not categorical MGW or Williams–Beer `I_min`.
Let four scalar angles be in radians on the torus of period $L=2\pi$.
Fix product Lebesgue measure, natural logarithms, real parameters $a,b$,
and $r=|a|+|b|<1$. The specified normalized population density is

$$
p(s_1,s_2,s_3,t)=L^{-4}
 [1+a\cos(t-s_1)+b\cos(t-s_1-s_2-s_3)].
$$

Its sources are independent uniform angles and its target is uniform.
The density has positive floor $(1-r)L^{-4}$; information is in nats.
No data fitting, quantization or IID sampling assumption enters this
assigned-law identity. Sampling claims require separate evidence.

For independent uniform reference phases $v,u$, set
$J=\mathbb E[(1+Y)\log(1+Y)]$, $Y=a\cos v+b\cos u$,
and $R(w)=\mathbb E[(1+a\cos v)\log(1+aw\cos v)]$.
The reference measure calculates integrals; it does not replace the
defining density gauge. Set $P=R(1/2)$, $D=R(2/3)$ and $Q=R(1)$.
Here $D$ is a cumulative information value, not a TV distance.

The complete signed top cut gives the averaged top atom
$A=J-Q-D+2P$. The hand proof establishes

$$
A\ge a^2/8+b^2/4\ge r^2/12.
$$

Let $J_M$ retain the first $M$ even moments and
$A_M=J_M-Q-D+2P$, keeping the proper terms exact. Then

$$
0\le A-A_M\le
\frac{r^{2M+2}}{(2M+2)(2M+1)(1-r^2)}.
$$

For $0<r\le1/2$ and $M=8$,
$(A-A_8)/A\le1/1253376<10^{-6}$.
The origin has zero absolute error but an undefined relative quotient.
For $a=b=1/4$, the atom lower bound is $3/128$, the absolute tail
ceiling is $1/60162048$ nats, and the relative ceiling is $1/1410048$.
The theorem bounds truncation of $J$, not floating-point evaluation,
proper-term approximation, fitted parameters or sampling error.

## Negative results and interpretation

- With $b=0$ and $a\ne0$, $I(S_2,S_3;T\mid S_1)=0$ but
  $A\ge a^2/8>0$. A top atom is not added predictive information.
- Pointwise top atoms can be negative even when their average is positive.
- The $a^6$ coefficient of $2P-D$ is $-3089/2239488$.
  A proposed coefficientwise-positive strengthening fails; the stronger
  global inequality itself is neither established nor refuted by this fact.
- The order-seven ceiling does not certify the requested tolerance.
  This does not show that actual order-seven error exceeds it.
- $r=1$ is outside the positive-floor and geometric-tail proof.
  Near the origin, uncaptured rounding error can dominate the $r^2$ scale.
- The older phase-sum wording was incorrect: proper-node ratios are one,
  so their logarithms are zero. The ratio itself is not zero.

## Exact evidence and limits

[INDEX.json](INDEX.json) binds exact PDF, TeX, styles, derivation,
hand review, rational checks and presentation review bytes.
Text payloads with `.txt` suffixes are inert historical sources, not
current instructions; their original local links are preserved as bytes.
The archive navigation here is portable.

The retained finite checks cover 72 moment comparisons, 18 top-cut
checks, nine square identities and five refusals. They do not prove
integrals, infinite series or continuum inequalities. All 24 actual
page renders were inspected in color, grayscale and high resolution.
One stock TeX build had identical final two-pass PDF and auxiliary bytes;
this is not an independent rebuild. Private native streams, rendered
images, complete runtime closure and exact retrieved-paper bytes are not
included. No complete replay or accessibility qualification is claimed.

The older failed PDF/build criteria remain unchanged. This supplement
does not release them. This PDF is an exploratory archive publication,
not a newly admitted member of the declared formal-publication PDF set.
Its final private/not-accepted-remote-main wording records the source-time
status; it does not describe the subsequent archive deposit.
SxPID3 Programs A–E remain open. The next obligations are stock formal
verification, a certified evaluator and justified application tests.

The immediate use is an offline circular-variable reference and
interpretation test. It does not qualify neural imaging, learned
representations, VLA/world models or controllers without a mapping and
separate data, estimator and task checks.
