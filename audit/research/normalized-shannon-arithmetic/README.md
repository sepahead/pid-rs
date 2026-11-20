# Rounding the average degrees of redundancy and vulnerability

**Sepehr Mahmoudian · 20 November 2026**

Can arithmetic alone change the reported average degree when its input values are already exact? For three nonnegative marginal inputs, the earlier Rust code returned the floating-point number immediately above the nearest representation of three tenths. A second example gives the correct ratio but loses one step in its separately reported numerator. Each example uses mutually consistent information values from one finite probability distribution.

## What the two degrees measure

**Terms and symbols.** The target $T$ and the $m$ sources $S_1,\ldots,S_m$ take finitely many values and have one joint distribution. Write $S$ for the tuple of all sources and $S_{-i}$ for the tuple after deleting source $i$. Entropy measures uncertainty. Mutual information $I$ measures the average reduction in target uncertainty supplied by another variable. Its unit is the **nat** when logarithms are natural. Let $J$ denote the information supplied by all sources, $a_i$ the information from source $i$ alone and $b_i$ the information from all sources except $i$. **Binary64** is the 64-bit floating-point format. **Rounding to nearest** selects the closest representable value. On a tie, the last retained binary digit is chosen to be even. [Gutknecht et al., 2025, version 1](https://arxiv.org/html/2504.15779v1#S2.E6) · [IEEE Standard for Floating-Point Arithmetic](https://standards.ieee.org/ieee/754/6210/)

For $m\ge1$ and $J=I(T;S)>0$, set $a_i=I(T;S_i)$ and $b_i=I(T;S_{-i})$. The dimensionless average degrees of redundancy and vulnerability are

$$
\bar r=\frac{\sum_{i=1}^{m}a_i}{J},
\qquad
\bar v=\frac{\sum_{i=1}^{m}(J-b_i)}{J}.
$$

Redundancy sums single-source contributions relative to the joint information. Vulnerability sums the relative losses when each source in turn is removed. The chain rule gives $J-b_i=I(T;S_i\mid S_{-i})$. Each summand in either numerator lies between zero and $J$, so each degree lies in $[0,m]$. Computing either degree requires only mutual information, with no choice of a decomposition into information atoms. Gutknecht and colleagues named them *Shannon invariants* in version 1, Propositions 1–2, Eqs. (6) and (10). Their revision, *Shannon observables*, gives them in Eqs. (2)–(3), (13) and (17). [Version 1, vulnerability](https://arxiv.org/html/2504.15779v1#S2.E10) · [Version 2, definitions](https://arxiv.org/html/2504.15779v2#S2.E2) · [Version 2, derivation](https://arxiv.org/html/2504.15779v2#S4.E13)

The inequalities also hold for an empirical distribution when every quantity uses the same table of relative frequencies and exact arithmetic. Rounding every exact input to nearest preserves their order, though the ratios can change or the denominator can round to zero. Separately fitted estimates and inconsistent units can violate the bounds. A common positive scale factor cancels in exact arithmetic. A fixed numerical denominator threshold still depends on the scale.

---

## Two finite-distribution examples

**Redundancy.** Suppose the three marginal informations are each $1/16$ nat and the joint information is $10/16$ nat. Their exact sum is $3/16$ nat and the ratio is $3/10$. The earlier code divided by the common marginal scale, summed three ones, and multiplied by the rounded scale ratio. In binary64 the two orders produce adjacent values.

| Evaluation | Binary64 bits in hexadecimal |
|---|---|
| Round the product of three and the rounded value of $1/10$ | `3fd3333333333334` |
| Round the exact $3/10$ directly | `3fd3333333333333` |

The nearest binary64 value to $1/10$ is $3602879701896397/2^{55}$. Three times that value lies exactly halfway between the two listed encodings. The upper encoding ends in an even bit and wins the tie. The exact $3/10$ lies closer to the lower encoding.

To realize the inputs, use independent binary variables $C,K$ with entropies $1/16$ and $9/16$ nats. Binary entropy varies continuously from zero to $\ln 2$, so both choices exist. Set $T=(C,K)$. Take independent fair bits $U,V$, also independent of $T$. The sources are $(C,U)$, $(C,V)$ and $(C,U\mathbin{\oplus}V\mathbin{\oplus}K)$, where $\oplus$ is addition modulo two. Each source reveals $C$ and alone reveals nothing about $K$. Together they recover both. This proves existence of a finite distribution with the stated informations.

**Vulnerability.** Now take $J=49/64$ nat and the two leave-one-out informations $49/64,48/64$ nats. The original-unit numerator is $1/64$ nat and the ratio is $1/49$. The earlier code obtained the nearest representation of $1/49$, then multiplied that rounded value by $J$ to reconstruct the numerator. Because $2^{58}\bmod 49=23$, the exact product of those represented operands is $2^{-6}-23\cdot2^{-64}$. It is below the midpoint $2^{-6}-2^{-60}$ to the predecessor of $2^{-6}$. The earlier numerator therefore had bits `3f8fffffffffffff`. Rounding $1/64$ directly gives `3f90000000000000`.

For a realization, choose independent $C,K$ with entropies $48/64$ and $1/64$ nats. A three-valued $C$ suffices because $48/64<\ln 3$. A binary $K$ suffices because $1/64<\ln 2$. Take $T=(C,K)$, $S_1=C$ and $S_2=(C,K)$. Deleting the first source leaves all of $T$. Deleting the second leaves $C$. The example explains why the ratio and numerator each need their own rounding operation. [Earlier implementation](https://github.com/sepahead/pid-rs/blob/0f3122a96e48a099581ad4faf3e3d5d9138367f6/crates/pid-core/src/invariants.rs) · [Corrected report](https://github.com/sepahead/pid-rs/blob/03325745f64becf437b9b3042b51a9d925450579/crates/pid-core/src/invariants.rs)

**Why exact sample counts cannot realize these values.** For a table of $N$ observations of $(X,T)$, let $n_{xt}$ count the rows with $X=x,T=t$, and let $n_x,n_t$ be the corresponding marginal counts. The empirical mutual information $I=I(X;T)$ in nats satisfies

$$
e^{NI}=\prod_{n_{xt}>0}\left(\frac{N n_{xt}}{n_x n_t}\right)^{n_{xt}}.
$$

The product is rational. If $I=a/b$ for positive integers $a,b$, raising the product to the power $b$ would give $e^{Na}$. Every positive integer power of $e$ is irrational. Thus neither example's positive rational mutual information values in nats can occur exactly in a finite count table. The constructed finite probability distributions realize them. [Hermite, *Sur la fonction exponentielle* (1873), §III](https://doi.org/10.3931/e-rara-101019)

Because finite count distributions are dense and mutual information is continuous on a fixed finite alphabet, one count table per example can reproduce all its once-rounded inputs simultaneously whenever each exact input lies strictly between its two rounding midpoints, as it does here.

---

## Rust implementation and computational cost

The stable public entry points in `pid_core::diagnostics` are `average_degree_of_redundancy` and `average_degree_of_vulnerability`. Each has a `_with_policy` variant. They require no optional Cargo feature. Redundancy takes the marginal slice first and the joint value second. Vulnerability takes the joint value first and the leave-one-out slice second. The report returns a dimensionless ratio, an optional numerator in nats, the supplied finite denominator in nats, the definition, units, status and policy. These functions perform no sampling, information estimation, training or resampling. [Public Rust functions](https://github.com/sepahead/pid-rs/blob/03325745f64becf437b9b3042b51a9d925450579/crates/pid-core/src/invariants.rs)

**Exact sum.** Write $u=2^{-1074}$, the smallest positive binary64 value. Every finite binary64 number is an integer multiple of $u$. The code adds these integer magnitudes into separate positive and negative arrays of 64-bit words. Redundancy supplies $m$ terms. Vulnerability supplies $J$ and the exact sign reversal of $b_i$ for each source, using $2m$ terms. Subtracting the two arrays gives the sign and an absolute integer $A$. The numerator is rounded directly from $+Au$ or $-Au$, according to its sign.

**Exact division before rounding.** Write the positive denominator as $d2^s u$, where $d$ is a positive integer smaller than $2^{53}$ and $s$ is an integer from zero through 2,045. For $A>0$, integer long division of $A2^{128}$ by $d$ gives quotient $Q$ and remainder $0\le r<d$. The magnitude of the exact ratio is

$$
\frac{A}{d2^s}=\left(Q+\frac{r}{d}\right)2^{-(s+128)}.
$$

The 128 extra low bits ensure $Q\ge2^{75}$, leaving room below the 53 significant bits. The first discarded bit is the guard bit. The sticky bit records whether any lower bit or the remainder is nonzero. The rounder increments the retained integer exactly when the guard bit is one and either the sticky bit is one or the retained integer is odd. For tiny results the spacing is at least $u$. Exact cancellation yields positive zero. A nonzero negative ratio may round to negative zero. [Integer division and rounding](https://github.com/sepahead/pid-rs/blob/03325745f64becf437b9b3042b51a9d925450579/crates/pid-core/src/exact_binary64.rs)

Let $L=\lceil(2098+w)/64\rceil$ words, where $w$ is the bit width of Rust's `usize`. One finite input uses at most 2,098 magnitude bits in units of $u$, and at most $2^w-1$ such terms need at most $w$ extra bits. The worst-case time is $O(mL)$ and auxiliary storage is $O(L)$, independent of sample size or alphabet. On a 64-bit target, $L=34$. Division uses a quotient array of $L+2$ words and takes one pass over it. The slice scan has no cancellation hook or caller-set budget. No runtime benchmark is reported.

---

## What the hosted comparison measured

A fixed set of 184 public Rust calls covered both methods, both default and explicit denominator policies, cancellation, underflow, ties and overflow. For each call the reference decoded the supplied binary64 inputs into exact rational numbers. It compared every field, including the bit patterns of available numbers. The reference rounded the exact ratio and exact numerator separately. Two reference routines agreed on the rounding of each value. One converted a rational number directly. The other searched the ordered binary64 values and compared the neighboring distances. They shared the inputs and the report specification. [Fixture and checker](../normalized-shannon-ratios/README.md)

| Comparison against exact expectations | Earlier code | Corrected code |
|---|---:|---:|
| Reports with a discrepancy, out of 184 | 41 | 0 |
| Different ratio field | 41 | 0 |
| Different status field | 13 | 0 |
| Different numerator field | 13 | 0 |
| Existing invariants tests passed, out of 16 | 16 | 16 |

Field counts overlap. A difference includes an absent field when a number was expected. Both hosted runs produced identical observations of the earlier code. The corrected run used Rust 1.99.1 on x86-64 Linux. An earlier observation harness failed to compile with Rust error E0277 while formatting a fixture digest and produced no observations. [Earlier run 44640265708](https://github.com/sepahead/pid-rs/actions/runs/44640265708) · [Corrected run 44640966503](https://github.com/sepahead/pid-rs/actions/runs/44640966503)

**Boundary cases.** For marginals $u,u$ and $J=2$, the exact ratio is $u$. Rounding each $u/2$ too early gives zero. For the largest finite binary64 value $M$, two inputs $M,M$ and $J=M$ give ratio 2, while the original-unit numerator overflows and is absent. Empty terms, nonfinite inputs, a nonpositive denominator, a denominator at or below the policy floor and an unrepresentable final ratio have separate statuses. The default floor is $10^{-12}$ nats. [Exact expected reports](../../../crates/pid-core/tests/fixtures/normalized_shannon_ratio.json)

The two ordinary examples are worked calculations outside the 184 calls. The table counts only the fixed Rust calls. Model assistance contributed to the implementation, examples and checks. The source argument and finite executions supply distinct evidence. They establish neither a kernel-checked implementation proof nor independent human review. Upstream estimation error and scientific use require their own analysis.

---

## What happens when the target is the complete source tuple?

Let $S=(S_1,\ldots,S_m)$ have a finite alphabet and positive entropy $H(S)$. If $T=S$, the joint mutual information is $H(S)$. Each single-source term is $I(S;S_i)=H(S_i)$, and each loss on removal is $I(S;S_i\mid S_{-i})=H(S_i\mid S_{-i})$. Substitution into the published formulas gives exactly the two source-only ratios, $\sum_i H(S_i)/H(S)$ and $\sum_i H(S_i\mid S_{-i})/H(S)$. This is an exact-arithmetic identity for this choice of target. The source-only Rust functions compute entropies from categorical rows. The target-based functions take mutual information values and apply a numerical denominator threshold. The three mutual information fields and the co-information field of the experimental two-source Python wrapper use nats, and its two degree fields are dimensionless. [Target-based definitions](https://arxiv.org/abs/2504.15779v1) · [Source-only formulas](../../../crates/pid-core/src/invariants.rs) · [Python binding](../../../crates/pid-python/src/lib.rs)

### Can rounding stop a convergent denominator from passing the threshold?

Yes. Let $c$ be the stored binary64 value of the default threshold, written as the decimal literal 1.0e-12 in Rust. Write $c_+$ for the next larger binary64 value. Their spacing is $2^{-92}$ nats. Pick the exact population mutual information

$$
J=c+\tfrac14(c_+-c).
$$

This value lies strictly above $c$ and below $(c+c_+)/2$. A binary source and a target that copies it can have this information. Binary entropy varies continuously from zero to $\ln 2$, and $J$ lies inside that range. Under independent, identically distributed sampling, the empirical frequency converges almost surely to the source probability. Its entropy, which is the empirical mutual information for this copy, consequently converges to $J$.

With probability one, every sufficiently late exact empirical value lies between $c$ and the midpoint. It passes the exact-real threshold. Rounding that same value once to nearest binary64 gives $c$, which the report rejects at equality. For a finite threshold with a finite successor, a limiting $J$ strictly above the upper midpoint guarantees eventual passage of this denominator comparison under the same convergence and single-rounding assumptions. When the limit is the midpoint, empirical values may approach it from either side. The midpoint is a positive dyadic rational, so the count-table identity above rules out an exact tie for empirical mutual information in nats. A general real estimate converted to binary64 can equal a midpoint, where the tie rule applies. Other input, estimator and quotient checks retain their own conditions. This worked example concerns the reporting rule and was developed separately from the 184 recorded calls. [Finite-alphabet convergence and assumptions](../../../FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) · [IEEE rounding rule](https://standards.ieee.org/ieee/754/6210/)

Cite Sepehr Mahmoudian (2026), *Rounding the average degrees of redundancy and vulnerability*, with the exact repository commit or release. Cite Gutknecht and colleagues for the definitions. [Software citation](../../../CITATION.cff) · [Print edition](../../../output/pdf/normalized-shannon-arithmetic.pdf) · [Print builder](build_pdf.py)
