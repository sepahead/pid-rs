# Print edition of the strict neighbour-count study

**Sepehr Mahmoudian · 25 November 2026**

The paper prints the complete mathematical source, its five-row figure, the five named stock Lean declarations with their observed axioms, and the following reproduction guidance. The two primary estimator papers retain their own scientific claims and authors. Include the exact source commit or release when citing this report. [Scientific study](README.md) · [Standalone PDF](../../../output/pdf/strict-neighbour-count-geometry.pdf) · [Software citation](../../../CITATION.cff)

<!-- upper example -->
For example take three rows with first source $1,2,4$ and second source $2,4,8$. For the literal upper bound the target values are $1,2,4$. For the open upper bound take $\varepsilon=1/8$, so the target is $9/8,18/8,36/8$. From the row with first source two, the two source distances are one and two. The perturbed target distances are $9/8$ and $18/8$. At rank one the radius is $9/8$ and the count pair is $(2,1)$. At rank two it is $18/8$ and the pair is $(3,2)$. Every row gives the same respective upper terms. The exact means at ranks one and two are $3/2,1/2$ nats for the literal version and $1/2,0$ nats for the open version. [All-rank exact computation](whole_upper.py)
<!-- end upper example -->

<!-- print supplement -->
## How to check the results

Run the finite reader from the study directory with `python3 -I -S -B check.py --self-test`. It checks the small coordinate grid, both three-row examples, the all-rank upper constructions and the actual five-row report. It also sends eight altered inputs to the original finite judge and requires a specific refusal for each one. For the separate Rust report, the updated reader compares all 72 quantiles and the two undefined-slope totals, and refuses 18 altered records. A second run with `python3 -O -I -S -B check.py --self-test` must return the same result.

To check the formal result, use unmodified Lean 4.34.1. The proof, model and observer have separate sources. The observer uses the general theorem and checks eight concrete predicates. It includes positive single-shell examples, the empty list, the zero-radius case and a positive multiple-member shell. Another source claims the wrong count for a valid shell. Its compilation must fail for that assertion. Run the following command after substituting the root of an unpacked stock release for `LEAN_ROOT`.

~~~sh
python3 -I -S -B replay.py --toolchain LEAN_ROOT --self-test
~~~

The stock checker loads compiled imports and checks safe, nonpartial declarations again. A declared axiom supplies its type. The program compares the individual axiom lists and both stock displays with their expected records. The first display omits eleven deep subterms in the witness proof. A separate stock display expands them. The compiled object and the fresh kernel replay determine the checked theorem. Arithmetic on approximate real data, population calibration and a general sharp lower bound on the mean remain separate questions. [Full formal evidence](EVIDENCE.md) · [False assertion](lean/Contradiction.lean)

The Rust client uses the public experimental continuous estimator on two source columns and one target column. Its output includes the mean and summaries of local values and counts. Its successful run does not show a row-labelled local series. The exact table in this report comes from a separate integer-distance calculation. The complete Rust record and source are supplied. [Public client](native/src/main.rs) · [Returned summaries](represented-report.json) · [Independent row calculation](two_arm.py)
<!-- end print supplement -->

The native build uses Pandoc, LuaLaTeX, the shared repository fonts and the published native figure. It checks the exact study source, five-row table of formal axioms, SVG and PDF, plus the Markdown-to-TeX correspondence. From this directory run the following command.

~~~sh
python3 -I -S -B build.py --output strict-neighbour-count-geometry.pdf
~~~

For the figure alone, use `figures/draw.py --output counts-and-distances.svg` with Python. The scientific source gives both row-count and resource assumptions. The recorded complete Rust clean build and run includes compilation and startup. The separate publisher timings cover document creation. [Sources and measured scope](EVIDENCE.md)
