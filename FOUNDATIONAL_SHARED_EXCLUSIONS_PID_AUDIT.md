# Foundational validity audit of shared-exclusions PID

## Exact semantics, compatibility firewall, adversarial counterexamples, and a bounded executable audit

**Status:** first-principles audit of the paper-defined categorical shared-exclusions measure
$i^{\mathrm{sx}}_\cap$ and its antichain-lattice PID. This document does not define a new PID
measure. It separates published theorems, project rederivations, exact counterexamples, bounded
computations, executable observations, and open questions.

**Date:** 25 July 2026

**Units:** nats unless a result is explicitly stated in bits.
**Primary object audited:** Makkeh--Gutknecht--Wibral shared exclusions, not PID in general.

The audit uses three complementary, implementation-distinct but correlated lanes for its most
sensitive compatibility conclusion. The standard-library Python checker and the Rust regression
each compute the concrete witness. Lean proves only the conditional transfer firewall: it isolates
the descriptor-factorization premise needed to transfer a descriptor-collision impossibility
result to a candidate PID, but it does not compute or certify the concrete Sx event calculation.
All three lanes share reviewed semantic cuts, including the encoding of the stipulated systems,
the descriptor map, and the conclusion being tested. Their agreement is therefore corroboration
across implementations, not logical independence.

---

## Executive decision

The categorical shared-exclusions construction is mathematically valid in the following precise
sense.

1. Its keyed source event is well-defined for every supported realization.
2. Its local cumulative is an ordinary likelihood-ratio information value for that keyed event.
3. The antichain order, event containments, and Möbius inversion give an exact signed decomposition.
4. The greatest-node cumulative is local mutual information, so the averaged atoms reconstruct the
   joint source--target mutual information exactly.
5. The informative and misinformative component atoms are nonnegative. The net atoms need not be.
6. Source permutation symmetry, coordinatewise bijective re-encoding invariance, self-redundancy,
   and the target chain rule follow from the definition.
7. The present Rust implementation reproduces exact finite witnesses, including a new adversarial
   three-source relation witness.

No fatal algebraic contradiction was found in the Makkeh--Gutknecht--Wibral construction or in its
core published theorems.

That conclusion is deliberately narrower than saying that shared exclusions is *the* uniquely
correct PID. The following stronger readings are false or unsupported.

- The disjunction event is not forced uniquely by Shannon theory. It implements a constitutive
  notion of shared logical consequence.
- An SxPID atom is not necessarily a nonnegative set-sized piece, dependence strength, common
  deterministic signal, common target feature, or causal contribution.
- Independent sources can have positive Sx redundancy. Net atoms can be negative.
- Net redundancy has no general data-processing monotonicity under source or target coarse-graining.
- The value is not identifiable from pairwise source--target marginals. It uses the full joint law.
- The source and target roles are not interchangeable.
- The pointwise auxiliary event changes with the realized source key. Its average is not the mutual
  information of one fixed auxiliary random variable.
- A PID atom alone does not establish mechanism, responsibility, deception, safety, or decision
  authority.

The correct foundational verdict is therefore:

> **Shared exclusions is a coherent, signed, local, event-logical PID under an explicit semantic
> contract. It is not a universal ontology of informational parts.**

The distinction is essential. Most apparent contradictions disappear when a result from another
PID semantics is prevented from being silently imported into the shared-exclusions definition.

---

## 1. Evidence classes and audit protocol

Every result below carries one of these evidence labels.

| Label | Meaning |
|---|---|
| **[P]** | Published theorem or definition in a primary source. |
| **[R]** | Separate exact repository rederivation in this audit. |
| **[X]** | Exact finite counterexample or exact finite witness. |
| **[B]** | Bounded exhaustive or seeded computation; evidence, not a universal proof. |
| **[E]** | Observation from the current `pid-rs` executable path. |
| **[O]** | Open question or unproved extension. |

The audit used the following process.

1. Freeze the paper-defined primitive before considering axioms or implementations.
2. Derive the lattice and reconstruction equations directly from events.
3. Separate constitutive semantics from numerical theorems.
4. Search for the smallest exact counterexample to every stronger interpretation.
5. Enumerate bounded empirical laws with exact rational arithmetic.
6. Run the same witnesses through an implementation-distinct Rust route.
7. Apply a compatibility firewall before importing any result from another PID framework.
8. Review each major result through at least five lenses:
   definitional compatibility, theorem validity, executable refinement, numerical/statistical
   implications, and adversarial counterexamples.

### 1.1 Five-lens result ledger

| Result | SxPID definitional compatibility | Theorem and assumptions | Executable refinement | Numerical/statistical implication | Adversarial finding |
|---|---|---|---|---|---|
| F1. Keyed event and local cumulative | Native definition | Valid on supported finite keys | Rust scans exact equality events | Rare events create large logs | Unsupported keys cannot be assigned a local value |
| F2. Antichain order and Möbius inversion | Native definition | Finite-poset inversion is exact | 2--4 source lattices implemented | Cancellation can amplify rounding | Reconstruction identities must be tested, not inferred from labels |
| F3. Nonnegative component atoms | Native published theorem | Applies separately to $+$ and $-$, not net atoms | Exact bounded checks agree | Interval signs should be reported near zero | Negative net atoms occur exactly |
| F4. Averaging and MI reconstruction | Native definition | Linearity plus greatest-node self-redundancy | Rust reconstructs all exact witnesses | Average is not MI of one fixed keyed event | Lyu witness is reconstructed despite its cross-target relation |
| F5. Symmetry, REI, and target chain rule | Native properties | Coordinatewise bijections only; target chain uses conditional law | Relabeling and lattice tests exist | Finite precision should preserve only within error bounds | Joint source mixing and coarse-graining are outside REI |
| F6. Identity and local positivity | Comparison properties, not Sx axioms | Sx rejects both in general | Exact COPY and target-copy cases reproduce failures | Signed inference is required | Independent sources have positive redundancy; a net unique atom is negative |
| F7. Disjunction as shared knowledge | Native semantic postulate | Logical consequence theorem is valid; statistical interpretation is a choice | Code evaluates the chosen disjunction exactly | Different semantics would define another estimand | No theorem makes the choice unique among all PID meanings |
| F8. Common deterministic signal | Incompatible stronger semantics | Not implied by Sx | No common-variable object is computed | Users must not label Sx as Gács--Körner common information | Independent COPY has positive Sx redundancy but only a constant common deterministic statistic |
| F9. Role and processing behavior | Native Sx values; stronger symmetry/DPI incompatible | Source--target asymmetry is built in | Exact witnesses are executable | Preprocessing changes the estimand and atom signs | Exact role-swap and coarse-graining counterexamples |
| F10. Identifiability and estimation | Native population functional needs full joint law | Finite-law identifiability is valid | Plug-in estimator uses empirical joint PMF | Sparse high-cardinality laws are difficult | Same pairwise marginals can have different Sx redundancy |
| F11. Lyu--Clark--Raviv impossibility claim | Their stipulated atoms are not Sx atoms | Internal descriptor theorem is valid; universal PID wording is overbroad | Tracked test rejects descriptor substitution | Cross-component relations change Sx atoms | Their two systems have 8 exactly different Sx atoms and reconstruct 3 vs 2 bits |
| F12. Downstream scientific interpretation | Sx can be an advisory statistic | No causal or authority theorem follows | Reports must carry assumption and estimand identity | UQ and model selection remain separate | Observationally equivalent causal systems defeat causal attribution |

