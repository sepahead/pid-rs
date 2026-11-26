# Reproduce the stimulus-resolution study

Sepehr Mahmoudian, 2026. Run the commands in the study directory. The Python calculations use the standard library. The first command checks the three-source decompositions, predictions and recorded Rust outputs without a network connection.

```sh
python3 -I -S -B check.py --self-test
python3 -O -I -S -B check.py --self-test
```

This route reads the original setting identities and the three observed target classes from the detailed results. For reconstruction it represents the three classes by zero, one and three spikes. Each calculation depends only on the class. This route therefore checks the archived class labels and the implementation on them. The distinct original-data route verifies all 651 responses, including the original counts within each class, by a digest of the exact 5,890-byte donor file. Supply the file you already have, or request its immutable published revision with the first command below. The download writes a new path. Give the second command the path to that file.

```sh
python3 -I -S -B check.py --fetch spikes_.dat
python3 -I -S -B check.py --data spikes_.dat --self-test
python3 -O -I -S -B check.py --data spikes_.dat --self-test
```

The two calculations agree on 216 exact rational products, the saturated classification counts and 3,906 held-level records. Each held-level record contains both forecast choices. The control suite alters a unit or nonunit product, swaps two methods, damages class and probability records and changes the measured input. The earlier published analysis of the same grid used two primary inputs. Its three target classes and uniform grid weights are used here. [Donor input](https://github.com/ModelDBRepository/180373/blob/655ac03999ecb5ce2b15f3b04cee4c250358a2ff/data/spikes_.dat) · [Study of the two original inputs](https://doi.org/10.3390/e24081021)

The original protected calculation had a separately fixed predicate, source and input. The active project calculator is its original source. The public second calculation uses the original event, order and comparison arithmetic. Its earlier host-specific command wrapper has been removed. The new entry compares each accepted output with both the second calculation and the saved records. These transfers preserve the initial numerical results and their scope. [Output format](output-format.md) · [Source identities](provenance.json) · [Two-method native build and comparison](rust-comparison/README.md)

To draw the figures, install the SVG-to-PDF program `rsvg-convert`. The PDF route uses the project's copies of the Source Sans fonts and the fontconfig backend. Pandoc and LuaLaTeX produce the standalone report. Use the repository checkout as the assets path when the study is in an independent projection.

```sh
python3 -I -S -B draw.py spikes_.dat figures --pdf
python3 -I -S -B build.py --output ../../../output/pdf/dendritic-stimulus-resolution.pdf
```

The vector graphics contain the actual setting counts and signed numerical comparisons. The native report uses a checked TeX rendering of its Markdown source. To reproduce that intermediate file after an editorial change, use `python3 -I -S -B build.py --write-body`. The original CPU readings, exact product files and figure inputs are separate from the build of the publication. [Report](README.md) · [Software citation](../../../CITATION.cff)
