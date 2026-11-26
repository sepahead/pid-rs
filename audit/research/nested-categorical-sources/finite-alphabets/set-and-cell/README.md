# Finite sharp bounds with one or two fine categories

Sepehr Mahmoudian · 2026

Each input is a matched pair of categorical readings on the same unit observations. The first reading is the proposed coarse reading. A violation occurs if the second reading takes the same value at two different coarse values. The mathematical question concerns the difference of two informative shared-exclusions cumulatives on the observed distribution. Multiply the difference in nats by the number of observations, then exponentiate. The written proofs give the least positive information difference using this positive rational product. Product one means that the information difference is zero. [Two available values](judge/FIRST.md) · [Exactly one value](judge/ONE-VALUE-FIRST.md) · [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149)

For at most two occupied fine values, the least product at a violation is 2N/(N−1), where N is the integer row count and N is at least two. For exactly one value it is N^N/(N−1)^(N−1). For two occupied values a violation first becomes possible at N=3. These bounds allow the number of coarse categories to vary. The proofs give the attaining distributions. A balanced binary distribution with arbitrary positive real weights can have a strictly positive gap as small as desired.

Python 3.14 and its standard library suffice. Each command needs a new output directory. One calculation uses explicit unions of sets of observation indices. A separate calculation uses the integer counts of the occupied pairs and their margins.

~~~sh
python3.14 -I -S -B judge/check.py candidate/from_cells.py ordinary
python3.14 -O -I -S -B judge/check.py candidate/from_cells.py optimized
cmp ordinary/RESULT.json RESULT.json
cmp optimized/RESULT.json RESULT.json
~~~

The two modes compared 63,601 ordered pairs through seven labelled observations. They checked the exact minimum and its equality cases separately for one and for two occupied fine labels. They also checked a four-observation counterexample to extending the binary bound to three fine categories. The program has no sample identity or independence assumption beyond the observed unit table. The input distributions in this enumeration are synthetic. The real-valued formulas and their limits have written proofs. No runtime claim for a deployed sensor follows from this finite enumeration.