---

## 2. Compatibility firewall

No external theorem is treated as a theorem about shared exclusions until its objects and
assumptions are shown to match the definitions in Section 3.

| Source or concept | Compatibility with categorical SxPID | Permitted use in this audit | Forbidden transplant |
|---|---|---|---|
| Makkeh, Gutknecht, and Wibral (2021) | **Native** | Definition, lattice cumulatives, component split, target chain rule, differentiability | None, subject to the paper's stated finite-discrete and interior-domain conditions |
| Gutknecht, Wibral, and Makkeh (2021) | **Native conceptual foundation** | Parthood and formal-logic indexing; constitutive principles | Treating the constitutive principles as uniquely forced Shannon theorems |
| Matthias, Makkeh, Wibral, and Gutknecht (2025) | **Compatible abstract PID theorem** | LP--TCR--REI and LP--ID--REI incompatibilities; Sx trade-off classification | Calling the incompatibility a defect unique to SxPID |
| Lyu, Clark, and Raviv (2026), Definition 6/Lemma 4 | **Incompatible atom semantics** | Comparison of coordinate-recoverability descriptors and relation loss | Calling $H(U_\alpha)$ the SxPID atom or transferring their reconstruction impossibility to SxPID |
| Williams--Beer identity/local positivity desiderata | **Comparison-only properties** | State what Sx accepts or rejects | Redefining Sx after observing a violation |
| Dependency coloring | **Estimator-layer only** | Concentration under a proved within-color independence contract | Calling it a new “colored PID” measure or attributing it to the Sx definition |
| `pid-rs` categorical kernel | **Executable approximation to the native definition** | Implementation evidence and regression testing | Treating passing tests as a proof of the semantic postulate or all real arithmetic |
| Support-change continuity theorem in this repository | **Project theorem about native averaged SxPID** | Closed-simplex continuity of averaged finite-alphabet quantities | Attributing it to the 2021 paper or applying it to disappearing pointwise keys |

This firewall resolves the most serious new challenge. Lyu--Clark--Raviv prove a result about a
vector of stipulated recoverability descriptors. Their vector is not the Möbius inversion of the
shared-exclusions cumulatives. The two constructions answer different questions.

---

## 3. The primitive, reconstructed from first principles

### 3.1 Finite sample space and keyed events

Let

$$
Z=(S_1,\ldots,S_n,T)
$$

have a probability law $p$ on a finite Cartesian-product alphabet. Fix a supported realization

$$
z=(s_1,\ldots,s_n,t),\qquad p(z)>0.
$$

For each nonempty source collection $a\subseteq[n]$, define the matching event

$$
E_a(s)=\bigcap_{i\in a}\{S_i=s_i\}.
$$

For an antichain $\alpha=\{a_1,\ldots,a_m\}$, define the inclusive disjunction

$$
A_\alpha(s)=\bigcup_{a\in\alpha}E_a(s).
\tag{1}
$$

Every branch $E_a(s)$ contains the keyed source realization. Hence $A_\alpha(s)$ contains it,
and

$$
p(A_\alpha)>0,
\qquad
p(T=t,A_\alpha)>0.
$$

The pointwise cumulative is

$$
c_\alpha(z;p)
=
\log\frac{p(T=t,A_\alpha)}{p(T=t)p(A_\alpha)}
=
\log\frac{p(T=t\mid A_\alpha)}{p(T=t)}.
\tag{2}
$$

This is an ordinary local likelihood ratio for the truth of the *keyed* event $A_\alpha(s)$.
It is not yet an atom.

The informative and misinformative components are

$$
c_\alpha^+(z;p)=-\log p(A_\alpha),
\qquad
c_\alpha^-(z;p)=\log\frac{p(T=t)}{p(T=t,A_\alpha)},
\tag{3}
$$

so that

$$
c_\alpha=c_\alpha^+-c_\alpha^-.
\tag{4}
$$

Both components are nonnegative because $p(A_\alpha)\le1$ and
$p(T=t,A_\alpha)\le p(T=t)$. The net value can have either sign.

**Finding F1 [P,R].** Equations (1)--(4) are well-defined for every supported finite key. The
mathematics does not assign a pointwise value to a realization that has zero probability.

### 3.2 Antichain order

For antichains $\alpha,\beta$, define

$$
\alpha\preceq\beta
\quad\Longleftrightarrow\quad
\forall b\in\beta\;\exists a\in\alpha:\;a\subseteq b.
\tag{5}
$$

If $a\subseteq b$, then $E_b(s)\subseteq E_a(s)$. Therefore

$$
\alpha\preceq\beta
\quad\Longrightarrow\quad
A_\beta(s)\subseteq A_\alpha(s).
\tag{6}
$$

It follows directly that both $c^+$ and $c^-$ increase along the lattice. Their difference need
not increase.

### 3.3 Möbius atoms and exact reconstruction

Define the pointwise atoms by the finite-poset zeta relation

$$
c_\alpha^u(z;p)
=
\sum_{\beta\preceq\alpha}\pi_\beta^u(z;p),
\qquad
u\in\{+, -, \mathrm{net}\},
\tag{7}
$$

where $\pi^{\mathrm{net}}=\pi^+-\pi^-$. Finite-poset Möbius inversion makes Equation (7)
unique once all cumulatives have been fixed.

The greatest antichain is $\{[n]\}$. Its event is the complete source realization:

$$
A_{\{[n]\}}(s)=\{S_1=s_1,\ldots,S_n=s_n\}.
$$

Thus

