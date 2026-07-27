# Retained failure: KSG/PID2 release-phase conflation

## Refuted release plan

The initial completion order attempted to land PID2 represented-sum hardening before the KSG
integer-harmonic implementation. Four release families had already advanced directly to strings
that combined both changes:

- `pid-core.experimental.continuous.pid2`;
- `pid-core.research.isx-heuristics`;
- `pid-core.experimental.hierarchy`; and
- `pid-core.experimental.pipelines.pid2-screening`.

That order is false on parent `626ded7`: the parent contains neither implementation, and a
PID2-only commit cannot truthfully claim integer-harmonic KSG inputs. Conversely, the old KSG
checker treated the KSG-only bridge strings as stale and authorized two unrelated I_min migrations.
It could therefore validate only the combined dirty tree, not a KSG-only release milestone.

## Correct phase boundary

Revision 3 binds one exact KSG-only state. The four bridge revisions are:

```text
pid-core.experimental.continuous.pid2
  separate-biased-term-pid2-integer-harmonic-v2
pid-core.research.isx-heuristics
  heuristic-baselines-with-integer-harmonic-ksg-v2
pid-core.experimental.hierarchy
  hierarchy-screening-with-integer-harmonic-ksg-v2
pid-core.experimental.pipelines.pid2-screening
  deterministic-pair-enumeration-with-integer-harmonic-pid2-v2
```

The two I_min families remain protected at their parent estimator revisions. The KSG checker now
requires 15 affected and 20 protected families. A later PID2 milestone must issue its own claim
and release revision and advance only the four bridge families to the combined strings.

## Evidence boundary

This is release/provenance assurance, not evidence for the harmonic identity, binary64 accuracy,
KSG consistency, shared-exclusions validity, or PID2 arithmetic. A green combined dirty tree did
not validate either isolated commit. Each milestone requires an index-derived or clean-worktree
replay of the exact staged snapshot.
