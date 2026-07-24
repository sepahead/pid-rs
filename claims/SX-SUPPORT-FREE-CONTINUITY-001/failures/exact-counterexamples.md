# Exact counterexamples and scope limits

## Evidence rule

This file records falsifiers and proof obstructions. Each conclusion is limited to the statement
that the construction tests. A counterexample to one proof step is not automatically a
counterexample to the final theorem.

Throughout this file, logarithms are natural and
$\eta=d_{\mathrm{TV}}(P,Q)=\frac12\lVert P-Q\rVert_1$.

## EC1: Exact generic $K=16$ entropy-only falsifier

Let the keyed cells be $0,1,\ldots,15$. Define a star neighborhood system by

$$
N_0=\{0,1,\ldots,15\},\qquad N_i=\{0,i\}\quad(1\leq i\leq15).
$$

Let

$$
P=\left(0,\frac1{15},\ldots,\frac1{15}\right)
$$

and

$$
Q=\left(\frac1{30},\frac1{30},
\frac1{15},\ldots,\frac1{15}\right),
$$

where $Q$ has fourteen trailing entries equal to $1/15$. Then

$$
\eta=\frac1{30},
\qquad
G_{\mathcal N}(P)=\log15,
$$

and

$$
G_{\mathcal N}(Q)
=
\frac1{30}\log15+\frac{14}{15}\log10.
$$

Therefore,

$$
|\Delta G|
=
\frac{29}{30}\log15-\frac{14}{15}\log10
=
0.4687024409376938\ldots.
$$

The entropy-only Fannes expression is

$$
h_2(1/30)+\frac1{30}\log15
=
0.2364130860453042\ldots.
$$

The strict comparison reduces to the integer inequality

$$
3^{28}29^{29}>2^{28}30^{30}.
$$

Status: `REJECTED-BY-EXACT-COUNTEREXAMPLE` for the generic entropy-only transfer.

Scope: this is an earlier generic star. It does not prove minimality and does not by itself give a
small-source SxPID witness.

## EC2: Exact three-source, five-cell SxPID witness

Use three sources. Keep the target constant. Use these source words, in order:

$$
000,\quad011,\quad202,\quad330,\quad444.
$$

Use the bottom singleton antichain

$$
\alpha=\{\{1\},\{2\},\{3\}\}.
$$

Let

$$
P=\left(0,\frac3{10},\frac3{10},\frac3{10},\frac1{10}\right)
$$

and

$$
Q=\left(\frac1{10},\frac3{10},\frac3{10},\frac3{10},0\right).
$$

Then $\eta=1/10$. The exact informative cumulative change is

$$
|\Delta C_\alpha^+|
=
\frac1{10}\log10+\frac9{10}\log\frac43
=
0.4891723745060074\ldots.
$$

Because the target is constant, the misinformative cumulative has the same change and the net
cumulative change is zero.

The union $\mathrm{supp}\,P\cup\mathrm{supp}\,Q$ is the five-state union-support face. The
Fannes--Audenaert entropy expression on that face is

$$
h_2(1/10)+\frac1{10}\log4.
$$

The excess is

$$
\frac9{10}\log\frac65-\frac1{10}\log4
=
0.0254599650025701\ldots.
$$

It is positive exactly when

$$
6^9>4\cdot5^9.
$$

This rejects using the ordinary entropy radius computed on the union-support face as a bound for
the Sx neighborhood functional. It does not assert failure of a looser expression formed with the
cardinality of the complete ambient Cartesian product.

For the common-residual split, both residual entropies equal

$$
E_a=E_b=\frac1{10}\log10.
$$

Also,

$$
\gamma_3(1/10)=\frac9{10}\log\frac43.
$$

Thus this witness attains

$$
|\Delta C_\alpha^+|=E_{\max}+\gamma_3
$$

exactly. The candidate budget is sharp at this instance.

Status: `REJECTED-BY-EXACT-COUNTEREXAMPLE` for an entropy-only bound on this five-row system.

Scope: the construction does not prove that five active cells are globally minimal. It also does
not reject a looser expression that inserts a larger ambient Cartesian-product cardinality.

## EC3: Exact four-source six-pair half-transfer witness

Keep the target constant. Use the center source word $0000$ and the six leaves

$$
0011,\quad0202,\quad0330,\quad4004,\quad5050,\quad6600.
$$

Let $\alpha$ contain all six two-source subsets:

$$
\alpha=
\{\{1,2\},\{1,3\},\{2,3\},\{1,4\},\{2,4\},\{3,4\}\}.
$$

In the listed cell order, let

$$
P=\left(0,\frac16,\frac16,\frac16,\frac16,\frac16,\frac16\right)
$$