$$
c_{\{[n]\}}(z;p)
=
\log\frac{p(t\mid s_1,\ldots,s_n)}{p(t)}
=
i(s_1,\ldots,s_n;t).
\tag{8}
$$

Summing every pointwise net atom therefore gives local mutual information. Define averaged atoms

$$
\Pi_\beta^u(p)=\sum_{z:p(z)>0}p(z)\pi_\beta^u(z;p).
\tag{9}
$$

Linearity of the finite sum gives

$$
\sum_\beta\Pi_\beta^{\mathrm{net}}(p)
=
I(S_1,\ldots,S_n;T).
\tag{10}
$$

**Finding F2 [P,R].** The reconstruction is an algebraic theorem about the distribution-dependent
cumulatives. It does not assume that atoms are statistically independent target coordinates.

### 3.4 What is actually nonnegative

Makkeh--Gutknecht--Wibral prove

$$
\pi_\beta^+(z;p)\ge0,
\qquad
\pi_\beta^-(z;p)\ge0
\tag{11}
$$

for every supported key. Equation (11) does **not** imply

$$
\pi_\beta^{\mathrm{net}}(z;p)\ge0
\quad\text{or}\quad
\Pi_\beta^{\mathrm{net}}(p)\ge0.
$$

The signed atom is the balance of a nonnegative informative increment and a nonnegative
misinformative increment.

Independent exact-rational checks in this audit found no counterexample to Equation (11):

- all 12,869 binary two-source empirical count tables with total count $1\le N\le8$, covering
  51,480 supported keys and all four atoms;
- all 4,844 binary three-source empirical count tables with $1\le N\le4$, covering 15,504
  supported keys and all 18 atoms;
- 40 seeded binary four-source count tables, covering 1,060 supported keys and all 166 atoms.

The first two searches were exhaustive within their stated bounds. The four-source search used
seed `1398296644`. Every comparison was performed on exact rational ratios before applying a
logarithm. These computations support the theorem but do not replace its proof.

**Finding F3 [P,B].** No component-sign flaw was found. A claim that the *net* atoms are all
nonnegative would be false.

---

## 4. Which semantics is being chosen?

### 4.1 The valid logical fact

For propositions $A_1,\ldots,A_m$, a proposition $C$ follows from every $A_i$ if and only if
it follows from their disjunction:

$$
(\forall i,\;A_i\models C)
\quad\Longleftrightarrow\quad
(A_1\lor\cdots\lor A_m)\models C.
\tag{12}
$$

This is a valid theorem of classical propositional logic. The disjunction is the strongest
proposition, up to logical equivalence, that is implied by every branch.

### 4.2 The constitutive step

Shared exclusions then identifies “information shared by the source statements” with the
likelihood-ratio information carried by the truth of that disjunction. That move is coherent, but it
is a semantic postulate. It is not derived uniquely from the Shannon axioms.

The parthood and logic paper makes the constitutive structure explicit:

- atoms are indexed by access/parthood patterns;
- non-atomic quantities are sums of their atoms;
- redundancy is the part common to specified source collections;
- statement-level commonality is represented by disjunction.

The isomorphism among parthood distributions, antichains, and logical statements establishes an
indexing structure. It does not prove that every scientifically useful notion of redundancy must use
Equation (2).

**Finding F7 [P,R].** The logic is sound. The uniqueness of the statistical meaning is not a
theorem. “Shared exclusions exactly captures shared information” is correct only after the
shared-logical-consequence semantics has been accepted.

### 4.3 Key dependence and the absence of one fixed auxiliary variable

The event $A_\alpha(s)$ depends on the complete realized source key $s$. At another source
realization $s'$, the formula changes. Consequently, the average in Equation (9) uses weights
$p(s,t)$ while changing the auxiliary event with $s$. It is not generally of the form

$$
I(W;T)
$$

for one fixed random variable $W$.

This is not a hidden defect; the 2021 paper states it. It also rules out two naive channel
interpretations and supplies a specially masked channel interpretation. Any downstream use that
speaks of a fixed “shared signal” must supply an additional construction and prove equivalence.

### 4.4 No nonconstant common deterministic signal in independent COPY

Let $S_1,S_2$ be independent fair bits and $T=(S_1,S_2)$. The Sx bottom redundancy is

$$
\Pi_{\{\{1\},\{2\}\}}^{\mathrm{net}}
=
\log\frac43>0.
\tag{13}
$$

Suppose a random variable $U$ were deterministically available from each source:

$$
U=f_1(S_1)=f_2(S_2)\quad\text{almost surely}.
$$

Because $S_1$ and $S_2$ are independent, $f_1(S_1)$ and $f_2(S_2)$ are independent. If
they are equal almost surely, then $U$ is independent of itself. For every value $u$,

$$
\Pr(U=u)=\Pr(U=u)^2,
$$

so every probability is zero or one and $U$ is constant. Hence $I(U;T)=0$, while Equation
(13) is positive.

**Finding F8 [X].** Sx redundancy is not Gács--Körner common information, common deterministic
content, or the entropy of a nonconstant statistic locally computable from every independent
source. Its “shared knowledge” is keyed and event-logical.

---

## 5. Exact axiomatic trade-offs

### 5.1 Coordinatewise re-encoding invariance

Let each source be relabeled by a bijection $f_i$ and the target by a bijection $g$. Equality
events are preserved:

$$
S_i=s_i
\quad\Longleftrightarrow\quad
f_i(S_i)=f_i(s_i).
$$

All probabilities in Equations (1)--(3) are unchanged. Therefore every cumulative and atom is
unchanged up to the corresponding source-label permutation.

This proves re-encoding invariance for coordinatewise bijections. A joint invertible map that mixes
two source variables changes the source partition and is not covered by this result.

### 5.2 Target chain rule

For $T=(T_1,T_2)$, a fixed keyed source event $A$ gives

$$
\log\frac{p(t_1,t_2\mid A)}{p(t_1,t_2)}
=
\log\frac{p(t_1\mid A)}{p(t_1)}
+
\log\frac{p(t_2\mid t_1,A)}{p(t_2\mid t_1)}.
\tag{14}
$$

The same identity propagates through linear Möbius inversion and averaging, using the ordinary
conditional-distribution definition for the second term.

### 5.3 Exact identity failure

For independent fair bits $S_1,S_2$ and $T=(S_1,S_2)$, each key has

$$
p(A)=\frac34,
\qquad
p(t)=\frac14,
\qquad
p(t,A)=\frac14.
$$

Therefore the bottom cumulative and atom are

