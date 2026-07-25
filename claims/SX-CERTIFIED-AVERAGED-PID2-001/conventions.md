# Conventions for SX-CERTIFIED-AVERAGED-PID2-001

## Canonical empirical count table

The accepted positive empirical support is a finite set

$$
\mathcal Z_+=\{z=(s_1,s_2,t):c_z>0\}.
$$

Each $s_1$, $s_2$, and $t$ is a nonempty fixed-width vector of canonical ASCII tokens. Counts are
canonical positive decimal strings representing integers

$$
c_z\in\mathbb N_{>0},
\qquad
N=\sum_{z\in\mathcal Z_+}c_z,
\qquad
\widehat P(z)=\frac{c_z}{N}.
$$

Rows are strictly increasing in lexicographic order and each complete state occurs exactly once.
The table describes an empirical law only. It does not assert that observed support equals
population support.

This uniqueness condition is also an executable proof premise. For a keyed supported row,

$$
\left|E_1(z)\cap E_2(z)\cap T(z)\right|_c=c_z,
$$

where $|\cdot|_c$ denotes count mass. Therefore the verifier may reconstruct
$|E_\vee(z)\cap T(z)|_c$ by inclusion--exclusion as
$|E_1(z)\cap T(z)|_c+|E_2(z)\cap T(z)|_c-c_z$. A future schema that permits repeated complete
states must replace $c_z$ with their aggregated intersection mass. It may not reuse this shortcut
without a new proof and retained mutation.

## Realization-keyed events

For a supported key $z=(s_1,s_2,t)$, define

$$
\begin{aligned}
E_1(z)&=\{z':s'_1=s_1\},\\
E_2(z)&=\{z':s'_2=s_2\},\\
E_{12}(z)&=E_1(z)\cap E_2(z),\\
E_\vee(z)&=E_1(z)\cup E_2(z),\\
T(z)&=\{z':t'=t\}.
\end{aligned}
$$

Equality compares the complete token vector. The cumulative node order and source-mask encoding
are:

| Node | Identifier | Source masks | Event |
|---|---|---:|---|
| 1 | `source_one` | `[1]` | $E_1$ |
| 2 | `source_two` | `[2]` | $E_2$ |
| 12 | `joint_sources` | `[3]` | $E_{12}$ |
| $\vee$ | `redundancy` | `[1,2]` | $E_\vee$ |

The redundancy event is a disjunction, not the joint-source intersection.

For a nonempty source collection $a\subseteq\{1,2\}$, let

$$
E_a(z)=\bigcap_{i\in a}E_i(z).
$$

An antichain is a nonempty set of nonempty source collections in which no member contains another.
The complete two-source antichain set is

$$
\alpha_R=\{\{1\},\{2\}\},\qquad
\alpha_1=\{\{1\}\},\qquad
\alpha_2=\{\{2\}\},\qquad
\alpha_{12}=\{\{1,2\}\}.
$$

Its event is

$$
A_\alpha(z)=\bigcup_{a\in\alpha}E_a(z).
$$

The redundancy order is

$$
\alpha\preceq\beta
\quad\Longleftrightarrow\quad
\forall b\in\beta\;\exists a\in\alpha:\ a\subseteq b.
$$

Thus $\alpha_R$ is the bottom node, $\alpha_{12}$ is the top node,
$\alpha_R\prec\alpha_i\prec\alpha_{12}$ for $i=1,2$, and $\alpha_1,\alpha_2$ are incomparable.
The executable nodes $(1,2,12,\vee)$ correspond to
$(\alpha_1,\alpha_2,\alpha_{12},\alpha_R)$. The event-union symbol $\vee$ must not be mistaken for
the lattice supremum.

For node $\alpha$, define exact integer masses

$$
U_{\alpha,z}=\sum_{z'\in A_\alpha(z)}c_{z'},
\qquad
V_{\alpha,z}=\sum_{z'\in A_\alpha(z)\cap T(z)}c_{z'},
\qquad
T_z=\sum_{z'\in T(z)}c_{z'}.
$$

Because the supported key belongs to every keyed event,

$$
0<c_z\le V_{\alpha,z}\le U_{\alpha,z}\le N,
\qquad
V_{\alpha,z}\le T_z\le N.
$$

Thus every logarithm argument below is positive.

## Averaged cumulatives

For each node $\alpha$:

$$
C^+_\alpha
=
\sum_{z\in\mathcal Z_+}\frac{c_z}{N}
\log\!\left(\frac{N}{U_{\alpha,z}}\right),
$$

$$
C^-_\alpha
=
\sum_{z\in\mathcal Z_+}\frac{c_z}{N}
\log\!\left(\frac{T_z}{V_{\alpha,z}}\right),
$$

and

$$
C^{\mathrm{sx}}_\alpha
=
\sum_{z\in\mathcal Z_+}\frac{c_z}{N}
\log\!\left(\frac{N V_{\alpha,z}}{U_{\alpha,z}T_z}\right)
=C^+_\alpha-C^-_\alpha.
$$

For nodes $1$, $2$, and $12$, the net cumulative is also reconstructed independently as ordinary
empirical mutual information between the indicated source collection and the target.

## Fixed two-source lattice

For each component $u\in\{+,-,\mathrm{sx}\}$, use

$$
C^u=
\begin{bmatrix}
C^u_1&C^u_2&C^u_{12}&C^u_\vee
\end{bmatrix}^{\mathsf T}
$$

and

$$
\Pi^u=
\begin{bmatrix}
U^u_1&U^u_2&S^u&R^u
\end{bmatrix}^{\mathsf T}.
$$

The pinned Möbius and zeta matrices are

