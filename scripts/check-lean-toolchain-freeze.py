#!/usr/bin/env python3
"""Fail-closed custody check for the frozen Lean 4.33.0 replay lane."""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
):
    print(
        "ERROR: check-lean-toolchain-freeze.py requires Python 3.11+ -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
PROJECT = ROOT / "audit/formal/lean"
POLICY = PROJECT / "toolchain-freeze-policy.json"
RECEIPT_RELATIVE = "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r10.json"
RECEIPT = ROOT / RECEIPT_RELATIVE
MAX_FILE_BYTES = 8 * 1024 * 1024
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EXPECTED_CLEAN_BUILD_STDOUT = ""
EXPECTED_CLEAN_BUILD_STDOUT_STREAM = {
    "bytes": len(EXPECTED_CLEAN_BUILD_STDOUT.encode("utf-8")),
    "sha256": hashlib.sha256(EXPECTED_CLEAN_BUILD_STDOUT.encode("utf-8")).hexdigest(),
}
# This literal is deliberately one line so the append-only receipt can reconstruct
# the exact pre-pin checker bytes without a checksum cycle.
# fmt: off
EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "f7875094b8b19c98bd97508633885abcc20e385512df60b87c73f639ffc8c559"
EXPECTED_COMPOSITE_V5_CHECKER_OPERATIONAL_SHA256 = "b510e3e1a9831a41f6904fd9fd259c227c426b11436ead11789a04ad474a8c30"
# fmt: on
EXPECTED_LOCAL_REPLAY_ROUTES = {
    "archive": (
        "/private/tmp/pid-rs-lean4330-extract.wGhf6H/lean-4.33.0-darwin_aarch64.tar.zst"
    ),
    "lean_bin": (
        "/private/tmp/pid-rs-lean4330-extract.wGhf6H/lean-4.33.0-darwin_aarch64/bin"
    ),
    "python": (
        "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/"
        "Versions/3.14/bin/python3.14"
    ),
    "git": "/usr/bin/git",
    "repo_root": "/private/tmp/pid-rs-sxpid2-atom-bridge.LHX9JM/repo",
}
EXPECTED_LOCAL_EXECUTABLE_SHA256 = {
    "git": "179301dcb41ea78accc3fa0048a7e6f6710d891945a751a34addd622020c1818",
    "lake": "58261a1a2fa1a362376c71e02ca854a093e71cc5e6ea64b287a931cb2565273d",
    "lean": "1b370cfcbf44e80d1b004ab1b1ab9a4c73951f9f7c242140bcff9bc577576554",
    "leanchecker": "257f505f8241ab595c6b557d661fd832dbdace6839ab35d9d1600b3dcbce5880",
    "python": "b502cb4c5b46b8d4192ec6bcb600ce8922f1afc396fcf646e8765c6eba74a0bf",
}
EXPECTED_LOCAL_EXECUTABLE_SIZE_BYTES = {
    "git": 118_928,
    "lake": 51_840,
    "lean": 49_968,
    "leanchecker": 78_128,
    "python": 52_448,
}
EXPECTED_LOCAL_EXECUTABLE_LINK_COUNTS = {
    "git": 78,
    "lake": 1,
    "lean": 1,
    "leanchecker": 1,
    "python": 1,
}
EXPECTED_ARCHIVE = {
    "file_name": "lean-4.33.0-darwin_aarch64.tar.zst",
    "sha256": "db5274b669be270af048b5e4f1e0ce571df6750e411956b3e1e6fcc2012410c2",
    "size_bytes": 556168134,
}
EXPECTED_LEAN_IDENTITY = {
    "build": "Release",
    "commit": "d8b18978322de05a8f3dba51ef03cf5461676c17",
    "platform": "arm64-apple-darwin24.6.0",
    "version": "4.33.0",
}
EXPECTED_LAKE_IDENTITY = {
    "lean_version": "4.33.0",
    "version": "5.0.0-src+d8b1897",
}
EXPECTED_CONFIG_HASHES = {
    "audit/formal/lean/lake-manifest.json": (
        "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af"
    ),
    "audit/formal/lean/lakefile.toml": (
        "ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0"
    ),
    "audit/formal/lean/lean-toolchain": (
        "302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b"
    ),
}
EXPECTED_PACKAGE_PINS = {
    "Cli": (
        "https://github.com/leanprover/lean4-cli",
        "6130a47896ce867c6a4a55373441e59e565bad0f",
        "v4.33.0",
        True,
    ),
    "LeanSearchClient": (
        "https://github.com/leanprover-community/LeanSearchClient",
        "5f4d51b81cbd3f6b32b156bfad9056621a040404",
        "main",
        True,
    ),
    "Qq": (
        "https://github.com/leanprover-community/quote4",
        "92c15be17b7caf78c2ad767ec40f89052d908d81",
        "master",
        True,
    ),
    "aesop": (
        "https://github.com/leanprover-community/aesop",
        "3448c0bcc5ce01b2d1546e483ec3620e32df3d0e",
        "master",
        True,
    ),
    "batteries": (
        "https://github.com/leanprover-community/batteries",
        "4488d40d070b9700d4d5a6aa342f0d40c31b2a2d",
        "main",
        True,
    ),
    "importGraph": (
        "https://github.com/leanprover-community/import-graph",
        "16f02aa7642864af59f1ff0e384a015994db9118",
        "main",
        True,
    ),
    "mathlib": (
        "https://github.com/leanprover-community/mathlib4.git",
        "db584cd6d46c92f209a44c0f1c829460d327499d",
        "v4.33.0",
        False,
    ),
    "plausible": (
        "https://github.com/leanprover-community/plausible",
        "b7eb3304aeae834b12dda98993a37f6a41f6f0bb",
        "main",
        True,
    ),
    "proofwidgets": (
        "https://github.com/leanprover-community/ProofWidgets4",
        "4be2e3d5087eeb272cf5a8853b8f9dd025ef5957",
        "main",
        True,
    ),
}
EXPECTED_SOURCE_HASHES = {
    "audit/formal/lean/PidFiniteConvergence.lean": "3b99c57000d6bf14077e8caf4de2f86d27f9654a8d984c9fc59d720947de84f8",
    "audit/formal/lean/PidFiniteConvergence/Dependence.lean": "39419a78bd294abdf7d545083ae6207c7e1db9ffbe88c3c03d2545c8397f709e",
    "audit/formal/lean/PidFiniteConvergence/Deterministic.lean": "e9dbd7c5b4578aabf92b76c0b8b684db4c1c1038dcdb033239b0076685c41610",
    "audit/formal/lean/PidFiniteConvergence/FractionalCover.lean": "4ea504a565a69f5222c205e01050b750e780ed17cb02558fe08e0c32e2f5718c",
    "audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean": "ac390d977bce813c7e882f719f33fdaed106fd2b776304f7c119f01bb0483756",
    "audit/formal/lean/PidFiniteConvergence/SupportChangeContinuity.lean": "f5b8b110f69e9d879edbc46948fa67153932540c2cf0ad791771fd6fe30c8370",
    "audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean": "cfedf974c73e11e56041013a47797462100f4b896235d6c4185c9ca0a232d77e",
    "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean": "fa3a1c5450648da4c4768dbd88e261abf1bcd3051f5af4526a63631c83f8648a",
    "audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean": "bc282ca506f50ac5af661b87b166cc76561a4da308ffe39892ad8df7f2fd875e",
    "audit/formal/lean/PidFiniteConvergenceSemanticContract.lean": "79705d3313c4cc479b978449d404d4a49b60890d42050e8860c8b6dfebafd703",
    "audit/formal/lean/PidFiniteConvergenceSxPid2AtomSemanticContract.lean": "536844605093f3aa3be480919de8c1fccff29f25930b3459a2cbfc995e739c47",
}
EXPECTED_CURRENT_EVIDENCE_HASHES = {
    "audit/evidence/foundational-sxpid-descriptor-factorization-lean-4.33.0.json": "9b084e930cd24e3aa6066be6a080e7f7f00963e4a77f7110f064ed23e032003b",
    "audit/evidence/foundational-sxpid-descriptor-factorization-mutations-4.33.0.json": "856b51ce90f23ef61e334f4504065d86f379493a0d246eba406311c3e377fdfe",
    "audit/evidence/lean-citation-edge-countermodel-4.33.0.json": "86ea83c01a6aa745734db873773ae8930b49ef323ef08f0120b562c4d00c4da7",
    "audit/evidence/lean-ksg-integer-harmonic-4.33.0.json": "d25f18530305e404d1d24a6eab2bda5f57b226d3db97c50ba4265c0c85ee9c35",
    "audit/evidence/lean-4.33.0-manifest-regeneration-2026-08-11.json": "9710525fd40ebe72c6ff6d5759014ce4aae05e18c2f9a5544833e17f0fa3f5a6",
    "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json": "9742bd6c5e45049a7576781fb00b112b93e9dda20359ae73a4fcc93e2b659a6d",
}
EXPECTED_CHECKER_HASHES = {
    "scripts/check-lean-citation-edge-countermodel.py": "63d80960a09014fb18daabe1649e2db2dbce92408313944837ee91e9e106feb8",
    "scripts/check-lean-citation-edge-countermodel-self-test.py": "7f2dbb5fdc8c1c50f9cf31d0bd03465465c3c235039db42c95c6192b3b0bbca3",
    "scripts/check-lean-descriptor-factorization-self-test.py": "678c1c722bc8d64d28e883c9615a8773a97bf046cc7e12f2ebd76456ce0e9c2a",
    "scripts/check-lean-descriptor-factorization.py": "7d1c4e4942d4430c6732c9b25492afa847c06aac371ce3dbbd648ba9cfde2bd0",
    "scripts/check-lean-exact-log-product.py": "52510a18ac5fa8b94113bfeba84f61cb28bdbe56be278fc76fb4d55407cb2dcd",
    "scripts/check-lean-finite-convergence-self-test.py": "0a199a1cb373c37531667d821bcad977a2d6fbe7978b939e68a2fd56f8089989",
    "scripts/check-lean-finite-convergence.py": "3ea61295232a03b08522a10257f82865038e760fe47eda34b7f470d2f8f268a0",
    "scripts/check-lean-ksg-integer-harmonic-self-test.py": "0bb0c999ad8bc20137deda54620d2983a5bd0ecaf4a74f81cbde23f997560517",
    "scripts/check-lean-ksg-integer-harmonic.py": "020034884471ace9bcae1c8aa0b303a223758964278b6a0b1ac9ff5eeea94684",
    "scripts/check-ksg-harmonic-revision-self-test.py": "2abbfe7a54e0c2e3263f3dbe1b8776b197ae13cd8fedacc6d1cc1997f94ee6f0",
    "scripts/check-ksg-harmonic-revision.py": "cf4692597bc49448d520580d96e1e6d23b4fc65834539095152bb561ec6450e9",
}
EXPECTED_DERIVED_EVIDENCE_HASHES = {
    "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-2026-08-11.json": "4b84e78ecc13444bf2d222438ccb5e66b5e33287d1affebf39103be62de277e4",
    "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.32.0.stdout": "fa9e2582d609716cf27f67717616cfddba08451c886ff7534ba9ae2223071421",
    "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.33.0.stdout": "37863241a6c106465dacea3cae3f90817eaadb82291754d38b04f16b0f6f3314",
    "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-query.lean": "468a05edeb997400264cb31c269435c130193ccf07006886f19101ae48a03ada",
}
PRESERVED_HISTORICAL_HASHES = {
    "audit/evidence/completion-active-resume-lean-4.32.2-route-correction-2026-08-08.historical.md": "4d636774f58d48212ac5ae83ea68fff106c07bb407b2dbf449503d792490e2e0",
    "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json": "63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6",
    "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json": "b644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9",
    "audit/evidence/lean-4.32.2-darwin-aarch64-observation-2026-08-07.raw.json": "374bc2eb53881cae4c7b989944dff3daff0fc02c2340ce39bd920a4ddb08723a",
    "audit/evidence/lean-4.32.2-darwin-aarch64-observation-2026-08-07.receipt.json": "4720cb4b6d0be274d52f36e2a16d63dcf6542ed47520b9370b956cc1d7d2a903",
    "audit/evidence/lean-4.32.2-darwin-aarch64-reviewed-pins-promotion-2026-08-07.receipt.json": "bfa40273b4f857ebc0a09a2cd87b0f37b5b4a3260e5d518e1c922cfc5196b821",
    "audit/evidence/lean-4.32.2-darwin-aarch64-route-correction-p2-2026-08-08.receipt.json": "0478b2b20af4a83da5c133a9a3d704d0bd0b5f08838a066693d0da361f9d73a8",
    "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-2026-08-08.raw.json": "167632a1087504a34b82db5afa6da8d3024e5752b29fe8ef328db40b4b8c2d5d",
    "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.failure.json": "9dfa00952af0ac6d28be6e0401d5406b05858e729a65ade6c59805351ce511df",
    "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stderr": "08f1429a37d040d20ea1c1a470cc6d779d8a06a1f45627867b5fe59827c8d93c",
    "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stdout": EMPTY_SHA256,
    "audit/evidence/lean-citation-edge-countermodel.json": "86c61895abc54e61a95b48082f7fd6ad7f47de230dbbc83b520f7f32f053267b",
    "audit/evidence/sxpid2-exact-product-lean-check.json": "3b4f5eb4efb1fa354f9b9c772508b0c7d7b900f61f3d2075fe58a1c5811a63e8",
    "audit/formal/lean/toolchain-release-v4.32.2.json": "c9cfcd4c38c0d73a1e765c1abaaf8b36e73bb230fbb6b700047abf0fb58e590f",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md": "1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": "322c3f633d0e1316a401e92b10afb541ee82cb9ba94afef88f4a2937c934b6ff",
    "claims/SX-COUNT-ATOM-BRIDGE-001/phase-a-verification-2026-08-10.md": "d884b0be6d63baed08abf29220d657a99eb2599893bb2f28d1ee79e19f6f0a1e",
    "claims/SX-COUNT-EVENT-BRIDGE-001/phase-a-verification-2026-07-25.md": "19def113939240dbebb0305fbca6e21bf50c75cb84fa0ea522bd9cc4cbf80860",
    "claims/SX-SUPPORT-FREE-CONTINUITY-001/route-memos/formal.md": "a6ae70a99f8c106865a3b38115353d5104c54e708439cfe535f45bdfb807f981",
}
PRESERVED_PRIOR_REPLAY_HASHES = {
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json": (
        "46a6d20351cd81d49fbcf56e0e35820fc5f57c0ddaa7a62bf81ce181ffc89d74"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json": (
        "235088aa9c87701955a190134f4a94d01cd531449ac577221e9f09a23b43772a"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r2.json": (
        "94f444735aaf112ab60c5af879710ae2e22de4e34d3ef9fe4a19afda337472c5"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r3.json": (
        "1258f5daa742a59758c3ccd6aa6be421e6b56e343bde6f4e8c252acb5cc04253"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r4.json": (
        "ddbf0a107c7e74fe5f3309ab33d295f6ad7a495353ac05bb14bbecfec6fb3382"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json": (
        "872175ca504efb24752633704fe13e57802e43ae25bb3c463c4fb8c9dfd073f7"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json": (
        "f14e7a33c01909055cc868fc955e6b2520ae15ebf0d598730911ec57a7f4c5ea"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r7.json": (
        "3dd2df7d7064bac93cf4806cdeac28d9ecc747444689162a4636029228822abb"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-14-r8.json": (
        "86251c48c0f720d1ca021dcac87dfbf6e1a54adf409ea8a8981102cea1769611"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9.json": (
        "e9136696563e007f98498080bb7a769c60353df83537ee90976ee9cc66c0873f"
    ),
}
PRESERVED_PRIOR_REPLAY_SCHEMAS = {
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json": (
        "pid-rs/lean-current-project-replay/v1"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r2.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r3.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r4.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r7.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-14-r8.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9.json": (
        "pid-rs/lean-current-project-replay/v2"
    ),
}
EXPECTED_POLICY_SHA256 = (
    "db0c403f61af1c49996ed217fd025007bd76743de8c57ff147fa12ed319eb204"
)
EXPECTED_ACTIVE_RESUME_SHA256 = (
    "16d8b97fd2aa2d31f9315252ca152d08498ca7fa9b262a7462fb9826f1abf667"
)
OPTION = "set_option backward.isDefEq.respectTransparency.types false in"
EXPECTED_OPTION_LINES = {
    "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean": (OPTION,),
    "audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean": (
        OPTION,
        OPTION,
    ),
    "audit/formal/lean/PidFiniteConvergenceSemanticContract.lean": (
        OPTION + " by",
        OPTION + " by",
        OPTION + " by",
    ),
    "audit/formal/lean/PidFiniteConvergenceSxPid2AtomSemanticContract.lean": (
        OPTION + " by",
    ),
}
EXPECTED_OPTION_TARGETS = {
    "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean": (
        OPTION + "\nderiving instance Fintype for SxPid2Node",
    ),
    "audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean": (
        OPTION + "\nderiving instance Fintype for SxPid2Component",
        OPTION + "\nderiving instance Fintype for SxPid2Atom",
    ),
    "audit/formal/lean/PidFiniteConvergenceSemanticContract.lean": (
        "(sxPid2SourceEvent .redundancy sxPid2AsymmetricAnchor) = 23 :=\n  "
        + OPTION
        + " by",
        "(sxPid2TargetRestrictedEvent .redundancy sxPid2AsymmetricAnchor) = 9 :=\n  "
        + OPTION
        + " by",
        "108 / 115 :=\n  " + OPTION + " by",
    ),
    "audit/formal/lean/PidFiniteConvergenceSxPid2AtomSemanticContract.lean": (
        "(sxPid2TargetRestrictedEvent .redundancy weightedAnchorOneZero) = 1 :=\n  "
        + OPTION
        + " by",
    ),
}
EXPECTED_TRIGGERS = (
    "security_or_kernel_issue",
    "required_capability_or_incompatibility",
    "baseline_unavailability",
    "explicit_human_migration_decision",
)
EXPECTED_NONTRIGGERS = (
    "new_stable_release_alone",
    "release_candidate_or_nightly_availability",
    "social_media_or_announcement_activity",
    "elapsed_update_cadence",
    "optional_unrequired_capability",
    "unmeasured_performance_speculation",
    "automated_dependency_bot_proposal",
)
EXPECTED_DIRECT_SOURCES = (
    "PidFiniteConvergence.lean",
    "PidFiniteConvergence/Dependence.lean",
    "PidFiniteConvergence/Deterministic.lean",
    "PidFiniteConvergence/FractionalCover.lean",
    "PidFiniteConvergence/LocalContinuity.lean",
    "PidFiniteConvergence/SupportChangeContinuity.lean",
    "PidFiniteConvergence/SxEventBridge.lean",
    "PidFiniteConvergence/TwoSourceCountEventBridge.lean",
    "PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean",
    "PidFiniteConvergenceSemanticContract.lean",
    "PidFiniteConvergenceSxPid2AtomSemanticContract.lean",
)
PYTHON_COMMAND_PAIRS = {
    "citation_checker": ("scripts/check-lean-citation-edge-countermodel.py", ()),
    "citation_self_test": (
        "scripts/check-lean-citation-edge-countermodel-self-test.py",
        (),
    ),
    "descriptor_checker": (
        "scripts/check-lean-descriptor-factorization.py",
        (),
    ),
    "descriptor_self_test": (
        "scripts/check-lean-descriptor-factorization-self-test.py",
        (),
    ),
    "exact_product_checker": ("scripts/check-lean-exact-log-product.py", ()),
    "finite_checker": ("scripts/check-lean-finite-convergence.py", ()),
    "finite_self_test": ("scripts/check-lean-finite-convergence-self-test.py", ()),
    "ksg_checker": ("scripts/check-lean-ksg-integer-harmonic.py", ()),
    "ksg_revision_checker": ("scripts/check-ksg-harmonic-revision.py", ()),
    "ksg_revision_self_test": (
        "scripts/check-ksg-harmonic-revision-self-test.py",
        (),
    ),
    "ksg_self_test": ("scripts/check-lean-ksg-integer-harmonic-self-test.py", ()),
}
PYTHON_COMMAND_ARGUMENTS = {
    "ksg_revision_checker": ("--claim-only",),
    "ksg_revision_self_test": ("--claim-only",),
}
EXPECTED_PROVIDER_OBSERVATIONS = {
    "classification": (
        "unauthenticated provider observations and equality to advertised bytes; "
        "not publisher authentication"
    ),
    "lean_release": {
        "asset_created_utc": "2026-08-10T06:08:40Z",
        "asset_digest_advertised": "sha256:" + EXPECTED_ARCHIVE["sha256"],
        "asset_size_bytes": EXPECTED_ARCHIVE["size_bytes"],
        "asset_state": "uploaded",
        "asset_updated_utc": "2026-08-10T06:09:26Z",
        "draft": False,
        "prerelease": False,
        "published_utc": "2026-08-10T06:09:46Z",
        "tag_kind": "lightweight_commit",
        "tag_target_commit": EXPECTED_LEAN_IDENTITY["commit"],
        "tag": "v4.33.0",
    },
    "mathlib_release": {
        "commit_time_utc": "2026-08-10T09:12:31Z",
        "subject": "chore: bump toolchain to v4.33.0 (#42604)",
        "tag": "v4.33.0",
        "tag_kind": "lightweight_commit",
        "tag_target_commit": EXPECTED_PACKAGE_PINS["mathlib"][1],
        "tree": "797420f01ffbca473c4cd972670394965e55208a",
    },
}
EXPECTED_CUSTODY_GATE_PATHS = (
    "scripts/check-lean-toolchain-freeze-self-test.py",
    "scripts/check-lean-toolchain-freeze.py",
)
EXPECTED_CURRENT_REPLAY_POINTER_PATHS = (
    "AGENTS.md",
    "CHANGELOG.md",
    "audit/evidence/completion-active-resume.md",
    "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md",
    "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md",
    "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md",
    "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md",
    "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md",
    "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md",
    "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md",
    "scripts/README.md",
)
EXPECTED_R10_SEQUENCE_EXPLANATION_PATHS = EXPECTED_CURRENT_REPLAY_POINTER_PATHS
EXPECTED_ACTIVE_RESUME_HASHES = {
    "audit/evidence/completion-active-resume-lean-4.32.2-route-correction-2026-08-08.historical.md": (
        "4d636774f58d48212ac5ae83ea68fff106c07bb407b2dbf449503d792490e2e0"
    ),
    "audit/evidence/completion-active-resume.md": (
        "16d8b97fd2aa2d31f9315252ca152d08498ca7fa9b262a7462fb9826f1abf667"
    ),
}
EXPECTED_PENDING_ACTIVE_RESUME_PATHS = tuple(
    relative
    for relative, digest in EXPECTED_ACTIVE_RESUME_HASHES.items()
    if digest == "0" * 64
)
PENDING_OPERATIONAL_SHA256 = "0" * 64
EXPECTED_OPERATIONAL_WIRING_HASHES = {
    ".github/workflows/ci.yml": "61283264499a7b6069a4e5e9563c72541ab101b69379f3ace75a12cd4bf4b175",
    ".github/workflows/ksg-m1a-composite-v4.yml": "3952fdfb596ce15e176795d8a6ec76aaad9d8d66e830129784d3b919ddc5cda5",
    ".github/workflows/ksg-m1a-composite-v5.yml": "7f41177c175d785c92512beb23cfd860c5cf94f12dd2a4aa0d4f414963c86593",
    "AGENTS.md": "a0b637a6ba0dc93c380372a24e93d1691e208a7ff4dd09777b5ceeddcfb1d539",
    "CHANGELOG.md": "022ea036511cfb7c1a2f661eeb05e158c208d41eab3c45ff423ad140cd8992c5",
    "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md": "538690ae27c6e52bb5bbb6844acb3cd8f32d46f8f08ef770e09dae8d33ae9bb6",
    "audit/evidence/external-model-pid-rs-deep-audit-adjudication-2026-08-12.md": "f0e8fed8fa0319eb5f56d4b942821f2c2f1aa77b41b4f99bc7bbf3a6b73a2bc8",
    "audit/evidence/ksg-rev4-m1a-candidate-boundary-2026-08-13.md": "85bb7aed98e33f924a12bb882d8aba396a8d31b66b1432caebc48627b1e0b292",
    "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md": "591bccc8e770b9b51ab34ce8cce9d2ac54973c50185141e1a598fd90260dcc16",
    "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json": "8797335e0f23240f6f018c4403caff1a6c209f9c110ffeaa91fb47503bf331ed",
    "audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json": "d9ec2ef753ee8f8f4f3d1d3bcc11aab791b4c127445088f250e7a53d71d896f5",
    "audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md": "3f0d5facb1c65b269c4e8633699773c2ef12d92ecdebfd9d85c9da7347f94ca4",
    "audit/evidence/ksg-rev4-m1a-hosted-recovery-path-policy-v1.json": "3bb78b296e9a1898ee72a2ae88988c1a73bbb81c3247054a500935f3690a4916",
    "audit/evidence/ksg-rev4-m1a-path-policy-v1.json": "7f4944ae0d4f9578c08a16f5bd5ba251e30339f574e11fa75840857a3710942e",
    "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json": "f4a187516847c9826e9729c83906e1598df4657bc069c54a5527e71bdde17dc5",
    "audit/evidence/ksg-m1a-composite-v4-process-visual-receipt-2026-08-17.md": "f014f36f8f3cd6325a5fa9f74eda2fb7a7d9b2202eea0cb81b4af2b6387e0b81",
    "audit/evidence/ksg-rev4-m1a-composite-v3-impossibility-2026-08-15.json": "735925734c1eeb41cf4fa6a48ed20ccbb5dd0d7da786239b2ab5723b7a632b6b",
    "audit/evidence/ksg-rev4-m1a-composite-v4-path-policy-v1.json": "9b6522e8ed8c3fc797dd89bedb933e677c16491c55296c3d919ae0f933872262",
    "audit/evidence/ksg-rev4-m1a-composite-v4-process-2026-08-15.md": "c821cd7fefb472a99d2b2df5a66b7f6deb18c9c9a9c5472046abb547f4047d30",
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-hosted-capture-v5-2026-08-18.json": "d64886ca605cf82eb501fba9020938ed3f0e1adf7f635b19f3fcda8d8909bd69",
    "audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md": "6596e3c7e4a8bca989ad4724efb2f9c7592564b359b29f3a2a7a224ce2270a29",
    "audit/evidence/ksg-rev4-m1a-composite-v5-boundary-visual-receipt-2026-08-18.md": "8e73300fb5b4a0ad3d56b5b2230a9a9a45c63295c9445e9ef91fa2805ee68420",
    "audit/evidence/ksg-rev4-m1a-composite-v5-path-policy-v1.json": "dc030a357eb9a18beb8d55a5ecb23bf79c8e55676a0c50bf6661847ce5b9a89c",
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9-prepublication-closure-rejected-2026-08-17.json": "fb162cc40da3059b61eab9024f4aa38cf6daf2d84ef7e1d8a26dc7d345291e70",
    "audit/evidence/mathematical-workflow-visual-receipt-2026-08-16.md": "cc604d039f1c6a488f3d25f3ca1d16bc7624db0cc4074608475bc662a8920a46",
    "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md": "c05898e692cce675a01dda5a2ff1703b9aedb06963eb47de0ba750abfd755517",
    "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md": "1d05f596f25a3fbd835e56eb741b2013b2a01de928c29b2c0c16847d37e95c4b",
    "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md": "56154607d698b6b95672b13b772df34d470daf4f9c308826387d424988b93656",
    "audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.pdf": "9111ff1ae77c011d9b75999852136880746f3e33b137ade877bee80f6e354499",
    "audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.svg": "9022812adeb3845e9d494428fb5e2f6489bb7cf938444c1c96c364c38d4f6095",
    "audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf": "2b7f97c1491b8ab05a6223e958c9dfd2e74e2d1a41c7973d4098ae7cafd4d2d3",
    "audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.svg": "2f5040914e30e2db84c43035c3983a5e7a0150288a1ea53f8291cd4b5e7bc081",
    "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.pdf": "5153da85fba111d0249f21b9b3818cbb94d550373e00dd563b568fdcd94e0932",
    "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.svg": "9cd110dcecdd839ea37046cccc8a3a387557ca710c2589faacc367bdb1f7e324",
    "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.pdf": "0960ae0cbfdf74118111fb994ed08acd6ab6246f2176e552b317cf9fc4ffdbad",
    "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.svg": "8c38292e6fcb0b848ebdbc745f48e8e85d9842b7a8184bd7305c593778c7b70e",
    "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.pdf": "8d730825723c81f4610b188e6f290b85ee89bf2b228337a6ff887bd24ad9423c",
    "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.svg": "2e8edce85d47398482b277fe35218f6d0c245975d3052109fe76a7db61ce97f9",
    "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.pdf": "e067092709715babc62027fa5d8f7da122ebb1837c4eee0ff90ad9c2f2766527",
    "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.svg": "536dbce98e3122a7dd32be17d262012a22b641e037e564b26091b310c58657ab",
    "audit/formal/latex/ksg-m1a-composite-v4-process.tex": "21667a4d5d25a875d56d8794486593d4328cae4b24b655d26bc33de527496657",
    "audit/formal/latex/ksg-m1a-composite-v5-boundary.tex": "8f32bf892c102b73c20d507c92b631d2387ab07b686ab7e0a163eae7f1f52527",
    "audit/formal/latex/mathematical-problem-solving-workflow.tex": "deb0cf82f4ddaa2ecfeb858d1130df12d9a3831feaf9f3215fa176c8a2f9aae1",
    "audit/formal/requirements-pdf.txt": "f1f2171ff6481ee900b72df600d8326140d001a1a024977b41386461e2b57d36",
    "audit/schemas/current-source-state-v1.schema.json": "501ed8fcca211ae598e041a5596b44574c48da46a9143cafe7266a7493b93f53",
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v4.schema.json": "7512e24e3256baaacca2d75a23a9ae2a530cd987f6460788d2b431175f41c8d1",
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v5.schema.json": "cbacb1bd7b5896a497312fd2a2809a33e43699bb3e4eb081d19cde6803b69c24",
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json": "797e7c5a0dc7122aff6c16319749c3a18683ebbe21e94dd039cdc5b7a330d42c",
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json": "345296eca6d944fbc40d1133b862a7ff047a6083123b023e1533a2f22cf4a2c5",
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v4.schema.json": "8492da6dfd704667515e7b9da88d501de34903e5e2b52582106211b07f48528e",
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v5.schema.json": "7fc4fac9fdf923610768df6a5e4c90440d85400572d31e48b45367eeeb8f8e9d",
    "audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json": "b477f8c4c3cb2066c0eb9c09a98cb9fbbc3ba330951aed440d2011fcace4d672",
    "audit/schemas/post-commit-source-state-v2.schema.json": "2f4531f4cde575d3bbb573d09a85a27664fef5c4f0fde32b232498460c9a198a",
    "justfile": "f0ba67880981b7ff1b8ca38e8f1218df1de1c9dc8be92e8c4930dc0b16617c7e",
    "output/pdf/ksg-m1a-composite-v4-process.pdf": "e9c38547d092b4d1c4940d4f04066d8384232d6afb3ea304f83fb4b18b835265",
    "output/pdf/ksg-m1a-composite-v5-boundary.pdf": "bf932cfb2dbe70500458cc8de0d4ce2f3718bfe5d135755e2a9147c3d6621a79",
    "output/pdf/ksg-m1a-composite-v5-boundary.rendering-receipt.tsv": "7730f32febfb3a0ce2bc90b8300980aa299c6afd1d957ada7a14daaeae741413",
    "output/pdf/mathematical-problem-solving-workflow.pdf": "6abf5af2ab7fb5cf0b40c37977dc38156d4bdf251b6f2948815c472fc77f1288",
    "output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv": "95a6e38797f6f4086ae0094bf187649bc01834a54e6a2d6c7aae9b2a4ae3b63d",
    "scripts/README.md": "67350d26d69a0d5774bdedb6e59ad4b46ef07c211ecf10340baad7a6c352ff47",
    "scripts/capture-ksg-m1a-composite-v4.py": "7cf9a6fe57c2a828def8789524069e14a21d35739a5019b4310613c8f44065ef",
    "scripts/capture-ksg-m1a-composite-v5.py": "a0e955c9645c852276a3750ee24c49c8feb029d748a73909461d4f71777b3a11",
    "scripts/check-certified-sxpid2-claim-self-test.py": "c4fc122de0908ad076ebd029e6bde80e9debb0ee3f187f39f71a644a6dc81327",
    "scripts/check-certified-sxpid2-claim.py": "54c64e7a9d21d6d1186d5e6d446c54584663318505ab96cc539a65ff986056e1",
    "scripts/check-current-release-state.sh": "a97a690a6e2df35b2bbe957c901c65418ced7104d2df6ea93ddb22f2cc03d99a",
    "scripts/check-current-source-state-v1-self-test.py": "3dc2d846f2512e10f871ad21dbda8d45817884998942c1325cf2b78138d5753e",
    "scripts/check-current-source-state-v1.py": "1d9561909cee8ace366802c76ba108cb5418499d9549946aad34c809fff57bd7",
    "scripts/check-formal-pdf-set.sh": "e26970509de4fef73e271083d203c82e871fa8e70ec5826b6b769ed4a41541c2",
    "scripts/check-formal-pdf-style.py": "624661dd734fa91728e77798708b2fa5a9fcbf4d799bb32f1b5388f7a661ce7e",
    "scripts/check-ksg-m1a-custody-correction-self-test.py": "a466461b9eecd4afd3f839aa8137a6fc6b4de13e1aa6e18dc81b0862c6f0fdcb",
    "scripts/check-ksg-m1a-custody-correction.py": "e504fb1617fc93abd096ced451d82c74745011edb4a3b4673bd2dd8c4cea3147",
    "scripts/check-ksg-m1a-hosted-recovery-self-test.py": "0ebd801ce758203ce12111ccec8802bc9a6c68ad80033105abc59f6e60d05787",
    "scripts/check-ksg-m1a-hosted-recovery.py": "7bbbe8d32e4f6ad631f9c2d5074f4a06e7872492945404ad26fd2195664592ee",
    "scripts/check-ksg-m1a-phase-self-test.py": "851299dfb62de6cbec9f77f893ea5992839bc007e77e5772c30689281307873c",
    "scripts/check-ksg-m1a-phase.py": "433b493a52af6f7c738ba96fed99cf1f5183d975785527c0a040848a0ae14d42",
    "scripts/check-ksg-m1a-composite-v4-process-pdf.sh": "8881f819da0a5ba8e6db31a007aa2465fbac7982de4c662b3d48d477bedfcf83",
    "scripts/check-ksg-m1a-composite-v4-self-test.py": "4a40f43396e5b45aa0a5762995eabb908b61d850b1a215aa817c731140a6078b",
    "scripts/check-ksg-m1a-composite-v4.py": "8fb61c4fcc831be1847ddec7448e2dbeb6f2f51b915b4b6cd91df561c491b5bb",
    "scripts/check-ksg-m1a-composite-v5-boundary-pdf-self-test.sh": "fe8aa30908d1d2f8fc603b50708a2f57011a8b7a46b95e82e1ec45b311660079",
    "scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh": "81c7e8efbec07dc7a1c26e0d63075a4bbae6c0125547d6daac70596940beb61c",
    "scripts/check-ksg-m1a-composite-v5-self-test.py": "61024e4df9ee0999fdf03e79c505dcf8c268188779b5424665143808679b24aa",
    "scripts/check-ksg-m1a-composite-v5.py": "b510e3e1a9831a41f6904fd9fd259c227c426b11436ead11789a04ad474a8c30",
    "scripts/check-mathematical-workflow-pdf-self-test.sh": "b8f42aa6dbd403861479c5a27960934bbf63f1d1372ec11caf8efc5a2a9d0228",
    "scripts/check-mathematical-workflow-pdf.sh": "7af9d7acde3f2f61022007eb3ad1bd1c1862b18636071f2df6f48d346ce7678f",
    "scripts/check-post-commit-source-state-v2-self-test.py": "b1f45814efca5754bdb33c0b41258be9f1874fd404ff7620505878a7c8fa4657",
    "scripts/check-post-commit-source-state-v2.py": "06fa6721d366fd33b9bd8997d108c31578bc32da4bcdcda8ccf5aeb22fad94d3",
    "scripts/check-release-state-self-test.sh": "e9fec4e65a42653b9488b5fb02ceee669aeb7d374ddd34334c6755fb7eff6f0d",
    "scripts/check-zeta-pid-transfer-firewall-self-test.py": "8803595bc5af615cf88215b9bdd40d7a8d227724b410c4b04802a63e81b0704e",
    "scripts/check-zeta-pid-transfer-firewall.py": "97d45807f7b58b9fb8a62a2c4007e514adfdc5aeadf811daf590010cb313b65f",
    "scripts/generate-lean-4.33-replay.py": "2a5b4a1b588f4b1fe66b30fd8814be2268584511a1b7306720cc158ea43115b9",
    "scripts/normalize-actions-checkout-worktree-config-self-test.py": "3eb085d0a49ff463aa3c419352d7c926d4804ff988e92edebbd3dd5ac013b101",
    "scripts/normalize-actions-checkout-worktree-config.py": "8887789f2039c8603a61f40f2518b707fa37f2311ccbd613e8c927fb6856be18",
}
EXPECTED_PENDING_OPERATIONAL_PATHS = tuple(
    relative
    for relative, digest in EXPECTED_OPERATIONAL_WIRING_HASHES.items()
    if digest == PENDING_OPERATIONAL_SHA256
)
EXPECTED_ABSENT_OPERATIONAL_PATHS = (
    "scripts/check-post-commit-source-state-v1-self-test.py",
    "scripts/check-post-commit-source-state-v1.py",
)
EXPECTED_ACTIVE_CLAIM_HASHES = {
    "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json": "360e070d2f92e141e0f1ab672e6f6dd8a8d41bc1f193b735cae93d44ed8ab32e",
    "claims/KSG-INTEGER-HARMONIC-001/formal-replay-lean-4.33.0-2026-08-11.md": "b5a974d3bc0cd66e37a963e33d87100c80c038d106f9bf19f27682062f848eae",
    "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md": "1402245ded95bf69c8088a087de9e6951acb0094c443265e3014d7abf4035e44",
    "claims/SX-COUNT-ATOM-BRIDGE-001/conventions.md": "9968de732de7477a5e6342893731affbd222a216ca822209e4059baebb6b6e74",
    "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md": "cca911f47befd9f47948a9233677fa0a5a909bcd13d7f803172cc542e1c68637",
    "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md": "76ec940dae7d2b98c52f51cb44b49e00bb835708cb0b11b02b076bfcba61af41",
    "claims/SX-COUNT-ATOM-BRIDGE-001/formal/theorem-map.md": "552d754b8332ae41a6ded0a5f607deb357c0e8fdfb8e96eaf09708f29396be8f",
    "claims/SX-COUNT-ATOM-BRIDGE-001/obligations-v2.md": "47e573e617088b38243a7b23b75e7e2624754b3f8d86be64de498086fa1b6ad7",
    "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md": "1008f44776f7a063a5a21632666266dd21e752c42639d53926119b03d0568f99",
    "claims/SX-COUNT-ATOM-BRIDGE-001/routes-v2.md": "517f59f595acc57197c267e295952389d67c7e2c47af6990127862ae9340f4b9",
    "claims/SX-COUNT-EVENT-BRIDGE-001/claim-v2.md": "4e8fc1dda680b5fdf0ffcdb3af7cbe97017fa6421a4cd3393983d4047a87ff7b",
    "claims/SX-COUNT-EVENT-BRIDGE-001/conventions.md": "344c78c61d017af3cf1b21d5585826e06ac4a4149f6e7b1b2b3c372df8155cb6",
    "claims/SX-COUNT-EVENT-BRIDGE-001/decision-v2.md": "663fc625c3ede8c1530aaad07d1446d01da022d5835650a489c7a9f0977b8445",
    "claims/SX-COUNT-EVENT-BRIDGE-001/evidence-matrix.md": "c2bc3f6a0fb551371c5385c79c5a272e9bd493eb37987108bc4193fc608c76df",
    "claims/SX-COUNT-EVENT-BRIDGE-001/formal/theorem-map.md": "f765416999303ba151a51f9706053c8546b0fc02216b780b4e9523ea157f6994",
    "claims/SX-COUNT-EVENT-BRIDGE-001/obligations-v2.md": "4257fbfc0af90d9a7d8247bc6d765b2348e618a5febcd9e37fb7cff8e0c057cc",
    "claims/SX-COUNT-EVENT-BRIDGE-001/revision-index.md": "8127e06261aec8953dcbf21d6880b6143bece27b7c9957d8ff026ab71e51d498",
    "claims/SX-COUNT-EVENT-BRIDGE-001/routes-v2.md": "8a41fb691e76104ad6e28a8b439ca2de836ad2a2dd42fd39cace7d8a0e2a2c11",
}
EXPECTED_PENDING_ACTIVE_CLAIM_PATHS = tuple(
    relative
    for relative, digest in EXPECTED_ACTIVE_CLAIM_HASHES.items()
    if digest == PENDING_OPERATIONAL_SHA256
)
EXPECTED_COMMAND_NAMES = (
    "lean_version_probe",
    "lake_version_probe",
    "clean_build",
    *(f"direct_lean_t0:{source}" for source in EXPECTED_DIRECT_SOURCES),
    "leanchecker_fresh",
    "theorem_axiom_audit",
    "derived_instance_query",
    *(
        name
        for pair in PYTHON_COMMAND_PAIRS
        for name in (f"{pair}:normal", f"{pair}:optimized")
    ),
)
GIT_FIXED_ARGUMENTS = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "core.attributesFile=/dev/null",
    "-c",
    "diff.external=",
)
EXPECTED_THEOREM_AXIOM_AUDIT_STDIN = {
    "bytes": 18200,
    "sha256": "30acaa1de98051b247a91b735eb8ab08f2870a7f6e23b81c18c362815681b2e4",
}
UTC_TIMESTAMP = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\Z")
SHA256_TEXT = re.compile(r"\A[0-9a-f]{64}\Z")


