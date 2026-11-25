# Check the W03 host environment and working directory

Sepehr Mahmoudian · 2026

The W03 question asks whether a particular order on finite families of sets places each family below itself. Its exact test is the 89-command source file in the original field. The file also accepts 16 unrestricted integer inputs. A *field* here is the fixed set of source files, permitted tools and checks for one attempt. This field tests whether a Linux host and a separate receiver can run the qualification procedure. The payload contains the original definitions and two artificial controls. It supplies zero proposed proofs of W03. [Original source and statements](../field/FIELD.md) · [Original native failure](../../../evidence/w03-host-origin-2026-11-25/README.md) · [Parthood paper](https://arxiv.org/abs/2008.09535v2)

The first qualification stopped in the guest environment check before it ran Lean. A *guest* is the process that receives a restricted view of the host. An *environment variable* associates a name with a text value in that process. The earlier check expected six names. The Ubuntu source of the launcher sets one further variable to the working directory. The earlier guest reported an environment error without listing the actual values. Its original failed result remains available for comparison. [First native run](https://github.com/sepahead/pid-rs/actions/runs/45527884640) · [Ubuntu launcher source](https://archive.ubuntu.com/ubuntu/pool/main/b/bubblewrap/bubblewrap_0.9.0-1ubuntu0.3.dsc)

## Which values does the guest check?

| Name | Required value | Purpose |
|---|---|---|
| `PATH` | `/stock/bin` | Directory that contains the official Lean programs |
| `LC_ALL` | `C.UTF-8` | Language and character encoding |
| `HOME` | `/tmp` | Guest home directory |
| `TMPDIR` | `/tmp` | Directory for temporary files |
| `LEAN_PATH` | `/objects` | Directory with previously compiled Lean objects |
| `LEAN_NUM_THREADS` | `1` | One Lean execution thread |
| `PWD` | `/src` | Working directory reported by the launcher |

The guest reads its actual process environment. It also asks the operating system for its current working directory. The returned directory must be `/src`. It checks every value and rejects any extra or missing name. For example, the seven required values with an actual working directory of `/tmp` fail. A process with the working directory `/src` and an additional variable also fails. On success the guest records the seven fixed values and the actual directory. The native supervisor and the separate receiver each check that record. [Environment rule](overrides/environment.py) · [Guest program](overrides/containment.py) · [Receiver](overrides/recipient.py)

## Native procedure and limits

The package includes readable changes and an archive of the effective field. It first verifies the preceding 28 files. The new field contains 29 files. Of those, 23 have byte-for-byte equality with the earlier field. The other six are the environment rule, the guest program, the supervisor, the receiving program, the field description and its generated file manifest. All four original theorem statements, their definitions, the original solver script and the official Lean release retain their original bytes. Run these commands from this directory to check the sources and the separate artificial inputs. [Source reader](verify_distribution.py) · [Field description](overrides/FIELD.md)

    python3 -I -S -B verify_distribution.py
    python3 -I -S -B check_environment.py
    python3 -I -S -B check_delivery.py

A native Linux worker verifies the 580,432,872-byte stock Lean 4.34.1 archive. A Linux control group applies the hard limits to the complete protected service. It permits one CPU, at most four gibibytes of memory (4,294,967,296 bytes) and zero swap. A service observer records the effective limits and measured memory before and after the run. A successful observation requires the measured peak to cover current use and stay under the hard memory limit. The guest has its own network namespace. The exact supervisor stops on failed checks or incomplete evidence. A separate job downloads the original provider artifact by numeric ID, verifies its digest and replays the full field recipient in ordinary and optimized Python. [Workflow](../../../../.github/workflows/w03-working-directory-qualification.yml) · [Observer](observe_service.py) · [Artifact reader](read_delivery.py)

This procedure can qualify a later submission under this field only after both real jobs pass. The separate supervisor, receiver and local readers share source definitions and official software. An accepted native check identifies its fixed environment and recorded execution. Scientific source correspondence, a proof of the original four statements and a public PID estimator each need separate evidence. [Research definitions and trust assumptions](../field/FIELD.md)

## Rust implementation and computational cost

This procedure has no Rust estimator or public runtime API. Its inputs are 29 source files and a fixed official Linux toolchain. It has no sample rows, sampling law, physical units, training or resampling. The verifier reads each source byte and compares its SHA-256 digest. The Linux host runs fixed source and artificial control stages sequentially. Each child has a 900-second limit. The field has a 5,400-second limit, and the service has a 5,700-second limit. This source does not supply a successful proof-runtime measurement. The earlier failed run has its own recorded limits and measured peak. [Original resource record](../../../evidence/w03-host-origin-2026-11-25/README.md)

Cite Sepehr Mahmoudian (2026), *Check the W03 host environment and working directory*, with the exact repository commit or release. [Software citation](../../../../CITATION.cff)
