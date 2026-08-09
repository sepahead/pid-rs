# Real-R constructor V8 architecture record

This record explains the accepted source/auditor checkpoint without publishing
or executing its path-bearing source bytes. It is historical documentation, not
an implementation specification for new work.

## Three-root authority model

The constructor binds one frozen packet root plus frozen inner- and outer-
capture roots. Packet evidence is path-addressed and source-last. Inner and
outer roots are held by descriptors and compared through canonical path,
device, inode, and mode observations. The design explicitly does not upgrade
the packet root to an unimplemented held-descriptor claim.

The frozen authority-directory deny set contains exactly 22 labelled native
directory identities. Before writes, those identities are compared with four
production writable identities: the repository root, its `audit` directory,
its `audit/evidence` directory, and the capture root. Self-test uses a separate
single writable fixture identity. Label sets, types, and canonical map
commitments are checked; count-only evidence is insufficient.

## Nine-stage construction order

1. Validate lexical boundaries and external scalar anchors.
2. Acquire and twice read packet, inner, and outer authority semantics; derive
   the 22 native directory identities.
3. Acquire held writable roots and reject aliases between all authority and
   writable/write-parent identities.
4. Snapshot fixed and repository inputs.
5. Compare the Q worktree projection.
6. Derive fresh-validator expectations and validate receipt semantics.
7. Plan five capture outputs with the capture manifest last.
8. Reopen and hold all three authority roots, recheck native separation, reread
   generic inputs, 619 repository files, five captures, and the terminal
   complete authority phase.
9. Write the receipt exclusively as the final constructor-managed content
   mutation.

The stage order is evidence-bearing. Earlier revisions were rejected when the
recorded chronology described a different order from the source.

## Packet and post-receipt closure

Each packet phase has two complete 53-event rounds: 50 companion reads, a
pre-source validation, the validator source read, and a post-source validation.
The validator is therefore source-last within the packet subphase. Two phases
produce 106 events each and 212 combined.

After the exclusive receipt write, a fresh namespace is created only from the
final held validator bytes. It validates the written receipt in memory. The
post-receipt closure has no packet/root path reopen, `run_check`, subprocess,
or constructor-managed write route.

## Control surfaces

The settled source registers 98 self-test mutations: 62 R10 authority/schema/
native/ordering routes and 36 local constructor routes. The independent-auditor
design also binds source and AST inventories, 64 token-structural mutants,
source-last ordering, failure cleanup, genuine 619+5 cases, fresh workers, and
normal/optimized behavior across Python 3.11 and 3.14.

These are bounded adversarial checks. Counts do not imply independent theorems,
mutation completeness, formal verification, security, or scientific validity.

## Failure and cleanup boundary

Owned descriptors close exactly once in reverse acquisition order. Downstream
authority cleanup is outer, then inner, then packet. Managed production cleanup
is capture, then repository. Preopened descriptors remain caller-owned. Failure
records retain scoped residue rather than allowing a failed attempt to be
mistaken for a clean retry.

No claim is made against uncatchable termination, unauthenticated concurrent
namespace mutation, absent history, compromised runtimes, or external writers
outside the bounded checks.
