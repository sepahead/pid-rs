# Linux qualification of the original W03 inputs

W03 is the project identifier for a test of the order relation in a
three-source categorical construction. This run tested whether the host can
execute its fixed verification inputs in the required working directory.
It supplied zero candidate proofs.

At commit 3d05081e736e16918a9cd7509913344f743f265d, the first Linux job
completed in the recorded system control group. The kernel reported a peak
memory use of 4,100,747,264 bytes. The service returned a 2,422,669-byte
archive to the provider. Its SHA-256 checksum was
`008fd2402f1d99008ac8c3a91f4d85f865e6158bd3a6a40ba5a1ed7fb34f3994`.
That measurement applies to this run and host.
[First job](https://github.com/sepahead/pid-rs/actions/runs/45610293895/job/139191742448)

The second Linux job downloaded the first archive. It checked the 49 recorded
commands in the qualification result with ordinary and optimized Python. Its
separate archive has SHA-256 checksum
`866ea90710d96dea8dd3571672a8ceeae9ae2d986ac8ab45e73a4ac0942fa0db`.
Both jobs passed. A candidate still needs its own registered statement,
original proof, kernel checks and counterexample controls.
[Receiving job](https://github.com/sepahead/pid-rs/actions/runs/45610293895/job/139200413010)

The earlier host test stopped at its environment check. It ran zero proof
commands and its receiving job was skipped. Each event retains its own inputs
and outcome. [Earlier record](../../../evidence/w03-host-origin-2026-11-25/README.md) ·
[Working-directory contract](README.md)
