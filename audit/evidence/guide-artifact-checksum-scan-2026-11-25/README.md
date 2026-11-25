# Three file checksums in the mathematical results guide

The full-history credential scan reported three fields in the guide at commit
45c4ef6f037f4b826230a065aab563119a744df1. Each field gives the SHA-256 checksum
of a published file. SHA-256 maps the file bytes to a 64-digit hexadecimal value.
The identifier and the file value can be checked together in the original Git
commit. All three values matched. The original scan reported a failure.
[Original job](https://github.com/sepahead/pid-rs/actions/runs/45580019430/job/139087422432)

| Original guide line | Published file |
|---:|---|
| 110 | [PDF of the quoted-state figure](https://github.com/sepahead/pid-rs/blob/45c4ef6f037f4b826230a065aab563119a744df1/audit/research/categorical-state-token/figures/quoted-token-boundaries.pdf) |
| 111 | [SVG of the same figure](https://github.com/sepahead/pid-rs/blob/45c4ef6f037f4b826230a065aab563119a744df1/audit/research/categorical-state-token/figures/quoted-token-boundaries.svg) |
| 171 | [Report on the categorical state token](https://github.com/sepahead/pid-rs/blob/45c4ef6f037f4b826230a065aab563119a744df1/output/pdf/categorical-state-token.pdf) |

The check reads each regular Git file and computes its checksum. It verifies the
complete key and value at the original line. The scanner policy names three guide
profiles and three specific key-value pairs. It uses the full manifest line and
the reported value for each pair. The current profile also checks against the
corresponding file in the checkout. A dated profile can retain the checksum of
an earlier published file.

To repeat the finite tests, use Python 3 and a local copy of Gitleaks 8.30.1.
Run the following command from a complete Git checkout that contains the original
commit. The scanner makes 78 paired comparisons with the original and current
policies. Each comparison checks the scanner exit status and the locations of
all findings. The tests include changed files, changed values, another field on
the same line and a neighboring field.

```sh
python3 -I -S -B scripts/check-guide-artifact-checksum-scan.py --scanner /path/to/gitleaks
```

Continuous integration repeats the tests with ordinary and optimized Python. It
also runs the original policy controls and the full Git history scan. The
finite checks apply to the named fields, files and scanner version.
