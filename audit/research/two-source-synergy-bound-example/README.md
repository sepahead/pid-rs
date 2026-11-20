# How the support count changes a synergy bound

**Sepehr Mahmoudian · 2026**

Two formulas give upper bounds for the same pair of device tables. An upper bound gives a limit on the size of the change. The tables also give the actual change in signed synergy.

## The two device tables

A **cell** lists two input bits and an output bit, in that order. The output is one exactly when both inputs are one. This rule is the Boolean AND function. In the reference distribution, the two inputs are independent and each bit has equal chances of zero and one.

The **support** is the set of cells with positive probability. Its union across two distributions includes every cell present in either distribution. $K$ is an integer upper bound on the size of that union. Here $p$ is the smallest positive reference probability.

**Total variation distance**, written $\eta$, is half the sum of the absolute probability changes. A **nat** is the information unit for natural logarithms. An **atom** is one term in a decomposition of information. Here the signed quantity is the synergy atom of the full two-source categorical shared-exclusions decomposition. [Defining paper](https://arxiv.org/abs/2002.03356v5)

| Cell | Reference count | Changed count |
|---|---:|---:|
| 000 | 50 | 1 |
| 010 | 50 | 99 |
| 100 | 50 | 50 |
| 111 | 50 | 50 |
| Total | 200 | 200 |

A count divided by 200 gives its probability. The table defines two complete distributions for this example. All other cells have probability zero in both distributions. The changed distribution keeps the AND rule.

Both distributions have the same four-cell support. Here $p=50/200=1/4$.

The first cell loses 49 counts and the second gains them. Thus $\eta=(49+49)/(2\times200)=49/200=0.245$.

For each cell, the signed value equals its informative part minus its misinformative part. Each distribution weights those values by its own probabilities. The result is its **signed averaged synergy**.

## Local and global bounds

Both formulas bound the absolute difference between the two averaged synergy values. The local bound uses the common support and requires $0<\eta<p$.

$$
A_p(\eta)=-\ln(1-\eta/p)-\eta+2\eta\ln(1/p).
$$

The two supports can differ for the global bound. Its formula requires $K\ge2$. The floor symbol rounds down to an integer.

$$
B_K(\eta)=\eta\,[12+\ln\lfloor K^2/4\rfloor-2\ln\eta].
$$

The number 12 includes 10 from the two-source synergy coefficients and 2 from the global distance bound. Both expressions take the value zero at zero distance. If the union contains one cell, both distributions give it probability one.

![Figure 1. Squares mark the global bounds and the circle marks the local bound. The labels give nats rounded to three decimal places.](support-bounds.svg)

Here $1-\eta/p=1/50$. The local bound rounds to **4.346307242 nats**.

- With **$K=4$**, $\lfloor4^2/4\rfloor=4$. The global bound rounds to **3.968825682 nats**. It is below the local bound.
- With **$K=16$**, $\lfloor16^2/4\rfloor=64$. The global bound rounds to **4.648109919 nats**. It is above the local bound.

The second calculation uses a deliberately loose upper bound on the same four occupied cells. The complete binary alphabet has only eight possible cells. Throughout the comparison, the distributions and the local bound stay fixed.

The comparison uses the two formulas before any additional limit from the range of the atom. These are the **uncapped** bounds. The original local theorem permits a smaller averaging coefficient, $\ln((1+p)^2/(4p))$, in place of $\ln(1/p)$. [Local derivation, two-source synergy](../../../DEPENDENCY_COLORED_SXPID_CONCENTRATION.md) · [Global derivation, Theorem 4 and equations (34)–(38)](../../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md)

## Device measurements

Two device tables can describe the same categorical inputs and output under two settings. Their probabilities give the movement and the support count. A reader can then bound the change in averaged synergy without calculating the atom. A direct atom calculation answers a different question about the actual change.

Two tables of 200 counts can also be identical. Their distance is then zero. In the changed table above, the smallest positive probability is $1/200$. Table size alone determines neither the distance nor the smallest positive probability. For sampled device data, the calculation describes the empirical tables. A confidence statement about the device requires a sampling model.

---

## The actual change in signed synergy

For one occupied cell, let $x,y$ be its two input bits and $t$ its target bit. Event $A$ means that the first input equals $x$. Event $B$ means that the second input equals $y$. Their union $A\cup B$ includes a row when either or both events occur. Their intersection $A\cap B$ requires both.

Write $\Pr(t\mid E)$ for the fraction of counts in event $E$ with target $t$. Each probability in one calculation comes from the same table. Let $R$ be the ratio whose natural logarithm gives the cell's signed synergy.

$$
R=\frac{\Pr(t\mid A\cap B)\,\Pr(t\mid A\cup B)}{\Pr(t\mid A)\,\Pr(t\mid B)}.
$$

The two-source decomposition subtracts each single-input information from the joint information and adds the shared information. For each event, the information is $\ln[\Pr(t\mid E)/\Pr(t)]$, where $\Pr(t)$ is the target probability. The four factors of $\Pr(t)$ cancel.

The shared information uses the inclusive union. The paper uses base-two logarithms. Natural logarithms give nats here. The AND rule gives $\Pr(t\mid A\cap B)=1$. [Defining paper, equations (2), (7) and (13)](https://arxiv.org/abs/2002.03356v5)

In changed cell 010 the target is zero. All 100 counts in $A$ have target zero. In $B$, 99 of the 149 counts have target zero. The union contains cells 000, 010 and 111. Of their 150 counts, 100 have target zero. Thus $R=(100/150)/(1\times99/149)=298/297$.

| Cell | Reference $R$ | Changed $R$ |
|---|---:|---:|
| 000 | 1 | 1 |
| 010 | 4/3 | 298/297 |
| 100 | 4/3 | 102/101 |
| 111 | 4/3 | 298/199 |

Each table weights $\ln R$ by its own cell probabilities. Write $S_P$ for the reference average and $S_Q$ for the changed average. In nats,

$$
\begin{aligned}
 S_P &= \tfrac34\ln(4/3),\\
 S_Q &= \tfrac1{200}\big[99\ln(298/297)+50\ln(102/101)+50\ln(298/199)\big].
\end{aligned}
$$

The averages round to **0.215761554339** and **0.105074106669 nats**, respectively. The signed difference $S_Q-S_P$ rounds to **−0.110687447670 nats**. Its magnitude rounds to **0.110687447670 nats**, below each bound in Figure 1.

An earlier calculation gives the same reference value for one count in each of the four occupied cells. Multiplication of all counts by 50 preserves their probabilities. The earlier enumeration stops at four total counts. [Earlier reference table, case 415 counting from zero](../../../crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json)

---

## Conditions for each calculation

The comparison uses a movement between two previously identified crossings. This choice shows that the order can reverse. It gives no frequency for reversals in device data.

- A support limit of three fails because four cells have positive probability.
- Exchanging the reference and changed tables preserves the distance. The new reference minimum is $1/200$, so the local condition fails.
- Changing the upper bound $K$ changes the global bound. The direct calculation of the two averages uses only the table probabilities.
- If only the distribution changes matter, total variation already answers the question. It needs no decomposition into atoms.

The two bounds are project derivations for the published shared-exclusions measure. The arithmetic check uses the exact example counts. AI assistance helped prepare the explanation and its checks. The source reports describe the mathematical and formal review for each underlying result.

## Rust implementation and computational cost

The stable Rust function `pid_core::stable::categorical::discrete_sxpid2_averaged` computes averaged atoms from aligned categorical rows. It requires no experimental feature.

The bound calculation scans $m$ listed cells in $O(m)$ operations and stores $O(m)$ counts. The separate atom verifier scans the cells for four events at each cell. It uses $O(m^2)$ count visits and $O(m)$ stored counts for two inputs. The exact products and logarithm bounds use integers that grow with the counts and precision.

Both programs operate on the supplied tables. They fit no model. No timing is reported. [Rust source](../../../crates/pid-core/src/sxpid.rs) · [Engineering cost reference](../../../RUST_IMPLEMENTATION_AND_COST.md)

## Reproduce the example

The count file fixes the variable order and all four cells. The programs use Python 3.11 or later and its standard library. In the study directory, enter these commands.

```sh
python3 -I -S -B example.py --check
python3 -I -S -B verify_numbers.py
python3 -I -S -B verify_signed_synergy.py
```

Place `-O` before `-I` to repeat the commands with the optimized interpreter. The option `--write` regenerates the SVG. The second program verifies both bound comparisons, their rounding and the support conditions. [Counts](counts.json) · [Drawing and decimal arithmetic](example.py) · [Rational bound check](verify_numbers.py)

The third program counts the four events for every occupied cell and reconstructs the signed atom. It compares the numerator and denominator of $\exp[200(S_Q-S_P)]$ as integers. The numerator is smaller, so the difference is negative. Rational lower and upper limits for the logarithms verify all twelve displayed decimal places. [Signed synergy calculation](verify_signed_synergy.py)

The optional PDF build uses the repository's shared publication styles, Pandoc, LuaLaTeX and librsvg. The command `python3 -I -S -B build_pdf.py --output reader.pdf` makes a new copy. The option `--check` compares a fresh build with the shipped PDF. The option `--check-committed` inspects the saved sources, PDF and links without typesetting. The publication profile in `publication.json` binds the source files, shared styles, figure, PDF and link targets.

**Citation.** Mahmoudian, Sepehr (2026). *How the support count changes a synergy bound*. Include the exact pid-rs commit or release. [Software citation](../../../CITATION.cff)