class FreezeError(RuntimeError):
    """The frozen policy, replay, live bytes, or historical custody failed."""


@dataclass(frozen=True)
class Snapshot:
    raw: bytes
    identity: tuple[int, int, int, int, int, int, int]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def replay_receipt_projection_sha256(receipt: dict[str, Any]) -> str:
    """Bind all replay observations except the intentionally cyclic checker hash."""

    projected = dict(receipt)
    custody = projected.get("custody_gate_sha256")
    if isinstance(custody, dict):
        self_test_path = "scripts/check-lean-toolchain-freeze-self-test.py"
        projected["custody_gate_sha256"] = {self_test_path: custody.get(self_test_path)}
    try:
        canonical = json.dumps(
            projected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise FreezeError(
            "replay receipt projection is not canonical JSON data"
        ) from error
    return hashlib.sha256(canonical).hexdigest()


def _identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def stable_read(path: Path, role: str) -> Snapshot:
    """Read a bounded single-linked regular file twice without following its leaf."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    parent_identities: list[tuple[str, tuple[int, int, int]]] = []
    cursor = absolute.parent
    while cursor != cursor.parent:
        metadata = cursor.lstat()
        require(
            stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
            f"{role} parent route must not contain a symbolic link: {cursor}",
        )
        parent_identities.append(
            (os.fspath(cursor), (metadata.st_dev, metadata.st_ino, metadata.st_mode))
        )
        cursor = cursor.parent
    before = absolute.lstat()
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"{role} must be a regular non-symbolic-link file",
    )
    require(before.st_nlink == 1, f"{role} must have exactly one hard link")
    require(before.st_size <= MAX_FILE_BYTES, f"{role} exceeds the size ceiling")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(absolute, flags)
    try:
        opened = os.fstat(descriptor)
        first = os.read(descriptor, MAX_FILE_BYTES + 1)
        require(len(first) <= MAX_FILE_BYTES, f"{role} exceeds the size ceiling")
        require(os.read(descriptor, 1) == b"", f"{role} changed size while reading")
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = os.read(descriptor, MAX_FILE_BYTES + 1)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = absolute.lstat()
    identities = (
        _identity(before),
        _identity(opened),
        _identity(after_descriptor),
        _identity(after),
    )
    require(
        all(value == identities[0] for value in identities[1:]),
        f"{role} identity changed during read",
    )
    require(first == second, f"{role} bytes changed during double read")
    require(len(first) == before.st_size, f"{role} byte count disagrees with metadata")
    for parent, expected in parent_identities:
        metadata = Path(parent).lstat()
        require(
            (metadata.st_dev, metadata.st_ino, metadata.st_mode) == expected,
            f"{role} parent route changed during read: {parent}",
        )
    return Snapshot(first, identities[0])


def duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(
    path: Path, role: str, *, pretty: bool | None = None
) -> tuple[Any, Snapshot]:
    snapshot = stable_read(path, role)
    try:
        text = snapshot.raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=duplicate_rejecting_object)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise FreezeError(
            f"{role} is not strict duplicate-free JSON: {error}"
        ) from error
    if pretty is not None:
        separators = None if pretty else (",", ":")
        indent = 2 if pretty else None
        canonical = (
            json.dumps(
                value,
                ensure_ascii=False,
                indent=indent,
                separators=separators,
                sort_keys=True,
            )
            + "\n"
        )
        require(text == canonical, f"{role} is not canonical JSON")
    return value, snapshot


def check_hashes(expected: dict[str, str], role: str) -> dict[str, Snapshot]:
    snapshots: dict[str, Snapshot] = {}
    for relative, digest in expected.items():
        snapshot = stable_read(ROOT / relative, f"{role}: {relative}")
        require(
            snapshot.sha256 == digest,
            f"{role} digest mismatch: {relative}: expected {digest}, found {snapshot.sha256}",
        )
        snapshots[relative] = snapshot
    return snapshots


def require_exact_keys(value: dict[str, Any], expected: set[str], role: str) -> None:
    require(
        set(value) == expected,
        f"{role} key inventory drifted: "
        f"missing={sorted(expected - set(value))}, "
        f"extra={sorted(set(value) - expected)}",
    )


def parse_utc_timestamp(value: object, role: str) -> datetime:
    require(
        isinstance(value, str) and UTC_TIMESTAMP.fullmatch(value) is not None,
        f"{role} is not canonical microsecond UTC text",
    )
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise FreezeError(f"{role} is not a valid timestamp: {error}") from error


def check_stream(value: object, role: str) -> tuple[int, str]:
    require(isinstance(value, dict), f"{role} is not an object")
    require_exact_keys(value, {"bytes", "sha256"}, role)
    count = value.get("bytes")
    digest = value.get("sha256")
    require(
        type(count) is int and count >= 0,
        f"{role} byte count is not a nonnegative integer",
    )
    require(
        isinstance(digest, str) and SHA256_TEXT.fullmatch(digest) is not None,
        f"{role} digest is not lowercase SHA-256",
    )
    require(
        (count == 0) == (digest == EMPTY_SHA256),
        f"{role} empty-byte/digest relationship is inconsistent",
    )
    return count, digest


def expected_command_specs() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    specs: list[tuple[str, str, tuple[str, ...]]] = [
        ("lean_version_probe", ".", ("lean", "--version")),
        ("lake_version_probe", ".", ("lake", "--version")),
        (
            "clean_build",
            "audit/formal/lean",
            ("lake", "--quiet", "--wfail", "build", "PidFiniteConvergence"),
        ),
    ]
    specs.extend(
        (
            f"direct_lean_t0:{source}",
            "audit/formal/lean",
            ("lake", "env", "lean", "-t", "0", source),
        )
        for source in EXPECTED_DIRECT_SOURCES
    )
    specs.extend(
        (
            (
                "leanchecker_fresh",
                "audit/formal/lean",
                ("lake", "env", "leanchecker", "--fresh", "PidFiniteConvergence"),
            ),
            (
                "theorem_axiom_audit",
                "audit/formal/lean",
                ("lake", "env", "lean", "--stdin"),
            ),
            (
                "derived_instance_query",
                "audit/formal/lean",
                (
                    "lake",
                    "env",
                    "lean",
                    "../../evidence/lean-4.32.0-to-4.33.0-derived-instances-query.lean",
                ),
            ),
        )
    )
    for pair, (script, flags) in PYTHON_COMMAND_PAIRS.items():
        arguments = PYTHON_COMMAND_ARGUMENTS.get(pair, ())
        specs.append(
            (
                f"{pair}:normal",
                ".",
                ("python3", "-I", "-S", "-B", *flags, script, *arguments),
            )
        )
        specs.append(
            (
                f"{pair}:optimized",
                ".",
                (
                    "python3",
                    "-O",
                    "-I",
                    "-S",
                    "-B",
                    *flags,
                    script,
                    *arguments,
                ),
            )
        )
    result = tuple(specs)
    require(
        tuple(name for name, _cwd, _argv in result) == EXPECTED_COMMAND_NAMES,
        "internal replay command inventory is inconsistent",
    )
    return result


def expected_dependency_preflight_specs() -> tuple[
    tuple[str, str, tuple[str, ...]], ...
]:
    specs: list[tuple[str, str, tuple[str, ...]]] = []
    for name in sorted(EXPECTED_PACKAGE_PINS):
        cwd = f"audit/formal/lean/.lake/packages/{name}"
        specs.extend(
            (
                (
                    f"{name} local config inventory",
                    cwd,
                    ("config", "--no-includes", "--local", "--name-only", "--list"),
                ),
                (f"{name} root check", cwd, ("rev-parse", "--show-toplevel")),
                (f"{name} revision check", cwd, ("rev-parse", "--verify", "HEAD")),
                (
                    f"{name} origin check",
                    cwd,
                    (
                        "config",
                        "--no-includes",
                        "--local",
                        "--get",
                        "remote.origin.url",
                    ),
                ),
                (
                    f"{name} cleanliness check",
                    cwd,
                    ("status", "--porcelain=v1", "--untracked-files=all"),
                ),
            )
        )
    return tuple(specs)


def check_dependency_preflight_records(
    receipt: dict[str, Any], environment: dict[str, Any], formal_start: datetime
) -> None:
    records = receipt.get("dependency_checkout_preflight")
    require(isinstance(records, list), "dependency preflight records are not a list")
    specs = expected_dependency_preflight_specs()
    require(len(records) == len(specs), "dependency preflight record count drifted")
    previous_end: datetime | None = None
    git = environment["git_executable"]
    root = environment["repo_root_observed"]
    for record, (name, cwd_relative, arguments) in zip(records, specs, strict=True):
        require(
            isinstance(record, dict), f"dependency preflight record malformed: {name}"
        )
        require_exact_keys(
            record,
            {
                "argv_executed",
                "cwd_observed_absolute",
                "end_utc",
                "executable_snapshot_equal_before_after",
                "exit_code",
                "name",
                "start_utc",
                "stderr",
                "stdin",
                "stdout",
            },
            f"dependency preflight record: {name}",
        )
        require(
            record.get("name") == name, f"dependency preflight name drifted: {name}"
        )
        require(
            record.get("argv_executed") == [git, *GIT_FIXED_ARGUMENTS, *arguments],
            f"dependency preflight argv drifted: {name}",
        )
        expected_cwd = os.path.join(root, cwd_relative)
        require(
            record.get("cwd_observed_absolute") == expected_cwd,
            f"dependency preflight cwd drifted: {name}",
        )
        start = parse_utc_timestamp(record.get("start_utc"), f"{name} start")
        end = parse_utc_timestamp(record.get("end_utc"), f"{name} end")
        require(start <= end, f"dependency preflight has negative duration: {name}")
        if previous_end is not None:
            require(
                previous_end <= start,
                f"dependency preflight chronology overlaps: {name}",
            )
        previous_end = end
        require(
            end <= formal_start,
            f"dependency preflight ran after formal replay began: {name}",
        )
        require(
            record.get("exit_code") == 0
            and record.get("executable_snapshot_equal_before_after") is True,
            f"dependency preflight status/snapshot drifted: {name}",
        )
        stdin = check_stream(record.get("stdin"), f"{name} stdin")
        stdout = check_stream(record.get("stdout"), f"{name} stdout")
        stderr = check_stream(record.get("stderr"), f"{name} stderr")
        require(
            stdin == (0, EMPTY_SHA256), f"dependency preflight stdin drifted: {name}"
        )
        require(
            stderr == (0, EMPTY_SHA256), f"dependency preflight stderr drifted: {name}"
        )
        package = name.split(" ", 1)[0]
        url, revision, _input, _inherited = EXPECTED_PACKAGE_PINS[package]
        if name.endswith(" root check"):
            expected = (expected_cwd + "\n").encode("utf-8")
            require(
                stdout == (len(expected), hashlib.sha256(expected).hexdigest()),
                f"dependency root output drifted: {package}",
            )
        elif name.endswith(" revision check"):
            expected = (revision + "\n").encode("utf-8")
            require(
                stdout == (len(expected), hashlib.sha256(expected).hexdigest()),
                f"dependency revision output drifted: {package}",
            )
        elif name.endswith(" origin check"):
            expected = (url + "\n").encode("utf-8")
            require(
                stdout == (len(expected), hashlib.sha256(expected).hexdigest()),
                f"dependency origin output drifted: {package}",
            )
        elif name.endswith(" cleanliness check"):
            require(
                stdout == (0, EMPTY_SHA256),
                f"dependency checkout was not clean: {package}",
            )
        else:
            require(
                stdout[0] > 0, f"dependency local config inventory was empty: {package}"
            )


def check_command_records(receipt: dict[str, Any]) -> None:
    environment = receipt.get("execution_environment")
    require(isinstance(environment, dict), "replay execution environment is malformed")
    require_exact_keys(
        environment,
        {
            "executable_link_counts",
            "executable_sha256",
            "executable_size_bytes",
            "git_executable",
            "lake_executable",
            "lean_bin_directory",
            "lean_executable",
            "leanchecker_executable",
            "python_executable",
            "repo_root_observed",
        },
        "replay execution environment",
    )
    path_keys = (
        "git_executable",
        "lake_executable",
        "lean_bin_directory",
        "lean_executable",
        "leanchecker_executable",
        "python_executable",
        "repo_root_observed",
    )
    for key in path_keys:
        require(
            isinstance(environment[key], str)
            and os.path.isabs(environment[key])
            and os.path.normpath(environment[key]) == environment[key],
            f"replay execution path is not normalized absolute text: {key}",
        )
    require(
        environment["executable_sha256"] == EXPECTED_LOCAL_EXECUTABLE_SHA256,
        "replay host-local executable digest drifted",
    )
    require(
        environment["executable_size_bytes"] == EXPECTED_LOCAL_EXECUTABLE_SIZE_BYTES,
        "replay host-local executable size drifted",
    )
    require(
        environment["executable_link_counts"] == EXPECTED_LOCAL_EXECUTABLE_LINK_COUNTS,
        "replay host-local executable link-count drifted",
    )
    require(
        os.path.dirname(environment["lake_executable"])
        == environment["lean_bin_directory"]
        == os.path.dirname(environment["lean_executable"]),
        "replay Lean/Lake executables do not share the observed release bin directory",
    )
    require(
        environment["lean_bin_directory"] == EXPECTED_LOCAL_REPLAY_ROUTES["lean_bin"]
        and environment["lean_executable"]
        == os.path.join(EXPECTED_LOCAL_REPLAY_ROUTES["lean_bin"], "lean")
        and environment["lake_executable"]
        == os.path.join(EXPECTED_LOCAL_REPLAY_ROUTES["lean_bin"], "lake")
        and environment["leanchecker_executable"]
        == os.path.join(EXPECTED_LOCAL_REPLAY_ROUTES["lean_bin"], "leanchecker")
        and environment["python_executable"] == EXPECTED_LOCAL_REPLAY_ROUTES["python"]
        and environment["git_executable"] == EXPECTED_LOCAL_REPLAY_ROUTES["git"]
        and environment["repo_root_observed"]
        == EXPECTED_LOCAL_REPLAY_ROUTES["repo_root"],
        "replay host-local execution route drifted",
    )
    require(
        os.path.basename(environment["lake_executable"]) == "lake"
        and os.path.basename(environment["lean_executable"]) == "lean"
        and os.path.basename(environment["leanchecker_executable"]) == "leanchecker"
        and os.path.basename(environment["python_executable"]).startswith("python3")
        and os.path.basename(environment["git_executable"]) == "git",
        "replay executable names drifted",
    )
    environment_policy = receipt.get("environment_policy")
    require(
        isinstance(environment_policy, dict),
        "replay environment policy is malformed",
    )
    require_exact_keys(
        environment_policy,
        {
            "ambient_environment_inherited",
            "command_timeout_seconds",
            "effective_nonsecret_environment",
            "isolated_home_initially_empty",
            "isolated_tmpdir_initially_empty",
            "isolated_tmpdir_identity_retained",
            "max_stderr_bytes",
            "max_stdout_bytes",
            "new_session_process_group_each_command",
            "process_group_cleanup_bounded_best_effort",
            "python_isolation_flags",
            "routing_variables_inherited",
            "signal_dispositions",
            "signal_mask",
            "stdin_inherited",
            "umask_octal",
        },
        "replay environment policy",
    )
    require(
        environment_policy.get("ambient_environment_inherited") is False
        and environment_policy.get("routing_variables_inherited") == []
        and environment_policy.get("stdin_inherited") is False,
        "replay environment inherited ambient variables",
    )
    require(
        environment_policy.get("umask_octal") == "0077",
        "replay fixed process umask drifted",
    )
    require(
        environment_policy.get("command_timeout_seconds") == 3600
        and environment_policy.get("max_stdout_bytes") == 16 * 1024 * 1024
        and environment_policy.get("max_stderr_bytes") == 16 * 1024 * 1024
        and environment_policy.get("new_session_process_group_each_command") is True
        and environment_policy.get("process_group_cleanup_bounded_best_effort") is True,
        "replay bounded-child policy drifted",
    )
    require(
        environment_policy.get("signal_mask") == []
        and environment_policy.get("signal_dispositions")
        == {
            "SIGCHLD": "SIG_DFL",
            "SIGHUP": "SIG_DFL",
            "SIGINT": "SIG_DFL",
            "SIGPIPE": "SIG_DFL",
            "SIGTERM": "SIG_DFL",
        },
        "replay normalized signal state drifted",
    )
    require(
        environment_policy.get("isolated_home_initially_empty") is True
        and environment_policy.get("isolated_tmpdir_initially_empty") is True
        and environment_policy.get("isolated_tmpdir_identity_retained") is True,
        "replay isolated environment was not recorded empty",
    )
    require(
        environment_policy.get("python_isolation_flags") == ["-I", "-S", "-B"],
        "replay Python isolation policy drifted",
    )
    effective = environment_policy.get("effective_nonsecret_environment")
    require(isinstance(effective, dict), "replay effective environment is malformed")
    require_exact_keys(
        effective,
        {
            "GIT_CONFIG_GLOBAL",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_NO_REPLACE_OBJECTS",
            "GIT_OPTIONAL_LOCKS",
            "GIT_PAGER",
            "GIT_TERMINAL_PROMPT",
            "HOME",
            "LANG",
            "LC_ALL",
            "PAGER",
            "PATH",
            "PYTHONDONTWRITEBYTECODE",
            "PYTHONNOUSERSITE",
            "TMPDIR",
            "TZ",
        },
        "replay effective environment",
    )
    require(
        effective.get("LANG") == "C"
        and effective.get("LC_ALL") == "C"
        and effective.get("TZ") == "UTC"
        and effective.get("PYTHONDONTWRITEBYTECODE") == "1"
        and effective.get("PYTHONNOUSERSITE") == "1",
        "replay fixed environment values drifted",
    )
    require(
        effective.get("GIT_CONFIG_GLOBAL") == "/dev/null"
        and effective.get("GIT_CONFIG_NOSYSTEM") == "1"
        and effective.get("GIT_NO_REPLACE_OBJECTS") == "1"
        and effective.get("GIT_OPTIONAL_LOCKS") == "0"
        and effective.get("GIT_PAGER") == "cat"
        and effective.get("GIT_TERMINAL_PROMPT") == "0"
        and effective.get("PAGER") == "cat",
        "replay fixed Git environment drifted",
    )
    require(
        effective.get("PATH")
        == os.pathsep.join(
            (
                environment["lean_bin_directory"],
                "/usr/bin",
                "/bin",
            )
        ),
        "replay executable PATH drifted",
    )
    home = effective.get("HOME")
    tmpdir = effective.get("TMPDIR")
    require(
        isinstance(home, str)
        and isinstance(tmpdir, str)
        and os.path.isabs(home)
        and os.path.isabs(tmpdir)
        and os.path.normpath(home) == home
        and os.path.normpath(tmpdir) == tmpdir
        and os.path.dirname(home) == os.path.dirname(tmpdir)
        and os.path.basename(home) == "home"
        and os.path.basename(tmpdir) == "tmp"
        and os.path.basename(os.path.dirname(home)).startswith(
            "pid-rs-lean433-replay-env."
        ),
        "replay isolated HOME/TMPDIR layout drifted",
    )

    records = receipt.get("command_records")
    require(isinstance(records, list), "replay command records are not a list")
    specs = expected_command_specs()
    require(
        len(records) == len(specs),
        "replay command record count drifted",
    )
    previous_end: datetime | None = None
    parsed_times: list[tuple[datetime, datetime]] = []
    by_name: dict[str, dict[str, Any]] = {}
    for record, (expected_name, expected_cwd, expected_argv) in zip(
        records, specs, strict=True
    ):
        require(
            isinstance(record, dict),
            f"replay command is not an object: {expected_name}",
        )
        require_exact_keys(
            record,
            {
                "argv_executed",
                "argv_logical",
                "cache_state",
                "cwd_observed_absolute",
                "cwd_repo_relative",
                "end_utc",
                "exit_code",
                "name",
                "start_utc",
                "stderr",
                "stdin",
                "stdout",
            },
            f"replay command {expected_name}",
        )
        require(
            record.get("name") == expected_name, "replay command order/name drifted"
        )
        require(
            record.get("cwd_repo_relative") == expected_cwd,
            f"replay cwd drifted: {expected_name}",
        )
        logical = record.get("argv_logical")
        executed = record.get("argv_executed")
        require(
            isinstance(logical, list)
            and all(isinstance(item, str) for item in logical)
            and tuple(logical) == expected_argv,
            f"replay logical argv drifted: {expected_name}",
        )
        require(
            isinstance(executed, list)
            and all(isinstance(item, str) for item in executed)
            and len(executed) == len(logical)
            and executed[1:] == logical[1:],
            f"replay executed argv drifted: {expected_name}",
        )
        expected_executable = {
            "lake": environment["lake_executable"],
            "lean": environment["lean_executable"],
            "python3": environment["python_executable"],
        }[logical[0]]
        require(
            executed[0] == expected_executable,
            f"replay executable drifted: {expected_name}",
        )
        expected_absolute_cwd = (
            environment["repo_root_observed"]
            if expected_cwd == "."
            else os.path.normpath(
                os.path.join(environment["repo_root_observed"], expected_cwd)
            )
        )
        require(
            record.get("cwd_observed_absolute") == expected_absolute_cwd,
            f"replay observed cwd drifted: {expected_name}",
        )
        start = parse_utc_timestamp(record.get("start_utc"), f"{expected_name} start")
        end = parse_utc_timestamp(record.get("end_utc"), f"{expected_name} end")
        require(start <= end, f"replay command has negative duration: {expected_name}")
        if previous_end is not None:
            require(
                previous_end <= start,
                f"replay command chronology overlaps: {expected_name}",
            )
        previous_end = end
        parsed_times.append((start, end))
        require(
            record.get("exit_code") == 0,
            f"replay command did not exit zero: {expected_name}",
        )
        stdout = check_stream(record.get("stdout"), f"{expected_name} stdout")
        stderr = check_stream(record.get("stderr"), f"{expected_name} stderr")
        require(
            stderr == (0, EMPTY_SHA256),
            f"replay command emitted stderr: {expected_name}",
        )
        stdin = record.get("stdin")
        stdin_stream = check_stream(stdin, f"{expected_name} stdin")
        cache_state = record.get("cache_state")
        if expected_name == "clean_build":
            require(
                stdin_stream == (0, EMPTY_SHA256),
                "clean build did not receive exact empty stdin",
            )
            require(
                cache_state
                == {
                    "dependency_packages_directory_present_before": True,
                    "project_build_directory_absent_before": True,
                    "project_config_directory_absent_before": True,
                    "project_oleans_reused": False,
                },
                "clean build cache-isolation record drifted",
            )
            require(
                record.get("stdout") == EXPECTED_CLEAN_BUILD_STDOUT_STREAM,
                "clean build exact stdout drifted",
            )
        elif expected_name == "lean_version_probe":
            require(
                stdin_stream == (0, EMPTY_SHA256) and cache_state is None,
                "Lean version probe recorded unexpected input/cache state",
            )
            line = receipt.get("lean_version_line")
            require(
                isinstance(line, str)
                and stdout
                == (
                    len(line.encode("utf-8")),
                    hashlib.sha256(line.encode("utf-8")).hexdigest(),
                ),
                "chronologized Lean version output drifted",
            )
            require(
                record["stderr"] == receipt.get("lean_version_stderr"),
                "chronologized Lean version stderr drifted",
            )
        elif expected_name == "lake_version_probe":
            require(
                stdin_stream == (0, EMPTY_SHA256) and cache_state is None,
                "Lake version probe recorded unexpected input/cache state",
            )
            line = receipt.get("lake_version_line")
            require(
                isinstance(line, str)
                and stdout
                == (
                    len(line.encode("utf-8")),
                    hashlib.sha256(line.encode("utf-8")).hexdigest(),
                ),
                "chronologized Lake version output drifted",
            )
            require(
                record["stderr"] == receipt.get("lake_version_stderr"),
                "chronologized Lake version stderr drifted",
            )
        elif expected_name == "theorem_axiom_audit":
            require(cache_state is None, "axiom audit unexpectedly records cache state")
            require(
                stdin == EXPECTED_THEOREM_AXIOM_AUDIT_STDIN
                and stdin_stream
                == (
                    EXPECTED_THEOREM_AXIOM_AUDIT_STDIN["bytes"],
                    EXPECTED_THEOREM_AXIOM_AUDIT_STDIN["sha256"],
                ),
                "theorem axiom audit stdin drifted from the exact 246-name query",
            )
            require(stdout == (0, EMPTY_SHA256), "theorem axiom audit emitted stdout")
        else:
            require(
                stdin_stream == (0, EMPTY_SHA256),
                f"replay command did not receive exact empty stdin: {expected_name}",
            )
            require(
                cache_state is None,
                f"replay command unexpectedly records cache state: {expected_name}",
            )
        if (
            expected_name.startswith("direct_lean_t0:")
            or expected_name == "leanchecker_fresh"
        ):
            require(
                stdout == (0, EMPTY_SHA256),
                f"Lean replay emitted stdout: {expected_name}",
            )
        if expected_name == "derived_instance_query":
            require(
                stdout
                == (
                    1850,
                    EXPECTED_DERIVED_EVIDENCE_HASHES[
                        "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.33.0.stdout"
                    ],
                ),
                "derived-instance query output drifted",
            )
        by_name[expected_name] = record

    window = receipt.get("execution_window")
    require(isinstance(window, dict), "replay execution window is malformed")
    require_exact_keys(window, {"end_utc", "start_utc"}, "replay execution window")
    require(
        parse_utc_timestamp(window.get("start_utc"), "replay window start")
        == parsed_times[0][0]
        and parse_utc_timestamp(window.get("end_utc"), "replay window end")
        == parsed_times[-1][1],
        "replay execution window does not bind first/last command",
    )
    check_dependency_preflight_records(receipt, environment, parsed_times[0][0])
    archive_observation = receipt.get("official_archive_observation")
    require(
        isinstance(archive_observation, dict)
        and parse_utc_timestamp(
            archive_observation.get("end_utc"), "local archive observation end"
        )
        <= parsed_times[0][0],
        "local archive observation was not completed before replay commands",
    )

    parity_pairs: dict[str, dict[str, object]] = {}
    for pair in PYTHON_COMMAND_PAIRS:
        normal = by_name[f"{pair}:normal"]
        optimized = by_name[f"{pair}:optimized"]
        require(
            normal["stdout"] == optimized["stdout"]
            and normal["stderr"] == optimized["stderr"],
            f"normal/-O output differs: {pair}",
        )
        parity_pairs[pair] = {
            "normal_stderr": normal["stderr"],
            "normal_stdout": normal["stdout"],
            "optimized_stderr": optimized["stderr"],
            "optimized_stdout": optimized["stdout"],
        }
    require(
        receipt.get("python_optimization_parity")
        == {"all_equal": True, "pairs": parity_pairs},
        "normal/-O replay parity summary drifted",
    )
    evidence_outputs = {
        "citation_checker": "audit/evidence/lean-citation-edge-countermodel-4.33.0.json",
        "descriptor_checker": "audit/evidence/foundational-sxpid-descriptor-factorization-lean-4.33.0.json",
        "descriptor_self_test": "audit/evidence/foundational-sxpid-descriptor-factorization-mutations-4.33.0.json",
        "exact_product_checker": "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json",
        "ksg_checker": "audit/evidence/lean-ksg-integer-harmonic-4.33.0.json",
    }
    for pair, evidence in evidence_outputs.items():
        require(
            by_name[f"{pair}:normal"]["stdout"]["sha256"]
            == EXPECTED_CURRENT_EVIDENCE_HASHES[evidence],
            f"current evidence is not the recorded checker stdout: {pair}",
        )


def check_policy() -> None:
    policy, snapshot = load_json(POLICY, "Lean freeze policy", pretty=True)
    require(
        snapshot.sha256 == EXPECTED_POLICY_SHA256, "Lean freeze policy digest mismatch"
    )
    require(
        policy.get("schema") == "pid-rs/lean-toolchain-freeze-policy/v1",
        "freeze policy schema drifted",
    )
    require(policy.get("state") == "frozen", "freeze policy is not frozen")
    automatic = policy.get("automatic_update_policy")
    require(isinstance(automatic, dict), "freeze automatic-update policy is malformed")
    require(
        automatic.get("check_latest_release") is False,
        "freeze policy enabled latest-release checks",
    )
    require(
        automatic.get("new_release_alone_is_trigger") is False,
        "new release alone became a trigger",
    )
    triggers = policy.get("reevaluation_triggers")
    require(isinstance(triggers, list), "freeze triggers are malformed")
    require(
        tuple(item.get("id") for item in triggers if isinstance(item, dict))
        == EXPECTED_TRIGGERS,
        "freeze trigger inventory drifted",
    )
    trigger_descriptions = {
        item["id"]: item.get("description", "") for item in triggers
    }
    for trigger, tokens in {
        "required_capability_or_incompatibility": (
            "required by the maintained project scope",
            "no acceptable pinned-baseline workaround",
        ),
        "baseline_unavailability": (
            "sustainably and reproducibly unobtainable",
            "official and repository-cache routes",
            "transient network",
        ),
        "explicit_human_migration_decision": (
            "explicit exception record with rationale",
            "new release alone is insufficient",
            "before activation",
        ),
    }.items():
        require(
            all(token in trigger_descriptions[trigger] for token in tokens),
            f"freeze trigger lost its evidentiary threshold: {trigger}",
        )
    require(
        tuple(policy.get("nontriggers", ())) == EXPECTED_NONTRIGGERS,
        "freeze nontrigger inventory drifted",
    )
    require(
        policy.get("candidate_transition_policy")
        == {
            "active_baseline_remains_authority_until": (
                "A migration candidate closes every required source, kernel, "
                "checker, mutation, custody, documentation, and replay gate."
            ),
            "failed_candidate_disposition": (
                "Reject or archive the candidate without changing the active "
                "4.33.0 baseline."
            ),
            "rollback_plan_required_before_activation": True,
        },
        "freeze candidate transition/rollback policy drifted",
    )
    pin = policy.get("active_pin")
    require(isinstance(pin, dict), "freeze active pin is malformed")
    require(
        pin.get("lean_toolchain") == "leanprover/lean4:v4.33.0",
        "freeze Lean pin drifted",
    )
    require(
        pin.get("lean_commit") == EXPECTED_LEAN_IDENTITY["commit"],
        "freeze Lean commit drifted",
    )
    require(
        pin.get("mathlib_revision") == EXPECTED_PACKAGE_PINS["mathlib"][1],
        "freeze Mathlib pin drifted",
    )
    require(pin.get("mathlib_tag") == "v4.33.0", "freeze Mathlib tag drifted")
    require(
        pin.get("lake_manifest_sha256")
        == EXPECTED_CONFIG_HASHES["audit/formal/lean/lake-manifest.json"],
        "freeze manifest digest drifted",
    )
    require(
        pin.get("lakefile_sha256")
        == EXPECTED_CONFIG_HASHES["audit/formal/lean/lakefile.toml"],
        "freeze lakefile digest drifted",
    )
    require(
        pin.get("selection") == "explicit_human_migration_decision",
        "freeze selection authority drifted",
    )


def check_manifest() -> None:
    manifest, _snapshot = load_json(
        PROJECT / "lake-manifest.json", "active Lake manifest"
    )
    require(isinstance(manifest, dict), "Lake manifest root must be an object")
    packages = manifest.get("packages")
    require(isinstance(packages, list), "Lake package inventory must be a list")
    require(
        all(isinstance(item, dict) for item in packages),
        "Lake package entry is not an object",
    )
    package_map = {item.get("name"): item for item in packages}
    require(len(package_map) == len(packages), "Lake package names are not unique")
    require(set(package_map) == set(EXPECTED_PACKAGE_PINS), "Lake package set drifted")
    for name, (
        url,
        revision,
        input_revision,
        inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        package = package_map[name]
        require(
            (
                package.get("type"),
                package.get("url"),
                package.get("rev"),
                package.get("inputRev"),
                package.get("inherited"),
            )
            == ("git", url, revision, input_revision, inherited),
            f"Lake package pin drifted: {name}",
        )


def mask_lean_comments_and_strings(text: str, role: str) -> str:
    """Mask nested block comments, line comments, and strings, preserving lines."""

    masked = list(text)
    index = 0
    block_depth = 0
    in_string = False
    while index < len(text):
        if block_depth:
            if text.startswith("/-", index):
                masked[index : index + 2] = [" ", " "]
                block_depth += 1
                index += 2
            elif text.startswith("-/", index):
                masked[index : index + 2] = [" ", " "]
                block_depth -= 1
                index += 2
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
            continue
        if in_string:
            if text[index] == "\\":
                masked[index] = " "
                index += 1
                if index < len(text):
                    if text[index] != "\n":
                        masked[index] = " "
                    index += 1
            elif text[index] == '"':
                masked[index] = " "
                in_string = False
                index += 1
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
            continue
        if text.startswith("/-", index):
            masked[index : index + 2] = [" ", " "]
            block_depth = 1
            index += 2
        elif text.startswith("--", index):
            while index < len(text) and text[index] != "\n":
                masked[index] = " "
                index += 1
        elif text[index] == '"':
            masked[index] = " "
            in_string = True
            index += 1
        else:
            index += 1
    require(block_depth == 0, f"unterminated Lean block comment: {role}")
    require(not in_string, f"unterminated Lean string: {role}")
    return "".join(masked)


def check_transparency(sources: dict[str, Snapshot]) -> None:
    observed: dict[str, tuple[str, ...]] = {}
    for relative, snapshot in sources.items():
        text = snapshot.raw.decode("utf-8", errors="strict")
        masked = mask_lean_comments_and_strings(text, relative)
        lines = tuple(
            line.strip()
            for line in masked.splitlines()
            if line.strip().startswith(
                "set_option backward.isDefEq.respectTransparency"
            )
        )
        if lines:
            observed[relative] = lines
    require(
        observed == EXPECTED_OPTION_LINES, "Lean transparency scope inventory drifted"
    )
    require(
        sum(map(len, observed.values())) == 7,
        "Lean transparency scope count is not seven",
    )
    require(
        sum(line == OPTION for lines in observed.values() for line in lines) == 3,
        "Lean Fintype-derivation command-scope count is not three",
    )
    require(
        sum(line == OPTION + " by" for lines in observed.values() for line in lines)
        == 4,
        "Lean proof-term-local scope count is not four",
    )
    for relative, targets in EXPECTED_OPTION_TARGETS.items():
        text = sources[relative].raw.decode("utf-8", errors="strict")
        masked = mask_lean_comments_and_strings(text, relative)
        require(
            all(masked.count(target) == 1 for target in targets),
            f"Lean transparency setting moved away from reviewed target: {relative}",
        )


def check_derived_instance_evidence() -> None:
    snapshots = check_hashes(
        EXPECTED_DERIVED_EVIDENCE_HASHES, "derived-instance evidence"
    )
    receipt_path = (
        "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-2026-08-11.json"
    )
    receipt, _ = load_json(ROOT / receipt_path, "derived-instance receipt", pretty=True)
    require(receipt.get("status") == "passed", "derived-instance receipt did not pass")
    old = snapshots[
        "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.32.0.stdout"
    ].raw.decode("utf-8")
    new = snapshots[
        "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.33.0.stdout"
    ].raw.decode("utf-8")
    require(
        old.count("@[implicit_reducible]") == 6,
        "4.32 derived-instance attribute count drifted",
    )
    require(
        new.count("@[instance_reducible]") == 6,
        "4.33 derived-instance attribute count drifted",
    )
    require(
        "@[instance_reducible]" not in old and "@[implicit_reducible]" not in new,
        "derived-instance attributes were conflated",
    )
    require(
        old.replace("@[implicit_reducible]", "@[instance_reducible]") == new,
        "derived-instance normalized printed skeletons/synthesis differ",
    )
    comparison = receipt.get("comparison", {})
    require(
        comparison.get("normalized_printed_declaration_skeletons_and_synthesis_equal")
        is True
        and "normalized_types_bodies_and_synthesis_equal" not in comparison,
        "derived-instance receipt overclaims full body equality",
    )
    names = comparison.get("printed_and_synthesized_instances")
    require(
        isinstance(names, list) and len(names) == 6 and len(set(names)) == 6,
        "derived-instance name inventory drifted",
    )
    for name in names:
        require(
            isinstance(name, str) and new.count(name) >= 2,
            f"derived instance was not printed and synthesized: {name}",
        )


def check_active_resume_split() -> None:
    active = stable_read(
        ROOT / "audit/evidence/completion-active-resume.md",
        "current completion pointer",
    )
    require(
        active.sha256 == EXPECTED_ACTIVE_RESUME_SHA256,
        "current completion pointer digest drifted",
    )
    text = active.raw.decode("utf-8", errors="strict")
    require(
        "Lean 4.33.0 freeze" in text, "current completion pointer lost the 4.33 freeze"
    )
    require(
        "A newer Lean release alone is not a migration trigger" in text,
        "current completion pointer lost freeze semantics",
    )
    require(
        "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r10.json" in text
        and "first 11 August replay" in text
        and "first 12 August replay" in text
        and "finalized r2 replay" in text
        and "finalized r3 replay" in text
        and "finalized r4 replay" in text
        and "finalized r5 replay" in text
        and "finalized r6 replay" in text
        and "finalized r7 replay" in text
        and "finalized r8 replay" in text
        and "prior evidence, not current runner custody" in text,
        "current completion pointer lost current/prior replay separation",
    )
    require(
        "completion-active-resume-lean-4.32.2-route-correction-2026-08-08.historical.md"
        in text,
        "current completion pointer lost historical archive route",
    )
    require(
        "not a current instruction" in text,
        "current completion pointer conflates historical instructions",
    )


def check_current_replay_pointers() -> None:
    current_leaf = (
        "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r10.json"
    )
    bound_paths = {
        *EXPECTED_ACTIVE_CLAIM_HASHES,
        *EXPECTED_ACTIVE_RESUME_HASHES,
        *EXPECTED_OPERATIONAL_WIRING_HASHES,
    }
    require(
        set(EXPECTED_CURRENT_REPLAY_POINTER_PATHS) <= bound_paths,
        "current replay pointer inventory is not fully hash-bound",
    )
    require(
        set(EXPECTED_R10_SEQUENCE_EXPLANATION_PATHS)
        <= set(EXPECTED_CURRENT_REPLAY_POINTER_PATHS),
        "r10 sequence explanation inventory is not pointer-bound",
    )
    for relative in EXPECTED_CURRENT_REPLAY_POINTER_PATHS:
        text = stable_read(
            ROOT / relative, f"current replay pointer: {relative}"
        ).raw.decode("utf-8", errors="strict")
        normalized = " ".join(text.split())
        require(
            current_leaf in normalized
            and "finalized" in normalized
            and "r6" in normalized
            and "r7" in normalized
            and "r8" in normalized
            and "execution credit only" in normalized
            and "exists and validates" in normalized,
            f"current/prior r10 replay pointer semantics drifted: {relative}",
        )
    for relative in EXPECTED_R10_SEQUENCE_EXPLANATION_PATHS:
        text = stable_read(
            ROOT / relative, f"r10 sequence explanation: {relative}"
        ).raw.decode("utf-8", errors="strict")
        normalized = " ".join(text.split())
        require(
            "tenth receipt" in normalized
            and "versioned sequence" in normalized
            and "originated on 12 August" in normalized
            and "eleventh current-project replay receipt overall" in normalized
            and "11 August historical receipt is outside" in normalized
            and "calendar date" in normalized
            and "schema" in normalized
            and "theorem" in normalized
            and "review" in normalized
            and "independence" in normalized,
            f"r10 sequencing/non-conflation boundary drifted: {relative}",
        )


def check_absent_operational_paths() -> None:
    require(
        len(EXPECTED_ABSENT_OPERATIONAL_PATHS)
        == len(set(EXPECTED_ABSENT_OPERATIONAL_PATHS)),
        "absent operational path inventory contains duplicates",
    )
    for relative in EXPECTED_ABSENT_OPERATIONAL_PATHS:
        require(
            not os.path.lexists(ROOT / relative),
            f"retired operational path unexpectedly exists: {relative}",
        )


def check_current_evidence() -> None:
    check_hashes(EXPECTED_CURRENT_EVIDENCE_HASHES, "current 4.33 evidence")
    for relative in EXPECTED_CURRENT_EVIDENCE_HASHES:
        evidence, _ = load_json(
            ROOT / relative, f"current 4.33 evidence JSON: {relative}", pretty=False
        )
        require(
            evidence.get("status") == "passed",
            f"current evidence did not pass: {relative}",
        )
        if relative.endswith("manifest-regeneration-2026-08-11.json"):
            require(
                evidence.get("schema")
                == "pid-rs/lean-manifest-regeneration-observation/v1"
                and evidence.get("lean_toolchain") == "leanprover/lean4:v4.33.0"
                and evidence.get("lean_version")
                == (
                    "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
                    + EXPECTED_LEAN_IDENTITY["commit"]
                    + ", Release)"
                )
                and evidence.get("procedure")
                == {
                    "cache_hook_disabled": True,
                    "dependency_sources_materialized_at_exact_revisions": True,
                    "environment": "separate isolated private probe",
                    "lake_update_executed": True,
                    "manifest_generated_by_lake": True,
                    "raw_command_log_retained": False,
                },
                "manifest-regeneration procedure record drifted",
            )
            require(
                evidence.get("result")
                == {
                    "lake_manifest_sha256": EXPECTED_CONFIG_HASHES[
                        "audit/formal/lean/lake-manifest.json"
                    ],
                    "lakefile_sha256": EXPECTED_CONFIG_HASHES[
                        "audit/formal/lean/lakefile.toml"
                    ],
                    "package_count": len(EXPECTED_PACKAGE_PINS),
                    "toolchain_file_sha256": EXPECTED_CONFIG_HASHES[
                        "audit/formal/lean/lean-toolchain"
                    ],
                }
                and evidence.get("package_revisions")
                == {
                    name: revision
                    for name, (
                        _url,
                        revision,
                        _input,
                        _inherited,
                    ) in EXPECTED_PACKAGE_PINS.items()
                },
                "manifest-regeneration result/pin inventory drifted",
            )
        elif relative.endswith("factorization-lean-4.33.0.json"):
            require(
                evidence.get("lean_toolchain") == "leanprover/lean4:v4.33.0",
                f"current evidence toolchain drifted: {relative}",
            )
            require(
                evidence.get("lean_executable_identity")
                == {
                    key: EXPECTED_LEAN_IDENTITY[key]
                    for key in ("build", "commit", "version")
                },
                f"current evidence Lean identity drifted: {relative}",
            )
        elif relative.endswith("factorization-mutations-4.33.0.json"):
            require(
                evidence.get("lean_version_portable_identity")
                == {
                    key: EXPECTED_LEAN_IDENTITY[key]
                    for key in ("build", "commit", "version")
                },
                f"current mutation evidence Lean identity drifted: {relative}",
            )
        else:
            require(
                evidence.get("lean_toolchain") == "leanprover/lean4:v4.33.0",
                f"current evidence toolchain drifted: {relative}",
            )
            expected_line = (
                "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
                + EXPECTED_LEAN_IDENTITY["commit"]
                + ", Release)"
            )
            require(
                evidence.get("lean_version") == expected_line,
                f"current evidence exact Lean identity line drifted: {relative}",
            )


def check_prior_replay_preservation() -> None:
    check_hashes(PRESERVED_PRIOR_REPLAY_HASHES, "preserved prior 4.33 replay")
    require(
        tuple(PRESERVED_PRIOR_REPLAY_SCHEMAS) == tuple(PRESERVED_PRIOR_REPLAY_HASHES),
        "preserved prior replay schema inventory drifted",
    )
    for relative, expected_schema in PRESERVED_PRIOR_REPLAY_SCHEMAS.items():
        prior, _snapshot = load_json(
            ROOT / relative, f"preserved prior replay JSON: {relative}", pretty=True
        )
        require(
            isinstance(prior, dict) and prior.get("schema") == expected_schema,
            f"preserved prior replay lost its exact schema identity: {relative}",
        )


def check_no_self_digest_cycle() -> None:
    digest_inventories = {
        "active claim authority": EXPECTED_ACTIVE_CLAIM_HASHES,
        "active configuration": EXPECTED_CONFIG_HASHES,
        "active/historical completion split": EXPECTED_ACTIVE_RESUME_HASHES,
        "active Lean checker": EXPECTED_CHECKER_HASHES,
        "current 4.33 evidence": EXPECTED_CURRENT_EVIDENCE_HASHES,
        "derived-instance evidence": EXPECTED_DERIVED_EVIDENCE_HASHES,
        "operational wiring": EXPECTED_OPERATIONAL_WIRING_HASHES,
        "preserved historical 4.32 evidence": PRESERVED_HISTORICAL_HASHES,
        "preserved prior 4.33 replay": PRESERVED_PRIOR_REPLAY_HASHES,
        "active Lean source": EXPECTED_SOURCE_HASHES,
    }
    for role, inventory in digest_inventories.items():
        require(
            RECEIPT_RELATIVE not in inventory,
            f"current replay receipt entered its own digest inventory: {role}",
        )
    require(
        not (
            set(EXPECTED_OPERATIONAL_WIRING_HASHES) & set(PRESERVED_PRIOR_REPLAY_HASHES)
        ),
        "operational wiring overlaps preserved prior replay evidence",
    )


def check_replay_receipt() -> None:
    receipt, _snapshot = load_json(RECEIPT, "Lean 4.33 replay receipt", pretty=True)
    require(isinstance(receipt, dict), "replay receipt root is not an object")
    require_exact_keys(
        receipt,
        {
            "active_claim_authority_sha256",
            "active_configuration",
            "active_resume_sha256",
            "checker_sha256",
            "command_records",
            "compatibility_scope",
            "current_evidence_sha256",
            "custody_gate_sha256",
            "dependency_checkout_preflight",
            "derived_instance_evidence_sha256",
            "environment_policy",
            "execution_environment",
            "execution_window",
            "historical_preservation_sha256",
            "lake_identity",
            "lake_version_line",
            "lake_version_stderr",
            "lean_identity",
            "lean_version_line",
            "lean_version_stderr",
            "official_archive",
            "official_archive_observation",
            "operational_wiring_sha256",
            "package_pins",
            "prior_replay_preservation_sha256",
            "prior_replay_schema",
            "provider_observations",
            "python_optimization_parity",
            "replay_custody_gate_sha256",
            "schema",
            "scope_boundary",
            "source_sha256",
            "status",
            "verification",
        },
        "Lean 4.33 replay receipt",
    )
    require(
        receipt.get("schema") == "pid-rs/lean-current-project-replay/v2",
        "replay receipt schema drifted",
    )
    require(receipt.get("status") == "passed", "replay receipt status is not passed")
    require(
        receipt.get("official_archive") == EXPECTED_ARCHIVE,
        "official archive observation drifted",
    )
    archive_observation = receipt.get("official_archive_observation")
    require(
        isinstance(archive_observation, dict),
        "local archive observation is malformed",
    )
    require_exact_keys(
        archive_observation,
        {
            "end_utc",
            "path_observed_absolute",
            "sha256",
            "single_link_regular_file",
            "size_bytes",
            "stable_descriptor_identity",
            "start_utc",
        },
        "local archive observation",
    )
    archive_path = archive_observation.get("path_observed_absolute")
    archive_start = parse_utc_timestamp(
        archive_observation.get("start_utc"), "local archive observation start"
    )
    archive_end = parse_utc_timestamp(
        archive_observation.get("end_utc"), "local archive observation end"
    )
    require(
        archive_start <= archive_end
        and isinstance(archive_path, str)
        and os.path.isabs(archive_path)
        and os.path.normpath(archive_path) == archive_path
        and os.path.basename(archive_path) == EXPECTED_ARCHIVE["file_name"]
        and archive_observation.get("sha256") == EXPECTED_ARCHIVE["sha256"]
        and archive_observation.get("size_bytes") == EXPECTED_ARCHIVE["size_bytes"]
        and archive_observation.get("single_link_regular_file") is True
        and archive_observation.get("stable_descriptor_identity") is True,
        "local archive bytes/identity drifted",
    )
    require(
        archive_path == EXPECTED_LOCAL_REPLAY_ROUTES["archive"],
        "replay host-local archive route drifted",
    )
    require(
        receipt.get("provider_observations") == EXPECTED_PROVIDER_OBSERVATIONS,
        "upstream provider observation drifted",
    )
    require(
        receipt.get("lean_identity") == EXPECTED_LEAN_IDENTITY,
        "replay Lean identity drifted",
    )
    require(
        receipt.get("lake_identity") == EXPECTED_LAKE_IDENTITY,
        "replay Lake identity drifted",
    )
    require(
        receipt.get("lean_version_line")
        == "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + EXPECTED_LEAN_IDENTITY["commit"]
        + ", Release)\n",
        "replay exact Lean version line drifted",
    )
    require(
        receipt.get("lake_version_line")
        == "Lake version 5.0.0-src+d8b1897 (Lean version 4.33.0)\n",
        "replay exact Lake version line drifted",
    )
    require(
        receipt.get("lean_version_stderr") == {"bytes": 0, "sha256": EMPTY_SHA256}
        and receipt.get("lake_version_stderr") == {"bytes": 0, "sha256": EMPTY_SHA256},
        "replay version command emitted stderr",
    )
    require(
        receipt.get("active_configuration") == EXPECTED_CONFIG_HASHES,
        "replay configuration hashes drifted",
    )
    expected_packages = {
        name: {
            "inherited": inherited,
            "input_revision": input_revision,
            "revision": revision,
            "url": url,
        }
        for name, (
            url,
            revision,
            input_revision,
            inherited,
        ) in EXPECTED_PACKAGE_PINS.items()
    }
    require(
        receipt.get("package_pins") == expected_packages, "replay package pins drifted"
    )
    require(
        receipt.get("source_sha256") == EXPECTED_SOURCE_HASHES,
        "replay source inventory drifted",
    )
    require(
        receipt.get("checker_sha256") == EXPECTED_CHECKER_HASHES,
        "replay checker inventory drifted",
    )
    require(
        receipt.get("current_evidence_sha256") == EXPECTED_CURRENT_EVIDENCE_HASHES,
        "replay current evidence inventory drifted",
    )
    require(
        receipt.get("historical_preservation_sha256") == PRESERVED_HISTORICAL_HASHES,
        "replay historical-preservation inventory drifted",
    )
    require(
        receipt.get("prior_replay_preservation_sha256")
        == PRESERVED_PRIOR_REPLAY_HASHES,
        "prior replay preservation inventory drifted",
    )
    require(
        receipt.get("prior_replay_schema") == PRESERVED_PRIOR_REPLAY_SCHEMAS,
        "prior replay schema inventory drifted",
    )
    require(
        receipt.get("derived_instance_evidence_sha256")
        == EXPECTED_DERIVED_EVIDENCE_HASHES,
        "replay derived-instance inventory drifted",
    )
    require(
        receipt.get("active_resume_sha256") == EXPECTED_ACTIVE_RESUME_HASHES,
        "replay active/historical completion split drifted",
    )
    require(
        receipt.get("active_claim_authority_sha256") == EXPECTED_ACTIVE_CLAIM_HASHES,
        "replay active claim authority drifted",
    )
    require(
        receipt.get("operational_wiring_sha256") == EXPECTED_OPERATIONAL_WIRING_HASHES,
        "replay operational wiring inventory drifted",
    )
    custody = receipt.get("custody_gate_sha256")
    require(isinstance(custody, dict), "replay custody-gate inventory is malformed")
    require(
        tuple(custody) == EXPECTED_CUSTODY_GATE_PATHS,
        "replay custody-gate exact path set drifted",
    )
    for relative, digest in custody.items():
        require(
            isinstance(digest, str) and SHA256_TEXT.fullmatch(digest) is not None,
            f"replay custody-gate digest is malformed: {relative}",
        )
        require(
            stable_read(ROOT / relative, f"custody gate: {relative}").sha256 == digest,
            f"replay custody-gate digest mismatch: {relative}",
        )
    replay_custody = receipt.get("replay_custody_gate_sha256")
    require(
        isinstance(replay_custody, dict),
        "replay-time custody-gate inventory is malformed",
    )
    require(
        tuple(replay_custody) == EXPECTED_CUSTODY_GATE_PATHS,
        "replay-time custody-gate exact path set drifted",
    )
    for relative, digest in replay_custody.items():
        require(
            isinstance(digest, str) and SHA256_TEXT.fullmatch(digest) is not None,
            f"replay-time custody-gate digest is malformed: {relative}",
        )
    self_test_path, checker_path = EXPECTED_CUSTODY_GATE_PATHS
    require(
        replay_custody[self_test_path] == custody[self_test_path],
        "replay-time and final self-test custody diverged",
    )
    checker_source = stable_read(
        ROOT / checker_path, "final Lean freeze checker reconstruction"
    ).raw.decode("utf-8", errors="strict")
    final_projection_line = (
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "
        f'"{EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256}"'
    )
    placeholder_projection_line = (
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = " + '"0"' + " * 64"
    )
    require(
        checker_source.count(final_projection_line) == 1
        and placeholder_projection_line not in checker_source,
        "final replay-projection literal is not uniquely reconstructable",
    )
    replay_checker_source = checker_source.replace(
        final_projection_line, placeholder_projection_line, 1
    ).encode("utf-8")
    require(
        hashlib.sha256(replay_checker_source).hexdigest()
        == replay_custody[checker_path],
        "replay checker pre-pin reconstruction drifted",
    )
    verification = receipt.get("verification")
    require(isinstance(verification, dict), "replay verification summary is malformed")
    require_exact_keys(
        verification,
        {
            "clean_build",
            "bound_static_surface",
            "direct_lean_t0",
            "forbidden_placeholder_hits",
            "imported_modules",
            "leanchecker",
            "named_source_theorems",
            "permitted_axioms",
            "python_checker_pairs",
            "source_written_declarations",
            "theorem_axiom_audit",
        },
        "replay verification summary",
    )
    require(
        verification.get("clean_build")
        == {
            "dependency_cache_reused": True,
            "project_oleans_reused": False,
            "status": "passed",
            "stdout_exact": EXPECTED_CLEAN_BUILD_STDOUT,
            "warnings": 0,
            "warnings_fail_build": True,
        },
        "clean build replay drifted",
    )
    require(
        verification.get("bound_static_surface")
        == {
            "atomic_snapshot_claimed": False,
            "custody_gate_endpoint_identity_equal": True,
            "custody_gate_files": len(EXPECTED_CUSTODY_GATE_PATHS),
            "post_commands": "passed",
            "pre_commands": "passed",
        },
        "bounded static-surface endpoint replay drifted",
    )
    require(
        verification.get("direct_lean_t0")
        == {
            "count": 11,
            "stderr_empty": True,
            "stdout_empty": True,
            "status": "passed",
        },
        "direct Lean replay drifted",
    )
    require(
        verification.get("leanchecker")
        == {"stderr_empty": True, "stdout_empty": True, "status": "passed"},
        "LeanChecker replay drifted",
    )
    require(
        verification.get("theorem_axiom_audit")
        == {
            "named_theorems": 246,
            "stderr_empty": True,
            "stdout_empty": True,
            "status": "passed",
        },
        "theorem axiom replay drifted",
    )
    require(
        verification.get("source_written_declarations") == 339,
        "source-written declaration count drifted",
    )
    require(
        verification.get("named_source_theorems") == 246, "source theorem count drifted"
    )
    require(verification.get("imported_modules") == 8, "imported module count drifted")
    require(
        verification.get("permitted_axioms")
        == ["Classical.choice", "Quot.sound", "propext"],
        "permitted axiom basis drifted",
    )
    require(
        verification.get("forbidden_placeholder_hits") == 0,
        "placeholder scan did not remain empty",
    )
    require(
        verification.get("python_checker_pairs") == len(PYTHON_COMMAND_PAIRS),
        "Python checker-pair inventory drifted",
    )
    check_command_records(receipt)
    compatibility = receipt.get("compatibility_scope")
    require(
        compatibility
        == {
            "broad_or_file_global_occurrences": 0,
            "command_scoped_fintype_derivation_occurrences": 3,
            "option": OPTION,
            "proof_term_local_occurrences": 4,
            "total_occurrences": 7,
        },
        "replay transparency compatibility scope drifted",
    )
    boundary = receipt.get("scope_boundary")
    require(
        isinstance(boundary, list) and len(boundary) == 11,
        "replay scope boundary drifted",
    )
    joined = " ".join(item for item in boundary if isinstance(item, str)).lower()
    for nonclaim in (
        "executed-tree-to-archive byte provenance",
        "publisher authentication",
        "reproducible build",
        "kernel soundness",
        "semantic equivalence",
        "rust or binary64",
        "generated helper proof bodies",
        "atomic snapshot",
        "does not authenticate its pinned host-local executables",
        "do not prove the operating system executed those exact bytes atomically",
        "do not bind dynamic-loader inputs",
        "not a sandbox or containment guarantee",
        "escaped descendants",
        "process-group identifier reuse",
    ):
        require(nonclaim in joined, f"replay nonclaim disappeared: {nonclaim}")
    require(
        replay_receipt_projection_sha256(receipt)
        == EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256,
        "replay receipt reviewed projection drifted",
    )


def check_static_without_receipt() -> None:
    check_no_self_digest_cycle()
    require(
        not EXPECTED_PENDING_OPERATIONAL_PATHS
        and PENDING_OPERATIONAL_SHA256
        not in EXPECTED_OPERATIONAL_WIRING_HASHES.values(),
        "operational wiring digest placeholders remain: "
        + ", ".join(EXPECTED_PENDING_OPERATIONAL_PATHS),
    )
    require(
        not EXPECTED_PENDING_ACTIVE_CLAIM_PATHS
        and PENDING_OPERATIONAL_SHA256 not in EXPECTED_ACTIVE_CLAIM_HASHES.values(),
        "active claim digest placeholders remain: "
        + ", ".join(EXPECTED_PENDING_ACTIVE_CLAIM_PATHS),
    )
    require(
        not EXPECTED_PENDING_ACTIVE_RESUME_PATHS
        and "0" * 64 not in EXPECTED_ACTIVE_RESUME_HASHES.values()
        and EXPECTED_ACTIVE_RESUME_SHA256 != "0" * 64,
        "active resume digest placeholders remain: "
        + ", ".join(EXPECTED_PENDING_ACTIVE_RESUME_PATHS),
    )
    check_policy()
    config = check_hashes(EXPECTED_CONFIG_HASHES, "active Lean configuration")
    require(
        config["audit/formal/lean/lean-toolchain"].raw == b"leanprover/lean4:v4.33.0\n",
        "active lean-toolchain contents drifted",
    )
    check_manifest()
    sources = check_hashes(EXPECTED_SOURCE_HASHES, "active Lean source")
    check_transparency(sources)
    check_hashes(EXPECTED_CHECKER_HASHES, "active Lean checker")
    check_current_evidence()
    check_derived_instance_evidence()
    check_hashes(EXPECTED_ACTIVE_CLAIM_HASHES, "active claim authority")
    check_hashes(EXPECTED_OPERATIONAL_WIRING_HASHES, "operational wiring")
    check_absent_operational_paths()
    check_hashes(PRESERVED_HISTORICAL_HASHES, "preserved historical 4.32 evidence")
    check_prior_replay_preservation()
    check_hashes(EXPECTED_ACTIVE_RESUME_HASHES, "active/historical completion split")
    check_active_resume_split()
    check_current_replay_pointers()


def check_all() -> None:
    check_static_without_receipt()
    check_replay_receipt()


def main() -> int:
    try:
        check_all()
    except (FreezeError, OSError) as error:
        print(f"Lean toolchain freeze check failed: {error}", file=sys.stderr)
        return 1
    print(
        "OK: Lean 4.33.0 remains frozen to the exact release/commit, nine-package "
        "closure, 11 source files, 3 Fintype-derivation command scopes plus 4 proof-term "
        "scopes, current replay evidence, six derived-instance printed-skeleton "
        "comparisons, and "
        f"{len(PRESERVED_HISTORICAL_HASHES)} byte-preserved historical 4.32 artifacts, "
        f"plus {len(PRESERVED_PRIOR_REPLAY_HASHES)} byte-preserved prior 4.33 replay"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
