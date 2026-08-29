#!/usr/bin/env python3
"""Fail closed when the revision-3 certified-SxPID2 assurance packet drifts."""

from __future__ import annotations

# BEGIN KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1
# ruff: noqa: E402 -- isolation is checked before non-bootstrap imports.

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-certified-sxpid2-claim.py requires Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys
# END KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


if sys.version_info < (3, 11):
    raise SystemExit("check-certified-sxpid2-claim.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
METHOD_ID = "validation.certified-sxpid2-reference"
REPORT_SCHEMA = "pid-rs/certified-sxpid-report/v2"
VERIFICATION_SCHEMA_V2 = "pid-rs/certified-sxpid-independent-verification/v2"
VERIFICATION_SCHEMA = "pid-rs/certified-sxpid-independent-verification/v3"
RESOURCE_POLICY = "sxpid2-certification-default-v2"
LOADED_EXECUTION_DOMAIN = "pid-certified-sxpid-independent-loaded-execution-v3"
EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256 = (
    "6c173cbf90fe27bbd43342f37ebe0378db76a1e4e8e22a92aa4d5416f9789bda"
)
EXPECTED_JUST_CERTIFIED_SXPID_RECIPE_SHA256 = (
    "fbd80548b0c62cb46f646e77e5f1df37d439299e71faec9bd05656839f660ae7"
)
EXPECTED_JUST_RELEASE_AUDIT_LINE_SHA256 = (
    "8bcf097b6852da0916044a48f4fb285d86a0db6124b4222346492235ab9da6db"
)
EXPECTED_EXECUTION_CONTAINER_SHA256 = {
    ".github/workflows/ci.yml": (
        "c34bfb2ed07fd324f045176a4e16e38bca399ee2cf4aed00a25f8484fa20cd3a"
    ),
    "justfile": ("1ea6f58c32861134a9f9cbb7f2c0804a997d782e7e78bd88bf492b6f2dc3b575"),
}
EXPECTED_REVISION3_AUTHORITY_SHA256 = {
    "audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md": (
        "aee278366f2bf990a5333dbaace7f190cb3191dfd2c2d972d8cf8ce33abe5004"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md": (
        "5eed715b409ce52271aa33dfba9466d566b78ef878438fdf7948f9a0135a9f7d"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md": (
        "31313a2069af8a02409aa466176c2c2105915344842be965983182ae236c1dc9"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md": (
        "8907de510080c53ef19de8e80f131f409588d88441205b11e34e6de59f7aa52f"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md": (
        "35aa45ed5cea6b0671a7012f048269e2970a5d39c50724fe1090c6fce0466fd7"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md": (
        "dcbdf594796dd9559a8882ff47599b1045f9671801e7f5ef26cd3edcbe355bf2"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md": (
        "9a9ec2894bf69513f04260bdeb991d454c65be693179868691513f69b7d7a346"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md": (
        "ab2974c309e40e36eba1c7e9fbe1d71e7a36aaf25eb91ec4d63d65e819c04f69"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md": (
        "7feba281c710a34e98cb75665b8a1e1adb63bbd31b972812945895faedb33046"
    ),
}
EXPECTED_RETAINED_HISTORICAL_PACKET_SHA256 = {
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md": (
        "d5fba2ba8d967144659ba146c7acb8fa3374ec7e544c1d0d06e722619fb6d9e3"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings.md": (
        "7989fdc848ce1be8d191508bf1cc908bbde0a4e44f42568e56048b26c3c5916a"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v1.md": (
        "887b542f357fe3b862988efba34230aa2d6f65ace16b43e0251559f9c3efdff4"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md": (
        "577765bca8e97950bb78ccca205ced15a6e40b0d6f73048887bc85f5731c538f"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/conventions.md": (
        "d2bc8441418303df7868b601605445765c90b2c0b1455cfc12575f0d7485bb7c"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md": (
        "d536192f4a31b151bd496261baa36fd321533fcbe186b692366507811958992e"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md": (
        "f150b443e7946ccd74ed076c2e581519de9c9ae1045a79d2ef7fb42f28d62d6a"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md": (
        "9344e9b052af84e863a306a4afdc9433736cc6f903f21bd3dc241cff3927a61b"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix.md": (
        "28da937d1801bf5c72e2a8e83078708d20fe6d6d1b2096e375a6473d341c3526"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v2.md": (
        "c331d4d8a53ea57c87e519f4e832799497b8169586a285d03937120aa69a84c0"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls.md": (
        "90f053619b776b62e2c196d4365a6ccb0d15576c649d138bba3586aea1a5fd49"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md": (
        "a8668d309a54be3791dcaed3ce5e7b36e06f6ceff0e91a7abda478589ae477bf"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map.md": (
        "36a40751e921bf78f9548fb98c582241505969081add04ad4cf1dc8b36fe71aa"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md": (
        "dee66c8f58bba53403ab169f07e7380eca62ec26d630105415b91c161accddac"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations.md": (
        "fe7ace497e5ce447b8b0c92275d3a828d39628df22cb92bf4ddc330f4483ce2e"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/exact-reconstruction.md": (
        "ca144ab501a07a7da9d72a31223bf5f8063b027ff055a45c131f86f1f60747d7"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/fable-verifier-adversarial-prompt.md": (
        "0caef62c2539af84fb922461098192b46839f4fff80273021f477d5f37e7abb2"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/fable-verifier-adversarial-review.md": (
        "19fbcfed7d87ba5c1d1ff150d10bd8b0e4c1cb0400f34d486b72bbb13dbb93eb"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/interval-containment.md": (
        "b39a7fc1344aca8cc3d043f4ea76c5f3f8475d5ab28633a1d3ef4c7b18b98eec"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/opus5-verifier-adversarial-prompt.md": (
        "b1264dd8cac5be61095bbf7e919757f35cf36ee6e03eb70b1cff8ff080ed5a29"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/opus5-verifier-adversarial-retry-prompt.md": (
        "860210bb09bf384d234b60b3665eaa0938b131ad3816d6d44649bf1211b96791"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/opus5-verifier-adversarial-review.md": (
        "3f7a488c883820a995353dc57f76d04b51636a1c477d0fb2517e3925ed836268"
    ),
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/provenance-custody.md": (
        "555a2fb82689a08fdbb546886ee8b30fab93ede36c1582ab74c87a69c6fe5f06"
    ),
}
EXPECTED_REVIEWED_DOCUMENTATION_SHA256 = {
    "audit/tools/certified-sxpid/README.md": (
        "61171ae73138570ecede4b1607b04f576807b6e92af1538539b38a0fca21f063"
    ),
    "scripts/README.md": (
        "57eee04a300d47eb451523ef2b2f0dc3435e5d28c2212745b852dd6c9d9d2242"
    ),
}
EXPECTED_CATALOG_METHOD_PROJECTION_SHA256 = (
    "a8318a5901b35d7187c6a031f66a3327ab53601ed3260249de2b25bcd2880b6a"
)
EXPECTED_EVIDENCE_PROJECTION_SHA256 = {
    "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json": (
        "9887b0deff4deeec915e363c77741e12973af49473f8a74ae98fbdd1afe4731c"
    ),
    "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json": (
        "57baea3ff12ee3feda2af0301f26fff4a0a6feba473efb3e820ffa0efc89b91b"
    ),
    "audit/evidence/sxpid2-exact-product-lean-check.json": (
        "c6424dfb99071606dc71668ad08b334be851156fa39e1825a6e73d5409e69174"
    ),
    "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json": (
        "9eb4ca9453a80ecf29e8b714f3db0a0ac23e1aca157e03b253f228469a79d13a"
    ),
    "audit/evidence/sxpid2-exact-product-mutation-suite.json": (
        "9922fb473f6bd52768e6f8120d0994e0903d7efe1e848c627650fd56a2c87de7"
    ),
    "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json": (
        "dfa276a129d0d82b739e3037488468fa921d5981b18c503a9cddef2a19511fbc"
    ),
    "audit/evidence/sxpid2-exact-product-qualification.json": (
        "6be55630c285e1bfc970c0b8796ca7cdcb79065b07afefcb467229afb2101870"
    ),
}
EXPECTED_LEAN_EVIDENCE_RAW_SHA256 = {
    "audit/evidence/sxpid2-exact-product-lean-check.json": (
        "3b4f5eb4efb1fa354f9b9c772508b0c7d7b900f61f3d2075fe58a1c5811a63e8"
    ),
    "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json": (
        "9742bd6c5e45049a7576781fb00b112b93e9dda20359ae73a4fcc93e2b659a6d"
    ),
}
EXPECTED_SUPPORT_GATE_SHA256 = {
    "scripts/check-formal-pdf-set.sh": (
        "de69e2106034d954cc9396fa64bb6b39e321e29b608c819e8f0ba23f6fc533c7"
    ),
}
EXPECTED_REVIEWED_EXECUTABLE_EVIDENCE_SHA256 = {
    "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md": (
        "538572da427e36142926bc6341fe32c4ab68a99b0d80cbfd3cf4c573b027e1e7"
    ),
    "audit/formal/latex/certified-sxpid2-executable-assurance.tex": (
        "297c9fdfae897b2136a3eb870a81c0ab0b3553d1056c1c87492dd0e6fbafdf61"
    ),
    "audit/formal/latex/exact-log-product-sxpid2-assurance.tex": (
        "9b8434e3062898f948bca72ba6ca5fdf9b23764390fe5552265ded2b8bdae81e"
    ),
    "audit/tools/certified-sxpid/deny.toml": (
        "8f5451e9ef2ee389a212f3c55b0d58032f5fe119fcff7109b74eff6d8ce04c03"
    ),
    "audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py": (
        "3b249687d0571f63e028ebaad44b1eb3df6feda4277bcfff1ee2fb6dd2be254d"
    ),
    "audit/tools/certified-sxpid/scripts/check-static-policy.py": (
        "8e318585121bdbfa3bcfbbef9587855cfc5ee2bd3f35dcccac8c4e38d4488a37"
    ),
    "output/pdf/certified-sxpid2-executable-assurance.pdf": (
        "2370637b750578fc1818279f6001f4143dd8e1e3d48136077a6953ceb2ee795c"
    ),
    "output/pdf/exact-log-product-sxpid2-assurance.pdf": (
        "1936f5bbddef4feeef6ce3418543142f2cb4aff815ae92a1144f30d5162f3c57"
    ),
    "scripts/check-certified-sxpid2-assurance-pdf.sh": (
        "b04db844f2e52baaba7250d209af69cb7eb2d26474f95b2bf896250061cf1392"
    ),
    "scripts/check-exact-log-product-sxpid2-pdf.sh": (
        "38453a6a9b040a31fb4de65a407efe0a7258e57fc3f2b06ceed8bbb20343f43d"
    ),
}
INCIDENT_PATH = (
    "audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md"
)
INCIDENT_COMMIT = "dc7b8de0a87443ef2bcde71b19938642f1af2197"
INCIDENT_TREE = "88b24c0ba4fcad4bd749b9146486143397b6a6eb"
INCIDENT_RUN = "30305288762"
INCIDENT_JOB = "90107923447"
INCIDENT_LOG_SHA256 = "7c9aa8c1c5f08506dc9dacfb54a9826fecf38393fc823e39dd0460bc1d0094db"
INCIDENT_VERIFIER_SHA256 = (
    "667bb3426a7fc936d90f74d7e1c0547dae7021fa250bb1f06c9c8c3b0d657d02"
)
INCIDENT_HARNESS_SHA256 = (
    "75fccc617b77513f48abaded50d31732f564abbcce2001f95527047d41ed85a9"
)

