# Retained negative signed-net atom

## Exact witness

Use binary cell order $8s_1+4s_2+2s_3+t$ and

```text
c[11] = 1, c[13] = 1, c[14] = 1,
all other counts = 0.
```

At antichain key `02+04`, $\alpha=(2,4)=\{\{S_2\},\{S_3\}\}$, exact reconstruction gives

$$
R^+_{\alpha}=\frac94,
\qquad
R^-_{\alpha}=4,
\qquad
R^{\mathrm{sx}}_{\alpha}=\frac{9}{16}.
$$

For this table and node, the cumulative and atom products coincide. Therefore

$$
\Pi^+_{\alpha}=\frac13\ln\frac94>0,
\qquad
\Pi^-_{\alpha}=\frac13\ln4>0,
$$

while

$$
\Pi^{\mathrm{sx}}_{\alpha}
=\frac13\ln\frac{9}{16}
=\frac23\ln\frac34
<0.
$$

The sign follows by exact integer comparison $9<16$. No decimal or floating tolerance is
involved.

## What this refutes

This exact empirical Makkeh--Gutknecht--Wibral witness refutes each of:

- all averaged signed-net SxPID3 atoms are nonnegative;
- nonnegative informative and misinformative component atoms imply their difference is
  nonnegative;
- a negative atom is necessarily floating noise; and
- clamping a negative net atom preserves the decomposition.

It does not refute the paper's separate component-nonnegativity theorem. It is not evidence about
another PID definition or a continuous estimator.

## Regression requirement

The exact product lane must classify this coordinate negative, the interval must contain its exact
negative magnitude and lie consistently below zero, and every Rust/report path must preserve the
negative value. A clamp, absolute value, unsigned schema, or “negative means abstain” mutation must
fail.