and

$$
Q=\left(\frac1{12},\frac1{12},
\frac16,\frac16,\frac16,\frac16,\frac16\right).
$$

Then $\eta=1/12$, and the informative and misinformative cumulative changes are

$$
|\Delta C_\alpha^+|
=
|\Delta C_\alpha^-|
=
\frac1{12}\log6+\frac56\log\frac32
=
0.4872008791924749\ldots.
$$

The net change is zero. The excess over the support-size-seven Fannes expression is

$$
0.05105160703397634\ldots>0.
$$

Its sign is exact:

$$
\text{excess}>0
\quad\Longleftrightarrow\quad
11^{11}>9\cdot2^{34}.
$$

For the half-transfer star family with $m$ branches, set

$$
P_m=\left(0,\frac1m,\ldots,\frac1m\right)
$$

and

$$
Q_m=\left(\frac1{2m},\frac1{2m},
\frac1m,\ldots,\frac1m\right).
$$

The exact change is

$$
\Delta_m
=
\frac1{2m}\log m+\frac{m-1}{m}\log\frac32.
$$

The route checked that the Fannes excess is negative for $m=1,\ldots,5$ and positive for
$m=6$.

Status: `REJECTED-BY-EXACT-COUNTEREXAMPLE` for the entropy-only bound at $m=6$.

Scope: six branches are minimal only in this half-transfer star family. The construction does not
prove global minimality over four-source SxPID laws or antichains.

## EC4: Corrected $T=S_1$ boundary witness

Use the fixed Cartesian-product alphabet

$$
\mathcal Z=\{0,1\}\times\{0\}\times\{0,1\}.
$$

Put

$$
P_0(0,0,0)=1.
$$

For $0<\varepsilon<1$, put

$$
P_\varepsilon(0,0,0)=1-\varepsilon,\qquad
P_\varepsilon(1,0,1)=\varepsilon,
$$

and give every other cell mass zero. Thus $S_2$ is constant and $T=S_1$ almost surely.

For the unique-$S_1$ atom,

$$
\Pi_{U_1}^+(P_\varepsilon)
=
\Pi_{U_1}^{\mathrm{net}}(P_\varepsilon)
=
h_2(\varepsilon).
$$

The rare local informative and net value is

$$
-\log\varepsilon,
$$

and its misinformative value is zero. Also,

$$
\lVert P_\varepsilon-P_0\rVert_1=2\varepsilon.
$$

Therefore,

$$
\frac{h_2(\varepsilon)}{2\varepsilon}\longrightarrow\infty.
$$

Status:

- `REJECTED-BY-EXACT-COUNTEREXAMPLE` for a global linear averaged modulus; and
- `REJECTED-BY-EXACT-COUNTEREXAMPLE` for finite pointwise continuity at support deletion.

Scope: the averaged value still tends to zero. This construction does not reject averaged
closed-simplex continuity. The earlier constant-target variant is not a net counterexample because
its informative and misinformative terms cancel.

## EC5: Exact net-residual max-shortcut obstruction

Use two sources and let $S_2$ be constant. For $0<\eta<1$, put $R=1-\eta$ and define the
parametric laws

$$
P_\eta(0,0,0)=\eta,
\qquad
P_\eta(1,0,2)=P_\eta(2,0,1)=R/2,
$$

$$
Q_\eta(1,0,1)=\eta,
\qquad
Q_\eta(1,0,2)=Q_\eta(2,0,1)=R/2.
$$

The committed executable fixture specializes this family to $\eta=1/10$ with total count 20:

$$
\begin{array}{c|ccc}
 & (0,0,0) & (1,0,2) & (2,0,1)\\
\hline
P\text{ count} & 2 & 9 & 9
\end{array}
$$

and

$$
\begin{array}{c|ccc}
 & (1,0,1) & (1,0,2) & (2,0,1)\\
\hline
Q\text{ count} & 2 & 9 & 9.
\end{array}
$$

For the parametric family, the common part has mass $R$. The left residual has mass $\eta$ at
$(0,0,0)$. The right residual has mass $\eta$ at $(1,0,1)$.

Since $S_2$ is constant, the unique-$S_1$ net atom equals the $S_1$-node cumulative. The node's
local value is pointwise mutual information, while its averaged cumulative is $I(S_1;T)$. The
left residual local value is

$$
\log\frac1\eta.
$$

The right residual local value is

$$
\log\frac{4\eta}{(1+\eta)^2}.
$$

The signed residual difference is therefore

$$
\eta
\left(
\log\frac1\eta
-
\log\frac{4\eta}{(1+\eta)^2}
\right)
=
2\eta\log\frac{1+\eta}{2\eta}.
$$

