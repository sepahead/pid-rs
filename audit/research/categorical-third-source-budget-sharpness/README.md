# The finite categorical third-source budget

Sepehr Mahmoudian, 2026. The scientific report *When a third-source information bound is attained* gives the equality condition for all finite categorical distributions, the least positive gap when only the total count and occupied third-alphabet size are fixed, and tables that attain it. The bound applies to every finite choice of the other alphabets. Attainment can require those alphabets to have enough labels. It also shows why the earlier varying-alphabet family needs an explicit independence and support condition. [Report source](EXPOSITION.md) [Report PDF](../../../output/pdf/categorical-third-source-budget-sharpness.pdf)

Run the exact arithmetic and all altered-output controls in this directory.

    python3 -I -S -B replay.py --self-test
    python3 -O -I -S -B replay.py --self-test
    python3 -I -S -B alphabet_scope.py --self-test
    python3 -O -I -S -B alphabet_scope.py --self-test

The expected output identifies 968 small binary tables, 123 attaining examples and eight refused changes to the stored finite report. The reference uses set unions, exact rational products and a positive total integer count. The stable Rust categorical routine calculates averaged atoms from complete integer-labelled observation rows. The report describes its public route and resource contracts. The universal lower bound requires only the table total and the number of occupied third labels. The second script checks all three two-label splits of four observations when the first two sources and the target are constant. This restriction raises the minimum. [Fixed-alphabet outputs](ALPHABET-SCOPE.json) [Exact values](RESULT.json) [Evidence, cost and reproduction](EVIDENCE.md) [Software citation](../../../CITATION.cff)

## A copied target and two matched tables

Makkeh, Gutknecht and Wibral had already exhibited a binary copied target with a negative noisy-source unique contribution and equal positive synergy. Their RndErr uses Finn and Lizier’s four-cell distribution. The September report already gave the two-source synergy formula and evaluated the same four cells. Here a constant middle source places those atoms in the 18-position order. Equation (19) of the earlier report then gives the condition for each of the five selected means to vanish. Two tables with identical Shannon entropies exhibit different absolute masses. [Earlier two-source identity and worked example](https://github.com/sepahead/pid-rs/blob/6a9f087be84bc21a89ff51e7da8e626e6883d73e/audit/evidence/finite-target-copy-mgw-synergy.md) · [Makkeh, Gutknecht and Wibral, §VI.C and Table III](https://arxiv.org/pdf/2002.03356v5#page=11) · [Finn and Lizier, §5.4](https://doi.org/10.3390/e20040297)

With the second source constant and the target equal to the first source, two empirical tables have the same 16 Shannon subset entropies and zero prediction error from the first source. In each table the five signed means sum to zero. Only the first table has two nonzero, opposite means and positive absolute mass. The paper gives both tables and the support test. A separate application uses 117 observed robot-wrist records. [Source comparison](independent/copy-target/PRIOR-EXAMPLE.md) · [Measured application](../robot-wrist-copied-target/README.md) · [Worked example](EXPOSITION.md) · [Exact checks](independent/copy-target/REPRODUCE.md) · [Separate calculation of all 18 positions](independent/paired-entropy/matched_shannon.py)
