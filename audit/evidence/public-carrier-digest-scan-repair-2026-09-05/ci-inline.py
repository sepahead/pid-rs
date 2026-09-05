import json
import subprocess
import tempfile
from pathlib import Path

config = Path.cwd() / ".gitleaks.toml"
ignore = Path.cwd() / ".gitleaksignore"
expected_ignored_fingerprints = (
    "9dcdf32f18076eefc768194079b4abf437009737:"
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md:generic-api-key:19",
    "5b4f3758d688dfd06d6072374922b00abad27ecf:"
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md:generic-api-key:19",
)
actual_ignored_fingerprints = tuple(ignore.read_text(encoding="utf-8").splitlines())
if actual_ignored_fingerprints != expected_ignored_fingerprints:
    raise SystemExit(
        "historical public-prose ignore fingerprints changed: "
        f"{actual_ignored_fingerprints!r}"
    )
# Construct a high-entropy-looking public digest without embedding a 64-hex fixture in CI.
digest = "0123456789abcdef" * 4
quote = '"'
pid3_public_prose = (
    "18-key serialization order, "
    "108-coordinate certificate, resource policy, independent-verification"
)
pid3_public_preceding = (
    "The canonical count-table transport, natural-log specialization,"
)
positive_only = (
    (
        "audit/evidence/repository-snapshot.json",
        f'{quote}api_projection_sha256{quote}: {quote}{digest}{quote},',
    ),
    (
        "release-scope-1.0.json",
        f'{quote}public_api_snapshot_sha256{quote}: {quote}{digest}{quote},',
    ),
    (
        "audit/api/public-api/pid-core-signature-revisions.json",
        f'{quote}public_api_snapshot_sha256{quote}: {quote}{digest}{quote},',
    ),
    (
        "audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-context.md",
        f'123 {quote}public_api_snapshot_sha256{quote}: {quote}{digest}{quote},',
    ),
    (
        "claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md",
        pid3_public_preceding + "\n" + pid3_public_prose,
    ),
)
cases = (
    (
        "audit/evidence/workflow-pdf-lualatex-format-hosted-receipt-2026-08-06.json",
        f'{quote}job_api_sha256{quote}: {quote}{digest}{quote},',
        (
            f'job_api_sha256 = {quote}{digest}{quote},',
            f'{quote}job_api_sha256: {quote}{digest}{quote},',
            f'job_api_sha256{quote}: {quote}{digest}{quote},',
            f'{quote}job_api_sha256{quote} = {quote}{digest}{quote},',
        ),
    ),
    (
        "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json",
        f'{quote}mutant_token_stream_sha256{quote}: {quote}{digest}{quote},',
        (
            f'mutant_token_stream_sha256 = {quote}{digest}{quote},',
            f'{quote}mutant_token_stream_sha256: {quote}{digest}{quote},',
            f'mutant_token_stream_sha256{quote}: {quote}{digest}{quote},',
            f'{quote}token_stream_sha256{quote}: {quote}{digest}{quote},',
        ),
    ),
    (
        "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.json",
        f'{quote}token_stream_sha256{quote}: {quote}{digest}{quote},',
        (
            f'token_stream_sha256 = {quote}{digest}{quote},',
            f'{quote}token_stream_sha256: {quote}{digest}{quote},',
            f'token_stream_sha256{quote}: {quote}{digest}{quote},',
            f'{quote}mutant_token_stream_sha256{quote}: {quote}{digest}{quote},',
        ),
    ),
    (
        "scripts/check-ksg-harmonic-revision.py",
        f'{quote}mutant_token_stream_sha256{quote}: {quote}{digest}{quote},',
        (
            f'mutant_token_stream_sha256 = {quote}{digest}{quote},',
            f'{quote}mutant_token_stream_sha256: {quote}{digest}{quote},',
            f'mutant_token_stream_sha256{quote}: {quote}{digest}{quote},',
            f'{quote}token_stream_sha256{quote}: {quote}{digest}{quote},',
        ),
    ),
    (
        "scripts/check-z3-ksg-integer-harmonic.py",
        f'token_stream_sha256={quote}{digest}{quote},',
        (
            f'{quote}token_stream_sha256{quote}: {quote}{digest}{quote},',
            f'{quote}token_stream_sha256 = {quote}{digest}{quote},',
            f'token_stream_sha256{quote} = {quote}{digest}{quote},',
            f'mutant_token_stream_sha256 = {quote}{digest}{quote},',
        ),
    ),
)

