# Format-file group fixture repair

The 9 September 2026 local exact PDF check stopped because its test fixture compared
the format file's group with the process's effective group. The captured file group was
`0`; the expected process group was `20`. These values need not be equal.

The [production capture](../../scripts/check-mathematical-results-guide-pdf.sh) correctly
records the file's `st_gid` and checks stable file metadata. The repair changes one
expectation in the [real-file fixture](../../scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py)
to `format_path.stat().st_gid`. The synthetic profile-selector data and production
permission, link, identity, hash and stability checks remain unchanged.

## Observed validation

Both default self-test entrypoints completed with exit 0 and empty stderr.

| Python mode | Elapsed seconds | Reported controls | Reported hostile mutations |
|---|---:|---:|---:|
| Normal | 3.292448417 | 80 | 61 |
| Optimized (`-O`) | 4.649453375 | 80 | 61 |

The two 421-byte stdout streams are identical. Their SHA256 is
`f812bb02c342ee7beca773ea5ae65a051e68a688e2ff856537abadbff80acb7f`.
These calls include actual capture, writable-file, hardlink, symlink and output-parent
fixtures, plus profile selection and dispatch checks. They run no PDF renderer or Lean
compiler. The fixture removes its temporary files, so the successful calls do not retain
a fresh observation that the particular file group differed from the process group.

## Retained failure and scope

The failed aggregate remains a failed attempt. Its earlier 87-page workflow PDF check
passed, but its later guide build and subsequent publication checks were not reached.
The focused repair checks do not complete those missing checks. A later aggregate must
use the changed source and a separate execution record.

The original source SHA256 is
`d9a08a49fd59382221b7871ede0a8ebf3def1de7084912ea287726dd7a67f845`;
the repaired source SHA256 is
`6179a485fa7c9ed1dc423337369262354dd1939d08762a38d352ab96422cdc02`.
Full permitted execution records, source preimages and independent reviews remain in
the local recovery archive; the ignored session handoff records their locations. The
focused execution archive has manifest SHA256
`2b50c01e46bc114b218d876fce220afb4f3fa206421637986366c2ccfe034f84`.
This record is a public summary, not a replacement for those archived bytes.

Hardcoding group `0`, accepting either group, changing file ownership, or removing the
metadata comparison would hide the incorrect assumption. Those routes were rejected.
The repair changes no PDF content, PID definition, estimator, numerical result or theorem.
