# Real-R constructor V8 public disposition

Snapshot: 2026-08-10

## Classification

This directory is a **historical, inert, non-authoritative public disposition**
for constructor source `cb5a33ca...` and auditor source `db79299d...`.
It records what was built, which bounded reviews passed, where the work sits in
the lineage, and why the raw source payloads are not on this public branch.

Agents and release tooling must not treat this directory as active
implementation, a test input, a package input, or scientific evidence.

## Source identities

| Role | Bytes | SHA-256 | Git blob SHA-1 | Public payload |
|---|---:|---|---|---|
| Constructor | 348,609 | `cb5a33ca69ef8a377292170b78308e094c1c2b07ed8d32eb0f8991faa9e97803` | `f994472bc8e5dd959007a6af2546a519c4066b5a` | Withheld |
| Independent-auditor design | 375,722 | `db79299daf10c0b470d109ae95c436775b06aecdd3aa3a9fdc8c4997e9b8d083` | `ba53ee281d125c3053cd7d124b26caf43a3234a2` | Withheld |

The private source checkpoints were regular single-link files observed at mode
`0600`. Their byte identities are preserved redundantly outside public Git.
Git metadata is not an exact representation of owner, group, inode, timestamps,
xattrs, or the original owner-only mode.

## Why the payload is withheld

Bounded scanning found no credential or private-key signature in either file.
However, the exact constructor contains six personal home-path occurrences and
eleven private-temporary-path occurrences. The auditor contains none. Redacting
those strings would create different bytes and must never be represented as the
accepted `cb5a33ca...` identity.

The repository owner has not yet recorded explicit informed approval for public
disclosure of those exact path-bearing bytes or a separate source-rights
confirmation for the payload. This branch therefore publishes commitments and
architecture only. It repeats no raw personal path.

## Reviewed scope

Two separately executed reviews gave the exact source/auditor pair scoped
migration GO. The bounded evidence included:

- CPython 3.11 and 3.14, normal and optimized source/auditor lanes;
- exactly `98 = 62 R10 + 36 local` registered controls;
- a 51-file, 65-metadata-record, 66-rooted-record synthetic packet fixture;
- 106 packet events per authority phase and 212 combined events;
- exact 22 authority-directory, 4 production-writable, and 1 self-test-writable
  native-identity label sets;
- nine recorded construction stages;
- the 619-repository-plus-5-capture final gate;
- source-last packet reads, held-byte post-receipt validation, zero post-receipt
  packet/R10 reopens, and reverse descriptor cleanup; and
- causal fail-closed invocation and mutation controls.

The word “independent” in the auditor filename means a distinct structural
auditor design. It does not mean third-party, organizationally independent, or
failure-independent validation.

## Nonclaims

This public disposition and the private source checkpoint do not establish:

- active pid-rs code, package qualification, freeze, construction, release, or
  publication authority;
- a fresh fixed-R10 replay during this public-disposition build;
- pre-archive provenance, source/authorship authentication, continuous or
  atomic custody, filesystem metadata exactness, or privacy/security
  attestation;
- source-logic correctness, formal verification, cross-platform reproduction,
  or method-catalog authority;
- any PID/Wibral theorem, estimator, statistical, or application result; or
- scientific novelty or a project-domain classification.

## Lineage

- `0fa045c3...`: terminal NO-GO; incomplete writable/native-alias separation.
- `ca3d9bb8...`: terminal NO-GO; reported chronology contradicted execution.
- `c5639e28...`: source GO, superseded by exactness hardening.
- `cb5a33ca...` + `db79299d...`: scoped source/auditor migration GO; this
  disposition.

Complete historical and terminal-negative bytes are kept under explicit
non-authoritative classifications in two private durable stores. No older
variant is copied into an active source path here.

## Verification

Run the public-disposition checker and its mutation suite in normal and
optimized Python. They validate only this directory's strict metadata and
claim boundary; they never import, execute, or reconstruct the withheld source:

```text
python3 scripts/check-real-r-constructor-public-disposition.py
python3 -O scripts/check-real-r-constructor-public-disposition.py
python3 scripts/check-real-r-constructor-public-disposition-self-test.py
python3 -O scripts/check-real-r-constructor-public-disposition-self-test.py
```