$$
\Pi^u=M C^u,
\qquad
M=
\begin{bmatrix}
 1& 0& 0&-1\\
 0& 1& 0&-1\\
-1&-1& 1& 1\\
 0& 0& 0& 1
\end{bmatrix},
$$

$$
C^u=Z\Pi^u,
\qquad
Z=
\begin{bmatrix}
1&0&0&1\\
0&1&0&1\\
1&1&1&1\\
0&0&0&1
\end{bmatrix}.
$$

Exact integer arithmetic checks $ZM=I_4$. The independent verifier declares its own copies of
these matrices and checks both inverse algebra and exact coordinate reconstruction.

## Twenty-four-coordinate order

There are exactly 24 coordinates:

1. 12 cumulatives: four nodes for each of informative, misinformative, and net;
2. 12 atoms: four atoms for each of informative, misinformative, and net.

The accepted identity order is versioned and exact. Duplicate, missing, reordered, or relabeled
coordinate identities are rejected.

## Exact log-linear normal form

Each coordinate is a finite map

$$
F=\sum_j a_j\log q_j,
\qquad
a_j\in\mathbb Q\setminus\{0\},
\quad
q_j\in\mathbb Q_{>0}\setminus\{1\}.
$$

Terms are keyed by exact rational $q_j$. Coefficients for equal arguments are combined exactly.
Zero coefficients and $\log 1$ are removed.

An empty map is a sound exact-zero witness. The converse is not asserted: identities such as
$\log2+\log3-\log6=0$ need not reduce to an empty map.

## Producer intervals

The Rust producer emits normalized dyadic endpoints

$$
L=m_L2^{e_L},
\qquad
U=m_U2^{e_U},
$$

with odd nonzero significands and the unique zero encoding $(m,e)=(0,0)$. The versioned precision
policy uses working precisions 128, 256, 512, 1024, 2048, and 4096 bits, intersects successive
enclosures, and requires final width at most $2^{-160}$.

The producer-only proof is conditional on directed Rug/MPFR operations. It is not the final
independent-containment route in this packet.

## Independent rational-log enclosure

For a positive rational $x$, the Python verifier writes

$$
x=2^e y,
\qquad
1\le y<2,
\qquad
z=\frac{y-1}{y+1}\in[0,1/3].
$$

It uses

$$
\log y
=
2\sum_{k=0}^{m-1}\frac{z^{2k+1}}{2k+1}+R_m
$$

with

$$
0\le R_m
\le
\frac{2z^{2m+1}}{(2m+1)(1-z^2)}
\le
\frac{9z^{2m+1}}{4(2m+1)}.
$$

The geometric series for $(1-z^2)^{-1}$ converges uniformly on $[0,1/3]$, which justifies
termwise integration on that interval. The cached $\log 2$ interval is computed separately,
without recursive range reduction, by the same recurrence at $y=2$ and therefore $z=1/3$.
Because $2=(1+z)/(1-z)$ and the tail bound includes the endpoint $z=1/3$, that base case encloses
$\log 2$.

To make the executable enclosure explicit, fix $b$ and put $S=2^b$. Define

$$
z_L=\lfloor Sz\rfloor,\qquad z_U=\lceil Sz\rceil,
$$

$$
w_L=\left\lfloor\frac{z_L^2}{S}\right\rfloor,\qquad
w_U=\left\lceil\frac{z_U^2}{S}\right\rceil,
$$

and initialize

$$
p_{0,L}=z_L,\quad p_{0,U}=z_U,\quad L_0=U_0=0.
$$

For $j=0,\ldots,m-1$, compute with exact integer floor and ceiling division

$$
\begin{aligned}
L_{j+1}
  &=L_j+\left\lfloor\frac{2p_{j,L}}{2j+1}\right\rfloor,\\
U_{j+1}
  &=U_j+\left\lceil\frac{2p_{j,U}}{2j+1}\right\rceil,\\
p_{j+1,L}
  &=\left\lfloor\frac{p_{j,L}w_L}{S}\right\rfloor,\\
p_{j+1,U}
  &=\left\lceil\frac{p_{j,U}w_U}{S}\right\rceil.
\end{aligned}
$$

Induction gives

$$
\frac{p_{j,L}}S\le z^{2j+1}\le\frac{p_{j,U}}S
$$

and outward lower and upper bounds on the first $j$ series terms. Therefore the returned reduced
log interval is

$$
\left[
\frac{L_m}{S},
\frac{U_m+\left\lceil 9p_{m,U}/(4(2m+1))\right\rceil}{S}
\right].
$$

The implementation uses

$$
m=\max\left\{32,\left\lfloor\frac{b+32}{3}\right\rfloor+1\right\}.
$$

Range reduction adds $e\log2$ and swaps the $\log2$ endpoints when $e<0$. Multiplication by a
negative rational coefficient likewise swaps endpoints. The fixed verifier precision schedule is
256, 384, 512, 768, 1024, 1536, and 2048 bits. For a coordinate it derives an interval $J_j$ and
accepts only if

$$
J_j\subseteq I_j.
$$

Overlap and precision-schedule exhaustion are not acceptance.

## Sign labels

For a certificate interval $[L,U]$:

- `certified_positive` requires $L>0$;
- `certified_negative` requires $U<0$;
- `certified_exact_zero` requires the sound empty-expression witness; and
- every other case is `unresolved_sign`.

No atom is clamped. Negative SxPID atoms are valid outputs.

## Scope exclusions

These conventions do not define a population theorem, confidence interval, continuous estimator,
pointwise decomposition, higher-source lattice, quantizer, or `pid-core` refinement.
