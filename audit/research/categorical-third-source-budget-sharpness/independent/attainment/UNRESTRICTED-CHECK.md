# Independent finite check of the third-source gap

Sepehr Mahmoudian, 2026. Cite the repository commit or release. This supplement uses the finite categorical construction of Makkeh, Gutknecht and Wibral. A row of a count table specifies probability equal to its count divided by the positive total N. There is no sampling or independence assumption. All logarithms below give nats. [Defining paper](https://arxiv.org/abs/2002.03356v5)

## Exact condition for equality

Let A=H(S₃ given S₁,S₂) and B=H(S₃ given S₁,S₂,T). Let K consist of the five three-source antichains at which every group contains source 3. These are {{3}}, {{1,3}}, {{2,3}}, {{1,3},{2,3}} and {{1,2,3}}. For each node β, write Pβ for its mean informative atom and Qβ for its mean misinformative atom. Both components are nonnegative. The signed mean is Pβ−Qβ. The sum M of the absolute values of these five signed means satisfies

$$
G=A+B-M=2\sum_{\beta\in K}\min(P_\beta,Q_\beta).
$$

The sums of the two components on K equal A and B by subtracting the cumulative information for sources 1 and 2 from the cumulative information for all three. If B=0, all five Qβ vanish and G=0. Conversely, if B>0 there are two positive rows with identical (s₁,s₂,t) and different values of s₃. Consider either row. Write E₃ for a match on its third value, and E₁₂ for a match on its first two values. Node {{3}} has a single greatest strict predecessor, namely {{3},{1,2}}. Every family strictly below {{3}} must include the single group {3} and another group contained in {1,2}. Thus subtracting these two cumulative values gives the informative atom

$$
\ln\!\left(1+\frac{P(E_{12}\setminus E_3)}{P(E_3)}\right).
$$

For the misinformative atom, condition both probabilities on T=t. The other positive row contributes to both numerators. Both denominators and the focal row probability are positive. Hence both mean atoms at {{3}} are positive and G>0.

## Exact minimum at fixed N and number of occupied labels

Let ℓ be the number of occupied S₃ values. Positive B requires 2≤ℓ≤N. Let u,v be the marginal counts for the two conflicting third labels. The focal counts are each at least one. The two rows give at least [ln(1+1/u)+ln(1+1/v)]/N to **each** mean atom at {{3}}. Conditioning may remove records from either count denominator. It retains the conflicting row in each numerator. The other ℓ−2 labels use at least one count each, so u+v≤s=N−ℓ+2. Minimizing (1+1/u)(1+1/v) first uses all s counts. It then maximizes uv because the product equals 1+(s+1)/(uv). Write a=⌊s/2⌋ and b=⌈s/2⌉. It follows that G≥2 ln[(1+1/a)(1+1/b)]/N.

Here is a second construction that gives equality at every feasible N,ℓ. Use the following ordered rows (S₁,S₂,S₃,T).

| Row | Count |
|---|---:|
| (0,0,0,0) | 1 |
| (0,0,1,0) | 1 |
| (0,1,0,1) | a−1 |
| (1,0,1,1) | b−1 |
| (j,j,j,j), one for each 2≤j<ℓ | 1 |

Omit zero counts. The marginal counts of 0 and 1 at S₃ are a and b. Only the first two rows share a first-source pair with conflicting S₃. Thus P at {{3}} is exactly ln[(1+1/a)(1+1/b)]/N. At T=0 the first two sources are constant, so the conditional informative value for S₃ is ln 2 at either of those rows and is assigned entirely to {{3}} within K. In each other target class the first-source pair determines S₃, so the sum of nonnegative conditional K atoms there is zero. Therefore Q at {{3}} is 2 ln 2/N, while its other four values are zero. Since a,b≥1, the informative {{3}} mean does not exceed the misinformative mean. This gives equality in the bound. At ℓ=1, or at N=1, there is no positive-gap case.

The factor exp(NG) lets the program check every inequality as an exact rational comparison. On all 4,844 nonempty binary four-variable count tables of total at most four, 1,196 have B>0 and a strictly positive gap. The remaining 3,648 have B=0 and gap zero. The minimum positive factors for N=2,3,4 are 16, 9 and 81/16. The count program also tests all 595 positive splits a+b=N for N=2 through 35 with ℓ=2 and all 120 pairs 2≤ℓ≤N≤16 with the balanced choice. The proof, not the finite census, covers larger counts and other finite alphabets.

## Rust implementation and computational cost

The Python verification uses the original finite event and predecessor definitions. Each of the up to 18 antichains requires a scan of every occupied row for each focal row, followed by subtraction of its predecessor contributions on the logarithmic scale. The code implements that subtraction by division of rational factors. For fixed dimension, the event scans take O(q²) comparisons for q occupied rows. The sizes of the integer products affect time and memory. This supplement introduces no production Rust routine. The structural gap calculation is an offline check on an exact discrete distribution. It supplies no estimator calibration or support for choosing a particular sensor or action.

Run check_finite_attainment.py and fixed_counts.py with Python 3, in both ordinary mode and with -O. Compare the two outputs with the corresponding JSON files. All finite case counts and minima in this supplement came from their genuine normal and optimized executions.
