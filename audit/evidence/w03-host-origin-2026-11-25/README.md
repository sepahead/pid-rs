# First Linux host result for the W03 order check

Sepehr Mahmoudian · 2026

W03 asks whether one project-defined order test returns true when the two finite families of source sets are equal. The original script also takes 16 integer inputs. Its 89 commands, the exact Lean statements and the definitions are in the [original field](../../research/three-source-w03-compositional-host/field/FIELD.md). Here, *qualification* means that the host and a separate receiver complete the prescribed checks before any proof submission.

On 25 November 2026 the first native Linux qualification stopped during its first command. The guest process rejected its environment and exited with status 1. No Lean command ran in this field. The job for the separate receiver was skipped. The field had no proposed proof of W03. The four recorded files below contain original output from this run. [Run 45527884640](https://github.com/sepahead/pid-rs/actions/runs/45527884640) · [First job](https://github.com/sepahead/pid-rs/actions/runs/45527884640/job/138915631384) · [First public source](https://github.com/sepahead/pid-rs/commit/bcfb27458a77c5952a0885e1acc210090c06a09f)

| Original record | What it contains |
|---|---|
| [Terminal](terminal.json) | Failed command, arguments, runtime limits, official tools and their digests |
| [Command error](command.stderr) | The guest reported `RuntimeError: environment` |
| [Service before](host-limit-before.json) and [after](host-limit-after.json) | Live service memory, swap and CPU limits |

The field expected exactly six environment variable names. Its Linux launcher also received the instruction to use `/src` as its working directory. In the distributed Ubuntu source of Bubblewrap 0.9.0-1ubuntu0.3, line 3297 of `bubblewrap.c` sets the variable `PWD` to the new working directory. Neither of the two Ubuntu patches changes that assignment. The distributed executable has the same SHA-256 as the one used in the failed run. This source observation explains why a seventh name is expected. The original guest output did not list any of the names or values that it saw. [Ubuntu source package and checksums](https://archive.ubuntu.com/ubuntu/pool/main/b/bubblewrap/bubblewrap_0.9.0-1ubuntu0.3.dsc) · [Ubuntu binary package](https://archive.ubuntu.com/ubuntu/pool/main/b/bubblewrap/bubblewrap_0.9.0-1ubuntu0.3_amd64.deb)

The service ran with a limit of one CPU, 4,294,967,296 bytes of memory and zero swap. Its recorded peak was 3,878,776,832 bytes. This is a measurement of the host service, including preparation of the stock toolchain. The original run counted zero proof submissions.

| Verified object | SHA-256 |
|---|---|
| First host artifact, ID 14983401905 | `c002ac69b3d531ba0e23cd8810620aae6ab64fd4ca29bf01567c1a9a7cde3124` |
| Native evidence archive inside it | `5344362c7f666dcea29251b46ff58428ccbce9ca586378e4d387235986ee686b` |
| Original terminal | `99c7c667dee75ef73cbb9551d645636eaa3768153908af28d8ee308e20a244cf` |
| Ubuntu executable used by the host | `e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71` |

Cite Sepehr Mahmoudian (2026), *First Linux host result for the W03 order check*, with the exact repository commit or release. [Software citation](../../../CITATION.cff)
