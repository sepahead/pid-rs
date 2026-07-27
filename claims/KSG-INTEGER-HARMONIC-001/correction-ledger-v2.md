# Correction ledger for `KSG-INTEGER-HARMONIC-001` revision 2

## C1 — frozen bit-oracle drift

- **Error:** revision 1 left 13 KSG/ISX/PID2/PID3 constants frozen at pre-integration values.
- **Detector:** four unchanged `parallel_bit_identity` tests fail.
- **Smallest witness:** the exact old/new arrays in
  `failures/stale-parallel-bit-oracles.md`; 12 fields differ and one KSG midpoint field does not.
- **Dependency reach:** E4 serial/parallel evidence and every claim that called the full suite
  clean. PID2 fields also reach `PID2-REPRESENTED-SUM-001` revision 2.
- **Load-bearing status:** blocking for executable completion; not a counterexample to the exact
  harmonic theorem.
- **Correction:** capture a literal non-`parallel` serial oracle, update only changed constants,
  retain the unchanged midpoint explicitly, then replay the same assertions with `parallel`.
- **Regression:** the four tests fail before correction and pass in both configurations after it.
- **Residual boundary:** frozen bits are deterministic regression values, not scientific truth.

## C2 — mislabeled arithmetic route and singular worst-cell wording

- **Error:** revision 1 assigned `16` eps/`764` asymmetries to a “compensated” four-term route and
  described one worst cell.
- **Detector:** independent evaluation of plain left association, Neumaier four-term reduction,
  and sorted range association.
- **Smallest witness:** `16/764/8` versus `8/0/39` versus `8/0/40`; the selected route has 40
  maximum-attaining cells.
- **Dependency reach:** route provenance and numerical-evidence wording.
- **Load-bearing status:** non-load-bearing for the already selected range formula; load-bearing
  for evidence integrity and future association discrimination.
- **Correction:** retain `route-memo-exact-numerics-erratum-v2.md` and freeze multiplicity 40.
- **Regression:** checker and Rust corpus test reject a changed multiplicity or association.
- **Residual boundary:** all association routes share one prefix/fixture and are correlated.

## C3 — incomplete generator custody

- **Error:** the standalone checker and Rust KSG fixture test validate the fixture sidecar but do
  not compare its embedded generator SHA-256 with the live generator bytes.
- **Detector:** source inspection; current embedded and live digests happen to agree.
- **Smallest witness:** a generator-byte mutation or resealed fixture metadata can evade the
  standalone relationship check even though the separate CI generator replay catches stale bytes.
- **Dependency reach:** E2/G1 fixture provenance, not the symbolic theorem.
- **Load-bearing status:** blocking for the stronger standalone custody claim.
- **Correction:** bind generator bytes, schema, bounds, and metadata in Python and Rust; copy the
  generator into isolated mutation roots.
- **Regression:** generator drift and resealed embedded-hash mutations fail closed.
- **Residual boundary:** generator and checker can still share the harmonic identity; hashing does
  not create mathematical independence or external custody.

## C4 — marker-preserving live shadowing

- **Error:** source checks require correct strings but do not establish which live definition
  reaches the output.
- **Detector:** live-code counterexamples that retain every required marker and then shadow
  `lower`/`upper` or overwrite `out[argument]`.
- **Smallest witness:** examples retained in `failures/evidence-gate-gaps.md`.
- **Dependency reach:** the claimed 16 source mutations and source-only conformance wording.
- **Load-bearing status:** blocking for that wording; compiled corpus behavior remains a separate
  partial backstop.
- **Correction:** add exact binding/write-count checks and named shadow mutations, plus compiled
  tiny/corpus witnesses.
- **Regression:** each mutation is accepted before and rejected after the checker change; compiled
  tests reject the semantically wrong source.
- **Residual boundary:** a textual checker is not a Rust semantic proof and must remain labeled
  accordingly.

## C5 — serial/parallel test gate mismatch

- **Error:** the frozen-reference file says it runs in serial and parallel configurations, but its
  file-level configuration requires `parallel`.
- **Detector:** direct source inspection and the parallel-enabled failure replay.
- **Smallest witness:** no test from that file exists in an `experimental-pipelines` build without
  `parallel`.
- **Dependency reach:** S1/P1 and E4 wording.
- **Load-bearing status:** blocking for an independently demonstrated serial-to-parallel equality.
- **Correction:** make the file compile with `experimental-pipelines` alone, capture serial, then
  rerun with `parallel`.
- **Regression:** test enumeration and frozen values appear in both feature profiles.
- **Residual boundary:** two builds on one target do not establish cross-platform bit identity.

## Preserved revision-1 artifact identities

| Artifact | SHA-256 |
|---|---|
| `call-site-map.md` | `048aaa4209f5c42616f18339775c463f1ac45fe7d25581c7b9d37d571d79c5a6` |
| `claim-v1.md` | `726907d19af21db00f3b4245722ac7a0d83b7e6df814aa3e589db47624344c44` |
| `obligations.md` | `b22e061070d16e69a39ede6f367a01c600b9c917ab199debc5ebca267b3b502e` |
| `routes.md` | `23b521232290b30c5d346b42f8cc55ecb1c5f639607a4fa03496cbdd3d1fe256` |
| `route-memo-exact-numerics-2026-07-25.md` | `1487761f2da443771854a1ad61b25042bb18267d68a67452e43d3c3a89d7cc7e` |
| `evidence-matrix.md` | `f9de6f6ebdd6fe30887c34e3abedef504ffbd2bba5e113a70f22a8f0b004b4fc` |
| `implementation-v1.md` | `83ee2a03b55ebc2161c3fec6dfe9a40680e8fae0b0bcebb01d5a1533f6872440` |
| `decision.md` | `0dabc4d4a0247cf55aa03f433bc47eab6f8b2f245824d27da0c7927ce30b79fe` |