$$
R_{\mathrm{sx}}=\log\frac{1/4}{(3/4)(1/4)}=\log\frac43.
$$

The complete two-source atoms are

$$
(R,U_1,U_2,\mathrm{Syn})
=
\left(
\log\frac43,
\log\frac32,
\log\frac32,
\log\frac43
\right),
\tag{15}
$$

whose sum is $\log4=I(S_1,S_2;T)$.

Identity-style redundancy would set $R=I(S_1;S_2)=0$. Shared exclusions deliberately answers a
different question.

### 5.4 Exact local-positivity failure

Use the same independent fair bits, but take $T=S_2$. Direct evaluation gives

$$
(R,U_1,U_2,\mathrm{Syn})
=
\left(
\log\frac43,
-\log\frac43,
\log\frac32,
\log\frac43
\right).
\tag{16}
$$

The negative atom has the exact component split

$$
U_1^+=\log\frac32,
\qquad
U_1^-=\log2,
\qquad
U_1=U_1^+-U_1^-=-\log\frac43.
\tag{17}
$$

Thus component nonnegativity and net local positivity are different properties.

### 5.5 The Matthias--Makkeh--Wibral--Gutknecht incompatibility

Their 2025 theorem shows that no general discrete antichain PID can satisfy all of:

1. net-atom local positivity (LP);
2. target chain rule (TCR); and
3. coordinatewise invertible re-encoding invariance (REI).

The exact rederivations above place SxPID as follows:

| Property | SxPID | Direct reason |
|---|---:|---|
| REI | yes | Equality events and probabilities survive coordinatewise bijections. |
| TCR | yes | Equation (14). |
| LP | no | Equation (16). |
| identity | no | Equation (15). |
| more than two sources | yes | Full finite antichain construction. |

**Finding F6 [P,R,X,E].** The incompatibility is a structural trade-off, not an unnoticed defect.
SxPID preserves TCR and REI and accepts signed net atoms. Any claim that it also has universal net
local positivity is false.

### 5.6 XOR-source-copy executable witness

Let $S_1,S_2$ be independent fair bits, $S_3=S_1\oplus S_2$, and
$T=(S_1,S_2,S_3)$. Then $I(S_1,S_2,S_3;T)=2\log2$. The current Rust kernel returns the
following nonzero net atoms:

$$
\begin{aligned}
\Pi_{\{\{1\},\{2\}\}}
=\Pi_{\{\{1\},\{3\}\}}
=\Pi_{\{\{2\},\{3\}\}}
&=\log\frac43,\\
\Pi_{\{\{1\},\{23\}\}}
=\Pi_{\{\{2\},\{13\}\}}
=\Pi_{\{\{3\},\{12\}\}}
&=\log\frac98,\\
\Pi_{\{\{12\},\{13\},\{23\}\}}
&=\log\frac{32}{27}.
\end{aligned}
\tag{18}
$$

All other atoms are zero in this symmetric witness, and the exact product identity is

$$
\left(\frac43\right)^3
\left(\frac98\right)^3
\frac{32}{27}
=4.
$$

Thus the atoms sum to $\log4$. The witness does not itself make every unconditional atom
negative. The incompatibility is universal across all targets and conditional decompositions, not a
claim that every one of its witness decompositions must display a negative atom.

---

## 6. Exact counterexample ledger

### 6.1 Negative redundancy in XOR

Let $S_1,S_2$ be independent fair bits and $T=S_1\oplus S_2$. For every supported key,

$$
p(A)=\frac34,
\qquad
p(t)=\frac12,
\qquad
p(t,A)=\frac14.
$$

Therefore

$$
R_{\mathrm{sx}}=\log\frac23<0.
\tag{19}
$$

The complete atom vector is

$$
\left(
\log\frac23,
\log\frac32,
\log\frac32,
\log\frac43
\right),
$$

which sums to $\log2$. This is not an arithmetic failure; it is the signed
informative-minus-misinformative semantics.

### 6.2 Full-joint dependence, not pairwise identifiability

Compare two laws:

- XOR: $S_1,S_2$ independent fair bits and $T=S_1\oplus S_2$;
- independence: $S_1,S_2,T$ are three independent fair bits.

Both laws have the same pairwise marginals $(S_1,T)$ and $(S_2,T)$: each is uniform and
independent. Yet

$$
R_{\mathrm{sx}}^{\mathrm{XOR}}=\log\frac23,
\qquad
R_{\mathrm{sx}}^{\mathrm{independent}}=0.
\tag{20}
$$

**Finding F10 [X].** SxPID is a functional of the full joint distribution. Pairwise mutual
informations or pairwise source--target marginals do not identify it.

### 6.3 Adding an irrelevant source changes net redundancy

Add an independent fair bit $S_3$ to the XOR system, with the target still
$T=S_1\oplus S_2$. The bottom three-source event has

$$
p(A)=\frac78,
\qquad
p(t,A)=\frac38,
$$

so

$$
R_{\mathrm{sx}}(S_1,S_2,S_3\to T)=\log\frac67.
\tag{21}
$$

This is larger than $\log(2/3)$, although the third source is independent and unused by the
target. The two nonnegative cumulant components both decrease as the disjunction expands; their
difference increases. A naive monotonicity rule for the net value is therefore invalid.

### 6.4 Exact source--target role asymmetry

Give equal probability to the three rows

$$
(S_1,S_2,T)\in\{(0,1,1),(1,0,0),(1,1,1)\}.
$$

For the ordinary direction,

$$
R_{\mathrm{sx}}(S_1,S_2\to T)
=
\frac13\log\frac94.
\tag{22}
$$

After exchanging $S_1$ and $T$, while retaining $S_2$ as the other source,

$$
R_{\mathrm{sx}}(T,S_2\to S_1)
=
\frac13\log\frac{27}{16}.
\tag{23}
$$

Their exact difference is

$$
\frac13\log\frac43>0.
$$

**Finding F9a [X].** PID is target-directed. Mutual-information symmetry does not make a PID
invariant under exchanging a source and the target.

### 6.5 No net atom data-processing law under coarse-graining

Start with independent fair $S_1,S_2$ and COPY target $T=(S_1,S_2)$. Deterministically
coarsen the target to $T'=S_1\oplus S_2$, and then to a constant. The bottom redundancy follows

$$
\log\frac43
\quad\longrightarrow\quad
\log\frac23
\quad\longrightarrow\quad
0.
\tag{24}
$$

The first processing step changes the sign. The second destroys all target information but
increases the signed redundancy from a negative number to zero.

