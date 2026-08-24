# Retained empirical-count weighting failure

## Exact witness

Use binary cell order $8s_1+4s_2+2s_3+t$ and

```text
c[0] = 2, c[4] = 1, all other counts = 0.
```

At key `03`, the two supported $S_1,S_2$ states have event masses two and one. With total
$N=3$, the paper-defined empirical-law average uses row probabilities $2/3$ and $1/3$:

$$
\begin{aligned}
C^+_{03}
&=\frac23\ln\frac32+\frac13\ln3\\
&=\frac13\ln\frac{27}{4}.
\end{aligned}
$$

Equivalently, the count-cleared exact product is

$$
Q^+_{03}=\left(\frac32\right)^2 3=\frac{27}{4}.
$$

The mutant that weights the two distinct support keys uniformly gives

$$
\widetilde C^+_{03}
=\frac12\ln\frac32+\frac12\ln3
=\frac12\ln\frac92.
$$

The values differ exactly:

$$
\widetilde C^+_{03}-C^+_{03}
=\frac16\ln2>0.
$$

The target is constant, so the same distinction occurs in the misinformative component while the
net cancels. A net-only test again fails to detect the wrong averaging law.

## Scientific boundary

Uniform weighting over supported realizations is not an alternative numerical approximation to
the same empirical functional. It changes the probability law. Replicating every count by the same
positive integer must preserve the averaged result; replacing counts by one does not.

## Regression requirement

The bounded corpus must include nonprimitive count vectors and check both:

- common replication $c\mapsto kc$ leaves all averaged coordinates invariant; and
- unequal counts are retained in every event product exponent and in the $1/N$ average.

Calling the 20,348 bounded count vectors “20,348 distinct laws” would hide this distinction; only
20,164 are primitive rational laws after gcd reduction.