But

$$
E_a=E_b=\eta\log\frac1\eta,
$$

and

$$
2\eta\log\frac{1+\eta}{2\eta}
>
\eta\log\frac1\eta.
$$

The strict inequality is equivalent to $(1-\eta)^2>0$. At the committed value $\eta=1/10$,
the two residual local values are $\log 10$ and $\log(40/121)$, and the residual difference is
$(1/5)\log(11/2)$.

Thus $E_{\max}$ cannot bound this signed residual term. The retained proof budget uses
$E_a+E_b$.

The same construction also gives a whole-output lower obstruction. With $R=1-\eta$, the complete
unique-$S_1$ net-atom difference is

$$
2\eta\log\frac{1+\eta}{2\eta}
+
R\log\frac{1+\eta}{R}.
$$

Therefore

$$
\lim_{\eta\downarrow0}
\frac{
\left|
\Pi_{U_1}^{\mathrm{net}}(P_\eta)
-
\Pi_{U_1}^{\mathrm{net}}(Q_\eta)
\right|
}{
\eta\log(1/\eta)
}
=2.
$$

This exact limit shows that a universal net-atom modulus needs leading logarithmic coefficient
at least two. It does not make the lower-order terms of the retained upper bound sharp.

Status:

- `REJECTED-BY-EXACT-COUNTEREXAMPLE` for the max-residual shortcut inside this proof
  decomposition; and
- `REJECTED-BY-EXACT-COUNTEREXAMPLE` for a family of covered fixed-system whole-net-atom bounds
  $c\eta\log(1/\eta)+O_{\mathcal F}(\eta)$ whose common leading coefficient satisfies $c<2$.

Scope: the construction does not make the lower-order terms, branch terms, or complete retained
upper bound globally sharp. It does not reject a different whole-atom bound whose leading
coefficient is at least two. Earlier bounded-search nonfindings are historical route evidence and
do not override the exact parametric calculation.

## EC6: Bounded nonfindings are not minimality proofs

The numerical route did not find a $K=4$ entropy-only violation on its finite grids. Those searches
used finitely many rational laws and finitely many neighborhood systems. The fast pass used
binary64 arithmetic before exact-input `Decimal` reevaluation of the selected candidate.

Status: `NOT-A-PROOF` for global five-cell minimality.

The exact witness formulas above remain valid. For the historical revision-1 numerical route, the
following statements were not resolved by bounded search:

- whether a different $K=4$ law gives an entropy-only violation;
- whether a smaller SxPID construction exists under another active-cell convention;
- whether another proof gives a stronger whole-atom net bound; and
- whether the then-candidate residual and overlap bounds hold on every finite simplex.

Revision 2 resolves the last item analytically through the generic residual-plus-load theorem and
its equivalence-union specialization. The Lean route still checks only supporting algebra and does
not formalize that full semantic proof.

## Replay boundary

The first exploratory generator and oracle used by the revision-1 route were in `/tmp`. Their
historical hashes remain recorded in
[../route-memos/numerical-attack.md](../route-memos/numerical-attack.md).

Revision 2 promotes independently regenerable evidence into the repository:

- [`scripts/generate-support-change-tolerant-sxpid-oracle.py`](../../../scripts/generate-support-change-tolerant-sxpid-oracle.py)
  generates and checks exact rational identities, a bounded seeded challenge corpus, and
  high-precision references;
- [`support_change_tolerant_sxpid_oracle.json`](../../../crates/pid-core/tests/fixtures/support_change_tolerant_sxpid_oracle.json)
  is the committed fixture, with SHA-256
  `aba9cefd44f40c2f8a552497c38bc9b063b4b41ca313196c1e7c4960fbaa2158`;
- [`support_change_tolerant_sxpid_oracle.json.sha256`](../../../crates/pid-core/tests/fixtures/support_change_tolerant_sxpid_oracle.json.sha256)
  is the fail-closed digest sidecar; and
- [`support_change_tolerant_sxpid_oracle.rs`](../../../crates/pid-core/tests/support_change_tolerant_sxpid_oracle.rs)
  replays 36 realizable empirical count tables through the public stable categorical API.

The generator's default check and `--check` mode pass, and the targeted Rust replay reports four
passing tests. This closes reproducibility for the committed bounded witnesses. It does not turn a
bounded nonfinding into a proof, refine the entire Rust implementation to the exact-real
specification, or enclose binary64 logarithm error.

The larger finite-grid searches are historical revision-1 route evidence only. Their scope and
ephemeral artifact hashes remain in
[`../route-memos/numerical-attack.md`](../route-memos/numerical-attack.md); the tracked generator
does not claim to rerun them.
