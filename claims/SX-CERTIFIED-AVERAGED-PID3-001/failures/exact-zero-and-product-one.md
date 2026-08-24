# Retained exact-zero and nonsyntactic-product-one failures

## Exact-zero binary64 residual

Use binary cell order $8s_1+4s_2+2s_3+t$ and

```text
c[11] = 1, c[13] = 1, c[15] = 1,
all other counts = 0.
```

At singleton antichain key `06`, mask $\{S_2,S_3\}$, the exact informative and
misinformative atom products are both $4/3$:

$$
R^+_{06}=R^-_{06}=\frac43,
\qquad
R^{\mathrm{sx}}_{06}=1,
\qquad
\Pi^{\mathrm{sx}}_{06}=0.
$$

The recursive binary64 mirror in the external audit produced

```text
informative     0x1.88c82c19bcf6dp-4
misinformative  0x1.88c82c19bcf70p-4
net            -0x1.8000000000000p-55
```

so component subtraction returned a nonzero negative residual for an exact zero. This is a
counterexample to binary64 exact-zero preservation for that evaluation path, not a counterexample
to the categorical functional and not yet a compiled-Rust refinement result.

## Nonempty expression whose product is one

Use

```text
c[4] = 1, c[5] = 1, c[8] = 1, c[9] = 4, c[12] = 1,
all other counts = 0.
```

The total is $N=8$. At atom key `01`, the Möbius row is

$$
\Pi_{01}=C_{01}-C_{01+06}.
$$

The exact cumulative products are

$$
\begin{aligned}
Q^+_{01}&=\frac{65536}{729},
&
Q^+_{01+06}&=\frac{65536}{2187},\\
Q^-_{01}&=\frac{84375}{1024},
&
Q^-_{01+06}&=\frac{28125}{1024}.
\end{aligned}
$$

Hence both atom products are nontrivial:

$$
R^+_{01}=3,
\qquad
R^-_{01}=3,
\qquad
R^{\mathrm{sx}}_{01}=1.
$$

The net log expression is nonempty before multiplicative normalization, yet the exact net atom is
zero. The recursive floating mirror returned `-0x1.0000000000000p-55`.

## What these witnesses refute

They refute:

- deciding exact zero from `f64 == 0.0`;
- treating any nonzero floating residual as a strict sign;
- recognizing exact zero only when the pre-normalized term list is empty;
- using an epsilon band as mathematical equality; and
- claiming that compensated summation supplies an exact product-one decision.

Arbitrarily small nonzero logarithmic values exist, so widening an epsilon until these witnesses
become zero creates false zeros elsewhere.

## Regression requirement

The verifier must normalize or compare the exact positive rational product with one. It must
classify both retained net atoms as exact zero, require their outward intervals to contain zero,
and retain their nonempty factor histories for mutation testing. A mutation to one factor,
exponent, event count, Möbius coefficient, or component label must cease to classify the affected
product as one.
