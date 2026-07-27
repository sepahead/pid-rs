# Retained failure: stale KSG/ISX/PID2/PID3 bit oracles

## Detector and exact result

The unchanged parallel-bit-identity tests were run on the audit-frozen integration tree. Four
tests failed with candidate values on the left and frozen values on the right:

| Group | Candidate values | Frozen values |
|---|---|---|
| KSG checksum/first/mid/last | `[13714940533915299,4611372573292626839,4608683422432580648,4609053335123176929]` | `[13714940533901959,4611372573292626840,4608683422432580648,4609053335123176934]` |
| ISX redundancy | `4608069949341512143` | `4608069949341512170` |
| PID2 red/unq1/unq2/syn | `[4608069949341512143,4590324628665003600,13821388618758275492,4591732782175321784]` | `[4608069949341512170,4590324628665003312,13821388618758275488,4591732782175321616]` |
| PID3 atom checksum/red checksum/atom 001/atom 111 | `[9260367673031411424,12358916445650220,13803885910316517056,4587721666143603408]` | `[9260367673031410956,12358916445649141,13803885910316517312,4587721666143603440]` |

Exactly 12 of the 13 fields differ. `KSG_LOCAL_TERM_MID` remains
`4608683422432580648`. It must be recorded as reviewed and unchanged, not described as stale or
silently rewritten.

## Commands

```text
cargo test --locked -p pid-core \
  --features experimental-pipelines,parallel \
  --test parallel_bit_identity match_serial_reference \
  -- --test-threads=1 --nocapture

cargo test --locked -p pid-core \
  --features experimental-pipelines,parallel \
  --test parallel_bit_identity \
  isx_redundancy_matches_serial_reference -- --exact --nocapture
```

The first command ran the KSG, PID2, and PID3 reference tests; the second isolated ISX. These runs
used a `parallel`-enabled build and therefore detect stale expected values but do not themselves
constitute an independent serial capture.

## Dependency reach and correction boundary

The failure blocks revision-1 E4. It does not refute the exact harmonic identity. The PID2 atom
row includes both integer-harmonic input changes and `PID2-REPRESENTED-SUM-001` revision-2 exact
synergy arithmetic. Re-freezing it under only the KSG claim would give false provenance.

Capture the settled serial values without `parallel`, then require the parallel build to match.
Do not update unrelated bootstrap constants merely because they share this file; dependency
analysis precedes any such edit.
