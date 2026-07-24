# Provenance boundaries and retained failures

## F1: A global linear modulus is false

### False statement

There is a finite constant $L$, independent of the law, such that every averaged categorical
SxPID atom satisfies

$$
|\Pi_\alpha(P)-\Pi_\alpha(Q)|
\leq L\lVert P-Q\rVert_1
$$

on the closed simplex.

### Correct counterexample

Use two sources and the fixed Cartesian-product alphabet

$$
\mathcal Z=\{0,1\}\times\{0\}\times\{0,1\}.
$$

Place positive mass only on

$$
z_0=(S_1,S_2,T)=(0,0,0),\qquad
z_1=(S_1,S_2,T)=(1,0,1).
$$

Let

$$
P_\varepsilon(z_1)=\varepsilon,\qquad
P_\varepsilon(z_0)=1-\varepsilon,
$$

set the other two cell masses to zero, and let $P_0(z_0)=1$ with every other cell mass zero.
Thus $S_2$ is constant and $T=S_1$ almost surely under every law in this family.

For the two-source redundancy node, the $S_2=0$ branch makes the union event the whole sample
space. Its informative and misinformative local cumulatives are zero. For the $S_1$ node, the
source event equals the keyed target event. Therefore the unique-$S_1$ atom satisfies

$$
\pi_{U_1}^+(z;P_\varepsilon)
=-\log P_\varepsilon(S_1=s_1),
\qquad
\pi_{U_1}^-(z;P_\varepsilon)=0.
$$

Consequently,

$$
\Pi_{U_1}^+(P_\varepsilon)
=
\Pi_{U_1}^{\mathrm{net}}(P_\varepsilon)
=
h_2(\varepsilon),
$$

where

$$
h_2(\varepsilon)
=
-\varepsilon\log\varepsilon
-(1-\varepsilon)\log(1-\varepsilon).
$$

Also,

$$
\lVert P_\varepsilon-P_0\rVert_1=2\varepsilon.
$$

Hence

$$
\frac{h_2(\varepsilon)}{2\varepsilon}\longrightarrow\infty.
$$

This rejects every global linear modulus. It also proves that any general modulus must permit
variation of order $\eta\log(1/\eta)$, where
$\eta=d_{\mathrm{TV}}(P_\varepsilon,P_0)=\varepsilon$.
It does not establish a sharp universal upper bound.

### Rejected earlier variant

An earlier exploratory variant set $T$ constant. That variant is not a net-atom counterexample.
When $T$ is constant, the informative and misinformative local components coincide, so the net
term cancels. It can still challenge a component-only linear claim, but it does not challenge the
net claim. The corrected construction uses $T=S_1$.

Status: `REJECTED-BY-COUNTEREXAMPLE` for the global linear statement.

## F2: Pointwise continuity across support deletion is false

In the corrected construction, evaluate the rare key $z_1$ while
$\varepsilon>0$. Its unique-$S_1$ informative and net atom is

$$
-\log\varepsilon,
$$

which diverges as $\varepsilon\downarrow0$. At $\varepsilon=0$, the key is absent.

Therefore, the new claim must concern averaged quantities. It must not assert a finite continuous
extension of every keyed local value.

Status: `REJECTED-BY-COUNTEREXAMPLE` for pointwise boundary continuity.

## F3: Component nonnegativity does not imply net nonnegativity

Makkeh, Gutknecht, and Wibral prove
$\pi_\alpha^+\geq0$ and $\pi_\alpha^-\geq0$. The net atom is their difference.

Their Table III RndErr example reports, for the second source’s averaged unique atom, approximately
$0.443$ informative bits and $0.811$ misinformative bits. The net value is approximately
$-0.367$ bits. Their XOR example also has negative local net shared information.

Source:
[Makkeh et al., final arXiv v5](https://arxiv.org/pdf/2002.03356v5),
[published DOI](https://doi.org/10.1103/PhysRevE.103.032149).

Consequence: nonnegativity can support component residual bounds. It cannot be applied directly to
net atoms.

## F4: Interior differentiability is not a boundary theorem

Makkeh et al. Section IV.B proves continuous differentiability over the interior of the probability
simplex. A path that creates or deletes a cell reaches the boundary. The source result does not
supply a total-variation modulus there.

Schick-Poland et al. give a measure-theoretic density differentiability result. It does not state
the fixed-finite-alphabet closed-simplex theorem in claim-v1.md.

Consequence: the new continuity result is project-defined. It must not be attributed to either
paper.

## F5: A zero weight does not make an undefined logarithm valid

Writing a fixed-alphabet sum with a zero-mass key can produce the informal expression
$0\cdot\infty$. This is not a real-number definition.

The accepted convention is a sum over $\mathrm{supp}\,P$. A fixed-alphabet totalization is
permitted only after a separate proof defines the zero-weight summand and proves equivalence.

## F6: A full-lattice sign theorem does not transfer automatically

Makkeh et al. Theorem IV.3 concerns the paper-defined Möbius inversion on the full redundancy
lattice. It does not prove component nonnegativity for:

- a truncated node set;
- an arbitrary coefficient matrix;
- a changed lattice order;
- another PID definition;
- a transform selected from the same law comparison.

The concrete project lattice and matrix must be identified with the source objects.

## F7: A changing observed alphabet changes the object

If each law uses only its observed support as its alphabet, the event map, matrix dimensions, and
possibly the lattice representation can change between endpoints. Such a comparison is not the
claim in revision 1.

The ambient Cartesian-product alphabet and full finite lattice must be fixed before comparing
laws.

## F8: General entropy continuity is not a direct substitution

For a general antichain, the keyed events $E_\alpha(s)$ overlap. They need not form a partition.
Makkeh et al. explain after Eq. (17) that the averaged shared-exclusions quantity is structurally
different from an ordinary mutual information because the auxiliary event changes with the keyed
realization.

Therefore, a Shannon-entropy continuity theorem alone does not close the common-overlap event
obligation. A dedicated argument is required.

## Scope boundaries

This packet does not support claims about:

- continuous or mixed-variable shared exclusions;
- adaptive or same-sample fitted quantization;
- finite-sample confidence or concentration;
- dependent rows or drift;
- binary64 signs near zero;
- correctness of a Rust implementation;
- downstream authorization or safety;
- scientific priority.
