# Reproduce the two categorical calculations

The reference named `verify.py` is the general 18-position event and inversion program in the study *When a third-source information bound is attained*. Its SHA-256 digest is `00b52c8e5e514d3bac05190352489aa6954814e06efff0b321cacafdb7122940`. Each program below checks that digest before it loads the reference. Python's standard library is sufficient.

From this directory, replace the path in the following commands with the path to that exact source. Each scientific output is compared as bytes. Both interpreter modes exercise the same full set of predicates.

```sh
python3 -I -S -B paired_counts.py --reference /path/to/verify.py --self-test > paired-run.json
cmp paired-run.json PAIRED-COUNTS.json
python3 -O -I -S -B paired_counts.py --reference /path/to/verify.py --self-test > paired-optimized.json
cmp paired-optimized.json PAIRED-COUNTS.json
python3 -I -S -B copy_support.py --reference /path/to/verify.py > support-run.json
cmp support-run.json COPY-SUPPORT.json
python3 -O -I -S -B copy_support.py --reference /path/to/verify.py > support-optimized.json
cmp support-optimized.json COPY-SUPPORT.json
```

The pair of tables and their predicted values were known before the first check. The support formula was written after inspection of that pair and before its separate finite sweep. The two programs read one shared 18-position implementation. They cannot provide an independent test of all its assumptions. A proof from the finite source events is in the accompanying note. The signed source and target roles are part of each predicate. [Copy target and support condition](COPY-TARGET.md) · [Significance and alternatives](SIGNIFICANCE.md)
