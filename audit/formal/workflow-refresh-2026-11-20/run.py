"""Record two sequential executions of the repository's registered workflow PDF producer."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time


STEM = "mathematical-problem-solving-workflow"
PDF = "output/pdf/" + STEM + ".pdf"
RECEIPT = "output/pdf/" + STEM + ".rendering-receipt.tsv"
GATE = "scripts/check-mathematical-workflow-pdf.sh"
MANIFEST = Path(__file__).with_name("inputs.json")
PIN = "ddfc44e41b07bbcadb7bc45ee521d55602c0a279226cf28d84bc4798f33f5080"
FIGURE_DIR = "audit/formal/latex/figures/mathematical-workflow/"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def demand(condition, detail):
    if not condition:
        raise ValueError(detail)


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root, table, field):
    identities = {}
    for relative, record in table.items():
        path = root / relative
        metadata = path.lstat()
        demand(path.resolve() == path and stat.S_ISREG(metadata.st_mode), relative)
        executable = bool(metadata.st_mode & 0o111)
        demand(executable == (record["mode"] == "100755"), f"mode mismatch: {relative}")
        actual = digest(path)
        demand(actual == record[field], f"{field} digest mismatch: {relative}")
        identities[relative] = actual
    return identities


def copy_observed(tmp, result):
    # The official program removes temporary output on exit. Read each fixed-point file
    # after its pass marker so a later gate failure can be diagnosed from genuine bytes.
    for base in tmp.glob("pid-rs-mathematical-workflow-pdf.*"):
        for build in ("build-a", "build-b"):
            source = base / build
            out = result / build
            if out.exists() or not (source / "pass-count.txt").is_file():
                continue
            try:
                evidence = {name: (source / name).read_bytes() for name in (
                    "pass-count.txt", STEM + ".pdf", "pid-rs-markdown-gc-receipt.tsv"
                )}
            except FileNotFoundError:
                continue
            out.mkdir()
            for name, data in evidence.items():
                (out / name).write_bytes(data)


def official(root, result, table):
    result.mkdir()
    arrived = result / "observed-unadjudicated"
    arrived.mkdir()
    with tempfile.TemporaryDirectory(prefix="workflow-refresh-", dir=os.environ["RUNNER_TEMP"]) as t:
        private = Path(t)
        for dirname in ("tmp", "config", "cache"):
            (private / dirname).mkdir(mode=0o700)
        env = {
            "PATH": os.environ["pythonLocation"] + "/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin",
            "TMPDIR": str(private / "tmp"), "XDG_CONFIG_HOME": str(private / "config"),
            "XDG_CACHE_HOME": str(private / "cache"), "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
        }
        started = time.monotonic()
        with (result / "stdout.txt").open("wb") as stdout, (result / "stderr.txt").open("wb") as stderr:
            with subprocess.Popen(["/usr/bin/bash", "--noprofile", "--norc", GATE, "--refresh"],
                                  cwd=root, env=env, stdout=stdout, stderr=stderr) as child:
                while child.poll() is None:
                    copy_observed(private / "tmp", arrived)
                    time.sleep(0.5)
                code = child.returncode
    detail = {"exit": code, "seconds": round(time.monotonic() - started, 3)}
    status = result / "official.json"
    save_json(status, detail)
    if code or (result / "stderr.txt").stat().st_size:
        detail["result"] = "failed"
        save_json(status, detail)
        return None
    demand("UPDATED: the workflow PDF" in (result / "stdout.txt").read_text(), "missing official success")
    official_products = result / "official-products"
    outputs = [PDF, RECEIPT] + [name for name in table if name.startswith(FIGURE_DIR) and name.endswith(".pdf")]
    demand(len(outputs) == 6, "publication product count")
    expected = digest(root / PDF)
    demand((root / RECEIPT).read_text().splitlines()[1] == "pdf_sha256\t" + expected, "PDF and rendering receipt differ")
    for name in outputs:
        target = official_products / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
        demand(digest(target) == digest(root / name), name)
    detail.update(result="passed", products={name: digest(official_products / name) for name in outputs})
    save_json(status, detail)
    return official_products / PDF


def available_pdf(official_pdf, result):
    if official_pdf:
        return official_pdf
    observed = result / "observed-unadjudicated"
    a, b = (observed / name / (STEM + ".pdf") for name in ("build-a", "build-b"))
    if a.is_file() and b.is_file() and digest(a) == digest(b):
        return a
    return None


def render_compare(previous, current, out):
    p = subprocess.run
    normal = out / "normal-120dpi"
    normal.mkdir()
    page_files = {}
    texts = {}
    for label, pdf in (("previous", previous), ("current", current)):
        extracted = subprocess.check_output(["pdftotext", "-layout", pdf, "-"]).split(b"\f")
        demand(len(extracted) == 88 and not extracted[-1], f"expected 87 pages: {label}")
        texts[label] = extracted[:-1]
        for mode in ("color", "gray"):
            directory = normal / label / mode
            directory.mkdir(parents=True)
            args = ["-gray"] if mode == "gray" else []
            p(["pdftoppm", "-png", *args, "-r", "120", pdf, directory / "page"], check=True)
            pages = sorted(directory.glob("page-*.png"))
            demand([int(f.stem.split("-")[1]) for f in pages] == list(range(1, 88)), f"render pages: {label}/{mode}")
            page_files[label, mode] = pages
    rows = []
    changed = set()
    for mode in ("color", "gray"):
        for pg, (one, two) in enumerate(zip(page_files["previous", mode], page_files["current", mode], strict=True), 1):
            d1, d2 = digest(one), digest(two)
            rows.append({"mode": mode, "page": pg, "previous": d1, "current": d2})
            if d1 != d2:
                changed.add(pg)
    text_delta = [pg for pg, (one, two) in enumerate(zip(texts["previous"], texts["current"], strict=True), 1) if one != two]
    save_json(out / "page-comparison.json", {"page_digests": rows, "raster_changed": sorted(changed), "layout_text_changed": text_delta})
    focus = sorted(changed | set(text_delta) | {73})
    detail = out / "detail-300dpi"
    detail.mkdir()
    for label, pdf in (("previous", previous), ("current", current)):
        for pg in focus:
            for mode, args in (("color", []), ("gray", ["-gray"])):
                target = detail / f"{label}-{mode}-{pg:02}"
                p(["pdftoppm", "-png", *args, "-r", "300", "-f", str(pg), "-l", str(pg), "-singlefile", pdf, target], check=True)
            (detail / f"{label}-{pg:02}.txt").write_bytes(texts[label][pg-1])
    save_json(out / "detail-sha256.json", {f.name: digest(f) for f in sorted(detail.glob("*.png"))})
    for name, pdf in (("previous", previous), ("current", current)):
        receipt = pdf.parent / Path(RECEIPT).name
        if not receipt.is_file():
            continue
        rows = list(csv.DictReader(receipt.read_text().splitlines()[4:], delimiter="\t"))
        demand(len(rows) == 174, "receipt page count")
        for row in rows:
            image = page_files[name, row["mode"]][int(row["page"]) - 1]
            demand(digest(image) == row["sha256"], f"additional render differs from official PNG: {name}/{row['mode']}/{row['page']}")


def main():
    mode, current_dir, previous_dir, results_dir = sys.argv[1:]
    current, previous, results = map(lambda p: Path(p).resolve(strict=True), (current_dir, previous_dir, results_dir))
    demand(mode in {"inputs", "refresh"} and digest(MANIFEST) == PIN, "request or input-register mismatch")
    table = json.loads(MANIFEST.read_text())
    demand(len(table) == 33 and sum(rec["input"] != rec["before"] for rec in table.values()) == 3, "input register shape")
    checked = {"current": verify(current, table, "input"), "previous": verify(previous, table, "before")}
    save_json(results / "source-receipt.json", checked)
    if mode == "inputs":
        return
    pages = {}
    accepted = {}
    for name, root in (("previous", previous), ("current", current)):
        result = results / name
        success = official(root, result, table)
        accepted[name] = success is not None
        pages[name] = available_pdf(success, result)
    terminal = {"official_refresh": accepted, "same_host_visual_comparison": "unavailable",
                "review_status": "requires actual page inspection"}
    path = results / "terminal.json"
    save_json(path, terminal)
    if all(pages.values()):
        try:
            render_compare(pages["previous"], pages["current"], results)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            terminal["same_host_visual_comparison"] = "failed"
            terminal["error"] = str(error)
            save_json(path, terminal)
            raise
        terminal["same_host_visual_comparison"] = "completed"
        save_json(path, terminal)
    demand(all(accepted.values()), "an official refresh failed; consult each official.json and retained diagnostics")


if __name__ == "__main__":
    main()
