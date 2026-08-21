# Retained event-connective and target mutations

## Scope

These are exact counterexamples to three plausible implementation mutations. They support the
Makkeh--Gutknecht--Wibral event firewall; they are not counterexamples to the paper-defined
functional.

Binary cells are indexed as $8s_1+4s_2+2s_3+t$.

## OR across branches must not become AND

Take

```text
c[0] = 1, c[4] = 1, all other counts = 0.
```

The supported states are $(0,0,0,0)$ and $(0,1,0,0)$. At antichain key `01+02`,
$\alpha=(1,2)$, the correct event is $E_1\cup E_2$. The two rows share $S_1=0$, so the
correct event mass is two at both keys:

$$
Q^+_{\alpha}=1,\qquad Q^-_{\alpha}=1,\qquad C^+_\alpha=C^-_\alpha=0.
$$

The mutant $E_1\cap E_2$ keeps only the keyed row. It instead gives

$$
\widetilde Q^+_{\alpha}=2^2=4,
\qquad
\widetilde Q^-_{\alpha}=2^2=4,
\qquad
\widetilde C^+_\alpha=\widetilde C^-_\alpha=\ln2.
$$

The net happens to remain zero because the target is constant. Therefore a net-only test would
miss this semantic error; informative and misinformative coordinates are mandatory.

## AND within one mask must not become OR

Use the same count table at singleton antichain key `03`, whose only branch constrains
$\{S_1,S_2\}$.

The correct within-mask conjunction distinguishes the two rows:

$$
Q^+_{03}=Q^-_{03}=4.
$$

The mutant “match $S_1$ or $S_2$” includes both rows because $S_1$ agrees:

$$
\widetilde Q^+_{03}=\widetilde Q^-_{03}=1.
$$

This witness separates the connective inside a source collection from the disjunction between
antichain collections.

## The target intersection must not be omitted

Take

```text
c[0] = 1, c[1] = 1, all other counts = 0.
```

The two rows have identical sources and opposite target values. At key `07`, the correct source
event has mass $U=2$, each target mass is $T_z=1$, and the target-restricted event mass is
$V=1$. Hence

$$
Q^+_{07}=Q^-_{07}=Q^{\mathrm{sx}}_{07}=1.
$$

If a verifier omits $T(z)$ and substitutes $V=U=2$, then

$$
\widetilde Q^-_{07}=(1/2)^2=1/4,
\qquad
\widetilde Q^{\mathrm{sx}}_{07}=4.
$$

It reports a spurious net value $\ln2$ nats and a negative “misinformative” cumulative. The
target intersection is therefore load-bearing rather than a redundant filter.

## Regression requirement

A semantic checker must reconstruct these products from the raw count table and reject each mutant
formula. Hard-coding the expected products without checking the mutated event path is not a valid
mutation test.
