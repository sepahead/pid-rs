# Independent interval-containment route memo

## Route record

- **Claim:** SX-CERTIFIED-AVERAGED-PID2-001 revision 1
- **Route:** exact-integer fixed-point rational logarithm and subset containment
- **Date:** 2026-07-24
- **Implementation:** `audit/tools/certified-sxpid/scripts/verify_certificate.py`
- **Disposition:** analytically supported and executably replayed; verifier not formally verified

## Why a second arithmetic route is needed

The Rust producer uses exact Rug rationals and MPFR directed rounding. Its analytic proof is
conditional on Rug, MPFR, GMP, the compiler, native ABI, and correct wrapper compilation.

The independent route treats the producer interval as an untrusted claim. It uses Python standard
library integers and `Fraction`, reconstructs the exact expression, and obtains a separate
enclosure without Rug, MPFR, GMP, NumPy, SymPy, Decimal, or `pid-core`.

## Logarithm derivation

For $x>0$, choose $e=\lfloor\log_2x\rfloor$ and exact rational $y=x2^{-e}$, so
$1\le y<2$. Let

$$
z=\frac{y-1}{y+1}.
$$

Then $0\le z\le1/3$ and

$$
\log x=e\log2+2\sum_{k=0}^{m-1}\frac{z^{2k+1}}{2k+1}+R_m.
$$

The geometric series converges uniformly on $[0,1/3]$, so termwise integration is valid there.
All integrated series terms are nonnegative. The omitted tail satisfies

$$
0\le R_m
\le
\frac{2z^{2m+1}}{(2m+1)(1-z^2)}
\le
\frac{9z^{2m+1}}{4(2m+1)}.
$$

The cached $\log 2$ interval is computed separately, without recursive range reduction, by the
same recurrence at $y=2$ and therefore $z=(2-1)/(2+1)=1/3$. Because
$2=(1+z)/(1-z)$ and the displayed tail bound includes $z=1/3$, this base case encloses
$\log 2$.

Exact floor and ceiling division at scale $2^b$ produce integer-unit lower and upper bounds.
Negative exact coefficients swap the contribution endpoints before finite-sum accumulation.

## Acceptance relation

Let $J_j=[\ell_j,u_j]$ be the independent rational enclosure and
$I_j=[L_j,U_j]$ the producer's normalized dyadic interval. The verifier accepts coordinate $j$
only when

$$
L_j\le\ell_j\le u_j\le U_j.
$$

Therefore, under the verifier premises,

$$
F_j\in J_j\subseteq I_j.
$$

This subset relation is the proof step. A small approximate error or interval overlap is not a
substitute.

## Qualification replay

The route:

- checked range reduction for every rational numerator/denominator pair in $1,\ldots,96$;
- checked $\log(1/2)=-\log2$ and $\log8=3\log2$ at 64, 128, and 256 bits;
- checked 975 containments of the fixed-point logarithm interval around an independently computed
  exact-`Fraction` partial-sum and rational-tail enclosure;
- proved all 24 containments for three live producer certificates;
- rejected a false zero interval;
- rejected a certified-positive interval collapsed to its own reported lower endpoint, which
  isolates the containment predicate from coarse structural checks;
- rejected a self-consistently forged expression;
- rejected false sign, width, precision, and dyadic evidence; and
- rejected resource-amplifying or noncanonical endpoints;
- rejected a retained one-sided fixed-point source mutation on the exact-rational qualification
  grid, without claiming that another evidence route would accept it;
- rejected four cross-artifact source/dependency binding adversaries;
- rejected six structural adversaries for their intended reasons;
- passed a symlinked-source invocation and a closed-stdout transport control; and
- produced byte-identical CLI output under the two retained Python hash seeds.

The 72 live containments demonstrate the route on nontrivial cases. The analytic series argument,
not the sample count, is what supports the general conditional implication.

## Trust boundary

The containment route still trusts:

- this verifier source;
- Python integer and `Fraction` semantics;
- the Python interpreter and operating system;
- JSON and SHA-256 implementations;
- the exact fixed-point rounding implementation;
- the reviewed tail-bound proof; and
- that the executed source matches the recorded digest.

It does not trust:

- producer exact-term lists;
- producer matrices;
- producer sign labels;
- the correctness of producer interval-endpoint generation—the parsed endpoint values still
  define $I_j$;
- Rug, MPFR, GMP, or Rust arithmetic; or
- the producer compiler or executable

for the mathematical containment inference.

## Open formal-method route

A stronger path would:

1. define the accepted byte grammar, its normalization, and exact SxPID2 expressions in Lean or
   Rocq;
2. prove the atanh-series tail bound and fixed-point routines;
3. extract or verify a small checker;
4. prove accepted checker output implies all 24 containments; and
5. validate the proof artifact with an independently pinned kernel.

That path is open and must not be implied by the current word “verified” in the JSON status.
