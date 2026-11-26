# Evidence and reproduction

Sepehr Mahmoudian, 2026. Cite *When a third-source information bound is attained* with the exact repository revision. [Study](EXPOSITION.md) [Software citation](../../../CITATION.cff)

## Scientific object and original sources

The paper-defined object is the finite categorical pointwise shared-exclusions decomposition of Makkeh, Gutknecht and Wibral, *Physical Review E* 103, 032149 (2021), arXiv:2002.03356v5. The retrieved defining PDF has SHA-256 5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6. It uses base-two logarithms. The study uses the natural logarithm throughout, which expresses the same additive relations in nats. The antichain order also has a logical interpretation in the work of Gutknecht, Wibral and Makkeh. [Defining publication](https://doi.org/10.1103/PhysRevE.103.032149) [Versioned source](https://arxiv.org/abs/2002.03356v5) [Order source](https://arxiv.org/abs/2008.09535v2)

In §VI.C and Table III, the defining paper already gives an exactly copied binary target, a noisy second source, a negative noisy-source unique mean and an equal positive synergy. The four-cell distribution comes from Finn and Lizier, whose own numerical values use a different functional. The September project report had already derived the two-source local and average synergy for a target containing the first source and an arbitrary residual. Its equation (19) factors the numerator difference, and equations (28)–(29) already evaluate the RndErr probabilities and ratios. The present proof places the four signed atoms in the 18-position order with a constant middle source and an exactly copied target. Individual vanishing of the five selected means follows from the earlier factorization. Two comparison tables give equal entropies for all 16 subsets. [September target-copy report, equations (1), (2), (19), (28) and (29)](https://github.com/sepahead/pid-rs/blob/6a9f087be84bc21a89ff51e7da8e626e6883d73e/audit/evidence/finite-target-copy-mgw-synergy.md) · [Makkeh, Gutknecht and Wibral, §VI.C and Table III](https://arxiv.org/pdf/2002.03356v5#page=11) · [Finn and Lizier, §5.4](https://doi.org/10.3390/e20040297) · [Printed values, exact arithmetic and the existing Rust regression](independent/copy-target/PRIOR-EXAMPLE.md)

The archived report *Source redundancy and SxPID3 atom budgets* gives the five-position cut, its component entropy identities and the earlier varying-alphabet limit. Its preserved Markdown SHA-256 is afaebc3b5b350459690f0b0b5d12e49781ac8665d605efe753a80eb9a0d277fe. The archive retains its dated evidence and limits. This study rederives the equations from the original events and characterizes strictness, the least positive integer-table gap and an occupied-support bound on a separate approaching family. The related nested categorical study uses a different directed entropy deficit, different event and different attaining distribution. [Historical scope](../../archive/shared-exclusions-research-findings-20261001/ARCHIVE.md) [Nested-source study](../nested-categorical-sources/EXPOSITION.md)

The observation domain contains three finite labelled sources and one finite target. The general equality proof uses a normalized finite distribution and compares only supported outcomes. The exact minimum restricts probabilities to nonnegative integer counts divided by their positive total. A row can be repeated within the table; the numerical meaning of its weight is its number of observations. Every finite choice of source and target alphabets obeys the lower bound. The example attaining it for each feasible pair of totals and occupied third labels chooses the other alphabets. Restricting their sizes further can raise the minimum. All constructed inputs here define complete artificial empirical distributions. There is no held-out, fitted, resampled or selected biological dataset. A continuous shared-exclusions estimator, another categorical decomposition or a sampling claim needs separate arguments.

## Reproduce the exact arithmetic

From this directory run each command and compare the complete output with the stored result.

    python3 -I -S -B verify.py --self-test
    python3 -O -I -S -B verify.py --self-test

The verifier uses Python's standard library. The exact values are reduced rational numbers. It computes event unions as sets of supported tuples and recovers all 18 signed pairs by recursively subtracting lower contributions in logarithmic coordinates. Division of rational arguments performs this subtraction exactly. The code counts each conditional entropy directly from the input cells. Separately, it obtains the support of each atom from collections of agreement masks and compares every predicted zero or positive value with the rational inversion. The basic invocation without the self-test flag runs the census and all constructed sharp examples. The stored output includes the adverse controls.

A separate exact check holds the first two sources and the target constant. With four observations and two occupied third labels it checks every positive labelled split. It computes all 18 signed atoms and evaluates the binary entropy separately from the two integer counts. All signed atoms vanish. The smallest gap has count-cleared factor $65536/729$, while a table with freely chosen other alphabets attains $81/16$. Both are exponentials of four times the gap in nats. The equal split has two equal counts attached to different labels and gives factor 256. The example was known before this finite check. [Source](alphabet_scope.py) [Exact outputs](ALPHABET-SCOPE.json)

    python3 -I -S -B alphabet_scope.py --self-test
    python3 -O -I -S -B alphabet_scope.py --self-test

The predeclared finite domain consists of all labelled binary tables with one, two or three observations, all pairs of sample sizes and occupied labels from 2 to 16, and three specified cases at total 25. An earlier exact integer implementation independently computed finite unions by inclusion–exclusion, inverted its set-labelled order, and returned its component values. Its 1,098 invocations include seven overlapping controls beyond the primary census and sharp tables. The two arithmetic procedures share the input law and source semantics, and both use Python rational arithmetic. A separate mathematical derivation used the singleton-third lower cover. This agreement tests specific derivations and finite inputs; no human or institutional review is claimed. Candidate selection was exploratory before the finite test condition was recorded. No formal theorem, result in Rust, end-to-end refinement, independent population inference or deployable estimator follows from these results.

## Construct and reproduce the figure

The table at left has four occupied tuples. Each right-panel marker fixes only the total of six and the indicated number of occupied third labels. The first two source alphabets and the target alphabet can vary. The panel reads the exact count-cleared factors from the same numerical output. A decimal conversion positions and labels each point in nats. At two occupied labels the left table attains the plotted first value. A zero entry is an unoccupied tuple. The figure does not interpolate fractional alphabet sizes. The source is separate from its native vector and embedded PDF.

    python3 -I -S -B figures/draw.py --data RESULT.json --output positive-budget-gap.svg
    env SOURCE_DATE_EPOCH=1795564800 TZ=UTC rsvg-convert -f pdf -o positive-budget-gap.pdf positive-budget-gap.svg
    python3 -I -S -B build.py --output categorical-third-source-budget-sharpness.pdf

The publication build checks that the tracked native body equals the conversion of the Markdown. It uses the repository's styles and fonts, Pandoc and LuaLaTeX. It prints each mathematical expression literally and handles actual prose links separately. It checks that the final two typesetting passes have identical PDF bytes. The observed figure renderer was librsvg 2.62.3 with Cairo 1.18.4. Exact PDF reproduction also depends on installed font and typesetting versions.

## Negative results and control scope

- If the target reveals the third source and the first two are constant, the conditional uncertainty including the target vanishes although the one without it is positive.
- If source 1 or source 2 alone determines the third label, dropping that conditioning source can introduce a false conflict.
- In a four-row distribution with a target equal to source 1, the mean misinformative singleton-third component exceeds its informative component. Thus the zero/positive inclusion does not compare component sizes. Revealing the third source gives a counterexample to the reverse support inclusion.
- Adding an unused third-label name to a two-label six-observation table gives an incorrect raised bound if the declared rather than occupied alphabet enters the calculation. The correct table attains its exact factor 256/81, which is less than four.
- Doubling every count preserves the underlying distribution and the gap in nats. It changes the count-clearing exponent and its fixed-total benchmark. Empty, all-zero, negative, Boolean, fractional and malformed count inputs are refused. Positive tables can contain stored zero entries.

## Review coverage

The scientific review considered the following 50 questions. The labels describe coverage and do not give extra statistical samples or independent votes.

1. Identity of the finite categorical functional, target identity, three source roles, grouping convention, group versus antichain, direction of the order, lower-set membership, maximal strict predecessor, uniqueness of finite inversion, number of valid nodes.
2. Occupied support, normalization, conditional source support, zero-probability outcomes, total count, integer versus real weights, singleton alphabet, unused labels, repeated rows, equal-probability special cases.
3. Conditional entropy without target, conditional entropy with target, informative sign, misinformative sign, signed cancellation, averaging before magnitude, both signs of the net, empty residual mass, target-conditioning counterexample, source-conditioning counterexamples.
4. Existence of a conflicting stratum, two distinct labels, marginal and conditional denominators, positive integer minima, product identity at fixed sum, integer balancing, sharpness at the smallest total, sharpness when every third label is distinct, feasible alphabet of the first source, exact attainability versus approaching a limit.
5. Auxiliary list independence, series convergence, support implication, failure of the converse, zero versus numeric dominance, independent event representation, finite census coverage, numerical locating of plotted points, comparison to simpler conditional information, absence of task or sampling validation.

Ten alternatives were considered. No change would leave equality and the varying-alphabet hypothesis undetermined. Direct conditional entropy decides whether an ambiguity exists but does not compute signed atom mass. The five abstract component budgets show nonnegativity and reduce the question to overlaps. The singleton node locates an overlap at a concrete conflict. The positive-list series handles each node before averaging. Integer optimization yields an explicit sharp constant. Synthetic attainment establishes that no better universal bound at the same counts is possible. Small exhaustive enumeration can falsify mistakes in these claims. Floating-point simulation cannot decide exact zeros. A formal proof would require a separately qualified categorical event model and a correspondence argument. The report uses exact analytic derivations, constructed equality tables and finite arithmetic. The census is supplementary.

## Matched categorical tables

The two added example tables are constructed empirical distributions, each with four observations. They use a copied target and a constant middle source. The resulting Shannon entropy vectors agree across all 16 subsets. The five signed means sum to zero in each table. Their five-position absolute masses in nats are one half of the natural logarithm of four thirds and zero. All finite counts and signs refer to this categorical shared-exclusions measure. Earlier examples of equal entropy diagrams and distinctions among decompositions have their own defining functions and laws. [Earlier entropy-diagram examples](https://doi.org/10.3390/e19100531) [Deterministic target and source dependencies](https://doi.org/10.3390/e20030169)

From the study directory, run the following commands. Repeat with `-O` immediately after `python3`. Each script reads only its stated data and source. The first two use the same 18-position implementation and the last uses a separate finite implementation. All three share the original scientific definition. The selected two tables were known in advance. Their comparison gives finite information about these tables. The zero-mass statement for the whole copy-target family uses the written proof. [Inputs and expected finite records](independent/copy-target/REPRODUCE.md) [Separate expected output](independent/paired-entropy/matched-normal.json)

```sh
python3 -I -S -B independent/copy-target/paired_counts.py --reference verify.py --self-test
python3 -I -S -B independent/copy-target/copy_support.py --reference verify.py
python3 -I -S -B independent/paired-entropy/matched_shannon.py
python3 -I -S -B figures/matrix_figure.py --data independent/copy-target/PAIRED-COUNTS.json --output copy-target-counts.svg
env SOURCE_DATE_EPOCH=1795564800 TZ=UTC rsvg-convert -f pdf -o copy-target-counts.pdf copy-target-counts.svg
```

The support calculation checks 80 nonempty two-by-two count matrices, 728 two-by-three matrices and 511 binary three-by-three support patterns. Some distributions appear in more than one set when unused labels are removed. The figure shows their separate two-table comparison. A linear scan of occupied cells tests the zero-mass condition after the row and column counts are available. The exact positive value also uses the counts. These calculations neither fit a model nor supply a population test or runtime guarantee.
