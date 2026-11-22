# Source sets and the logarithm in the finite shared-exclusions formula

Sepehr Mahmoudian · 21 November 2026

When does the finite shared-exclusions formula have a value at an observed outcome, and which number does it report? These questions affect the definition before any averaging, sampling, or numerical approximation.

## What the earlier report said

The July report, as revised on 20 November, defined a union for an antichain of nonempty source sets. It then inferred that the union had positive probability because every member contained the observed outcome. Its pointwise formula took a logarithm. Three passages called the result, or the quantity whose lower-node contributions are subtracted, a likelihood ratio. The original PDF is retained at its exact revision. [Previous report, Section 4 and final claim table](https://github.com/sepahead/pid-rs/blob/9431551d655e520ced9c25c7f348f013fa4e4bd0/output/pdf/foundational-shared-exclusions-pid-audit.pdf)

## Two different requirements for a node

A source set lists indices of sources observed together. An antichain is a family in which neither of two distinct members contains the other. A node in this decomposition meets two additional requirements. The family contains at least one member, and every member contains at least one source index. Williams and Beer use the nonempty power set twice in their definition of the nodes. Makkeh, Gutknecht and Wibral form the union of joint source-matching events and take a logarithm of a conditional probability ratio. The report uses natural logarithms and reports information in nats. [Williams and Beer, equation (4)](https://arxiv.org/abs/1004.2515v1) · [Makkeh, Gutknecht and Wibral, Section II and Appendix A](https://arxiv.org/abs/2002.03356v5)

Let $p$ be a probability distribution on a finite set of complete outcomes of $n\geq1$ categorical sources and one target. Fix $z=(s_1,\ldots,s_n,t)$ with $p(z)>0$. A member $a$ specifies the event $E_a$ that every source listed in $a$ agrees with its value at $z$. Let $A$ be the union of these events over the node. Choose one member. The outcome $z$ lies in its event and has target value $t$. Hence

$$
p(A)\ \geq\ p(T=t,A)\ \geq\ p(z)>0.
$$

Also $p(T=t)\geq p(z)$. All three factors in the next formula are positive. An empty family has no member to choose. Its union is the empty event. A family containing the empty source set is different again. The conjunction over that empty set is always true, so its event is the whole sample space.

## One outcome checks both corrections

Take one source and one target, with a single complete outcome of probability one. For the empty family, $p(A)=p(T=t,A)=0$. The conditional probability at this event has the undefined form $0/0$. For the admitted node whose only member contains source one, both probabilities equal one. Write $r=p(T=t\mid A)/p(T=t)$ for the dimensionless probability ratio. Then $r=1$, and the pointwise redundancy is $\ln r=0$ nats. A second example separates them at a positive information value. If a fair binary source equals its target, a match on that source gives $r=2$ and $\ln r=\ln 2$ nats. At a general node, subtract the strictly lower atoms from the log ratio to obtain the atom.

## What the correction changes

Correction of the family domain makes the positivity proof valid for every defined node. Correction of the prose makes the named quantity agree with the displayed equation. The Rust enumerator already starts with positive source masks and positive selections of those masks. For one through four source indices the node counts are 1, 4, 18 and 166. The general stable Rust evaluator accepts two through four sources. These checks address the node definition and the log ratio. Source-to-code correspondence for every input, floating-point error bounds, and statistical calibration have their own evidence requirements. [Rust enumerator](../../crates/pid-core/src/sxpid.rs) · [Mathematical report](../../FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md) · [Software citation](../../CITATION.cff)


The previous Markdown also identified an older Rust source digest as current. Its own current evidence at the time bound a different source file. The previous print and record remain accessible by revision. On 21 November only the explanatory comment above the node enumerator changed in that Rust file. Rerunning the original exact checker gives the same complete outcome data and a new digest for that source. [Previous evidence at its exact commit](https://github.com/sepahead/pid-rs/blob/5628bb6e2b6f14619a72a045a0dbb3ab8cbf6186/audit/evidence/foundational-sxpid-lcr-exact-audit.json) · [Current complete record](foundational-sxpid-lcr-exact-audit.json)

## A determining pair and the top atom

In the finite categorical shared-exclusions construction, fix one supported reference row. Let $A,B,C$ be the events that the two sources in groups 12, 13 and 23, respectively, match this row. Let $F$ be a match on all three sources. Events that differ only outside the support have the same probabilities. The proof uses this equality on the support. Every proper source group is contained in a pair. Inclusion–exclusion on the three lower sets of nodes therefore gives eight cumulative terms for the top atom. If $A=F$ on the support, then $A$ is contained in both $B$ and $C$ there. The terms cancel in four pairs. This gives zero at the reference row. If source three is a function of the first two on the support, the same cancellation holds at every supported row and survives averaging. [Full expansion, proof and constant-source example](../../FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md#when-a-pair-determines-the-complete-source-tuple)

Equality of all three pair events with $F$ at every supported reference row requires that each pair determine the tuple. Two independent fair bits and a third source fixed at zero show the difference. Sources one and two then determine the tuple. Sources one and three do not.

For the XOR tuple copy, the four equiprobable source tuples are 000, 011, 101 and 110. The target is the tuple itself. All three pair events now coincide. Their common cumulative value is $\ln 4$ nats. At the node with all three pairs as alternatives, the strictly lower atoms sum to $\ln(27/8)$ nats. The remaining atom is $\ln(32/27)$ nats. Separate one-to-one changes of the labels of each source and of the target preserve the matching probabilities.

The stable Rust entry `pid_core::stable::categorical::discrete_sxpid3` returns averaged informative and misinformative atoms and their signed difference in nats. On these four rows, eleven exact zero signed atoms gave positive binary64 zero. Seven exact signed atoms were nonzero. The three copies of $\ln(4/3)$ gave the nearest binary64 number. The three copies of $\ln(9/8)$ gave a number two representable steps above the nearest. The copy of $\ln(32/27)$ gave a number two steps below the nearest. The complete printed words are in the report. The finite-check input included two other four-row tables, before and after constant recoding. One run produced 54 named atoms and 162 component words on the three tables. The [complete tab-separated output](finite-sx-averaged-words-2026-11-21.tsv) gives the case, node, informative word, misinformative word and signed word in that order. Hexadecimal source masks use bits 1, 2 and 4. A plus sign separates groups in a node. The output had SHA-256 `ca9c264ffdc3270bfeaa083491165ef6b63cbb1f162a58d3945b682edbfd9509`. Two earlier link failures stopped before any table evaluation. The original comparison checked the named values to an absolute tolerance of $10^{-12}$ nats. A later exact interval calculation identified the nearest binary64 value for each of the four positive logarithms after the observed words were available. These observations apply to this Rust 1.99.1 release execution. [Rust entry and returned fields](../../crates/pid-core/src/sxpid.rs) · [Four-symbol sign constraints](source-partition-sign-margin-2026-11-19.md)

The two systems from Lyu, Clark and Raviv form a separate example. Exact event counts give eight nonzero signed atoms. The Rust test compares the results with expected logarithms at its declared tolerance. [Exact record](foundational-sxpid-lcr-exact-audit.json) · [Rust test](../../crates/pid-core/tests/sxpid_relation_witness.rs)

Cite Sepehr Mahmoudian (2026), *Source sets and the logarithm in the finite shared-exclusions formula*, with the exact repository commit or release. Cite the defining papers for the scientific objects. [Software citation](../../CITATION.cff)
