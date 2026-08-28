# Mathematical results guide

This guide gives junior readers a map of the principal mathematical results and assurance work in
pid-rs. Each result card identifies the mathematical object and its assumptions. Each card also
gives the central formula, evidence, cost, use, strongest nonclaim, and complete proof or
publication artifact.

> **Non-authoritative guide.** Scope-specific files govern each type of statement:
>
> - [`method-catalog.json`](method-catalog.json) governs method identity, provenance,
>   implementation status, and the public surface.
> - [`METHODS.md`](METHODS.md) and [`METHODS_SUMMARY.md`](METHODS_SUMMARY.md) provide generated views
>   of the catalog.
> - The linked active revision index and decision govern the claim lifecycle.
> - The detailed Markdown and PDF reports govern exact statements.
>
> If this guide conflicts with a scope-specific governing source, the governing source takes
> precedence.

The repository assigns authority by scope. The narrow SxPID3 factorization/bounded audit is an
integrated stable validation entry. The separate full SxPID3 certificate specification remains
proposed and unsupported. Neither status changes the other.

In this guide, “New in pid-rs” means repository implementation, rederivation, theorem composition,
counterexample, diagnostic, or assurance work. The phrase is **not** a scientific-priority claim.
All information quantities below use natural logarithms and are in **nats**. The MGW paper uses
bits. Multiplication by the positive factor $\log 2$ converts its values to nats without changing
signs or equalities.

## 1. Reading conventions and semantic firewall

### Evidence labels

| Label | Meaning | Boundary |
|---|---|---|
| **[P]** | Published definition or theorem | Does not prove the local transcription or code |
| **[R]** | Exact repository proof or rederivation | No scientific-priority, runtime, or statistical claim |
| **[X]** | Exact counterexample | Refutes only the stated stronger claim |
| **[B]** | Bounded exhaustive/finite-corpus result | No conclusion outside its declared domain |
| **[E]** | Executable observation/test | Not a proof of its specification or runtime |
| **[O]** | Open obligation or prohibited transfer | Does not negate a narrower accepted result |

A **functional** takes a probability law as its input. An **estimator** infers a functional from
samples. A PID **cumulative** belongs to a lattice node. Möbius inversion produces an **atom** from
the cumulatives.

Exact real, exact rational, and represented binary64 statements are different types of
statements. Formal and executable routes can share human statements or transcriptions. Therefore,
route counts do not imply independence.

### Five distinct lanes

