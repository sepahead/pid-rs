# A true finest-grid interval that the whole schedule rejects

**Sepehr Mahmoudian · 2026**

A correct interval need not contain a second correct interval for the same number. Here a new counted input and four complete, constructed 108-coordinate reports exercise the original reader. The input is a finite empirical distribution. The reports are fixtures. The six previously archived producer reports keep their own source identities. [Original reader](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/audit/research/three-source-six-certificate-observations/check.py) · [Defining shared-exclusions paper](https://doi.org/10.1103/PhysRevE.103.032149)

## The one-grid-unit rule

At output precision $p$ let one output grid unit equal $2^{-p}$ nats. Scale all real values below into these units. Suppose a real value $y$ lies in a raw interval $[l,u]$ whose width is less than one. Let $[A,B]$ also contain $y$, with $A$ and $B$ integers in this **same** grid. Then

$$
l>y-1\ge A-1,\qquad u<y+1\le B+1 .
$$

Taking the floor below and ceiling above shows that $[A-1,B+1]$ contains the final checker interval. This proof includes equality of the true value with a producer endpoint. The subunit bound applies on the genuine three-source counted inputs described in the width result.

The corrected interval must still meet every wire rule. Two-sided padding adds $2\cdot2^{-p}$ nats to its width. A producer interval already at the cap $2^{-160}$ would exceed that cap. The normalized dyadic coefficient, allowed exponent, byte, resource, coordinate and binding checks still apply. The alignment hypothesis is substantive. For example, in grid units let $y=1/5$, $l=-7/10$ and $u=y$. The raw width is below one. Starting from the off-grid singleton $[y,y]$ and adding one at both ends does not include $\lfloor l\rfloor=-1$. This is an arithmetic example of the general hypothesis. [Original wire and schedules](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md)

## A complete counted example

The two other source readings are constant. The first reading is binary and uniform, and the target either reveals it or records the symbol `x` for erasure. Read the four occupied rows in the order $(0,0),(0,\mathrm{x}),(1,1),(1,\mathrm{x})$ of first-source and target levels. Their counts are $269,584,269,584$. The total is $N=1706$. The informative factor at the first-source singleton is two with total exponent $N$. The misinformative factor is two with exponent $1168$. The signed cumulative product is $2^{538}$ and the true average is $y=(538/1706)\ln 2$ nats.

Set $p=2048$. Write $a=\lfloor 2^{2048}y\rfloor$. To verify the exact integer without using the original range reduction, use

$$
\ln 2=\ln(3/2)+\ln(4/3).
$$

For $d=5,7$, respectively, $z=1/d$ gives the series for $\ln((1+z)/(1-z))$. Sum the first 500 positive terms $2z^{2j+1}/(2j+1)$ with $j$ from zero through 499. Bound the omitted tail by $2z^{1001}/[1001(1-z^2)]$. After scaling by $2^{2048}(538/1706)$, both rational bounds lie strictly between the same consecutive integers. The complete 616-digit integer $a$ is in the source output.

At its seven successive precisions $256,384,512,768,1024,1536,2048$, the checker widths in each stage's own units are $1,1,1,1,1,1,2$. At the first six stages, one grid unit already exceeds $2^{-2048}$. These positive widths also follow directly from the positive log-two helper width multiplied by the nonzero exponent 538. At the last stage the original interval is $[a-1,a+1]$ in units of $2^{-2048}$. The true single cell $[a,a+1]$ fails the containment test at every stage.

Only the selected coordinate changes in the four constructed reports. Their other 107 intervals all pass at the first precision. The complete original typed reader gave the following results.

| Selected interval in final-grid units | Actual outcome |
|---|---|
| $[a,a+1]$ | Rejected for independent interval containment |
| $[a-1,a+1]$ | All 108 coordinates accepted. The selected coordinate passes at 2048. |
| $[a,a+2]$ | Rejected for independent interval containment |
| $[a-1,a+2]$ | All 108 coordinates accepted. The selected coordinate passes at 2048. |

The canonical input has 492 bytes. All four canonical reports have 98,271 or 98,272 bytes, below the original 131,072-byte local report cap. The tight interval's two normalized exponents are $-2043$ and $-2048$. Its width, the one-sided widths and the two-sided width all meet the original absolute width limit. All seven stages, four full report hashes and the original checker identities appear in the output. The local reader reconstructs all products, bindings and content. A successful call on these constructed bytes makes no claim about an action by the historical producer.

Across the seven previously fixed four-row reveal/erase examples, the individual side needed to enlarge each true single cell is upper, upper, upper, lower, upper, upper, lower in precision order. Thus always padding only the lower side and always padding only the upper side each fails on an actual counted example. The general two-sided rule covers both possibilities.

## Rust implementation and computational cost

The public finite categorical Rust estimator returns floating-point averages. The complete 108-coordinate audit in this example belongs to the original Python certificate checker. It uses four distinct counted rows, three categorical sources, one target and seven maximum precision stages. The independent cell calculation uses two exact 500-term sums and two rational tail bounds. The other 107 selected report intervals reuse the original checker at 256 bits. Those 107 are development fixtures and share the checker implementation. Bounds on one constructed coordinate do not establish future-sample calibration or estimator performance. No runtime benchmark is claimed.

Run `true_cell.py` with the unchanged six-table `check.py`. An optional new output directory receives the complete canonical input and reports. The independent seven-table orientation replay also needs the earlier empirical table list, its original arithmetic source and the companion `true_cell.py`. Ordinary and optimized Python give the same outputs. Cite this note with its year and exact repository commit or release. [Software citation](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/CITATION.cff)