def scan(files):
    with tempfile.TemporaryDirectory(prefix="pid-rs-gitleaks-self-test-") as raw:
        root = Path(raw) / "source"
        root.mkdir()
        for relative, line in files:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(line + "\n", encoding="utf-8")
        report = Path(raw) / "report.json"
        completed = subprocess.run(
            (
                "/tmp/gitleaks",
                "dir",
                ".",
                "--config",
                str(config),
                "--gitleaks-ignore-path",
                "/dev/null",
                "--redact",
                "--no-banner",
                "--report-format",
                "json",
                "--report-path",
                str(report),
            ),
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        findings = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
        return completed.returncode, findings, completed.stderr

intended_files = positive_only + tuple((path, intended) for path, intended, _ in cases)
code, findings, stderr = scan(intended_files)
if code != 0 or findings:
    raise SystemExit(f"intended public-digest controls were rejected: {stderr}")

detected = 0
for path, line in intended_files:
    key = next(
        candidate
        for candidate in (
            "public_api_snapshot_sha256",
            "api_projection_sha256",
            "job_api_sha256",
            "mutant_token_stream_sha256",
            "token_stream_sha256",
            pid3_public_prose,
        )
        if candidate in line
    )
    original_negatives = (
        ("nearby_path", path + ".nearby", line),
        ("nearby_key", path, line.replace(key, "nearby_" + key, 1)),
        (
            "nonhex_value",
            path,
            line.replace(digest, "g" + digest[1:], 1)
            if digest in line
            else line.replace("108-coordinate", "109-coordinate", 1),
        ),
        (
            "secret_prefix",
            path,
            line.replace(digest, "secret_" + digest, 1)
            if digest in line
            else line.replace("18-key", "secret_18-key", 1),
        ),
    )
    for negative_class, negative_path, negative_line in original_negatives:
        code, findings, stderr = scan(((negative_path, negative_line),))
        if code != 1 or len(findings) != 1 or findings[0].get("RuleID") != "generic-api-key":
            raise SystemExit(
                f"public-digest {negative_class} control escaped for {path}: "
                f"exit={code}, findings={len(findings)}, stderr={stderr}"
            )
        detected += 1

prose_path = "claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1.md"
for malformed_prose in (
    "prefix " + pid3_public_prose,
    "19-key serialization order, " + "108-coordinate certificate",
    pid3_public_prose + " suffix",
):
    code, findings, stderr = scan(
        ((prose_path, pid3_public_preceding + "\n" + malformed_prose),)
    )
    if code != 1 or len(findings) != 1 or findings[0].get("RuleID") != "generic-api-key":
        raise SystemExit(
            "malformed public-prose control escaped: "
            f"exit={code}, findings={len(findings)}, stderr={stderr}"
        )
    detected += 1

for path, _, malformed in cases:
    for line in malformed:
        code, findings, stderr = scan(((path, line),))
        if code != 1 or len(findings) != 1 or findings[0].get("RuleID") != "generic-api-key":
            raise SystemExit(
                f"malformed public-digest control escaped for {path}: "
                f"exit={code}, findings={len(findings)}, stderr={stderr}"
            )
        detected += 1
if detected != 63:
    raise SystemExit(f"expected 63 rejected controls, observed {detected}")
print("Gitleaks narrow-allowlist self-test passed: 10 intended, 63 rejected")

# Keep the existing 10 intended and 63 rejected controls above unchanged.
# This fixture serializes public Fin-3 antichain keys; it contains no credential.
import hashlib
import itertools

carrier_keys = (
    "01", "02", "03", "04", "05", "06", "07", "01+02", "01+04", "01+06",
    "02+04", "02+05", "03+04", "03+05", "03+06", "05+06", "01+02+04", "03+05+06",
)
carrier_digest = hashlib.sha256(
    json.dumps(list(carrier_keys), separators=(",", ":")).encode("ascii")
).hexdigest()
carrier_key = "carrier_keys_sha256"
carrier_line = f'{quote}{carrier_key}{quote}: {quote}{carrier_digest}{quote}'
carrier_paths = (
    "audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4.json",
    "scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py",
)
carrier_intended = 0
carrier_rejected = 0
carrier_adjacent = 0

for path in carrier_paths:
    for intended in (
        carrier_line,
        "    " + carrier_line + ",",
        "\t" + carrier_line + "\t",
        "{\n  " + carrier_line + ',\n  "description": "public carrier evidence"\n}',
        "EXPECTED_DIGESTS: dict[str, str] = {\n    " + carrier_line + ',\n    "other": "public"\n}',
    ):
        code, findings, stderr = scan(((path, intended),))
        if code != 0 or findings:
            raise SystemExit(f"public carrier context was rejected for {path}: {stderr}")
        carrier_intended += 1

    synthetic_token_line = f'api_key = {quote}secret_{digest}{quote}'
    hostile_lines = (
        ("changed_digest", carrier_line.replace(carrier_digest, digest), 1, None),
        ("changed_last_hex", carrier_line.replace(carrier_digest, carrier_digest[:-1] + "3"), 1, None),
        ("nonhex", carrier_line.replace(carrier_digest, carrier_digest[:-1] + "g"), 1, None),
        ("nearby_key", carrier_line.replace(carrier_key, "neighbor_" + carrier_key), 1, None),
        ("suffix_key", carrier_line.replace(carrier_key, carrier_key + "_backup"), 1, None),
        ("uppercase_key", carrier_line.replace(carrier_key, carrier_key.upper()), 1, None),
        ("equals", carrier_line.replace(":", " ="), 1, None),
        ("unquoted_key", carrier_line.replace(quote + carrier_key + quote, carrier_key), 1, None),
        ("single_quoted_key", carrier_line.replace(quote + carrier_key + quote, "'" + carrier_key + "'"), 1, None),
        ("prefix", "prefix " + carrier_line, 1, None),
        ("suffix_comment", carrier_line + " # public carrier", 1, None),
        ("missing_value_quote", carrier_line[:-1], 1, None),
        ("extra_comma", carrier_line + ",,", 1, None),
        ("adjacent_before", synthetic_token_line + "\n" + carrier_line, 1, 1),
        ("adjacent_after", carrier_line + "\n" + synthetic_token_line, 1, 2),
        ("adjacent_same_line", carrier_line + ", " + synthetic_token_line, 2, 1),
    )
    hostile_paths = (
        ("suffix_path", path + ".nearby", carrier_line, 1, None),
        ("prefix_path", "nearby/" + path, carrier_line, 1, None),
        ("renamed_path", path.replace("v4.", "v5."), carrier_line, 1, None),
    )
    for case_name, case_path, line, expected_count, token_line in (
        tuple((name, path, line, count, token_line) for name, line, count, token_line in hostile_lines)
        + hostile_paths
    ):
        code, findings, stderr = scan(((case_path, line),))
        if (
            code != 1
            or len(findings) != expected_count
            or any(finding.get("RuleID") != "generic-api-key" for finding in findings)
            or (
                token_line is not None
                and not any(
                    finding["StartLine"] <= token_line <= finding["EndLine"]
                    for finding in findings
                )
            )
        ):
            raise SystemExit(
                f"carrier {case_name} control escaped for {path}: "
                f"exit={code}, findings={len(findings)}, stderr={stderr}"
            )
        carrier_rejected += 1

    public_line = "    " + carrier_line + ","
    adjacent_forms = (
        ("json_api", f'    "api_key": "secret_{digest}",'),
        ("json_token", f'    "access_token": "secret_{digest}",'),
        ("same_key_changed_value", f'    "{carrier_key}": "{digest}",'),
        ("neighbor_key", f'    "neighbor_{carrier_key}": "{digest}",'),
        ("python_api", f'api_key = "secret_{digest}"'),
        ("split_json_value", f'"api_key":\n"secret_{digest}"'),
        ("split_python_value", f'api_key =\n"secret_{digest}"'),
        ("split_key_colon", f'"api_key"\n: "secret_{digest}"'),
        ("unquoted_api", f'api_key = secret_{digest}'),
        ("json_no_indent", f'"api_key": "secret_{digest}",'),
    )
    for (case_name, token), direction, gap in itertools.product(
        adjacent_forms, ("before", "after"), ("\n", "\n\n")
    ):
        line = token + gap + public_line if direction == "before" else public_line + gap + token
        token_lines = tuple(
            number for number, physical_line in enumerate(line.splitlines(), 1)
            if digest in physical_line
        )
        code, findings, stderr = scan(((path, line),))
        if (
            code != 1
            or len(findings) != 1
            or findings[0].get("RuleID") != "generic-api-key"
            or not token_lines
            or not any(
                findings[0]["StartLine"] <= number <= findings[0]["EndLine"]
                for number in token_lines
            )
        ):
            raise SystemExit(
                f"carrier adjacent {case_name}/{direction}/gap{len(gap)} control escaped "
                f"for {path}: exit={code}, findings={len(findings)}, stderr={stderr}"
            )
        carrier_adjacent += 1

code, findings, stderr = scan(((".gitleaks.toml", config.read_text(encoding="utf-8")),))
if code != 0 or findings:
    raise SystemExit(f"public carrier policy text produced a new finding: {stderr}")
if (carrier_intended, carrier_rejected, carrier_adjacent) != (10, 38, 80):
    raise SystemExit(
        "carrier policy control inventory drifted: "
        f"{carrier_intended} intended, {carrier_rejected} rejected, {carrier_adjacent} adjacent"
    )
print(
    "Gitleaks carrier-policy self-test passed: 10 intended contexts, 38 rejected shapes/paths, "
    "80 retained adjacent credentials, 1 policy-text control"
)
