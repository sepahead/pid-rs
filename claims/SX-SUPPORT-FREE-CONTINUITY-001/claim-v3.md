# Claim SX-SUPPORT-FREE-CONTINUITY-001, revision 3

## Record status

Revision 3 was created on 2026-07-24 after the exact-real proof in
[`claim-v2.md`](claim-v2.md) had closed analytically and a later adversarial pass identified an
additional exact asymptotic result. It is retrospective, not preregistered, and makes no
scientific-priority claim.

Revision 3 incorporates every object, convention, equation, scope restriction, falsifier, and
nonclaim in Revision 2. It adds only the leading-order optimality statements below. Revision 2
remains immutable evidence of the earlier claim boundary.

The claim disposition is **closed for the exact-real analytic statements**. The formal route
checks supporting finite-vector, event-semantic, and fractional-cover subclaims. It does not check
the complete logarithmic functional, lattice, averaging, or Rust refinement path. Certified
binary64 error, estimator calibration, independent peer review, and consumer qualification remain
separate claims.

## Claim class

This is a project-defined exact-real theorem about the paper-defined averaged categorical
shared-exclusions PID. It defines neither a new PID measure nor a new estimator.

The novelty-safe description is:

> A project-defined, support-change-tolerant total-variation modulus for averaged categorical
> shared-exclusions quantities on a fixed finite alphabet, with fixed-system witnesses showing
> that a family of fixed-system component or net bounds cannot use common leading coefficients
> below one or two, even when its lower-order constants depend on the system.

No priority claim is made.

## Incorporated Revision 2 claim

All statements in [`claim-v2.md`](claim-v2.md) remain part of Revision 3. In particular, the
following objects remain fixed:

- a positive source count;
- nonempty finite source and target alphabets;
- their complete Cartesian-product alphabet;
- the full finite redundancy lattice, its order, and its Möbius inverse;
- the paper-defined keyed event map;
- support-restricted averaging;
- natural-logarithm units; and
- exact real arithmetic.

For laws $p$ and $q$, continue to use

$$
\eta=d_{\mathrm{TV}}(p,q),\qquad R=1-\eta,
$$

the coordinatewise overlap $r$, residuals $a$ and $b$, residual entropies
$E_\vee$ and $E_\Sigma$, the equivalence-union term $g_J$, the fixed Möbius matrix $M$, row sums
$s_\alpha$, and weighted branch terms $W_\alpha$ exactly as Revision 2 defines them.

Revision 3 does not change any inequality or endpoint convention in Equations (V2.1)--(V2.13).

## New exact asymptotic claim

### Upper orders

For a fixed alphabet size $K\ge2$ and fixed branch count $J$,

$$
e_K^\vee(\eta)
=
\eta\log\frac1\eta+O(\eta),
$$

$$
e_K^\Sigma(\eta)
=
2\eta\log\frac1\eta+O(\eta),
$$

and

$$
g_J(\eta)=O(\eta)
$$

as $\eta\downarrow0$.

### Component lower coefficients

The copied-source law path retained in
[`failures/exact-counterexamples.md`](failures/exact-counterexamples.md) has a fixed finite
alphabet and an informative unique atom equal to $h_2(\eta)$. Therefore

$$
\lim_{\eta\downarrow0}
\frac{h_2(\eta)}{\eta\log(1/\eta)}
=1.
\tag{V3.1}
$$

The constant-target paper-semantic equality witness has identical informative and
misinformative bottom atoms and total change

$$
\eta\log\frac1\eta+g_J(\eta).
$$

It gives the same coefficient-one limit for the misinformative family. These are fixed-system,
fixed-atom witnesses. Consider a family that assigns each covered fixed system $\mathcal F$ a
component-atom bound

$$
c\,\eta\log(1/\eta)+O_{\mathcal F}(\eta),
$$

where the lower-order constant may depend on $\mathcal F$ but $c$ is common. The witnesses force
$c\ge1$. This does not say that every covered system or atom attains that coefficient.

### Net lower coefficient

Use the fixed two-source system from the exact signed-residual witness. Keep $S_2$ constant and,
for $0<\eta<1$ and $R=1-\eta$, define the displayed $(S_1,T)$ cells by

$$
p(0,0)=\eta,\qquad p(1,2)=p(2,1)=R/2,
$$

$$
q(1,1)=\eta,\qquad q(1,2)=q(2,1)=R/2.
$$

The bottom net cumulative is zero, so the unique-$S_1$ net atom is $I(S_1;T)$. Exact evaluation
gives

$$
I_p(S_1;T)
=
-\eta\log\eta-R\log\frac{R}{2},
$$

$$
I_q(S_1;T)
=
\eta\log\frac{4\eta}{(1+\eta)^2}
+
R\log\frac{2}{1+\eta}.
$$

Hence

$$
\begin{aligned}
\left|
\Pi_{U_1}^{\mathrm{net}}(p)
-
\Pi_{U_1}^{\mathrm{net}}(q)
\right|
&=
2\eta\log\frac{1+\eta}{2\eta}
\\
&\quad+
(1-\eta)\log\frac{1+\eta}{1-\eta},
\end{aligned}
\tag{V3.2}
$$

and both terms are positive. Therefore

$$
\lim_{\eta\downarrow0}
\frac{
\left|
\Pi_{U_1}^{\mathrm{net}}(p)
-
\Pi_{U_1}^{\mathrm{net}}(q)
\right|
}{
\eta\log(1/\eta)
}
=2.
\tag{V3.3}
$$

This is a fixed-system, fixed-atom witness. For a family of net-atom bounds

$$
c\,\eta\log(1/\eta)+O_{\mathcal F}(\eta)
$$

with a common leading coefficient and system-dependent lower-order constant, the witness forces
$c\ge2$. This does not say that every covered system or atom attains that coefficient.

## Exact scope of optimality

Equations (V3.1)--(V3.3) prove leading-order optimality only. They do not establish:

- globally sharp $O(\eta)$ constants;
- globally sharp branch or Möbius terms;
- equality for every cumulative or atom;
- a single law pair that simultaneously saturates every bound;
- attainment by every covered system or atom;
- a pointwise support-boundary theorem;
- an alphabet-independent modulus;
- a binary64 error enclosure; or
- estimator or consumer validity.

The upper theorem fixes its finite alphabet, event system, and lattice. The new lower witnesses
constrain the common leading coefficient in a family of such fixed-system bounds; the
$O_{\mathcal F}(\eta)$ remainder may remain system-dependent. This is not an alphabet-independent
modulus, which the retained counterexample rejects. The witnesses do not compare or define another
PID measure.

## Closure evidence

The analytic derivation is in
[`../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md`](../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md),
Section 9.6. The matching standalone LaTeX source and PDF contain the same proposition.

The exact law families and the residual obstruction are retained in
[`failures/exact-counterexamples.md`](failures/exact-counterexamples.md). The
implementation-separated generator and bounded Rust replay include fixed empirical instances of
the same systems. Their decimal comparisons are not the proof of the limits.

The limits follow symbolically from the displayed exact formulas. The Lean artifact does not
currently formalize Equations (V3.1)--(V3.3). This boundary must remain explicit.