| Lane | Object in this repository | Do not conflate it with |
|---|---|---|
| **Categorical MGW shared exclusions** | Finite-law event-logical PID of [Makkeh, Gutknecht, and Wibral (2021)](https://doi.org/10.1103/PhysRevE.103.032149), implemented for two to four sources | Ehrlich continuous Sx, Williams–Beer $I_{\min}$, or BROJA |
| **Continuous Ehrlich shared exclusions** | Distinct continuous functional/kNN estimator of [Ehrlich et al. (2024)](https://doi.org/10.1103/PhysRevE.110.014115). Experimental here | A categorical theorem or transparent quantization of the categorical theorem |
| **Williams–Beer $I_{\min}$** | Different categorical redundancy of [Williams and Beer (2010)](https://arxiv.org/abs/1004.2515) | Categorical Sx merely because both use an antichain carrier |
| **BROJA** | Bivariate finite-alphabet optimization-based PID proposal of [Bertschinger et al. (2014)](https://doi.org/10.3390/e16042161). Comparison boundary only here | Any accepted mapping from Sx or $I_{\min}$. The repository asserts no mapping |
| **KSG** | MI estimator of [Kraskov, Stögbauer, and Grassberger (2004)](https://doi.org/10.1103/PhysRevE.69.066138) | A PID definition or proof of a downstream continuous PID |

This guide therefore avoids the blanket phrase “Wibral PID.” The repository has no accepted result
for either of these ideas:

- A target-permutation affine-reflection theorem.
- A generic affine reconstruction across different PID definitions.

### Lattice positions versus audit coordinates

Categorical Sx has 4, 18, and 166 lattice positions for two, three, and four sources. Audit
registries expand each lattice by two stages (cumulative/atom) and three components
(informative/misinformative/net):

$$
24=4\times2\times3,
\qquad
108=18\times2\times3.
$$

Thus, SxPID3 has 18 net atoms. The count 108 is an audit-registry coordinate count. The count 166
belongs to SxPID4.

![The 108 audit expressions expand, rather than replace, the 18-position SxPID3 lattice.](audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg)

## 2. Result map

| Family | Status and evidence | Detailed source |
|---|---|---|
| 1. Foundational categorical-Sx audit | Stable validation.<br> Published object **[P]**. Repository audit **[R,X,B,E]**. Broad semantics open **[O]** | [`FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md`](FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md) · [PDF](output/pdf/foundational-shared-exclusions-pid-audit.pdf) |
| 2. Finite plug-in convergence | Stable validation.<br> Published limit tools **[P]**. Repository composition **[R,X,B,E]**. Floating/runtime bridge open **[O]** | [`FINITE_ALPHABET_PLUGIN_CONVERGENCE.md`](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) · [PDF](output/pdf/finite-alphabet-plugin-convergence.pdf) |
| 3. Support-change averaged-Sx continuity | Stable validation.<br> Theorem/counterexamples **[R,X]**. Bounded/formal subevidence **[B,E]**. Full refinement open **[O]** | [`SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md`](SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md) · [PDF](output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf) |
| 4. Dependency-color concentration | Stable validation.<br> Published inequalities **[P]**. Repository composition/Sx bounds **[R,X,B,E]**. Automatic coloring absent **[O]** | [`DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md) · [PDF](output/pdf/dependency-colored-sxpid-concentration.pdf) |
| 5. Exact SxPID2 assurance | Count-to-atom formal scope complete **[R]**.<br> Product-one counterexample **[X]**. Certifier conditional **[B,E]** with integration open **[O]** | [count-to-atom proof](audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md) · [exact-product report](audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md) · [certifier decision v3](claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md) |
| 6. SxPID3 factorization/audit | Integrated stable validation: method anchor **[P]**, factorization **[R]**, counterexamples **[X]**, bounded audit **[B,E]**, correspondence/certificate open **[O]** | [`SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md`](SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md) · [PDF](output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf) |
| 7. Binary64/quantizer assurance | Implemented measure-specific arithmetic/diagnostics **[R,B,E]**.<br> Bounded nonfindings and policy rejections **[B,E,O]**. No estimator or full refinement **[O]** | [`NUMERICAL_ASSURANCE.md`](NUMERICAL_ASSURANCE.md). Dedicated PDF absent |
| 8. KSG integer-harmonic arithmetic | Exact/formal/bounded core scoped GO **[P,R,X,B,E]**.<br> Repository/publication integration **NO-GO [O]** | [`claim-v4.md`](claims/KSG-INTEGER-HARMONIC-001/claim-v4.md) · [`integration-disposition-v4.md`](claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md) |

`stable` is a catalog family status. The status does not claim estimator consistency, calibration,
application validity, scientific novelty, or complete formal verification.

## 3. Categorical-Sx theory

### 3.1 Foundational semantic audit

**Scope and formula.** The formula uses a supported finite key $z=(s,t)$ and an antichain
$\alpha$. The symbol $p$ denotes the finite probability law. The symbol $A_\alpha(s)$ denotes the
MGW disjunction of matching source events. The cumulative components are:

$$
c_\alpha^+=-\log p(A_\alpha),\qquad
c_\alpha^-=\log\frac{p(T=t)}{p(T=t,A_\alpha)},\qquad
c_\alpha^{\mathrm{net}}=c_\alpha^+-c_\alpha^-.
$$

The symbols $c_\alpha^+$, $c_\alpha^-$, and $c_\alpha^{\mathrm{net}}$ denote informative,
misinformative, and net cumulative components, respectively.

The full-lattice atoms are the fixed finite Möbius inverse of these cumulatives. [Rota
(1964)](https://doi.org/10.1007/BF00531932) supplies the classical tool. pid-rs did not invent
Möbius inversion.

**Result and boundary.** The audit separates native Sx properties from imported desiderata. The
audit retains exact failures of these properties:

- Generic identity/local positivity.
- Source-target symmetry.
- Coarse-graining monotonicity.
- Pairwise identifiability.
- Descriptor substitution.

Published informative and misinformative component atoms are nonnegative on the stated full
lattice. The net difference may be negative.

Exact witnesses and a generic Lean descriptor-factorization lemma do not prove all laws, Rust
refinement, causality, or a unique interpretation. **[P,R,X,B,E,O]**

**Cost/use.** The result adds no new estimator. Sampled use requires the empirical full joint PMF.
Lattice/event cost grows sharply from 4 to 18 to 166 nodes.

In neural or sensor work, a negative signed atom does not by itself prove harm, suppression, or
common deterministic information. A separate domain theorem must support any such label.

**Read next.** [`FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md`](FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md)
and the corresponding [PDF](output/pdf/foundational-shared-exclusions-pid-audit.pdf). Catalog entry:
`validation.foundational-shared-exclusions-audit`.

### 3.2 Fixed finite-alphabet plug-in convergence

**Assumptions/result.** The result fixes a finite alphabet, a lattice, and a law $P$ with support
$S$. The sequence of laws $Q_n$ must satisfy both conditions:

- $Q_n(z)\to P(z)$ for every cell.
- $\mathrm{supp}(Q_n)\subseteq S$.

The supports of $Q_n$ eventually equal $S$. All supported-key categorical-Sx
cumulatives/atoms/averages then converge. Separate continuity arguments cover the listed
$I_{\min}$ and Shannon quantities without equating their definitions.

The premises hold almost surely in either of two cases:

- The rows are i.i.d. with marginal $P$.
- The rows are strictly stationary **ergodic** with marginal $P$.

Stationarity alone is insufficient. **[P,R,X]**

For i.i.d. rows on $K$ cells, $\alpha$ is a failure-probability budget with $0<\alpha<1$. A
Hoeffding/spending-sequence composition gives the following simultaneous bound for every prefix
$n$ with probability at least $1-\alpha$:

$$
\lVert\widehat P_n-P\rVert_1
\le B_n:=K\sqrt{\frac{\log(K\pi^2n^2/(3\alpha))}{2n}}.
$$

Here, $\widehat P_n$ is the empirical law of the first $n$ rows. The quantity $B_n$ is the
simultaneous $L^1$ radius.

A guaranteed support-entry time also needs a known population floor
$p_{\min}=\min_{z\in S}P(z)>0$. An empirical minimum cannot reveal an unseen rare cell.

The frozen-transform corollary uses the training sigma-field $\mathcal G$. The training artifact
and fitted transform generate $\mathcal G$. The corollary requires all these conditions:

- The raw evaluation space is standard Borel.
- The failure symbol $\bot$ is outside the finite output alphabet $\mathcal Z$.
- One map $Q(\omega,x)$ is measurable from $\mathcal G\otimes\mathcal B(\mathcal X)$ to
  $\mathcal Z\cup\{\bot\}$.
- The training sigma-field determines the random choice of $Q$.
- The output alphabet and block structure are finite and fixed.
- The map is frozen for every evaluation row and every prefix.
- Evaluation rows are conditionally i.i.d. given $\mathcal G$.
- $\Pr(Q(W_1)\ne\bot\mid\mathcal G)=1$ almost surely.

Here, $\mathcal B(\mathcal X)$ is the Borel sigma-field on the raw evaluation space. The symbol
$W_1$ denotes one raw evaluation row.

Conditional on $\mathcal G$, the target is the random push-forward law
$P_Q(z)=\Pr(Q(W_1)=z\mid\mathcal G)$. It is generally not the unconditional mixture law. The
theorem applies to the conditional functional for almost every training realization.

An i.i.d. raw evaluation sequence independent of the training artifact is an important special
case. Otherwise, the corollary does not require independence from the training artifact after the
conditional-i.i.d. contract is proved.

This theorem-level statement is broader than the stable fitted-wrapper contract. The stable
fitted-quantized APIs require the training artifact to be independent of the raw evaluation
sequence. This guide does not relax that cataloged API condition.

**Evidence/cost/use.** Lean covers a deterministic core. Lean does not cover the stochastic
theorem, complete higher-source semantics, Rust, or floating point. The bound can be conservative.

This result gives a consistency route for an empirical plug-in estimator. The result is not a new
estimator or calibration theorem. The corollary covers a held-out quantizer application only when
all frozen-transform conditions hold. Quantization changes the estimand. **[R,B,E,O]**

**Read next.** [`FINITE_ALPHABET_PLUGIN_CONVERGENCE.md`](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) and
the corresponding [PDF](output/pdf/finite-alphabet-plugin-convergence.pdf). Catalog entry:
`validation.finite-alphabet-plugin-convergence`.

### 3.3 Support-change-tolerant averaged-Sx continuity

**Assumptions/result.** The result fixes three objects:

- One complete finite alphabet of size $K$.
- The source-event family.
- The full Möbius lattice.

Laws $p,q$ may create/delete support inside that alphabet. The definitions are
$\eta=\frac12\lVert p-q\rVert_1$, $r_z=\min(p_z,q_z)$, $a=p-r$, and $b=q-r$. The result also uses
$E_\vee=\max(E(a),E(b))$ and $E_\Sigma=E(a)+E(b)$, where
$E(d)=-\sum_{d_z>0}d_z\log d_z$.

The quantity $\eta$ is the total variation distance. The vector $r$ contains the shared cellwise
mass. The vectors $a$ and $b$ contain the two residual masses. The function $E$ is the displayed
residual-mass sum.

The function is $g_J(\eta)=(1-\eta)\log(1+J\eta/(1-\eta))$ on $0<\eta<1$. Its endpoint values are
$g_J(0)=g_J(1)=0$. The other definitions are
$W_\alpha=\sum_\beta|M_{\alpha\beta}|g_{J_\beta}$ and
$s_\alpha=\sum_\beta M_{\alpha\beta}$.

Here, $M_{\alpha\beta}$ is a coefficient of the fixed Möbius inverse. The branch count is
$J_\beta=|\beta|$. The quantity $s_\alpha$ is a row sum of that inverse. The atom bounds are:

$$
|\Delta\Pi_\alpha^+|\le E_\vee+W_\alpha,\quad
|\Delta\Pi_\alpha^-|\le E_\vee+W_\alpha+|s_\alpha|g_1,\quad
|\Delta\Pi_\alpha^{\mathrm{net}}|\le E_\Sigma+2W_\alpha+|s_\alpha|g_1.
$$

For $\eta>0$ (which implies $K\ge2$),
$E_\vee\le\eta\log((K-1)/\eta)$ and
$E_\Sigma\le\eta\log(\lfloor K^2/4\rfloor/\eta^2)$. Both envelopes take the value zero at
$\eta=0$.

The exact functions above are not all monotone on $[0,1]$. Suppose a statistical result gives only
$\eta\le\varepsilon$. Direct substitution of $\varepsilon$ into the exact formulas is invalid
without a monotonicity proof.

For $K\ge2$, the monotone upper envelopes are:

$$
\bar e_K^\vee(\varepsilon)
=\varepsilon\left[1+\log\frac{K-1}{\varepsilon}\right],
\qquad
\bar e_K^\Sigma(\varepsilon)
=\varepsilon\left[2+\log\frac{\lfloor K^2/4\rfloor}{\varepsilon^2}\right].
$$

Both barred envelopes take the value zero at $\varepsilon=0$. For
$0\le\eta\le\varepsilon\le1$, the valid replacements satisfy:

$$
E_\vee\le\bar e_K^\vee(\varepsilon),
\qquad
E_\Sigma\le\bar e_K^\Sigma(\varepsilon),
\qquad
g_J(\eta)\le J\eta\le J\varepsilon.
$$

These monotone replacements can feed the atom bounds.

**Evidence/boundary.** The repository proves the residual/load decomposition. Fixed-system
witnesses establish a lower limit for one specified family of bounds. This family uses one common
leading coefficient and covers the retained witnesses. Such a family needs a coefficient of at
least 1 for components and 2 for net atoms.

The result does not include any of these theorems:

- A global linear theorem.
- A pointwise disappearing-key theorem.
- An alphabet-free theorem.
- An active-face Fannes theorem.
- A truncated-lattice theorem.

Lean covers subclaims. Lean does not cover the complete probability/Rust bridge. **[R,X,B,E,O]**

**Cost/use.** The result adds neither an estimator nor a confidence interval. A separately
justified law-distance radius can feed the deterministic modulus through the barred replacements
above. Fixed lattice coefficients are precomputable.

The result applies when rare cells enter/leave while the alphabet and quantizer remain fixed.

**Read next.** [`SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md`](SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md)
and the corresponding [PDF](output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf).
Catalog entry:
`validation.support-change-tolerant-averaged-sxpid-continuity`.

## 4. Sampling and exact finite-table assurance

### 4.1 Dependency-color concentration

**Assumptions/result.** Fix an integer $n\ge1$. Complete rows
$Z_i=(S_{1i},\ldots,S_{mi},T_i)$ for $1\le i\le n$ share one law $P$ on a $K$-cell alphabet with
$K\ge2$. The design must declare a coloring $\kappa$ before outcomes are observed. The set of color
labels is finite or countable. Rows must be jointly mutually independent **within** each color.

Dependence across colors may be arbitrary. Dependence among coordinates within each complete row
is unrestricted.

None of these weaker conditions is sufficient:

- Pairwise independence.
- Zero covariance.
- Adaptive colors.
- An unspecified mixing label.

The class load $n_{a,n}$ counts the first $n$ rows that have color $a$. The following bound holds
for every $\varepsilon>0$. The sums run over occupied colors:

$$
V_n=\left(\sum_a\sqrt{n_{a,n}}\right)^2,
\qquad
\Pr(\lVert\widehat P_n-P\rVert_1\ge\varepsilon)
\le\min\left\{1,(2^K-2)e^{-n^2\varepsilon^2/(2V_n)}\right\}.
$$

$V_n$ is Janson's cover-specific factor. The factor is not an estimated effective sample size. The
derivation uses [Hoeffding](https://doi.org/10.1080/01621459.1963.10500830),
[Janson](https://doi.org/10.1002/rsa.20008), and
[Weissman et al](https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2003/HPL-2003-97R1.pdf).
Repository work supplies prefix/drift and Sx-specific compositions.

A separate common-support local theorem uses laws $p$ and $q$ on the same fixed complete finite
alphabet. It has both law conditions:

- $\mathrm{supp}(q)\subseteq\mathrm{supp}(p)$.
- $\delta=\lVert q-p\rVert_1<2p_{\min}$.

Here, $p_{\min}=\min_{z\in\mathrm{supp}(p)}p(z)>0$.

The local theorem uses a supported realization $z=(s_1,\ldots,s_m,t)$. It also uses a nonempty
antichain $\alpha$ of nonempty source subsets. For each component
$u\in\{+,-,\mathrm{sx}\}$, the theorem states:

$$
\left|c_\alpha^u(z;q)-c_\alpha^u(z;p)\right|
\le\Lambda,
\qquad
\Lambda=\log\frac{p_{\min}}{p_{\min}-\delta/2}.
$$

The label $\mathrm{sx}$ denotes the net cumulative component. Thus, $\Lambda$ bounds the absolute
between-law change, not the cumulative value. **[P,R,X]**

**Evidence/cost/use.** Lean checks deterministic algebra. Lean does not check whether a scientific
design satisfies independence. Computing $V_n$ is cheap. However, $2^K-2$ can make the bound
vacuous, and validation of the dependence premise can be difficult. pid-rs supplies no public
automatic color estimator.

A fixed-width transformation of i.i.d. innovations can satisfy the premise. The coloring must be
predeclared, and same-color windows must use disjoint innovations. Arbitrary rolling data does not
satisfy the premise merely because a transformation has fixed width. **[B,E,O]**

**Read next.** [`DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md)
and the corresponding [PDF](output/pdf/dependency-colored-sxpid-concentration.pdf). Catalog entry:
`validation.dependency-color-sxpid-concentration`.

### 4.2 Exact two-source categorical-Sx assurance

**Assumptions/result.** Exactly two finite categorical sources and a finite target have natural
counts $c_z$ with $n=\sum_zc_z>0$. The conditions allow zero cells. The conditions prohibit
smoothing. For every cumulative or atom coordinate, exact event counts give a positive rational
$R$ with

$$
V=\frac1n\log R,
\qquad
V=0\iff R=1,
\qquad
\mathrm{sign}(V)=\mathrm{sign}(R-1).
$$

The assurance covers the 24 coordinates $4\times2\times3$. A retained counterexample shows that a
nonempty term map may still have product one. **[R,X]**

**Exact-product preflight.** A canonical expression has positive rational bases $x_j$ and rational
coefficients $q_j$ with $nq_j\in\mathbb Z$. Its denominator-cleared product and conservative
projection are:

$$
R=\prod_j x_j^{nq_j},
\qquad
B=\sum_j |nq_j|\left(
\mathrm{bits}(\mathrm{num}\,x_j)
+\mathrm{bits}(\mathrm{den}\,x_j)
\right).
$$

Here, $\mathrm{num}$ and $\mathrm{den}$ give the numerator and denominator. The function
$\mathrm{bits}$ gives the integer bit length.

**Status 1: count-to-atom bridge.** The Lean bridge is complete only in its supplied-count,
fixed-two-source scope. It does not prove paper correspondence, component nonnegativity, decoding,
Rust/binary64, sampling, or higher sources.

**Status 2: exact-product path.** One expression has at most 256 terms. Each absolute cleared
exponent is at most 16,384. Per-expression projected bits satisfy $B\le262{,}144$. The aggregate
projection is at most 1,048,576. A rejection means `unavailable` and never supplies a sign.

**Status 3: conditional certifier.** Certifier revision 3 gives conditional assurance for accepted
interval reports. It gives an exact sign or zero only when status is `compared`. Integration and
independent custody remain open. The intervals are not confidence intervals. **[R,B,E,O]**

**Cost/use.** Big rational products can grow quickly. Therefore, the exact-product path is an
offline oracle/escalation path for small empirical tables or near cancellation. The exact-product
path is not a population estimator.

**Read next: count-to-atom proof.** See
[`TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md`](audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md) and its
[PDF](output/pdf/two-source-sxpid-count-atom-bridge.pdf).

**Read next: exact-product report.** See
[`EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md`](audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md) and its
[PDF](output/pdf/exact-log-product-sxpid2-assurance.pdf).

**Read next: lifecycle decisions.** See the [`count-bridge decision
v2`](claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md) and [`certifier decision
v3`](claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md).

## 5. Higher-source, numerical, and continuous-estimator assurance

### 5.1 SxPID3 source-marginal factorization and bounded audit

**Factorization.** The factorization assumes:

- Finite source/target alphabets.
- One supplied source-only shared-exclusions event family **intended to transcribe MGW**.
- Natural-log units.
- One literally fixed transform.

“Source marginal” means the joint law $P_S$ of $(S_1,S_2,S_3)$. The term does not mean three
separate marginals. The set $E_\alpha(s)$ is the supplied source-only shared-exclusions event for
key $s$ and node $\alpha$. For supported source keys, the informative cumulative is:

$$
I_\alpha^+(P)=\sum_{s:P_S(s)>0}P_S(s)\left[-\log\sum_{s'\in E_\alpha(s)}P_S(s')\right]=G_\alpha(P_S).
$$

Hence, equal complete source marginals give equal informative cumulatives. Applying one fixed
linear transform to equal cumulatives gives equal transformed coordinates. Equal complete source
marginals need **not** preserve misinformative/net components. Exact counterexamples also show that
equal separate one-source marginals do not determine the informative vector. The continuity
specialization is deterministic, not a permutation calibration. **[P,R,X]**

**Bounded audit.** The exact domain has:

- Three ordered binary sources.
- One binary target.
- Every labeled 16-cell count table with $1\le N\le5$.

$$
\sum_{N=1}^{5}\binom{N+15}{15}=20{,}348,
\qquad
20{,}348\times108=2{,}197{,}584.
$$

The audit evaluates 2,197,584 products per route. Under a source-bound execution receipt, two
routes emit the same route-neutral v2 expression-stream SHA-256. The routes also emit the same
six-block sign/zero census. The routes use disjoint implementations under shared semantics.
Therefore, the routes are not independent proofs. Both routes retain the human transcription and
host/runtime premises.
**[B,E,O]**

**Status/cost/use.** The catalog marks the narrow entry
`validation.sxpid3-source-marginal-bounded-audit` as integrated and stable. Paper-to-local
correspondence remains open. These additional obligations also remain open:

- Concrete carrier/order proofs.
- Nonzero-log enclosure.
- Compiled-Rust/binary64 refinement.
- Larger domains.
- Population validity.
- External review.

The result adds no estimator. Cached source-event masses let target-only reallocations reuse the
informative block. A surrogate test still needs exchangeability. The exact audit is expensive.
Big-integer size depends on the input.

**Read next.** [`SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md`](SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md)
and [PDF](output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf). The separate full-certificate
[`revision index`](claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md) and
[`proposed decision`](claims/SX-CERTIFIED-AVERAGED-PID3-001/decision.md) have no accepted target
evidence. The separate full-certificate status does not downgrade or strengthen the integrated
narrow result.

### 5.2 Represented-binary64 and quantizer assurance

**Result.** Every finite binary64 number is an integer multiple of $2^{-1074}$. On supported 32-bit
and 64-bit targets, each positive or negative magnitude array has $L=34$ fixed limbs. Thus, one
accumulator has 68 limb slots in its two magnitude arrays. For finite operands, the reducer returns:

$$
\mathrm{reduce}(x_1,\ldots,x_n)
=\mathrm{RN}_{\mathrm{even}}\left(\sum_i x_i\right).
$$

The operator $\mathrm{RN}_{\mathrm{even}}$ rounds to nearest in binary64 and breaks ties to
even. The inner sum is exact for the **already represented** operands. The measure-specific call
sites are:

- Final averaging of represented categorical-Sx informative and misinformative components. The
  net component remains their derived difference.
- The four-operand Williams–Beer $I_{\min}$ PID2 synergy.
- Represented continuous-PID2 synergy plus its three reconstruction checks.

The reducer does not make probabilities, logarithms, or estimates exact. The reducer transfers no
semantics between those PID families. The reducer rejects a non-finite input. The reducer also
rejects an accepted-operand count beyond `usize::MAX`. Exact cancellation returns positive zero.
Estimator-facing callers reject an exact sum that rounds beyond the finite binary64 range.
**[R,B,E]**

The equal-width quantizer now constructs finite monotone edges across extreme ranges. The
quantizer reports nominal and finite-map-reachable joint cardinalities as `Option<u128>` values.
The quantizer reports the observed joint cardinality as `usize`. An optional numeric value is
present only when the relevant product fits in `u128`. `None` denotes overflow of that optional
product. Map reachability is not population support.

Bounded investigations did not justify these changes:

- Changing pointwise Sx Möbius reduction.
- Changing three-source $I_{\min}$ reduction.

These are bounded executable nonfindings, not counterexamples. **[B,E,O]**

The repository also rejected an order-dependent fast mode as policy-incompatible. **[O]**

**Cost/use.** For $n$ operands, reduction is $O(nL)$ with fixed $L=34$. The resource envelope
charges at most $2L$ limb visits per accepted add and $4L$ visits for finalization. Two Sx component
accumulators per lattice node require about:

- 4,416 bytes for two sources.
- 19,872 bytes for three sources.
- 183,264 bytes for four sources.

These amounts exclude other structures. Suitable uses include reproducible channel ordering,
exact reachability diagnostics, and resource preflight. The assurance is not a portable latency or
estimator-error theorem.

**Read next.** [`NUMERICAL_ASSURANCE.md`](NUMERICAL_ASSURANCE.md). A dedicated
`output/pdf/numerical-assurance.pdf` does not exist. This guide does not replace a dedicated
Numerical Assurance PDF.

### 5.3 KSG positive-integer harmonic arithmetic

**Status and theorem.** Revision 4 is active. The exact/formal/bounded core has scoped GO results.
However, repository/publication integration remains **NO-GO**. Final `decision-v4.md` and
`evidence-matrix-v4.md` are absent.

The symbol $\psi$ denotes the digamma function, and $\gamma$ denotes the Euler–Mascheroni
constant. For every positive integer $m$, [NIST DLMF Equation
5.4.14](https://dlmf.nist.gov/5.4.E14) gives $\psi(m)=H_{m-1}-\gamma$. Here, $H_0=0$ and
$H_j=\sum_{r=1}^j1/r$ for $j\ge1$. The variables $x$ and $y$ are positive-integer digamma arguments
from the inventoried estimator mappings.

The theorem has these conditions:

- $n\ge2$.
- $1\le k<n$.
- $k\le x,y\le n$.
- Coefficient pattern $(+1,+1,-1,-1)$.
- The published positive-integer identity is supplied as a typed premise at all four arguments.

Under these conditions, the arithmetic term satisfies:

$$
T=\psi(k)+\psi(n)-\psi(x)-\psi(y)
=H_{k-1}+H_{n-1}-H_{x-1}-H_{y-1},
\qquad
-D\le T\le D.
$$

Here, $D=H_{n-1}-H_{k-1}$. The bound is sharp on the rectangular arithmetic domain. Neighbor
geometry need not fully realize that domain. A stronger $x+y\le n+k$ route remains an unpromoted
conditional source lemma. **[P,R,O]**

**Evidence/boundary.** The packet has 19 scoped Lean theorems and 4 conditional Z3 obligations. The
packet also has bounded 8,198-row modular/enclosure/compiled evidence. Routes share the analytic
premise and human statement choices.

A rejected prime has exact-nonzero zero-residue collisions. Thus, modular zero is not exact zero in
general. Selected primes provide redundant fault diversity, not independent proofs.

Nothing here proves:

- Rust refinement.
- Neighbor geometry.
- KSG consistency.
- Ehrlich validity.
- PID atoms. **[X,B,E,O]**

**Cost/use.** A shifted harmonic table costs $O(n)$ setup/storage and gives $O(1)$ eligible local
terms. The table is a strong arithmetic regression oracle. The table is not a new estimator, speed
guarantee, support theorem, or calibration result.

**Read next.** [`revision-index.md`](claims/KSG-INTEGER-HARMONIC-001/revision-index.md),
[`claim-v4.md`](claims/KSG-INTEGER-HARMONIC-001/claim-v4.md),
[`formal-assurance-v4.md`](claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md), and
[`integration-disposition-v4.md`](claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md).
The existing `ksg-m1a-composite-*` PDFs are process/boundary packets, not a self-contained math
paper.

## 6. Estimator choice, global nonclaims, and further reading

| Data/question | First route | Still required |
|---|---|---|
| Supplied finite PMF/counts | Direct categorical functional. Exact assurance within its scope | Correct method/event encoding |
| I.i.d. categorical sample | Empirical plug-in plus finite-alphabet result | Fixed law, support/sample-size and UQ arguments |
| Explicit dependence coloring | Dependency-color bound | Predeclared valid within-color mutual independence |
| Nearby finite laws with support changes | Averaged-Sx modulus | Same alphabet/event/lattice and a justified law-distance radius |
| Continuous sample | Report-first KSG or experimental Ehrlich surface | Support, geometry, bias/calibration, dependence, and UQ |
| Near-zero empirical SxPID2 value | Bounded exact-product escalation | Two-source supplied-count scope and conditional statuses |

The following boundaries apply across all results:

- Bounded agreement stays bounded.
- Oracles must not read answer tables.
- Oracles must not import the implementation result as truth.
- Oracles must not weaken tolerances to pass.
- Oracles must not convert “unavailable” into a sign.
- The result boundaries prohibit clamping negative net atoms and exact zeros.
- Quantization or added noise changes the estimand.
- Shared names, citations, lattices, and software dependencies do not transfer semantics.
- No result supplies causal meaning, consumer authorization, or formal verification of all pid-rs.

Every use example above is illustrative. No use example qualifies an application.

These sources describe process and durable evidence:

- [`MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md) and the
  corresponding [PDF](output/pdf/mathematical-problem-solving-workflow.pdf).
- [`PID_MATHEMATICAL_AUDIT_PROTOCOL.md`](PID_MATHEMATICAL_AUDIT_PROTOCOL.md).
- [`PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md`](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md).
- [`FORMAL_TOOL_ADOPTION_AUDIT.md`](FORMAL_TOOL_ADOPTION_AUDIT.md).
- [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

These workflows preserve evidence. The workflows do not raise a theorem beyond its assumptions.

The guide uses these primary sources:

- The MGW categorical-Sx paper.
- The [part-whole/formal-logic account](https://doi.org/10.1098/rspa.2021.0110).
- The Ehrlich continuous-Sx paper.
- Williams–Beer $I_{\min}$.
- [Bertschinger et al. (2014)](https://doi.org/10.3390/e16042161) on bivariate finite-alphabet
  unique information.
- KSG.
- [NIST DLMF Equation 5.4.14](https://dlmf.nist.gov/5.4.E14).
- [Rota's Möbius theory](https://doi.org/10.1007/BF00531932).
- [Hoeffding](https://doi.org/10.1080/01621459.1963.10500830).
- [Janson](https://doi.org/10.1002/rsa.20008).
- [Weissman et al](https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2003/HPL-2003-97R1.pdf).

The linked detailed reports give equation-level provenance. Each report marks the precise point
where each source stops applying.
