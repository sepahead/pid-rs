"""Read the measured process fields and the registered command independently of its reported outcome."""
from fractions import Fraction
import importlib.util
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("observer_support", HERE / "support.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

RECEIPT_FIELDS = set("""
tag stage argv exit stop elapsed_seconds campaign_elapsed_seconds group_rss_sample_count
max_observed_group_rss_bytes direct_wait4_maxrss_bytes retained_before_receipt_bytes native_process_group
post_group_absent residual_after_wait4 stdout_sha256 stderr_sha256 stdout_bytes stderr_bytes
""".split())
STOPS = (None, "observed process-group RSS", "native or campaign time", "retained storage",
         "unreaped process-group member", "final native resource limit")
SETUP = "bind and provision"
FINAL = "final checks"


def clock(value):
    S.require(type(value) in (float, int) and 0 <= value <= (1 << 53) and math.isfinite(value), "finite clock")
    return Fraction(value)


def dispatches(ledger, names, terminal_elapsed):
    S.require(type(ledger) is list and len(ledger) <= len(names), "dispatch prefix")
    terminal = clock(terminal_elapsed)
    intervals = {}
    previous = Fraction(0)
    for index, record in enumerate(ledger):
        tag = names[index]
        S.require(type(record) is dict and set(record) == {"tag", "begin", "end"} and record["tag"] == tag,
                  "ordered dispatch prefix")
        begin, end = clock(record["begin"]), clock(record["end"])
        S.require(previous <= begin < end <= terminal, "serial dispatch intervals inside campaign")
        intervals[tag] = (begin, end)
        previous = end
    return intervals


def receipt(row, tag, folder, interval):
    S.require(type(row) is dict and set(row) == RECEIPT_FIELDS and row["tag"] == tag and row["stage"] == S.STAGE,
              "complete native receipt "+tag)
    for field in ("group_rss_sample_count", "max_observed_group_rss_bytes", "direct_wait4_maxrss_bytes",
                  "retained_before_receipt_bytes", "native_process_group", "stdout_bytes", "stderr_bytes"):
        S.require(type(row[field]) is int and row[field] >= 0, "integer receipt field "+field)
    S.require(type(row["argv"]) is list and row["argv"] and all(type(v) is str and v for v in row["argv"]) and
              type(row["exit"]) is int and -127 <= row["exit"] <= 255 and row["native_process_group"] > 0 and
              type(row["residual_after_wait4"]) is bool and type(row["post_group_absent"]) is bool and
              row["stop"] in STOPS, "native process metadata "+tag)
    for stream in ("stdout", "stderr"):
        S.require(S.info(folder/stream) == {"bytes":row[stream+"_bytes"],"sha256":row[stream+"_sha256"]},
                  "native stream "+tag)
    elapsed = clock(row["elapsed_seconds"])
    end = clock(row["campaign_elapsed_seconds"])
    begin, finish = interval
    # The provider records its campaign endpoint after the process wait and a storage walk.
    # Its endpoint minus the process duration lies inside the enclosing serial dispatch.
    S.require(elapsed > 0 and begin <= end-elapsed < end <= finish, "native interval outside its serial dispatch "+tag)
    sample_count = row["group_rss_sample_count"]
    group, direct = row["max_observed_group_rss_bytes"], row["direct_wait4_maxrss_bytes"]
    S.require((sample_count > 0 or group == 0) and sample_count <= 1 + elapsed // Fraction(8,100) and
              group % 1024 == direct % 1024 == 0, "process sampler metadata "+tag)
    S.require(row["retained_before_receipt_bytes"] >= row["stdout_bytes"]+row["stderr_bytes"],
              "stream sizes exceed reported evidence bytes "+tag)


def coherent_stop(row, interval):
    """A stopped run may retain other violations. The first diagnostic can predate the final size scan."""
    reason = row["stop"]
    limit = S.SAFE_LIMITS
    if reason is None:
        S.require(row["post_group_absent"] and not row["residual_after_wait4"] and
                  max(row["max_observed_group_rss_bytes"],row["direct_wait4_maxrss_bytes"]) <= limit["group_rss_bytes"] and
                  row["retained_before_receipt_bytes"] <= limit["retained_bytes"] and
                  row["elapsed_seconds"] <= limit["subprocess_seconds"] and row["campaign_elapsed_seconds"] <= limit["campaign_seconds"],
                  "unreported resource or cleanup stop")
    elif reason == "observed process-group RSS":
        S.require(row["group_rss_sample_count"] > 0 and row["max_observed_group_rss_bytes"] > limit["group_rss_bytes"],
                  "unsupported process-group RSS stop")
    elif reason == "unreaped process-group member":
        S.require(row["residual_after_wait4"] or not row["post_group_absent"], "unsupported cleanup stop")
    elif reason == "native or campaign time":
        S.require(row["elapsed_seconds"] >= limit["subprocess_seconds"] or row["campaign_elapsed_seconds"] >= limit["campaign_seconds"],
                  "unsupported native or campaign time stop")

    elif reason == "final native resource limit":
        # The provider reads final size and checks its deadline before recording the campaign endpoint.
        # The dispatch begins no later than the provider call, so end-begin is an upper bound on time since call entry.
        begin,_ = interval
        end = clock(row["campaign_elapsed_seconds"])
        measured = []
        if row["direct_wait4_maxrss_bytes"] > limit["group_rss_bytes"]:
            measured.append("direct process peak")
        if row["retained_before_receipt_bytes"] > limit["retained_bytes"]:
            measured.append("final retained file lengths")
        if clock(row["elapsed_seconds"]) > limit["subprocess_seconds"]:
            measured.append("elapsed native duration")
        possible_time = end > limit["campaign_seconds"] or end-begin > limit["subprocess_seconds"]
        S.require(measured or possible_time, "final limit label has no possible resource condition")
        S.require(not row["residual_after_wait4"] and row["post_group_absent"] and
                  row["max_observed_group_rss_bytes"] <= limit["group_rss_bytes"], "earlier recorded stop precedes a final-only label")
        return {"measured_excess":measured,"time_may_have_crossed":possible_time,
                "interpretation":"final limit reported; exact instant of the final deadline check is absent"}
    elif reason == "retained storage":
        return {"interpretation":"provider reported a transient storage excess; the peak size was not retained"}
    return None if reason is None else {"interpretation":"reported by the fixed provider; compare the associated native measurements"}



def path(value):
    p = PurePosixPath(value)
    S.require(p.is_absolute() and not value.startswith("//") and p.as_posix() == value and ".." not in p.parts and "\\" not in value,
              "canonical absolute recorded path")
    return p


def execution_roots(execution):
    S.require(type(execution) is dict and set(execution)=={"workspace","runner_temp","python"} and
              all(type(v) is str for v in execution.values()), "launch execution directories")
    workspace, temp, python = (path(execution[name]) for name in ("workspace","runner_temp","python"))
    S.require(re.fullmatch(r"python3(?:\.[0-9]+)?",python.name) and not (temp.is_relative_to(workspace) or workspace.is_relative_to(temp)),
              "distinct launch directories and Python interpreter")
    return workspace, temp, python


class Commands:
    """Bind the archive, installed release and working directories to the workflow's exact argument grammar."""
    def __init__(self,execution):
        self.workspace,self.temp,self.python=execution_roots(execution)
        self.bin=self.temp/"index-observer-v4-stock/lean-4.34.1-linux/bin"
        self.result=self.temp/"index-observer-v4-evidence/result"

    def verify(self, tag, argv):
        if tag == "extract-official":
            S.require(len(argv) == 7 and argv[:4] == ["/usr/bin/tar","--zstd","--no-same-owner","-xf"] and argv[5] == "-C",
                      "stock extraction command")
            archive, stock = path(argv[4]), path(argv[6])
            S.require(archive == self.temp/"index-observer-v4-release.tar.zst" and stock == self.temp/"index-observer-v4-stock",
                      "fixed release and stock directories")
        elif tag in ("stock-version","stock-commit"):
            flag = "--version" if tag == "stock-version" else "--githash"
            S.require(argv == [str(self.bin/"lean"),flag], "stock identity command "+tag)
        elif tag == S.POST:
            S.require(len(argv) == 7 and path(argv[0])==self.python and
                      argv[1:4] == ["-I","-S","-B"] and path(argv[4]) == self.workspace/S.PACKAGE/"frames.py" and
                      argv[5:] == ["--result",str(self.result)], "same-capped offline postprocessor")
        else:
            kind, unit = tag.split("-",1)
            if kind == "fresh":
                S.require(argv == [str(self.bin/"leanchecker"),"--fresh",unit], "pinned fresh object "+unit)
            else:
                expected = [str(self.bin/"lean")] + (["--json"] if kind == "refuse" else [])
                expected += ["-DwarningAsError=true","-R",str(self.result/"sources"),"-o",str(self.result/"objects"/(unit+".olean")),unit+".lean"]
                S.require(argv == expected, "exact stock compiler "+unit)


def stock_text(tag, folder):
    if tag not in ("stock-version","stock-commit"):
        return True
    expected = S.STOCK_VERSION if tag == "stock-version" else S.STOCK_GIT
    return (folder/"stdout").read_bytes() == (expected+"\n").encode("ascii")


def stage(rows, index, tag, source, known):
    kind, unit = tag.split("-",1)
    name = unit+".lean"
    imports = [line.split()[1] for line in source[name].decode().splitlines() if line.startswith("import ")]
    local = {module+".olean":known[module+".olean"] for module in imports if module+".lean" in source}
    expected = {"kind":kind,"module":unit,"source":S.info_bytes(source[name]),"local_imports":local,"preceding":dict(known)}
    S.require(index < len(rows) and rows[index] == expected, "failed prefix prior objects or complete staged import/owner sequence "+tag)
    if kind == "fresh":
        S.require(unit+".olean" in known, "pinned fresh object "+unit)


def headers(items):
    """Check all ZipInfo descriptors before a byte is copied. This helper also accepts an in-memory descriptor list."""
    S.require(0 < len(items) <= 550 and len(set(x.filename for x in items)) == len(items), "unique ordinary ZIP members")
    expanded = 0
    for item in items:
        name = item.filename
        parsed = PurePosixPath(name)
        mode = stat.S_IFMT(item.external_attr >> 16)
        S.require(name == item.orig_filename and parsed.parts and parsed.as_posix() == name and not parsed.is_absolute() and
                  ".." not in parsed.parts and "\\" not in name and not (item.flag_bits & 1) and not item.is_dir() and
                  mode in (0,stat.S_IFREG) and not (item.external_attr & 0x10), "ordinary regular or unspecified ZIP file")
        S.require(type(item.file_size) is int and item.file_size >= 0, "ZIP member size")
        expanded += item.file_size
        S.require(expanded <= S.SAFE_LIMITS["retained_bytes"], "expanded ZIP ceiling")
    return expanded


def copy_registered(src, destination):
    """Use a new destination after the outer job and archive identity have been checked."""
    items = src.infolist()
    headers(items)
    for item in items:
        dest = destination / item.filename
        dest.parent.mkdir(parents=True,exist_ok=True)
        with src.open(item) as incoming, dest.open("xb") as outgoing:
            shutil.copyfileobj(incoming,outgoing,1 << 17)
        S.require(dest.stat().st_size == item.file_size, "ordinary ZIP content size")
