# SxPID3 PDF-check checkout-integrity incident

Date: **4 September 2026**

Disposition: **repository-process incident; cause unresolved; no mathematical result changed**

## Why this record exists

An exact SxPID3 PDF check was started in a disposable integration checkout. During that run, the
checkout lost a large part of its tracked working tree and could no longer resolve many Git
objects. Work stopped immediately. This record separates what was observed from hypotheses about
cause, records the bounded recovery, and turns the failure into a reusable operating control. It is
not evidence against the SxPID3 mathematics and is not evidence that the PDF scripts caused the
damage.

## Observed facts

- The affected checkout still reported candidate HEAD
  `ab0c6970050e1b87216fbd0846911143a92c3904`.
- A later read-only status census reported 644 entries: 612 worktree deletions, 11 worktree-only
  modifications, eight index-only modifications, five paths modified in both index and worktree,
  one index addition, and seven untracked entries. Those mutually exclusive porcelain-v1 classes
  sum to 644. They are observations of the damaged state, not a claim that every entry changed in
  one operation.
- `git fsck --connectivity-only` reported invalid remote-ref pointers, invalid reflog entries, and
  missing cache-tree objects. The checkout was therefore excluded from all later acceptance
  evidence.
- The event was temporally associated with the exact PDF-check invocation. Temporal association is
  not a causal proof.

## Recovery and custody

Before any further experiment, 26 live work-in-progress files were copied to a separate recovery
packet. Its 26-line SHA-256 manifest has digest
`36e8be10ff282fe206f2fc622a6ecfd42f7ab8e0c79ca30f1e2e9590d9a2d666`; every entry was verified
inside that packet. This packet was a local continuity aid, not publication or mathematical
evidence.

A new checkout was then created without hardlinks from an intact local `main`, the exact candidate
branch was fetched from GitHub, and the checkout was moved to
`ab0c6970050e1b87216fbd0846911143a92c3904`. The saved 26-file overlay was applied and verified
against the recovery manifest before editing resumed. A connectivity check succeeded for the
reachable recovered checkout. Baseline tracked files came from the exact fetched branch rather
than from the damaged object store. The current accepted files will receive new Git identities and
fresh gates; the rescue-manifest digest must not be substituted for those final identities.

This establishes recovery of the enumerated overlay and branch baseline. It does not prove that an
unknown, unenumerated private byte never existed in the damaged checkout.

## Static causal audit

The three in-scope shell scripts were read line by line:

- `scripts/build-sxpid3-source-marginal-audit-pdf.sh`;
- `scripts/check-sxpid3-source-marginal-audit-pdf.sh`; and
- `scripts/check-sxpid3-source-marginal-audit-builder-self-test.sh`.

Under ordinary trusted-Bash, trusted-`PATH`, and standard-`mktemp` semantics, their recursive
cleanup targets are freshly created, name-scoped temporary directories. They contain no Git
command and construct no `.git` path. The builder's only publication move replaces the explicitly
selected PDF file. Static inspection therefore found no normal script path that explains deletion
of a repository tree or object database.

The audit did identify residual environmental and race risks:

1. an initial Bash can execute a caller-selected `BASH_ENV` before line one;
2. a nested Bash can import exported functions even when `BASH_ENV=/dev/null` and
   `--noprofile --norc` are present;
3. external tools are selected through `PATH`, not authenticated by content;
4. a hostile or faulty `mktemp` result needs post-creation parent and object validation;
5. a regular, nonsymbolic publication temporary can still be a hard link;
6. the old self-test cleanup guard checked a basename pattern without binding its exact parent;
7. a concurrent filesystem actor can replace a validated path between checks; and
8. the standalone builder intentionally replaces any caller-selected, validated regular PDF.

These risks justify hardening but do not identify the incident's cause. The cause remains
**unadjudicated**.

## Defense-in-depth response

The candidate scripts now:

- clear `BASH_ENV` and `ENV` on entry and launch each nested Bash through an external
  `/usr/bin/env -i` boundary with an explicit admitted environment;
- canonicalize each fresh temporary directory, bind its exact parent and generated basename, and
  bind its device/inode identity before permitting cleanup;
- bind the publication temporary to the already validated output directory, expected basename,
  current owner, single-link state, zero initial size, and device/inode identity;
- separate `EXIT` cleanup from `INT` and `TERM` exit status; and
- exercise hostile nested-`BASH_ENV`, exported-function, escaped-directory-`mktemp`, and
  publication-hard-link-`mktemp` cases in the focused builder self-test.