TEXT_PATHS = (
    "audit/tools/certified-sxpid/src/report.rs",
    "audit/tools/certified-sxpid/src/resource.rs",
    "audit/tools/certified-sxpid/src/lib.rs",
    "audit/tools/certified-sxpid/README.md",
    "audit/tools/certified-sxpid/deny.toml",
    "audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py",
    "audit/tools/certified-sxpid/scripts/check-static-policy.py",
    "audit/tools/certified-sxpid/scripts/verify_certificate.py",
    "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
    "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
    "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
    "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
    INCIDENT_PATH,
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v1.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/conventions.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/exact-reconstruction.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/fable-verifier-adversarial-prompt.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/fable-verifier-adversarial-review.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/interval-containment.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/opus5-verifier-adversarial-prompt.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/opus5-verifier-adversarial-retry-prompt.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/opus5-verifier-adversarial-review.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/route-memos/provenance-custody.md",
    "justfile",
    ".github/workflows/ci.yml",
    "scripts/README.md",
    "scripts/check-certified-sxpid2-assurance-pdf.sh",
    "scripts/check-exact-log-product-sxpid2-pdf.sh",
    "scripts/check-formal-pdf-set.sh",
)

JSON_PATHS = (
    "method-catalog.json",
    "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
    "audit/evidence/sxpid2-exact-product-qualification.json",
    "audit/evidence/sxpid2-exact-product-mutation-suite.json",
    "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
    "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
    "audit/evidence/sxpid2-exact-product-lean-check.json",
    "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json",
)

HASH_PATHS = (
    "audit/tools/certified-sxpid/scripts/verify_certificate.py",
    "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
    "audit/tools/certified-sxpid/scripts/_exact_product.py",
    "audit/tools/certified-sxpid/scripts/check-exact-products.py",
    "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "audit/evidence/sxpid2-exact-product-mutation-suite.json",
    "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
    "audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
    "scripts/check-lean-exact-log-product.py",
    "audit/formal/lean-exact-log-product/PidExactLogProduct.lean",
    "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
    "scripts/generate-sxpid2-exhaustive-oracle.py",
    *EXPECTED_LEAN_EVIDENCE_RAW_SHA256,
    *EXPECTED_REVIEWED_EXECUTABLE_EVIDENCE_SHA256,
)

REQUIRED_CATALOG_PATHS = frozenset(
    {
        "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
        "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
        "audit/formal/lean-exact-log-product/PidExactLogProduct.lean",
        "audit/tools/certified-sxpid/src/product.rs",
        "audit/tools/certified-sxpid/scripts/_exact_product.py",
        "audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
        "audit/tools/certified-sxpid/scripts/check-exact-products.py",
        "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
        "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
        "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
        "audit/evidence/sxpid2-exact-product-qualification.json",
        "audit/evidence/sxpid2-exact-product-mutation-suite.json",
        "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
        "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
        "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json",
        INCIDENT_PATH,
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md",
        "output/pdf/exact-log-product-sxpid2-assurance.pdf",
        "scripts/check-lean-exact-log-product.py",
        "scripts/check-exact-log-product-sxpid2-pdf.sh",
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-certified-sxpid2-claim-self-test.py",
        "scripts/check-formal-pdf-set.sh",
    }
)

GATE_COMMANDS = (
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
    "python3 scripts/check-lean-exact-log-product.py",
    "python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
    "python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py",
    "python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
    "python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
)


