#!/usr/bin/env python3
"""Hostile tests for exact-open-font publication figure regeneration."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import NoReturn


CHECK_NAME = "publication open-font figure regeneration self-test"
EXPECTED_FONTS = (
    (
        "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Regular.otf",
        "7134d229b15cdd0827376d8a24f6f531f616eb1b3fecd16e1cf8a86d0bf6bc51",
        False,
    ),
    (
        "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Semibold.otf",
        "aa53ed4fc17334a0c2ee8412c1e4e728bfb732a96b119164f7354343dad8f2f2",
        False,
    ),
    (
        "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Bold.otf",
        "daccddbe3dd60fe10f6e8a785eda187925da6b611141024dffa43626998dfc7c",
        False,
    ),
    (
        "fonts/opentype/public/lm/lmsans10-regular.otf",
        "d431b786b9b603662718e79cfe9b441f47a8b0b3e854dde89d5acb3ed7cfd682",
        True,
    ),
    (
        "fonts/opentype/public/lm/lmsans10-bold.otf",
        "a597b710326c1a8a2c7238d808e5d38711638a72a32383478db4829d63afd687",
        True,
    ),
)
EXPECTED_OUTPUTS = {
    "semantic-firewall.pdf",
    "result-evidence-map.pdf",
    "audit-coordinate-crosswalk.pdf",
    "source-cylinder-factorization.pdf",
    "open-font-regeneration-receipt.json",
}
EXPECTED_LICENSE_ARTIFACTS = (
    (
        "audit/formal/latex/mathematical-results-guide/font-licenses/"
        "source-sans-pro-ofl-1.1-tex-live-2024.txt",
        4529,
        "4a4a4179a96b5ef6786186d199f0d049b151352f460b8d2f3c00083792f37dd9",
    ),
    (
        "audit/formal/latex/mathematical-results-guide/font-licenses/"
        "gust-font-license-1.0-tex-live-2024.txt",
        1377,
        "49ea6cb9257bbee0a3979c48a774cd221550ac1c20c95549efe45fc99cc18050",
    ),
    (
        "audit/formal/latex/mathematical-results-guide/font-licenses/"
        "manifest-latin-modern-2.004-tex-live-2024.txt",
        52635,
        "402c79f4ede8548a6fe6f82f42f0288cb0243ba2403dfdeeaadf55d189a46fae",
    ),
)


def fail(detail: str) -> NoReturn:
    raise SystemExit(f"{CHECK_NAME} failed: {detail}")


def run_query(command: list[str], label: str) -> str:
    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        fail(f"{label} could not run: {error}")
    value = result.stdout.strip()
    if result.returncode != 0 or not value or "\n" in value or "\r" in value:
        fail(f"{label} did not return one path")
    return value


def canonical_existing(raw: str, label: str) -> Path:
    candidate = Path(raw)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        fail(f"cannot resolve {label}: {error}")
    if not candidate.is_absolute() or resolved != candidate:
        fail(f"{label} is not a canonical absolute path: {raw!r}")
    return candidate


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_script(path: Path, body: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
    try:
        data = body.encode("utf-8")
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                fail(f"wrapper write made no progress: {path}")
            offset += written
    finally:
        os.close(descriptor)


def copy_font_fixture(
    destination: Path, texmf_dist: Path, texmf_debian: Path | None
) -> Path:
    destination.mkdir(mode=0o700)
    for relative, expected_hash, may_use_debian in EXPECTED_FONTS:
        candidates = [texmf_dist / relative]
        if may_use_debian and texmf_debian is not None:
            candidates.append(texmf_debian / relative)
        source = next((path for path in candidates if path.is_file() and not path.is_symlink()), None)
        if source is None:
            fail(f"accepted font fixture is absent: {relative}")
        observed = hash_file(source)
        if observed != expected_hash:
            fail(f"accepted font fixture hash changed for {relative}: {observed}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with source.open("rb") as source_stream, target.open("xb") as target_stream:
            shutil.copyfileobj(source_stream, target_stream)
    return destination


def invoke(
    checker: Path,
    output: Path,
    texmf_dist: Path,
    *,
    environment: dict[str, str],
    extra: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-O")
    command.extend(
        [
            str(checker),
            "--output-dir",
            str(output),
            "--texmf-dist",
            str(texmf_dist),
        ]
    )
    if extra:
        command.extend(extra)
    try:
        return subprocess.run(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            check=False,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        fail(f"regenerator invocation could not run: {error}")


def expect_reject(
    label: str,
    checker: Path,
    output: Path,
    texmf_dist: Path,
    expected: str,
    *,
    environment: dict[str, str],
    extra: list[str] | None = None,
) -> None:
    result = invoke(
        checker,
        output,
        texmf_dist,
        environment=environment,
        extra=extra,
    )
    diagnostic = result.stdout + result.stderr
    if result.returncode == 0:
        fail(f"hostile case was accepted: {label}")
    if expected not in diagnostic:
        fail(f"hostile case {label} emitted the wrong diagnostic: {diagnostic!r}")
    if output.is_dir() and not output.is_symlink():
        fail(f"hostile case published an output directory: {label}")


def main() -> int:
    repository_root = Path(__file__).resolve(strict=True).parent.parent
    checker = repository_root / "scripts/regenerate-mathematical-results-guide-open-font-figures.py"
    if checker.is_symlink() or not checker.is_file():
        fail("production regenerator is absent, non-regular, or symbolic")
    source = checker.read_text(encoding="utf-8")
    required_source_tokens = (
        '"PANGOCAIRO_BACKEND": "fontconfig"',
        "output directory must be outside the repository",
        "for run_index in (1, 2):",
        "rendered[0][output_name] != rendered[1][output_name]",
        '"pandoc_used": False',
        '"license_artifacts": license_artifact_receipt',
        "4bdf42c690a214a0f69410d71a6b889c5c4a695f",
    )
    missing_tokens = [token for token in required_source_tokens if token not in source]
    if missing_tokens:
        fail(f"production source lost critical contracts: {missing_tokens}")

    texmf_dist = canonical_existing(
        run_query(["kpsewhich", "-var-value=TEXMFDIST"], "TEXMFDIST query"),
        "TEXMFDIST",
    )
    texmf_debian_raw = ""
    query = subprocess.run(
        ["kpsewhich", "-var-value=TEXMFDEBIAN"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
        text=True,
    )
    if query.returncode == 0 and query.stdout.strip():
        texmf_debian_raw = query.stdout.strip()
    elif query.returncode not in (0, 1) or query.stdout.strip() or query.stderr.strip():
        fail("TEXMFDEBIAN query failed unexpectedly")
    texmf_debian = (
        canonical_existing(texmf_debian_raw, "TEXMFDEBIAN") if texmf_debian_raw else None
    )

    test_root = Path(tempfile.mkdtemp(prefix="pid-rs-open-font-self-test-")).resolve(
        strict=True
    )
    try:
        base_fonts = copy_font_fixture(test_root / "font-fixture", texmf_dist, texmf_debian)
        wrappers = test_root / "wrappers"
        wrappers.mkdir(mode=0o700)
        pandoc_marker = test_root / "pandoc-was-invoked"
        write_script(
            wrappers / "pandoc",
            "#!/bin/sh\nprintf 'invoked\\n' > "
            + repr(str(pandoc_marker))
            + "\nexit 97\n",
        )
        base_environment = dict(os.environ)
        base_environment["PATH"] = str(wrappers) + os.pathsep + base_environment.get("PATH", "")
        base_environment["FONTCONFIG_FILE"] = "/hostile/ambient-fontconfig.xml"
        base_environment["FONTCONFIG_PATH"] = "/hostile/ambient-fontconfig-path"
        base_environment["PANGOCAIRO_BACKEND"] = "coretext"

        accepted_output = test_root / "accepted-output"
        accepted = invoke(
            checker,
            accepted_output,
            base_fonts,
            environment=base_environment,
        )
        if accepted.returncode != 0:
            fail(f"accepted control failed: {(accepted.stdout + accepted.stderr)!r}")
        if {path.name for path in accepted_output.iterdir()} != EXPECTED_OUTPUTS:
            fail("accepted control published the wrong file set")
        if pandoc_marker.exists():
            fail("the accepted control invoked hostile Pandoc")
        receipt = json.loads(
            (accepted_output / "open-font-regeneration-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        if (
            receipt.get("pandoc_used") is not False
            or receipt.get("canonical_publication") is not False
            or receipt.get("repeatability", {}).get("raw_byte_equality") is not True
            or receipt.get("font_provenance", {})
            .get("source_sans_pro", {})
            .get("peeled_upstream_commit_locator")
            != "4bdf42c690a214a0f69410d71a6b889c5c4a695f"
        ):
            fail("accepted receipt lost its scope or provenance boundary")
        observed_license_artifacts = tuple(
            (entry.get("path"), entry.get("bytes"), entry.get("sha256"))
            for entry in receipt.get("license_artifacts", [])
        )
        if observed_license_artifacts != EXPECTED_LICENSE_ARTIFACTS:
            fail("accepted receipt lost exact local license-artifact custody")

        split_dist = test_root / "split-texmf-dist"
        split_debian = test_root / "split-texmf-debian"
        split_dist.mkdir()
        split_debian.mkdir()
        for relative, _expected_hash, may_use_debian in EXPECTED_FONTS:
            split_root = split_debian if may_use_debian else split_dist
            split_target = split_root / relative
            split_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base_fonts / relative, split_target)
        split_output = test_root / "split-layout-output"
        split_result = invoke(
            checker,
            split_output,
            split_dist,
            environment=base_environment,
            extra=["--texmf-debian", str(split_debian)],
        )
        if split_result.returncode != 0:
            fail(f"accepted split-layout control failed: {(split_result.stdout + split_result.stderr)!r}")
        split_receipt = json.loads(
            (split_output / "open-font-regeneration-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        split_roots = {
            entry["filename"]: entry["source_root"] for entry in split_receipt["fonts"]
        }
        if any(
            split_roots[Path(relative).name]
            != ("texmf-debian" if may_use_debian else "texmf-dist")
            for relative, _expected_hash, may_use_debian in EXPECTED_FONTS
        ):
            fail("accepted split-layout receipt recorded the wrong font roots")
        if pandoc_marker.exists():
            fail("the accepted split-layout control invoked hostile Pandoc")

        expect_reject(
            "relative output",
            checker,
            Path("relative-output"),
            base_fonts,
            "output directory is not an exact canonical absolute path",
            environment=base_environment,
        )
        existing_output = test_root / "existing-output"
        existing_output.mkdir()
        result = invoke(
            checker,
            existing_output,
            base_fonts,
            environment=base_environment,
        )
        if result.returncode == 0 or "output directory already exists" not in (
            result.stdout + result.stderr
        ):
            fail("existing-output hostile case was not rejected")

        repository_output = repository_root / ".open-font-self-test-output-must-not-exist"
        if repository_output.exists() or repository_output.is_symlink():
            fail("reserved repository-output test path already exists")
        expect_reject(
            "repository output",
            checker,
            repository_output,
            base_fonts,
            "output directory must be outside the repository",
            environment=base_environment,
        )

        symlink_target = test_root / "symlink-target"
        symlink_target.mkdir()
        symlink_output = test_root / "symlink-output"
        symlink_output.symlink_to(symlink_target, target_is_directory=True)
        result = invoke(
            checker,
            symlink_output,
            base_fonts,
            environment=base_environment,
        )
        if result.returncode == 0 or "contains a symbolic or non-canonical component" not in (
            result.stdout + result.stderr
        ):
            fail("symbolic output was not rejected")

        root_symlink = test_root / "font-root-symlink"
        root_symlink.symlink_to(base_fonts, target_is_directory=True)
        expect_reject(
            "symbolic font root",
            checker,
            test_root / "symbolic-root-output",
            root_symlink,
            "TEXMFDIST contains a symbolic or non-canonical component",
            environment=base_environment,
        )

        hash_fonts = copy_font_fixture(test_root / "hash-fonts", texmf_dist, texmf_debian)
        hash_target = hash_fonts / EXPECTED_FONTS[0][0]
        mutated = bytearray(hash_target.read_bytes())
        mutated[0] ^= 1
        hash_target.write_bytes(mutated)
        expect_reject(
            "font hash mutation",
            checker,
            test_root / "hash-output",
            hash_fonts,
            "font hash mismatch for SourceSansPro-Regular.otf",
            environment=base_environment,
        )

        symlink_fonts = copy_font_fixture(test_root / "symlink-fonts", texmf_dist, texmf_debian)
        symlink_leaf = symlink_fonts / EXPECTED_FONTS[0][0]
        symlink_copy = test_root / "font-outside-admitted-path.otf"
        shutil.copyfile(symlink_leaf, symlink_copy)
        symlink_leaf.unlink()
        symlink_leaf.symlink_to(symlink_copy)
        expect_reject(
            "symbolic font leaf",
            checker,
            test_root / "symlink-font-output",
            symlink_fonts,
            "font SourceSansPro-Regular.otf from texmf-dist is not a direct regular file",
            environment=base_environment,
        )

        def copy_license_checker_fixture(label: str) -> tuple[Path, Path]:
            fixture_root = test_root / label
            fixture_checker = (
                fixture_root
                / "scripts/regenerate-mathematical-results-guide-open-font-figures.py"
            )
            fixture_checker.parent.mkdir(parents=True)
            shutil.copyfile(checker, fixture_checker)
            for relative, _expected_bytes, _expected_hash in EXPECTED_LICENSE_ARTIFACTS:
                source_path = repository_root / relative
                target_path = fixture_root / relative
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_path, target_path)
            return fixture_root, fixture_checker

        license_hash_root, license_hash_checker = copy_license_checker_fixture(
            "license-hash-fixture"
        )
        license_hash_path = license_hash_root / EXPECTED_LICENSE_ARTIFACTS[0][0]
        license_hash_bytes = bytearray(license_hash_path.read_bytes())
        license_hash_bytes[0] ^= 1
        license_hash_path.write_bytes(license_hash_bytes)
        expect_reject(
            "license evidence hash mutation",
            license_hash_checker,
            test_root / "license-hash-output",
            base_fonts,
            "font-license evidence bytes changed for",
            environment=base_environment,
        )

        license_missing_root, license_missing_checker = copy_license_checker_fixture(
            "license-missing-fixture"
        )
        (license_missing_root / EXPECTED_LICENSE_ARTIFACTS[1][0]).unlink()
        expect_reject(
            "missing license evidence",
            license_missing_checker,
            test_root / "license-missing-output",
            base_fonts,
            "cannot stat font-license evidence",
            environment=base_environment,
        )

        license_symlink_root, license_symlink_checker = copy_license_checker_fixture(
            "license-symlink-fixture"
        )
        license_symlink_path = license_symlink_root / EXPECTED_LICENSE_ARTIFACTS[2][0]
        license_symlink_target = test_root / "license-evidence-outside-fixture.txt"
        shutil.copyfile(license_symlink_path, license_symlink_target)
        license_symlink_path.unlink()
        license_symlink_path.symlink_to(license_symlink_target)
        expect_reject(
            "symbolic license evidence",
            license_symlink_checker,
            test_root / "license-symlink-output",
            base_fonts,
            "is not a direct regular file",
            environment=base_environment,
        )

        real_fc_list = Path(shutil.which("fc-list") or "").resolve(strict=True)
        extra_inventory = wrappers / "fc-list-hostile"
        write_script(
            extra_inventory,
            "#!/bin/sh\n"
            + repr(str(real_fc_list))
            + ' "$@" || exit $?\nprintf \'/hostile/extra.otf\\tHostileFont\\n\'\n',
        )
        expect_reject(
            "extra Fontconfig inventory",
            checker,
            test_root / "inventory-output",
            base_fonts,
            "isolated Fontconfig inventory changed",
            environment=base_environment,
            extra=["--fc-list", str(extra_inventory)],
        )

        hostile_match = wrappers / "fc-match-hostile"
        write_script(
            hostile_match,
            "#!/bin/sh\nprintf '/hostile/wrong.otf\\tHostileFont\\n'\n",
        )
        expect_reject(
            "wrong Fontconfig selection",
            checker,
            test_root / "selection-output",
            base_fonts,
            "Fontconfig selected the wrong program",
            environment=base_environment,
            extra=["--fc-match", str(hostile_match)],
        )

        real_rsvg = Path(shutil.which("rsvg-convert") or "").resolve(strict=True)
        mutate_config = wrappers / "rsvg-mutate-config"
        write_script(
            mutate_config,
            "#!/bin/sh\n"
            "if [ \"${1-}\" = '--version' ]; then exec "
            + repr(str(real_rsvg))
            + ' "$@"; fi\n'
            + repr(str(real_rsvg))
            + ' "$@" || exit $?\nprintf \'<!-- hostile -->\\n\' >> "$FONTCONFIG_FILE"\n',
        )
        expect_reject(
            "Fontconfig mutation during render",
            checker,
            test_root / "config-mutation-output",
            base_fonts,
            "Fontconfig configuration changed",
            environment=base_environment,
            extra=["--rsvg-convert", str(mutate_config)],
        )

        nondeterministic = wrappers / "rsvg-nondeterministic"
        write_script(
            nondeterministic,
            "#!/bin/sh\n"
            "if [ \"${1-}\" = '--version' ]; then exec "
            + repr(str(real_rsvg))
            + ' "$@"; fi\n'
            + repr(str(real_rsvg))
            + ' "$@" || exit $?\n'
            "for argument in \"$@\"; do\n"
            "  case \"$argument\" in\n"
            "    --output=*run-2*) printf '%% hostile second pass\\n' >> \"${argument#--output=}\" ;;\n"
            "  esac\n"
            "done\n",
        )
        expect_reject(
            "non-deterministic second render",
            checker,
            test_root / "nondeterministic-output",
            base_fonts,
            "is not byte-reproducible across independent render passes",
            environment=base_environment,
            extra=["--rsvg-convert", str(nondeterministic)],
        )
    finally:
        shutil.rmtree(test_root)

    print("OK: open-font figure regenerator accepted 2 controls and rejected 14 hostile cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