Alternatively, in the XOR system coarsen one source to a constant. Its source event is then always
true, and the bottom redundancy changes from $\log(2/3)$ to zero.

**Finding F9b [X].** Mutual information obeys data processing. Individual signed SxPID atoms do
not inherit a universal data-processing inequality. Preprocessing must be treated as an estimand
change.

---

## 7. The 2026 “structural impossibility” challenge

### 7.1 Exact witness pair

Lyu--Clark--Raviv, arXiv:2604.03869v2 (14 April 2026), define two systems.

For the **hat system**, let

$$
x_1,x_2,x_4,x_5,x_7,x_8\stackrel{\mathrm{iid}}\sim\mathrm{Bernoulli}(1/2),
$$

and set

$$
x_3=x_1\oplus x_2,
\quad
x_6=x_4\oplus x_5,
\quad
x_9=x_7\oplus x_8.
$$

For the **tilde system**, let

$$
x_1,x_2,x_4,x_5,x_7\stackrel{\mathrm{iid}}\sim\mathrm{Bernoulli}(1/2),
$$

and set

$$
x_3=x_1\oplus x_2,
\quad
x_6=x_4\oplus x_5,
\quad
x_9=x_1\oplus x_5,
\quad
x_8=x_7\oplus x_1\oplus x_5.
$$

In both systems,

$$
S_1=(x_1,x_4,x_7),
\quad
S_2=(x_2,x_5,x_8),
\quad
S_3=(x_3,x_6,x_9),
\quad
T=(x_1,x_5,x_9).
\tag{25}
$$

The hat system has 64 equiprobable latent states and three independent target bits:

$$
I(\widehat S;\widehat T)=H(\widehat T)=3\log2.
$$

The tilde system has 32 equiprobable latent states and the target relation
$x_9=x_1\oplus x_5$:

$$
I(\widetilde S;\widetilde T)=H(\widetilde T)=2\log2.
$$

### 7.2 What their Definition 6 assigns

Each target coordinate has the same minimal recovering antichain in both systems:

$$
\alpha(x_1)=\{\{1\},\{23\}\},
\quad
\alpha(x_5)=\{\{2\},\{13\}\},
\quad
\alpha(x_9)=\{\{3\},\{12\}\}.
\tag{26}
$$

Their Lemma 4 stipulates

$$
\Pi(\alpha)=H(U_\alpha).
\tag{27}
$$

It therefore assigns one bit to each of the three labels in Equation (26) and zero to every other
label, in both systems.

The crucial observation is immediate. In the tilde system those three one-bit coordinates are not
independent. Their stipulated values sum to three bits, while the target has only two bits. Thus the
vector in Equation (27) is a recoverability descriptor vector, not a whole-equals-sum-of-parts PID
of $I(S;T)$.

The final step of their Lemma 4 proof says that the atom value is “assigned” as $H(U_\alpha)$.
No Möbius inversion of a Sx cumulative appears. No argument makes the $U_\alpha$ independent
across different labels. Theorem 1 is valid on its explicitly stated Definition 6 domain: the two
witness laws have the same complete descriptor vector and unequal mutual information, so no single
map from that vector reconstructs mutual information for every law in that domain. Marginal
component entropies and access labels do not encode the witness's cross-coordinate relation.

### 7.3 Exact SxPID result

Shared exclusions does not assign the stipulated vector. A separate exact event scan and the
current Rust kernel both give the following eight nonzero net atoms.

| Antichain family | Hat SxPID atom | Tilde SxPID atom |
|---|---:|---:|
| $\{\{1\},\{2\},\{3\}\}$ | $\log(16/11)$ | $\log(8/5)$ |
| each of $\{\{1\},\{2\}\},\{\{1\},\{3\}\},\{\{2\},\{3\}\}$ | $\log(11/10)$ | $\log(15/14)$ |
| each of the three labels in Equation (26) | $\log(25/22)$ | $\log(49/45)$ |
| $\{\{12\},\{13\},\{23\}\}$ | $\log(352/125)$ | $\log(540/343)$ |

The other ten atoms are zero in each system. The exact product reconstructions are

$$
\frac{16}{11}
\left(\frac{11}{10}\right)^3
\left(\frac{25}{22}\right)^3
\frac{352}{125}
=8,
\tag{28}
$$

and

$$
\frac85
\left(\frac{15}{14}\right)^3
\left(\frac{49}{45}\right)^3
\frac{540}{343}
=4.
\tag{29}
$$

After taking logs, Equations (28) and (29) give $3\log2$ and $2\log2$, respectively.
Exactly 8 of 18 net atoms differ; 10 agree exactly. The maximum atom difference is

$$
\log\frac{352/125}{540/343}
\approx0.58147874590342\ \text{nats}
=0.83889650309719\ \text{bits}.
$$

The informative and misinformative ratios are also exact. For example, the three recovery-label
atoms have

$$
\widehat\Pi^+=\log\frac{225}{176},
\quad
\widehat\Pi^-=\log\frac98,
$$

whereas

$$
\widetilde\Pi^+=\log\frac{49}{40},
\quad
\widetilde\Pi^-=\log\frac98.
$$

The relation changes the informative increments even though the minimal recoverability labels are
unchanged.

### 7.4 Correct scope of the impossibility result

**Valid theorem on the stated Definition 6 domain [P,R]:** the exhibited laws have equal complete
vectors $(H(U_\alpha))_\alpha$ and unequal mutual information. Therefore no single function of
that descriptor vector reconstructs mutual information for every law in that domain.

**Not established [X,E]:** that two distributions have the same SxPID atoms, or that SxPID cannot
reconstruct their mutual information.

#### Descriptor-factorization firewall

The transfer condition can be stated without PID terminology. Let $D(P)$ be a descriptor vector,
$A(P)$ an atom vector, and $J(P)$ the quantity to be reconstructed. Suppose the atom assignment
factors through the descriptors:

$$
A=g\circ D.
\tag{30}
$$

If two systems satisfy

$$
D(P)=D(Q),
\qquad
J(P)\ne J(Q),
\tag{31}
$$

then $A(P)=A(Q)$, so no function $f$ can satisfy $f(A(R))=J(R)$ for every system $R$.
Conversely,

$$
D(P)=D(Q),
\qquad
A(P)\ne A(Q)
\quad\Longrightarrow\quad
\nexists g\; A=g\circ D.
\tag{32}
$$