class ClaimPacketError(RuntimeError):
    """The live certifier, evidence, catalog, or versioned claim packet disagrees."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ClaimPacketError(f"duplicate JSON object key: {key!r}")
        value[key] = item
    return value


def reject_nonfinite_json_constant(value: str) -> None:
    raise ClaimPacketError(f"non-finite/nonstandard JSON constant: {value}")


def parse_json(raw: str, path: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_json_constant,
        )
    except (json.JSONDecodeError, ClaimPacketError) as error:
        raise ClaimPacketError(f"{path}: invalid strict JSON: {error}") from error


def canonical_json_projection_sha256(value: Any, label: str) -> str:
    try:
        canonical = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ClaimPacketError(f"{label} cannot be canonically projected") from error
    return hashlib.sha256(canonical).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClaimPacketError(message)


@dataclass(frozen=True)
class Snapshot:
    text: Mapping[str, str]
    json_values: Mapping[str, Any]
    sha256: Mapping[str, str]
    raw_text_sha256: Mapping[str, str]


def read_snapshot(root: Path = ROOT) -> Snapshot:
    text: dict[str, str] = {}
    raw_text_hashes: dict[str, str] = {}
    for relative in TEXT_PATHS:
        path = root / relative
        require(
            path.is_file() and not path.is_symlink(),
            f"missing/nonregular text: {relative}",
        )
        raw = path.read_bytes()
        try:
            text[relative] = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ClaimPacketError(f"non-UTF-8 text authority: {relative}") from error
        raw_text_hashes[relative] = hashlib.sha256(raw).hexdigest()
    values: dict[str, Any] = {}
    for relative in JSON_PATHS:
        path = root / relative
        require(
            path.is_file() and not path.is_symlink(),
            f"missing/nonregular JSON: {relative}",
        )
        values[relative] = parse_json(path.read_text(encoding="utf-8"), relative)
    hashes: dict[str, str] = {}
    for relative in HASH_PATHS:
        path = root / relative
        require(
            path.is_file() and not path.is_symlink(),
            f"missing/nonregular bound source: {relative}",
        )
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in REQUIRED_CATALOG_PATHS:
        path = root / relative
        require(
            path.is_file() and not path.is_symlink(),
            f"missing/nonregular evidence: {relative}",
        )
        require(path.stat().st_size > 0, f"empty evidence artifact: {relative}")
    return Snapshot(
        text=text,
        json_values=values,
        sha256=hashes,
        raw_text_sha256=raw_text_hashes,
    )


def require_token(snapshot: Snapshot, path: str, token: str, label: str) -> None:
    require(token in snapshot.text[path], f"{label} missing from {path}: {token!r}")


def require_comment_free_structured_markdown(text: str, path: str) -> None:
    require(
        "<!--" not in text and "-->" not in text,
        f"HTML comments are forbidden in structured Markdown authority: {path}",
    )
    for match in re.finditer(r"<[^>\n]+>", text):
        require(
            re.fullmatch(r"<https?://[^ >]+>", match.group(0)) is not None,
            f"raw HTML is forbidden in structured Markdown authority: {path}",
        )


def markdown_active_lines(text: str, path: str) -> tuple[str, ...]:
    require_comment_free_structured_markdown(text, path)
    active: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines():
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence_character is None:
            if (
                opening is not None
                and opening.group(1).startswith("`")
                and "`" in opening.group(2)
            ):
                opening = None
            if opening is not None:
                fence = opening.group(1)
                fence_character = fence[0]
                fence_length = len(fence)
                continue
            active.append(line)
            continue
        closing = re.match(
            rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
            line,
        )
        if closing is not None:
            fence_character = None
            fence_length = 0
    require(
        fence_character is None,
        f"unclosed fenced block in structured Markdown authority: {path}",
    )
    for line in active:
        require(
            re.match(r"^ {0,3}(?:=+|-+)[ \t]*$", line) is None,
            f"setext/horizontal headings are forbidden in structured Markdown authority: {path}",
        )
        if "|" in line:
            require(
                line.startswith("|") and line.endswith("|"),
                f"noncanonical pipe-table row in structured Markdown authority: {path}",
            )
            require(
                "](" not in line,
                f"linked pipe-table cells are forbidden in structured Markdown authority: {path}",
            )
    return tuple(active)


def level_two_heading_text(line: str) -> str | None:
    match = re.match(r"^ {0,3}##[ \t]+(.+?)[ \t]+#*[ \t]*$", line)
    if match is None:
        match = re.match(r"^ {0,3}##[ \t]+(.+?)[ \t]*$", line)
    if match is None:
        return None
    return match.group(1).rstrip("#").rstrip()


def markdown_section(snapshot: Snapshot, path: str, heading: str) -> str:
    source = snapshot.text[path]
    lines = markdown_active_lines(source, path)
    expected_heading = heading.removeprefix("## ")
    starts = [
        index
        for index, line in enumerate(lines)
        if level_two_heading_text(line) == expected_heading
    ]
    require(
        len(starts) == 1,
        f"expected one {heading!r} section in {path}, observed {len(starts)}",
    )
    start = starts[0] + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if level_two_heading_text(lines[index]) is not None
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def markdown_table_rows(text: str) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            rows.append(tuple(cell.strip() for cell in stripped[1:-1].split("|")))
    return tuple(rows)


def require_unique_table_row(
    snapshot: Snapshot,
    path: str,
    *,
    key: str,
    expected: tuple[str, ...],
    label: str,
    section: str | None = None,
) -> None:
    text = (
        "\n".join(markdown_active_lines(snapshot.text[path], path))
        if section is None
        else markdown_section(snapshot, path, section)
    )
    matches = [row for row in markdown_table_rows(text) if row and row[0] == key]
    require(
        len(matches) == 1,
        f"{label} must have exactly one table row in {path}; observed {len(matches)}",
    )
    require(
        matches[0] == expected,
        f"{label} table row differs in {path}: "
        f"expected={expected!r}; observed={matches[0]!r}",
    )


def require_active_command(
    snapshot: Snapshot, path: str, command: str, label: str
) -> None:
    lines = snapshot.text[path].splitlines()
    if path == "justfile":
        expected = f"    {command}"
        matches = []
        for index, line in enumerate(lines):
            if line != expected:
                continue
            recipe = next(
                (
                    preceding[:-1]
                    for preceding in reversed(lines[:index])
                    if preceding
                    and not preceding[0].isspace()
                    and re.fullmatch(r"[A-Za-z0-9_-]+:", preceding) is not None
                ),
                None,
            )
            if recipe == "certified-sxpid" and (
                index == 0 or not lines[index - 1].rstrip().endswith("\\")
            ):
                matches.append(line)
    else:
        expected = f"      - run: {command}"
        matches = []
        current_job: str | None = None
        for index, line in enumerate(lines):
            job_match = re.fullmatch(r"  ([A-Za-z0-9_-]+):", line)
            if job_match is not None:
                current_job = job_match.group(1)
            if line != expected:
                continue
            if current_job != "certified-sxpid-reference":
                continue
            indent = len(line) - len(line.lstrip(" "))
            inside_block_scalar = False
            for preceding in reversed(lines[:index]):
                stripped = preceding.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                preceding_indent = len(preceding) - len(preceding.lstrip(" "))
                if preceding_indent >= indent:
                    continue
                inside_block_scalar = (
                    re.search(r":\s*[|>][1-9+-]{0,2}\s*(?:#.*)?$", stripped) is not None
                )
                break
            has_step_sibling = False
            for following in lines[index + 1 :]:
                stripped = following.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                following_indent = len(following) - len(following.lstrip(" "))
                if following_indent <= indent:
                    break
                has_step_sibling = True
                break
            job_start = next(
                (
                    position
                    for position in range(index, -1, -1)
                    if lines[position] == "  certified-sxpid-reference:"
                ),
                -1,
            )
            job_has_condition = any(
                re.match(r"^    if:", candidate) is not None
                for candidate in lines[job_start + 1 : index]
            )
            if (
                not inside_block_scalar
                and not has_step_sibling
                and not job_has_condition
            ):
                matches.append(line)
    require(
        len(matches) == 1,
        f"{label} must occur once as an active command in {path}: {command!r}",
    )


def require_just_dependency(
    snapshot: Snapshot, recipe: str, dependency: str, label: str
) -> None:
    definitions = [
        match.group(1).split()
        for line in snapshot.text["justfile"].splitlines()
        if (
            match := re.fullmatch(
                rf"{re.escape(recipe)}:\s*(.*)",
                line,
            )
        )
        is not None
    ]
    require(
        len(definitions) == 1 and dependency in definitions[0],
        f"{label} missing from justfile: {recipe} -> {dependency}",
    )


def require_exact_gate_container_digests(snapshot: Snapshot) -> None:
    workflow_lines = snapshot.text[".github/workflows/ci.yml"].splitlines(keepends=True)
    workflow_starts = [
        index
        for index, line in enumerate(workflow_lines)
        if line == "  certified-sxpid-reference:\n"
    ]
    require(
        len(workflow_starts) == 1,
        "certified-sxpid-reference workflow job is not unique",
    )
    workflow_start = workflow_starts[0]
    workflow_end = next(
        (
            index
            for index in range(workflow_start + 1, len(workflow_lines))
            if re.fullmatch(r"  [A-Za-z0-9_-]+:\n", workflow_lines[index]) is not None
        ),
        len(workflow_lines),
    )
    workflow_digest = hashlib.sha256(
        "".join(workflow_lines[workflow_start:workflow_end]).encode("utf-8")
    ).hexdigest()
    require(
        workflow_digest == EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256,
        "certified-sxpid-reference workflow job exact digest changed",
    )

    just_lines = snapshot.text["justfile"].splitlines(keepends=True)
    just_starts = [
        index for index, line in enumerate(just_lines) if line == "certified-sxpid:\n"
    ]
    require(len(just_starts) == 1, "certified-sxpid just recipe is not unique")
    just_start = just_starts[0]
    just_end = next(
        (
            index
            for index in range(just_start + 1, len(just_lines))
            if just_lines[index].strip() and not just_lines[index][0].isspace()
        ),
        len(just_lines),
    )
    recipe_digest = hashlib.sha256(
        "".join(just_lines[just_start:just_end]).encode("utf-8")
    ).hexdigest()
    require(
        recipe_digest == EXPECTED_JUST_CERTIFIED_SXPID_RECIPE_SHA256,
        "certified-sxpid just recipe exact digest changed",
    )
    release_lines = [line for line in just_lines if line.startswith("release-audit:")]
    require(
        len(release_lines) == 1
        and hashlib.sha256(release_lines[0].encode("utf-8")).hexdigest()
        == EXPECTED_JUST_RELEASE_AUDIT_LINE_SHA256,
        "release-audit just dependency line exact digest changed",
    )


def require_exact_text_digests(
    snapshot: Snapshot, expected: Mapping[str, str], label: str
) -> None:
    for path, expected_digest in expected.items():
        observed_digest = snapshot.raw_text_sha256[path]
        require(
            observed_digest == expected_digest,
            f"{label} changed for {path}: "
            f"expected {expected_digest}, observed {observed_digest}",
        )


def validate(snapshot: Snapshot) -> None:
    # Live producer/verifier/schema agreement.
    exact_log_tex = "audit/formal/latex/exact-log-product-sxpid2-assurance.tex"
    for token in (
        "current pinned Lean 4.33.0 project",
        "The current execution receipt is the versioned\n"
        "\\texttt{sxpid2-exact-product-lean-check-4.33.0.json}.",
        "historical Lean 4.32 evidence",
    ):
        require_token(
            snapshot,
            exact_log_tex,
            token,
            "exact-log current/historical Lean boundary",
        )
    for stale in ("standalone Lean 4.32", "current pinned Lean 4.32"):
        require(
            stale not in snapshot.text[exact_log_tex],
            f"exact-log TeX contains stale current-toolchain wording: {stale}",
        )
    require_token(
        snapshot,
        "audit/tools/certified-sxpid/src/report.rs",
        REPORT_SCHEMA,
        "report schema",
    )
    require_token(
        snapshot,
        "audit/tools/certified-sxpid/src/resource.rs",
        RESOURCE_POLICY,
        "resource policy",
    )
    verifier = "audit/tools/certified-sxpid/scripts/verify_certificate.py"
    for token, label in (
        (REPORT_SCHEMA, "verifier report schema"),
        (VERIFICATION_SCHEMA, "verification schema"),
        (RESOURCE_POLICY, "verifier resource policy"),
        (LOADED_EXECUTION_DOMAIN, "loaded-execution digest domain"),
        ("_stabilize_code_string_cache", "loaded-execution cache normalization"),
        ("sys.intern", "loaded-execution string interning"),
        ("not_compared_per_expression_preflight_limit", "product local abstention"),
        ("not_compared_total_preflight_limit", "product aggregate abstention"),
        ("certified_exact_zero", "product exact-zero decision"),
        ("exact_multiplicative_product_equals_one", "product zero witness"),
        ("src/product.rs", "verifier source manifest"),
    ):
        require_token(snapshot, verifier, token, label)
    harness = "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
    for token, label in (
        (VERIFICATION_SCHEMA, "harness verification schema"),
        ("def check_loaded_execution_cache_stability", "cache-stability control"),
        ("def check_post_import_execution_mutation", "live-code mutation control"),
        (
            "def check_post_import_semantic_constant_mutations",
            "semantic-constant mutation controls",
        ),
        (
            "def check_cache_normalization_source_mutation",
            "cache-normalization source-mutation control",
        ),
        ("loaded-execution cache/integrity controls", "control-count output"),
        (
            "CPython-3.11 cache-normalization source",
            "version-conditioned source-mutation output",
        ),
    ):
        require_token(snapshot, harness, token, label)
    require_token(
        snapshot,
        "audit/tools/certified-sxpid/src/lib.rs",
        '"src/product.rs"',
        "producer source manifest",
    )
    tool_readme = "audit/tools/certified-sxpid/README.md"
    for token, label in (
        (REPORT_SCHEMA, "tool report schema"),
        (VERIFICATION_SCHEMA, "tool verification schema"),
        (RESOURCE_POLICY, "tool resource policy"),
        (LOADED_EXECUTION_DOMAIN, "tool loaded-execution domain"),
        ("two named cache/code controls", "tool control boundary"),
        ("check_cache_normalization_source_mutation", "tool source-mutant boundary"),
        ("not a proof of Python", "tool runtime boundary"),
    ):
        require_token(snapshot, tool_readme, token, label)

    # Historical revisions remain explicit, and revision 3 names only its verifier-runtime delta.
    decision_v1 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md"
    require_token(snapshot, decision_v1, "revision 1", "historical decision revision")
    require_token(
        snapshot, decision_v1, "Revision 1 must be re-adjudicated", "historical trigger"
    )
    require_token(
        snapshot,
        decision_v1,
        "Historical revision 1 must not be silently rewritten",
        "historical preservation rule",
    )
    claim_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md"
    for token, label in (
        ("revision 2", "claim revision"),
        (REPORT_SCHEMA, "claim report schema"),
        (VERIFICATION_SCHEMA_V2, "historical claim verification schema"),
        (RESOURCE_POLICY, "claim resource policy"),
        ("exact-product record has status `compared`", "claim product premise"),
        ("does not replace the dyadic interval", "claim lane separation"),
        ("no exact-product zero/sign claim is available", "claim abstention boundary"),
        ("defines no new PID measure", "claim provenance boundary"),
    ):
        require_token(snapshot, claim_v2, token, label)
    decision_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md"
    require_token(
        snapshot, decision_v2, "historical decision remains", "revision preservation"
    )
    require_token(
        snapshot,
        decision_v2,
        "Revision 2 requires a new revision",
        "revision-2 trigger",
    )
    require_token(
        snapshot,
        decision_v2,
        "exact five-factor rational",
        "revision-2 retained-witness formal boundary",
    )
    bindings_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md"
    require_token(
        snapshot,
        bindings_v2,
        "Six generic exact log/product/sign theorems",
        "revision-2 generic Lean inventory",
    )
    require_token(
        snapshot,
        bindings_v2,
        "separate exact-rational and Rust routes bind those",
        "revision-2 Lean-to-SxPID non-refinement boundary",
    )
    obligations_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md"
    require_token(
        snapshot,
        obligations_v2,
        "six generic theorems plus one exact five-factor rational identity",
        "revision-2 Lean obligation inventory",
    )
    evidence_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md"
    require_token(
        snapshot,
        evidence_v2,
        "exact five-factor Lean identity",
        "revision-2 retained-witness evidence",
    )
    theorem_map_v2 = (
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md"
    )
    require_token(
        snapshot,
        theorem_map_v2,
        "exact five-factor rational product identity",
        "revision-2 theorem/evidence boundary",
    )
    require_token(
        snapshot,
        theorem_map_v2,
        "the retained five-factor rational identity; exact-rational and Rust routes separately bind that",
        "revision-2 formal non-refinement boundary",
    )
    index = "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md"
    require_token(snapshot, index, "| 1 |", "revision-1 index row")
    require_token(snapshot, index, "| 2 |", "revision-2 index row")
    require_token(snapshot, index, "| 3 |", "revision-3 index row")
    require_token(
        snapshot,
        index,
        "Only the independent-verification schema, loaded-execution digest domain",
        "revision-3 index boundary",
    )

    claim_v3 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md"
    for token, label in (
        ("revision 3", "revision-3 claim identity"),
        (REPORT_SCHEMA, "revision-3 retained report schema"),
        (VERIFICATION_SCHEMA, "revision-3 verification schema"),
        (RESOURCE_POLICY, "revision-3 retained resource policy"),
        (LOADED_EXECUTION_DOMAIN, "revision-3 loaded-execution domain"),
        (
            "same two narrow per-input implications as revision 2",
            "unchanged claim scope",
        ),
        ("not a portable semantic hash", "digest portability exclusion"),
        ("cache-normalization source mutation", "source-mutant claim boundary"),
        ("does not yet have a fresh public green CI rerun", "open CI boundary"),
        ("defines no new PID measure", "revision-3 provenance boundary"),
    ):
        require_token(snapshot, claim_v3, token, label)

    bindings_v3 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md"
    for token, label in (
        (VERIFICATION_SCHEMA, "revision-3 binding schema"),
        (LOADED_EXECUTION_DOMAIN, "revision-3 binding digest domain"),
        ("check_cache_normalization_source_mutation", "source-mutant binding"),
        (
            "The producer source-manifest membership remains the same 17 paths",
            "retained manifest",
        ),
        ("No such future identifier is asserted here", "noncircular commit boundary"),
        ("fresh public green CI rerun", "open binding CI boundary"),
    ):
        require_token(snapshot, bindings_v3, token, label)
    for relative, label in (
        (verifier, "revision-3 verifier source digest"),
        (harness, "revision-3 harness source digest"),
    ):
        digest = snapshot.sha256[relative]
        require_unique_table_row(
            snapshot,
            bindings_v3,
            key=f"`{relative}`",
            expected=(f"`{relative}`", f"`{digest}`"),
            label=label,
            section="## Revision-3 source digests",
        )

    obligations_v3 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md"
    for token, label in (
        ("C3 remove nonsemantic intern-cache drift", "revision-3 obligation graph"),
        ("N3 remove-normalization source mutant", "source-mutant obligation"),
        (
            "`marshal` correctness remain trusted",
            "revision-3 runtime obligation boundary",
        ),
        ("fresh public CI rerun", "revision-3 open CI obligation"),
    ):
        require_token(snapshot, obligations_v3, token, label)

    evidence_v3 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md"
    for token, label in (
        ("Actions run `30305288762`, job `90107923447`", "retained CI evidence"),
        (
            "Two added runtime controls, 51 semantic-constant mutations, and one affected-runtime source mutant are not new SxPID mathematics",
            "unchanged mathematics",
        ),
    ):
        require_token(snapshot, evidence_v3, token, label)
    require_unique_table_row(
        snapshot,
        evidence_v3,
        key="Digests are portable semantic hashes across runtimes.",
        expected=(
            "Digests are portable semantic hashes across runtimes.",
            "No evidence; explicitly excluded",
            "Unsupported",
            "Runtime implementation/version and marshal format can matter",
        ),
        label="unsupported digest claim",
    )

    theorem_map_v3 = (
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md"
    )
    for token, label in (
        ("Revision 3 adds no mathematical theorem", "unchanged formal inventory"),
        (
            "no formal artifact verifies the Python runtime-integrity route",
            "formal boundary",
        ),
        ("Lean verifies the revision-3 verifier", "prohibited formal wording"),
    ):
        require_token(snapshot, theorem_map_v3, token, label)

    failures_v3 = (
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/"
        "retained-negative-controls-v3.md"
    )
    for token, label in (
        (
            "V3-NC1: nonsemantic cache state caused a fail-closed false rejection",
            "incident control",
        ),
        (
            "V3-NC2: cache normalization must not erase mutation sensitivity",
            "cache control",
        ),
        ("V3-NC3: a live code replacement must still fail", "live-code control"),
        (
            "V3-NC4: removing cache normalization must expose the affected path",
            "source-mutant control",
        ),
        (
            "V3-NC6: schema v2 cannot inherit schema-v3 digest semantics",
            "schema boundary control",
        ),
    ):
        require_token(snapshot, failures_v3, token, label)

    decision_v3 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md"
    for token, label in (
        ("historical decision remains", "revision-3 historical preservation"),
        ("Revision 3 requires a new revision", "revision-3 trigger"),
        ("Integration evidence remains open", "revision-3 open integration boundary"),
    ):
        require_token(snapshot, decision_v3, token, label)
    prohibited = markdown_section(snapshot, decision_v3, "## Prohibited wording")
    supported = markdown_section(snapshot, decision_v3, "## Supported wording")
    green_wording = "- “the observed CI run was green”; or"
    require(
        green_wording in prohibited.splitlines(),
        f"prohibited green-run wording missing from {decision_v3}",
    )
    rendered_supported = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", supported)
    rendered_supported = re.sub(r"[*_`]+", "", rendered_supported)
    rendered_supported = " ".join(rendered_supported.lower().split())
    require(
        "the observed ci run was green" not in rendered_supported,
        f"prohibited green-run wording entered the supported section in {decision_v3}",
    )
    for prohibited_supported_phrase in (
        "pid-rs or the sxpid2 certifier is formally verified",
        "cpython or the verifier is verified",
        "the loaded-execution digest is a portable semantic hash",
        "the pid-core or binary64 estimator is certified",
        "the interval is a confidence interval",
        "all sxpid atoms have a proved sign",
        "continuous or higher-source pid is covered",
        "independent review/custody is complete",
    ):
        require(
            prohibited_supported_phrase not in rendered_supported,
            f"prohibited wording entered the supported section in {decision_v3}: "
            f"{prohibited_supported_phrase!r}",
        )

    incident = snapshot.text[INCIDENT_PATH]
    for token, label in (
        (INCIDENT_COMMIT, "incident commit"),
        (INCIDENT_TREE, "incident tree"),
        (INCIDENT_RUN, "incident run"),
        (INCIDENT_JOB, "incident job"),
        (INCIDENT_LOG_SHA256, "incident retrieved-log digest"),
        (INCIDENT_VERIFIER_SHA256, "incident failing verifier digest"),
        (INCIDENT_HARNESS_SHA256, "incident failing harness digest"),
        ("used CPython 3.11.15 on", "incident runtime"),
        ("green rerun open", "incident open rerun status"),
        ("false rejection", "incident classification"),
    ):
        require(token in incident, f"{label} missing from {INCIDENT_PATH}: {token!r}")
    for relative, label in (
        (verifier, "incident candidate verifier digest"),
        (harness, "incident candidate harness digest"),
    ):
        digest = snapshot.sha256[relative]
        require_unique_table_row(
            snapshot,
            INCIDENT_PATH,
            key=f"`{relative}`",
            expected=(f"`{relative}`", f"`{digest}`"),
            label=label,
            section="## Candidate correction and revision boundary",
        )

    # Catalog must describe and inventory the complete revision-3 assurance route.
    catalog = snapshot.json_values["method-catalog.json"]
    require(isinstance(catalog, dict), "method catalog root is not an object")
    methods = catalog.get("methods")
    require(isinstance(methods, list), "method catalog has no methods array")
    matches = [
        item
        for item in methods
        if isinstance(item, dict) and item.get("id") == METHOD_ID
    ]
    require(len(matches) == 1, f"expected one {METHOD_ID!r} catalog entry")
    method = matches[0]
    require(
        method.get("scientific_novelty_claim") == "none",
        "certifier acquired a scientific novelty claim",
    )
    require(
        method.get("definition_origin") == "project-defined",
        "certifier definition origin drifted",
    )
    require(
        method.get("implementation_origin") == "local-implementation",
        "certifier implementation origin drifted",
    )
    source_files = method.get("source_files")
    require(isinstance(source_files, list), "certifier source_files is not an array")
    missing = sorted(REQUIRED_CATALOG_PATHS.difference(source_files))
    require(
        not missing, f"certifier catalog omits revision-3 source/evidence: {missing}"
    )
    validation = method.get("validation")
    require(isinstance(validation, dict), "certifier validation block is absent")
    evidence_paths = validation.get("evidence_paths")
    require(
        isinstance(evidence_paths, list), "certifier evidence_paths is not an array"
    )
    evidence_required = {
        path
        for path in REQUIRED_CATALOG_PATHS
        if path.startswith(
            (
                "audit/evidence/",
                "audit/formal/",
                "claims/",
                "output/pdf/",
                "scripts/check-",
            )
        )
    }
    missing_evidence = sorted(evidence_required.difference(evidence_paths))
    require(
        not missing_evidence,
        f"certifier validation omits revision-3 evidence: {missing_evidence}",
    )
    combined_claim_text = "\n".join(
        str(method.get(field, ""))
        for field in ("summary", "new_in_pid_rs", "constraints")
    )
    for token in (
        "exact-product",
        "product-one",
        "not a population",
        "not end-to-end formally verified",
    ):
        require(
            token in combined_claim_text.lower(),
            f"catalog claim boundary omits {token!r}",
        )
    require(
        canonical_json_projection_sha256(method, "certifier catalog method")
        == EXPECTED_CATALOG_METHOD_PROJECTION_SHA256,
        "certifier catalog method exact reviewed projection changed",
    )

    # Recorded evidence must be self-identifying and retain its bounded negative result.
    qualification = snapshot.json_values[
        "audit/evidence/sxpid2-exact-product-qualification.json"
    ]
    require(
        qualification.get("schema") == "pid-rs/sxpid2-exact-product-qualification/v1",
        "qualification schema drifted",
    )
    require(
        qualification.get("status") == "passed",
        "exact-product qualification is not passed",
    )
    checks = qualification.get("checks", {})
    require(
        checks.get("expression_products") == 11_856,
        "qualification product count drifted",
    )
    require(checks.get("exact_signs") == 11_856, "qualification sign count drifted")
    qualification_bindings = qualification.get("bindings", {})
    for field, relative in (
        (
            "exact_product_source_sha256",
            "audit/tools/certified-sxpid/scripts/_exact_product.py",
        ),
        (
            "qualification_source_sha256",
            "audit/tools/certified-sxpid/scripts/check-exact-products.py",
        ),
        (
            "fixture_sha256",
            "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
        ),
        ("fixture_generator_sha256", "scripts/generate-sxpid2-exhaustive-oracle.py"),
    ):
        require(
            qualification_bindings.get(field) == snapshot.sha256[relative],
            f"qualification binding {field} does not match {relative}",
        )

    mutations = snapshot.json_values[
        "audit/evidence/sxpid2-exact-product-mutation-suite.json"
    ]
    require(
        mutations.get("status") == "passed",
        "exact-product mutation suite is not passed",
    )
    require(
        mutations.get("certificate_mutations_killed") == 13,
        "certificate-mutation count drifted",
    )
    require(
        mutations.get("semantic_source_mutations_killed") == 6,
        "source-mutation count drifted",
    )
    require(
        mutations.get("structural_adversaries_rejected") == 4,
        "structural-adversary count drifted",
    )
    require(
        mutations.get("preflight_before_powering_controls_passed") == 2,
        "preflight-before-powering control count drifted",
    )
    require(
        mutations.get("boundary_evidence_projection_controls_passed") == 51,
        "boundary-evidence projection control count drifted",
    )
    require(
        mutations.get("boundary_receipt_scalar_leaf_mutations_checked") == 276
        and mutations.get("boundary_receipt_retained_leaf_changes_detected") == 274
        and mutations.get("boundary_receipt_declared_dynamic_leaf_invariances") == 2,
        "boundary-receipt scalar-leaf projection partition drifted",
    )
    require(
        mutations.get("boundary_receipt_retained_leaf_changes_detected", 0)
        + mutations.get("boundary_receipt_declared_dynamic_leaf_invariances", 0)
        == mutations.get("boundary_receipt_scalar_leaf_mutations_checked"),
        "boundary-receipt scalar-leaf subtotals do not reconstruct the total",
    )
    require(
        mutations.get("certificate_replay_scalar_leaf_mutations_checked") == 960
        and mutations.get("certificate_replay_retained_leaf_changes_detected") == 956
        and mutations.get("certificate_replay_declared_variable_leaf_invariances") == 4,
        "certificate-replay scalar-leaf projection partition drifted",
    )
    require(
        mutations.get("certificate_replay_retained_leaf_changes_detected", 0)
        + mutations.get("certificate_replay_declared_variable_leaf_invariances", 0)
        == mutations.get("certificate_replay_scalar_leaf_mutations_checked"),
        "certificate-replay scalar-leaf subtotals do not reconstruct the total",
    )
    require(
        mutations.get("total_adversaries") == 23,
        "exact-product adversary count drifted",
    )
    require(
        mutations.get("certificate_mutations_killed", 0)
        + mutations.get("semantic_source_mutations_killed", 0)
        + mutations.get("structural_adversaries_rejected", 0)
        == mutations.get("total_adversaries"),
        "exact-product mutation subtotals do not reconstruct the total",
    )
    mutation_bindings = mutations.get("bindings", {})
    require(
        mutation_bindings.get("exact_product_source_sha256")
        == snapshot.sha256["audit/tools/certified-sxpid/scripts/_exact_product.py"],
        "mutation evidence exact-product source binding drifted",
    )
    require(
        mutation_bindings.get("self_test_source_sha256")
        == snapshot.sha256[
            "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py"
        ],
        "mutation evidence self-test source binding drifted",
    )

    boundary = snapshot.json_values[
        "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json"
    ]
    require(
        boundary.get("status") == "passed", "non-syntactic zero boundary is not passed"
    )
    findings = boundary.get("findings", {})
    require(
        findings.get("n8_coordinate_count") == 16,
        "total-eight product-one count drifted",
    )
    witness = findings.get("minimized_witness", {})
    require(
        witness.get("counts") == [0, 0, 1, 1, 1, 4, 1, 0],
        "retained product-one witness drifted",
    )
    require(
        witness.get("interval_decision") == "unresolved_sign",
        "counterexample interval boundary drifted",
    )
    require(
        witness.get("exact_product_decision") == "certified_exact_zero",
        "counterexample product decision drifted",
    )
    boundary_bindings = boundary.get("bindings", {})
    require(
        boundary_bindings.get("exact_product_source_sha256")
        == snapshot.sha256["audit/tools/certified-sxpid/scripts/_exact_product.py"],
        "boundary evidence exact-product source binding drifted",
    )
    require(
        boundary_bindings.get("boundary_script_sha256")
        == snapshot.sha256[
            "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py"
        ],
        "boundary evidence script binding drifted",
    )
    require(
        set(boundary_bindings)
        == {
            "boundary_script_sha256",
            "certifier_executable_sha256",
            "exact_product_source_sha256",
            "live_certificate_replay_projection_sha256",
            "live_certificate_sha256",
            "live_input_sha256",
        },
        "boundary evidence binding inventory drifted",
    )
    for key, value in boundary_bindings.items():
        require(
            isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            f"boundary evidence binding is not a SHA-256 digest: {key}",
        )

    portability_path = (
        "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json"
    )
    portability = snapshot.json_values[portability_path]
    require(
        portability.get("schema")
        == "pid-rs/certified-sxpid2-boundary-replay-portability/v1",
        "boundary-replay process schema drifted",
    )
    require(
        portability.get("status") == "passed", "boundary-replay process is not passed"
    )
    portability_bindings = portability.get("bindings", {})
    require(
        set(portability_bindings)
        == {
            "boundary_evidence_sha256",
            "boundary_script_sha256",
            "exact_product_self_test_sha256",
            "exact_product_source_sha256",
            "mutation_evidence_sha256",
            "parent_boundary_evidence_sha256",
        },
        "boundary-replay process binding inventory drifted",
    )
    for field, relative in (
        (
            "boundary_evidence_sha256",
            "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
        ),
        (
            "boundary_script_sha256",
            "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
        ),
        (
            "exact_product_self_test_sha256",
            "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
        ),
        (
            "exact_product_source_sha256",
            "audit/tools/certified-sxpid/scripts/_exact_product.py",
        ),
        (
            "mutation_evidence_sha256",
            "audit/evidence/sxpid2-exact-product-mutation-suite.json",
        ),
    ):
        require(
            portability_bindings.get(field) == snapshot.sha256[relative],
            f"boundary-replay process binding {field} does not match {relative}",
        )
    require(
        portability_bindings.get("parent_boundary_evidence_sha256")
        == "2c663e0b6f9db2c8c70385515fff475ecb891afc9da491f79e67f3aadfc9db96",
        "boundary-replay parent evidence binding drifted",
    )
    portability_replay = portability.get("replay", {})
    require(
        portability_replay.get("ordinary_replay_changed_committed_bytes") is False,
        "boundary-replay ordinary mode changed committed bytes",
    )
    require(
        portability_replay.get("stable_projection_equal") is True,
        "boundary-replay stable projection did not agree",
    )
    require(
        portability_replay.get("cross_platform_execution_performed") is False,
        "boundary-replay platform-execution boundary drifted",
    )
    require(
        portability_replay.get("historical_refresh_stdout_sha256")
        == portability_bindings.get("boundary_evidence_sha256"),
        "boundary-replay historical stdout/evidence binding drifted",
    )
    require(
        portability_replay.get("live_certificate_replay_projection_sha256")
        == boundary_bindings.get("live_certificate_replay_projection_sha256"),
        "boundary-replay certificate projection binding drifted",
    )
    require(
        portability_replay.get("certificate_differences_observed_on_same_host")
        == [
            "payload/tool_binding/runtime_source_manifest_sha256",
            "payload_sha256",
        ],
        "boundary-replay observed certificate-difference inventory drifted",
    )
    portability_failure = portability.get("failure", {})
    require(
        portability_failure.get("class")
        == "execution_receipt_overwrite_across_artifact_builds"
        and portability_failure.get("retained_negative_result") is True,
        "boundary-replay retained failure classification drifted",
    )
    require(
        portability_failure.get("historical_certificate_sha256")
        == boundary_bindings.get("live_certificate_sha256")
        and portability_failure.get("historical_certifier_executable_sha256")
        == boundary_bindings.get("certifier_executable_sha256"),
        "boundary-replay historical execution bindings drifted",
    )
    require(
        portability_replay.get("current_live_receipt_retention")
        == "digest_only_not_independently_replayable_custody",
        "boundary-replay current-live retention boundary drifted",
    )
    portability_verification = portability.get("verification", {})
    require(
        portability_verification.get("binding_inventory")
        == [
            "boundary_script_sha256",
            "certifier_executable_sha256",
            "exact_product_source_sha256",
            "live_certificate_replay_projection_sha256",
            "live_certificate_sha256",
            "live_input_sha256",
        ],
        "boundary-replay complete binding inventory drifted",
    )
    require(
        portability_verification.get("boundary_evidence_projection_controls_passed")
        == 51,
        "boundary-replay projection control count drifted",
    )
    expected_leaf_partition = {
        "boundary_receipt_declared_dynamic_leaf_invariances": 2,
        "boundary_receipt_retained_leaf_changes_detected": 274,
        "boundary_receipt_scalar_leaf_mutations_checked": 276,
        "certificate_replay_declared_variable_leaf_invariances": 4,
        "certificate_replay_retained_leaf_changes_detected": 956,
        "certificate_replay_scalar_leaf_mutations_checked": 960,
        "total_scalar_leaf_mutations_checked": 1_236,
    }
    require(
        portability_verification.get("exhaustive_scalar_leaf_partition")
        == expected_leaf_partition,
        "boundary-replay exhaustive scalar-leaf partition drifted",
    )
    for field, count in expected_leaf_partition.items():
        if field == "total_scalar_leaf_mutations_checked":
            continue
        require(
            mutations.get(field) == count,
            f"boundary-replay process/mutation evidence disagree for {field}",
        )
    require(
        portability_verification.get("dynamic_replay_bindings")
        == ["certifier_executable_sha256", "live_certificate_sha256"],
        "boundary-replay dynamic outer-binding inventory drifted",
    )
    require(
        portability_verification.get("stable_replay_bindings")
        == [
            "boundary_script_sha256",
            "exact_product_source_sha256",
            "live_certificate_replay_projection_sha256",
            "live_input_sha256",
        ],
        "boundary-replay stable outer-binding inventory drifted",
    )
    require(
        portability_verification.get("certificate_projection_excluded_paths")
        == [
            "payload/tool_binding/runtime_source_manifest_sha256",
            "payload/tool_binding/build_context/rustc_verbose_version",
            "payload/tool_binding/build_context/build_host",
            "payload/tool_binding/build_context/build_target",
        ],
        "boundary-replay certificate exclusion inventory drifted",
    )
    require(
        portability_verification.get("ordinary_mode")
        == "read_only_compare_stable_projection_and_emit_full_live_receipt_to_stdout",
        "boundary-replay ordinary mode drifted",
    )
    require(
        portability_verification.get("update_mode") == "explicit_update_evidence_only",
        "boundary-replay update mode drifted",
    )
    portability_boundary = portability.get("claim_boundary", "")
    for token in (
        "No second operating system or architecture was executed",
        "not executable identity",
        "not cross-platform validated",
        "not a portable semantic hash",
    ):
        require(
            token in portability_boundary,
            f"boundary-replay claim boundary omits {token!r}",
        )

    historical_lean_path = "audit/evidence/sxpid2-exact-product-lean-check.json"
    current_lean_path = "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json"
    historical_lean = snapshot.json_values[historical_lean_path]
    current_lean = snapshot.json_values[current_lean_path]
    for role, lean in (
        ("historical Lean 4.32", historical_lean),
        ("current Lean 4.33", current_lean),
    ):
        require(
            lean.get("status") == "passed",
            f"Lean exact-product check is not passed: {role}",
        )
        require(
            lean.get("theorems_kernel_checked") == 7,
            f"Lean theorem count drifted: {role}",
        )
        require(
            "Generic log/product/sign algebra only" in lean.get("boundary", ""),
            f"Lean boundary broadened: {role}",
        )
        require(
            lean.get("source_sha256")
            == snapshot.sha256[
                "audit/formal/lean-exact-log-product/PidExactLogProduct.lean"
            ],
            f"Lean evidence theorem-source binding drifted: {role}",
        )
    require(
        historical_lean.get("lean_toolchain") == "leanprover/lean4:v4.32.0"
        and historical_lean.get("checker_source_sha256")
        == "37ae2779cbf3caaafc57aee324f61e64d992e513825ec475302e8c91527c04d9"
        and historical_lean.get("lake_manifest_sha256")
        == "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd",
        "historical Lean 4.32 evidence identity drifted",
    )
    require(
        current_lean.get("lean_toolchain") == "leanprover/lean4:v4.33.0"
        and current_lean.get("checker_source_sha256")
        == snapshot.sha256["scripts/check-lean-exact-log-product.py"],
        "current Lean 4.33 evidence checker/toolchain binding drifted",
    )
    require(
        current_lean.get("lake_manifest_sha256")
        == "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af",
        "current Lean 4.33 evidence manifest binding drifted",
    )
    lean_version = current_lean.get("lean_version")
    matched_version = re.fullmatch(
        r"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
        r"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), "
        r"commit (?P<commit>[0-9a-f]{40}), (?P<build>[A-Za-z][A-Za-z0-9_.+-]*)\)",
        lean_version if isinstance(lean_version, str) else "",
    )
    require(
        matched_version is not None
        and (
            matched_version.group("version"),
            matched_version.group("commit"),
            matched_version.group("build"),
        )
        == (
            "4.33.0",
            "d8b18978322de05a8f3dba51ef03cf5461676c17",
            "Release",
        ),
        "current Lean 4.33 portable release identity drifted",
    )

    challenge = snapshot.json_values[
        "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json"
    ]
    require(
        challenge.get("status") == "no_counterexample_found_within_search",
        "evolutionary result status drifted",
    )
    require(
        challenge.get("search", {}).get("unique_count_tables_evaluated") == 5_921,
        "evolutionary evaluation count drifted",
    )
    require(
        "not a universal nonnegativity proof" in challenge.get("negative_boundary", ""),
        "evolutionary negative boundary broadened",
    )
    challenge_bindings = challenge.get("bindings", {})
    require(
        challenge_bindings.get("exact_product_source_sha256")
        == snapshot.sha256["audit/tools/certified-sxpid/scripts/_exact_product.py"],
        "evolutionary evidence exact-product source binding drifted",
    )
    require(
        challenge_bindings.get("challenge_source_sha256")
        == snapshot.sha256[
            "audit/tools/certified-sxpid/scripts/challenge-exact-products.py"
        ],
        "evolutionary evidence script binding drifted",
    )
    for path, expected_digest in EXPECTED_EVIDENCE_PROJECTION_SHA256.items():
        require(
            canonical_json_projection_sha256(
                snapshot.json_values[path],
                f"certified-SxPID evidence {path}",
            )
            == expected_digest,
            f"certified-SxPID evidence exact reviewed projection changed: {path}",
        )
    for path, expected_digest in EXPECTED_LEAN_EVIDENCE_RAW_SHA256.items():
        require(
            snapshot.sha256[path] == expected_digest,
            f"exact Lean execution evidence bytes changed: {path}",
        )

    # Every normal entry point must execute the new gates; the formal inventory must include the paper.
    for path in ("justfile", ".github/workflows/ci.yml"):
        require(
            "--update-evidence" not in snapshot.text[path],
            f"ordinary gate container must not update historical evidence: {path}",
        )
        for command in GATE_COMMANDS:
            require_active_command(
                snapshot, path, command, "revision-3 executable gate"
            )
    require_just_dependency(
        snapshot,
        "release-audit",
        "certified-sxpid",
        "revision-3 release-audit dependency",
    )
    require_exact_gate_container_digests(snapshot)
    formal_set = "scripts/check-formal-pdf-set.sh"
    require_token(
        snapshot,
        formal_set,
        '"exact-log-product-sxpid2-assurance"',
        "formal PDF inventory",
    )
    require_token(
        snapshot,
        formal_set,
        "scripts/check-exact-log-product-sxpid2-pdf.sh",
        "formal PDF replay",
    )
    scripts_readme = "scripts/README.md"
    for token in (
        "check-certified-sxpid2-claim.py",
        "check-exact-log-product-sxpid2-pdf.sh",
        "bounded exact",
        "rational-product zero/sign extension",
        "revision-3 claim",
        "Two named cache/code controls",
    ):
        require_token(snapshot, scripts_readme, token, "script documentation")
    # Complete-byte custody is an independent layer over the semantic checks.
    # It closes enclosing workflow/Just semantics and Markdown rendering
    # equivalences that the deliberately small parsers above cannot model.
    require_exact_text_digests(
        snapshot,
        EXPECTED_EXECUTION_CONTAINER_SHA256,
        "reviewed revision-3 execution container digest",
    )
    require_exact_text_digests(
        snapshot,
        EXPECTED_REVISION3_AUTHORITY_SHA256,
        "immutable revision-3 authority digest",
    )
    require_exact_text_digests(
        snapshot,
        EXPECTED_RETAINED_HISTORICAL_PACKET_SHA256,
        "immutable retained historical packet digest",
    )
    require_exact_text_digests(
        snapshot,
        EXPECTED_REVIEWED_DOCUMENTATION_SHA256,
        "immutable reviewed certified-SxPID documentation digest",
    )
    require_exact_text_digests(
        snapshot,
        EXPECTED_SUPPORT_GATE_SHA256,
        "immutable reviewed certified-SxPID support-gate digest",
    )
    for path, expected_digest in EXPECTED_REVIEWED_EXECUTABLE_EVIDENCE_SHA256.items():
        require(
            snapshot.sha256[path] == expected_digest,
            f"immutable reviewed executable/evidence artifact digest changed: {path}",
        )


def main() -> int:
    try:
        validate(read_snapshot())
        print(
            "OK: certified SxPID2 claim revisions 1-3, schemas, evidence, "
            "catalog, and gates are coherent"
        )
        return 0
    except (OSError, UnicodeError, ClaimPacketError) as error:
        print(f"certified SxPID2 claim check failed: {error}", file=sys.stderr)
        return 1


# BEGIN KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1
import argparse  # noqa: E402 -- removable private CLI block preserves cb3f bytes.


SELF_TEST_VECTOR_SCHEMA = "pid-rs/certified-sxpid2-claim-self-test-vector/v1"
MAX_SELF_TEST_VECTOR_BYTES = 8 * 1024 * 1024


def canonical_json_bytes(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ClaimPacketError(
            "self-test value cannot be canonically encoded"
        ) from error
    return (rendered + "\n").encode("utf-8")


def parse_canonical_json_bytes(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ClaimPacketError(f"{label}: input is not UTF-8") from error
    try:
        value = parse_json(text, label)
    except ValueError as error:
        raise ClaimPacketError(f"{label}: invalid strict JSON: {error}") from error
    require(raw == canonical_json_bytes(value), f"{label}: input is not canonical JSON")
    return value


def exact_mapping(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} is not an object")
    require(set(value) == keys, f"{label} key inventory differs")
    return value


def snapshot_data(snapshot: Snapshot) -> dict[str, Any]:
    return {
        "json_values": dict(snapshot.json_values),
        "raw_text_sha256": dict(snapshot.raw_text_sha256),
        "sha256": dict(snapshot.sha256),
        "text": dict(snapshot.text),
    }


def decode_self_test_json_value(value: Any) -> Any:
    if value == {"__pid_rs_self_test_nonfinite__": "NaN"}:
        return float("nan")
    if isinstance(value, list):
        return [decode_self_test_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: decode_self_test_json_value(item) for key, item in value.items()}
    return value


def snapshot_from_delta(value: Any, *, pin_unfrozen_containers: bool) -> Snapshot:
    delta = exact_mapping(
        value,
        {"json_values", "raw_text_sha256", "sha256", "text"},
        "snapshot delta",
    )
    baseline = read_snapshot()

    def overlaid_mapping(
        name: str, baseline_values: Mapping[str, Any], *, strings_only: bool
    ) -> dict[str, Any]:
        replacements = delta[name]
        require(
            isinstance(replacements, dict), f"snapshot delta {name} is not an object"
        )
        require(
            set(replacements).issubset(baseline_values),
            f"snapshot delta {name} contains an unknown path",
        )
        if strings_only:
            require(
                all(isinstance(item, str) for item in replacements.values()),
                f"snapshot delta {name} contains a non-string value",
            )
        result = dict(baseline_values)
        result.update(
            {
                path: decode_self_test_json_value(item)
                if name == "json_values"
                else item
                for path, item in replacements.items()
            }
        )
        if name == "raw_text_sha256" and pin_unfrozen_containers:
            pin_by_path = {
                ".github/workflows/ci.yml": EXPECTED_EXECUTION_CONTAINER_SHA256[
                    ".github/workflows/ci.yml"
                ],
                "justfile": EXPECTED_EXECUTION_CONTAINER_SHA256["justfile"],
                "scripts/README.md": EXPECTED_REVIEWED_DOCUMENTATION_SHA256[
                    "scripts/README.md"
                ],
            }
            for path, expected in pin_by_path.items():
                if path not in replacements:
                    result[path] = expected
        return result

    return Snapshot(
        text=overlaid_mapping("text", baseline.text, strings_only=True),
        json_values=overlaid_mapping(
            "json_values", baseline.json_values, strings_only=False
        ),
        sha256=overlaid_mapping("sha256", baseline.sha256, strings_only=True),
        raw_text_sha256=overlaid_mapping(
            "raw_text_sha256", baseline.raw_text_sha256, strings_only=True
        ),
    )


def snapshot_without_unfrozen_container_pins() -> Snapshot:
    return snapshot_from_delta(
        {"json_values": {}, "raw_text_sha256": {}, "sha256": {}, "text": {}},
        pin_unfrozen_containers=True,
    )


def emit_self_test_result(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value))
    sys.stdout.buffer.flush()


def emit_self_test_failure(error: Exception) -> int:
    message = str(error)
    if len(message) > 512:
        message = message[:509] + "..."
    emit_self_test_result({"error": message, "result": "fail"})
    return 1


def require_private_runtime_mode() -> None:
    require(
        sys.version_info >= (3, 11)
        and sys.flags.isolated == 1
        and sys.flags.safe_path
        and sys.flags.no_site == 1
        and sys.flags.ignore_environment == 1
        and sys.dont_write_bytecode
        and sys.flags.optimize in {0, 1},
        "private self-test route requires Python 3.11+ -I -S -B and at most one -O",
    )


def run_self_test_vector_mode() -> int:
    try:
        require_private_runtime_mode()
        raw = sys.stdin.buffer.read(MAX_SELF_TEST_VECTOR_BYTES + 1)
        require(
            len(raw) <= MAX_SELF_TEST_VECTOR_BYTES,
            "self-test vector exceeds byte bound",
        )
        request = exact_mapping(
            parse_canonical_json_bytes(raw, "self-test vector"),
            {"arguments", "operation", "schema"},
            "self-test vector",
        )
        require(
            request["schema"] == SELF_TEST_VECTOR_SCHEMA,
            "self-test vector schema differs",
        )
        require(
            isinstance(request["operation"], str), "self-test operation is malformed"
        )
        arguments = request["arguments"]
        operation = request["operation"]
        if operation == "runtime_mode":
            values = exact_mapping(arguments, {"optimize"}, "runtime-mode arguments")
            require(
                type(values["optimize"]) is int
                and values["optimize"] in {0, 1}
                and values["optimize"] == sys.flags.optimize,
                "checker child optimization differs from its parent",
            )
            emit_self_test_result({"result": "pass"})
            return 0
        if operation == "snapshot":
            exact_mapping(arguments, set(), "snapshot arguments")
            emit_self_test_result(
                {"result": "snapshot", "snapshot": snapshot_data(read_snapshot())}
            )
            return 0
        if operation == "strict_json":
            values = exact_mapping(arguments, {"raw"}, "strict-JSON arguments")
            require(
                isinstance(values["raw"], str), "strict-JSON raw value is malformed"
            )
            try:
                parse_json(values["raw"], "self-test strict JSON")
            except (ValueError, ClaimPacketError) as error:
                return emit_self_test_failure(
                    ClaimPacketError(
                        f"self-test strict JSON: invalid strict JSON: {error}"
                    )
                )
            emit_self_test_result({"result": "pass"})
            return 0
        if operation == "validate":
            values = exact_mapping(arguments, {"delta"}, "validation arguments")
            snapshot = snapshot_from_delta(
                values["delta"], pin_unfrozen_containers=True
            )
        elif operation == "validate_structural_baseline":
            exact_mapping(arguments, set(), "structural-baseline arguments")
            snapshot = snapshot_without_unfrozen_container_pins()
        else:
            raise ClaimPacketError("self-test operation is not registered")
    except (OSError, UnicodeError, ClaimPacketError) as error:
        print(
            f"certified SxPID2 self-test vector protocol failed: {error}",
            file=sys.stderr,
        )
        return 2

    try:
        validate(snapshot)
    except (OSError, UnicodeError, ClaimPacketError) as error:
        return emit_self_test_failure(error)
    emit_self_test_result({"result": "pass"})
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, allow_abbrev=False, add_help=False
    )
    parser.add_argument("--self-test-vectors", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    private_arguments = parse_args()
    if private_arguments.self_test_vectors:
        if sys.argv[1:] != ["--self-test-vectors"]:
            print(
                "check-certified-sxpid2-claim.py: private option must occur exactly once",
                file=sys.stderr,
            )
            raise SystemExit(2)
        raise SystemExit(run_self_test_vector_mode())
# END KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1


if __name__ == "__main__":
    raise SystemExit(main())
