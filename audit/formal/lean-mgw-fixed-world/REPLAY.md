# Replaying the fixed finite proof

This guide describes the later observed research adapter and its inputs. It is
not a claim of a supported one-command runner or of cross-platform qualification.
The underlying finite categorical MGW definitions, proof scope and primary
citations are in the [mathematical paper](../../evidence/mgw-fixed-world-added-information-2026-09-09.md).
The [evidence guide](EVIDENCE.md) separates mathematical checks, native observations,
synthetic controls and the retained failures.

## Required inputs

- All nine exact sources listed in [SOURCE_GRAPH.json](SOURCE_GRAPH.json), in a
  complete pid-rs checkout or source export. The four files in this directory alone
  are insufficient. The five dependencies retain their existing repository paths.
- The seven exact Python files in [adapter-v2](replay-support/adapter-v2/prepare.py).
  Their paths and hashes are listed in [LATER_EXECUTION.json](LATER_EXECUTION.json).
  Only `prepare.py`, `run-one.py` and the two installed observers are entry points
  in the native procedure. The runtime and validator are source-loaded helpers.
- An existing Lean sysroot and external package directory whose files match the
  [compressed installation profile](replay-support/installed-profile-macos-arm64-v1.json.gz).
  Its uncompressed SHA-256 is
  `f9ec05aa708a293e265b4d6891e66744d1b7fc01737331a905a0b6d3d742874c`.
  The profile uses the aliases `sysroot` and `packages`; the paths below those
  roots are relative. It contains 139,934 file pins, not the files themselves.
- Python 3.11 or later with `-I -S -B`. This execution used CPython 3.14.6.
  Native entry under `-O` is deliberately refused. Native commands use the pinned
  macOS ARM64 installation; another platform requires its own declared evidence.
- The host `/bin/ps` process monitor, CPython runtime and operating-system
  facilities used by `runtime.py`. These dependencies are outside the installed
  Lean/package profile; their complete provenance is not established here.
- A new writable stage and a reviewer outside the candidate's write authority to
  inspect the fixed inputs, actual results and predecessor records.

The profile is a forensic comparison object, not a download or installation
recipe. A version string alone cannot establish its file bytes. A changed or
unavailable installed file stops this exact-profile route. Do not alter the
expected digest merely to make the comparison pass. A different installation may
be assessed in a separately declared replay with its own evidence.

## Observed procedure

1. Decompress the profile to a new file, verify the uncompressed digest above, and
   inspect the source graph, adapter and input roots. Decompression does not run
   code or validate an installation.
2. Invoke `adapter-v2/prepare.py` with `--export`, `--sysroot`, `--packages`,
   `--profile`, `--profile-sha256` and `--output`. Use canonical existing input
   directories and a fresh output path. The adapter copies the nine source files
   into `work`, creates empty project object directories, binds current installed
   metadata and search-path membership, and writes a new ten-command plan.
   `ADMISSION.json` initially has `native_execution_admitted: false`.
3. Run the copied `observe-installed.py` with `-I -S -B`. Inspect its actual
   successful terminal result and `preparation/INSTALLED_PRE.json`. The full byte
   and metadata observation must match the new installed manifest. No Lean command
   has run at this point.
4. The external reviewer checks the complete source and command plan, initial
   empty objects, static controls, current clocks, full installed precheck, and
   source/runtime assumptions. The observed admission then bound the precheck
   and actual preparation records, set the literal admission Boolean to true,
   and supplied the resulting admission SHA-256 separately to the caller.
   A candidate-generated or merely well-shaped admission record is insufficient.
5. Call the copied `run-one.py ORDINAL ADMISSION_SHA256` once for each ordinal
   1 through 10. Ordinals 1–9 compile the declared modules in order; ordinal 10
   invokes `leanchecker --fresh PidMgwFixedWorld.Candidate`. Each successor requires
   a reviewer-written `ROOT_ACCEPTED.json` for its predecessor, binding the actual
   result and the reviewed object-state digest. The reviewer also advances
   `OBJECT_STATE.json` to the exact reviewed `OBJECTS_AFTER.json`. These are
   operator review records, not an independent proof assistant or authentication.
6. Require actual zero exit, empty stderr, no operational failure and no remaining
   observed group members. Only ordinal 9 may emit stdout. Its exact 21-target
   report must match the bound report and pass the unchanged strict validator.
   Inspect the actual tool result and all object changes before admitting a
   successor. A timeout, crash, unexpected output or changed input stops the run.
7. Run the copied `observe-installed-post.py` once. Inspect its actual terminal
   result and `preparation/INSTALLED_FINAL_POST.json`, and join all ten records,
   streams, reviews and object states with both installed observations.

The prepared execution window is 90 minutes, with a further 20 minutes for final
custody. The plan permits ten native commands, one at a time, and no retries.
Compiler calls have 60-second bounds; the kernel call has 300 seconds. The monitor
caps each retained stream at 8 MiB and samples an 8 GiB group-RSS limit and a 2 GiB
stage-disk limit. It does not impose a macOS address-space cap. Its process-group
observations do not establish containment of descendants that change groups.
Sequential hashes and metadata are not an atomic snapshot or a loader trace.

All supplied execution and control registrations describe closed past attempts.
Do not resume them, reuse their outputs as fresh evidence, or increase their limits.
The original `STATIC_CONTROL_PLAN_V2.json` is retained for identification of the
executed controls. Another control execution needs its own declared plan and
output identities. The negative preparation sources are retained for inspection;
they are not the positive adapter.

## Remaining public-runner work

The exact adapter was executed on the recorded installation, but the complete
public workflow still needs independent review, a bound reusable operator
controller, reviewed control/custody projections, publication gates and hosted
qualification. The accompanying report does not claim those obligations complete.
Replaying these finite targets also does not prove Rust refinement, statistical
calibration, continuous or hyperbolic transfer, or practical sensor value.