The final focused self-test passed in a fresh disposable no-hardlink canary with nine accepted
controls, 38 hostile cases, eight required-source alias checks, and five static guards. The same
run built the 23-page PDF only into canary scratch, with SHA-256
`788b993f39133f1bf0b1d5e81f61421d9f6a35ea774db53ff50fa3eed21a8cd2`.
Pre/post manifests were byte-identical for 1,161 non-Git files, three object-store files, the
34-line candidate status, and reachable-object connectivity. Their manifest SHA-256 values were,
respectively, `895f7fe76d0005b0ad407ab8093bf6d319e31a677281570d611614effa9ba361`,
`a1de3bea31d3083e82bbbfb47e2f45fa3ced10b29da5f6336b723ca5bf46acba`,
`ed1a01a4a45f3762f6f4c70eec2d4e6cab92f5be73fcbc4e4f702b675d88ee32`, and the
empty-output digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
These locally retained manifests support that one execution but are not independent custody or a
universal filesystem-safety proof.

## Insufficient routes retained as negative results

| Attempted route | Why it was attractive | Counterexample or limit | Current disposition |
|---|---|---|---|
| Set `BASH_ENV=/dev/null` and `ENV=/dev/null` on the nested Bash command | Prevent startup files from running | On the repository host's Bash 3.2, an exported function remained importable and executable under those settings | Insufficient alone; nested launches now cross `/usr/bin/env -i` |
| Test only `-f` and `! -L` for the publication temporary | Reject directories and symbolic links cheaply | A hard link is still a regular nonsymbolic file; copying through it can overwrite its other name | Rejected; require owner, link count one, zero initial size, and stable device/inode identity |
| Bind only temporary parent and basename before recursive cleanup | Prevent broad or escaped cleanup targets | A same-name replacement inside the admitted parent can denote a different object | Strengthened with device/inode identity; a check/use race remains |
| State that signal traps preserve the intended status | Explain `INT`/`TERM` behavior simply | Cleanup refusal can replace the status, and an interrupted child can be mapped by a surrounding failure block | Claim narrowed; no integrated signal theorem or hostile signal fixture is asserted |
| Treat a clean disposable canary as proof of general safety | It exercises the real scripts away from the working checkout | One execution cannot authenticate tools, exclude a concurrent actor, or prove causation for the earlier loss | Retained only as bounded execution evidence |

Clearing variables inside a script cannot undo startup code that an untrusted caller caused the
first Bash process to execute before line one. The clean boundary removes variables and exported
functions from nested launches; it does not authenticate the explicitly reintroduced `PATH`,
prevent a hostile initial interpreter, or eliminate concurrent path-replacement races. A clean
external launcher or container boundary is still required for hostile-host claims.

## Acceptance protocol after the incident

High-impact artifact gates use this order:

1. preserve and hash live work before experimentation;
2. create a disposable no-hardlink checkout from an independently intact repository;
3. use an explicit canonical scratch root and start the first Bash through an external clean
   environment boundary, not only an in-script `unset`;
4. record source-tree and reachable-object checks before the run;
5. build only to scratch on the first pass;
6. record source-tree and reachable-object checks after the run;
7. copy back only a byte-verified derived artifact;
8. rerun its semantic and PDF gates on the exact candidate bytes; and
9. commit and push only after the candidate and remote identities agree.

When stronger isolation is available, mount the repository read-only, keep scratch on a separate
writable filesystem, use an admitted tool-only `PATH`, and trace `unlink`, `rename`, and `rmdir`
system calls. A failed or unavailable tracing tool does not authorize treating an untraced run as
equivalent evidence.

## Nonimplications

This incident and its response do not:

- change an equation, theorem, finite reconstruction, census, or Program A--E status;
- show a defect in Makkeh--Gutknecht--Wibral shared exclusions;
- show that the PDF builder or checker caused the checkout damage;
- prove that the hardened scripts are secure against a hostile host, kernel, filesystem, or
  authenticated-tool substitution;
- turn visual PDF inspection into mathematical verification; or
- authorize deletion of the damaged checkout or recovery packet before final Git and remote
  custody is independently confirmed.

The negative result is operationally useful: a disposable checkout can itself fail, so isolation
must be paired with pre-run preservation, post-run integrity evidence, and an explicit recovery
path.