This is the exact logical firewall. The Lyu--Clark--Raviv witness proves a reconstruction
impossibility for atom assignments that accept Equation (30), with their recoverability-label and
component-entropy descriptor. It does not transfer to an atom assignment merely because that
assignment is indexed by the same antichain lattice. A separate theorem must establish Equation
(30) for that assignment.

The SxPID calculation supplies the converse witness in Equation (32): the two systems have the same
stipulated recoverability descriptors but eight different Sx atoms. Therefore SxPID does not factor
through that descriptor map. This does not make the descriptor theorem false. It shows that the
operative premise is descriptor sufficiency, not antichain indexing alone.

The generic argument is kernel-checked in
[`audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean`](audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean).
It contains three axiom-free theorems: descriptor factorization forces equal atoms; a descriptor
collision with unequal target quantities blocks universal reconstruction; and an atom distinction
at a descriptor collision refutes factorization. The pinned checker and a three-mutation fail-closed
suite, augmented by three kernel-checked finite premise countermodels, are
[`scripts/check-lean-descriptor-factorization.py`](scripts/check-lean-descriptor-factorization.py)
and
[`scripts/check-lean-descriptor-factorization-self-test.py`](scripts/check-lean-descriptor-factorization-self-test.py).
Their deterministic records are stored in
[`audit/evidence/foundational-sxpid-descriptor-factorization-lean-4.33.0.json`](audit/evidence/foundational-sxpid-descriptor-factorization-lean-4.33.0.json)
and
[`audit/evidence/foundational-sxpid-descriptor-factorization-mutations-4.33.0.json`](audit/evidence/foundational-sxpid-descriptor-factorization-mutations-4.33.0.json).
The checker binds the theorem source, Lake manifest/configuration, toolchain identifier, and
reported Lean version. These are reproducibility checks, not an authenticity or binary-attestation
claim about the installed Lean/mathlib toolchain.

Phrases such as “regardless of any axioms” and “rules out any multivariate information
decomposition that relies solely on the antichain lattice” are therefore safe only when read with
the descriptor-factorization premise explicit. Distribution-dependent signed Möbius atoms,
including SxPID, do not accept that premise in this witness.

**Preserved insight:** antichain access labels alone do not store all relations among semantically
named target components. A future relation-aware representation may be useful as metadata or a
second analytical layer. It must not replace Sx atoms with nonadditive coordinate entropies and
still call the result a decomposition of mutual information.

### 7.5 Three complementary, implementation-distinct but correlated lanes

The tracked negative regression is
[`crates/pid-core/tests/sxpid_relation_witness.rs`](crates/pid-core/tests/sxpid_relation_witness.rs).
It contains both the exact rational-product oracle and a mutation that substitutes the stipulated
three-one-bit descriptor vector. The mutation is rejected because it is not SxPID and fails tilde
reconstruction.

The standard-library Python lane is
[`audit/tools/foundational_sxpid/check_lcr_relation_witness.py`](audit/tools/foundational_sxpid/check_lcr_relation_witness.py).
It does not import or invoke `pid-rs`. It generates all 18 antichains from the seven nonempty
three-source subsets and performs the later exact Möbius inversion in formal prime-exponent
logarithms. Before that Sx calculation, it binds the generated rows to the
paper's fair-bit/XOR constructions and verifies the Definition 6 finite-law premises: exactly the
indices $1,5,9$ are determined by the target; each source's three latent components are mutually,
not merely pairwise, independent; and every one of the 24 target-component/source-group cases per
system is either exactly recoverable or exactly independent. It then derives the three minimal
recovering antichains, computes every Lemma 4 descriptor entropy from the rows, and proves equality
of the two complete 18-coordinate descriptor vectors. Finally, it independently derives the 8/18
Sx atom differences and exact MI products 8 and 4. It also verifies that every local component atom
is constant over each equiprobable support, which is the premise needed to identify the displayed
local ratios with the averaged ratios in this special witness.

The checker kills three negative mutations:

1. inclusive union replaced by intersection;
2. the three row-derived one-bit Lemma 4 descriptors substituted for SxPID atoms; and
3. the tilde cross-coordinate relation changed.

Its complete deterministic record is
[`audit/evidence/foundational-sxpid-lcr-exact-audit.json`](audit/evidence/foundational-sxpid-lcr-exact-audit.json).
That record binds the checker, row generators, Rust regression, and Rust kernel by SHA-256. At the
original 2026-07-25 audit, the checker digest was
`8244bd6a3a3a590f8a8da9f63ce5d5114d3453cb4623bde70ce02c7ddbeec96a`, the Rust regression digest
was `e11076dfd0bc8e8b3f3565128ed87c2cabe03c0f25b966e76fe925a09e3451ed`, and the audited kernel
digest was `f08b56bac473474b39dd2cf2f09c5d13ccda025825a011ee1870f6f2979ff98a`. The current record was
regenerated after later same-sample custody work and binds kernel digest
`00d3eaecd5517fe0f36b54d576b77a79beb1424f795847a7ed8a1155aabb3ef6`. Every other record byte is
unchanged. This source-binding refresh does not widen or re-adjudicate the audit claim.

The formal lane is the generic Lean factorization firewall above. Its proof has no axioms in the
Lean kernel inventory. The self-test kills removal of the factorization premise, replacement of the
unequal-quantity premise by equality, and replacement of the unequal-atom premise by equality.
Separate finite Bool/Unit countermodels show why each altered premise cannot support the original
conclusion: equal descriptors alone need not equalize atoms, equal quantities can admit a universal
reconstruction, and equal atoms can admit descriptor factorization.
This lane proves only the conditional transfer logic, not the concrete Sx event calculation; the
Python exact-rational and Rust lanes compute that concrete witness. All three lanes still depend on
reviewed semantic cuts that connect the published constructions, descriptor map, Sx definitions,
and tested conclusion. They are implementation-distinct corroboration, not independent proofs of
one end-to-end statement.

**Finding F11 [P,R,X,E].** The 2026 witness is a genuine warning against treating access labels plus
marginal component entropies as a complete representation. It is not a contradiction of
shared-exclusions PID.

---

## 8. Support, continuity, and estimation

### 8.1 Pointwise boundary behavior

For a supported key, every event probability in Equation (2) is positive. If the key disappears
from support, the corresponding local value no longer has an operational occurrence on which to be
evaluated. Along a rare-key sequence, local values can diverge like $-\log p(z)$.

The 2021 differentiability theorem concerns the interior of a fixed finite probability simplex. It
does not state pointwise continuity for disappearing keys.

### 8.2 Averaged closed-simplex behavior

