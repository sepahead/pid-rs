# Testing each side of an interval at a fixed precision

**Sepehr Mahmoudian · 2026**

The lower and upper sides of a true grid interval can each need an extra unit. This finite computation checks both directions at every scheduled precision on the complete four-row reveal/erase family admitted by the local per-row count limit. It uses the three-source categorical shared-exclusions definition and the original integer reader. [Original reader](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/audit/research/three-source-six-certificate-observations/check.py) · [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149)

Let $a$ and $b$ be the positive counts in each of the two revealed cells and each of the two erased cells, respectively. The target reveals a balanced binary first source in the two revealed cells. The other two source readings are constant. The total count is $N=2(a+b)$ and the revealed count is $m=2a$. The singleton first-source cumulative signed product is $Q=2^m$, and the true mean is $(m/N)\ln 2$ nats. For each of seven output precisions, the reader examines all $999^2=998001$ choices with $1\le a,b\le999$. The outer total runs in increasing order, then the revealed count. These are constructed finite distributions. They do not estimate a frequency in measured data.

At precision $p$ let $G=2^{24}$ and let $L_2,U_2$ be the two integer bounds for $2^{p+24}\ln 2$ from the original helper. Set $C=U_2-L_2$ and $D=NG$. The actual raw endpoint integers before dividing by $D$ are $mL_2,mU_2$. Put $s=(mL_2)\bmod D$, with $0\le s<D$. Because $0<mC<D$, the final grid interval has width two if and only if $s+mC>D$. This strict test includes both cases when an endpoint is a grid point. For every positive hit, the program reconstructs the actual four typed rows and all 108 product preflights. It locates the true grid cell with two independently formed rational bounds on $\ln(3/2)+\ln(4/3)$. Its lower and upper endpoints compare the true cell with the actual full original logarithm call.

| Output bits | True cell needs a unit below | True cell needs a unit above |
|---:|---:|---:|
| 256 | 0 | 4 |
| 384 | 0 | 1 |
| 512 | 0 | 3 |
| 768 | 7 | 1 |
| 1024 | 0 | 45 |
| 1536 | 6 | 8 |
| 2048 | 6 | 3 |

All 84 positive hits passed the original typed and arithmetic tests. The independent positive-series enclosure resolved the true cell for each hit. No direction remained unclassified. The zeros in the table describe exactly this family and these per-row limits.

At 2,048 bits the first lower-required case has $N=1706$, $m=538$ and counts 269, 584, 269, 584 in the order first-source and target pairs $(0,0),(0,x),(1,1),(1,x)$. The symbol $x$ records an erasure. The first upper-required case has $N=1934$, $m=1428$ and counts 714, 253, 714, 253. For each input the generator constructs four complete, source-shaped 108-coordinate records. Their other 107 coordinates use the same intervals. The original typed reader rejects the true single cell and the interval expanded only on the opposite side. The interval expanded on the needed side and the interval expanded on both sides each pass all 108 coordinates. In every passing report the chosen coordinate passes at 2,048 bits and the other 107 pass at 256 bits. Only one coordinate's interval varies within each four-report comparison. All complete reports meet the original width and byte limits. No action by the original historical producer is implied.

At a single fixed final precision and with the same original coordinate, neither universally choosing only the upper side nor universally choosing only the lower side can guarantee containment. The previous two-sided one-unit rule is sufficient if the padded interval meets its other wire requirements.

## Rust implementation and computational cost

The tested procedure is the original Python integer reader. The stable categorical Rust estimator returns floating-point averages. The finite census uses one exact modular update per table and precision, followed by an original typed reconstruction for each candidate of width two. It considers 6,986,007 table-precision pairs and runs the complete report verifier on eight constructed reports. Ordinary Python and optimized Python produce identical census bytes and canonical reports. It measures no estimator throughput, sampling error, deployment cost or population calibration. Cite this note with its year and the exact repository commit or release. [Software citation](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/CITATION.cff)
