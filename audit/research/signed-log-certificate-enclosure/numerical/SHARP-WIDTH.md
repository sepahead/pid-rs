# Sharp widths of the signed rational logarithm interval

**Sepehr Mahmoudian · 2026**

The six-table checker takes a positive rational product $Q$, a positive integer $N$ and a precision $p$. It encloses $(\ln Q)/N$ in nats. One output grid unit is $2^{-p}$ nats. This note determines the greatest possible width at each allowed $p$ and $N$ under the original product-size limit. It also determines the maximum for the counted data to which the program was applied. In the latter result, the four input rows in each example define an empirical distribution. They have no training or test role. These are project-derived statements about the original arithmetic. The categorical shared-exclusions measure is due to Makkeh, Gutknecht and Wibral. [Arithmetic source, lines 185–258](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/audit/research/three-source-six-certificate-observations/arithmetic.py#L185-L258) · [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149)

## Inputs and statement

Write $\beta(a)$ for the number of digits in the base-two representation of a positive integer $a$. Let $(A_i/B_i)^{c_i}$ range over the factors of $Q$. Each $A_i$ and $B_i$ is a positive integer and each $c_i$ is an integer. The empty product equals one. The product-size test requires

$$
2+\sum_i |c_i|\bigl(\beta(A_i)+\beta(B_i)\bigr)\le262144.
$$

Let $b=p+24$, $S=2^b$, $G=2^{24}$ and $J=\lceil b/3\rceil+1$. The function for the odd-power series returns two integers in units of $1/S$. Denote by $C_p$ their difference when its argument is $1/3$, the input for $\ln 2$. A floor rounds to the next integer at or below its argument. A ceiling rounds to the next integer at or above its argument.

For each $N\ge1$ the **exact maximum scalar width**, in final grid units, is

$$
1+\left\lceil\frac{262141 C_p+2J}{NG}\right\rceil .
$$

The maximum ranges over products satisfying the size test, with $N$ independently chosen. The next table gives the exact constants. The last column gives the first total for which every greater or equal total has maximum width two.

| $p$ | $J$ | $C_p$ | Maximum at $N=1$ | First total with maximum two for all larger totals |
|---:|---:|---:|---:|---:|
| 256 | 95 | 106 | 3 | 2 |
| 384 | 137 | 144 | 4 | 3 |
| 512 | 180 | 186 | 4 | 3 |
| 768 | 265 | 272 | 6 | 5 |
| 1024 | 351 | 361 | 7 | 6 |
| 1536 | 521 | 532 | 10 | 9 |
| 2048 | 692 | 699 | 12 | 11 |

For **genuine three-source count tables with at most 1,024 occupied joint rows**, the maximum over all such admitted tables is **two** at each precision. At total $N=1$, or with a single occupied row, every product is one and its width is zero. Four-row examples attain two at each precision. The other induced mathematical restrictions matter when $N$ is fixed.

## Bound the integer calculation

For a regular argument $0<z\le1/3$, the original helper begins with $l=\lfloor Sz\rfloor$ and $h=\lceil Sz\rceil$. It fixes $v=\lfloor l^2/S\rfloor$ and $u=\lceil h^2/S\rceil$. The first power gap $h-l$ is at most one. Since $S\ge256$,

$$
u/S\le(1/3+1/S)^2+1/S<1/8.
$$

The unrounded squares divided by $S$ differ by $(h-l)(h+l)/S<1$. Consequently $u-v\le2$. At every update $0\le l\le S/3$. Suppose $h-l\le2$. The two real arguments for the next directed integer updates differ by

$$
\frac{(h-l)u+l(u-v)}{S}\le 2/8+2/3<1.
$$

Floor below and ceiling above give an integer gap of at most two. This proves the same upper bound at every power. The first series term contributes at most two units to the accumulated width. For any later odd denominator $k\ge3$, the numerator remainder modulo $k$ is at most $k-1$. Hence

$$
\lceil 2h/k\rceil-\lfloor 2l/k\rfloor
\le \left\lfloor\frac{2(h-l)+2k-2}{k}\right\rfloor\le2.
$$

The actual nonzero branch adds one further internal unit to cover the omitted analytic tail. Its integer interval width is therefore at most $2J+1$. This bound accounts for all included rounding operations. The separate zero branch returns $(0,0)$ immediately.

For $Q\ne1$ the program takes $e=\lfloor\log_2Q\rfloor$ and reduces the factor to $Q/2^e\in[1,2)$. Here $\log_2$ denotes base-two logarithm. Each factor has $|\log_2(A_i/B_i)|<\beta(A_i)+\beta(B_i)-1$. The sum of the nonzero absolute exponents is at least one. The size limit gives $-262141\le e\le262140$. The two extremes are reached by the reciprocal and the value, respectively, of $2^{262141}-1$.

Let $w_r$ be the reduced factor’s integer helper width. The combined internal width is exactly $E=w_r+|e|C_p$. This formula includes the reversed endpoints when $e<0$. If the lower combined integer is $L$ and its remainder upon division by $Y=NG$ is $d\in\{0,\dots,Y-1\}$, the final width is $\lceil(d+E)/Y\rceil$. It is at most $1+\lceil(E-1)/Y\rceil$. Substitution gives the stated upper bound. The exact $Q=1$ branch has zero width. For independent scalar inputs without the size limit, $Q=2^k$ at $N=1$ has internal width $kC_p$ for every positive integer $k$. No finite uniform bound follows there.

## Attain all scalar bounds

For the 32 pairs $(p,N)$ below the last column's threshold, the finite certificate gives an integer $k\le262140$ for which each of $Q=2^k$ and $Q=2^{-k}$ attains the bound. Both products meet the factor-size limit. Their reduced factor is exactly one. The certificate includes $k$, the two fixed-endpoint hash and the target width for every such pair. The replay independently computes the fixed integer pair, verifies the original helper's pair, and invokes the full original logarithm routine at both signs. For example, $p=256$, $N=1$, $k=262140$ gives width three. These values use the scalar domain.

For all other totals one rational product suffices. Set $T=2^{2080}$ and $Q=(T-1)/T$. Its exponent is $-1$ and its reduced series argument is $(T-2)/(3T-2)$. This is $4/[3(3T-2)]$ below $1/3$. At every allowed field the difference times $S$ is less than $1/3$. The fractional part of $S/3$ is either $1/3$ or $2/3$. Thus the starting lower and upper integers for the reduced factor and for $\ln2$ coincide. All later helper operations coincide. The combined interval is $[-C_p,C_p]$. Since $0<C_p<G$, its final interval has endpoints $-1,1$ in grid units for **every** positive integer $N$. The exact logarithm in this example is negative. This establishes a maximum on an infinite set of totals without testing each total.

## Use the constraints from the finite categorical method

Let $c_j$ be the positive multiplicity of occupied joint row $j$, and let $s$ be the number of occupied joint rows. A keyed source event contains its anchor row. Its intersection with the anchor's target event also contains that row. The event and target counts are at most $N$. Each of its original informative and misinformative factors therefore lies between one and $N/c_j$. Their separate cumulative averages in bits lie in $[0,H]$, where

$$
H=\sum_{j=1}^s\frac{c_j}{N}\log_2\frac{N}{c_j}\le\log_2s.
$$

The inequality follows by applying the concavity of the logarithm to the weights $c_j/N$. The signed difference has absolute value at most $H$. A cumulative coordinate uses one such value. An atom uses a row of the inverse of the 18-node order matrix. In its original row order the sums of the absolute coefficients are $2,2,4,2,4,4,8,2,2,4,2,4,4,4,4,4,1,8$. These integers can be checked by multiplying the order matrix and the inverse in both orders. Hence $|\log_2 Q|\le8N\log_2s$. For $s\le1024$, $|e|\le80N$ because $80N$ is an integer. At all scheduled fields $2J+1\le1385$. Thus

$$
E\le1385(1+80N)\le112185N<2^{24}N.
$$

The final width is at most two. This argument uses the actual counted event construction. It does not require the factor-size bound as an arithmetic inequality. The program's separate resource rules still determine which tables it accepts. [Original count events and projection](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/audit/research/three-source-six-certificate-observations/arithmetic.py#L128-L212)

For each precision, take two equally probable values of the first source. Give each of the two other sources one fixed level. The categorical target either reveals the first source or records an erasure. Choose positive even integers $m<N$, with $N$ even. The two revealed cells have count $m/2$ each. The two erased cells have count $(N-m)/2$ each. For the node consisting of the first source, the informative product is $2^N$. The misinformative product is $2^{N-m}$. The signed cumulative product is $2^m$. The resulting value is $(m/N)\ln2$ nats.

| $p$ | $N$ | $m$ | Count in each revealed cell | Count in each erased cell |
|---:|---:|---:|---:|---:|
| 256 | 1444 | 1434 | 717 | 5 |
| 384 | 1364 | 1170 | 585 | 97 |
| 512 | 1866 | 998 | 499 | 434 |
| 768 | 1708 | 1494 | 747 | 107 |
| 1024 | 408 | 386 | 193 | 11 |
| 1536 | 1108 | 1054 | 527 | 27 |
| 2048 | 1706 | 538 | 269 | 584 |

Each table passes the original typed-input, count, memory-reservation and all 108 per-coordinate product preflights. The original signed cumulative checker returns width exactly two. The finite search checks increasing even $N$ and increasing even $m$ until the first admitted crossing for each field. Its minimality statement applies only to this preselected four-row family. No sampling or population-estimation claim follows. The width of the independent interval also cannot guarantee that it lies inside another correct enclosure of the same true value.

## Rust implementation and computational cost

These statements concern the archived Python integer checker. The stable categorical Rust entry point `pid_core::stable::categorical::discrete_sxpid3_averaged` returns empirical finite-precision averages. Its input rows contain the three categorical sources and target. Its public calculation does not issue the Python integer interval. The scalar proof uses two directed series of $J$ terms, with the $\ln 2$ pair reusable at the same field. The coordinate-size test bounds integer operand lengths. Each four-row example sends all 108 original plans through their preflights. The witness search uses exact modular arithmetic and then calls the original program on the selected rows. The separate stock proof concerns the integer recurrence. This note's global width and sharpness results have a written proof and exact finite checks. No estimator timing, floating-point refinement or sampling calibration is claimed.

To reproduce the two checks, supply the original arithmetic file to each script. `coordinate_width.py` emits the scalar result and `empirical_width_witness.py` emits all seven full tables with their two large endpoint numerators. Both programs use only the Python standard library. Their outputs are identical under regular Python and `python -O`. The arithmetic source and finite example executions share an implementation. The alternative fixed $\ln 2$ recurrence, row argument, signed rounding identity and explicit original-program witnesses supply separately checkable parts of the derivation. Cite this note with the year and exact public repository commit or release. [Software citation](https://github.com/sepahead/pid-rs/blob/c416ace7a92d9859917cf3bd56b67b43f1fc3614/CITATION.cff)