The repository's separate project theorem proves that, on one fixed finite Cartesian-product
alphabet, the support-restricted averaged cumulatives and full-lattice atoms extend continuously
across support changes. The small probability weight controls the diverging local log. This does not
make the pointwise quantity continuous.

The distinction is:

$$
\text{rare-key local value may diverge}
\quad\text{while}\quad
p(z)\,\pi_\alpha(z;p)\to0.
$$

### 8.3 Population identifiability versus sample reliability

For a known finite alphabet, the population SxPID is identified by the full joint law. A plug-in
estimator replaces that law by empirical cell frequencies. Consistency under a fixed finite alphabet
does not provide all of the following:

- a useful finite-sample rate for an unknown sparse law;
- support discovery;
- protection against adaptive quantization;
- valid inference after model or feature selection;
- dependence-robust uncertainty without a proved sampling contract;
- a binary64 sign certificate near cancellation;
- or causal identification.

The joint alphabet grows multiplicatively with sources, source cardinalities, and target
cardinality. Antichain counts also grow rapidly: 18 nodes for three sources and 166 for four.
Scientific use should therefore report at least:

1. the fixed estimand and source partition;
2. observed and declared alphabet sizes;
3. support occupancy and rare-cell sensitivity;
4. sampling/dependence assumptions;
5. preprocessing fit/evaluation separation;
6. informative and misinformative components;
7. numerical sign or tie uncertainty;
8. reconstruction residuals;
9. sensitivity to sample size and quantization;
10. an explicit noncausal interpretation boundary.

**Finding F4/F10 [R].** Exact-real continuity and plug-in consistency establish mathematical
stability in a fixed regime. They do not establish practical calibration in every downstream data
regime.

---

## 9. Interpretive and causal limits

### 9.1 What a positive or negative atom supports

A local net atom is an increment in a likelihood ratio after Möbius subtraction. Its sign says
whether the increment's informative component exceeds its misinformative component under the Sx
event semantics. The averaged sign is the probability-weighted balance of those local increments.

It does not, without additional assumptions, mean:

- beneficial or harmful mechanism;
- redundancy or synergy in a causal structural equation;
- correct or incorrect sensor;
- deception or intent;
- replaceability of a subsystem;
- robustness to intervention;
- safety margin;
- or probability that a decision is correct.

### 9.2 Observational equivalence blocks causal attribution

SxPID is a functional of an observational joint distribution. Distinct causal graphs can induce the
same joint law, and hence the same SxPID. No statistic of that law alone can distinguish those
graphs without additional causal assumptions or interventions.

### 9.3 Decision use requires an external loss model

The paper's pointwise operational interpretation concerns Bayesian prediction from a specially
constructed, metadata-masked event channel. A real decision system also needs:

- a declared action set and loss function;
- calibration under the deployment distribution;
- a sequential error policy if repeatedly monitored;
- drift and out-of-distribution rules;
- and explicit abstention behavior.

SxPID can be evidence inside such a system. It is not itself an authorization rule.

**Finding F12 [R].** Causal or authority-grade conclusions are an interpretive overreach unless a
separate theorem connects the observational Sx estimand to the required intervention or decision
quantity.

---

## 10. Validity regime contract

### 10.1 Regime in which categorical SxPID is a defensible estimand

Use categorical SxPID when all of the following are true.

- Variables and the target are categorical, or quantization is a separately declared estimand.
- The source partition has scientific meaning and is fixed before evaluation.
- The objective is explicitly shared logical-exclusion information.
- Signed net atoms are acceptable and informative/misinformative parts are retained.
- The full joint distribution is estimable in the declared sampling regime.
- Dependence, drift, and selection are handled by separate valid procedures.
- Numerical cancellation and reconstruction are checked.
- Interpretation remains observational unless a causal bridge is separately justified.

### 10.2 Regime in which another object is required

Do not present SxPID as the answer when the scientific question requires:

- a common deterministic random variable;
- only nonnegative additive pieces;
- identity-style redundancy;
- monotonicity under arbitrary local processing;
- a source--target symmetric quantity;
- a decomposition identified by pairwise marginals;
- causal contribution or intervention value;
- high-dimensional continuous PID without a valid estimator;
- or an authority-grade probability of correctness.

These are different mathematical requirements, not optional labels for the same output.

---

## 11. Formal-verification consequences

The foundational audit changes what should be proved. A formal development must not encode an
overstrong semantic claim as though it followed from the event algebra.

### 11.1 Exact specification layer

Formalize:

1. finite source and target alphabets;
2. supported keys and equality events;
3. source collections and antichains;
4. Equation (1) event unions;
5. Equations (2)--(4) cumulatives;
6. the order in Equation (5) and containment in Equation (6);
7. the concrete finite Möbius inversion;
8. greatest-node local-MI identity;
9. averaged reconstruction;
10. component nonnegativity;
11. coordinatewise re-encoding invariance;
12. target chain rule;
13. exact counterexamples to identity, LP, pairwise identifiability, and net data processing.

Counterexamples should be formal theorems, not comments. They prevent a later refactor from
silently strengthening the claim.

### 11.2 Executable refinement layer

Prove that:

- canonical row counting equals the empirical law;
- every event count equals its logical predicate;
- the Rust antichain order matches Equation (5);
- inversion reconstructs every cumulative;
- specialized and general source-count paths agree;
- exact integer count products cannot overflow inside their admitted domain;
- and reports preserve signed atoms and component identity.

### 11.3 Certified numerical layer

Exact counts give rational pre-log quantities. Directed-rounding intervals can certify every log,
sum, atom, and reconstruction. Report:

- certified positive;
- certified negative;
- or unresolved because the interval contains zero.

This is materially more faithful to signed Sx semantics than clamping negative values.

### 11.4 Semantic proof obligations

Keep these as explicit assumptions or rejected claims:

- **accepted:** disjunction represents shared logical consequence;
- **rejected:** disjunction is uniquely forced among all redundancy meanings;
- **rejected:** atoms are common deterministic target coordinates;
- **rejected:** net atoms are nonnegative set sizes;
- **rejected:** observational atoms are causal effects.

Formal verification can prove a precise model correct. It cannot make an unchosen scientific
semantics uniquely true.

---

## 12. Research directions that preserve correctness

### 12.1 Relation annotations, not replacement atoms **[O]**

The Lyu witness shows that access labels and marginal component entropies lose cross-component
relations. A safe extension is to attach relation invariants to a valid Sx decomposition as
metadata, while preserving Equation (10). Candidate annotations include target multi-information,
algebraic constraints, or explicitly declared factor graphs. They must not be added again as
ordinary atoms unless a new exact reconstruction theorem prevents double counting.

