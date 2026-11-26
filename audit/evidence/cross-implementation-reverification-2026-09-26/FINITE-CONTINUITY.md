# What the September continuity experiment measured

Sepehr Mahmoudian, 2026. Cite this report with the repository commit or release. The quantities are local cumulative shared-exclusions information for finite categorical sources and a finite target, in nats. The defining probabilities follow the paper by Makkeh, Gutknecht and Wibral. [Defining paper](https://arxiv.org/abs/2002.03356v5)

## Research question

Which local changes in this fixed set of count tables attain the continuity bound exactly? The answer distinguishes an exact equality from a close decimal approximation. No new PID functional is introduced.

## Inputs and result

The original September program used random seed 1 and attempted 4,000 draws. Each draw had two or three sources, with source and target alphabet sizes of two or three. It formed two integer count tables on the same occupied joint support and with the same total count D. Its binary floating-point random steps selected these inputs. The measurements below first verify all the resulting integer vectors against an execution of the original source. These are generated finite examples, and all their rows define the two distributions. [Original experiment](https://github.com/sepahead/pid-rs/blob/927e5138d23e0bd24b70f8df0fd38e610456a244/audit/evidence/cross-implementation-reverification-2026-09-26/python/check_one_lambda.py)

Let M be the smallest positive cell count in the original table. Let h be the sum of counts removed from its donor cells. The comparison requires 0 < h < M and a sum of absolute cell differences equal to 2h. Write B = M/(M−h) and Λ = ln B. For each supported row, a family names alternative groups of sources that can match that row. No member group contains another. The event E is the union of those matches. The event C fixes the row's target. Write a and a′ for the respective counts of E in the two tables, b and b′ for counts of E intersected with C, and c and c′ for counts of C. All six counts are positive. Three positive factors give the absolute changes of the informative, misinformative and signed cumulative values when their absolute natural logarithms are taken.

$$
U_+=a/a',\qquad U_-=c'b/(b'c),\qquad U_s=U_+/U_-.
$$

The exact bound |ln U| ≤ Λ is equivalent to max(U,1/U) ≤ B. Integer cross-multiplication tests both direction and equality without a logarithm. Across 3,999 admissible original draws and 634,112 row/family pairs, all 1,902,336 comparisons passed. Exact equality occurred 39 times in the informative component, 51 times in the misinformative component and zero times in the signed component. All 39 informative equalities lost exactly h counts from a minimum-weight match. All 51 misinformative equalities lost h counts from a minimum-weight intersection while the target count stayed fixed. These are observations on this finite panel. Its 3,999 full ordered pairs of tables have SHA-256 c9b2b4f367d452c29d7d39261156c9373f3aad34e0dcbb052b3127681287a7cd in the program's declared encoding.

## A rigorous maximum on these finite inputs

For a signed factor put F = max(U_s,1/U_s), so that 1 ≤ F ≤ B. The gap between its normalized absolute change and one satisfies

$$
1-\ln(F)/\ln(B)\;\ge\;(B-F)/(B(B-1)).
$$

Indeed ln(B/F) ≥ (B−F)/B and ln B ≤ B−1, by elementary bounds on the logarithm. This rational lower bound for the gap leaves two potential competitors to the rounding threshold 0.99999965435. For each, divide F and B by exact powers of two so that the remaining fraction s is in [1,2). With z=(s−1)/(s+1), use 24 odd-power series terms for ln s and the same calculation at z=1/3 for ln 2. The omitted tail lies between zero and 2z⁴⁹/[49(1−z²)], since every omitted denominator is at least 49. Directed rational arithmetic gives the winning enclosure [0.9999996544072924, 0.9999996544072925]. Only trial 776, flat row 20, joint tuple (1,0,0,2), all three sources in one group, can attain it. Its factor is 878946942652088757/727729676370096637 and B is 1000000000000/827956266271. Thus the signed maximum, rounded to ten decimal places, is 0.9999996544.

## A strict value inside the old equality tolerance

The original 80-place Decimal program printed the same rounding and counts. It counted a ratio as equal when the ratio was at least 1−10⁻⁶⁰. It reported a violation only when the component maximum exceeded 1+10⁻⁶⁰. It also used three Python assertions for its input premises, all removed under Python optimization. The complete original program gives the same output in both modes on these genuine inputs. An explicit malformed premise is rejected by the original assertions in ordinary Python and accepted under optimization. The current integer checker uses conditions that execute in both modes.

For a valid strict control, put H=10⁷⁰. Give a three-valued first source counts (H,H,H), a constant second source, and a constant target. The perturbed counts are (H/2+1,H−1,3H/2). Select only the first source, at its first category. Then h=H/2 and B=2. Its normalized informative change is ln(H/(H/2+1))/ln 2. It is strictly less than one, with deficit ln(1+2/H)/ln 2 < 4/H < 10⁻⁶⁰. Perturbing instead to (H/2,H,3H/2) gives exact equality. These examples show why the integer decision is needed. The signed component for a constant target vanishes; this example concerns the informative component.

## Rust implementation and computational cost

This is an offline verification of local cumulative values. There is no new Rust estimator or public API. The input search scans every admissible supported row and every nonempty antichain, four for two sources and eighteen for three. The reference builds finite matching sets from the product alphabet. Each event count can require scanning that alphabet. Multiple-precision cost depends on the integer lengths. The total of 1,902,336 comparisons describes this particular panel. The only logarithm bounds in the final comparison concern the two surviving signed factors and their denominators. No production-runtime timing or statistical calibration is claimed.

Run the [independent integer checker](python/exact_local_bound.py) with Python 3. Repeat the command with the `-O` flag. Compare both outputs with the [stored exact result](results/one_lambda_independent.json). Run the [table identity checker](python/original_panel_identity.py) with the [September source](python/check_one_lambda.py) and the stored exact result as its two arguments. It checks all original table inputs before the first September logarithm for each table. Compare its output with the [table identity result](results/one_lambda_original_panel.json). The [original September numerical printout](results/check_one_lambda.txt) is also available. The two computations share the original input design. Their agreement does not establish a population theorem, equality for every admissible table, or a result for Möbius-inverted PID atoms.

## Rust implementation and computational cost

These two Python checks compare exact integers and rational numbers. The stable Rust implementation of the categorical shared-exclusions functional reports estimates in nats. The checker has no production Rust API or feature gate. The table generator uses two or three sources, a target and two or three values per variable. It visits each occupied row and each source family in the seeded panel. The cost grows with the number of visited pairs, the number of occupied cells summed for each event and the bit length of the integer products. The computation is an offline check. It has no training, resampling or online timing claim. [Software citation](../../../CITATION.cff)
