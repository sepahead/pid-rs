# A finite-size bound for a repeated-source example

Sepehr Mahmoudian, 2026. Cite this note with its repository commit or release. The calculation uses the finite categorical shared-exclusions definition of Makkeh, Gutknecht and Wibral. All logarithms use the natural base and all information values are in nats. [Defining paper, equations (13)–(15)](https://arxiv.org/abs/2002.03356v5)

## Question and assumptions

How close does the five-position absolute mass get to its entropy bound at a finite alphabet size? A previous project note gives the limiting example in its section “Sharpness across finite alphabets”. This derivation specifies the joint distribution, treats dependence between the last two variables, and gives an exact finite formula with a sharp upper bound on the error. [Original project note](https://github.com/sepahead/pid-rs/blob/aebf505feb89d3bd8caea95d0b6341e4059f021b/audit/archive/shared-exclusions-research-findings-20261001/source-redundancy.md.txt)

Fix a finite pair Z = (U,V). Write p_z for its probability at an occupied value z and m for the number of such values. Thus p_z > 0 on the listed support and the sum of p_z is one. For each integer L ≥ 1, let X be uniform on L distinct symbols and independent of the **pair** Z. The three sources are S₁ = X, S₂ = a constant and S₃ = Z. The target is T = (X,U). The same distribution of Z is used as L varies. The pair U,V can be dependent. Pairwise independence of X,U,V alone does not give the required product distribution. For example, take independent fair U,V and let X equal their exclusive OR. Every pair is independent, but H(U,V given X) is ln 2, whereas H(U)+H(V) is 2 ln 2.

H denotes Shannon entropy, the probability-weighted mean of minus the logarithm of probability. Conditional entropy takes the mean within each observed conditioning class. In this construction put A = H(Z given S₁,S₂) = H(U,V), B = H(Z given S₁,S₂,T) = H(V given U), and Δ = A−B = H(U).

## Why only two of the five positions can contribute

At a fixed supported row, a source group matches when every listed source has the row's value. A family of alternative groups matches when at least one of its groups matches. An antichain is a family in which no group contains another. Adding a larger group to such a union has no effect if its smaller group is already present. For an event E of this form the local signed cumulative information is ln(P(E given T=t)/P(E)). Its value is zero when E is the whole space. For two antichains β and α write β ≤ α when every group of α contains at least one group of β. Each cumulative value is the sum of local atoms at all β ≤ α. Successive subtraction on this finite order gives a unique set of atoms. The mean of a local signed atom is taken with the original joint probabilities.

The constant second source always matches. Delete index 2 from each group. If a group becomes empty, the original union was the whole space. No group involving only sources 1 and 3 can be contained in that empty group. Otherwise the reduced union is exactly the corresponding two-source event. Remove duplicate groups and supersets. For every two-source antichain β, the relation β ≤ α holds precisely when β is below the reduced antichain. Put the four two-source atoms at {{1},{3}}, {{1}}, {{3}}, {{1,3}}, with zeros at the fourteen other positions. At each of the eighteen original positions, summing these atoms at and below that position gives its cumulative value. Uniqueness proves this statement for the original atoms.

The complement of the nodes below {{1,2}} consists of {{3}}, {{1,3}}, {{2,3}}, {{1,3},{2,3}} and {{1,2,3}}. Call this set K. The last three have zero signed atoms. Let M be the sum, over K, of the absolute values of the **mean** signed atoms. The two remaining atoms need not be nonnegative.

## Exact finite values

At a row with X=x and Z=z the union “X=x or Z=z” has probability p_z+(1−p_z)/L by independence of X from Z. Its conditional probability given T=(x,u) is one, since the first alternative holds. Its mean signed cumulative value is

$$
r_L=-\sum_z p_z\ln\bigl(p_z+(1-p_z)/L\bigr).
$$

The mean single-source values are H(X) and Δ. Their joint-source value is H(X)+Δ because the two sources determine T and X is independent of U. By subtracting the two-source cumulative values, the mean signed atoms at {{3}} and {{1,3}} are Δ−r_L and r_L. Thus, for every L,

$$
M=|\Delta-r_L|+r_L,\qquad (2A-\Delta)-M=2\min\{B,A-r_L\}.
$$

In particular r₁=0 and M=Δ at L=1. Each term in r_L increases to its term in A, so M tends to 2A−Δ. M stays at Δ until r_L exceeds Δ. If B=0, the bound is attained at every L, including examples with nonconstant U. If B>0, then m>1 and each occupied p_z<1. Thus A−r_L>0 and the bound is strictly above M at every finite L. When m=1 every quantity is zero.

## A sharp bound at fixed size

Rewrite the error as

$$
A-r_L=\sum_z p_z\ln\bigl(1+(p_z^{-1}-1)/L\bigr).
$$

Concavity of the logarithm bounds this weighted mean by the logarithm at its weighted mean argument. Since the sum of p_z(p_z⁻¹−1) is m−1, the finite shortfall satisfies

$$
0\le(2A-\Delta)-M\le 2\ln\bigl(1+(m-1)/L\bigr).
$$

The bound is sharp for **every** pair of integers L,m ≥ 1. Take U constant and V uniform on m values, independently of X. Then Δ=0, A=B=ln m, r_L=ln(Lm/(L+m−1)) and M=2r_L. For L=m=2 one gets M=2 ln(4/3) and a shortfall of 2 ln(3/2). This example also rules out a coefficient of one. For fixed m, the bound tends to zero uniformly over all joint distributions on at most m occupied values. If m=L grows in this uniform example, the shortfall is 2 ln(2−1/L), which tends to 2 ln 2. The fixed-support conclusion does not cover that sequence. More generally, the displayed bound tends to zero whenever (m−1)/L tends to zero.

## Rust implementation and computational cost

This note gives a population calculation and its finite exact-arithmetic check. Its assumptions describe a constructed joint distribution. Its rows supply the distribution itself. There is no train/test split, resampling or estimate of a physical population. The dedicated formula has no new Rust entry point. Its finite sum takes O(m) arithmetic operations, assuming each probability is already available. The Python reference independently enumerates all eighteen three-source antichains on each of q=Lm occupied rows. It scans those rows again to find every match event and uses exact integer products to compare the resulting atoms. At fixed dimension and number of antichains, the search visits O(q²) row pairs and stores O(q) rows. Multiple-precision operation cost also depends on the weights and on the sizes of the resulting integer powers. It runs offline. No timing or estimator-calibration claim is made.

Run the two commands below with Python 3. Compare each output to the accompanying stored result. The finite checks use 55 choices of distribution and alphabet size, including 25 attaining examples. All 11,034 local signed atoms are checked individually. Finite checks complement the general derivation. The argument concerns the signed, finite categorical construction and these source and target roles only.

```sh
python3 -I -S -B check_product_family.py
python3 -O -I -S -B check_product_family.py
```