### 12.2 Characterize the semantic uniqueness class **[O]**

Determine the weakest explicit axioms under which disjunction is uniquely selected as the
statement-level common consequence. State clearly whether those axioms concern logic,
epistemology, decision theory, or Shannon information. This would replace the phrase “exactly the
shared information” with a falsifiable representation theorem.

### 12.3 Coarse-graining calculus for signed atoms **[O]**

No universal atomwise data-processing inequality exists. A useful replacement would classify
transformations under which:

- the keyed event sigma-algebra is preserved;
- atom families merge in a known way;
- signs are stable;
- or only the total mutual information is monotone.

Exact counterexamples in Section 6 should be retained as negative controls.

### 12.4 Operational validation of the masked event channel **[O]**

The published operational interpretation uses a specific channel that hides metainformation and
prevents learning across uses. Test whether realistic observers or algorithms actually receive that
information structure. If not, the application has changed the operational estimand.

### 12.5 Finite-sample signed certification **[O]**

Combine valid sampling concentration, closed-simplex continuity, and interval arithmetic to return
atom enclosures. Separate:

- model error;
- sampling error;
- preprocessing selection error;
- and numerical error.

One scalar “confidence score” should not collapse these logically different sources.

---

## 13. Final claim ledger

| Claim | Decision | Evidence |
|---|---|---|
| The Sx keyed cumulative is a valid local likelihood ratio | **Established** | [P,R] Equations (1)--(4) |
| The antichain atoms reconstruct mutual information | **Established** | [P,R,E] Equations (7)--(10), exact witnesses |
| Informative and misinformative component atoms are nonnegative | **Established; separately bounded-tested** | [P,B] |
| Net Sx atoms are nonnegative | **False** | [X,E] Equations (16), (17), and (19) |
| SxPID satisfies coordinatewise REI and target chain rule | **Established** | [P,R] Equation (14) and equality-event invariance |
| SxPID satisfies identity | **False** | [X,E] Equation (15) |
| Sx redundancy is common deterministic information | **False** | [X] Section 4.4 |
| Pairwise marginals identify Sx redundancy | **False** | [X] Equation (20) |
| Net atoms obey arbitrary source/target data processing | **False** | [X] Equation (24) |
| Source and target roles are interchangeable | **False** | [X] Equations (22), (23) |
| The disjunction semantics is logically coherent | **Established** | [P,R] Equation (12) |
| The disjunction semantics is uniquely forced by Shannon theory | **Not established** | Constitutive-semantic gap |
| Lyu's two systems have identical SxPID atoms | **False** | [X,E] Equations (28), (29) |
| Lyu's descriptor theorem exposes lost cross-coordinate relations | **Established within its stipulated model** | [P,R] |
| Descriptor-collision impossibility transfers to every antichain-indexed PID | **False without a descriptor-factorization theorem** | [P,R,X,E], Equations (30)--(32), Lean firewall |
| Lyu's theorem refutes all antichain-lattice PID, including SxPID | **Not established for SxPID** | Descriptor factorization fails; Python and Rust compute the witness, while Lean checks only the conditional firewall; all three lanes share reviewed semantic cuts |
| SxPID is causal or authority-grade by itself | **False/unsupported** | Observational identifiability boundary |
| Categorical SxPID is a defensible signed event-logical estimand | **Yes, under the regime contract** | Entire audit |

---

## 14. Reproducibility record

The executable witness was evaluated against repository commit
`6e29b3f5badc337a58eb821babc41641037e15d0`. At audit time,
`crates/pid-core/src/sxpid.rs` had SHA-256
`f08b56bac473474b39dd2cf2f09c5d13ccda025825a011ee1870f6f2979ff98a` and no local diff.
The environment was:

- `rustc 1.96.0 (ac68faa20 2026-05-25)`;
- `cargo 1.96.0 (30a34c682 2026-05-25)`;
- Python 3.14.6 for implementation-distinct exact-rational enumeration.

The permanent witness command is:

```text
python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py \
  --write-evidence audit/evidence/foundational-sxpid-lcr-exact-audit.json
cargo test --locked -p pid-core --test sxpid_relation_witness
python3 -I -S scripts/check-lean-descriptor-factorization.py
python3 -I -S scripts/check-lean-descriptor-factorization-self-test.py
```

At creation, the Python checker and both Rust tests passed. The exact checker derives the
event counts, order, atom ratios, and mutations without the Rust implementation or floating point.
The Rust lane separately evaluates the complete public event and lattice implementation. Its integer-product
assertions run before any log or binary64 reconstruction comparison.
The Lean lane proves only the conditional transfer firewall and does not compute the concrete
witness. These implementation-distinct lanes share the reviewed semantic cuts stated in Section
7.5, so this record does not claim three logically independent end-to-end proofs.

---

## Primary sources

1. Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral. “Introducing a differentiable
   measure of pointwise shared information.” *Physical Review E* 103, 032149 (2021).
   [doi:10.1103/PhysRevE.103.032149](https://doi.org/10.1103/PhysRevE.103.032149),
   [arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356).
2. Aaron J. Gutknecht, Michael Wibral, and Abdullah Makkeh. “Bits and Pieces: Understanding
   Information Decomposition from Part-whole Relationships and Formal Logic.” *Proceedings of
   the Royal Society A* 477, 20210110 (2021).
   [doi:10.1098/rspa.2021.0110](https://doi.org/10.1098/rspa.2021.0110),
   [arXiv:2008.09535](https://arxiv.org/abs/2008.09535).
3. Philip Hendrik Matthias, Abdullah Makkeh, Michael Wibral, and Aaron J. Gutknecht. “Novel
   Inconsistency Results for Partial Information Decomposition.”
   [arXiv:2512.16662v1](https://arxiv.org/abs/2512.16662), 18 December 2025. Version 1 was the
   version audited and remained the current arXiv version when rechecked on 25 July 2026.
4. Aobo Lyu, Andrew Clark, and Netanel Raviv. “Structural Impossibility of Antichain-Lattice
   Partial Information Decomposition.”
   [arXiv:2604.03869v2](https://arxiv.org/abs/2604.03869), 14 April 2026.
5. Paul L. Williams and Randall D. Beer. “Nonnegative Decomposition of Multivariate
   Information.” [arXiv:1004.2515](https://arxiv.org/abs/1004.2515), 2010.
