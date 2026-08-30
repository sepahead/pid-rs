# Sensor-placement guide hosted OpenAction correction

## Scope

This note retains one negative hosted result for the PDF of
`PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md`. It records a renderer-compatibility correction. It
does not change the guide's mathematics, application claims, source citations, or visual design.

## Exact failed observation

GitHub Actions [run `33326355121`](https://github.com/sepahead/pid-rs/actions/runs/33326355121),
job `99297111398`, evaluated pid-rs commit
`855605a2a2098fa82fccb07521bae5cc382fa747` on Ubuntu 24.04. The formal-PDF job used the repository's
pinned Pandoc 3.10.2 path and the runner's installed TeX Live 2023 packages. The canonical 47-page
PDF passed its object check. The hosted rebuild completed with SHA-256
`1396ee8bd197404391262173526e0d7da653b9699e62f12b894d89f8728cf58b`, but its object check then
failed with this exact diagnostic:

```text
PDF object check failed: catalog OpenAction is not a bounded internal GoTo
```

The failed job did not publish the rebuilt PDF as a retained repository artifact. Therefore, the
observation establishes only that the rebuilt catalog value failed the checker's typed dictionary
and `/S /GoTo` predicate. This note does not claim the unretained object's exact raw syntax.

## Cause boundary and selected repair

The same hosted job successfully exercised the repository's existing LPPL-licensed tagpdf
OpenAction compatibility source for the mathematical results guide. That source adds the upstream
structure-aware OpenAction update only when the installed tagpdf lacks its native implementation;
current tagpdf keeps its native path. The sensor-placement builder had not included this already
reviewed compatibility source.

The selected repair reuses those exact compatibility bytes in the sensor-placement build. The
builder, its source-derived trailer identifier, and the checker now all bind the compatibility
file. This is narrower than accepting multiple OpenAction shapes in the checker: both old and
current tagpdf must still produce one typed internal `GoTo` action to page one. Exact mode remains a
byte-equality requirement. Cross-toolchain mode still validates both complete PDF object graphs
before it can compare their reviewed text and geometry relation.

## Required closure evidence

The correction is not complete on the strength of this explanation. A descendant commit must pass
all of these checks:

1. the existing tagpdf compatibility self-test;
2. the sensor-placement builder and exact local PDF check;
3. the complete formal-PDF aggregate in hosted Ubuntu cross-toolchain mode; and
4. the complete repository CI matrix at the exact descendant commit.

Until those checks pass, the failed hosted result remains a negative result and main promotion is
blocked.
