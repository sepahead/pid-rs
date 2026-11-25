# Host qualification for the original W03 order test

Sepehr Mahmoudian · 2026 · Verification procedure

W03 asks whether a finite family of source sets is ordered below itself by the exact operation in an archived SMT script. SMT means satisfiability modulo theories. The original script has 89 commands. It includes sixteen integer inputs that range over all integers. Testing its 128 possible seven-bit family codes alone does not prove the statement for all valuations. The original bytes, four required Lean statements and their definitions are included with this package. The broad parthood construction comes from Gutknecht, Wibral and Makkeh. This source-order test is a project construction. It has no sampling distribution, information units, or numerical PID estimator. [Original question and definitions](field/FIELD.md) · [Original script](field/inputs/W03.smt2) · [Defining parthood paper](https://arxiv.org/abs/2008.09535v2)

This package delivers the second, unchanged W03 source-compositional field to a native Linux worker. A field here is the fixed source, statement and checker package for one research attempt. A successful qualification compiles the original definitions and observes their declaration types. It must also verify one artificial success and one artificial failure with the official Lean 4.34.1 kernel tool. Already published failures of earlier proof attempts keep their own results. The qualification contains zero proposed proofs of the original W03 statement. A later scientific submission requires separate authorization, a previously verified qualification and one immutable candidate. [Fixed field and authority requirements](field/FIELD.md) · [Prior original W03 attempt](../../evidence/three-original-reachable-attempt-2026-11-21/README.md) · [Stock release](https://github.com/leanprover/lean4/releases/tag/v4.34.1)

The first native Linux run stopped at its environment check. It ran zero Lean commands and submitted no original proof. The separate receiving job was skipped. [Original terminal, resource measurements and source diagnosis](../../evidence/w03-host-origin-2026-11-25/README.md)

## Source identity and inputs

The original immutable archive has 28 regular files. Its SHA-256 is 46fe098e7f1d2e94e29f5b9a88e93d36e156f5b6514ad8b052822933c6e865ef. Its internal file manifest has SHA-256 4773c2363ced0c069cf0bb3cc17baae51ca94f9599be7fbf4656a589a21a8067. Both the archive and each readable file are present. Run the verification command in this directory. The output identifies the archive and the manifest.

    python3 -I -S -B verify_distribution.py
    python3 -I -S -B check_delivery.py

The second command exercises the artifact checks with synthetic input. Its example terminal records a failure. This command tests transport only.

The package fixes the exact Linux release, the compiler and the stock checker. The existing 4.33.0 project baseline applies to other declarations. This W03 job uses the separately identified 4.34.1 binaries. Imported compiled objects enter Lean with their recorded trust level. The stock fresh check replays eligible declarations, accepts the listed axioms as assumptions and skips unsafe and partial declarations. The field inventories the permitted compiler helpers and checks the protected terms and their dependency closures separately. [Version and binary digests](field/stock.json) · [Explicit trust surface](field/FIELD.md) · [Original proof slots](field/lean/W03Scope.lean)

## Native run and readback

The dedicated workflow runs on an x86-64 Ubuntu virtual machine. It downloads and verifies the public release, then starts one protected service. The kernel memory limit is at most 4 GiB. Swap is limited to zero for the service. The worker pins the computation to one eligible CPU. The original field permits 5,400 seconds for its stages, 900 seconds for one child and less than 1 GiB of retained native output. It checks that at least 12 GiB of storage are free before provision. A separate observer reads the live service limits and records memory use before and after the qualification. A missing limit, failed negative control, partial output or absent result leaves qualification open. [Workflow](../../../.github/workflows/w03-source-host-qualification.yml) · [Stock host checks](field/stock.py)

The first job uploads the complete native command history, source files, compiler outputs, live limits and terminal record if they exist. A second job retrieves the provider's actual artifact ID, its advertised SHA-256 and the ZIP bytes. It verifies the original event and reproduces the fixed recipient result in normal and optimized Python. A separate recipient can then download both artifacts and the original job logs. The source field, administrator and shared host dependencies still require explicit accounting. The host result, its copies and its recipients have distinct roles. [Read the received archive](read_delivery.py) · [Original recipient](field/recipient.py)

## Rust implementation and computational cost

This host operation has no Rust API, estimator, samples, training or resampling. Its fixed inputs are the 89-command source, the bound Lean modules and one official toolchain archive of 580,432,872 bytes. The original judge compiles and replays each permitted module sequentially. The number of compiled modules and commands, peak sampled child memory and elapsed time come from the actual run. The separate receiver reads all retained files. Checking the input and returned byte digests takes time proportional to their sizes. There is no timing result for a complete W03 proof here. An SMT solver or direct Boolean table is sufficient for a separate finite computation when source-linked proof of all original valuations is outside the question. [Field budget and limits](field/FIELD.md) · [Comparison of proof routes](field/REVIEW.md)


Cite Sepehr Mahmoudian (2026), *Host qualification for the original W03 order test*, with the exact repository commit or release. [Software citation](../../../CITATION.cff)
