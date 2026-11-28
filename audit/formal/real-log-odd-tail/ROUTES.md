# Real logarithm remainder for the finite categorical count calculation

**Sepehr Mahmoudian · 2026**

The certificate for integer count tables evaluates positive rational products with natural logarithms. The finite sum and the final signed division already have separate checked integer models. This study asks whether stock Lean can check a real upper bound that is sharper than the published library bound. The real statement has no data rows. A later comparison with count tables must supply its own hypotheses and correspondence.

For a nonnegative integer $n$ and a real number $x$ with $0\leq x<1$, let $H_n(x)$ be half the natural logarithm of $(1+x)/(1-x)$ minus the sum of $x^{2i+1}/(2i+1)$ over all integers $0\leq i<n$. Define $U_n(x)=x^{2n+1}/((2n+1)(1-x^2))$. The question is whether $0\leq H_n(x)\leq U_n(x)$ and both inequalities are strict when $x>0$. At zero both endpoints and the error vanish. The sum is empty when $n=0$. Multiply by two to recover the full logarithm. All bounds are dimensionless. Natural logarithms give information in nats.

The odd power series is classical. The contribution sought is an exact formal statement for the stated error and a checked account of the transfer still needed for this calculation. No claim of mathematical priority is made. [NIST Digital Library of Mathematical Functions, equation 4.38.5](https://dlmf.nist.gov/4.38.E5) · [Mathlib derivative and existing bounds](https://github.com/leanprover-community/mathlib4/blob/d13f23b723b8a846827a245b89c10fc7d3f11612/Mathlib/Analysis/SpecialFunctions/Log/Deriv.lean#L261-L347)

The registered memo preserves the original text. In its route table, lines 21 and 22 have broken mathematical delimiters. Line 24 of the later selected edition retained the error in the denominator-cleared expression. The derivative below gives the corrected grouping. [Registered memo](history/original-route-register.md.txt#L21-L22) · [Selected edition before correction](history/selected-routes-before-notation-2026-11-28.md.txt#L24) · [Corrected derivative](#derivative-after-clearing-the-denominator)

## What could establish this statement

| Route | Premises and evidence needed | Failure condition and disposition |
|---|---|---|
| Keep the written integral proof | The integrand is continuous up to each fixed endpoint below one. | It gives an analytic argument. It does not supply a Lean declaration. Retain it in the publications. |
| Apply the two existing library inequalities | Use the precise half-log convention and the pinned real domain. | The upper bound omits the divisor $2n+1$. For $x>0$ the upper amounts coincide only at $n=0$. For $x=0$ they both vanish. Keep as the simpler comparator. |
| Use Shannon mutual information or direct task loss | A physical application must define its source variables, target, distribution and utility. | These quantities cannot bound the truncation error of the real logarithm. Use direct interval containment for the downstream arithmetic question. |
| Use rational evaluations or quadrature | Give inputs, precision, rounding and interval enclosure. | Sampling does not cover all real arguments. Use exact rational controls for signs and normalization. |
| Compare the infinite tail term by term with a geometric series | Prove the odd-power expansion for $\lvert x\rvert<1$, convergence, positivity and a strict comparison for a positive term after the first. | This is a direct paper proof. It needs more series machinery in Lean. Reopen it if the calculus route fails. |
| Use the high-order remainder in Taylor's theorem | Derivatives through order $2n+1$ must have a uniform bound on the interval. | A coarse derivative estimate can lose the divisor. Require the stated exact bound before adoption. |
| Integrate the derivative of the finite remainder | Establish its derivative on the entire interval and replace the reciprocal by its largest value there. | Correct on the closed interval below one. A strict inequality needs a genuine interval on which the integrand is smaller. |
| Differentiate the upper envelope with the endpoint held fixed | For $0<y<x<1$ compare positive denominators $1-y^2$ and $1-x^2$. | Works for each fixed $x$. It needs a separate ordering step and a treatment of $x=0$. |
| Differentiate the moving upper envelope | Prove the derivative of $U_n(y)-H_n(y)$ equals $2y^{2n+2}/((2n+1)(1-y^2)^2)$. | Division is legitimate below one. It permits a direct monotonicity argument, with more quotient algebra. |
| Multiply through by the positive denominator before differentiating | Prove $H_n(y)>0$ when $0<y<1$ using the lower sum with one more term. Then differentiate $F_n(y)$ as defined below. | Its derivative simplifies to $2yH_n(y)$. Positive sign on the open interval gives strictness. Check all casts, the empty sum and endpoint separately. Selected for the first attempt. |
| Induct backwards from a shifted finite sum and take a limit | A uniform bound on the shifted remainder must tend to zero and the intervening finite inequalities must hold. | It avoids differentiating the envelope but adds a limit. Reserve it when the derivative correspondence is unavailable. |
| Return only the bound on the seven attained precision cases | Establish the factor for specific arguments and the exact integer schedule. | This is a separate finite predicate and could support the specified reader. It leaves the declared universal statement open. |

The two stock library observations, the proposed stronger theorem, the integer proofs, the finite execution and the finite categorical application of Makkeh, Gutknecht and Wibral have different subjects. The easier library result took about 2.884 billion bytes of sampled group memory under a fresh checker on Linux. No local machine import is part of this plan. The existing source remains pinned to Mathlib revision d13f23b723b8a846827a245b89c10fc7d3f11612 and Lean 4.34.1. The underlying functional is the finite categorical shared-exclusions construction of Makkeh, Gutknecht and Wibral. The analytic remainder applies to positive numbers independently of the choice of a PID. [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149)

## Integral proof

Fix a nonnegative integer $n$ and an endpoint $0\leq x<1$. Let $y$ range from zero to $x$. Differentiate the finite sum in the definition of $H_n$. The finite geometric sum then gives

$$
H_n'(y)=\frac{1}{1-y^2}-\sum_{i=0}^{n-1}y^{2i}
       =\frac{y^{2n}}{1-y^2}.
$$

For $n=0$ the sum is empty and the numerator is the constant one. At zero the right derivative is one for $n=0$ and zero for $n>0$. Since $H_n(0)=0$, integration gives

$$
H_n(x)=\int_0^x\frac{y^{2n}}{1-y^2}\,dy .
$$

For $0<y<x$, the integrand is positive and $1/(1-y^2)<1/(1-x^2)$. Holding the latter factor fixed and integrating $y^{2n}$ gives $0<H_n(x)<U_n(x)$ whenever $0<x<1$. At $x=0$ both sides are zero. [Worked bound for the full logarithm on the certificate interval](../../research/signed-log-certificate-enclosure/EXPOSITION.md#the-error-after-the-last-term)

## Geometric series proof

For $0<x<1$, the convergent odd-power expansion of the half-logarithm gives a positive remainder starting at $i=n$. Replace each denominator $2i+1$ by $2n+1$. The first term stays equal, and the term with $i=n+1$ strictly increases. Summing the resulting geometric series gives

$$
0<H_n(x)=\sum_{i=n}^{\infty}\frac{x^{2i+1}}{2i+1}
 <\frac{x^{2n+1}}{2n+1}\sum_{j=0}^{\infty}x^{2j}=U_n(x).
$$

The geometric ratio is $x^2<1$. At zero every term vanishes. The full logarithm and its error equal twice the half-logarithm and its error. [NIST DLMF, equation 4.6.4](https://dlmf.nist.gov/4.6.E4)

## Derivative after clearing the denominator

For the route selected in the first formal attempt, define the difference after multiplication by the positive factor $1-y^2$,

$$
F_n(y)=\frac{y^{2n+1}}{2n+1}-(1-y^2)H_n(y).
$$

The product rule and the derivative in the integral proof give

$$
F_n'(y)=y^{2n}+2yH_n(y)-(1-y^2)H_n'(y)=2yH_n(y).
$$

At zero $F_n(0)=F_n'(0)=0$, including for $n=0$. The derivative is positive for $0<y<1$ because $H_n(y)>0$. Thus $F_n(x)>0$ there. Division by $1-x^2$ recovers the strict upper bound. Differentiating the unscaled difference directly also works,

$$
\frac{d}{dy}\bigl(U_n(y)-H_n(y)\bigr)
 =\frac{2y^{2n+2}}{(2n+1)(1-y^2)^2}.
$$

Both differences vanish at zero. The four formal submissions have their original outcomes. [Original proof attempts](HOSTED-RESULTS.md) · [Two checked Mathlib inequalities](../real-log-library-read/HOSTED-RESULTS.md)

## Scope of critical review

The author examined the domain of the logarithm, positivity of its argument, the factor one half, the outer factor of two, the empty sum, the exact index origin, the last included summand, the first omitted power, the first omitted divisor, casts from natural numbers, exact real division, the closed endpoint at zero, the excluded pole at one, odd parity, use of a positive denominator, the monotonicity direction, strictness on the interior, strictness versus equality at zero, differentiability, continuity at each endpoint, the domain of the derivative formula, the power rule for $n=0$, the positive one-more-term comparison, algebra after clearing denominators, the applicability of the mean-value theorem, and a concrete case with $x=1/2$. The analysis also covers law normalization, units, PMF support, finite categories, row multiplicities, zero weights, joint support, the rational-to-real map, signed exponents, outward integer rounding, the precision schedule, grid units, strict versus non-strict output tests, and the distinction among different PIDs. The execution review covers theorem name, exact elaborated statement, proof type, compiled dependency identity, downloaded cache trust, stock tool hashes, source integrity, transitive axioms, fresh proof replay, proof payload ownership, independent judge ownership, false controls, time and memory ceilings, missing runner outcomes, provider object readback, earlier rejection retention and the limits of model review. Each check has the specific source or test described in the contract. Counting checks does not validate the result.

Cite Sepehr Mahmoudian, *Real logarithm remainder for the finite categorical count calculation* (2026), with the exact pid-rs commit or release. [Software citation](../../../CITATION.cff)
