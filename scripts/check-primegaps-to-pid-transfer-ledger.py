#!/usr/bin/env python3
"""Validate the bounded PrimeGaps-to-PID semantic-transfer ledger.

This checker binds one reviewed PrimeGaps commit, the canonical repository 20-lens registry,
source-anchor syntax, exact ledger registries, and the current and protected-preimage identities of
the 13 proposed SxPID3 packet files.  External artifacts are hash-only observations: validating
their records does not recover their bytes or establish source truth, authenticity, independent
review, scientific correctness, or acceptance of a PID claim.

The checked-in schema declares JSON Schema Draft 2020-12.  ``json_schema_subset`` evaluates every
assertion keyword used by that pinned schema and fails on unsupported keywords.  It is deliberately
not presented as a general Draft 2020-12 implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import types
from typing import Any, Final
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "audit/evidence/primegaps-to-pid-transfer-ledger-v1.json"
DEFAULT_SCHEMA = ROOT / "audit/schemas/primegaps-to-pid-transfer-ledger-v1.schema.json"
DEFAULT_WORKFLOW = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"

SCHEMA_DIALECT: Final[str] = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID: Final[str] = "urn:pid-rs:schema:primegaps-to-pid-transfer-ledger:v1"
REVIEWED_COMMIT: Final[str] = "1faa7b14e82ddebc2772dfb9153922f01b106477"
JSON_SCHEMA_SUBSET_SHA256: Final[str] = (
    "067e6d6b10d33f5b9c1bab6bc621735267a06f2461d6c0da3c8342ac8bd391a6"
)
SCHEMA_SHA256: Final[str] = (
    "842701050fa82edf82691dac2fd5eae7c93806fed7f9c128d1a92255ba1dae47"
)
LEDGER_SHA256: Final[str] = (
    "18763feaa707ea797d409de7df7e152e77fc778d4bd631c2ca9734790a4c7bda"
)
ANCHOR_REGISTRY_SHA256: Final[str] = (
    "78bccc50109c2778d7db5cc8ebf03f49fa1224e5072f347699d517a15956e590"
)
COUNCIL_REGISTRY_SHA256: Final[str] = (
    "642353de99fae38b469ee5e302eaba8cdca35102601e24a52c774413743ea3f0"
)

SOURCE_MANIFEST_BOUNDARY: Final[str] = (
    "Repository-path entries are byte-checked local recovery inputs. Every external entry is "
    "hash-only: this ledger records its observed digest, size, locator, and bounded status but "
    "does not retain the bytes, guarantee retrieval, or establish durable custody."
)

CANONICAL_LENSES: Final[tuple[tuple[int, str], ...]] = (
    (1, "Estimand"),
    (2, "Types"),
    (3, "Quantifiers"),
    (4, "Mappings"),
    (5, "Support/reference measure"),
    (6, "Lattice/source count"),
    (7, "Units/gauge"),
    (8, "Population/empirical"),
    (9, "Sampling"),
    (10, "Selection/UQ"),
    (11, "Formal correspondence"),
    (12, "Kernel/axioms/toolchain"),
    (13, "Route dependency diversity"),
    (14, "Numerical/binary64"),
    (15, "Compiled/wrapper parity"),
    (16, "Counterexample/mutation"),
    (17, "Custody/threat/refusal"),
    (18, "Citations/novelty"),
    (19, "Ecosystem/authority"),
    (20, "Resource/platform/release"),
)

TRANSFER_IDS: Final[tuple[str, ...]] = (
    "theory-certificate-composite-lanes",
    "untrusted-discovery-small-checker",
    "finite-semantic-bridge",
    "explicit-premise-types",
    "challenge-comparator",
    "proof-document-dag",
    "sparse-dag-and-shards",
    "content-addressed-durable-promotion",
    "autoresearch-promotion-boundary",
    "prime-gap-mathematics",
    "exact-certificate-to-continuous-validity",
    "cached-ci-or-self-review-as-sufficient",
)
DESIGN_DECISION_IDS: Final[tuple[str, ...]] = (
    "typed-semantic-mass-dag",
    "separate-reduced-rational-plan",
    "factor-dag-revision-boundary",
    "content-addressed-sharded-replay",
    "custom-packed-trees",
    "direct-prime-gap-mathematics-transfer",
)
COUNCIL_IDS: Final[tuple[str, ...]] = (
    "integrator",
    "source-auditor",
    "transfer-designer",
    "transfer-adversary",
)
EXTERNAL_SOURCE_IDS: Final[tuple[str, ...]] = (
    "primegaps-git-tree",
    "primegaps-interactive-paper",
    "primegaps-blueprint-pdf",
    "primegaps-blueprint-layout-text",
    "primegaps-certificate-json",
    "primegaps-ci-job-log",
)
LOCAL_SOURCE_IDS: Final[tuple[str, ...]] = (
    "sxpid3-packet-bindings",
    "sxpid3-packet-claim-v1",
    "sxpid3-packet-conventions",
    "sxpid3-packet-decision",
    "sxpid3-packet-evidence-matrix",
    "sxpid3-packet-failure-count-weighting",
    "sxpid3-packet-failure-event-connective-target",
    "sxpid3-packet-failure-exact-zero-product-one",
    "sxpid3-packet-failure-mask-array-order",
    "sxpid3-packet-failure-negative-net-atom",
    "sxpid3-packet-obligations",
    "sxpid3-packet-revision-index",
    "sxpid3-packet-routes",
)
SOURCE_IDS: Final[tuple[str, ...]] = EXTERNAL_SOURCE_IDS + LOCAL_SOURCE_IDS

PROPOSED_REVISION: Final[str] = (
    "protected-worktree preimage bound by source_sha256/source_size_bytes; repository bytes "
    "received formatting-only Markdown normalization before integration; proposed packet, not "
    "accepted evidence; this manifest does not itself prove semantic equivalence"
)
NEGATIVE_REVISION: Final[str] = (
    "protected-worktree preimage bound by source_sha256/source_size_bytes; repository bytes "
    "received formatting-only Markdown normalization before integration; retained negative "
    "evidence; this manifest does not itself prove semantic equivalence"
)
OBLIGATIONS_REVISION: Final[str] = (
    "protected-worktree preimage bound by source_sha256/source_size_bytes; repository bytes "
    "received formatting-only Markdown normalization before integration; all Programs A--E "
    "remain open; this manifest does not itself prove semantic equivalence"
)
ROUTES_REVISION: Final[str] = (
    "protected-worktree preimage bound by source_sha256/source_size_bytes; repository bytes "
    "received formatting-only Markdown normalization before integration; proposed routes, not "
    "accepted evidence; this manifest does not itself prove semantic equivalence"
)

# id, repository path, current sha256, current size, protected preimage sha256, preimage size,
# revision text.  Preimage fields bind the original protected-worktree bytes; this checker has no
# dependency on that worktree and does not claim that the manifest alone proves semantic equality.
LOCAL_SOURCE_RECORDS: Final[
    tuple[tuple[str, str, str, int, str, int, str], ...]
] = (
    (
        "sxpid3-packet-bindings",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md",
        "bffd5f422b109335070011fd315034d4d4aa7bed54032a4c9426d43dd2a6507b",
        10446,
        "95f56e43223e7d98ed768ef14c1d12054810a0776c733dbc891a302e241f9d7a",
        10466,
        PROPOSED_REVISION,
    ),
    (
        "sxpid3-packet-claim-v1",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md",
        "3c0ce09a17d1925a01f54d35733c6f01effbdd6ae3d081d194a7fadf6e04b31b",
        10608,
        "197318e901f08184356f97bcb272918175dae189da4ffb7ffe69312950f9df64",
        10626,
        PROPOSED_REVISION,
    ),
    (
        "sxpid3-packet-conventions",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md",
        "2d14bea9d6f0a2d07493ddaf7d89a130f4ad62680319cb9efba465590c2250c7",
        11831,
        "d97975ca5ec377c5a20b4f7754ec4ac5b13214efde5a4c071a65359f48ec9b2c",
        11951,
        PROPOSED_REVISION,
    ),
    (
        "sxpid3-packet-decision",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/decision.md",
        "122c17693ada4dea23e1757f99d9aec9b0970317435b16de944668ebb751211b",
        6532,
        "6718d0cb98309e28638b30a64146b0d51705b33553b4485e14e70c979ae9c37b",
        6538,
        PROPOSED_REVISION,
    ),
    (
        "sxpid3-packet-evidence-matrix",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-matrix.md",
        "ee3db98b1eca36616f0eb28f97a7c478a6d49b56bbd97c769d14b292f0fc4c4a",
        8436,
        "aa9f7df9161bc0d582859c0425e033aceb24358addf994f77391d6868eb35cde",
        8468,
        PROPOSED_REVISION,
    ),
    (
        "sxpid3-packet-failure-count-weighting",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/count-weighting.md",
        "4871c0c4b3d456ea6839ef2eb0353813f972bbeaee3b863b69e11c24a26a4d50",
        1694,
        "64adcf0701cde2a76c4e3935d0ea709015cd4031af2fa080d1bc7c327aba9488",
        1708,
        NEGATIVE_REVISION,
    ),
    (
        "sxpid3-packet-failure-event-connective-target",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/event-connective-and-target-mutations.md",
        "b16b5210f98b5f5f148faa27a4cb4d27ed235d9fec30624214cf6bf6ebf339ad",
        2478,
        "0d4e71d5a423a57d9d9dccef03de17028cf49bdc06eb52d01acc37a6004eda75",
        2512,
        NEGATIVE_REVISION,
    ),
    (
        "sxpid3-packet-failure-exact-zero-product-one",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/exact-zero-and-product-one.md",
        "99fbc4535501ee0adc2e3624e8c42763563a4de15acf95d98ff1a65ac1267161",
        2514,
        "b97dafe456486612d96bb08208869b808e727d7c386a123fb14e281a54b0968a",
        2522,
        NEGATIVE_REVISION,
    ),
    (
        "sxpid3-packet-failure-mask-array-order",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/mask-and-array-order.md",
        "d198e7c4a29a5363d6e182c6dee3c3ff1ed63b4d383c3224b33fd312830a24e8",
        1501,
        "9a6087d2f297d327ce7f5e16e1a36092e27d5808cf5e7beb4748e78eec665b19",
        1517,
        NEGATIVE_REVISION,
    ),
    (
        "sxpid3-packet-failure-negative-net-atom",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/negative-net-atom.md",
        "59fc673aa47659d578269ed80edf895a25ebc45548351fe9a4ec9ce3c18e57bf",
        1553,
        "703b9ee1ee2c44c69f1751be3eca85adfc361327da4bae44c217a0d5e1c98611",
        1559,
        NEGATIVE_REVISION,
    ),
    (
        "sxpid3-packet-obligations",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/obligations.md",
        "054bfc40bc18bdbc86918b1b47f169aa69b7e6343d5faa85e4940933583269fe",
        13533,
        "70c738567e65bc4be91501397528bcf4d89d5ceb2fd3b5243298a77f0f6e0523",
        13549,
        OBLIGATIONS_REVISION,
    ),
    (
        "sxpid3-packet-revision-index",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md",
        "cf33f912f12793739b3e7a4a4b41b974709ead47df59fcfca37f8de443d4719e",
        1392,
        "cf33f912f12793739b3e7a4a4b41b974709ead47df59fcfca37f8de443d4719e",
        1392,
        PROPOSED_REVISION,
    ),
    (
        "sxpid3-packet-routes",
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/routes.md",
        "609b737d494da09cc1e47410c1c318661a46fd417549e98d21033eeaedbf967b",
        12609,
        "4e2a71eda6fd86f85e53dc04b394ef4e8a24f158293e3a905cba02a9c61fc551",
        12619,
        ROUTES_REVISION,
    ),
)

EXTERNAL_SOURCE_RECORDS: Final[dict[str, dict[str, object]]] = {
    "primegaps-git-tree": {
        "artifact_id": "primegaps-git-tree",
        "durability": "hash-only-external",
        "kind": "git-tree",
        "locator": (
            "https://github.com/AxiomMath/PrimeGapsLib/tree/"
            "1faa7b14e82ddebc2772dfb9153922f01b106477"
        ),
        "revision": (
            "commit 1faa7b14e82ddebc2772dfb9153922f01b106477; tree "
            "611f4b1caccb7850996cf425aefb1a6c42ed629f; sha256 over raw root-tree object "
            "bytes; bytes are not retained by this ledger"
        ),
        "sha256": "898fbafacfba703605273c62814e2161be4fb9c67c632103e417280e92e8ddab",
        "size_bytes": 970,
        "status": "reviewed-git-object",
    },
    "primegaps-interactive-paper": {
        "artifact_id": "primegaps-interactive-paper",
        "durability": "hash-only-external",
        "kind": "html",
        "locator": "https://primegaps.axiommath.ai/paper/",
        "revision": "retrieved 2026-08-19; bytes are not retained by this ledger",
        "sha256": "8ab349b59a897780ee7b023ec9b350442fc77b36aec84873019bff2612a97c90",
        "size_bytes": 10793548,
        "status": "reviewed-exact-bytes",
    },
    "primegaps-blueprint-pdf": {
        "artifact_id": "primegaps-blueprint-pdf",
        "durability": "hash-only-external",
        "kind": "pdf",
        "locator": "https://primegaps.axiommath.ai/blueprint.pdf",
        "revision": (
            "retrieved 2026-08-19; 132 A4 pages; bytes are not retained by this ledger"
        ),
        "sha256": "c93efd077ff4236926379d9879cc82e124a12f4eecc1c43a685054b6ba866117",
        "size_bytes": 1153093,
        "status": "reviewed-exact-bytes",
    },
    "primegaps-blueprint-layout-text": {
        "artifact_id": "primegaps-blueprint-layout-text",
        "durability": "hash-only-external",
        "kind": "text",
        "locator": "urn:pid-rs:derived:primegaps-blueprint-layout-text",
        "revision": (
            "derived locally with pdftotext -layout from the reviewed blueprint PDF on "
            "2026-08-19; bytes are not retained by this ledger"
        ),
        "sha256": "1ea1f0fb79561a91edba050bc767325882aee83c51dd1ba169e2e0a5e25bd8cf",
        "size_bytes": 495392,
        "status": "reviewed-exact-bytes",
    },
    "primegaps-certificate-json": {
        "artifact_id": "primegaps-certificate-json",
        "durability": "hash-only-external",
        "kind": "json",
        "locator": (
            "https://github.com/AxiomMath/PrimeGapsLib/blob/"
            "1faa7b14e82ddebc2772dfb9153922f01b106477/"
            "PrimeGapsCert/Gap246/k50e25d25n1295.json"
        ),
        "revision": (
            "1,295 source rows at exact repository commit; bytes are not retained by this ledger"
        ),
        "sha256": "99808e1d95204c5bbc0cde845641cfdbb41ea950fa7fa9858df8bd093111787a",
        "size_bytes": 55303,
        "status": "reviewed-exact-bytes",
    },
    "primegaps-ci-job-log": {
        "artifact_id": "primegaps-ci-job-log",
        "durability": "hash-only-external",
        "kind": "workflow-log",
        "locator": (
            "https://github.com/AxiomMath/PrimeGapsLib/actions/runs/32171224732/"
            "job/95822587109"
        ),
        "revision": (
            "provider log retrieved 2026-08-19; bytes are not retained by this ledger"
        ),
        "sha256": "408c6b2193069268c2250227e326d0aabdd233244b1b6de804c9c98d4750c2b5",
        "size_bytes": 33294,
        "status": "provider-observation",
    },
}

AUTORESEARCH_PRESERVED: Final[tuple[str, ...]] = (
    "Candidate generation may be heuristic and remains outside the trusted conclusion.",
    "The promoted finite mathematical conclusion depends on a separately checked exact witness, "
    "not on search frequency, score, or the numerical discovery trajectory.",
)
AUTORESEARCH_CHANGED: Final[tuple[str, ...]] = (
    "PrimeGaps needs some valid existential coefficient witness, whereas a PID report is a "
    "deterministic function of exact submitted count bytes and must reject parser or identity "
    "drift.",
    "PID autoresearch searches semantic counterexamples, exact count tables, interval stress "
    "cases, and implementation layouts rather than sieve coefficients.",
    "PID empirical estimator or implementation selection may require holdout, "
    "sequential-inference, or other selection-aware controls that are not supplied by an exact "
    "existential witness theorem.",
    "Pre-registration, candidate-inaccessible judging, complete exposure logging, and durable "
    "retention of rejected or selection-bearing candidates are pid-rs promotion controls; the "
    "reviewed PrimeGaps materials do not establish them.",
)
AUTORESEARCH_SOURCE_SEMANTICS: Final[str] = (
    "A numerical candidate can be found by heuristic search because the final theorem depends on "
    "an exact checked witness rather than the discovery trajectory."
)

WORKFLOW_SECTION_START: Final[str] = "### 6. Run the required 20-lens adversarial audit\n"
WORKFLOW_SECTION_END: Final[str] = (
    "For every strict sign, ranking, or separation claim, bind an exact or enclosed positive margin"
)
WORKFLOW_LENS_RE = re.compile(r"^\| ([0-9]+)\. ([^|]+?) \|", re.MULTILINE)
GITHUB_ANCHOR_RE = re.compile(
    r"^https://github\.com/AxiomMath/PrimeGapsLib/blob/([^/]+)/"
    r"([^#]+)#L([0-9]+)-L([0-9]+)$"
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )


def canonical_json_ascii(value: object) -> str:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_ascii(value).encode("ascii")).hexdigest()


def load_schema_validator() -> tuple[type[ValueError], Any]:
    """Compile the exact single-link validator source without a sys.path import."""

    path = ROOT / "scripts/json_schema_subset.py"
    before = os.lstat(path)
    require(
        stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
        "SCHEMA.validator_file_type",
    )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        source = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            source.extend(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    require(
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(source) == before.st_size,
        "SCHEMA.validator_unstable_read",
    )
    require(
        hashlib.sha256(source).hexdigest() == JSON_SCHEMA_SUBSET_SHA256,
        "SCHEMA.validator_sha256",
    )
    module = types.ModuleType("primegaps_transfer_json_schema_subset")
    module.__file__ = str(path)
    code = compile(
        bytes(source),
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module.SchemaValidationError, module.validate


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def read_canonical_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    require(raw != b"", f"{label}.empty")
    require(not raw.startswith(b"\xef\xbb\xbf"), f"{label}.bom")
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError) as error:
        message = str(error)
        if "duplicate key" in message:
            raise RuntimeError(f"{label}.duplicate_key") from error
        raise RuntimeError(f"{label}.json") from error
    require(isinstance(value, dict), f"{label}.root_type")
    require(raw == canonical_json(value).encode("utf-8"), f"{label}.canonical_json")
    return value, raw


def registry_ids(
    entries: object, field: str, label: str, expected: tuple[str, ...]
) -> tuple[str, ...]:
    require(isinstance(entries, list), f"ID.{label}.container")
    values = tuple(entry[field] for entry in entries)
    require(len(values) == len(set(values)), f"ID.{label}.unique")
    require(values == expected, f"ID.{label}.roster")
    return values


def parse_workflow_lenses(path: Path) -> tuple[tuple[int, str], ...]:
    text = path.read_text(encoding="utf-8", errors="strict")
    require(text.count(WORKFLOW_SECTION_START) == 1, "WORKFLOW.section_start")
    start = text.index(WORKFLOW_SECTION_START)
    require(text.count(WORKFLOW_SECTION_END, start) == 1, "WORKFLOW.section_end")
    end = text.index(WORKFLOW_SECTION_END, start)
    rows = tuple(
        (int(number), name.strip())
        for number, name in WORKFLOW_LENS_RE.findall(text[start:end])
    )
    require(rows == CANONICAL_LENSES, "WORKFLOW.lens_registry")
    return rows


def validate_anchor(locator: str, entry_id: str, index: int) -> None:
    label = f"ANCHOR.{entry_id}.{index}"
    parsed = urlsplit(locator)
    require(parsed.scheme == "https", f"{label}.scheme")
    require(parsed.username is None and parsed.password is None, f"{label}.credentials")
    require(parsed.query == "", f"{label}.query")
    if parsed.hostname == "primegaps.axiommath.ai":
        require(locator == "https://primegaps.axiommath.ai/paper/", f"{label}.paper")
        return
    require(parsed.hostname == "github.com", f"{label}.host")
    match = GITHUB_ANCHOR_RE.fullmatch(locator)
    require(match is not None, f"{label}.github_shape")
    revision, source_path, first_line, last_line = match.groups()
    require(revision == REVIEWED_COMMIT, "ANCHOR.github_revision")
    require("blob/main" not in locator, "ANCHOR.github_revision")
    require("%" not in source_path and "\\" not in source_path, f"{label}.path_encoding")
    parts = PurePosixPath(source_path).parts
    require(parts and all(part not in ("", ".", "..") for part in parts), f"{label}.path")
    require(int(first_line) >= 1 and int(first_line) <= int(last_line), f"{label}.lines")


def validate_external_locator(locator: str, artifact_id: str) -> None:
    label = f"SOURCE.external_locator.{artifact_id}"
    if locator.startswith("urn:"):
        require(
            locator == "urn:pid-rs:derived:primegaps-blueprint-layout-text",
            label,
        )
        return
    parsed = urlsplit(locator)
    require(parsed.scheme == "https", label)
    require(parsed.hostname in {"github.com", "primegaps.axiommath.ai"}, label)
    require(parsed.username is None and parsed.password is None, label)
    require(parsed.query == "" and parsed.fragment == "", label)


def local_expected_record(
    row: tuple[str, str, str, int, str, int, str]
) -> dict[str, object]:
    (
        artifact_id,
        locator,
        current_sha256,
        current_size,
        source_sha256,
        source_size,
        revision,
    ) = row
    return {
        "artifact_id": artifact_id,
        "durability": "repository-path",
        "kind": "text",
        "locator": locator,
        "revision": revision,
        "sha256": current_sha256,
        "size_bytes": current_size,
        "source_sha256": source_sha256,
        "source_size_bytes": source_size,
        "status": "reviewed-exact-bytes",
    }


def validate_repository_file(
    repository_root: Path,
    expected: dict[str, object],
) -> dict[str, object]:
    artifact_id = str(expected["artifact_id"])
    locator = str(expected["locator"])
    pure = PurePosixPath(locator)
    require(not pure.is_absolute(), f"SOURCE.repository_path.{artifact_id}")
    require(
        pure.parts and all(part not in ("", ".", "..") for part in pure.parts),
        f"SOURCE.repository_path.{artifact_id}",
    )
    require("\\" not in locator and ":" not in pure.parts[0], f"SOURCE.repository_path.{artifact_id}")
    root = repository_root.resolve(strict=True)
    candidate = repository_root.joinpath(*pure.parts)
    metadata = candidate.lstat()
    require(stat.S_ISREG(metadata.st_mode), f"SOURCE.repository_file_type.{artifact_id}")
    resolved = candidate.resolve(strict=True)
    require(resolved.is_relative_to(root), f"SOURCE.repository_escape.{artifact_id}")
    raw = candidate.read_bytes()
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    require(len(raw) == expected["size_bytes"], f"SOURCE.repository_bytes.{artifact_id}")
    require(
        observed_sha256 == expected["sha256"],
        f"SOURCE.repository_bytes.{artifact_id}",
    )
    return {
        "artifact_id": artifact_id,
        "locator": locator,
        "sha256": observed_sha256,
        "size_bytes": len(raw),
        "source_sha256": expected["source_sha256"],
        "source_size_bytes": expected["source_size_bytes"],
    }


def validate_autoresearch(transfer_by_id: dict[str, dict[str, Any]]) -> None:
    entry = transfer_by_id["autoresearch-promotion-boundary"]
    require(
        tuple(entry["preserved_assumptions"]) == AUTORESEARCH_PRESERVED,
        "AUTORESEARCH.preserved_assumptions",
    )
    require(
        tuple(entry["changed_assumptions"]) == AUTORESEARCH_CHANGED,
        "AUTORESEARCH.changed_assumptions",
    )
    require(
        entry["source_semantics"] == AUTORESEARCH_SOURCE_SEMANTICS,
        "AUTORESEARCH.source_semantics",
    )
    preserved = " ".join(AUTORESEARCH_PRESERVED).lower()
    for introduced_control in (
        "pre-registration",
        "candidate-inaccessible",
        "complete exposure",
        "holdout",
    ):
        require(
            introduced_control not in preserved,
            "AUTORESEARCH.source_control_conflation",
        )


def validate(
    *,
    ledger_path: Path,
    schema_path: Path,
    workflow_path: Path,
    repository_root: Path,
) -> dict[str, object]:
    schema, schema_raw = read_canonical_json(schema_path, "SCHEMA")
    require(schema.get("$schema") == SCHEMA_DIALECT, "SCHEMA.dialect")
    require(schema.get("$id") == SCHEMA_ID, "SCHEMA.id")
    require(b"blob/main" not in schema_raw, "SCHEMA.mutable_locator")
    require(hashlib.sha256(schema_raw).hexdigest() == SCHEMA_SHA256, "SCHEMA.sha256")

    ledger, ledger_raw = read_canonical_json(ledger_path, "LEDGER")
    schema_validation_error, validate_json_schema = load_schema_validator()
    try:
        validate_json_schema(ledger, schema, name="PrimeGaps transfer ledger")
    except schema_validation_error as error:
        raise RuntimeError("SCHEMA.instance") from error

    require(ledger["reviewed_source_commit"] == REVIEWED_COMMIT, "SOURCE.reviewed_commit")
    require(
        ledger["source_manifest_boundary"] == SOURCE_MANIFEST_BOUNDARY,
        "SOURCE.durability_boundary",
    )

    transfer_ids = registry_ids(
        ledger["transfer_entries"], "id", "transfer_entries", TRANSFER_IDS
    )
    decision_ids = registry_ids(
        ledger["design_decisions"], "id", "design_decisions", DESIGN_DECISION_IDS
    )
    source_ids = registry_ids(
        ledger["source_manifest"], "artifact_id", "source_manifest", SOURCE_IDS
    )
    council_ids = registry_ids(
        ledger["council"]["roles"], "role", "council", COUNCIL_IDS
    )
    all_ids = transfer_ids + decision_ids + source_ids + council_ids
    require(len(all_ids) == len(set(all_ids)), "ID.global.unique")

    workflow_lenses = parse_workflow_lenses(workflow_path)
    ledger_lenses = tuple(
        (entry["lens"], entry["name"]) for entry in ledger["lens_review"]
    )
    require(ledger_lenses == workflow_lenses, "LENS.registry")

    require(
        canonical_sha256(ledger["council"]) == COUNCIL_REGISTRY_SHA256,
        "COUNCIL.registry_sha256",
    )

    transfer_by_id = {entry["id"]: entry for entry in ledger["transfer_entries"]}
    anchor_registry: list[dict[str, object]] = []
    for entry_id in TRANSFER_IDS:
        for index, anchor in enumerate(transfer_by_id[entry_id]["source_anchors"]):
            validate_anchor(anchor["locator"], entry_id, index)
            anchor_registry.append(
                {
                    "entry_id": entry_id,
                    "locator": anchor["locator"],
                    "meaning": anchor["meaning"],
                }
            )
    observed_anchor_sha256 = canonical_sha256(anchor_registry)
    require(observed_anchor_sha256 == ANCHOR_REGISTRY_SHA256, "ANCHOR.registry_sha256")

    validate_autoresearch(transfer_by_id)

    source_by_id = {entry["artifact_id"]: entry for entry in ledger["source_manifest"]}
    for artifact_id in EXTERNAL_SOURCE_IDS:
        actual = source_by_id[artifact_id]
        validate_external_locator(actual["locator"], artifact_id)
        require(
            "source_sha256" not in actual and "source_size_bytes" not in actual,
            f"SOURCE.external_preimage_fields.{artifact_id}",
        )
        require(
            actual == EXTERNAL_SOURCE_RECORDS[artifact_id],
            f"SOURCE.external_identity.{artifact_id}",
        )

    local_byte_records: list[dict[str, object]] = []
    for row in LOCAL_SOURCE_RECORDS:
        expected = local_expected_record(row)
        artifact_id = str(expected["artifact_id"])
        require(
            source_by_id[artifact_id] == expected,
            f"SOURCE.repository_identity.{artifact_id}",
        )
        local_byte_records.append(validate_repository_file(repository_root, expected))

    require(
        hashlib.sha256(ledger_raw).hexdigest() == LEDGER_SHA256,
        "LEDGER.sha256",
    )

    local_byte_registry_sha256 = canonical_sha256(local_byte_records)
    lens_registry_sha256 = canonical_sha256(
        [{"lens": number, "name": name} for number, name in CANONICAL_LENSES]
    )
    return {
        "anchor_count": len(anchor_registry),
        "anchor_registry_sha256": observed_anchor_sha256,
        "council_independence_scope": "correlated_advisory_only",
        "council_role_count": len(COUNCIL_IDS),
        "decision_id_count": len(DESIGN_DECISION_IDS),
        "external_artifact_count": len(EXTERNAL_SOURCE_IDS),
        "external_artifact_custody": "hash_only_not_recovery",
        "format": "/pid-rs/primegaps-to-pid-transfer-ledger-check/v1",
        "gate": "GO",
        "ledger_sha256": hashlib.sha256(ledger_raw).hexdigest(),
        "lens_count": len(CANONICAL_LENSES),
        "lens_registry_sha256": lens_registry_sha256,
        "nonclaims": [
            "not_external_byte_recovery_or_durable_custody",
            "not_source_truth_authenticity_or_exhaustive_review",
            "not_independent_human_or_institutional_review",
            "not_formal_numerical_statistical_or_pid_claim_acceptance",
            "not_semantic_equivalence_proof_for_format_normalization",
        ],
        "packet_status": "proposed_programs_A_through_E_open",
        "repository_artifact_count": len(LOCAL_SOURCE_IDS),
        "repository_byte_registry_sha256": local_byte_registry_sha256,
        "reviewed_source_commit": REVIEWED_COMMIT,
        "schema_dialect": SCHEMA_DIALECT,
        "schema_sha256": hashlib.sha256(schema_raw).hexdigest(),
        "schema_validation_scope": "pinned_schema_all_used_assertions_bounded_validator",
        "schema_validator_sha256": JSON_SCHEMA_SUBSET_SHA256,
        "scope": "ledger_semantics_identity_and_local_byte_custody_only",
        "source_artifact_count": len(SOURCE_IDS),
        "source_preimage_binding_count": len(LOCAL_SOURCE_IDS),
        "transfer_id_count": len(TRANSFER_IDS),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate(
        ledger_path=args.ledger,
        schema_path=args.schema,
        workflow_path=args.workflow,
        repository_root=args.repository_root,
    )
    sys.stdout.write(canonical_json_ascii(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"PrimeGaps-to-PID transfer ledger: {error}", file=sys.stderr)
        raise SystemExit(1)
