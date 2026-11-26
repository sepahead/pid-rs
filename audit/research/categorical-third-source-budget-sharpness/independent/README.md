# Independent finite count calculations

Sepehr Mahmoudian, 2026. Give the exact repository commit or release when using this calculation.

The count check assigns no sampling model. Each of the four columns is categorical. The first three columns are sources and the fourth is their target. Positive counts define the empirical distribution. Natural logarithms give nats. The measure is finite categorical shared exclusions. [Makkeh, Gutknecht and Wibral, revision 5](https://arxiv.org/abs/2002.03356v5).

Run `python3 independent_count_products.py` and compare the output with `binary-counts.json`. The computation enumerates all 18 nodes before it selects the five outside the downset of the first two sources. It groups the positive cells by agreement masks and by target value. It computes the exponentials of total-count-scaled mean redundancies with rational arithmetic, performs lattice inversion and then checks the exact gap. The four-bit rows give 16, 136, 816 and 3,876 distinct unsigned count tables at totals one through four. There are 1,196 tables with a positive conditional entropy and 3,648 with a zero gap. At totals two, three and four the smallest exponentials of the scaled positive gap are 16, 9 and 81/16. A second set contains 153 constructed tables attaining the proved minimum through total 18. The four-row exclusive-OR case rejects a pairwise-independence reading.

The separate fixed-distribution calculation examines 55 laws and lengths, including dependence in the finite pair. The 613 occupied rows give 11,034 local signed atom products. Its source identifies its exact inputs and selection. The stated panels overlap. None supplies a population performance estimate or a comparison of competing estimators. [Fixed-distribution argument](FIXED-DISTRIBUTION.md).
