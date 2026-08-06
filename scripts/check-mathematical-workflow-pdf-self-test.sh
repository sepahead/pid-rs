#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="${BASH_SOURCE[0]%/*}"
if [[ "$SCRIPT_DIRECTORY" == "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIRECTORY="."
fi
ROOT="$(cd "$SCRIPT_DIRECTORY/.." && pwd -P)"
CHECK_NAME="mathematical workflow PDF checker self-test"
EXPECTED_PAGES=51
EXPECTED_DPI=120

TMP_PARENT_RAW="${TMPDIR:-/tmp}"
if [[ ! -d "$TMP_PARENT_RAW" ]]; then
  echo "$CHECK_NAME: temporary root is not a directory" >&2
  exit 2
fi
TMP_PARENT="$(cd "$TMP_PARENT_RAW" && pwd -P)"
case "$TMP_PARENT" in
  / | "")
    echo "$CHECK_NAME: refusing an ambiguous temporary root" >&2
    exit 2
    ;;
esac
TEST_ROOT="$(mktemp -d "$TMP_PARENT/pid-rs-workflow-pdf-self-test.XXXXXX")"
TEST_ROOT="$(cd "$TEST_ROOT" && pwd -P)"

cleanup() {
  local status=$?
  trap - EXIT
  case "$TEST_ROOT" in
    "$TMP_PARENT"/pid-rs-workflow-pdf-self-test.*)
      chmod -R u+w "$TEST_ROOT" 2>/dev/null || true
      if ! rm -rf -- "$TEST_ROOT"; then
        echo "$CHECK_NAME: failed to remove the exact temporary test root: $TEST_ROOT" >&2
        status=1
      fi
      ;;
    *)
      echo "$CHECK_NAME: refusing ambiguous temporary cleanup: $TEST_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap cleanup EXIT

PASS_COUNT=0
RESULT_LOG="$TEST_ROOT/result.log"
# C3 adds six mechanically separated control families to the 194-control predecessor suite.  A
# moving aggregate can hide accidental deletion from one family behind addition to another, so the
# final gate freezes all seven partitions and the 313-control total.  Keep these counters in
# portable scalar shell variables: the supported Darwin system Bash does not provide associative
# arrays.
C3_ACTIVE_FAMILY=""
C3_BOUNDED_PROBE_COUNT=0
C3_ENTRY_WRAPPER_COUNT=0
C3_RUNTIME_MAP_COUNT=0
C3_FLS_MAP_PATH_COUNT=0
C3_EXECUTABLE_CUSTODY_COUNT=0
C3_FORMAT_CUSTODY_COUNT=0
EXPECTED_PREDECESSOR_CONTROL_COUNT=194
EXPECTED_C3_BOUNDED_PROBE_COUNT=37
EXPECTED_C3_ENTRY_WRAPPER_COUNT=17
EXPECTED_C3_RUNTIME_MAP_COUNT=7
EXPECTED_C3_FLS_MAP_PATH_COUNT=8
EXPECTED_C3_EXECUTABLE_CUSTODY_COUNT=3
EXPECTED_C3_FORMAT_CUSTODY_COUNT=47
EXPECTED_TOTAL_CONTROL_COUNT=313
# This suite never compiles the 51-page report.  Its locally observed slowest focused PDF-parser
# control completes in about 16 seconds; the common wrapper's three-minute decision deadline
# retains more than 11x observed slack for hosted runners.  Publication, readiness, cleanup,
# absence polling, and reaping are separately bounded stages under the declared progress premise.
CONTROL_TIMEOUT_SECONDS=180
# Test-only, internally assigned scheduling hook for the release-readiness race control.  The
# production path keeps this at zero; the dedicated control sets it to one for exactly one probe.
C3_RELEASE_READY_DELAY_SECONDS=0
PROBE_CLEANUP_PYTHON="$(command -v python3)"
PS_COMMAND="$(command -v ps)"
SELF_TEST_BASH="$(type -P bash)"
KPSEWHICH_COMMAND="$(command -v kpsewhich || true)"
readonly SELF_TEST_BASH KPSEWHICH_COMMAND
for resolved_command in \
  "$PROBE_CLEANUP_PYTHON" "$PS_COMMAND" "$SELF_TEST_BASH" "$KPSEWHICH_COMMAND"; do
  if [[ "$resolved_command" != /* || ! -x "$resolved_command" ]]; then
    echo "$CHECK_NAME: cannot resolve exact cleanup commands" >&2
    exit 2
  fi
done

reset_result_log() {
  python3 -I -S - "$RESULT_LOG" <<'PY'
import os
from pathlib import Path
import stat
import sys


path = Path(sys.argv[1])
for required_flag in ("O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK"):
    if not hasattr(os, required_flag):
        raise SystemExit(f"result-log reset lacks required {required_flag}")
flags = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_NOFOLLOW
    | os.O_CLOEXEC
    | os.O_NONBLOCK
)
descriptor = os.open(path, flags, 0o600)
try:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit("result log is not a single-link regular file")
    leaf = path.lstat()
    fields = ("st_dev", "st_ino", "st_mode", "st_nlink")
    if tuple(getattr(before, field) for field in fields) != tuple(
        getattr(leaf, field) for field in fields
    ):
        raise SystemExit("result-log path identity differs from its descriptor")
    os.ftruncate(descriptor, 0)
    os.fchmod(descriptor, 0o600)
    os.fsync(descriptor)
    after = os.fstat(descriptor)
    stable_fields = ("st_dev", "st_ino", "st_nlink", "st_size")
    if tuple(getattr(after, field) for field in stable_fields) != (
        before.st_dev,
        before.st_ino,
        1,
        0,
    ):
        raise SystemExit("result-log identity changed during descriptor truncation")
finally:
    os.close(descriptor)
PY
}

prove_probe_group_absent() {
  python3 -I -S - "$1" <<'PY'
import os
import sys
import time


process_group = int(sys.argv[1])
for _ in range(100):
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        break
    except PermissionError:
        pass
    time.sleep(0.05)
else:
    raise SystemExit("probe process group remains allocated after bounded cleanup")
PY
}

run_bounded_probe() {
  local timeout_seconds="$1"
  shift
  local decision_root="$TEST_ROOT/probe-decision-$PASS_COUNT"
  local decision_claim_second=-1
  local decision_absolute_deadline
  local decision_publication_grace_seconds=5
  local decision_record_kind=""
  local decision_record_custody_status
  local probe_status_record="$decision_root/probe-status"
  local release_ready_marker="$decision_root/release-ready"
  local timeout_marker="$decision_root/timeout"
  local watchdog_error_marker="$decision_root/watchdog-error"
  local group_cleanup_status
  local probe_pid
  local probe_status
  local probe_wait_status
  local group_release_failure=""
  local watchdog_pid
  if [[ -e "$decision_root" ]]; then
    fail "bounded probe decision root already exists: $decision_root"
  fi
  (
    decision_absolute_deadline=$((SECONDS + timeout_seconds + decision_publication_grace_seconds))
    # Monitor mode gives the probe anchor and watchdog distinct process groups.  The anchor turns
    # monitor mode off before invoking the control, so every ordinary child remains in the anchored
    # probe group.  Completion and timeout race through one exclusive decision directory.  A
    # successful claimant publishes at most one canonical record; a claimed directory without a
    # record is custody failure.  The retained anchor prevents PGID reuse until the parent has
    # completed its cleanup adjudication.
    set -m
    (
      set +m
      probe_anchor_pid="$(python3 -I -S -c 'import os; print(os.getppid())')"
      readonly probe_anchor_pid
      # The anchor must survive the watchdog's advisory TERM so a final group SIGKILL can still use
      # the original PGID.  Usually the parent cancels the watchdog and dispatches that KILL; the
      # watchdog retains a delayed KILL fallback if the parent is descheduled.  Use a caught no-op
      # handler, not SIG_IGN: an ignored disposition survives exec and would prevent a nested shell
      # from restoring TERM's default action.  A caught shell handler resets to default across exec.
      trap ':' TERM
      set +e
      "$@"
      probe_status=$?
      set -e
      set +e
      python3 -I -S - "$decision_root" "$probe_status" <<'PY'
import os
from pathlib import Path
import sys


decision_root = Path(sys.argv[1])
probe_status = int(sys.argv[2])
if not 0 <= probe_status <= 255:
    raise SystemExit(f"probe status is outside the shell byte range: {probe_status}")
try:
    os.mkdir(decision_root, 0o700)
except FileExistsError:
    raise SystemExit(75)
temporary = decision_root / "probe-status.tmp"
final = decision_root / "probe-status"
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
descriptor = os.open(temporary, flags, 0o600)
try:
    payload = f"probe_status={probe_status}\n".encode("ascii")
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise SystemExit("probe-status record write made no progress")
        view = view[written:]
    os.fchmod(descriptor, 0o600)
    os.fsync(descriptor)
finally:
    os.close(descriptor)
os.replace(temporary, final)
directory_descriptor = os.open(
    decision_root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
)
try:
    os.fsync(directory_descriptor)
finally:
    os.close(directory_descriptor)
PY
      publication_status=$?
      set -e
      # Keep the exact group leader allocated after the control completes.  The parent sends group
      # SIGSTOP before inspecting membership, then releases a lone anchor or attempts SIGKILL on a
      # rejected group while that PGID is still expected.  A successful completion publisher
      # installs its release trap only after the publisher child has exited, then publishes the
      # shell-built readiness marker before stopping.  The parent will not adjudicate completion
      # until that exact marker is canonical.
      if [[ "$publication_status" -eq 0 ]]; then
        # RELEASE_READINESS_ARM: install the release trap before readiness becomes visible.
        trap 'exit 0' USR1
        # RELEASE_READINESS_PUBLISH: open a no-clobber final node with shell builtins after the
        # publisher child has exited.  The test hook deliberately induces an empty-node window
        # available to the parent's bounded descriptor retry; it does not require the parent to
        # observe that partial state under arbitrary scheduling.
        umask 077
        set -C
        if ! exec 9>"$release_ready_marker"; then
          set +C
          echo "$CHECK_NAME: release-readiness marker open failed" >&2
          kill -STOP "$probe_anchor_pid"
          exit 125
        fi
        set +C
        case "$C3_RELEASE_READY_DELAY_SECONDS" in
          0)
            ;;
          1)
            sleep 1
            ;;
          *)
            echo "$CHECK_NAME: invalid internal release-readiness delay" >&2
            exec 9>&-
            kill -STOP "$probe_anchor_pid"
            exit 125
            ;;
        esac
        if ! printf 'release_ready=1\n' >&9; then
          exec 9>&-
          echo "$CHECK_NAME: release-readiness marker write failed" >&2
          kill -STOP "$probe_anchor_pid"
          exit 125
        fi
        exec 9>&-
      elif [[ "$publication_status" -ne 75 ]]; then
        echo "$CHECK_NAME: completion-record publisher failed: $publication_status" >&2
      fi
      kill -STOP "$probe_anchor_pid"
      exit 125
    ) &
    probe_pid=$!
    python3 -I -S - \
      "$probe_pid" "$timeout_seconds" "$decision_root" <<'PY' \
      >/dev/null 2>&1 &
import os
from pathlib import Path
import signal
import sys
import time


process_group = int(sys.argv[1])
timeout_seconds = int(sys.argv[2])
decision_root = Path(sys.argv[3])
classification_committed = False


def handle_parent_cancellation(_signal_number, _frame):
    if not classification_committed:
        raise SystemExit(0)


signal.signal(signal.SIGTERM, handle_parent_cancellation)


def claim_decision() -> bool:
    try:
        os.mkdir(decision_root, 0o700)
    except FileExistsError:
        return False
    return True


def publish_record(name: str, payload: str) -> None:
    temporary = decision_root / f"{name}.tmp"
    final = decision_root / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(temporary, flags, 0o600)
    try:
        view = memoryview(payload.encode("ascii"))
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise SystemExit(f"{name} record write made no progress")
            view = view[written:]
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, final)
    directory_descriptor = os.open(
        decision_root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    )
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


if timeout_seconds < 1:
    if not claim_decision():
        raise SystemExit(0)
    classification_committed = True
    publish_record("watchdog-error", "watchdog_error=invalid-timeout\n")
    raise SystemExit(1)
try:
    observed_group = os.getpgid(process_group)
except ProcessLookupError:
    if not claim_decision():
        raise SystemExit(0)
    classification_committed = True
    publish_record("watchdog-error", "watchdog_error=probe-group-missing-at-start\n")
    raise SystemExit(1)
if observed_group != process_group:
    if not claim_decision():
        raise SystemExit(0)
    classification_committed = True
    publish_record(
        "watchdog-error",
        f"watchdog_error=process-group-mismatch:{observed_group}\n",
    )
    try:
        os.kill(process_group, signal.SIGTERM)
    except ProcessLookupError:
        pass
    raise SystemExit(1)
time.sleep(timeout_seconds)
try:
    observed_group = os.getpgid(process_group)
except ProcessLookupError:
    if not claim_decision():
        raise SystemExit(0)
    classification_committed = True
    publish_record("watchdog-error", "watchdog_error=probe-group-missing-at-deadline\n")
    raise SystemExit(1)
if observed_group != process_group:
    if not claim_decision():
        raise SystemExit(0)
    classification_committed = True
    publish_record(
        "watchdog-error",
        f"watchdog_error=late-process-group-mismatch:{observed_group}\n",
    )
    try:
        os.kill(process_group, signal.SIGTERM)
    except ProcessLookupError:
        pass
    raise SystemExit(1)
if not claim_decision():
    raise SystemExit(0)
classification_committed = True
publish_record("timeout", f"timeout_seconds={timeout_seconds}\n")
try:
    os.killpg(process_group, signal.SIGTERM)
except ProcessLookupError:
    pass
time.sleep(2)
try:
    os.killpg(process_group, signal.SIGKILL)
except ProcessLookupError:
    pass
PY
    watchdog_pid=$!
    set +m

    # RELEASE_READINESS_WAIT: do not spend a preliminary grace waiting for readiness-node
    # existence.  A visible completion record breaks this loop; central decision capture and
    # watchdog reaping then precede the sole five-second readiness descriptor validator below.
    while [[ ! -f "$timeout_marker" && ! -f "$watchdog_error_marker" ]]; do
      if [[ -f "$probe_status_record" ]]; then
        break
      fi
      if [[ -e "$decision_root" ]]; then
        if [[ "$decision_claim_second" -eq -1 ]]; then
          decision_claim_second=$SECONDS
        elif (( SECONDS - decision_claim_second >= decision_publication_grace_seconds )); then
          break
        fi
      fi
      if (( SECONDS >= decision_absolute_deadline )); then
        break
      fi
      if ! kill -0 "$probe_pid" 2>/dev/null && ! kill -0 "$watchdog_pid" 2>/dev/null; then
        break
      fi
      sleep 0.01
    done

    if [[ ! -f "$probe_status_record" \
        && ! -f "$timeout_marker" \
        && ! -f "$watchdog_error_marker" ]]; then
      # Neither producer published a decision record.  A producer may have died before claiming or
      # stalled after claiming the exclusive directory.  Kill both bounded process domains rather
      # than inferring which state occurred from the directory alone.
      set +e
      kill -KILL "$watchdog_pid" 2>/dev/null || true
      wait "$watchdog_pid" 2>/dev/null || true
      if kill -0 "$probe_pid" 2>/dev/null; then
        kill -KILL -- "-$probe_pid" 2>/dev/null || kill -KILL "$probe_pid" 2>/dev/null || true
      fi
      wait "$probe_pid" 2>/dev/null || true
      prove_probe_group_absent "$probe_pid"
      group_absence_status=$?
      set -e
      if [[ "$group_absence_status" -ne 0 ]]; then
        echo "$CHECK_NAME: bounded probe could not prove post-cleanup group absence" >&2
        exit 125
      fi
      echo "$CHECK_NAME: bounded probe produced no published decision record" >&2
      exit 125
    fi

    # Bind every decision producer to one exact, descriptor-replayed, mode-0600 record before the
    # record selects any completion/timeout/error branch.  This is custody of the private test
    # protocol, not authenticity against a same-UID writer that can replace the entire private
    # root between the checked transitions.
    set +e
    decision_record_kind="$(python3 -I -S - "$decision_root" "$timeout_seconds" <<'PY'
import os
from pathlib import Path
import re
import stat
import sys


decision_root = Path(sys.argv[1])
timeout_seconds = int(sys.argv[2])
root_metadata = decision_root.lstat()
if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_IMODE(root_metadata.st_mode) != 0o700:
    raise SystemExit("decision root is not a mode-0700 directory")

names = ("probe-status", "timeout", "watchdog-error")
observed = [name for name in names if os.path.lexists(decision_root / name)]
if len(observed) != 1:
    raise SystemExit(f"expected exactly one decision record, observed {observed!r}")
name = observed[0]
path = decision_root / name
flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
descriptor = os.open(path, flags)
try:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit("decision record is not a single-link regular file")
    if stat.S_IMODE(before.st_mode) != 0o600:
        raise SystemExit("decision record mode is not 0600")
    if before.st_size > 256:
        raise SystemExit("decision record exceeds the 256-byte parser bound")
    payload = bytearray()
    while len(payload) <= 256:
        block = os.read(descriptor, 257 - len(payload))
        if not block:
            break
        payload.extend(block)
    after = os.fstat(descriptor)
finally:
    os.close(descriptor)
leaf = path.lstat()
identity_fields = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)
if tuple(getattr(before, field) for field in identity_fields) != tuple(
    getattr(after, field) for field in identity_fields
) or tuple(getattr(after, field) for field in identity_fields) != tuple(
    getattr(leaf, field) for field in identity_fields
):
    raise SystemExit("decision record identity changed during descriptor replay")

raw = bytes(payload)
if name == "probe-status":
    match = re.fullmatch(
        rb"probe_status=([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\n",
        raw,
    )
    if match is None:
        raise SystemExit("probe-status decision payload is not canonical")
    print(f"probe-status:{match.group(1).decode('ascii')}")
elif name == "timeout":
    if raw != f"timeout_seconds={timeout_seconds}\n".encode("ascii"):
        raise SystemExit("timeout decision payload is not canonical")
    print("timeout")
else:
    if re.fullmatch(
        rb"watchdog_error=(?:invalid-timeout|probe-group-missing-at-start|"
        rb"probe-group-missing-at-deadline|process-group-mismatch:[1-9][0-9]*|"
        rb"late-process-group-mismatch:[1-9][0-9]*)\n",
        raw,
    ) is None:
        raise SystemExit("watchdog-error decision payload is not canonical")
    print("watchdog-error")
PY
    )"
    decision_record_custody_status=$?
    set -e
    if [[ "$decision_record_custody_status" -ne 0 ]]; then
      set +e
      kill -KILL "$watchdog_pid" 2>/dev/null || true
      wait "$watchdog_pid" 2>/dev/null || true
      if kill -0 "$probe_pid" 2>/dev/null; then
        kill -KILL -- "-$probe_pid" 2>/dev/null || kill -KILL "$probe_pid" 2>/dev/null || true
      fi
      wait "$probe_pid" 2>/dev/null || true
      prove_probe_group_absent "$probe_pid"
      group_absence_status=$?
      set -e
      if [[ "$group_absence_status" -ne 0 ]]; then
        echo "$CHECK_NAME: bounded probe could not prove post-cleanup group absence" >&2
        exit 125
      fi
      echo "$CHECK_NAME: bounded probe decision record failed custody" >&2
      exit 125
    fi

    # A visible record is the committed decision.  From this point the parent performs final
    # adjudication: it attempts to kill the watchdog and waits under the admitted kernel-progress premise,
    # then attempts group cleanup when needed.  The watchdog's delayed KILL may already have won
    # under descheduling; cleanup provenance is not inferred from absence.  Ordinary completion
    # sends group SIGSTOP before its bounded membership snapshot below; signal delivery is not
    # promoted into a proof that every member reached a stopped state.
    set +e
    kill -KILL "$watchdog_pid" 2>/dev/null || true
    wait "$watchdog_pid" 2>/dev/null || true
    if [[ "$decision_record_kind" == probe-status:* ]]; then
      # RELEASE_READINESS_VALIDATE: parse exact marker custody before group membership/release.
      python3 -I -S - \
        "$release_ready_marker" "$decision_publication_grace_seconds" <<'PY'
import os
import stat
import sys
import time


path = sys.argv[1]
deadline = time.monotonic() + int(sys.argv[2])
last_error = "marker was never observed"
flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
while True:
    descriptor = None
    try:
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise RuntimeError("marker is not a single-link regular file")
        if stat.S_IMODE(before.st_mode) != 0o600:
            raise RuntimeError("marker mode is not 0600")
        payload = bytearray()
        while len(payload) <= len(b"release_ready=1\n"):
            block = os.read(descriptor, len(b"release_ready=1\n") + 1 - len(payload))
            if not block:
                break
            payload.extend(block)
        after = os.fstat(descriptor)
        leaf = os.lstat(path)
        identity_fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size")
        if tuple(getattr(before, field) for field in identity_fields) != tuple(
            getattr(after, field) for field in identity_fields
        ) or tuple(getattr(after, field) for field in identity_fields) != tuple(
            getattr(leaf, field) for field in identity_fields
        ):
            raise RuntimeError("marker identity changed during descriptor replay")
        if bytes(payload) != b"release_ready=1\n":
            raise RuntimeError("marker payload is not canonical")
        break
    except (OSError, RuntimeError) as error:
        last_error = str(error)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if time.monotonic() >= deadline:
        raise SystemExit(f"release-readiness marker did not become canonical: {last_error}")
    time.sleep(0.01)
PY
      release_readiness_status=$?
      if [[ "$release_readiness_status" -ne 0 ]]; then
        kill -KILL -- "-$probe_pid" 2>/dev/null || kill -KILL "$probe_pid" 2>/dev/null || true
        wait "$probe_pid" 2>/dev/null || true
        prove_probe_group_absent "$probe_pid"
        group_absence_status=$?
        set -e
        if [[ "$group_absence_status" -ne 0 ]]; then
          echo "$CHECK_NAME: bounded probe could not prove post-cleanup group absence" >&2
          exit 125
        fi
        echo "$CHECK_NAME: bounded probe release-readiness custody failed" >&2
        exit 125
      fi
      probe_status="${decision_record_kind#probe-status:}"

      "$PROBE_CLEANUP_PYTHON" -I -S - "$probe_pid" "$PS_COMMAND" <<'PY'
import os
import signal
import subprocess
import sys


process_group = int(sys.argv[1])
ps_command = sys.argv[2]
cleanup_status = 4
detail = None
ownership_proven = False
try:
    observed_group = os.getpgid(process_group)
    if observed_group != process_group:
        raise RuntimeError("probe anchor no longer owns its exact process group")
    ownership_proven = True
    os.killpg(process_group, signal.SIGSTOP)
    completed = subprocess.run(
        [ps_command, "-A", "-o", "pid=", "-o", "pgid="],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=5,
    )
    members = []
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2:
            raise RuntimeError(f"unexpected ps membership row: {line!r}")
        process_id, observed_process_group = map(int, fields)
        if observed_process_group == process_group:
            members.append(process_id)
    if process_group not in members:
        raise RuntimeError(
            "probe anchor is absent from its process-group membership snapshot"
        )
    unexpected = sorted(
        process_id for process_id in members if process_id != process_group
    )
    if unexpected:
        cleanup_status = 3
        detail = (
            "bounded probe left unexpected process-group members: "
            + ",".join(map(str, unexpected))
        )
    else:
        cleanup_status = 0
except Exception as error:
    detail = f"bounded probe membership cleanup failed closed: {error}"
finally:
    if ownership_proven:
        try:
            if cleanup_status == 0:
                os.kill(process_group, signal.SIGUSR1)
                os.kill(process_group, signal.SIGCONT)
            else:
                os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            if cleanup_status == 0:
                cleanup_status = 4
                detail = "probe anchor disappeared during bounded release"
if detail is not None:
    print(detail, file=sys.stderr)
raise SystemExit(cleanup_status)
PY
      group_cleanup_status=$?
      if [[ "$group_cleanup_status" -ne 0 ]] && kill -0 "$probe_pid" 2>/dev/null; then
        kill -KILL -- "-$probe_pid" 2>/dev/null || kill -KILL "$probe_pid" 2>/dev/null || true
      fi
      wait "$probe_pid" 2>/dev/null
      probe_wait_status=$?
      if [[ "$group_cleanup_status" -eq 0 && "$probe_wait_status" -ne 0 ]]; then
        group_release_failure="clean probe anchor did not acknowledge bounded release"
      fi
      if [[ "$group_cleanup_status" -ne 0 && "$probe_wait_status" -ne 137 ]]; then
        group_release_failure="rejected probe group did not report shell status 137 (SIGKILL)"
      fi
    else
      if kill -0 "$probe_pid" 2>/dev/null; then
        kill -KILL -- "-$probe_pid" 2>/dev/null || kill -KILL "$probe_pid" 2>/dev/null || true
      fi
      wait "$probe_pid" 2>/dev/null
      probe_wait_status=$?
      group_cleanup_status=0
    fi

    prove_probe_group_absent "$probe_pid"
    group_absence_status=$?
    set -e

    if [[ "$group_absence_status" -ne 0 ]]; then
      echo "$CHECK_NAME: bounded probe could not prove post-cleanup group absence" >&2
      exit 125
    fi
    if [[ -n "$group_release_failure" ]]; then
      echo "$CHECK_NAME: $group_release_failure" >&2
      exit 125
    fi
    if [[ "$decision_record_kind" == "watchdog-error" ]]; then
      echo "$CHECK_NAME: bounded probe watchdog could not establish process-group custody" >&2
      exit 125
    fi
    if [[ "$decision_record_kind" == "timeout" ]]; then
      echo "$CHECK_NAME: bounded probe exceeded $timeout_seconds seconds" >&2
      exit 124
    fi
    if [[ "$decision_record_kind" != probe-status:* ]]; then
      echo "$CHECK_NAME: bounded probe produced no typed completion record" >&2
      exit 125
    fi
    if [[ "$group_cleanup_status" -eq 3 ]]; then
      echo "$CHECK_NAME: bounded probe rejected surviving process-group members" >&2
      exit 125
    fi
    if [[ "$group_cleanup_status" -ne 0 ]]; then
      echo "$CHECK_NAME: bounded probe rejected process-group membership/cleanup custody" >&2
      exit 125
    fi
    exit "$probe_status"
  )
}

publish_test_probe_status_atomically() {
  local decision_root="$1"
  local payload_text="$2"
  local final_mode="$3"
  python3 -I -S - "$decision_root" "$payload_text" "$final_mode" <<'PY'
import os
from pathlib import Path
import sys


root = Path(sys.argv[1])
payload_text = sys.argv[2]
final_mode = int(sys.argv[3], 8)
if "\n" in payload_text or final_mode not in (0o600, 0o644):
    raise SystemExit("test decision-record parameters are outside the closed fixture set")
temporary = root / "probe-status.tmp"
final = root / "probe-status"
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
descriptor = os.open(temporary, flags, 0o600)
try:
    payload = memoryview((payload_text + "\n").encode("ascii"))
    while payload:
        written = os.write(descriptor, payload)
        if written <= 0:
            raise SystemExit("test decision-record write made no progress")
        payload = payload[written:]
    os.fchmod(descriptor, final_mode)
    os.fsync(descriptor)
finally:
    os.close(descriptor)
os.replace(temporary, final)
directory_descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
try:
    os.fsync(directory_descriptor)
finally:
    os.close(directory_descriptor)
PY
}

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  case "$C3_ACTIVE_FAMILY" in
    "")
      ;;
    bounded-probe)
      C3_BOUNDED_PROBE_COUNT=$((C3_BOUNDED_PROBE_COUNT + 1))
      ;;
    entry-wrapper)
      C3_ENTRY_WRAPPER_COUNT=$((C3_ENTRY_WRAPPER_COUNT + 1))
      ;;
    runtime-map)
      C3_RUNTIME_MAP_COUNT=$((C3_RUNTIME_MAP_COUNT + 1))
      ;;
    fls-map-path)
      C3_FLS_MAP_PATH_COUNT=$((C3_FLS_MAP_PATH_COUNT + 1))
      ;;
    executable-custody)
      C3_EXECUTABLE_CUSTODY_COUNT=$((C3_EXECUTABLE_CUSTODY_COUNT + 1))
      ;;
    format-custody)
      C3_FORMAT_CUSTODY_COUNT=$((C3_FORMAT_CUSTODY_COUNT + 1))
      ;;
    *)
      fail "unknown active C3 control family: $C3_ACTIVE_FAMILY"
      ;;
  esac
  printf 'ok %d - %s\n' "$PASS_COUNT" "$1"
}

# The production checker runs this suite from its own verify phase.  Any nested checker probe must
# start without the parent's captured-phase or live-lock custody; otherwise it can exercise the
# outer build root instead of the bounded fixture and, on cleanup, remove state owned by its
# parent.  Preserve every unrelated ambient variable so the dedicated contamination cases below
# can still test their named inputs.
without_workflow_gate_custody() {
  env \
    -u PID_RS_WORKFLOW_PDF_PHASE \
    -u PID_RS_WORKFLOW_PDF_ROOT \
    -u PID_RS_WORKFLOW_PDF_BUILD_ROOT \
    -u PID_RS_WORKFLOW_PDF_SAFE_PATH \
    -u PID_RS_WORKFLOW_PDF_LOCK_FD \
    -u PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256 \
    "$@"
}

fail() {
  echo "$CHECK_NAME: $1" >&2
  if [[ -s "$RESULT_LOG" ]]; then
    echo "--- captured output ---" >&2
    sed -n '1,160p' "$RESULT_LOG" >&2
    echo "--- end captured output ---" >&2
  fi
  exit 1
}

expect_accept() {
  local label="$1"
  shift
  reset_result_log
  # RESULT_LOG is inside this suite's private root and no test mutates it concurrently.  The shell
  # redirect below reopens the validated path; this is a same-process liveness guard, not a
  # descriptor-handoff or adversarial path-race claim.
  if ! run_bounded_probe "$CONTROL_TIMEOUT_SECONDS" "$@" >"$RESULT_LOG" 2>&1; then
    fail "$label: accepted control failed"
  fi
  pass "$label"
}

rejection_status_is_creditable() {
  # Under the admitted trusted-fixture convention, checker/validator rejection has two typed
  # outcomes: 1 for detected artifact or semantic drift, and 2 for a detected
  # prerequisite/environment contract violation.  This is not a causal type theorem for an
  # arbitrary marker-bearing hostile command.  Do not collapse arbitrary nonzero statuses into
  # evidence: watchdog/custody failures, command-launch failures, and signal deaths remain
  # uncreditable even when their output contains the marker.
  [[ "$1" -eq 1 || "$1" -eq 2 ]]
}

expect_reject() {
  local label="$1"
  local expected="$2"
  local status
  shift 2
  reset_result_log
  # Same private-root/same-process boundary as expect_accept: this is not descriptor handoff.
  set +e
  run_bounded_probe "$CONTROL_TIMEOUT_SECONDS" "$@" >"$RESULT_LOG" 2>&1
  status=$?
  set -e
  if ! rejection_status_is_creditable "$status"; then
    fail "$label: rejection status $status is outside the exact creditable set {1,2}"
  fi
  if ! grep -F -- "$expected" "$RESULT_LOG" >/dev/null; then
    fail "$label: rejection did not reach the claimed branch: $expected"
  fi
  pass "$label"
}

C3_ACTIVE_FAMILY="bounded-probe"
if ! run_bounded_probe 2 bash --noprofile --norc -c 'exit 0'; then
  fail "bounded-probe watchdog changed a successful status"
fi
pass "bounded-probe watchdog preserves normal success"

set +e
run_bounded_probe 2 bash --noprofile --norc -c 'exit 7'
watchdog_status=$?
set -e
if [[ "$watchdog_status" -ne 7 ]]; then
  fail "bounded-probe watchdog changed a nonzero status: $watchdog_status"
fi
pass "bounded-probe watchdog preserves an ordinary nonzero status"

reset_result_log
C3_RELEASE_READY_DELAY_SECONDS=1
release_delay_started=$SECONDS
set +e
run_bounded_probe 2 bash --noprofile --norc -c 'exit 0' >"$RESULT_LOG" 2>&1
release_delay_status=$?
set -e
C3_RELEASE_READY_DELAY_SECONDS=0
release_delay_elapsed=$((SECONDS - release_delay_started))
if [[ "$release_delay_status" -ne 0 || "$release_delay_elapsed" -lt 1 ]]; then
  fail "induced one-second readiness window did not complete successfully with the expected elapsed lower bound"
fi
pass "bounded-probe succeeds with an induced readiness window and observed elapsed time of at least one second"

publish_invalid_release_readiness() {
  local invalid_decision_root="$TEST_ROOT/probe-decision-$PASS_COUNT"
  umask 077
  mkdir "$invalid_decision_root"
  set -C
  printf 'release_ready=0\n' >"$invalid_decision_root/release-ready"
  set +C
  # Publish canonical status only after the complete invalid readiness payload is closed.  Status
  # visibility is the parent handoff, so the named control cannot pass on an absent/partial marker.
  publish_test_probe_status_atomically \
    "$invalid_decision_root" "probe_status=0" 0600 || return 88
}
reset_result_log
set +e
run_bounded_probe 2 publish_invalid_release_readiness >"$RESULT_LOG" 2>&1
invalid_readiness_status=$?
set -e
if [[ "$invalid_readiness_status" -ne 125 ]] \
    || ! grep -F -- 'marker payload is not canonical' \
      "$RESULT_LOG" >/dev/null \
    || ! grep -F -- 'bounded probe release-readiness custody failed' \
      "$RESULT_LOG" >/dev/null; then
  fail "noncanonical release-readiness payload did not fail closed"
fi
pass "bounded-probe rejects a noncanonical release-readiness payload after one descriptor grace"

publish_wrong_mode_decision_record() {
  local wrong_mode_decision_root="$TEST_ROOT/probe-decision-$PASS_COUNT"
  umask 077
  mkdir "$wrong_mode_decision_root"
  publish_test_probe_status_atomically \
    "$wrong_mode_decision_root" "probe_status=0" 0644 || return 88
  set -C
  printf 'release_ready=1\n' >"$wrong_mode_decision_root/release-ready"
  set +C
}
reset_result_log
set +e
run_bounded_probe 2 publish_wrong_mode_decision_record >"$RESULT_LOG" 2>&1
wrong_mode_decision_status=$?
set -e
if [[ "$wrong_mode_decision_status" -ne 125 ]] \
    || ! grep -F -- 'decision record mode is not 0600' \
      "$RESULT_LOG" >/dev/null \
    || ! grep -F -- 'bounded probe decision record failed custody' \
      "$RESULT_LOG" >/dev/null; then
  fail "wrong-mode completion decision record did not fail closed"
fi
pass "bounded-probe rejects a canonical-payload completion record with mode 0644"

reset_result_log
set +e
run_bounded_probe 0 sleep 300 >"$RESULT_LOG" 2>&1
invalid_timeout_status=$?
set -e
if [[ "$invalid_timeout_status" -ne 125 ]] \
    || ! grep -F -- 'bounded probe watchdog could not establish process-group custody' \
      "$RESULT_LOG" >/dev/null; then
  fail "canonical invalid-timeout watchdog-error record did not reach its typed custody branch"
fi
pass "bounded-probe validates the canonical watchdog-error decision record before status 125"

DESCENDANT_PID_FILE="$TEST_ROOT/watchdog-descendant.pid"
reset_result_log
set +e
# This single-quoted program is interpreted by the nested Bash process, where its dollars expand.
# shellcheck disable=SC2016
run_bounded_probe 1 \
  bash --noprofile --norc -c \
    'python3 -I -S -c '\''import time; time.sleep(300)'\'' & descendant=$!; printf '\''%s\n'\'' "$descendant" >"$1"; wait "$descendant"' \
    bash "$DESCENDANT_PID_FILE" \
  >"$RESULT_LOG" 2>&1
watchdog_status=$?
set -e
if [[ "$watchdog_status" -ne 124 ]] \
    || ! grep -F -- 'bounded probe exceeded 1 seconds' "$RESULT_LOG" >/dev/null; then
  fail "bounded-probe watchdog did not report its exact timeout status"
fi
python3 -I -S - "$DESCENDANT_PID_FILE" <<'PY'
import os
from pathlib import Path
import sys
import time


process_id = int(Path(sys.argv[1]).read_text(encoding="ascii").strip())
for _ in range(100):
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        break
    time.sleep(0.05)
else:
    raise SystemExit(f"bounded-probe descendant survived process-group termination: {process_id}")
PY
pass "bounded-probe timeout returns 124 and terminates its descendant process group"

IGNORING_DESCENDANT_PID_FILE="$TEST_ROOT/watchdog-ignoring-descendant.pid"
IGNORING_DESCENDANT_READY_FILE="$TEST_ROOT/watchdog-ignoring-descendant.ready"
reset_result_log
set +e
# The descendant installs SIG_IGN before publishing its ready marker.  Killing only the probe
# leader, or omitting the parent's final anchored-group SIGKILL, leaves this process alive.
# shellcheck disable=SC2016
run_bounded_probe 1 \
  bash --noprofile --norc -c \
    'python3 -I -S -c '\''import signal, sys, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(sys.argv[1]).write_text("ready\n", encoding="ascii", newline="\n"); time.sleep(300)'\'' "$2" & descendant=$!; printf '\''%s\n'\'' "$descendant" >"$1"; for _ in {1..100}; do [[ -e "$2" ]] && break; sleep 0.01; done; [[ -e "$2" ]] || exit 88; wait "$descendant"' \
    bash "$IGNORING_DESCENDANT_PID_FILE" "$IGNORING_DESCENDANT_READY_FILE" \
  >"$RESULT_LOG" 2>&1
watchdog_status=$?
set -e
if [[ "$watchdog_status" -ne 124 ]] \
    || ! grep -F -- 'bounded probe exceeded 1 seconds' "$RESULT_LOG" >/dev/null; then
  fail "bounded-probe escalation did not report its exact timeout status"
fi
python3 -I -S - "$IGNORING_DESCENDANT_PID_FILE" <<'PY'
import os
from pathlib import Path
import sys
import time


process_id = int(Path(sys.argv[1]).read_text(encoding="ascii").strip())
for _ in range(100):
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        break
    time.sleep(0.05)
else:
    raise SystemExit(
        f"TERM-ignoring descendant survived bounded SIGKILL cleanup: {process_id}"
    )
PY
pass "bounded-probe timeout completes SIGKILL cleanup for a TERM-ignoring descendant"

for creditable_status in 1 2; do
  if ! rejection_status_is_creditable "$creditable_status"; then
    fail "exact rejection-status classifier does not credit status $creditable_status"
  fi
done
for uncreditable_status in 0 3 4 123 124 125 126 127 128 130 143 255; do
  if rejection_status_is_creditable "$uncreditable_status"; then
    fail "rejection-status classifier credited status $uncreditable_status"
  fi
done
pass "rejection-status classifier credits only exact typed statuses 1 and 2"

reset_result_log
set +e
run_bounded_probe 2 \
  bash --noprofile --norc -c \
    'printf '\''claimed-signal-branch\n'\''; trap - TERM; kill -TERM $$' \
  >"$RESULT_LOG" 2>&1
signal_status=$?
set -e
if [[ "$signal_status" -ne 143 ]] \
    || ! grep -F -- 'claimed-signal-branch' "$RESULT_LOG" >/dev/null; then
  fail "signal-status fixture did not produce its exact marker and status 143"
fi
if rejection_status_is_creditable "$signal_status"; then
  fail "signal-status fixture could receive rejection credit"
fi
pass "rejection classifier denies marker-bearing self-SIGTERM status 143"

ORPHAN_PID_FILE="$TEST_ROOT/watchdog-normal-orphan.pid"
ORPHAN_READY_FILE="$TEST_ROOT/watchdog-normal-orphan.ready"
reset_result_log
set +e
# shellcheck disable=SC2016
run_bounded_probe 2 \
  bash --noprofile --norc -c \
    'python3 -I -S -c '\''import signal, sys, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(sys.argv[1]).write_text("ready\n", encoding="ascii", newline="\n"); time.sleep(300)'\'' "$2" & descendant=$!; printf '\''%s\n'\'' "$descendant" >"$1"; for _ in {1..100}; do [[ -e "$2" ]] && break; sleep 0.01; done; [[ -e "$2" ]] || exit 88; exit 0' \
    bash "$ORPHAN_PID_FILE" "$ORPHAN_READY_FILE" \
  >"$RESULT_LOG" 2>&1
orphan_status=$?
set -e
if [[ "$orphan_status" -ne 125 ]] \
    || ! grep -F -- 'bounded probe rejected surviving process-group members' \
      "$RESULT_LOG" >/dev/null; then
  fail "ordinary probe completion did not reject its surviving process-group member"
fi
python3 -I -S - "$ORPHAN_PID_FILE" <<'PY'
import os
from pathlib import Path
import sys
import time


process_id = int(Path(sys.argv[1]).read_text(encoding="ascii").strip())
for _ in range(100):
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        break
    time.sleep(0.05)
else:
    raise SystemExit(f"ordinary-completion descendant survived group cleanup: {process_id}")
PY
pass "bounded-probe ordinary completion rejects and kills a surviving descendant"

PUBLICATION_STALL_PID_FILE="$TEST_ROOT/watchdog-publication-stall.pid"
PUBLICATION_STALL_READY_FILE="$TEST_ROOT/watchdog-publication-stall.ready"
claim_probe_decision_without_record() {
  # Claim first so the watchdog cannot win while a loaded runner schedules the descendant.  The
  # record publication remains bounded by the parent's separate five-second decision-publication
  # grace; this no-record fixture never enters completion-readiness validation.
  mkdir "$TEST_ROOT/probe-decision-$PASS_COUNT"
  python3 -I -S -c \
    'import signal, sys, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(sys.argv[1]).write_text("ready\n", encoding="ascii", newline="\n"); time.sleep(300)' \
    "$PUBLICATION_STALL_READY_FILE" &
  publication_stall_descendant=$!
  printf '%s\n' "$publication_stall_descendant" >"$PUBLICATION_STALL_PID_FILE"
  for _ in {1..100}; do
    [[ -e "$PUBLICATION_STALL_READY_FILE" ]] && break
    sleep 0.01
  done
  [[ -e "$PUBLICATION_STALL_READY_FILE" ]] || return 88
  sleep 300
}
reset_result_log
set +e
run_bounded_probe 1 claim_probe_decision_without_record >"$RESULT_LOG" 2>&1
publication_status=$?
set -e
if [[ "$publication_status" -ne 125 ]] \
    || ! grep -F -- 'bounded probe produced no published decision record' \
      "$RESULT_LOG" >/dev/null; then
  fail "decision-publication stall did not reach its bounded custody rejection"
fi
python3 -I -S - "$PUBLICATION_STALL_PID_FILE" <<'PY'
import os
from pathlib import Path
import sys
import time


process_id = int(Path(sys.argv[1]).read_text(encoding="ascii").strip())
for _ in range(100):
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        break
    time.sleep(0.05)
else:
    raise SystemExit(
        f"publication-stall descendant survived process-group cleanup: {process_id}"
    )
PY
pass "bounded-probe rejects an exclusive decision claim without a published record"

MALFORMED_STATUS_PID_FILE="$TEST_ROOT/watchdog-malformed-status.pid"
MALFORMED_STATUS_READY_FILE="$TEST_ROOT/watchdog-malformed-status.ready"
publish_malformed_status_with_descendant() {
  local malformed_decision_root="$TEST_ROOT/probe-decision-$PASS_COUNT"
  # As above, claim before any readiness scheduling; atomically publish the complete deliberately
  # malformed record only after the TERM-ignoring child has established the cleanup obligation.
  # The central three-kind decision parser precedes completion-readiness validation, so no
  # release-readiness node is needed for this hostile branch.
  umask 077
  mkdir "$malformed_decision_root"
  python3 -I -S -c \
    'import signal, sys, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(sys.argv[1]).write_text("ready\n", encoding="ascii", newline="\n"); time.sleep(300)' \
    "$MALFORMED_STATUS_READY_FILE" &
  malformed_status_descendant=$!
  printf '%s\n' "$malformed_status_descendant" >"$MALFORMED_STATUS_PID_FILE"
  for _ in {1..100}; do
    [[ -e "$MALFORMED_STATUS_READY_FILE" ]] && break
    sleep 0.01
  done
  [[ -e "$MALFORMED_STATUS_READY_FILE" ]] || return 88
  publish_test_probe_status_atomically \
    "$malformed_decision_root" "probe_status=not-a-status" 0600 || return 88
  sleep 300
}
reset_result_log
set +e
run_bounded_probe 2 publish_malformed_status_with_descendant >"$RESULT_LOG" 2>&1
malformed_status=$?
set -e
if [[ "$malformed_status" -ne 125 ]] \
    || ! grep -F -- 'probe-status decision payload is not canonical' \
      "$RESULT_LOG" >/dev/null \
    || ! grep -F -- 'bounded probe decision record failed custody' \
      "$RESULT_LOG" >/dev/null; then
  fail "malformed completion record did not reach its bounded custody rejection"
fi
python3 -I -S - "$MALFORMED_STATUS_PID_FILE" <<'PY'
import os
from pathlib import Path
import sys
import time


process_id = int(Path(sys.argv[1]).read_text(encoding="ascii").strip())
for _ in range(100):
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        break
    time.sleep(0.05)
else:
    raise SystemExit(
        f"malformed-record descendant survived process-group cleanup: {process_id}"
    )
PY
pass "bounded-probe rejects malformed decision payload only after descendant cleanup"

PROBE_CLEANUP_PYTHON_ORIGINAL="$PROBE_CLEANUP_PYTHON"
PROBE_CLEANUP_PYTHON="$TEST_ROOT/absent-cleanup-python"
reset_result_log
set +e
run_bounded_probe 2 bash --noprofile --norc -c 'exit 0' >"$RESULT_LOG" 2>&1
cleanup_launch_status=$?
set -e
PROBE_CLEANUP_PYTHON="$PROBE_CLEANUP_PYTHON_ORIGINAL"
if [[ "$cleanup_launch_status" -ne 125 ]] \
    || ! grep -F -- 'bounded probe rejected process-group membership/cleanup custody' \
      "$RESULT_LOG" >/dev/null; then
  fail "cleanup-helper launch failure did not fail closed after group cleanup"
fi
pass "bounded-probe cleanup-helper launch failure kills the anchored group and rejects"

PS_COMMAND_ORIGINAL="$PS_COMMAND"
PS_COMMAND="$TEST_ROOT/non-executable-ps"
printf 'not executable\n' >"$PS_COMMAND"
chmod 0600 "$PS_COMMAND"
reset_result_log
set +e
run_bounded_probe 2 bash --noprofile --norc -c 'exit 0' >"$RESULT_LOG" 2>&1
cleanup_ps_status=$?
set -e
PS_COMMAND="$PS_COMMAND_ORIGINAL"
if [[ "$cleanup_ps_status" -ne 125 ]] \
    || ! grep -F -- 'bounded probe rejected process-group membership/cleanup custody' \
      "$RESULT_LOG" >/dev/null; then
  fail "cleanup membership-command failure did not fail closed after group cleanup"
fi
pass "bounded-probe membership-command failure kills the anchored group and rejects"

RESULT_LOG_ORIGINAL="$RESULT_LOG"
reset_result_log
pass "result-log reset accepts one direct single-link regular file"

expect_result_log_reset_reject() {
  local candidate="$1"
  local label="$2"
  local reset_status
  RESULT_LOG="$candidate"
  set +e
  reset_result_log >"$RESULT_LOG_ORIGINAL" 2>&1
  reset_status=$?
  set -e
  RESULT_LOG="$RESULT_LOG_ORIGINAL"
  if ! rejection_status_is_creditable "$reset_status"; then
    fail "$label: result-log rejection status $reset_status is outside {1,2}"
  fi
  pass "$label"
}

printf 'outside\n' >"$TEST_ROOT/result-log-outside"
ln -s "$TEST_ROOT/result-log-outside" "$TEST_ROOT/result-log-symlink"
expect_result_log_reset_reject \
  "$TEST_ROOT/result-log-symlink" \
  "result-log reset rejects a symlink without following it"

python3 -I -S -c 'import os, sys; os.mkfifo(sys.argv[1])' "$TEST_ROOT/result-log-fifo"
expect_result_log_reset_reject \
  "$TEST_ROOT/result-log-fifo" \
  "result-log reset rejects a FIFO without blocking"

mkdir "$TEST_ROOT/result-log-directory"
expect_result_log_reset_reject \
  "$TEST_ROOT/result-log-directory" \
  "result-log reset rejects a directory"

printf 'multiply linked\n' >"$TEST_ROOT/result-log-hardlink-source"
ln "$TEST_ROOT/result-log-hardlink-source" "$TEST_ROOT/result-log-hardlink"
expect_result_log_reset_reject \
  "$TEST_ROOT/result-log-hardlink" \
  "result-log reset rejects a multiply linked regular file"
if [[ "$(cat "$TEST_ROOT/result-log-hardlink-source")" != "multiply linked" ]]; then
  fail "result-log reset modified hostile multiply linked bytes before rejection"
fi
pass "result-log hardlink rejection preserves the preexisting shared bytes"

replace_once() {
  local path="$1"
  local old="$2"
  local new="$3"
  python3 -I -S - "$path" "$old" "$new" <<'PY'
from pathlib import Path
import copy
import sys


path = Path(sys.argv[1])
old = sys.argv[2]
new = sys.argv[3]
text = path.read_text(encoding="utf-8")
if text.count(old) != 1:
    raise SystemExit(f"expected exactly one mutation target in {path}: {old!r}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
PY
}

mutate_run_bounded_probe_once() {
  local path="$1"
  local old="$2"
  local new="$3"
  python3 -I -S - "$path" "$old" "$new" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
old = sys.argv[2]
new = sys.argv[3]
text = path.read_text(encoding="utf-8")
start = text.index("run_bounded_probe() {")
end = text.index("\n}\n\npublish_test_probe_status_atomically() {", start) + 2
region = text[start:end]
if region.count(old) != 1:
    raise SystemExit(f"expected one bounded-probe mutation target: {old!r}")
region = region.replace(old, new, 1)
path.write_text(text[:start] + region + text[end:], encoding="utf-8", newline="\n")
PY
}

validate_watchdog_timeout_order() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = text.index("run_bounded_probe() {")
end = text.index("\n}\n\npublish_test_probe_status_atomically() {", start) + 2
region = text[start:end]
handler_definition = region.index("def handle_parent_cancellation(_signal_number, _frame):")
handler_guard = region.index("if not classification_committed:", handler_definition)
handler_exit = region.index("raise SystemExit(0)", handler_guard)
handler_install = region.index(
    "signal.signal(signal.SIGTERM, handle_parent_cancellation)", handler_exit
)
deadline = region.index("time.sleep(timeout_seconds)")
late_group_check = region.index("observed_group = os.getpgid(process_group)", deadline)
late_mismatch = region.index("if observed_group != process_group:", late_group_check)
late_error_marker = region.index(
    'f"watchdog_error=late-process-group-mismatch:{observed_group}\\n"',
    late_mismatch,
)
late_mismatch_exit = region.index("raise SystemExit(1)", late_error_marker)
timeout_marker = region.index(
    'publish_record("timeout", f"timeout_seconds={timeout_seconds}\\n")',
    late_group_check,
)
timeout_claim = region.index("if not claim_decision():", late_mismatch_exit)
timeout_commit = region.find("classification_committed = True", late_mismatch_exit)
termination = region.find("os.killpg(process_group, signal.SIGTERM)", timeout_marker)
if not handler_definition < handler_guard < handler_exit < handler_install < deadline:
    raise SystemExit("watchdog parent-cancellation handler custody drifted")
if not (
    deadline
    < late_group_check
    < late_mismatch
    < late_error_marker
    < late_mismatch_exit
):
    raise SystemExit("watchdog late process-group adjudication order drifted")
if timeout_marker < late_mismatch_exit:
    raise SystemExit(
        "watchdog timeout classification precedes late process-group adjudication"
    )
if timeout_commit == -1 or not (
    late_mismatch_exit < timeout_claim < timeout_commit < timeout_marker
):
    raise SystemExit("watchdog timeout classification is not committed before its marker")
if termination == -1 or not timeout_marker < termination:
    raise SystemExit("watchdog timeout classification is not recorded before termination")
PY
}

validate_release_readiness_order() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = text.index("run_bounded_probe() {")
end = text.index("\n}\n\npublish_test_probe_status_atomically() {", start) + 2
region = text[start:end]
ordered = (
    "      publication_status=$?",
    "# RELEASE_READINESS_ARM: install the release trap before readiness becomes visible.",
    "        trap 'exit 0' USR1",
    "# RELEASE_READINESS_PUBLISH: open a no-clobber final node with shell builtins after the",
    r'''        if ! exec 9>"$release_ready_marker"; then''',
    r'''        if ! printf 'release_ready=1\n' >&9; then''',
    "# RELEASE_READINESS_WAIT: do not spend a preliminary grace waiting for readiness-node",
    "# Bind every decision producer to one exact, descriptor-replayed, mode-0600 record before the",
    'raise SystemExit("timeout decision payload is not canonical")',
    'raise SystemExit("watchdog-error decision payload is not canonical")',
    "# RELEASE_READINESS_VALIDATE: parse exact marker custody before group membership/release.",
    "        \"$release_ready_marker\" \"$decision_publication_grace_seconds\" <<'PY'",
    "    os.killpg(process_group, signal.SIGSTOP)",
)
positions = []
for marker in ordered:
    if region.count(marker) != 1:
        raise SystemExit(f"release-readiness order marker drifted: {marker}")
    positions.append(region.index(marker))
if positions != sorted(positions) or len(set(positions)) != len(positions):
    raise SystemExit("release-readiness publication/adjudication order drifted")
handoff = '''      if [[ -f "$probe_status_record" ]]; then
        break
      fi'''
if region.count(handoff) != 1:
    raise SystemExit("release-readiness completion-record handoff drifted")
if region.count("os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK") != 2:
    raise SystemExit("decision/readiness no-follow descriptor custody drifted")
readiness_guards = {
    "descriptor flags": (
        'last_error = "marker was never observed"\n'
        "flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK"
    ),
    "regular/link": (
        "        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:\n"
        '            raise RuntimeError("marker is not a single-link regular file")'
    ),
    "mode": (
        "        if stat.S_IMODE(before.st_mode) != 0o600:\n"
        '            raise RuntimeError("marker mode is not 0600")'
    ),
    "identity": '            raise RuntimeError("marker identity changed during descriptor replay")',
}
for label, marker in readiness_guards.items():
    if region.count(marker) != 1:
        raise SystemExit(f"release-readiness {label} guard drifted")
decision_guards = {
    "root mode": (
        "if not stat.S_ISDIR(root_metadata.st_mode) or "
        "stat.S_IMODE(root_metadata.st_mode) != 0o700:\n"
        '    raise SystemExit("decision root is not a mode-0700 directory")'
    ),
    "regular/link": (
        "    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:\n"
        '        raise SystemExit("decision record is not a single-link regular file")'
    ),
    "identity": '    raise SystemExit("decision record identity changed during descriptor replay")',
}
for label, marker in decision_guards.items():
    if region.count(marker) != 1:
        raise SystemExit(f"decision-record {label} guard drifted")
if region.count('    if raw != f"timeout_seconds={timeout_seconds}\\n".encode("ascii"):') != 1:
    raise SystemExit("decision-record timeout exact-payload guard drifted")
watchdog_payload_guard = (
    "    if re.fullmatch(\n"
    '        rb"watchdog_error=(?:invalid-timeout|probe-group-missing-at-start|"'
)
if region.count(watchdog_payload_guard) != 1:
    raise SystemExit("decision-record watchdog-error exact-payload guard drifted")
if region.count('if bytes(payload) != b"release_ready=1\\n":') != 1:
    raise SystemExit("release-readiness canonical payload check drifted")
PY
}

prepare_watchdog_mutant() {
  local source="$1"
  local destination="$2"
  cp "$source" "$destination"
  python3 -I -S - "$source" "$destination" <<'PY'
import os
from pathlib import Path
import stat
import sys


source = Path(sys.argv[1])
destination = Path(sys.argv[2])
for required_flag in ("O_NOFOLLOW", "O_CLOEXEC"):
    if not hasattr(os, required_flag):
        raise SystemExit(f"watchdog mutant custody lacks required {required_flag}")
flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
source_descriptor = os.open(source, flags)
destination_descriptor = os.open(destination, flags)
try:
    source_stat = os.fstat(source_descriptor)
    destination_before = os.fstat(destination_descriptor)
    for label, metadata in (
        ("source", source_stat),
        ("destination", destination_before),
    ):
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise SystemExit(
                f"watchdog mutant {label} is not a single-link regular file"
            )
    identity_fields = ("st_dev", "st_ino", "st_mode", "st_nlink")
    for label, path, metadata in (
        ("source", source, source_stat),
        ("destination", destination, destination_before),
    ):
        leaf = path.lstat()
        if tuple(getattr(metadata, field) for field in identity_fields) != tuple(
            getattr(leaf, field) for field in identity_fields
        ):
            raise SystemExit(
                f"watchdog mutant {label} path identity differs from its descriptor"
            )

    def read_all(descriptor):
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    if read_all(source_descriptor) != read_all(destination_descriptor):
        raise SystemExit("watchdog mutant copy differs from its exact source bytes")

    read_only_mode = stat.S_IMODE(destination_before.st_mode) & ~0o222
    os.fchmod(destination_descriptor, read_only_mode)
    destination_read_only = os.fstat(destination_descriptor)
    if (
        destination_read_only.st_dev,
        destination_read_only.st_ino,
        destination_read_only.st_nlink,
        stat.S_IMODE(destination_read_only.st_mode),
    ) != (
        destination_before.st_dev,
        destination_before.st_ino,
        1,
        read_only_mode,
    ):
        raise SystemExit("watchdog mutant read-only mode transition changed custody")

    writable_mode = read_only_mode | stat.S_IWUSR
    os.fchmod(destination_descriptor, writable_mode)
    destination_after = os.fstat(destination_descriptor)
    if (
        destination_after.st_dev,
        destination_after.st_ino,
        destination_after.st_nlink,
        destination_after.st_size,
        stat.S_IMODE(destination_after.st_mode),
    ) != (
        destination_before.st_dev,
        destination_before.st_ino,
        1,
        destination_before.st_size,
        writable_mode,
    ):
        raise SystemExit("watchdog mutant writable mode transition changed custody")
finally:
    os.close(destination_descriptor)
    os.close(source_descriptor)

destination_leaf = destination.lstat()
if (
    destination_leaf.st_dev,
    destination_leaf.st_ino,
    destination_leaf.st_nlink,
    destination_leaf.st_size,
    stat.S_IMODE(destination_leaf.st_mode),
) != (
    destination_after.st_dev,
    destination_after.st_ino,
    1,
    destination_after.st_size,
    stat.S_IMODE(destination_after.st_mode),
):
    raise SystemExit("watchdog mutant final leaf custody drifted")
PY
}

SELFTEST_SOURCE="$ROOT/scripts/check-mathematical-workflow-pdf-self-test.sh"
expect_accept \
  "release-readiness source custody orders publisher exit, trap, marker, wait, validation, and membership" \
  validate_release_readiness_order "$SELFTEST_SOURCE"

case_file="$TEST_ROOT/release-readiness-trap-removed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  "        trap 'exit 0' USR1" \
  "        # hostile mutation removed the release trap"
expect_reject \
  "release-readiness source custody rejects a missing pre-readiness release trap" \
  "release-readiness order marker drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/release-readiness-payload-validation-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
# These are exact production-source literals for a region-scoped mutation, not expressions here.
# shellcheck disable=SC2016
mutate_run_bounded_probe_once \
  "$case_file" \
  'if bytes(payload) != b"release_ready=1\n":' \
  'if False:'
expect_reject \
  "release-readiness source custody rejects bypass of exact payload validation" \
  "release-readiness canonical payload check drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/release-readiness-no-follow-removed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  $'last_error = "marker was never observed"\nflags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK' \
  $'last_error = "marker was never observed"\nflags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK'
expect_reject \
  "release-readiness source custody rejects removal of descriptor no-follow" \
  "decision/readiness no-follow descriptor custody drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/release-readiness-regular-link-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  $'        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:\n            raise RuntimeError("marker is not a single-link regular file")' \
  $'        if False:\n            raise RuntimeError("marker is not a single-link regular file")'
expect_reject \
  "release-readiness source custody rejects bypass of regular-file/link-count validation" \
  "release-readiness regular/link guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/release-readiness-mode-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  $'        if stat.S_IMODE(before.st_mode) != 0o600:\n            raise RuntimeError("marker mode is not 0600")' \
  $'        if False:\n            raise RuntimeError("marker mode is not 0600")'
expect_reject \
  "release-readiness source custody rejects bypass of mode-0600 validation" \
  "release-readiness mode guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/release-readiness-identity-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  '            raise RuntimeError("marker identity changed during descriptor replay")' \
  '            pass  # hostile mutation bypassed descriptor/leaf identity failure'
expect_reject \
  "release-readiness source custody rejects bypass of descriptor/leaf identity validation" \
  "release-readiness identity guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/decision-record-root-mode-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  $'if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_IMODE(root_metadata.st_mode) != 0o700:\n    raise SystemExit("decision root is not a mode-0700 directory")' \
  $'if False:\n    raise SystemExit("decision root is not a mode-0700 directory")'
expect_reject \
  "decision-record source custody rejects bypass of private-root mode validation" \
  "decision-record root mode guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/decision-record-regular-link-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  $'    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:\n        raise SystemExit("decision record is not a single-link regular file")' \
  $'    if False:\n        raise SystemExit("decision record is not a single-link regular file")'
expect_reject \
  "decision-record source custody rejects bypass of regular-file/link-count validation" \
  "decision-record regular/link guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/decision-record-identity-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  '    raise SystemExit("decision record identity changed during descriptor replay")' \
  '    pass  # hostile mutation bypassed decision descriptor/leaf identity failure'
expect_reject \
  "decision-record source custody rejects bypass of descriptor/leaf identity validation" \
  "decision-record identity guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/decision-record-timeout-payload-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  '    if raw != f"timeout_seconds={timeout_seconds}\n".encode("ascii"):' \
  '    if False:'
expect_reject \
  "decision-record source custody rejects bypass of exact timeout payload validation" \
  "decision-record timeout exact-payload guard drifted" \
  validate_release_readiness_order "$case_file"

case_file="$TEST_ROOT/decision-record-watchdog-payload-guard-bypassed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
mutate_run_bounded_probe_once \
  "$case_file" \
  $'    if re.fullmatch(\n        rb"watchdog_error=(?:invalid-timeout|probe-group-missing-at-start|"' \
  $'    if False and re.fullmatch(\n        rb"watchdog_error=(?:invalid-timeout|probe-group-missing-at-start|"'
expect_reject \
  "decision-record source custody rejects bypass of allowed watchdog-error payload validation" \
  "decision-record watchdog-error exact-payload guard drifted" \
  validate_release_readiness_order "$case_file"

expect_accept \
  "watchdog source custody records timeout classification before process-group termination" \
  validate_watchdog_timeout_order "$SELFTEST_SOURCE"

case_file="$TEST_ROOT/watchdog-timeout-order-reversed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = text.index("run_bounded_probe() {")
end = text.index("\n}\n\npublish_test_probe_status_atomically() {", start) + 2
region = text[start:end]
marker_line = 'publish_record("timeout", f"timeout_seconds={timeout_seconds}\\n")\n'
termination_block = (
    "try:\n"
    "    os.killpg(process_group, signal.SIGTERM)\n"
    "except ProcessLookupError:\n"
    "    pass\n"
)
if region.count(marker_line) != 1 or region.count(termination_block) != 1:
    raise SystemExit("watchdog order-mutation precondition drifted")
region = region.replace(marker_line, "", 1)
region = region.replace(termination_block, termination_block + marker_line, 1)
path.write_text(text[:start] + region + text[end:], encoding="utf-8", newline="\n")
PY
expect_reject \
  "watchdog source custody rejects TERM-before-timeout-classification reordering" \
  "watchdog timeout classification is not recorded before termination" \
  validate_watchdog_timeout_order "$case_file"

case_file="$TEST_ROOT/watchdog-late-group-order-reversed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = text.index("run_bounded_probe() {")
end = text.index("\n}\n\npublish_test_probe_status_atomically() {", start) + 2
region = text[start:end]
deadline = region.index("time.sleep(timeout_seconds)")
prefix = region[:deadline]
late = region[deadline:]
marker_line = 'publish_record("timeout", f"timeout_seconds={timeout_seconds}\\n")\n'
late_adjudication = "if observed_group != process_group:\n"
if late.count(marker_line) != 1:
    raise SystemExit("watchdog late-group-order mutation precondition drifted")
late = late.replace(marker_line, "", 1)
late_mismatch = late.find(late_adjudication)
if late_mismatch == -1:
    raise SystemExit("watchdog late-group-order mutation precondition drifted")
late = late[:late_mismatch] + marker_line + late[late_mismatch:]
path.write_text(text[:start] + prefix + late + text[end:], encoding="utf-8", newline="\n")
PY
expect_reject \
  "watchdog source custody rejects timeout classification before late group adjudication" \
  "watchdog timeout classification precedes late process-group adjudication" \
  validate_watchdog_timeout_order "$case_file"

case_file="$TEST_ROOT/watchdog-timeout-commit-removed.sh"
prepare_watchdog_mutant "$SELFTEST_SOURCE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = text.index("run_bounded_probe() {")
end = text.index("\n}\n\npublish_test_probe_status_atomically() {", start) + 2
region = text[start:end]
deadline = region.index("time.sleep(timeout_seconds)")
prefix = region[:deadline]
late = region[deadline:]
normal_classification = (
    "if not claim_decision():\n"
    "    raise SystemExit(0)\n"
    "classification_committed = True\n"
    'publish_record("timeout", f"timeout_seconds={timeout_seconds}\\n")\n'
)
mutated_classification = normal_classification.replace(
    "classification_committed = True\n", "", 1
)
if late.count(normal_classification) != 1:
    raise SystemExit("watchdog timeout-commit mutation precondition drifted")
late = late.replace(normal_classification, mutated_classification, 1)
path.write_text(text[:start] + prefix + late + text[end:], encoding="utf-8", newline="\n")
PY
expect_reject \
  "watchdog source custody rejects an uncommitted timeout marker" \
  "watchdog timeout classification is not committed before its marker" \
  validate_watchdog_timeout_order "$case_file"
C3_ACTIVE_FAMILY=""

extract_heredoc_containing() {
  local checker="$1"
  local marker="$2"
  local destination="$3"
  python3 -I -S - "$checker" "$marker" "$destination" <<'PY'
from pathlib import Path
import sys


checker = Path(sys.argv[1])
marker = sys.argv[2]
destination = Path(sys.argv[3])
lines = checker.read_text(encoding="utf-8").splitlines(keepends=True)
matches = [index for index, line in enumerate(lines) if marker in line]
if len(matches) != 1:
    raise SystemExit(
        f"checker marker must occur exactly once: {marker!r}; observed {len(matches)}"
    )
marker_index = matches[0]
start = None
for index in range(marker_index, -1, -1):
    if "<<'PY'" in lines[index]:
        start = index + 1
        break
if start is None:
    raise SystemExit(f"no containing Python heredoc starts before marker: {marker!r}")
end = None
for index in range(marker_index + 1, len(lines)):
    if lines[index].rstrip("\r\n") == "PY":
        end = index
        break
if end is None or not start <= marker_index < end:
    raise SystemExit(f"no containing Python heredoc ends after marker: {marker!r}")
body = "".join(lines[start:end])
if not body.endswith("\n"):
    raise SystemExit(f"extracted Python heredoc lacks LF termination: {marker!r}")
compile(body, str(checker), "exec")
destination.write_text(body, encoding="utf-8", newline="\n")
PY
}

extract_shell_region() {
  local checker="$1"
  local start_marker="$2"
  local end_marker="$3"
  local destination="$4"
  python3 -I -S - "$checker" "$start_marker" "$end_marker" "$destination" <<'PY'
from pathlib import Path
import sys


checker = Path(sys.argv[1])
start_marker = sys.argv[2]
end_marker = sys.argv[3]
destination = Path(sys.argv[4])
lines = checker.read_text(encoding="utf-8").splitlines(keepends=True)
starts = [index for index, line in enumerate(lines) if start_marker in line]
ends = [index for index, line in enumerate(lines) if end_marker in line]
if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
    raise SystemExit(
        "checker shell-region markers must occur once in order: "
        f"start={start_marker!r}:{starts!r}; end={end_marker!r}:{ends!r}"
    )
body = "".join(lines[starts[0] : ends[0]])
if not body.endswith("\n"):
    raise SystemExit("extracted shell region lacks LF termination")
destination.write_text(
    "#!/usr/bin/env bash\nset -euo pipefail\n" + body,
    encoding="utf-8",
    newline="\n",
)
PY
}

copy_manifest_fixture() {
  local destination="$1"
  local parent
  local relative
  local paths=(
    "scripts/check-mathematical-workflow-pdf.sh"
    "scripts/check-mathematical-workflow-pdf-self-test.sh"
    "scripts/sync-mathematical-workflow-tex.py"
    "scripts/sync-mathematical-workflow-tex-self-test.py"
    "scripts/check-citation-edge-countermodel.py"
    "scripts/check-citation-edge-countermodel-self-test.py"
    "scripts/check-formal-pdf-log.sh"
    "scripts/check-formal-pdf-log-self-test.sh"
    "scripts/compare-formal-pdf-renders.py"
    "scripts/compare-formal-pdf-renders-self-test.py"
    "audit/evidence/x-thread-citation-edge-application.json"
    "audit/evidence/x-thread-citation-source-manifest.json"
    "audit/formal/latex/mathematical-problem-solving-workflow.tex"
    "audit/formal/latex/pid-rs-report-tables.sty"
    "audit/formal/latex/pid-rs-workflow-publication.sty"
    "audit/formal/requirements-pdf.txt"
    "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.svg"
    "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.pdf"
    "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.svg"
    "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.pdf"
    "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.svg"
    "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.pdf"
    "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.svg"
    "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.pdf"
    "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
    "output/pdf/mathematical-problem-solving-workflow.pdf"
    "output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv"
  )
  mkdir -p "$destination"
  for relative in "${paths[@]}"; do
    if [[ ! -f "$ROOT/$relative" ]]; then
      fail "fixture source is absent: $relative"
    fi
    parent="${relative%/*}"
    if [[ "$parent" == "$relative" ]]; then
      parent="."
    fi
    mkdir -p "$destination/$parent"
    cp "$ROOT/$relative" "$destination/$relative"
    # The production checker executes this suite from a mode-0444 read-only source snapshot.
    # Mutation fixtures are private working copies, so restore only owner write permission after
    # copying; otherwise `cp` preserves 0444 and the first deliberate source mutation cannot run.
    chmod u+w "$destination/$relative"
  done
}

BASE_REPOSITORY="$TEST_ROOT/base-repository"
copy_manifest_fixture "$BASE_REPOSITORY"
CHECKER="$BASE_REPOSITORY/scripts/check-mathematical-workflow-pdf.sh"
BASE_PDF="$BASE_REPOSITORY/output/pdf/mathematical-problem-solving-workflow.pdf"
BASE_RENDERING_RECEIPT="$BASE_REPOSITORY/output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv"
BASE_MARKDOWN="$BASE_REPOSITORY/MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
BASE_FIGURE_DIR="$BASE_REPOSITORY/audit/formal/latex/figures/mathematical-workflow"

CAPTURE_VALIDATOR="$TEST_ROOT/capture-manifest.py"
EXECUTABLE_VALIDATOR="$TEST_ROOT/capture-executables.py"
SNAPSHOT_VALIDATOR="$TEST_ROOT/verify-snapshot.py"
SOURCE_SEMANTIC_VALIDATOR="$TEST_ROOT/validate-source-semantics.py"
VISUAL_VALIDATOR="$TEST_ROOT/validate-visual-receipt.py"
SVG_VALIDATOR="$TEST_ROOT/validate-svg.py"
REPORT_VALIDATOR="$TEST_ROOT/validate-report-pdf.py"
NAVIGATION_COMPARATOR="$TEST_ROOT/compare-navigation.py"
RENDERING_RECEIPT_VALIDATOR="$TEST_ROOT/validate-rendering-receipt.py"
REFRESH_WRITER="$TEST_ROOT/refresh-artifacts.py"
RENDERED_TEXT_VALIDATOR="$TEST_ROOT/validate-rendered-text.sh"
FONT_SOURCE_VALIDATOR="$TEST_ROOT/validate-font-source.py"
FORMAT_SOURCE_VALIDATOR="$TEST_ROOT/validate-format-source.py"
FORMAT_REPLAY_VALIDATOR="$TEST_ROOT/verify-captured-format.py"
TEXMFDEBIAN_QUERY_VALIDATOR="$TEST_ROOT/validate-texmfdebian-query.sh"
ENTRY_WRAPPER_WRITER="$TEST_ROOT/write-entry-wrapper.py"
FLS_CLOSURE_VALIDATOR="$TEST_ROOT/validate-fls-closure.py"
extract_heredoc_containing "$CHECKER" "def read_regular_beneath" "$CAPTURE_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  'mathematical workflow PDF check: executable capture {detail}' \
  "$EXECUTABLE_VALIDATOR"
extract_heredoc_containing "$CHECKER" "root_status = root.lstat()" "$SNAPSHOT_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  "direct_source_literals = (" \
  "$SOURCE_SEMANTIC_VALIDATOR"
extract_heredoc_containing "$CHECKER" "expected_fields = {" "$VISUAL_VALIDATOR"
extract_heredoc_containing "$CHECKER" "expected_geometry = {" "$SVG_VALIDATOR"
extract_heredoc_containing "$CHECKER" "def validate_action" "$REPORT_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  "coordinate_tolerance_points = 2.0" \
  "$NAVIGATION_COMPARATOR"
extract_heredoc_containing "$CHECKER" \
  "def canonical_uint(raw: str, label: str, field: str)" \
  "$RENDERING_RECEIPT_VALIDATOR"
extract_heredoc_containing "$CHECKER" "def open_directory_beneath" "$REFRESH_WRITER"
extract_shell_region \
  "$CHECKER" \
  "required_text=(" \
  "if grep -F -- '??'" \
  "$RENDERED_TEXT_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  "allowed_relative_paths = {" \
  "$FONT_SOURCE_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  'mathematical workflow PDF check: format source {detail}' \
  "$FORMAT_SOURCE_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  "captured format verification lacks" \
  "$FORMAT_REPLAY_VALIDATOR"
extract_shell_region \
  "$CHECKER" \
  "adjudicate_texmfdebian_query() {" \
  "# TEXMFDEBIAN_QUERY_END" \
  "$TEXMFDEBIAN_QUERY_VALIDATOR"
extract_heredoc_containing \
  "$CHECKER" \
  'mathematical workflow PDF check: entry-wrapper capture {detail}' \
  "$ENTRY_WRAPPER_WRITER"
extract_heredoc_containing \
  "$CHECKER" \
  "def is_forbidden_tex_map_path" \
  "$FLS_CLOSURE_VALIDATOR"
bash -n "$RENDERED_TEXT_VALIDATOR"
bash -n "$TEXMFDEBIAN_QUERY_VALIDATOR"
pass "production validator heredocs and rendered-text/font-query regions extract uniquely and parse"

run_texmfdebian_query_validator() {
  local query_status="$1"
  local query_output="$2"
  bash -c \
    'source "$1"; adjudicate_texmfdebian_query "$2" "$3"' \
    bash "$TEXMFDEBIAN_QUERY_VALIDATOR" "$query_status" "$query_output"
}

expect_accept \
  "Debian overlay query accepts a successful exact-root result" \
  run_texmfdebian_query_validator 0 /usr/share/texmf
expect_accept \
  "Debian overlay query accepts the normalized absent-variable value after command substitution" \
  run_texmfdebian_query_validator 1 ""
expect_reject \
  "Debian overlay query rejects an empty unexpected failure status" \
  "Debian TeX overlay query failed unexpectedly" \
  run_texmfdebian_query_validator 2 ""
expect_reject \
  "Debian overlay query rejects output attached to absent-variable status" \
  "Debian TeX overlay query failed unexpectedly" \
  run_texmfdebian_query_validator 1 /hostile/overlay
expect_reject \
  "Debian overlay query rejects success without a declared root" \
  "Debian TeX overlay query failed unexpectedly" \
  run_texmfdebian_query_validator 0 ""

FONT_FIXTURE="$TEST_ROOT/font-source-fixture"
FONT_DIST="$FONT_FIXTURE/texmf-dist"
FONT_DEBIAN="$FONT_FIXTURE/texmf-debian"
FONT_OUTSIDE="$FONT_FIXTURE/outside"
mkdir -p \
  "$FONT_DIST/fonts/opentype/adobe/sourcesanspro" \
  "$FONT_DIST/fonts/opentype/public/lm" \
  "$FONT_DEBIAN/fonts/opentype/public/lm" \
  "$FONT_DEBIAN/fonts/opentype/public/lm-math" \
  "$FONT_OUTSIDE"
printf 'source sans\n' >"$FONT_DIST/fonts/opentype/adobe/sourcesanspro/SourceSansPro-Regular.otf"
printf 'dist latin modern\n' >"$FONT_DIST/fonts/opentype/public/lm/lmroman10-regular.otf"
printf 'debian latin modern\n' >"$FONT_DEBIAN/fonts/opentype/public/lm/lmroman10-regular.otf"
printf 'debian latin modern math\n' >"$FONT_DEBIAN/fonts/opentype/public/lm-math/latinmodern-math.otf"
printf 'outside\n' >"$FONT_OUTSIDE/lmroman10-regular.otf"

run_font_capture() {
  local font_name="$1"
  local query_path="$2"
  local dist_root="$3"
  local debian_root="$4"
  local destination_root="$5"
  mkdir "$destination_root"
  python3 -I -S "$FONT_SOURCE_VALIDATOR" \
    "$font_name" "$query_path" "$dist_root" "$debian_root" "$destination_root" || return $?
  cmp "$query_path" "$destination_root/$font_name"
}

expect_accept \
  "font source admits the exact TeX Live Source Sans path" \
  run_font_capture \
  SourceSansPro-Regular.otf \
  "$FONT_DIST/fonts/opentype/adobe/sourcesanspro/SourceSansPro-Regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/copied-source-sans.otf"
expect_accept \
  "font source admits the exact TeX Live Latin Modern path" \
  run_font_capture \
  lmroman10-regular.otf \
  "$FONT_DIST/fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/copied-dist-lm.otf"
expect_accept \
  "font source admits Ubuntu's exact TEXMFDEBIAN Latin Modern path" \
  run_font_capture \
  lmroman10-regular.otf \
  "$FONT_DEBIAN/fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/copied-debian-lm.otf"
expect_accept \
  "font source admits Ubuntu's exact TEXMFDEBIAN Latin Modern Math path" \
  run_font_capture \
  latinmodern-math.otf \
  "$FONT_DEBIAN/fonts/opentype/public/lm-math/latinmodern-math.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/copied-debian-lm-math.otf"
expect_reject \
  "font source rejects an empty Kpathsea result" \
  "font source query is empty for lmroman10-regular.otf" \
  run_font_capture \
  lmroman10-regular.otf "" "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/empty.otf"
expect_reject \
  "font source rejects a multiline Kpathsea result" \
  "font source query is not one absolute LF-free path for lmroman10-regular.otf" \
  run_font_capture \
  lmroman10-regular.otf $'/first\n/second' "$FONT_DIST" "$FONT_DEBIAN" \
  "$FONT_FIXTURE/multiline.otf"
expect_reject \
  "font source rejects a path outside both exact TeX roots" \
  "font source query escapes the admitted exact TeX roots for lmroman10-regular.otf" \
  run_font_capture \
  lmroman10-regular.otf "$FONT_OUTSIDE/lmroman10-regular.otf" "$FONT_DIST" "$FONT_DEBIAN" \
  "$FONT_FIXTURE/outside.otf"
expect_reject \
  "font source rejects Source Sans selected from the Debian overlay" \
  "font source query escapes the admitted exact TeX roots for SourceSansPro-Regular.otf" \
  run_font_capture \
  SourceSansPro-Regular.otf \
  "$FONT_DEBIAN/fonts/opentype/adobe/sourcesanspro/SourceSansPro-Regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/wrong-root.otf"
expect_reject \
  "font source rejects redundant-slash query spelling" \
  "font source query is not canonically spelled for lmroman10-regular.otf" \
  run_font_capture \
  lmroman10-regular.otf \
  "$FONT_DIST//fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/redundant-slash.otf"
expect_reject \
  "font source rejects dot-component query spelling" \
  "font source query is not canonically spelled for lmroman10-regular.otf" \
  run_font_capture \
  lmroman10-regular.otf \
  "$FONT_DIST/./fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/dot-component.otf"
ln -s \
  "$FONT_DIST/fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_DEBIAN/fonts/opentype/public/lm/lmroman10-italic.otf"
expect_reject \
  "font source rejects a symlink at an otherwise allowlisted path" \
  "font source is not a direct regular file for lmroman10-italic.otf" \
  run_font_capture \
  lmroman10-italic.otf \
  "$FONT_DEBIAN/fonts/opentype/public/lm/lmroman10-italic.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/symlink-leaf.otf"
FONT_PARENT_SYMLINK="$FONT_FIXTURE/parent-symlink-root"
mkdir -p "$FONT_PARENT_SYMLINK"
ln -s "$FONT_DIST/fonts" "$FONT_PARENT_SYMLINK/fonts"
expect_reject \
  "font source rejects a symlinked intermediate directory" \
  "font source cannot open direct font-directory component 'fonts'" \
  run_font_capture \
  lmroman10-regular.otf \
  "$FONT_PARENT_SYMLINK/fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_PARENT_SYMLINK" "$FONT_DEBIAN" "$FONT_FIXTURE/symlink-parent.otf"
python3 -I -S -c 'import os, sys; os.mkfifo(sys.argv[1])' \
  "$FONT_DEBIAN/fonts/opentype/public/lm/lmroman10-bold.otf"
expect_reject \
  "font source rejects a FIFO without blocking" \
  "font source is not a direct regular file for lmroman10-bold.otf" \
  run_font_capture \
  lmroman10-bold.otf \
  "$FONT_DEBIAN/fonts/opentype/public/lm/lmroman10-bold.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_FIXTURE/fifo-source.otf"
FONT_DESTINATION_OUTSIDE="$FONT_FIXTURE/destination-outside"
FONT_DESTINATION_SYMLINK="$FONT_FIXTURE/destination-symlink"
mkdir "$FONT_DESTINATION_OUTSIDE"
ln -s "$FONT_DESTINATION_OUTSIDE" "$FONT_DESTINATION_SYMLINK"
expect_reject \
  "font capture rejects a symlinked destination directory" \
  "font source cannot open direct directory component 'destination-symlink'" \
  python3 -I -S "$FONT_SOURCE_VALIDATOR" \
  lmroman10-regular.otf \
  "$FONT_DIST/fonts/opentype/public/lm/lmroman10-regular.otf" \
  "$FONT_DIST" "$FONT_DEBIAN" "$FONT_DESTINATION_SYMLINK"

FORMAT_FIXTURE="$TEST_ROOT/format-source-fixture"
FORMAT_SYSVAR="$FORMAT_FIXTURE/texmf-sysvar"
FORMAT_SOURCE="$FORMAT_SYSVAR/web2c/luahbtex/lualatex.fmt"
FORMAT_OUTSIDE="$FORMAT_FIXTURE/outside/lualatex.fmt"
mkdir -p \
  "$FORMAT_SYSVAR/web2c/luahbtex" \
  "$FORMAT_FIXTURE/outside"
printf 'exact captured LuaLaTeX format fixture\n' >"$FORMAT_SOURCE"
printf 'wrong generated format leaf\n' >"$FORMAT_SYSVAR/web2c/luahbtex/xelatex.fmt"
printf 'outside generated format root\n' >"$FORMAT_OUTSIDE"

run_format_capture() {
  local query_path="$1"
  local source_root="$2"
  local destination_root="$3"
  local receipt
  local captured_size
  local captured_sha256
  mkdir "$destination_root"
  receipt="$(python3 -I -S "$FORMAT_SOURCE_VALIDATOR" \
    "$query_path" "$source_root" "$destination_root")" || return $?
  IFS=$'\t' read -r captured_size captured_sha256 <<<"$receipt"
  if [[ ! "$captured_size" =~ ^[1-9][0-9]*$ \
      || ! "$captured_sha256" =~ ^[0-9a-f]{64}$ ]]; then
    echo "format fixture capture returned a malformed receipt" >&2
    return 1
  fi
  chmod 0555 "$destination_root"
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
    "$destination_root/lualatex.fmt" "$captured_size" "$captured_sha256" || return $?
  cmp "$query_path" "$destination_root/lualatex.fmt"
}

run_private_format_lookup() {
  local format_root="$1"
  local texformats_value="$2"
  local search_path
  local selected_path
  search_path="$(env -i \
    "HOME=$FORMAT_FIXTURE" \
    "TEXFORMATS=$texformats_value" \
    "$KPSEWHICH_COMMAND" \
      --engine=luahbtex \
      --progname=lualatex \
      --show-path=fmt)" || return $?
  selected_path="$(env -i \
    "HOME=$FORMAT_FIXTURE" \
    "TEXFORMATS=$texformats_value" \
    "$KPSEWHICH_COMMAND" \
      --engine=luahbtex \
      --progname=lualatex \
      --must-exist \
      --format=fmt \
      lualatex.fmt)" || return $?
  if [[ "$search_path" != "$format_root" || "$selected_path" != "$format_root/lualatex.fmt" ]]; then
    echo "private format lookup escaped its exact one-directory search path" >&2
    return 1
  fi
}

validate_format_custody_source() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")


def fail(detail: str) -> None:
    raise SystemExit(f"format-custody source invariant drifted: {detail}")


required_once = (
    'FORMAT_PATH="$FORMAT_ROOT/lualatex.fmt"',
    'relative = Path("web2c/luahbtex") / format_name',
    'if source != texmf_sysvar / relative:',
    'source_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK',
    'destination_descriptor = os.open(\n            format_name,\n            os.O_RDWR\n'
    '            | os.O_CREAT\n            | os.O_EXCL',
    'os.fchmod(destination_descriptor, 0o444)',
    'chmod 0555 "$FORMAT_ROOT"',
    'local run_format_search_path=""',
    'cd "$run_dir"\n      env -i \\\n        "${CLEAN_BASE_ENV[@]}" \\\n'
    '        "${run_environment[@]}" \\\n'
    '        "TEXINPUTS=$SNAPSHOT_ROOT/audit/formal/latex:$REPORT_FIGURE_DIR:"',
    'if [[ "$PRIVATE_FORMAT_SEARCH_PATH" != "$FORMAT_ROOT" \\\n    || "$PRIVATE_FORMAT_QUERY" != "$FORMAT_PATH" ]]; then',
    'if [[ "$run_format_search_path" != "$FORMAT_ROOT" \\\n      || "$run_format_query" != "$FORMAT_PATH" ]]; then',
    'if raw_format_inputs != {format_path}:',
    'if resolved_format_inputs != {format_path}:',
    'if path == format_path:\n                continue',
    'if path == format_path and (size, digest) != (format_bytes, format_sha256):',
    'if digest.hexdigest() != expected_sha256:',
)
for literal in required_once:
    if text.count(literal) != 1:
        fail(f"required exact literal count differs from one: {literal!r}")
if text.count('if os.listdir(root_descriptor) != [path.name]:') != 2:
    fail("sealed one-file root inventory is not checked before and after replay")
expected_counts = {
    "--engine=luahbtex": 5,
    "--progname=lualatex": 5,
    "--show-path=fmt": 2,
    'TEXFORMATS=$FORMAT_ROOT': 2,
    "verify_captured_format_exact": 4,
    "root_chain_before != root_chain_after": 2,
    "destination_chain_before != destination_chain_after": 2,
    "file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK": 2,
    "if str(source) != query_result:": 2,
    "if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:": 2,
    "format snapshot $FORMAT_BYTES bytes sha256 $FORMAT_SHA256": 3,
    "format source $FORMAT_QUERY; format snapshot $FORMAT_BYTES bytes sha256 $FORMAT_SHA256": 3,
}
for literal, expected in expected_counts.items():
    if text.count(literal) != expected:
        fail(f"literal inventory for {literal!r} is {text.count(literal)}, expected {expected}")
for forbidden in ('TEXFORMATS=$FORMAT_ROOT:', 'TEXFORMATS=:$FORMAT_ROOT', 'format_root ='):
    if forbidden in text:
        fail(f"forbidden broad format admission is present: {forbidden!r}")
try:
    capture = text.index('if ! FORMAT_CAPTURE="$(capture_format_exact')
    seal = text.index('chmod 0555 "$FORMAT_ROOT"')
    private_preflight = text.index('if ! PRIVATE_FORMAT_SEARCH_PATH="$(env -i')
    build_definition = text.index("build_report() {")
    build_a = text.index('build_report "build-a"')
    build_b = text.index('build_report "build-b"')
    build_end = text.index('\n}\n\nbuild_report "build-a"', build_definition)
    build_region = text[build_definition:build_end]
    while_loop = build_region.index('  while [[ "$pass_number" -le 6 ]]; do')
    per_pass_verify = build_region.index("    if ! verify_captured_format_exact")
    compiler_call = build_region.index("        lualatex \\")
    final_verify = text.index("if ! verify_captured_format_exact", build_b)
    fls_closure = text.index(
        'python3 -I -S - \\\n  "$BUILD_ROOT/build-a"', final_verify
    )
except ValueError as error:
    fail(f"ordered format-custody source region is absent: {error}")
if not capture < seal < private_preflight < build_definition < build_a < build_b:
    fail("capture, seal, preflight, and two-build ordering is not strict")
if not while_loop < per_pass_verify < compiler_call:
    fail("per-pass format verification is not inside the loop before the compiler")
if not build_a < build_b < final_verify < fls_closure:
    fail("final format verification is not strictly after both builds and before FLS capture")
PY
}

mutate_occurrence() {
  local path="$1"
  local old="$2"
  local new="$3"
  local occurrence="$4"
  python3 -I -S - "$path" "$old" "$new" "$occurrence" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
old = sys.argv[2]
new = sys.argv[3]
occurrence = int(sys.argv[4])
text = path.read_text(encoding="utf-8")
starts = []
offset = 0
while True:
    index = text.find(old, offset)
    if index < 0:
        break
    starts.append(index)
    offset = index + len(old)
if occurrence < 1 or occurrence > len(starts):
    raise SystemExit(f"mutation occurrence {occurrence} is outside 1..{len(starts)}")
index = starts[occurrence - 1]
text = text[:index] + new + text[index + len(old):]
path.write_text(text, encoding="utf-8", newline="\n")
PY
}

move_format_verifier_for_mutation() {
  local path="$1"
  local mode="$2"
  python3 -I -S - "$path" "$mode" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
mode = sys.argv[2]
text = path.read_text(encoding="utf-8")
if mode in ("before-loop", "after-compiler"):
    build_start = text.index("build_report() {")
    build_end = text.index('\n}\n\nbuild_report "build-a"', build_start)
    region = text[build_start:build_end]
    verify_start = region.index("    if ! verify_captured_format_exact")
    verify_end = region.index("    fi\n", verify_start) + len("    fi\n")
    verify_block = region[verify_start:verify_end]
    region = region[:verify_start] + region[verify_end:]
    if mode == "before-loop":
        insertion = region.index('  while [[ "$pass_number" -le 6 ]]; do')
    else:
        compiler = region.index("        lualatex \\")
        insertion = region.index("    fi\n", compiler) + len("    fi\n")
    region = region[:insertion] + verify_block + region[insertion:]
    text = text[:build_start] + region + text[build_end:]
elif mode == "before-builds":
    build_a = text.index('build_report "build-a"')
    build_b = text.index('build_report "build-b"', build_a)
    verify_start = text.index("if ! verify_captured_format_exact", build_b)
    verify_end = text.index("fi\n", verify_start) + len("fi\n")
    verify_block = text[verify_start:verify_end]
    text = text[:verify_start] + text[verify_end:]
    build_a = text.index('build_report "build-a"')
    text = text[:build_a] + verify_block + text[build_a:]
else:
    raise SystemExit(f"unknown format-verifier mutation mode: {mode}")
path.write_text(text, encoding="utf-8", newline="\n")
PY
}

C3_ACTIVE_FAMILY="format-custody"
FORMAT_PRIVATE_ROOT="$FORMAT_FIXTURE/private-format"
expect_accept \
  "format custody captures the exact generated leaf into a byte-identical sealed one-file root" \
  run_format_capture "$FORMAT_SOURCE" "$FORMAT_SYSVAR" "$FORMAT_PRIVATE_ROOT"
expect_reject \
  "format custody rejects a different leaf beneath the same generated-state root" \
  "format source query escapes the one admitted generated-format leaf" \
  run_format_capture \
  "$FORMAT_SYSVAR/web2c/luahbtex/xelatex.fmt" \
  "$FORMAT_SYSVAR" "$FORMAT_FIXTURE/wrong-leaf"
expect_reject \
  "format custody rejects the expected leaf outside the exact generated-state root" \
  "format source query escapes the one admitted generated-format leaf" \
  run_format_capture "$FORMAT_OUTSIDE" "$FORMAT_SYSVAR" "$FORMAT_FIXTURE/outside-root"
expect_reject \
  "format custody rejects an empty Kpathsea result" \
  "format source query is empty" \
  run_format_capture "" "$FORMAT_SYSVAR" "$FORMAT_FIXTURE/empty-query"
expect_reject \
  "format custody rejects a multiline Kpathsea result" \
  "format source query is not one absolute LF-free path" \
  run_format_capture \
  $'/first\n/second' "$FORMAT_SYSVAR" "$FORMAT_FIXTURE/multiline-query"
expect_reject \
  "format custody rejects a relative Kpathsea result" \
  "format source query is not one absolute LF-free path" \
  run_format_capture \
  web2c/luahbtex/lualatex.fmt "$FORMAT_SYSVAR" "$FORMAT_FIXTURE/relative-query"
expect_reject \
  "format custody rejects redundant-slash spelling of the otherwise exact source" \
  "format source query is not canonically spelled" \
  run_format_capture \
  "$FORMAT_SYSVAR//web2c/luahbtex/lualatex.fmt" \
  "$FORMAT_SYSVAR" "$FORMAT_FIXTURE/redundant-slash-query"

FORMAT_EMPTY_SYSVAR="$FORMAT_FIXTURE/empty-source-sysvar"
mkdir -p "$FORMAT_EMPTY_SYSVAR/web2c/luahbtex"
python3 -I -S -c 'from pathlib import Path; import sys; Path(sys.argv[1]).touch()' \
  "$FORMAT_EMPTY_SYSVAR/web2c/luahbtex/lualatex.fmt"
expect_reject \
  "format capture rejects an empty exact source before reading" \
  "format source size is outside the 1..67108864-byte bound: 0" \
  run_format_capture \
  "$FORMAT_EMPTY_SYSVAR/web2c/luahbtex/lualatex.fmt" \
  "$FORMAT_EMPTY_SYSVAR" "$FORMAT_FIXTURE/empty-source"

FORMAT_OVERSIZE_SYSVAR="$FORMAT_FIXTURE/oversize-source-sysvar"
mkdir -p "$FORMAT_OVERSIZE_SYSVAR/web2c/luahbtex"
python3 -I -S -c \
  'import sys; stream = open(sys.argv[1], "xb"); stream.truncate(64 * 1024 * 1024 + 1); stream.close()' \
  "$FORMAT_OVERSIZE_SYSVAR/web2c/luahbtex/lualatex.fmt"
expect_reject \
  "format capture rejects a sparse 64-MiB-plus-one exact source before reading" \
  "format source size is outside the 1..67108864-byte bound: 67108865" \
  run_format_capture \
  "$FORMAT_OVERSIZE_SYSVAR/web2c/luahbtex/lualatex.fmt" \
  "$FORMAT_OVERSIZE_SYSVAR" "$FORMAT_FIXTURE/oversize-source"
expect_accept \
  "private TEXFORMATS exposes exactly one search directory and its captured format" \
  run_private_format_lookup "$FORMAT_PRIVATE_ROOT" "$FORMAT_PRIVATE_ROOT"
expect_reject \
  "private TEXFORMATS rejects a trailing-colon expansion even when the captured format wins" \
  "private format lookup escaped its exact one-directory search path" \
  run_private_format_lookup "$FORMAT_PRIVATE_ROOT" "$FORMAT_PRIVATE_ROOT:"
expect_accept \
  "production source preserves exact format capture, sealing, lookup, FLS, and build ordering" \
  validate_format_custody_source "$CHECKER"

case_file="$TEST_ROOT/format-engine-selector-removed.sh"
cp "$CHECKER" "$case_file"
mutate_occurrence "$case_file" '--engine=luahbtex' '--engine=hostile' 1
expect_reject \
  "format source custody rejects removal of the exact LuaHBTeX engine selector" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-build-before-capture.sh"
cp "$CHECKER" "$case_file"
replace_once "$case_file" 'build_report "build-a"' ': # displaced build-a call'
# Exact production-source literal; this self-test shell must not expand the command substitution.
# shellcheck disable=SC2016
replace_once \
  "$case_file" \
  'if ! FORMAT_CAPTURE="$(capture_format_exact' \
  $'build_report "build-a"\nif ! FORMAT_CAPTURE="$(capture_format_exact'
expect_reject \
  "format source custody rejects compilation moved before capture and sealing" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-root-seal-weakened.sh"
cp "$CHECKER" "$case_file"
# Exact production-source literals; this self-test shell must not expand FORMAT_ROOT.
# shellcheck disable=SC2016
replace_once "$case_file" 'chmod 0555 "$FORMAT_ROOT"' 'chmod 0755 "$FORMAT_ROOT"'
expect_reject \
  "format source custody rejects weakening the read-only root snapshot guard" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-fls-admission-broadened.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  $'if path == format_path:\n                continue' \
  $'if beneath(path, texmf_root):\n                continue'
expect_reject \
  "format source custody rejects broad TeX-root admission in place of exact-path admission" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

FORMAT_SYMLINK_SYSVAR="$FORMAT_FIXTURE/symlink-sysvar"
mkdir -p "$FORMAT_SYMLINK_SYSVAR/web2c/luahbtex"
ln -s "$FORMAT_SOURCE" "$FORMAT_SYMLINK_SYSVAR/web2c/luahbtex/lualatex.fmt"
expect_reject \
  "format capture rejects a symlink at the otherwise exact generated-format leaf" \
  "format source is not a direct regular file" \
  run_format_capture \
  "$FORMAT_SYMLINK_SYSVAR/web2c/luahbtex/lualatex.fmt" \
  "$FORMAT_SYMLINK_SYSVAR" "$FORMAT_FIXTURE/source-leaf-symlink"

FORMAT_PARENT_SYMLINK_SYSVAR="$FORMAT_FIXTURE/parent-symlink-sysvar"
mkdir "$FORMAT_PARENT_SYMLINK_SYSVAR"
ln -s "$FORMAT_SYSVAR/web2c" "$FORMAT_PARENT_SYMLINK_SYSVAR/web2c"
expect_reject \
  "format capture rejects a symlinked intermediate generated-format directory" \
  "format source cannot open direct format-directory component 'web2c'" \
  run_format_capture \
  "$FORMAT_PARENT_SYMLINK_SYSVAR/web2c/luahbtex/lualatex.fmt" \
  "$FORMAT_PARENT_SYMLINK_SYSVAR" "$FORMAT_FIXTURE/source-parent-symlink"

FORMAT_FIFO_SYSVAR="$FORMAT_FIXTURE/fifo-sysvar"
mkdir -p "$FORMAT_FIFO_SYSVAR/web2c/luahbtex"
python3 -I -S -c 'import os, sys; os.mkfifo(sys.argv[1])' \
  "$FORMAT_FIFO_SYSVAR/web2c/luahbtex/lualatex.fmt"
expect_reject \
  "format capture rejects a FIFO at the exact leaf without blocking" \
  "format source is not a direct regular file" \
  run_format_capture \
  "$FORMAT_FIFO_SYSVAR/web2c/luahbtex/lualatex.fmt" \
  "$FORMAT_FIFO_SYSVAR" "$FORMAT_FIXTURE/source-fifo"

FORMAT_DESTINATION_OUTSIDE="$FORMAT_FIXTURE/destination-outside"
FORMAT_DESTINATION_SYMLINK="$FORMAT_FIXTURE/destination-symlink"
mkdir "$FORMAT_DESTINATION_OUTSIDE"
ln -s "$FORMAT_DESTINATION_OUTSIDE" "$FORMAT_DESTINATION_SYMLINK"
expect_reject \
  "format capture rejects a symlinked private destination root" \
  "format source cannot open direct directory component 'destination-symlink'" \
  python3 -I -S "$FORMAT_SOURCE_VALIDATOR" \
  "$FORMAT_SOURCE" "$FORMAT_SYSVAR" "$FORMAT_DESTINATION_SYMLINK"

FORMAT_PREEXISTING_DESTINATION="$FORMAT_FIXTURE/preexisting-destination"
mkdir "$FORMAT_PREEXISTING_DESTINATION"
python3 -I -S -c 'from pathlib import Path; import sys; Path(sys.argv[1]).touch()' \
  "$FORMAT_PREEXISTING_DESTINATION/lualatex.fmt"
expect_reject \
  "format capture rejects an empty preexisting destination leaf" \
  "format source cannot create the exclusive private format leaf" \
  python3 -I -S "$FORMAT_SOURCE_VALIDATOR" \
  "$FORMAT_SOURCE" "$FORMAT_SYSVAR" "$FORMAT_PREEXISTING_DESTINATION"

FORMAT_FIXTURE_RECEIPT="$(python3 -I -S - "$FORMAT_SOURCE" <<'PY'
from pathlib import Path
import hashlib
import sys


data = Path(sys.argv[1]).read_bytes()
print(f"{len(data)}\t{hashlib.sha256(data).hexdigest()}")
PY
)"
IFS=$'\t' read -r FORMAT_FIXTURE_BYTES FORMAT_FIXTURE_SHA256 <<<"$FORMAT_FIXTURE_RECEIPT"
if [[ ! "$FORMAT_FIXTURE_BYTES" =~ ^[1-9][0-9]*$ \
    || ! "$FORMAT_FIXTURE_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  fail "format replay fixture receipt is malformed"
fi

make_format_replay_fixture() {
  local root="$1"
  mkdir "$root"
  cp "$FORMAT_SOURCE" "$root/lualatex.fmt"
  chmod 0444 "$root/lualatex.fmt"
  chmod 0555 "$root"
}

case_dir="$FORMAT_FIXTURE/replay-wrong-digest"
make_format_replay_fixture "$case_dir"
expect_reject \
  "format replay rejects a wrong same-size digest receipt" \
  "captured format digest receipt drifted" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE_BYTES" \
  0000000000000000000000000000000000000000000000000000000000000000

case_dir="$FORMAT_FIXTURE/replay-wrong-size"
make_format_replay_fixture "$case_dir"
expect_reject \
  "format replay rejects a wrong size receipt" \
  "captured format mode or size receipt drifted" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$((FORMAT_FIXTURE_BYTES + 1))" "$FORMAT_FIXTURE_SHA256"

case_dir="$FORMAT_FIXTURE/replay-wrong-file-mode"
make_format_replay_fixture "$case_dir"
chmod 0644 "$case_dir/lualatex.fmt"
expect_reject \
  "format replay rejects a writable captured-format file" \
  "captured format mode or size receipt drifted" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE_BYTES" "$FORMAT_FIXTURE_SHA256"

case_dir="$FORMAT_FIXTURE/replay-wrong-root-mode"
make_format_replay_fixture "$case_dir"
chmod 0755 "$case_dir"
expect_reject \
  "format replay rejects a writable private-format root" \
  "captured format root is not a mode-0555 directory" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE_BYTES" "$FORMAT_FIXTURE_SHA256"

case_dir="$FORMAT_FIXTURE/replay-hardlink"
make_format_replay_fixture "$case_dir"
ln "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE/replay-hardlink-alias"
expect_reject \
  "format replay rejects a multiply linked captured-format file" \
  "captured format is not a single-link regular file" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE_BYTES" "$FORMAT_FIXTURE_SHA256"

case_dir="$FORMAT_FIXTURE/replay-extra-root-entry"
mkdir "$case_dir"
cp "$FORMAT_SOURCE" "$case_dir/lualatex.fmt"
printf 'undeclared root entry\n' >"$case_dir/extra"
chmod 0444 "$case_dir/lualatex.fmt" "$case_dir/extra"
chmod 0555 "$case_dir"
expect_reject \
  "format replay rejects an extra entry in the sealed private root" \
  "captured format root inventory is not exact" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE_BYTES" "$FORMAT_FIXTURE_SHA256"

case_dir="$FORMAT_FIXTURE/replay-leaf-symlink"
mkdir "$case_dir"
ln -s "$FORMAT_SOURCE" "$case_dir/lualatex.fmt"
chmod 0555 "$case_dir"
expect_reject \
  "format replay rejects a symlink at its exact private leaf" \
  "captured format descriptor open failed" \
  python3 -I -S "$FORMAT_REPLAY_VALIDATOR" \
  "$case_dir/lualatex.fmt" "$FORMAT_FIXTURE_BYTES" "$FORMAT_FIXTURE_SHA256"

case_file="$TEST_ROOT/format-capture-source-nofollow-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'source_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK' \
  'source_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK'
expect_reject \
  "format source custody rejects removal of source-leaf no-follow" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-capture-source-rewalk-removed.sh"
cp "$CHECKER" "$case_file"
mutate_occurrence "$case_file" 'root_chain_before != root_chain_after' 'False' 2
expect_reject \
  "format source custody rejects removal of the complete source-chain rewalk comparison" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-capture-destination-rewalk-removed.sh"
cp "$CHECKER" "$case_file"
mutate_occurrence "$case_file" 'destination_chain_before != destination_chain_after' 'False' 2
expect_reject \
  "format source custody rejects removal of the destination-chain rewalk comparison" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-replay-nofollow-removed.sh"
cp "$CHECKER" "$case_file"
mutate_occurrence \
  "$case_file" \
  'file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK' \
  'file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK' \
  2
expect_reject \
  "format source custody rejects removal of replay leaf no-follow" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-replay-digest-check-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'if digest.hexdigest() != expected_sha256:' \
  'if False:'
expect_reject \
  "format source custody rejects removal of the replay digest comparison" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-replay-link-count-check-removed.sh"
cp "$CHECKER" "$case_file"
mutate_occurrence \
  "$case_file" \
  'if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:' \
  'if not stat.S_ISREG(before.st_mode):' \
  1
expect_reject \
  "format source custody rejects removal of the replay single-link comparison" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-destination-exclusive-create-removed.sh"
cp "$CHECKER" "$case_file"
mutate_occurrence "$case_file" '        | os.O_EXCL' '        | os.O_TRUNC' 2
expect_reject \
  "format source custody rejects removal of exclusive destination creation" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-run-environment-removed.sh"
cp "$CHECKER" "$case_file"
# Exact production-source literal; this self-test shell must not expand FORMAT_ROOT.
# shellcheck disable=SC2016
mutate_occurrence "$case_file" 'TEXFORMATS=$FORMAT_ROOT' 'TEXFORMATS=' 2
expect_reject \
  "format source custody rejects removal of the compiler's private format search path" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-compiler-environment-consumer-removed.sh"
cp "$CHECKER" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
build_start = text.index("build_report() {")
build_end = text.index('\n}\n\nbuild_report "build-a"', build_start)
region = text[build_start:build_end]
compiler = region.index("        lualatex \\")
command_start = region.rfind("    if ! (\n", 0, compiler)
command_end = region.index("    ) >", compiler)
command = region[command_start:command_end]
needle = '        "${run_environment[@]}" \\\n'
if command_start < 0 or command.count(needle) != 1:
    raise SystemExit("expected one run-environment consumer in the LuaLaTeX command")
command = command.replace(needle, "", 1)
region = region[:command_start] + command + region[command_end:]
text = text[:build_start] + region + text[build_end:]
path.write_text(text, encoding="utf-8", newline="\n")
PY
expect_reject \
  "format source custody rejects bypass of the private environment by the actual compiler" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-per-pass-verifier-before-loop.sh"
cp "$CHECKER" "$case_file"
move_format_verifier_for_mutation "$case_file" before-loop
expect_reject \
  "format source custody rejects moving per-pass verification before the bounded pass loop" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-per-pass-verifier-after-compiler.sh"
cp "$CHECKER" "$case_file"
move_format_verifier_for_mutation "$case_file" after-compiler
expect_reject \
  "format source custody rejects moving per-pass verification after LuaLaTeX" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-final-verifier-before-builds.sh"
cp "$CHECKER" "$case_file"
move_format_verifier_for_mutation "$case_file" before-builds
expect_reject \
  "format source custody rejects moving final verification before both isolated builds" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"

case_file="$TEST_ROOT/format-final-receipt-removed.sh"
cp "$CHECKER" "$case_file"
# Exact production-source literal; this self-test shell must not expand receipt variables.
# shellcheck disable=SC2016
mutate_occurrence \
  "$case_file" \
  'format source $FORMAT_QUERY; format snapshot $FORMAT_BYTES bytes sha256 $FORMAT_SHA256' \
  'format source and snapshot omitted' \
  1
expect_reject \
  "format source custody rejects omission of the final source/size/digest receipt" \
  "format-custody source invariant drifted" \
  validate_format_custody_source "$case_file"
C3_ACTIVE_FAMILY=""

validate_map_file_free_wrapper_custody() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
required_once = (
    'ENTRY_WRAPPER_NAME="pid-rs-map-file-free-entry.tex"',
    'python3 -I -S - "$entry_wrapper" "$SNAPSHOT_ROOT/$SOURCE" <<\'PY\'',
    r'    "\\pdfextension mapfile {}\n"',
    'pid_rs_existing_find_map = luatexbase.callback_descriptions("find_map_file")',
    "for _ in pid_rs_pairs(pid_rs_existing_find_map) do",
    "if pid_rs_prior_map_callback_count ~= 0 then",
    "local function pid_rs_deny_map_file(name)",
    "local function pid_rs_deny_category_two_font_map_event(category, filename)",
    "if category == 2 then",
    "PID-RS-MAP-FILE-DENIED:",
    "PID-RS-CATEGORY-TWO-FONT-MAP-EVENT-DENIED:",
    "pid-rs deny font-map lookup",
    "pid-rs deny category-2 font-map events",
    r'    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\n"',
    r'f"\\input{{{source_path}}}\n"',
    'flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC',
    'if not stat.S_ISREG(after.st_mode) or after.st_nlink != 1:',
    'leaf_fields = ("st_dev", "st_ino", "st_size", "st_nlink")',
    '-jobname="$REPORT_STEM" \\\n',
    '          "$entry_wrapper"\n',
    "grep -Fxc -- 'PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source'",
    "def is_forbidden_tex_map_path(path: Path) -> bool:",
    'folded_parts[index : index + 2] == ("fonts", "map")',
    "for path in raw_input_paths:\n            if is_forbidden_tex_map_path(path):",
    "for path in resolved_inputs:\n            if is_forbidden_tex_map_path(path):",
    "loaded a forbidden raw ",
    "loaded a forbidden resolved ",
    "expected_entry_wrapper = (run_dir / entry_wrapper_name).resolve()",
)
for literal in required_once:
    if text.count(literal) != 1:
        raise SystemExit(f"map-file-free wrapper custody literal drifted: {literal!r}")
if text.count("luatexbase.add_to_callback(") != 2:
    raise SystemExit("map-file-free wrapper callback registration inventory drifted")
ordered = (
    r'    "\\pdfextension mapfile {}\n"',
    'pid_rs_existing_find_map = luatexbase.callback_descriptions("find_map_file")',
    "local function pid_rs_deny_map_file(name)",
    "pid-rs deny font-map lookup",
    "pid-rs deny category-2 font-map events",
    r'    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\n"',
    r'f"\\input{{{source_path}}}\n"',
)
positions = [text.index(literal) for literal in ordered]
if positions != sorted(positions):
    raise SystemExit("map-file-free entry-wrapper operations are out of order")
writer = text.index('python3 -I -S - "$entry_wrapper" "$SNAPSHOT_ROOT/$SOURCE"')
compiler = text.index("        lualatex ", writer)
jobname = text.index('-jobname="$REPORT_STEM"', compiler)
entry = text.index('          "$entry_wrapper"', jobname)
if not writer < compiler < jobname < entry:
    raise SystemExit("map-file-free wrapper is not captured before its stable-jobname compilation")
if "RequirePackage{luatexbase}" in text:
    raise SystemExit("map-file-free wrapper added an unnecessary legacy callback-manager package")
PY
}

C3_ACTIVE_FAMILY="entry-wrapper"
expect_accept \
  "map-file-free wrapper custody binds capture, callback denials, order, sentinel, job name, and FLS evidence" \
  validate_map_file_free_wrapper_custody "$CHECKER"

ENTRY_FIXTURE="$TEST_ROOT/entry-wrapper-fixture"
mkdir "$ENTRY_FIXTURE"
python3 -I -S "$ENTRY_WRAPPER_WRITER" \
  "$ENTRY_FIXTURE/pid-rs-map-file-free-entry.tex" \
  /captured/source/workflow.tex
python3 -I -S - "$ENTRY_FIXTURE/pid-rs-map-file-free-entry.tex" <<'PY'
from pathlib import Path
import stat
import sys


path = Path(sys.argv[1])
expected = (
    "\\pdfextension mapfile {}\n"
    "\\directlua{\n"
    "  local pid_rs_error = error\n"
    "  local pid_rs_pairs = pairs\n"
    "  local pid_rs_tostring = tostring\n"
    '  local pid_rs_existing_find_map = luatexbase.callback_descriptions("find_map_file")\n'
    "  local pid_rs_prior_map_callback_count = 0\n"
    "  for _ in pid_rs_pairs(pid_rs_existing_find_map) do\n"
    "    pid_rs_prior_map_callback_count = pid_rs_prior_map_callback_count + 1\n"
    "  end\n"
    "  if pid_rs_prior_map_callback_count ~= 0 then\n"
    "    pid_rs_error(\n"
    '      "PID-RS-UNEXPECTED-PRIOR-MAP-CALLBACKS:"\n'
    "        .. pid_rs_tostring(pid_rs_prior_map_callback_count), 0)\n"
    "  end\n"
    "  local function pid_rs_deny_map_file(name)\n"
    '    pid_rs_error("PID-RS-MAP-FILE-DENIED:" .. pid_rs_tostring(name), 0)\n'
    "  end\n"
    "  local function pid_rs_deny_category_two_font_map_event(category, filename)\n"
    "    if category == 2 then\n"
    "      pid_rs_error(\n"
    '        "PID-RS-CATEGORY-TWO-FONT-MAP-EVENT-DENIED:"\n'
    "          .. pid_rs_tostring(filename), 0)\n"
    "    end\n"
    "  end\n"
    "  luatexbase.add_to_callback(\n"
    '    "find_map_file", pid_rs_deny_map_file,\n'
    '    "pid-rs deny font-map lookup")\n'
    "  luatexbase.add_to_callback(\n"
    '    "start_file", pid_rs_deny_category_two_font_map_event,\n'
    '    "pid-rs deny category-2 font-map events")\n'
    "}\n"
    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\n"
    "\\input{/captured/source/workflow.tex}\n"
).encode("utf-8")
observed = path.read_bytes()
mode = stat.S_IMODE(path.lstat().st_mode)
if observed != expected:
    raise SystemExit("entry-wrapper writer output differs from its exact expected bytes")
if mode != 0o444 or path.lstat().st_nlink != 1 or not path.is_file():
    raise SystemExit("entry-wrapper writer output is not one mode-0444 regular file")
PY
pass "entry-wrapper writer produces the exact ordered single-link mode-0444 bytes"

case_file="$TEST_ROOT/map-file-free-primitive-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  '    "\\pdfextension mapfile {}\n"' \
  '    "\\pdfextension mapline {}\n"'
expect_reject \
  "map-file-free wrapper custody rejects removal of the default-map disabling primitive" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-order-reversed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  '    "\\pdfextension mapfile {}\n"' \
  '    "PID-RS-ORDER-SWAP-PLACEHOLDER\n"'
replace_once \
  "$case_file" \
  '    f"\\input{{{source_path}}}\n"' \
  '    "\\pdfextension mapfile {}\n"'
replace_once \
  "$case_file" \
  '    "PID-RS-ORDER-SWAP-PLACEHOLDER\n"' \
  '    f"\\input{{{source_path}}}\n"'
expect_reject \
  "map-file-free wrapper custody rejects moving default-map suppression after source loading" \
  "map-file-free entry-wrapper operations are out of order" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-prior-inventory-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'if pid_rs_prior_map_callback_count ~= 0 then' \
  'if false then'
expect_reject \
  "map-file-free wrapper custody rejects removal of the preexisting map-callback inventory" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-registration-description-drift.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'pid-rs deny font-map lookup' \
  'hostile registration description drift'
expect_reject \
  "map-file-free wrapper custody rejects drift of the map-lookup registration description" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-find-denial-returns.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  '    '\''    pid_rs_error("PID-RS-MAP-FILE-DENIED:" .. pid_rs_tostring(name), 0)\n'\''' \
  '    '\''    return name\n'\'''
expect_reject \
  "map-file-free wrapper custody rejects a find_map_file handler changed from denial to return" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-category-two-guard-weakened.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'if category == 2 then' \
  'if category == 3 then'
expect_reject \
  "map-file-free wrapper custody rejects drift of the category-2 defense-in-depth guard" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-sentinel-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  '    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\n"' \
  '    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=unchecked}\n"'
expect_reject \
  "map-file-free wrapper custody rejects drift of the generated pre-source sentinel" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-sentinel-duplicated.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  '    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\n"' \
  $'    "\\\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\\n"\n    "\\\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\\n"'
expect_reject \
  "map-file-free wrapper custody rejects a duplicated success sentinel" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-jobname-removed.sh"
cp "$CHECKER" "$case_file"
# These are exact production-source literals, not values for this self-test shell to expand.
# shellcheck disable=SC2016
replace_once \
  "$case_file" \
  '-jobname="$REPORT_STEM"' \
  '-jobname=hostile-drift'
expect_reject \
  "map-file-free wrapper custody rejects removal of the stable report job name" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-run-entry-removed.sh"
cp "$CHECKER" "$case_file"
# These are exact production-source literals, not values for this self-test shell to expand.
# shellcheck disable=SC2016
replace_once \
  "$case_file" \
  '          "$entry_wrapper"' \
  '          "$SNAPSHOT_ROOT/$SOURCE"'
expect_reject \
  "map-file-free wrapper custody rejects bypass of the captured run entry" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-capture-nofollow-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC' \
  'flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC'
expect_reject \
  "entry-wrapper custody rejects removal of descriptor no-follow capture" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-fls-directory-check-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'folded_parts[index : index + 2] == ("fonts", "map")' \
  'folded_parts[index : index + 2] == ("font", "maps")'
expect_reject \
  "map-path custody rejects removal of the case-insensitive fonts/map component check" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-raw-fls-loop-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'for path in raw_input_paths:' \
  'for path in ():'
expect_reject \
  "map-path custody rejects removal of the raw-input FLS check" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-resolved-fls-loop-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  $'for path in resolved_inputs:\n            if is_forbidden_tex_map_path(path):' \
  $'for path in ():\n            if is_forbidden_tex_map_path(path):'
expect_reject \
  "map-path custody rejects removal of the resolved-input FLS check" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"

case_file="$TEST_ROOT/map-file-free-required-wrapper-removed.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  'expected_entry_wrapper = (run_dir / entry_wrapper_name).resolve()' \
  'expected_entry_wrapper = source_path'
expect_reject \
  "FLS custody rejects removal of the exact per-run entry-wrapper requirement" \
  "map-file-free wrapper custody literal drifted" \
  validate_map_file_free_wrapper_custody "$case_file"
C3_ACTIVE_FAMILY=""

MAP_SOURCE="$(kpsewhich --must-exist pdftex.map)"
if [[ "$MAP_SOURCE" != /* || ! -f "$MAP_SOURCE" || "$MAP_SOURCE" == *$'\n'* ]]; then
  fail "exact default pdfTeX map query did not return one absolute file"
fi

make_runtime_map_probe() {
  local fixture_root="$1"
  local mode="$2"
  mkdir "$fixture_root"
  cp "$MAP_SOURCE" "$fixture_root/evil.data"
  case "$mode" in
    tex-mapfile)
      printf '%s\n' \
        '\pdfextension mapfile {+evil.data}' \
        '\endinput' \
        >"$fixture_root/source.tex"
      ;;
    tex-mapfile-absolute)
      printf '\\pdfextension mapfile {+%s}\n\\endinput\n' \
        "$fixture_root/evil.data" \
        >"$fixture_root/source.tex"
      if ! grep -F -- "$fixture_root/evil.data" "$fixture_root/source.tex" >/dev/null; then
        fail "absolute mapfile probe did not retain its exact path"
      fi
      ;;
    texmf-shaped-renamed-mapfile)
      mkdir -p "$fixture_root/texmf/opaque"
      cp "$MAP_SOURCE" "$fixture_root/texmf/opaque/evil.data"
      printf '\\pdfextension mapfile {+%s}\n\\endinput\n' \
        "$fixture_root/texmf/opaque/evil.data" \
        >"$fixture_root/source.tex"
      if ! grep -F -- \
          "$fixture_root/texmf/opaque/evil.data" "$fixture_root/source.tex" >/dev/null; then
        fail "TEXMF-shaped renamed-map probe did not retain its exact path"
      fi
      ;;
    lua-mapfile)
      printf '%s\n' \
        '\directlua{pdf.mapfile("+evil.data")}' \
        '\endinput' \
        >"$fixture_root/source.tex"
      ;;
    lua-mapfile-absolute)
      printf '\\directlua{pdf.mapfile("+%s")}\n\\endinput\n' \
        "$fixture_root/evil.data" \
        >"$fixture_root/source.tex"
      if ! grep -F -- "$fixture_root/evil.data" "$fixture_root/source.tex" >/dev/null; then
        fail "absolute Lua mapfile probe did not retain its exact path"
      fi
      ;;
    category-two)
      printf '%s\n' \
        '\directlua{callback.find("start_file")(2, "inert-category-two-probe")}' \
        '\endinput' \
        >"$fixture_root/source.tex"
      ;;
    mapline-boundary)
      printf '%s\n' \
        '\pdfextension mapline {+pidrsprobe pidrsprobe}' \
        '\directlua{pdf.mapline("-pidrsprobe")}' \
        '\documentclass{article}' \
        '\begin{document}\end{document}' \
        >"$fixture_root/source.tex"
      ;;
    *)
      fail "unknown runtime map probe mode: $mode"
      ;;
  esac
  python3 -I -S "$ENTRY_WRAPPER_WRITER" \
    "$fixture_root/pid-rs-map-file-free-entry.tex" \
    "$fixture_root/source.tex"
  (
    cd "$fixture_root"
    lualatex \
      -no-shell-escape \
      -recorder \
      -interaction=nonstopmode \
      -halt-on-error \
      -jobname=runtime-map-probe \
      -output-directory="$fixture_root" \
      "$fixture_root/pid-rs-map-file-free-entry.tex"
  )
}

C3_ACTIVE_FAMILY="runtime-map"
case_dir="$TEST_ROOT/runtime-tex-mapfile-denial"
expect_reject \
  "entry-wrapper denies toolchain-selected pdftex.map bytes renamed for the TeX primitive" \
  "PID-RS-MAP-FILE-DENIED:evil.data" \
  make_runtime_map_probe "$case_dir" tex-mapfile

case_dir="$TEST_ROOT/runtime-absolute-mapfile-denial"
expect_reject \
  "entry-wrapper denies toolchain-selected pdftex.map bytes requested by absolute path" \
  "PID-RS-MAP-FILE-DENIED:" \
  make_runtime_map_probe "$case_dir" tex-mapfile-absolute

case_dir="$TEST_ROOT/runtime-texmf-shaped-renamed-mapfile-denial"
expect_reject \
  "entry-wrapper denies toolchain-selected pdftex.map bytes beneath a TEXMF-shaped path" \
  "PID-RS-MAP-FILE-DENIED:" \
  make_runtime_map_probe "$case_dir" texmf-shaped-renamed-mapfile

case_dir="$TEST_ROOT/runtime-lua-mapfile-denial"
expect_reject \
  "entry-wrapper denies toolchain-selected pdftex.map bytes renamed for pdf.mapfile" \
  "PID-RS-MAP-FILE-DENIED:evil.data" \
  make_runtime_map_probe "$case_dir" lua-mapfile

case_dir="$TEST_ROOT/runtime-lua-absolute-mapfile-denial"
expect_reject \
  "entry-wrapper denies an absolute toolchain-selected pdftex.map request from pdf.mapfile" \
  "PID-RS-MAP-FILE-DENIED:" \
  make_runtime_map_probe "$case_dir" lua-mapfile-absolute

case_dir="$TEST_ROOT/runtime-category-two-denial"
expect_reject \
  "entry-wrapper category-2 defense rejects a simulated font-map event" \
  "PID-RS-CATEGORY-TWO-FONT-MAP-EVENT-DENIED:inert-category-two-probe" \
  make_runtime_map_probe "$case_dir" category-two

case_dir="$TEST_ROOT/runtime-mapline-boundary"
expect_accept \
  "entry-wrapper explicitly does not claim to deny file-free TeX/Lua mapline state mutation" \
  make_runtime_map_probe "$case_dir" mapline-boundary
C3_ACTIVE_FAMILY=""

make_fls_closure_fixture() {
  local fixture_root="$1"
  local extra_input="${2:-}"
  local run_dir
  mkdir -p \
    "$fixture_root/repository" \
    "$fixture_root/snapshot" \
    "$fixture_root/texmf/tex" \
    "$fixture_root/fonts" \
    "$fixture_root/format" \
    "$fixture_root/figures" \
    "$fixture_root/run-a/passes" \
    "$fixture_root/run-b/passes"
  printf 'source\n' >"$fixture_root/snapshot/source.tex"
  printf 'shared style\n' >"$fixture_root/snapshot/shared.sty"
  printf 'publication style\n' >"$fixture_root/snapshot/publication.sty"
  printf 'system input\n' >"$fixture_root/texmf/tex/system.sty"
  printf 'captured format\n' >"$fixture_root/format/lualatex.fmt"
  printf 'figure\n' >"$fixture_root/figures/figure.pdf"
  for run_dir in "$fixture_root/run-a" "$fixture_root/run-b"; do
    printf '2\n' >"$run_dir/pass-count.txt"
    printf 'captured wrapper\n' >"$run_dir/pid-rs-map-file-free-entry.tex"
    printf 'generated input\n' >"$run_dir/generated.aux"
    printf 'pdf output\n' >"$run_dir/mathematical-problem-solving-workflow.pdf"
    {
      printf 'PWD %s\n' "$run_dir"
      printf 'INPUT %s\n' "$fixture_root/snapshot/source.tex"
      printf 'INPUT %s\n' "$fixture_root/snapshot/shared.sty"
      printf 'INPUT %s\n' "$fixture_root/snapshot/publication.sty"
      printf 'INPUT %s\n' "$fixture_root/texmf/tex/system.sty"
      printf 'INPUT %s\n' "$fixture_root/format/lualatex.fmt"
      printf 'INPUT %s\n' "$fixture_root/figures/figure.pdf"
      printf 'INPUT %s\n' "$run_dir/pid-rs-map-file-free-entry.tex"
      printf 'INPUT %s\n' "$run_dir/generated.aux"
      if [[ -n "$extra_input" ]]; then
        printf 'INPUT %s\n' "$extra_input"
      fi
      printf 'OUTPUT %s\n' "$run_dir/mathematical-problem-solving-workflow.pdf"
    } >"$run_dir/passes/pass-1.fls"
    cp "$run_dir/passes/pass-1.fls" "$run_dir/passes/pass-2.fls"
  done
}

run_fls_closure_validator() {
  local fixture_root="$1"
  python3 -I -S "$FLS_CLOSURE_VALIDATOR" \
    "$fixture_root/run-a" \
    "$fixture_root/run-b" \
    "$fixture_root/repository" \
    "$fixture_root/snapshot" \
    "$fixture_root/texmf" \
    "$fixture_root/fonts" \
    "$fixture_root/format/lualatex.fmt" \
    16 \
    31a5f5c91a938706c263de5a49b0623d91f936f873f2444f687316b55d9bc61b \
    "$fixture_root/snapshot/source.tex" \
    "$fixture_root/snapshot/shared.sty" \
    "$fixture_root/snapshot/publication.sty" \
    "$fixture_root/figures" \
    "$fixture_root/closure" \
    pid-rs-map-file-free-entry.tex \
    figure
}

C3_ACTIVE_FAMILY="fls-map-path"
case_dir="$(mktemp -d "$TEST_ROOT/fls-map-file-free.XXXXXX")"
make_fls_closure_fixture "$case_dir"
expect_accept \
  "FLS closure accepts a bounded fixture with its exact entry and no font-map file path evidence" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-renamed-map-boundary.XXXXXX")"
mkdir -p "$case_dir/texmf/opaque"
cp "$MAP_SOURCE" "$case_dir/texmf/opaque/evil.data"
make_fls_closure_fixture "$case_dir" "$case_dir/texmf/opaque/evil.data"
expect_accept \
  "FLS paths cannot classify toolchain-selected pdftex.map bytes renamed outside fonts/map" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-raw-map-alias.XXXXXX")"
mkdir -p "$case_dir/hostile"
printf 'resolved non-map target\n' >"$case_dir/hostile/target.bin"
ln -s target.bin "$case_dir/hostile/alias.map"
make_fls_closure_fixture "$case_dir" "$case_dir/hostile/alias.map"
expect_reject \
  "FLS closure rejects a raw .map alias even when its target has no map suffix" \
  "loaded a forbidden raw TeX map-path input" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-mixed-case-map.XXXXXX")"
mkdir -p "$case_dir/hostile"
printf 'mixed case map\n' >"$case_dir/hostile/hostile.MAP"
make_fls_closure_fixture "$case_dir" "$case_dir/hostile/hostile.MAP"
expect_reject \
  "FLS closure rejects a mixed-case raw .MAP suffix" \
  "loaded a forbidden raw TeX map-path input" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-hidden-map.XXXXXX")"
mkdir -p "$case_dir/hostile"
printf 'hidden mixed case map\n' >"$case_dir/hostile/.MaP"
make_fls_closure_fixture "$case_dir" "$case_dir/hostile/.MaP"
expect_reject \
  "FLS closure rejects a raw hidden .MaP leaf" \
  "loaded a forbidden raw TeX map-path input" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-font-map-subtree.XXXXXX")"
mkdir -p "$case_dir/hostile/FoNtS/MaP"
printf 'map-tree payload without suffix\n' >"$case_dir/hostile/FoNtS/MaP/payload.dat"
make_fls_closure_fixture "$case_dir" "$case_dir/hostile/FoNtS/MaP/payload.dat"
expect_reject \
  "FLS closure rejects a non-.map file beneath mixed-case fonts/map components" \
  "loaded a forbidden raw TeX map-path input" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-resolved-map-target.XXXXXX")"
mkdir -p "$case_dir/hostile/direct" "$case_dir/hostile/fonts/map"
printf 'resolved map-tree target\n' >"$case_dir/hostile/fonts/map/target.dat"
ln -s ../fonts/map/target.dat "$case_dir/hostile/direct/alias.bin"
make_fls_closure_fixture "$case_dir" "$case_dir/hostile/direct/alias.bin"
expect_reject \
  "FLS closure rejects a raw non-map alias resolving beneath fonts/map" \
  "loaded a forbidden resolved TeX map-path input" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-resolved-map-suffix.XXXXXX")"
mkdir -p "$case_dir/hostile/direct" "$case_dir/hostile/targets"
printf 'resolved map suffix target\n' >"$case_dir/hostile/targets/target.MaP"
ln -s ../targets/target.MaP "$case_dir/hostile/direct/alias.bin"
make_fls_closure_fixture "$case_dir" "$case_dir/hostile/direct/alias.bin"
expect_reject \
  "FLS closure rejects a raw neutral alias resolving to a mixed-case .MaP leaf" \
  "loaded a forbidden resolved TeX map-path input" \
  run_fls_closure_validator "$case_dir"
C3_ACTIVE_FAMILY=""

C3_ACTIVE_FAMILY="format-custody"
case_dir="$(mktemp -d "$TEST_ROOT/fls-private-format.XXXXXX")"
make_fls_closure_fixture "$case_dir"
expect_accept \
  "FLS closure admits the one exact raw and resolved private-format path" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-missing-private-format.XXXXXX")"
make_fls_closure_fixture "$case_dir"
python3 -I -S - "$case_dir" <<'PY'
from pathlib import Path
import sys


root = Path(sys.argv[1])
format_row = f"INPUT {root / 'format' / 'lualatex.fmt'}"
for path in sorted(root.glob("run-*/passes/pass-*.fls")):
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines.count(format_row) != 1:
        raise SystemExit(f"format fixture row inventory drifted: {path}")
    path.write_text(
        "\n".join(line for line in lines if line != format_row) + "\n",
        encoding="utf-8",
        newline="\n",
    )
PY
expect_reject \
  "FLS closure rejects a pass that omits the captured private format" \
  "recorded a format outside its exact raw path" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-extra-ambient-format.XXXXXX")"
mkdir -p "$case_dir/texmf/web2c"
printf 'ambient format beneath otherwise allowed TeX root\n' \
  >"$case_dir/texmf/web2c/ambient.fmt"
make_fls_closure_fixture "$case_dir" "$case_dir/texmf/web2c/ambient.fmt"
expect_reject \
  "FLS closure rejects an extra format beneath the otherwise allowed TeX installation root" \
  "recorded a format outside its exact raw path" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-mixed-case-raw-format-alias.XXXXXX")"
mkdir -p "$case_dir/texmf/aliases"
printf 'neutral target behind mixed-case raw format alias\n' \
  >"$case_dir/texmf/aliases/target.bin"
ln -s target.bin "$case_dir/texmf/aliases/ambient.FMT"
make_fls_closure_fixture "$case_dir" "$case_dir/texmf/aliases/ambient.FMT"
expect_reject \
  "FLS closure rejects a mixed-case raw .FMT alias resolving to a neutral target" \
  "recorded a format outside its exact raw path" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-mixed-case-resolved-format.XXXXXX")"
mkdir -p "$case_dir/texmf/aliases" "$case_dir/texmf/web2c"
printf 'mixed-case resolved ambient format\n' \
  >"$case_dir/texmf/web2c/ambient.FMT"
ln -s ../web2c/ambient.FMT "$case_dir/texmf/aliases/ambient.bin"
make_fls_closure_fixture "$case_dir" "$case_dir/texmf/aliases/ambient.bin"
expect_reject \
  "FLS closure rejects a neutral raw alias resolving to a mixed-case .FMT target" \
  "loaded a format outside its exact resolved path" \
  run_fls_closure_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/fls-private-format-alias.XXXXXX")"
mkdir -p "$case_dir/texmf/aliases"
make_fls_closure_fixture "$case_dir" "$case_dir/texmf/aliases/private.fmt"
ln -s ../../format/lualatex.fmt "$case_dir/texmf/aliases/private.fmt"
expect_reject \
  "FLS closure rejects a raw alias even when it resolves to the exact private format" \
  "recorded a format outside its exact raw path" \
  run_fls_closure_validator "$case_dir"
C3_ACTIVE_FAMILY=""

validate_pypdf_path_order() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
capture_loop = "for root in package_roots:\n    sys.path.insert(0, str(root))"
import_loop = (
    'for package_root in dict.fromkeys((sysconfig.get_path("purelib"), '
    'sysconfig.get_path("platlib"))):\n'
    "    if package_root:\n"
    "        sys.path.insert(0, package_root)"
)
if text.count(capture_loop) != 1:
    raise SystemExit("pypdf capture path-order loop drifted")
if text.count(import_loop) != 3:
    raise SystemExit("pypdf consumer path-order loop inventory drifted")
if "reversed(package_roots)" in text:
    raise SystemExit("pypdf capture precedence differs from consumer imports")
PY
}

expect_accept \
  "pypdf manifest capture and all consumers share one package-root precedence" \
  validate_pypdf_path_order "$CHECKER"

case_file="$TEST_ROOT/pypdf-reversed-capture.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  $'for root in package_roots:\n    sys.path.insert(0, str(root))' \
  $'for root in reversed(package_roots):\n    sys.path.insert(0, str(root))'
expect_reject \
  "pypdf path-order guard rejects a capture/import precedence mismatch" \
  "pypdf capture path-order loop drifted" \
  validate_pypdf_path_order "$case_file"

validate_command_resolution_custody() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
markers = (
    "# COMMAND_RESOLUTION_INITIAL: bind commands before the lock/re-exec transition.",
    "# COMMAND_RESOLUTION_PRE_MANIFEST: bind search results immediately before phase custody capture.",
    "# COMMAND_RESOLUTION_POST_VALIDATION: reject persistent PATH/symlink drift before final custody and optional refresh.",
)
for marker in markers:
    indices = [index for index, line in enumerate(lines) if line == marker]
    if len(indices) != 1 or indices[0] + 1 >= len(lines):
        raise SystemExit(f"command-resolution custody marker drifted: {marker}")
    if lines[indices[0] + 1] != "verify_command_resolution":
        raise SystemExit(f"command-resolution custody call is absent after marker: {marker}")
if lines.count("verify_command_resolution() {") != 1:
    raise SystemExit("command-resolution verifier definition drifted")
if lines.count("verify_command_resolution") != 3:
    raise SystemExit("command-resolution custody call inventory drifted")
start = lines.index("commands=(")
end = lines.index(")", start + 1)
commands = [line.strip() for line in lines[start + 1 : end]]
for required in ("basename", "env", "luaotfload-tool", "ps", "sleep", "texlua"):
    if commands.count(required) != 1:
        raise SystemExit(f"transitive executable command is absent or duplicated: {required}")
PY
}

expect_accept \
  "command resolution is rebound initially, before manifests, and after build/validation consumers" \
  validate_command_resolution_custody "$CHECKER"

case_file="$TEST_ROOT/executable-missing-post-resolution.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  $'# COMMAND_RESOLUTION_POST_VALIDATION: reject persistent PATH/symlink drift before final custody and optional refresh.\nverify_command_resolution' \
  $'# COMMAND_RESOLUTION_POST_VALIDATION: reject persistent PATH/symlink drift before final custody and optional refresh.\n# hostile mutation removed the post-validation command-resolution check'
expect_reject \
  "command-resolution custody guard rejects removal of the post-validation check" \
  "command-resolution custody call is absent after marker" \
  validate_command_resolution_custody "$case_file"

C3_ACTIVE_FAMILY="executable-custody"
for transitive_command in basename ps sleep; do
  case_file="$TEST_ROOT/executable-missing-$transitive_command.sh"
  cp "$CHECKER" "$case_file"
  replace_once \
    "$case_file" \
    "  $transitive_command" \
    "  # hostile mutation removed transitive command $transitive_command"
  expect_reject \
    "command-resolution custody rejects missing transitive $transitive_command" \
    "transitive executable command is absent or duplicated: $transitive_command" \
    validate_command_resolution_custody "$case_file"
done
C3_ACTIVE_FAMILY=""

validate_lock_bootstrap_custody() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
required = (
    "LOCK_BOOTSTRAP_PARENT=0",
    'if [[ -z "${PID_RS_WORKFLOW_PDF_LOCK_FD+x}" \\\n    && -z "${PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256+x}" ]]; then',
    'elif [[ -z "${PID_RS_WORKFLOW_PDF_LOCK_FD+x}" \\\n    || -z "${PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256+x}" ]]; then',
    "has_descriptor = \"PID_RS_WORKFLOW_PDF_LOCK_FD\" in os.environ",
    "has_root_digest = \"PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256\" in os.environ",
    'if not raw_descriptor.isdigit():\n        fail("inherited descriptor is not a decimal integer")',
    'if held_digest != root_digest:\n        fail("inherited repository-root digest differs")',
    'if [[ "$LOCK_BOOTSTRAP_STATUS" -ne 0 ]]; then\n  exit "$LOCK_BOOTSTRAP_STATUS"\nfi',
    'if [[ "$LOCK_BOOTSTRAP_PARENT" -eq 1 ]]; then\n  exit 0\nfi',
)
positions = []
for fragment in required:
    if text.count(fragment) != 1:
        raise SystemExit(f"lock-bootstrap custody fragment drifted: {fragment!r}")
    positions.append(text.index(fragment))
if positions != sorted(positions):
    raise SystemExit("lock-bootstrap custody fragments are out of order")
if 'raw_descriptor.isdigit() and held_digest == root_digest' in text:
    raise SystemExit("lock bootstrap still falls through from an invalid inherited environment")
PY
}

expect_accept \
  "publication-lock bootstrap propagates status and rejects partial or forged inherited state" \
  validate_lock_bootstrap_custody "$CHECKER"

case_file="$TEST_ROOT/lock-parent-continues.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  $'if [[ "$LOCK_BOOTSTRAP_PARENT" -eq 1 ]]; then\n  exit 0\nfi' \
  $'if [[ "$LOCK_BOOTSTRAP_PARENT" -eq 1 ]]; then\n  : # hostile mutation lets the original non-lock-bearing shell continue\nfi'
expect_reject \
  "publication-lock guard rejects launcher continuation after its lock-bearing child" \
  "lock-bootstrap custody fragment drifted" \
  validate_lock_bootstrap_custody "$case_file"

case_file="$TEST_ROOT/lock-root-digest-fallthrough.sh"
cp "$CHECKER" "$case_file"
replace_once \
  "$case_file" \
  $'if held_digest != root_digest:\n        fail("inherited repository-root digest differs")' \
  $'if held_digest != root_digest:\n        pass  # hostile mutation accepts a forged root binding'
expect_reject \
  "publication-lock guard rejects forged-root fallthrough" \
  "lock-bootstrap custody fragment drifted" \
  validate_lock_bootstrap_custody "$case_file"

expect_reject \
  "publication-lock runtime rejects a partial inherited environment" \
  "publication lock environment is only partially specified" \
  without_workflow_gate_custody \
  PID_RS_WORKFLOW_PDF_LOCK_FD=7 \
  bash --noprofile --norc "$CHECKER" --exact

expect_reject \
  "publication-lock runtime rejects a nonnumeric inherited descriptor" \
  "publication lock inherited descriptor is not a decimal integer" \
  without_workflow_gate_custody \
  PID_RS_WORKFLOW_PDF_LOCK_FD=not-a-number \
  PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256=forged \
  bash --noprofile --norc "$CHECKER" --exact

# Publication-source semantics.  Canonical-protocol mutations change the root Markdown and only
# the exact embedded Markdown enclosure together; typeset-only transition mutations change TeX
# alone.  This preserves byte-equality preconditions so each rejection reaches its claimed branch.
SEMANTIC_STEMS=(
  four-object-assurance-chain
  obligation-dag-minimal-cuts
  shared-oracle-correlated-routes
  invalidation-publication-state-machine
)

make_semantic_fixture() {
  local destination="$1"
  mkdir -p "$destination"
  cp \
    "$BASE_REPOSITORY/audit/formal/latex/mathematical-problem-solving-workflow.tex" \
    "$destination/workflow.tex"
  cp "$BASE_MARKDOWN" "$destination/workflow.md"
  cp \
    "$BASE_REPOSITORY/audit/formal/latex/pid-rs-workflow-publication.sty" \
    "$destination/publication.sty"
}

run_source_semantic_validator() {
  local directory="$1"
  python3 -I -S "$SOURCE_SEMANTIC_VALIDATOR" \
    "$directory/workflow.tex" \
    "$directory/workflow.md" \
    "$directory/publication.sty" \
    "${SEMANTIC_STEMS[@]}"
}

mutate_canonical_pair() {
  local source="$1"
  local markdown="$2"
  local old="$3"
  local new="$4"
  python3 -I -S - "$source" "$markdown" "$old" "$new" <<'PY'
from pathlib import Path
import sys


source_path = Path(sys.argv[1])
markdown_path = Path(sys.argv[2])
old = sys.argv[3]
new = sys.argv[4]
source = source_path.read_text(encoding="utf-8")
markdown = markdown_path.read_text(encoding="utf-8")
begin_marker = "\\begin{markdown}\n"
end_marker = "\\end{markdown}"
if source.count(begin_marker) != 1 or source.count(end_marker) != 1:
    raise SystemExit("canonical Markdown enclosure mutation precondition drifted")
begin = source.index(begin_marker) + len(begin_marker)
end = source.index(end_marker, begin)
if source[begin:end] != markdown:
    raise SystemExit("canonical Markdown pair differs before hostile mutation")
if markdown.count(old) != 1:
    raise SystemExit(
        f"expected one canonical semantic mutation target, observed {markdown.count(old)}: {old!r}"
    )
mutated = markdown.replace(old, new, 1)
source = source[:begin] + mutated + source[end:]
markdown_path.write_text(mutated, encoding="utf-8", newline="\n")
source_path.write_text(source, encoding="utf-8", newline="\n")
PY
}

case_dir="$(mktemp -d "$TEST_ROOT/source-semantic-control.XXXXXX")"
make_semantic_fixture "$case_dir"
expect_accept \
  "publication source semantic validator accepts the exact canonical pair" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-post-markdown-suffix.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  $'\n\n\\end{document}\n' \
  $'\n\n% unreviewed post-Markdown command\n\\typeout{UNREVIEWED}\n\\end{document}\n'
expect_reject \
  "TeX source rejects executable or inert bytes after the reviewed Markdown enclosure" \
  "TeX source has bytes outside the exact reviewed post-Markdown suffix" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-fenced-scientific-assertion.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "Orient every dependency-bearing edge from prerequisite to dependent" \
  $'Edge orientation may instead be chosen arbitrarily.\n\n```text\nOrient every dependency-bearing edge from prerequisite to dependent\n```'
expect_reject \
  "canonical semantics reject a required scientific assertion retained only in fenced code" \
  "canonical semantic correction is absent: Orient every dependency-bearing edge from prerequisite to dependent" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-auto-equation-numbering.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  '\begin{align*}' \
  '\begin{align}'
expect_reject \
  "TeX source rejects auto-numbered display collisions" \
  "typeset-only primer contains auto-numbered display environments" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-auto-alignat-numbering.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once "$case_dir/workflow.tex" '\begin{align*}' '\begin{alignat}{2}'
replace_once "$case_dir/workflow.tex" '\end{align*}' '\end{alignat}'
expect_reject \
  "TeX source rejects alternate auto-numbered amsmath environments" \
  "typeset-only primer contains auto-numbered display environments" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-bare-primer-heading.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  '\PidWorkflowSubsection{Status of this primer}' \
  '\subsection{Status of this primer}'
expect_reject \
  "TeX source rejects headings that can anchor before their page break" \
  "typeset-only primer contains bare heading commands" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-equation-tag-sequence.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  '\tag{12}' \
  '\tag{11}'
expect_reject \
  "TeX source rejects duplicate or nonmonotone manual equation tags" \
  "typeset-only primer equation-tag sequence drifted" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-starred-equation-tag.XXXXXX")"
make_semantic_fixture "$case_dir"
# The following single-quoted TeX literals intentionally end in two backslashes.
# shellcheck disable=SC1003
replace_once \
  "$case_dir/workflow.tex" \
  'R   &=c_R,\\' \
  'R   &=c_R,\tag*{(1)}\\'
expect_reject \
  "TeX source rejects an extra visible starred equation tag" \
  "typeset-only primer equation-tag sequence drifted" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-csname-heading-bypass.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  '\PidWorkflowSubsection{Status of this primer}' \
  $'% \\PidWorkflowSubsection{\n\\csname subsection\\endcsname{Status of this primer}'
expect_reject \
  "exact primer custody rejects a TeX csname heading bypass" \
  "typeset-only primer exact-byte custody drifted" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-wrapper-needspace-removal.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/publication.sty" \
  '\par\Needspace{14\baselineskip}%' \
  '\par%'
expect_reject \
  "exact style custody rejects removal of heading space reservation" \
  "workflow publication style exact-byte custody drifted" \
  run_source_semantic_validator "$case_dir"

direct_literal='The assurance path therefore contains three distinct transitions, each with its own obligation:'
case_dir="$(mktemp -d "$TEST_ROOT/source-transition-path.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  "$direct_literal" \
  'The assurance path contains three transitions with one shared obligation:'
expect_reject \
  "TeX source rejects removal of the three-transition obligation boundary" \
  "required TeX assurance-boundary wording must occur once: $direct_literal" \
  run_source_semantic_validator "$case_dir"

direct_literal='The assurance chain has four distinct objects and three separately justified assurance transitions.'
case_dir="$(mktemp -d "$TEST_ROOT/source-transition-caption.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  "$direct_literal" \
  'The assurance chain has four objects connected by one general assurance argument.'
expect_reject \
  "TeX source rejects removal of the figure transition boundary" \
  "required TeX assurance-boundary wording must occur once: $direct_literal" \
  run_source_semantic_validator "$case_dir"

direct_literal='An AND/OR directed acyclic graph has frozen admissible universe U = {A1, A2, B1, C}, route A = {A1, A2, C}, and route B = {B1, C}.'
case_dir="$(mktemp -d "$TEST_ROOT/source-figure2-prose-routes.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  "$direct_literal" \
  'An AND/OR directed acyclic graph has several premises and two routes.'
expect_reject \
  "TeX source rejects removal of the Figure 2 frozen-universe and route binding" \
  "required TeX assurance-boundary wording must occur once: $direct_literal" \
  run_source_semantic_validator "$case_dir"

direct_literal='The complete inclusion-minimal cut family is {C}, {A1, B1}, and {A2, B1}; the common goal and synthetic route aggregators are excluded from the admissible cut universe.'
case_dir="$(mktemp -d "$TEST_ROOT/source-figure2-prose-cuts.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  "$direct_literal" \
  'The diagram shows several cuts after excluding some synthetic nodes.'
expect_reject \
  "TeX source rejects removal of the Figure 2 complete-cut prose binding" \
  "required TeX assurance-boundary wording must occur once: $direct_literal" \
  run_source_semantic_validator "$case_dir"

direct_literal='AND prerequisites, OR routes, and the complete three-cut family in the frozen example.'
case_dir="$(mktemp -d "$TEST_ROOT/source-figure2-caption.XXXXXX")"
make_semantic_fixture "$case_dir"
replace_once \
  "$case_dir/workflow.tex" \
  "$direct_literal" \
  'AND prerequisites, OR routes, and example cuts.'
expect_reject \
  "TeX source rejects drift of the Figure 2 complete-family caption" \
  "required TeX assurance-boundary wording must occur once: $direct_literal" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-inline-code.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "source workflow" \
  "\`source workflow\`"
expect_reject \
  "canonical Markdown rejects whitespace-bearing inline code" \
  "whitespace-bearing inline code is incompatible with the publication renderer at canonical Markdown line" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-pin-arxiv.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "arXiv:2002.03356v5" \
  "arXiv:2002.03356v4"
expect_reject \
  "canonical semantics reject drift of the MGW primary-source revision pin" \
  "canonical semantic literal is absent: arXiv:2002.03356v5" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-pin-erratum.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "PhysRevE.83.019903" \
  "PhysRevE.83.019904"
expect_reject \
  "canonical semantics reject drift of the KSG erratum source pin" \
  "canonical semantic literal is absent: PhysRevE.83.019903" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-cut.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "frozen admissible vertex universe" \
  "mutable admissible vertex universe"
expect_reject \
  "canonical semantics reject removal of the frozen cut universe" \
  "canonical semantic literal is absent: frozen admissible vertex universe" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-binary64.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "underflow/subnormals" \
  "underflow and subnormals"
expect_reject \
  "canonical semantics reject weakening the binary64 exceptional-case literal" \
  "canonical semantic literal is absent: underflow/subnormals" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-claim-field.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "Completion predicate and adjudicator" \
  "Completion rule and adjudicator"
expect_reject \
  "canonical semantics reject removal of the completion-predicate claim field" \
  "canonical semantic literal is absent: Completion predicate and adjudicator" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-claim-disposition.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "Completeness is a disposition, not an evidence class" \
  "Completion is a disposition, not an evidence class"
expect_reject \
  "canonical semantics reject conflation of completeness with an evidence class" \
  "canonical semantic literal is absent: Completeness is a disposition, not an evidence class" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-openai-attribution.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "both were supplied from the same OpenAI CDN source family" \
  "both were produced by one institution"
expect_reject \
  "canonical semantics reject overbroad proof-process source attribution" \
  "canonical semantic literal is absent: both were supplied from the same OpenAI CDN source family" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-operation-order.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "order of conditioning, fitting, mixing or averaging, nonlinear transforms, and Möbius inversion" \
  "order of the main calculations"
expect_reject \
  "canonical semantics reject removal of the noncommuting-operation audit" \
  "canonical semantic literal is absent: order of conditioning, fitting, mixing or averaging, nonlinear transforms, and Möbius inversion" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-joint-witness.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "one compatible joint version or witness when simultaneity is required" \
  "one witness when useful"
expect_reject \
  "canonical semantics reject weakening the compatible-joint-witness requirement" \
  "canonical semantic literal is absent: one compatible joint version or witness when simultaneity is required" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-total-error-budget.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "one total error budget smaller than every strict claimed margin" \
  "separate error estimates for a strict claim"
expect_reject \
  "canonical semantics reject removal of the total-error-versus-margin requirement" \
  "canonical semantic literal is absent: one total error budget smaller than every strict claimed margin" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-construction-native-import.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "the construction-native local or target-outcome-specific information object, any cumulative-event" \
  "the common local information object, its cumulative-event"
expect_reject \
  "canonical semantics reject a generic PID import object" \
  "canonical semantic literal is absent: the construction-native local or target-outcome-specific information object, any cumulative-event semantics and Möbius convention it actually uses" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-construction-native-packet.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "the construction-native local or target-outcome-specific information object and decomposition" \
  "the common pointwise information object and decomposition"
expect_reject \
  "canonical semantics reject a generic PID claim-packet object" \
  "canonical semantic literal is absent: the construction-native local or target-outcome-specific information object and decomposition convention; for MGW" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-identification-overlap.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "admissible state/event identifications and incidental overlaps" \
  "ordinary state examples"
expect_reject \
  "canonical semantics reject removal of identification/overlap counterexamples" \
  "canonical semantic literal is absent: admissible state/event identifications and incidental overlaps" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-adjacent-negative.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "neighboring non-target method or estimand that it must reject" \
  "additional method that it may compare"
expect_reject \
  "canonical semantics reject removal of adjacent-method negative controls" \
  "canonical semantic literal is absent: neighboring non-target method or estimand that it must reject" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-comment-concealment.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "A route that merely failed is not a counterexample" \
  $'A route that merely failed conclusively disproves the claim\n\n<!-- A route that merely failed is not a counterexample -->'
expect_reject \
  "canonical Markdown rejects a required assertion retained only in an HTML comment" \
  "canonical Markdown contains an HTML comment opener" \
  run_source_semantic_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/source-exact-markdown-bytes.XXXXXX")"
make_semantic_fixture "$case_dir"
mutate_canonical_pair \
  "$case_dir/workflow.tex" \
  "$case_dir/workflow.md" \
  "# Mathematical problem-solving workflow for pid-rs" \
  $'# Mathematical problem-solving workflow for pid-rs '
expect_reject \
  "canonical Markdown exact-source custody rejects otherwise unrecognized byte drift" \
  "canonical Markdown exact-byte custody drifted" \
  run_source_semantic_validator "$case_dir"

# Exercise the exact shell array and loop that guard report-extracted text without compiling the
# report.  The accepted control is generated from the extracted production array; each hostile
# case removes only one newly bound Figure 2 sentinel.
make_rendered_text_control() {
  local directory="$1"
  mkdir -p "$directory"
  python3 -I -S - "$RENDERED_TEXT_VALIDATOR" "$directory/built.txt" <<'PY'
from pathlib import Path
import shlex
import sys


validator = Path(sys.argv[1])
destination = Path(sys.argv[2])
lines = validator.read_text(encoding="utf-8").splitlines()
starts = [index for index, line in enumerate(lines) if line == "required_text=("]
if len(starts) != 1:
    raise SystemExit(f"rendered-text array start count drifted: {starts!r}")
start = starts[0]
end = next(
    (index for index in range(start + 1, len(lines)) if lines[index] == ")"),
    None,
)
if end is None:
    raise SystemExit("rendered-text array terminator is absent")
sentinels: list[str] = []
for line in lines[start + 1 : end]:
    fields = shlex.split(line, posix=True)
    if len(fields) != 1:
        raise SystemExit(f"rendered-text array row is noncanonical: {line!r}")
    sentinels.append(fields[0])
if not sentinels or len(sentinels) != len(set(sentinels)):
    raise SystemExit("rendered-text array is empty or contains duplicates")
destination.write_text("\n".join(sentinels) + "\n", encoding="utf-8", newline="\n")
PY
}

run_rendered_text_validator() {
  local directory="$1"
  env -i \
    "PATH=$PATH" \
    "LC_ALL=C" \
    "LANG=C" \
    "TZ=UTC" \
    "BUILD_ROOT=$directory" \
    "CHECK_NAME=mathematical workflow PDF check" \
    "$SELF_TEST_BASH" --noprofile --norc "$RENDERED_TEXT_VALIDATOR"
}

case_dir="$(mktemp -d "$TEST_ROOT/rendered-text-control.XXXXXX")"
make_rendered_text_control "$case_dir"
expect_accept \
  "rendered-text binding accepts the exact production sentinel inventory" \
  run_rendered_text_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/rendered-text-heading.XXXXXX")"
make_rendered_text_control "$case_dir"
replace_once \
  "$case_dir/built.txt" \
  "Accepted routes, AND prerequisites, and all minimal cuts" \
  "Accepted routes, AND prerequisites, and minimal cuts"
expect_reject \
  "rendered-text binding rejects drift of the Figure 2 heading" \
  "rendered-text sentinel is absent: Accepted routes, AND prerequisites, and all minimal cuts" \
  run_rendered_text_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/rendered-text-cuts.XXXXXX")"
make_rendered_text_control "$case_dir"
replace_once \
  "$case_dir/built.txt" \
  "All inclusion-minimal cuts: {C}; {A1, B1}; {A2, B1}" \
  "All inclusion-minimal cuts: {C}; {A1, B1}"
expect_reject \
  "rendered-text binding rejects omission of the third Figure 2 cut" \
  "rendered-text sentinel is absent: All inclusion-minimal cuts: {C}; {A1, B1}; {A2, B1}" \
  run_rendered_text_validator "$case_dir"

expect_accept \
  "standalone Figure 2 PDF sentinel remains a stable heading prefix" \
  python3 -I -S - "$CHECKER" <<'PY'
from pathlib import Path
import sys


checker = Path(sys.argv[1]).read_text(encoding="utf-8")
start = checker.index("figure_sentinel() {")
end = checker.index("validate_font_table() {", start)
region = checker[start:end]
mapping = (
    "obligation-dag-minimal-cuts) printf '%s\\n' "
    "'Accepted routes, AND prerequisites' ;;"
)
if region.count(mapping) != 1:
    raise SystemExit("standalone Figure 2 sentinel mapping drifted")
if "Accepted routes, AND prerequisites, and all minimal cuts" in region:
    raise SystemExit("standalone Figure 2 sentinel became coupled to the expanded heading")
PY

# Executable-byte manifest parser.  Trusted-root admission is tested through the shell entry below;
# these direct cases bind regular-file, inventory, and size checks to the exact embedded capturer.
case_dir="$(mktemp -d "$TEST_ROOT/executable-control.XXXXXX")"
printf 'bounded-executable-control\n' >"$case_dir/tool"
chmod 755 "$case_dir/tool"
expect_accept \
  "executable manifest accepts one bounded regular executable" \
  python3 -I -S "$EXECUTABLE_VALIDATOR" \
  "$case_dir/manifest.tsv" 1 tool "$case_dir/tool"

case_dir="$(mktemp -d "$TEST_ROOT/executable-symlink.XXXXXX")"
printf 'bounded-executable-symlink-control\n' >"$case_dir/real-tool"
chmod 755 "$case_dir/real-tool"
ln -s "$case_dir/real-tool" "$case_dir/tool"
expect_reject \
  "executable manifest rejects a symlink path" \
  "executable capture path is not a regular non-symlink file: tool:" \
  python3 -I -S "$EXECUTABLE_VALIDATOR" \
  "$case_dir/manifest.tsv" 1 tool "$case_dir/tool"

case_dir="$(mktemp -d "$TEST_ROOT/executable-duplicate.XXXXXX")"
printf 'bounded-executable-duplicate-control\n' >"$case_dir/tool"
chmod 755 "$case_dir/tool"
expect_reject \
  "executable manifest rejects duplicate command names" \
  "executable capture received an invalid command inventory" \
  python3 -I -S "$EXECUTABLE_VALIDATOR" \
  "$case_dir/manifest.tsv" 2 tool tool "$case_dir/tool" "$case_dir/tool"

case_dir="$(mktemp -d "$TEST_ROOT/executable-env-shebang.XXXXXX")"
printf '#!/usr/bin/env runner\n' >"$case_dir/script"
printf 'bounded-delegated-interpreter\n' >"$case_dir/runner"
chmod 755 "$case_dir/script" "$case_dir/runner"
env_path="$(python3 -I -S -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$(type -P env)")"
expect_accept \
  "executable manifest closes an env shebang over both env and its delegated interpreter" \
  python3 -I -S "$EXECUTABLE_VALIDATOR" \
  "$case_dir/manifest.tsv" 3 script env runner \
  "$case_dir/script" "$env_path" "$case_dir/runner"

case_dir="$(mktemp -d "$TEST_ROOT/executable-missing-shebang-interpreter.XXXXXX")"
printf '#!/usr/bin/env absent-runner\n' >"$case_dir/script"
chmod 755 "$case_dir/script"
expect_reject \
  "executable manifest rejects an uncaptured delegated shebang interpreter" \
  "delegated shebang interpreter is absent from the executable manifest: script: absent-runner" \
  python3 -I -S "$EXECUTABLE_VALIDATOR" \
  "$case_dir/manifest.tsv" 2 script env "$case_dir/script" "$env_path"

case_dir="$(mktemp -d "$TEST_ROOT/executable-size.XXXXXX")"
python3 -I -S - "$case_dir/tool" <<'PY'
from pathlib import Path
import sys


with Path(sys.argv[1]).open("xb") as stream:
    stream.truncate(512 * 1024 * 1024 + 1)
PY
chmod 755 "$case_dir/tool"
expect_reject \
  "executable manifest rejects a file above its 512 MiB bound" \
  "executable capture file exceeds the 512 MiB executable-capture bound: tool:" \
  python3 -I -S "$EXECUTABLE_VALIDATOR" \
  "$case_dir/manifest.tsv" 1 tool "$case_dir/tool"

# Bootstrap and command-admission controls.  Each case exits before source capture or TeX work.
case_dir="$(mktemp -d "$TEST_ROOT/bootstrap-python.XXXXXX")"
mkdir -p "$case_dir/bin"
printf '#!/bin/sh\nexit 99\n' >"$case_dir/bin/python3"
chmod 755 "$case_dir/bin/python3"
expect_reject \
  "repository/temporary PATH bootstrap Python is rejected" \
  "bootstrap python is outside the admitted executable roots" \
  without_workflow_gate_custody \
  BASH_ENV=/dev/null ENV=/dev/null PATH="$case_dir/bin:$PATH" \
  "$SELF_TEST_BASH" "$CHECKER" --exact

case_dir="$(mktemp -d "$TEST_ROOT/hostile-command.XXXXXX")"
mkdir -p "$case_dir/bin"
printf '#!/bin/sh\nexit 99\n' >"$case_dir/bin/awk"
chmod 755 "$case_dir/bin/awk"
expect_reject \
  "repository/temporary PATH command is rejected" \
  "command is outside the admitted executable roots: awk:" \
  without_workflow_gate_custody \
  BASH_ENV=/dev/null ENV=/dev/null PATH="$case_dir/bin:$PATH" \
  "$SELF_TEST_BASH" "$CHECKER" --exact

expect_reject \
  "verify phase without bootstrap custody is rejected" \
  "captured phase lacks its bootstrap custody" \
  without_workflow_gate_custody \
  BASH_ENV=/dev/null ENV=/dev/null PID_RS_WORKFLOW_PDF_PHASE=verify \
  "$SELF_TEST_BASH" "$CHECKER" --exact

expect_reject \
  "unknown internal phase is rejected" \
  "invalid internal phase" \
  without_workflow_gate_custody \
  BASH_ENV=/dev/null ENV=/dev/null PID_RS_WORKFLOW_PDF_PHASE=hostile \
  "$SELF_TEST_BASH" "$CHECKER" --exact

case_dir="$(mktemp -d "$TEST_ROOT/tmp-colon.XXXXXX")"
bad_tmp="$case_dir/contains:separator"
mkdir -p "$bad_tmp"
expect_reject \
  "Kpathsea/XML-unsafe temporary root is rejected" \
  "temporary root is unsafe for Kpathsea/XML list syntax" \
  without_workflow_gate_custody \
  BASH_ENV=/dev/null ENV=/dev/null TMPDIR="$bad_tmp" \
  "$SELF_TEST_BASH" "$CHECKER" --exact

case_dir="$TEST_ROOT/repository:unsafe"
mkdir -p "$case_dir/scripts"
cp "$CHECKER" "$case_dir/scripts/check-mathematical-workflow-pdf.sh"
expect_reject \
  "Kpathsea/XML-unsafe repository root is rejected" \
  "repository root is unsafe for Kpathsea/XML list syntax" \
  without_workflow_gate_custody BASH_ENV=/dev/null ENV=/dev/null \
  "$SELF_TEST_BASH" "$case_dir/scripts/check-mathematical-workflow-pdf.sh" --exact

# Exercise an actual capture -> read-only snapshot -> env -i -> --noprofile/--norc verify handoff.
# The intended semantic mutation is first in its validator family, so its exact diagnostic proves
# that verification reached captured checker bytes rather than failing incidentally in bootstrap.
ENV_REPOSITORY="$TEST_ROOT/environment-repository"
cp -R "$BASE_REPOSITORY" "$ENV_REPOSITORY"
replace_once \
  "$ENV_REPOSITORY/MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md" \
  "at every observable checkpoint" \
  "at each observable checkpoint"
replace_once \
  "$ENV_REPOSITORY/audit/formal/latex/mathematical-problem-solving-workflow.tex" \
  "at every observable checkpoint" \
  "at each observable checkpoint"
POISON_DIR="$TEST_ROOT/environment-poison"
mkdir -p "$POISON_DIR"
BASH_ENV_ENTERED="$POISON_DIR/capture-shell-entered"
BASH_ENV_LEAKED="$POISON_DIR/verify-shell-leaked"
PYTHONPATH_LEAKED="$POISON_DIR/pythonpath-leaked"
# The generated poison must expand only if a child shell receives BASH_ENV.
# shellcheck disable=SC2016
printf '%s\n' \
  'case "${PID_RS_WORKFLOW_PDF_PHASE:-capture}" in' \
  "  verify) : >\"$BASH_ENV_LEAKED\" ;;" \
  "  *) : >\"$BASH_ENV_ENTERED\" ;;" \
  'esac' >"$POISON_DIR/bash-env.sh"
printf '%s\n' \
  'from pathlib import Path' \
  "Path(\"$PYTHONPATH_LEAKED\").write_text(\"leaked\\n\", encoding=\"utf-8\")" \
  >"$POISON_DIR/sitecustomize.py"
: >"$RESULT_LOG"
set +e
without_workflow_gate_custody \
  BASH_ENV="$POISON_DIR/bash-env.sh" \
  ENV="$POISON_DIR/bash-env.sh" \
  PYTHONPATH="$POISON_DIR" \
  "$SELF_TEST_BASH" "$ENV_REPOSITORY/scripts/check-mathematical-workflow-pdf.sh" --refresh \
  >"$RESULT_LOG" 2>&1
environment_status=$?
set -e
if [[ "$environment_status" -eq 0 ]]; then
  fail "clean-environment re-exec: semantic hostile fixture was accepted"
fi
if ! grep -F -- \
  "canonical semantic correction is absent: at every observable checkpoint" \
  "$RESULT_LOG" >/dev/null; then
  fail "clean-environment re-exec: did not reach the intended captured semantic branch"
fi
if [[ ! -f "$BASH_ENV_ENTERED" ]]; then
  fail "clean-environment re-exec: BASH_ENV poison was not active in the capture shell"
fi
if [[ -e "$BASH_ENV_LEAKED" ]]; then
  fail "clean-environment re-exec: BASH_ENV reached the verification shell"
fi
if [[ -e "$PYTHONPATH_LEAKED" ]]; then
  fail "clean-environment re-exec: PYTHONPATH reached an isolated Python invocation"
fi
pass "capture-to-verify re-exec strips BASH_ENV, ENV, and PYTHONPATH"

# Source manifest capture: test the actual embedded openat/lstat/inventory implementation.
make_capture_fixture() {
  local destination="$1"
  mkdir -p "$destination/base/figures"
  printf 'source\n' >"$destination/base/input.txt"
  printf '<svg/>\n' >"$destination/base/figures/alpha.svg"
  printf '%%PDF-1.7\n' >"$destination/base/figures/alpha.pdf"
}

run_capture_validator() {
  local directory="$1"
  shift
  python3 -I -S "$CAPTURE_VALIDATOR" \
    "$directory/base" "$directory/manifest.tsv" "" "figures" 1 alpha "$@"
}

case_dir="$(mktemp -d "$TEST_ROOT/capture-control.XXXXXX")"
make_capture_fixture "$case_dir"
expect_accept \
  "source capture accepts canonical single-link regular inventory" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-refresh-missing-pdf.XXXXXX")"
make_capture_fixture "$case_dir"
rm "$case_dir/base/figures/alpha.pdf"
expect_accept \
  "refresh-mode source capture permits an absent generated figure PDF" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg

case_dir="$(mktemp -d "$TEST_ROOT/capture-exact-missing-pdf.XXXXXX")"
make_capture_fixture "$case_dir"
rm "$case_dir/base/figures/alpha.pdf"
expect_reject \
  "exact-mode source capture requires every declared figure PDF" \
  "figure directory inventory differs; missing=['alpha.pdf']" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-symlink.XXXXXX")"
make_capture_fixture "$case_dir"
mv "$case_dir/base/input.txt" "$case_dir/real-input.txt"
ln -s "$case_dir/real-input.txt" "$case_dir/base/input.txt"
expect_reject \
  "source capture rejects a symlink leaf" \
  "input is not a regular non-symlink file: 'input.txt'" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-hardlink.XXXXXX")"
make_capture_fixture "$case_dir"
ln "$case_dir/base/input.txt" "$case_dir/second-link.txt"
expect_reject \
  "source capture rejects a multiply-linked input" \
  "input is not a single-link regular file: 'input.txt'" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-component.XXXXXX")"
make_capture_fixture "$case_dir"
mkdir -p "$case_dir/base/real-directory"
printf 'nested\n' >"$case_dir/base/real-directory/nested.txt"
ln -s "$case_dir/base/real-directory" "$case_dir/base/alias"
expect_reject \
  "source capture rejects a symlink path component" \
  "path component is not a real directory: 'alias/nested.txt': 'alias'" \
  run_capture_validator "$case_dir" alias/nested.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-extra.XXXXXX")"
make_capture_fixture "$case_dir"
printf 'unexpected\n' >"$case_dir/base/figures/unexpected.txt"
expect_reject \
  "figure inventory rejects an undeclared entry" \
  "figure directory inventory differs;" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-figure-hardlink.XXXXXX")"
make_capture_fixture "$case_dir"
ln "$case_dir/base/figures/alpha.svg" "$case_dir/second-figure-link.svg"
expect_reject \
  "figure inventory rejects a multiply-linked declared entry" \
  "figure inventory entry is not a single-link regular file: 'alpha.svg'" \
  run_capture_validator "$case_dir" input.txt figures/alpha.svg figures/alpha.pdf

case_dir="$(mktemp -d "$TEST_ROOT/capture-duplicate.XXXXXX")"
make_capture_fixture "$case_dir"
expect_reject \
  "source manifest rejects duplicate path declarations" \
  "manifest contains duplicate paths" \
  run_capture_validator "$case_dir" input.txt input.txt

case_dir="$(mktemp -d "$TEST_ROOT/capture-noncanonical.XXXXXX")"
make_capture_fixture "$case_dir"
expect_reject \
  "source manifest rejects parent-traversal spelling" \
  "noncanonical relative path: 'sub/../input.txt'" \
  run_capture_validator "$case_dir" sub/../input.txt

# Read-only snapshot validator: independently cover modes, object types, and exact inventories.
make_snapshot_fixture() {
  local destination="$1"
  mkdir -p "$destination/a"
  printf 'captured\n' >"$destination/a/input.txt"
  chmod 444 "$destination/a/input.txt"
  chmod 555 "$destination/a" "$destination"
}

case_dir="$(mktemp -d "$TEST_ROOT/snapshot-control.XXXXXX")/snapshot"
make_snapshot_fixture "$case_dir"
expect_accept \
  "read-only snapshot accepts exact 0555/0444 single-link inventory" \
  python3 -I -S "$SNAPSHOT_VALIDATOR" "$case_dir" a/input.txt

case_dir="$(mktemp -d "$TEST_ROOT/snapshot-symlink.XXXXXX")/snapshot"
mkdir -p "$case_dir/a"
printf 'outside\n' >"${case_dir%/*}/outside.txt"
ln -s "${case_dir%/*}/outside.txt" "$case_dir/a/input.txt"
chmod 555 "$case_dir/a" "$case_dir"
expect_reject \
  "read-only snapshot rejects a symlink file" \
  "contains a non-regular file: 'a/input.txt'" \
  python3 -I -S "$SNAPSHOT_VALIDATOR" "$case_dir" a/input.txt

case_dir="$(mktemp -d "$TEST_ROOT/snapshot-hardlink.XXXXXX")/snapshot"
make_snapshot_fixture "$case_dir"
ln "$case_dir/a/input.txt" "${case_dir%/*}/second-link.txt"
expect_reject \
  "read-only snapshot rejects a multiply-linked file" \
  "file is not a single-link mode-0444 regular file: 'a/input.txt'" \
  python3 -I -S "$SNAPSHOT_VALIDATOR" "$case_dir" a/input.txt

case_dir="$(mktemp -d "$TEST_ROOT/snapshot-mode.XXXXXX")/snapshot"
make_snapshot_fixture "$case_dir"
chmod 755 "$case_dir/a"
expect_reject \
  "read-only snapshot rejects writable directory mode" \
  "directory mode drifted from 0555: 'a'" \
  python3 -I -S "$SNAPSHOT_VALIDATOR" "$case_dir" a/input.txt

case_dir="$(mktemp -d "$TEST_ROOT/snapshot-extra.XXXXXX")/snapshot"
mkdir -p "$case_dir/a" "$case_dir/extra"
printf 'captured\n' >"$case_dir/a/input.txt"
chmod 444 "$case_dir/a/input.txt"
chmod 555 "$case_dir/a" "$case_dir/extra" "$case_dir"
expect_reject \
  "read-only snapshot rejects an undeclared directory" \
  "directory inventory drifted;" \
  python3 -I -S "$SNAPSHOT_VALIDATOR" "$case_dir" a/input.txt

# Refresh writer: exercise descriptor-relative success, cross-binding, object-type rejection,
# stable-parent admission, exact non-output-source/figure inventories, and rollback through final
# verification. A process kill or power loss between the six renames remains outside this bounded
# test and is documented by production.
make_refresh_fixture() {
  local directory="$1"
  local figure_directory="audit/formal/latex/figures/mathematical-workflow"
  local -a figure_stems=(
    four-object-assurance-chain
    obligation-dag-minimal-cuts
    shared-oracle-correlated-routes
    invalidation-publication-state-machine
  )
  local stem
  mkdir -p \
    "$directory/root/output/pdf" \
    "$directory/root/$figure_directory" \
    "$directory/source/figures"
  printf 'stable-non-output-source\n' >"$directory/root/source-sentinel.txt"
  printf 'old-pdf-bytes\n' >"$directory/root/output/pdf/workflow.pdf"
  printf 'old-receipt-bytes\n' >"$directory/root/output/pdf/workflow.tsv"
  printf 'new-pdf-bytes\n' >"$directory/source/workflow.pdf"
  for stem in "${figure_stems[@]}"; do
    printf '<svg id="%s"/>\n' "$stem" \
      >"$directory/root/$figure_directory/$stem.svg"
    printf 'old-%s-pdf-bytes\n' "$stem" \
      >"$directory/root/$figure_directory/$stem.pdf"
    printf 'new-%s-pdf-bytes\n' "$stem" \
      >"$directory/source/figures/$stem.pdf"
  done
  python3 -I -S - \
    "$directory/source/workflow.pdf" \
    "$directory/source/workflow.tsv" \
    "$directory/root" \
    "$directory/source/root-inputs.tsv" <<'PY'
import hashlib
from pathlib import Path
import sys


pdf = Path(sys.argv[1]).read_bytes()
Path(sys.argv[2]).write_text(
    "schema\trefresh-self-test\n"
    f"pdf_sha256\t{hashlib.sha256(pdf).hexdigest()}\n",
    encoding="utf-8",
    newline="\n",
)
root = Path(sys.argv[3])
manifest = Path(sys.argv[4])
relatives = ["source-sentinel.txt"] + sorted(
    path.relative_to(root).as_posix()
    for path in (
        root / "audit/formal/latex/figures/mathematical-workflow"
    ).glob("*.svg")
)
rows = []
for relative in relatives:
    data = (root / relative).read_bytes()
    rows.append(f"{relative}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\n")
manifest.write_text("".join(rows), encoding="utf-8", newline="\n")
PY
}

run_refresh_writer() {
  local directory="$1"
  local writer="${2:-$REFRESH_WRITER}"
  local figure_directory="audit/formal/latex/figures/mathematical-workflow"
  python3 -I -S "$writer" \
    "$directory/root" \
    "$directory/source/root-inputs.tsv" \
    6 \
    "$directory/source/workflow.pdf" \
    "$directory/source/workflow.tsv" \
    "$directory/source/figures/four-object-assurance-chain.pdf" \
    "$directory/source/figures/obligation-dag-minimal-cuts.pdf" \
    "$directory/source/figures/shared-oracle-correlated-routes.pdf" \
    "$directory/source/figures/invalidation-publication-state-machine.pdf" \
    output/pdf/workflow.pdf \
    output/pdf/workflow.tsv \
    "$figure_directory/four-object-assurance-chain.pdf" \
    "$figure_directory/obligation-dag-minimal-cuts.pdf" \
    "$figure_directory/shared-oracle-correlated-routes.pdf" \
    "$figure_directory/invalidation-publication-state-machine.pdf"
}

assert_no_refresh_staging_residue() {
  local directory="$1"
  if find "$directory/root" -name '*.refresh-*' -print -quit | grep -q .; then
    fail "refresh operation left a staging or recovery artifact"
  fi
}

assert_no_refresh_temporaries() {
  local directory="$1"
  python3 -I -S - "$directory/root/output/pdf" <<'PY'
from pathlib import Path
import stat
import sys


root = Path(sys.argv[1])
paths = (
    root / "workflow.pdf",
    root / "workflow.tsv",
    root.parent.parent / "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.pdf",
    root.parent.parent / "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.pdf",
    root.parent.parent / "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.pdf",
    root.parent.parent / "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.pdf",
)
temporaries = sorted(
    path.as_posix()
    for directory in {path.parent for path in paths}
    for path in directory.iterdir()
    if ".refresh-" in path.name
)
if temporaries:
    raise SystemExit(f"refresh temporaries remain: {temporaries!r}")
for path in paths:
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise SystemExit(f"refresh destination type drifted: {path}")
    if stat.S_IMODE(status.st_mode) != 0o644:
        raise SystemExit(f"refresh destination mode drifted: {path}")
PY
}

snapshot_refresh_destinations() {
  local directory="$1"
  mkdir -p "$directory/originals/figures"
  cp "$directory/root/output/pdf/workflow.pdf" "$directory/originals/workflow.pdf"
  cp "$directory/root/output/pdf/workflow.tsv" "$directory/originals/workflow.tsv"
  cp "$directory/root/audit/formal/latex/figures/mathematical-workflow"/*.pdf \
    "$directory/originals/figures/"
}

assert_refresh_destinations_restored() {
  local directory="$1"
  local stem
  cmp "$directory/originals/workflow.pdf" "$directory/root/output/pdf/workflow.pdf" \
    || fail "refresh rollback did not restore the original report PDF"
  cmp "$directory/originals/workflow.tsv" "$directory/root/output/pdf/workflow.tsv" \
    || fail "refresh rollback did not restore the original rendering receipt"
  for stem in "${SEMANTIC_STEMS[@]}"; do
    cmp \
      "$directory/originals/figures/$stem.pdf" \
      "$directory/root/audit/formal/latex/figures/mathematical-workflow/$stem.pdf" \
      || fail "refresh rollback did not restore the original figure: $stem"
  done
  assert_no_refresh_temporaries "$directory"
}

case_dir="$(mktemp -d "$TEST_ROOT/refresh-control.XXXXXX")"
make_refresh_fixture "$case_dir"
expect_accept \
  "refresh writer installs the cross-bound pair through stable descriptors" \
  run_refresh_writer "$case_dir"
cmp "$case_dir/source/workflow.pdf" "$case_dir/root/output/pdf/workflow.pdf" \
  || fail "refresh success PDF readback differs"
cmp "$case_dir/source/workflow.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "refresh success receipt readback differs"
for stem in "${SEMANTIC_STEMS[@]}"; do
  cmp \
    "$case_dir/source/figures/$stem.pdf" \
    "$case_dir/root/audit/formal/latex/figures/mathematical-workflow/$stem.pdf" \
    || fail "refresh success figure readback differs: $stem"
done
assert_no_refresh_temporaries "$case_dir"
pass "refresh success leaves exact mode-0644 single-link files and no staging residue"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-absent-control.XXXXXX")"
make_refresh_fixture "$case_dir"
rm \
  "$case_dir/root/output/pdf/workflow.pdf" \
  "$case_dir/root/output/pdf/workflow.tsv" \
  "$case_dir/root/audit/formal/latex/figures/mathematical-workflow"/*.pdf
expect_accept \
  "refresh writer installs all six artifacts when every destination is initially absent" \
  run_refresh_writer "$case_dir"
cmp "$case_dir/source/workflow.pdf" "$case_dir/root/output/pdf/workflow.pdf" \
  || fail "absent-destination success PDF readback differs"
cmp "$case_dir/source/workflow.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "absent-destination success receipt readback differs"
for stem in "${SEMANTIC_STEMS[@]}"; do
  cmp \
    "$case_dir/source/figures/$stem.pdf" \
    "$case_dir/root/audit/formal/latex/figures/mathematical-workflow/$stem.pdf" \
    || fail "absent-destination success figure readback differs: $stem"
done
assert_no_refresh_temporaries "$case_dir"
pass "refresh absent-destination path leaves exact files and no staging residue"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-binding.XXXXXX")"
make_refresh_fixture "$case_dir"
replace_once \
  "$case_dir/source/workflow.tsv" \
  'pdf_sha256' \
  'wrong_pdf_sha256'
expect_reject \
  "refresh writer rejects a receipt that does not bind its staged PDF" \
  "refresh rendering receipt does not uniquely bind the staged PDF" \
  run_refresh_writer "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-source-symlink.XXXXXX")"
make_refresh_fixture "$case_dir"
mv "$case_dir/source/workflow.pdf" "$case_dir/source/workflow-real.pdf"
ln -s workflow-real.pdf "$case_dir/source/workflow.pdf"
expect_reject \
  "refresh writer rejects a symlink source" \
  "refresh source is not a single-link regular file" \
  run_refresh_writer "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-destination-hardlink.XXXXXX")"
make_refresh_fixture "$case_dir"
ln "$case_dir/root/output/pdf/workflow.pdf" "$case_dir/root/output/pdf/second-link.pdf"
expect_reject \
  "refresh writer rejects a multiply linked destination" \
  "refresh destination output/pdf/workflow.pdf is not a single-link regular file" \
  run_refresh_writer "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-parent-symlink.XXXXXX")"
make_refresh_fixture "$case_dir"
mv "$case_dir/root/output" "$case_dir/root/output-real"
ln -s output-real "$case_dir/root/output"
expect_reject \
  "refresh writer rejects a symlink destination parent" \
  "refresh destination parent is not a stable real directory" \
  run_refresh_writer "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-rollback.XXXXXX")"
make_refresh_fixture "$case_dir"
cp "$case_dir/root/output/pdf/workflow.pdf" "$case_dir/old.pdf"
cp "$case_dir/root/output/pdf/workflow.tsv" "$case_dir/old.tsv"
mkdir "$case_dir/old-figures"
cp "$case_dir/root/audit/formal/latex/figures/mathematical-workflow"/*.pdf \
  "$case_dir/old-figures/"
rollback_writer="$case_dir/refresh-injected-failure.py"
cp "$REFRESH_WRITER" "$rollback_writer"
replace_once \
  "$rollback_writer" \
  $'        for item in staged:\n            assert_all_live_bindings(f"before replacing {item[\'relative\']}")\n            parent_descriptor = int(item["parent_descriptor"])' \
  $'        for replacement_index, item in enumerate(staged):\n            if replacement_index == 1:\n                raise OSError("injected second replacement failure")\n            assert_all_live_bindings(f"before replacing {item[\'relative\']}")\n            parent_descriptor = int(item["parent_descriptor"])'
expect_reject \
  "refresh writer reports an injected second-replacement failure" \
  "injected second replacement failure" \
  run_refresh_writer "$case_dir" "$rollback_writer"
cmp "$case_dir/old.pdf" "$case_dir/root/output/pdf/workflow.pdf" \
  || fail "refresh rollback did not restore the original PDF"
cmp "$case_dir/old.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "refresh rollback did not preserve the original receipt"
for stem in "${SEMANTIC_STEMS[@]}"; do
  cmp \
    "$case_dir/old-figures/$stem.pdf" \
    "$case_dir/root/audit/formal/latex/figures/mathematical-workflow/$stem.pdf" \
    || fail "refresh rollback did not preserve the original figure: $stem"
done
assert_no_refresh_temporaries "$case_dir"
pass "refresh ordinary-exception rollback restores all six original files without staging residue"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-absent-first-rollback.XXXXXX")"
make_refresh_fixture "$case_dir"
cp "$case_dir/root/output/pdf/workflow.tsv" "$case_dir/old.tsv"
mkdir "$case_dir/old-figures"
cp "$case_dir/root/audit/formal/latex/figures/mathematical-workflow"/*.pdf \
  "$case_dir/old-figures/"
rm "$case_dir/root/output/pdf/workflow.pdf"
absent_rollback_writer="$case_dir/refresh-injected-absent-rollback.py"
cp "$REFRESH_WRITER" "$absent_rollback_writer"
replace_once \
  "$absent_rollback_writer" \
  $'        for item in staged:\n            assert_all_live_bindings(f"before replacing {item[\'relative\']}")\n            parent_descriptor = int(item["parent_descriptor"])' \
  $'        for replacement_index, item in enumerate(staged):\n            if replacement_index == 1:\n                raise OSError("injected absent-first rollback failure")\n            assert_all_live_bindings(f"before replacing {item[\'relative\']}")\n            parent_descriptor = int(item["parent_descriptor"])'
expect_reject \
  "refresh writer rolls back an initially absent first destination" \
  "injected absent-first rollback failure" \
  run_refresh_writer "$case_dir" "$absent_rollback_writer"
if [[ -e "$case_dir/root/output/pdf/workflow.pdf" || \
      -L "$case_dir/root/output/pdf/workflow.pdf" ]]; then
  fail "refresh rollback recreated an initially absent report PDF"
fi
cmp "$case_dir/old.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "absent-first rollback changed the original receipt"
for stem in "${SEMANTIC_STEMS[@]}"; do
  cmp \
    "$case_dir/old-figures/$stem.pdf" \
    "$case_dir/root/audit/formal/latex/figures/mathematical-workflow/$stem.pdf" \
    || fail "absent-first rollback changed an untouched figure: $stem"
done
assert_no_refresh_staging_residue "$case_dir"
pass "refresh rollback removes an installed node whose destination was initially absent"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-cross-parent-rollback.XXXXXX")"
make_refresh_fixture "$case_dir"
snapshot_refresh_destinations "$case_dir"
cross_parent_writer="$case_dir/refresh-injected-cross-parent-failure.py"
cp "$REFRESH_WRITER" "$cross_parent_writer"
replace_once \
  "$cross_parent_writer" \
  $'        for item in staged:\n            assert_all_live_bindings(f"before replacing {item[\'relative\']}")\n            parent_descriptor = int(item["parent_descriptor"])' \
  $'        for replacement_index, item in enumerate(staged):\n            if replacement_index == 4:\n                raise OSError("injected fifth replacement failure")\n            assert_all_live_bindings(f"before replacing {item[\'relative\']}")\n            parent_descriptor = int(item["parent_descriptor"])'
expect_reject \
  "refresh writer rolls back four completed replacements spanning two parents" \
  "injected fifth replacement failure" \
  run_refresh_writer "$case_dir" "$cross_parent_writer"
assert_refresh_destinations_restored "$case_dir"
pass "refresh rollback restores completed report, receipt, and figure replacements"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-final-cas-race.XXXXXX")"
make_refresh_fixture "$case_dir"
cp "$case_dir/root/output/pdf/workflow.tsv" "$case_dir/old.tsv"
mkdir "$case_dir/old-figures"
cp "$case_dir/root/audit/formal/latex/figures/mathematical-workflow"/*.pdf \
  "$case_dir/old-figures/"
race_writer="$case_dir/refresh-injected-final-cas-race.py"
cp "$REFRESH_WRITER" "$race_writer"
replace_once \
  "$race_writer" \
  $'            else:\n                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )' \
  $'            else:\n                if not replaced:\n                    concurrent_temporary = create_staged_file(\n                        parent_descriptor,\n                        "concurrent-writer",\n                        b"concurrent-writer-bytes\\n",\n                        0o644,\n                    )\n                    atomic_rename_at(\n                        parent_descriptor,\n                        concurrent_temporary,\n                        destination_name,\n                        exchange=True,\n                    )\n                    os.unlink(concurrent_temporary, dir_fd=parent_descriptor)\n                    os.fsync(parent_descriptor)\n                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )'
expect_reject \
  "refresh writer detects a destination replacement in its final compare-and-swap window" \
  "destination changed in the final compare-and-swap window: output/pdf/workflow.pdf" \
  run_refresh_writer "$case_dir" "$race_writer"
printf 'concurrent-writer-bytes\n' >"$case_dir/concurrent.pdf"
cmp "$case_dir/concurrent.pdf" "$case_dir/root/output/pdf/workflow.pdf" \
  || fail "refresh final-CAS rollback overwrote concurrent PDF bytes"
cmp "$case_dir/old.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "refresh final-CAS race changed the original receipt"
for stem in "${SEMANTIC_STEMS[@]}"; do
  cmp \
    "$case_dir/old-figures/$stem.pdf" \
    "$case_dir/root/audit/formal/latex/figures/mathematical-workflow/$stem.pdf" \
    || fail "refresh final-CAS race changed an untouched figure: $stem"
done
assert_no_refresh_temporaries "$case_dir"
pass "refresh final-CAS rollback preserves concurrent bytes and all untouched artifacts"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-final-cas-symlink.XXXXXX")"
make_refresh_fixture "$case_dir"
cp "$case_dir/root/output/pdf/workflow.tsv" "$case_dir/old.tsv"
symlink_race_writer="$case_dir/refresh-injected-final-cas-symlink.py"
cp "$REFRESH_WRITER" "$symlink_race_writer"
replace_once \
  "$symlink_race_writer" \
  $'            else:\n                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )' \
  $'            else:\n                if not replaced:\n                    concurrent_temporary = ".concurrent-symlink"\n                    os.symlink(\n                        "concurrent-target",\n                        concurrent_temporary,\n                        dir_fd=parent_descriptor,\n                    )\n                    atomic_rename_at(\n                        parent_descriptor,\n                        concurrent_temporary,\n                        destination_name,\n                        exchange=True,\n                    )\n                    os.unlink(concurrent_temporary, dir_fd=parent_descriptor)\n                    os.fsync(parent_descriptor)\n                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )'
expect_reject \
  "refresh writer detects and restores a symlink replacement in its final swap window" \
  "destination changed in the final compare-and-swap window: output/pdf/workflow.pdf" \
  run_refresh_writer "$case_dir" "$symlink_race_writer"
python3 -I -S - "$case_dir/root/output/pdf/workflow.pdf" <<'PY'
from pathlib import Path
import os
import stat
import sys


path = Path(sys.argv[1])
status = path.lstat()
if not stat.S_ISLNK(status.st_mode) or os.readlink(path) != "concurrent-target":
    raise SystemExit("refresh final-CAS recovery did not preserve the concurrent symlink")
PY
cmp "$case_dir/old.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "refresh symlink race changed the original receipt"
if find "$case_dir/root" -name '*.refresh-*' -print -quit | grep -q .; then
  fail "refresh symlink race left a staging artifact"
fi
pass "refresh final-CAS recovery preserves a concurrent symlink without staging residue"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-final-cas-hardlink.XXXXXX")"
make_refresh_fixture "$case_dir"
cp "$case_dir/root/output/pdf/workflow.tsv" "$case_dir/old.tsv"
hardlink_race_writer="$case_dir/refresh-injected-final-cas-hardlink.py"
cp "$REFRESH_WRITER" "$hardlink_race_writer"
replace_once \
  "$hardlink_race_writer" \
  $'            else:\n                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )' \
  $'            else:\n                if not replaced:\n                    concurrent_temporary = create_staged_file(\n                        parent_descriptor,\n                        "concurrent-hardlink",\n                        b"concurrent-hardlink-bytes\\n",\n                        0o644,\n                    )\n                    concurrent_second = ".concurrent-hardlink-second"\n                    os.link(\n                        concurrent_temporary,\n                        concurrent_second,\n                        src_dir_fd=parent_descriptor,\n                        dst_dir_fd=parent_descriptor,\n                        follow_symlinks=False,\n                    )\n                    atomic_rename_at(\n                        parent_descriptor,\n                        concurrent_temporary,\n                        destination_name,\n                        exchange=True,\n                    )\n                    os.unlink(concurrent_temporary, dir_fd=parent_descriptor)\n                    os.fsync(parent_descriptor)\n                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )'
expect_reject \
  "refresh writer detects and restores a multiply linked replacement in its final swap window" \
  "destination changed in the final compare-and-swap window: output/pdf/workflow.pdf" \
  run_refresh_writer "$case_dir" "$hardlink_race_writer"
printf 'concurrent-hardlink-bytes\n' >"$case_dir/concurrent-hardlink.pdf"
cmp "$case_dir/concurrent-hardlink.pdf" "$case_dir/root/output/pdf/workflow.pdf" \
  || fail "refresh final-CAS recovery did not preserve concurrent hard-link bytes"
python3 -I -S - \
  "$case_dir/root/output/pdf/workflow.pdf" \
  "$case_dir/root/output/pdf/.concurrent-hardlink-second" <<'PY'
from pathlib import Path
import os
import sys


left = os.stat(Path(sys.argv[1]), follow_symlinks=False)
right = os.stat(Path(sys.argv[2]), follow_symlinks=False)
if (left.st_dev, left.st_ino, left.st_nlink) != (right.st_dev, right.st_ino, 2):
    raise SystemExit("concurrent hard-link identity was not preserved")
PY
cmp "$case_dir/old.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "refresh hard-link race changed the original receipt"
if find "$case_dir/root" -name '*.refresh-*' -print -quit | grep -q .; then
  fail "refresh hard-link race left a staging artifact"
fi
pass "refresh final-CAS recovery preserves a concurrent hard link without staging residue"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-post-install-symlink.XXXXXX")"
make_refresh_fixture "$case_dir"
cp "$case_dir/root/output/pdf/workflow.pdf" "$case_dir/old.pdf"
cp "$case_dir/root/output/pdf/workflow.tsv" "$case_dir/old.tsv"
post_install_writer="$case_dir/refresh-injected-post-install-symlink.py"
cp "$REFRESH_WRITER" "$post_install_writer"
replace_once \
  "$post_install_writer" \
  $'                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )\n                item["install_kind"] = "exchange"' \
  $'                atomic_rename_at(\n                    parent_descriptor,\n                    new_temporary,\n                    destination_name,\n                    exchange=True,\n                )\n                if not replaced:\n                    os.unlink(destination_name, dir_fd=parent_descriptor)\n                    os.symlink(\n                        "post-install-concurrent-target",\n                        destination_name,\n                        dir_fd=parent_descriptor,\n                    )\n                    os.fsync(parent_descriptor)\n                item["install_kind"] = "exchange"'
expect_reject \
  "refresh rollback preserves a type-changing writer that arrives after installation" \
  "replacement failed and rollback was incomplete" \
  run_refresh_writer "$case_dir" "$post_install_writer"
python3 -I -S - "$case_dir/root/output/pdf/workflow.pdf" <<'PY'
from pathlib import Path
import os
import stat
import sys


path = Path(sys.argv[1])
status = path.lstat()
if (
    not stat.S_ISLNK(status.st_mode)
    or os.readlink(path) != "post-install-concurrent-target"
):
    raise SystemExit("post-install concurrent symlink was not preserved")
PY
cmp "$case_dir/old.tsv" "$case_dir/root/output/pdf/workflow.tsv" \
  || fail "refresh post-install race changed the original receipt"
python3 -I -S - \
  "$case_dir/root/output/pdf" \
  "$case_dir/old.pdf" <<'PY'
from pathlib import Path
import sys


directory = Path(sys.argv[1])
old = Path(sys.argv[2]).read_bytes()
recovery = sorted(path for path in directory.iterdir() if ".refresh-new." in path.name)
if len(recovery) != 1 or recovery[0].read_bytes() != old:
    raise SystemExit("displaced pre-install PDF recovery node was not retained exactly")
PY
pass "refresh incomplete rollback retains the displaced original while preserving a concurrent path"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-final-verification-rollback.XXXXXX")"
make_refresh_fixture "$case_dir"
snapshot_refresh_destinations "$case_dir"
final_verification_writer="$case_dir/refresh-injected-final-verification.py"
cp "$REFRESH_WRITER" "$final_verification_writer"
replace_once \
  "$final_verification_writer" \
  $'        assert_all_live_bindings("final pair verification")' \
  $'        assert_all_live_bindings("final pair verification")\n        raise RuntimeError("injected final verification failure")'
expect_reject \
  "refresh writer rolls back all six artifacts after final live verification begins" \
  "injected final verification failure" \
  run_refresh_writer "$case_dir" "$final_verification_writer"
assert_refresh_destinations_restored "$case_dir"
pass "refresh final-verification failure restores every original artifact"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-post-install-source-drift.XXXXXX")"
make_refresh_fixture "$case_dir"
snapshot_refresh_destinations "$case_dir"
source_drift_writer="$case_dir/refresh-injected-source-drift.py"
cp "$REFRESH_WRITER" "$source_drift_writer"
replace_once \
  "$source_drift_writer" \
  $'        verify_nonoutput_source_manifest("post-install verification")' \
  $'        (root / "source-sentinel.txt").write_bytes(b"injected-source-drift\\n")\n        verify_nonoutput_source_manifest("post-install verification")'
expect_reject \
  "refresh writer rolls back all artifacts when a non-output source drifts after installation" \
  "non-output source changed during post-install verification: source-sentinel.txt" \
  run_refresh_writer "$case_dir" "$source_drift_writer"
assert_refresh_destinations_restored "$case_dir"
pass "refresh post-install source drift is detected inside the rollback window"

case_dir="$(mktemp -d "$TEST_ROOT/refresh-final-figure-inventory.XXXXXX")"
make_refresh_fixture "$case_dir"
snapshot_refresh_destinations "$case_dir"
figure_inventory_writer="$case_dir/refresh-injected-figure-extra.py"
cp "$REFRESH_WRITER" "$figure_inventory_writer"
replace_once \
  "$figure_inventory_writer" \
  $'        verify_final_figure_inventory()' \
  $'        (root / figure_parent / "unexpected-extra.pdf").write_bytes(b"concurrent-extra\\n")\n        verify_final_figure_inventory()'
expect_reject \
  "refresh writer rolls back all artifacts when the final figure inventory gains an extra node" \
  "final figure inventory differs;" \
  run_refresh_writer "$case_dir" "$figure_inventory_writer"
assert_refresh_destinations_restored "$case_dir"
printf 'concurrent-extra\n' >"$case_dir/expected-extra.pdf"
cmp \
  "$case_dir/expected-extra.pdf" \
  "$case_dir/root/audit/formal/latex/figures/mathematical-workflow/unexpected-extra.pdf" \
  || fail "refresh rollback did not preserve the unexpected concurrent figure entry"
pass "refresh final-inventory failure preserves the extra node and restores all six outputs"

# Visual-review receipt parser.  Build a valid fixture from exact copied artifact bytes first.
VISUAL_CONTROL="$TEST_ROOT/visual-control.md"
python3 -I -S - \
  "$VISUAL_CONTROL" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" \
  "$EXPECTED_PAGES" "$EXPECTED_DPI" <<'PY'
from pathlib import Path
import hashlib
import sys


destination = Path(sys.argv[1])
pdf = Path(sys.argv[2])
rendering_receipt = Path(sys.argv[3])
pages = int(sys.argv[4])
dpi = int(sys.argv[5])
text = f"""# Mathematical workflow PDF visual-review receipt

schema: `pid-rs/mathematical-workflow-visual-review/v1`
subject: `output/pdf/mathematical-problem-solving-workflow.pdf`
pdf_sha256: `{hashlib.sha256(pdf.read_bytes()).hexdigest()}`
rendering_receipt: `output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv`
rendering_receipt_sha256: `{hashlib.sha256(rendering_receipt.read_bytes()).hexdigest()}`
pages: `{pages}`
dpi: `{dpi}`
color_pages_reviewed: `1-{pages}`
grayscale_pages_reviewed: `1-{pages}`
original_resolution_spot_checks: `1-{pages}`
figure_pages_reviewed: `3,4,9,10`
status: `passed`
review_date_utc: `2026-08-04`
reviewer_kind: `agent-visual-inspection`

All {pages} color pages and all {pages} grayscale pages were viewed in page order.

No blank, clipped, overlapping, misordered, or visibly corrupt page was observed.

Every workflow figure was reviewed at original resolution in both color and grayscale.

The root agent and a separately assigned visual-review agent inspected the artifact; that role separation is not evidentiary independence.

This receipt records a bounded page-by-page agent visual inspection; it is not a proof of mathematical correctness, accessibility conformance, or semantic completeness.
"""
destination.write_text(text, encoding="utf-8", newline="\n")
PY

expect_accept \
  "visual receipt accepts exact artifact bindings and bounded-review language" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$VISUAL_CONTROL" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" \
  "$EXPECTED_PAGES" "$EXPECTED_DPI"

case_file="$TEST_ROOT/visual-private-path.md"
cp "$VISUAL_CONTROL" "$case_file"
printf "host: \`/private/host-specific\`\n" >>"$case_file"
expect_reject \
  "visual receipt rejects private host paths" \
  "visual receipt contains a private or host-local path" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"

case_file="$TEST_ROOT/visual-duplicate-field.md"
cp "$VISUAL_CONTROL" "$case_file"
printf "schema: \`pid-rs/mathematical-workflow-visual-review/v1\`\n" >>"$case_file"
expect_reject \
  "visual receipt rejects duplicate canonical fields" \
  "visual receipt must contain exactly one canonical schema field" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"

case_file="$TEST_ROOT/visual-digest.md"
cp "$VISUAL_CONTROL" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import re
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text, count = re.subn(r"(?m)^pdf_sha256: `[0-9a-f]{64}`$", f"pdf_sha256: `{'0' * 64}`", text)
if count != 1:
    raise SystemExit("visual PDF digest mutation target drifted")
path.write_text(text, encoding="utf-8", newline="\n")
PY
expect_reject \
  "visual receipt rejects a stale PDF digest binding" \
  "visual receipt field pdf_sha256 differs" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"

case_file="$TEST_ROOT/visual-statement.md"
cp "$VISUAL_CONTROL" "$case_file"
replace_once \
  "$case_file" \
  "No blank, clipped, overlapping, misordered, or visibly corrupt page was observed." \
  "No obvious layout defect was observed."
expect_reject \
  "visual receipt rejects weakened required review language" \
  "visual receipt required top-level review paragraph is absent or duplicated" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"

case_file="$TEST_ROOT/visual-contradictory-extra-paragraph.md"
cp "$VISUAL_CONTROL" "$case_file"
printf '\nContradiction: no page was actually viewed.\n' >>"$case_file"
expect_reject \
  "visual receipt rejects an undeclared contradictory top-level paragraph" \
  "visual receipt paragraph inventory differs from the closed schema" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"

case_file="$TEST_ROOT/visual-crlf.md"
python3 -I -S - "$VISUAL_CONTROL" "$case_file" <<'PY'
from pathlib import Path
import sys


source = Path(sys.argv[1]).read_bytes()
Path(sys.argv[2]).write_bytes(source.replace(b"\n", b"\r\n", 1))
PY
expect_reject \
  "visual receipt rejects noncanonical CRLF bytes" \
  "visual receipt does not have canonical LF termination" \
  python3 -I -S "$VISUAL_VALIDATOR" \
  "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"

mutate_visual_context() {
  local destination="$1"
  local mode="$2"
  python3 -I -S - "$VISUAL_CONTROL" "$destination" "$mode" <<'PY'
from pathlib import Path
import sys


source = Path(sys.argv[1]).read_text(encoding="utf-8")
destination = Path(sys.argv[2])
mode = sys.argv[3]
if mode == "comment":
    mutated = f"<!--\n{source}-->\n"
elif mode == "fence":
    mutated = f"```text\n{source}```\n"
elif mode == "quote":
    mutated = "\n".join(f"> {line}" for line in source.splitlines()) + "\n"
else:
    raise SystemExit(f"unknown visual-context mutation: {mode}")
destination.write_text(mutated, encoding="utf-8", newline="\n")
PY
}

for context_mode in comment fence quote; do
  case_file="$TEST_ROOT/visual-$context_mode.md"
  mutate_visual_context "$case_file" "$context_mode"
  expect_reject \
    "visual receipt rejects fields and claims concealed in $context_mode context" \
    "visual receipt contains forbidden Markdown concealment or non-top-level content" \
    python3 -I -S "$VISUAL_VALIDATOR" \
    "$case_file" "$BASE_PDF" "$BASE_RENDERING_RECEIPT" "$EXPECTED_PAGES" "$EXPECTED_DPI"
done

# SVG validator.  All hostile cases start from a control that the same extracted production block
# accepts, preventing malformed baseline fixtures from supplying false-positive rejection credit.
SVG_STEMS=(
  four-object-assurance-chain
  obligation-dag-minimal-cuts
  shared-oracle-correlated-routes
  invalidation-publication-state-machine
)
run_svg_validator() {
  python3 -I -S "$SVG_VALIDATOR" "$1" "${SVG_STEMS[@]}"
}

expect_accept \
  "SVG validator accepts all four exact source figures" \
  run_svg_validator "$BASE_FIGURE_DIR"

make_svg_case() {
  local destination="$1"
  mkdir -p "$destination"
  cp "$BASE_FIGURE_DIR"/*.svg "$destination/"
}

expect_figure2_replacement_reject() {
  local slug="$1"
  local label="$2"
  local old="$3"
  local new="$4"
  local expected="$5"
  local directory
  directory="$(mktemp -d "$TEST_ROOT/svg-figure2-$slug.XXXXXX")"
  make_svg_case "$directory"
  replace_once \
    "$directory/obligation-dag-minimal-cuts.svg" \
    "$old" \
    "$new"
  expect_reject "$label" "$expected" run_svg_validator "$directory"
}

# Figure 2 has four separately checked semantic layers: canonical metadata, a finite independently
# enumerated minimal-transversal family, accessible description prose, and visible inventory text.
# Keep every non-target layer exact in each mutant so an unrelated parse or wording failure cannot
# earn credit for the branch named by the case.
expect_figure2_replacement_reject \
  "source-svg-binding" \
  "Figure 2 rejects drift of the source-SVG title/description binding" \
  'aria-labelledby="obligation-title obligation-desc"' \
  'aria-labelledby="obligation-desc obligation-title"' \
  "obligation-dag-minimal-cuts.svg source-SVG title/description binding must name title then description"

expect_figure2_replacement_reject \
  "cut-omission" \
  "Figure 2 rejects omission of the A2,B1 minimal cut from metadata" \
  'data-minimal-cuts="C;A1,B1;A2,B1"' \
  'data-minimal-cuts="C;A1,B1"' \
  "obligation-dag-minimal-cuts.svg declared cuts are not the complete minimal transversal family:"

expect_figure2_replacement_reject \
  "cut-nonminimal" \
  "Figure 2 rejects an added nonminimal A1,A2,B1 metadata cut" \
  'data-minimal-cuts="C;A1,B1;A2,B1"' \
  'data-minimal-cuts="C;A1,B1;A2,B1;A1,A2,B1"' \
  "obligation-dag-minimal-cuts.svg declared cuts are not the complete minimal transversal family:"

expect_figure2_replacement_reject \
  "route-a" \
  "Figure 2 rejects drift of route A metadata" \
  'data-route-a="A1,A2,C"' \
  'data-route-a="A1,C"' \
  "obligation-dag-minimal-cuts.svg route family drifted"

expect_figure2_replacement_reject \
  "universe" \
  "Figure 2 rejects drift of the frozen admissible universe metadata" \
  'data-admissible-universe="A1,A2,B1,C"' \
  'data-admissible-universe="A1,B1,C"' \
  "obligation-dag-minimal-cuts.svg admissible universe drifted"

expect_figure2_replacement_reject \
  "description-universe" \
  "Figure 2 rejects deletion of the accessible frozen-universe literal" \
  "frozen admissible universe U = {A1, A2, B1, C}" \
  "declared universe U = {A1, A2, B1, C}" \
  "obligation-dag-minimal-cuts.svg description lacks cut semantics: 'frozen admissible universe U = {A1, A2, B1, C}'"

expect_figure2_replacement_reject \
  "description-routes" \
  "Figure 2 rejects deletion of the accessible route-family literal" \
  "route A = {A1, A2, C} and route B = {B1, C}" \
  "declared A = {A1, A2, C} and declared B = {B1, C}" \
  "obligation-dag-minimal-cuts.svg description lacks cut semantics: 'route A = {A1, A2, C} and route B = {B1, C}'"

expect_figure2_replacement_reject \
  "description-cuts" \
  "Figure 2 rejects deletion of the accessible complete-cut-family literal" \
  "complete inclusion-minimal cut family is {C}, {A1, B1}, and {A2, B1}" \
  "declared cut family is {C}, {A1, B1}, and {A2, B1}" \
  "obligation-dag-minimal-cuts.svg description lacks cut semantics: 'complete inclusion-minimal cut family is {C}, {A1, B1}, and {A2, B1}'"

expect_figure2_replacement_reject \
  "visible-or" \
  "Figure 2 rejects deletion of the visible OR-acceptance literal" \
  "A or B accepted" \
  "Either accepted route suffices" \
  "obligation-dag-minimal-cuts.svg lacks corrected visible semantic text: 'A or B accepted'"

expect_figure2_replacement_reject \
  "visible-universe" \
  "Figure 2 rejects deletion of the visible frozen-universe inventory" \
  "Frozen U = {A1, A2, B1, C}" \
  "Declared U = {A1, A2, B1, C}" \
  "obligation-dag-minimal-cuts.svg lacks corrected visible semantic text: 'Frozen U = {A1, A2, B1, C}'"

expect_figure2_replacement_reject \
  "visible-routes" \
  "Figure 2 rejects deletion of the visible route inventory" \
  "Routes: A = {A1, A2, C}; B = {B1, C}" \
  "Declared routes: A = {A1, A2, C}; B = {B1, C}" \
  "obligation-dag-minimal-cuts.svg lacks corrected visible semantic text: 'Routes: A = {A1, A2, C}; B = {B1, C}'"

expect_figure2_replacement_reject \
  "visible-cuts" \
  "Figure 2 rejects deletion of the visible complete-cut inventory" \
  "All inclusion-minimal cuts: {C}; {A1, B1}; {A2, B1}" \
  "Declared minimal cuts: {C}; {A1, B1}; {A2, B1}" \
  "obligation-dag-minimal-cuts.svg lacks corrected visible semantic text: 'All inclusion-minimal cuts: {C}; {A1, B1}; {A2, B1}'"

expect_figure2_replacement_reject \
  "forbidden-route-node-cut" \
  "Figure 2 rejects the old route-node cut while retaining required semantics" \
  '</svg>' \
  $'  <!-- Cut 2: {route A, route B} -->\n</svg>' \
  "obligation-dag-minimal-cuts.svg retains superseded implication language: 'Cut 2: {route A, route B}'"

case_dir="$(mktemp -d "$TEST_ROOT/svg-doctype.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  $'<?xml version="1.0" encoding="UTF-8"?>\n' \
  $'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE svg [<!ENTITY hostile "x">]>\n'
expect_reject \
  "SVG rejects DOCTYPE/entity declarations" \
  "four-object-assurance-chain.svg contains a DOCTYPE or entity declaration" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-resource.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  $'<?xml version="1.0" encoding="UTF-8"?>\n' \
  $'<?xml version="1.0" encoding="UTF-8"?>\n<!-- data:text/plain,hostile -->\n'
expect_reject \
  "SVG rejects external/executable resource forms" \
  "four-object-assurance-chain.svg contains a forbidden external or executable CSS/resource form" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-hidden.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '<svg xmlns=' \
  '<svg style="display:none" xmlns='
expect_reject \
  "SVG rejects hidden content" \
  "four-object-assurance-chain.svg contains hidden content" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-hidden-presentation.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  'A · target correspondence' \
  'A · target mapping'
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '</svg>' \
  $'  <text display="none">target correspondence</text>\n</svg>'
expect_reject \
  "SVG rejects a required literal hidden by a presentation attribute" \
  "four-object-assurance-chain.svg contains hidden content" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-hidden-defs.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  'A · target correspondence' \
  'A · target mapping'
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '</svg>' \
  $'  <defs><text>target correspondence</text></defs>\n</svg>'
expect_reject \
  "SVG excludes required literals placed in nonrendered definition containers" \
  "four-object-assurance-chain.svg contains text in a nonrendered container" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-required-fill-none.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '<text x="84" y="550" class="small">' \
  '<text x="84" y="550" class="small" style="fill:none">'
expect_reject \
  "SVG rejects required semantic text made nonvisible with a none fill" \
  "four-object-assurance-chain.svg contains text with a none fill" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-required-off-canvas.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '<text x="84" y="550" class="small">' \
  '<text x="1684" y="550" class="small">'
expect_reject \
  "SVG rejects required semantic text anchored outside the declared viewBox" \
  "four-object-assurance-chain.svg text anchor lies outside the viewBox" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-exact-bytes.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '</svg>' \
  $'  <!-- semantically inert unreviewed byte drift -->\n</svg>'
expect_reject \
  "SVG exact-source custody rejects otherwise unrecognized byte drift" \
  "four-object-assurance-chain.svg differs from its exact visually reviewed source bytes" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-event.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '<svg xmlns=' \
  '<svg onload="hostile()" xmlns='
expect_reject \
  "SVG rejects event-handler attributes" \
  "four-object-assurance-chain.svg contains an event handler or XML base" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-palette.XXXXXX")"
make_svg_case "$case_dir"
python3 -I -S - "$case_dir/four-object-assurance-chain.svg" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "#1F3F60" not in text:
    raise SystemExit("palette mutation target drifted")
path.write_text(text.replace("#1F3F60", "#FF00FF"), encoding="utf-8", newline="\n")
PY
expect_reject \
  "SVG rejects paint outside the exact project palette" \
  "four-object-assurance-chain.svg uses an unsupported paint declaration: '#FF00FF'" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-duplicate-id.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '</svg>' \
  $'  <g id="four-object-title"/>\n</svg>'
expect_reject \
  "SVG rejects duplicate XML identifiers" \
  "four-object-assurance-chain.svg contains duplicate XML identifiers" \
  run_svg_validator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/svg-href.XXXXXX")"
make_svg_case "$case_dir"
replace_once \
  "$case_dir/four-object-assurance-chain.svg" \
  '</svg>' \
  $'  <a href="/ambient/resource"/>\n</svg>'
expect_reject \
  "SVG rejects non-local href attributes" \
  "four-object-assurance-chain.svg contains a non-local href" \
  run_svg_validator "$case_dir"

# Rendering-receipt parser.  Validate the exact copied committed receipt first, then mutate only
# the generated side so each rejection is labelled and branch-specific.
run_rendering_receipt_validator() {
  local generated_receipt="$1"
  python3 -I -S "$RENDERING_RECEIPT_VALIDATOR" \
    "$BASE_RENDERING_RECEIPT" "$BASE_PDF" \
    "$generated_receipt" "$BASE_PDF" \
    "$EXPECTED_PAGES" "$EXPECTED_DPI" --exact
}

expect_accept \
  "rendering receipt accepts exact v2 row inventory and PDF binding" \
  run_rendering_receipt_validator "$BASE_RENDERING_RECEIPT"

mutate_rendering_receipt() {
  local source="$1"
  local destination="$2"
  local mode="$3"
  python3 -I -S - "$source" "$destination" "$mode" <<'PY'
from pathlib import Path
import sys


source = Path(sys.argv[1])
destination = Path(sys.argv[2])
mode = sys.argv[3]
lines = source.read_text(encoding="utf-8").splitlines()
if mode == "leading-zero":
    fields = lines[5].split("\t")
    if fields[:2] != ["color", "1"]:
        raise SystemExit("leading-zero mutation target drifted")
    fields[1] = "01"
    lines[5] = "\t".join(fields)
elif mode == "row-order":
    lines[5], lines[6] = lines[6], lines[5]
elif mode == "digest-case":
    fields = lines[5].split("\t")
    if len(fields) != 10:
        raise SystemExit("digest mutation target drifted")
    fields[5] = fields[5].upper()
    lines[5] = "\t".join(fields)
elif mode == "gray-chroma":
    index = next(index for index, line in enumerate(lines) if line.startswith("gray\t1\t"))
    fields = lines[index].split("\t")
    if fields[-1] != "0":
        raise SystemExit("grayscale chroma mutation target drifted")
    fields[-1] = "1"
    lines[index] = "\t".join(fields)
elif mode == "pdf-digest":
    if not lines[1].startswith("pdf_sha256\t"):
        raise SystemExit("PDF digest mutation target drifted")
    lines[1] = f"pdf_sha256\t{'0' * 64}"
else:
    raise SystemExit(f"unknown rendering-receipt mutation: {mode}")
destination.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
PY
}

case_file="$TEST_ROOT/rendering-leading-zero.tsv"
mutate_rendering_receipt "$BASE_RENDERING_RECEIPT" "$case_file" leading-zero
expect_reject \
  "rendering receipt rejects noncanonical integers" \
  "generated rendering receipt has a noncanonical page" \
  run_rendering_receipt_validator "$case_file"

case_file="$TEST_ROOT/rendering-order.tsv"
mutate_rendering_receipt "$BASE_RENDERING_RECEIPT" "$case_file" row-order
expect_reject \
  "rendering receipt rejects row reordering" \
  "generated rendering receipt page order/inventory drifted" \
  run_rendering_receipt_validator "$case_file"

case_file="$TEST_ROOT/rendering-digest-case.tsv"
mutate_rendering_receipt "$BASE_RENDERING_RECEIPT" "$case_file" digest-case
expect_reject \
  "rendering receipt rejects noncanonical PNG digests" \
  "generated rendering receipt page 1 PNG digest is noncanonical" \
  run_rendering_receipt_validator "$case_file"

case_file="$TEST_ROOT/rendering-gray-chroma.tsv"
mutate_rendering_receipt "$BASE_RENDERING_RECEIPT" "$case_file" gray-chroma
expect_reject \
  "rendering receipt rejects grayscale chroma" \
  "generated rendering receipt page 1 grayscale chroma count is nonzero" \
  run_rendering_receipt_validator "$case_file"

case_file="$TEST_ROOT/rendering-pdf-digest.tsv"
mutate_rendering_receipt "$BASE_RENDERING_RECEIPT" "$case_file" pdf-digest
expect_reject \
  "rendering receipt rejects a stale PDF binding" \
  "generated rendering receipt PDF digest binding drifted" \
  run_rendering_receipt_validator "$case_file"

# Cross-toolchain navigation comparator.  These compact manifests isolate route identity, null
# status, annotation flags, and the inclusive two-point coordinate tolerance from PDF parsing.
make_navigation_fixture() {
  local directory="$1"
  mkdir -p "$directory"
  printf '%s\n' \
    $'schema\tpid-rs-workflow-navigation-manifest-v1' \
    $'outline\t0\t1\tHeading' \
    $'destination\tdest.1\t1\t/XYZ\t10\t100\tnull\tnull\tnull' \
    $'annotation\t1\t1\tURI\thttps://example.com\t20\t30\t40\t50\t0' \
    >"$directory/left.tsv"
  cp "$directory/left.tsv" "$directory/right.tsv"
}

run_navigation_comparator() {
  local directory="$1"
  python3 -I -S "$NAVIGATION_COMPARATOR" \
    "$directory/left.tsv" "$directory/right.tsv"
}

case_dir="$(mktemp -d "$TEST_ROOT/navigation-control.XXXXXX")"
make_navigation_fixture "$case_dir"
expect_accept \
  "cross-toolchain navigation accepts identical route and coordinate manifests" \
  run_navigation_comparator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/navigation-boundary.XXXXXX")"
make_navigation_fixture "$case_dir"
replace_once \
  "$case_dir/right.tsv" \
  $'destination\tdest.1\t1\t/XYZ\t10\t100\tnull\tnull\tnull' \
  $'destination\tdest.1\t1\t/XYZ\t12\t100\tnull\tnull\tnull'
expect_accept \
  "cross-toolchain navigation admits exactly the documented two-point coordinate boundary" \
  run_navigation_comparator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/navigation-over-boundary.XXXXXX")"
make_navigation_fixture "$case_dir"
replace_once \
  "$case_dir/right.tsv" \
  $'destination\tdest.1\t1\t/XYZ\t10\t100\tnull\tnull\tnull' \
  $'destination\tdest.1\t1\t/XYZ\t12.0001\t100\tnull\tnull\tnull'
expect_reject \
  "cross-toolchain navigation rejects movement above two points" \
  "coordinate moved by 2.0001 points" \
  run_navigation_comparator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/navigation-outline-route.XXXXXX")"
make_navigation_fixture "$case_dir"
replace_once \
  "$case_dir/right.tsv" \
  $'outline\t0\t1\tHeading' \
  $'outline\t0\t2\tHeading'
expect_reject \
  "cross-toolchain navigation rejects outline-page drift" \
  "outline route differs" \
  run_navigation_comparator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/navigation-null-status.XXXXXX")"
make_navigation_fixture "$case_dir"
replace_once \
  "$case_dir/right.tsv" \
  $'destination\tdest.1\t1\t/XYZ\t10\t100\tnull\tnull\tnull' \
  $'destination\tdest.1\t1\t/XYZ\t10\t100\t0\tnull\tnull'
expect_reject \
  "cross-toolchain navigation rejects null-coordinate status drift" \
  "null coordinate status differs" \
  run_navigation_comparator "$case_dir"

case_dir="$(mktemp -d "$TEST_ROOT/navigation-annotation-flags.XXXXXX")"
make_navigation_fixture "$case_dir"
replace_once \
  "$case_dir/right.tsv" \
  $'annotation\t1\t1\tURI\thttps://example.com\t20\t30\t40\t50\t0' \
  $'annotation\t1\t1\tURI\thttps://example.com\t20\t30\t40\t50\t2'
expect_reject \
  "cross-toolchain navigation rejects annotation-flag drift" \
  "annotation page/order/target/flags differ" \
  run_navigation_comparator "$case_dir"

# Reachable PDF active-content validator. Mutants retain the exact expected-page report as their clone
# source, so catalogue/page/deep-walk diagnostics cannot be credited to an unrelated tiny PDF.
run_report_validator() {
  local pdf="$1"
  local mode="$2"
  local manifest
  manifest="$TEST_ROOT/report-navigation-$(basename "$pdf").tsv"
  rm -f -- "$manifest"
  if ! python3 -I -S "$REPORT_VALIDATOR" \
      "$pdf" "$BASE_MARKDOWN" "$EXPECTED_PAGES" "$mode" "$manifest"; then
    return 1
  fi
  if [[ ! -s "$manifest" ]]; then
    fail "report validator did not produce its navigation manifest: $pdf"
  fi
}

expect_accept \
  "report validator accepts the exact copied publication PDF" \
  run_report_validator "$BASE_PDF" --exact

make_pdf_mutant() {
  local destination="$1"
  local mode="$2"
  python3 -I -S - "$BASE_PDF" "$destination" "$mode" <<'PY'
from pathlib import Path
import copy
import sys
import sysconfig


for package_root in dict.fromkeys(
    (sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))
):
    if package_root:
        sys.path.insert(0, package_root)

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NumberObject,
    TextStringObject,
)


source = Path(sys.argv[1])
destination = Path(sys.argv[2])
mode = sys.argv[3]
writer = PdfWriter(clone_from=source)
writer.pdf_header = "%PDF-1.7"
sentinel_action = DictionaryObject(
    {
        NameObject("/Type"): NameObject("/Action"),
        NameObject("/S"): NameObject("/JavaScript"),
        NameObject("/JS"): TextStringObject("inert hostile-mutation sentinel"),
    }
)
if mode == "catalog-open-action":
    writer.root_object[NameObject("/OpenAction")] = sentinel_action
elif mode == "catalog-legacy-dests":
    writer.root_object[NameObject("/Dests")] = DictionaryObject()
elif mode == "page-additional-actions":
    writer.pages[0][NameObject("/AA")] = DictionaryObject(
        {NameObject("/O"): sentinel_action}
    )
elif mode == "nested-javascript-key":
    writer.root_object[NameObject("/PidRsSelfTest")] = DictionaryObject(
        {NameObject("/JavaScript"): TextStringObject("inert hostile-mutation sentinel")}
    )
elif mode == "nested-action-object":
    writer.root_object[NameObject("/PidRsSelfTest")] = sentinel_action
elif mode == "nested-launch-action":
    writer.root_object[NameObject("/PidRsSelfTest")] = DictionaryObject(
        {
            NameObject("/S"): NameObject("/Launch"),
            NameObject("/F"): TextStringObject("/tmp/inert-self-test"),
        }
    )
elif mode == "page-presentation-launch":
    writer.pages[0][NameObject("/PresSteps")] = DictionaryObject(
        {
            NameObject("/NA"): DictionaryObject(
                {
                    NameObject("/S"): NameObject("/Launch"),
                    NameObject("/F"): TextStringObject("/tmp/inert-self-test"),
                }
            )
        }
    )
elif mode == "page-cropbox":
    writer.pages[0][NameObject("/CropBox")] = ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)]
    )
elif mode == "page-artbox":
    writer.pages[0][NameObject("/ArtBox")] = ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)]
    )
elif mode == "page-user-unit":
    writer.pages[0][NameObject("/UserUnit")] = NumberObject(2)
elif mode == "page-media-origin":
    shifted_box = ArrayObject(
        [
            FloatObject("1"),
            FloatObject("1"),
            FloatObject("596.276"),
            FloatObject("842.89"),
        ]
    )
    for box_name in ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox"):
        writer.pages[0][NameObject(box_name)] = copy.deepcopy(shifted_box)
elif mode == "misdirect-outline":
    def resolve(value):
        return value.get_object() if isinstance(value, IndirectObject) else value

    def mutate_outline(node) -> bool:
        while node is not None:
            outline_item = resolve(node)
            if str(outline_item.get("/Title")) == "1.5 PID vocabulary and a finite worked reconstruction":
                action = resolve(outline_item.get("/A"))
                if str(action.get("/S")) != "/GoTo":
                    raise SystemExit("outline mutation action target drifted")
                action[NameObject("/D")] = TextStringObject("page.1")
                return True
            first = outline_item.get("/First")
            if first is not None and mutate_outline(first):
                return True
            node = outline_item.get("/Next")
        return False

    outlines = resolve(writer.root_object.get("/Outlines"))
    if outlines is None or not mutate_outline(outlines.get("/First")):
        raise SystemExit("outline mutation title target drifted")
elif mode == "misdirect-named-destination":
    def resolve(value):
        return value.get_object() if isinstance(value, IndirectObject) else value

    def mutate_destination_tree(node) -> bool:
        node = resolve(node)
        names = resolve(node.get("/Names", []))
        for index in range(0, len(names), 2):
            if str(names[index]) == "AMS.10":
                destination = resolve(names[index + 1])
                destination_array = resolve(destination.get("/D"))
                destination_array[0] = writer.pages[0].indirect_reference
                return True
        for child in resolve(node.get("/Kids", [])):
            if mutate_destination_tree(child):
                return True
        return False

    names_root = resolve(writer.root_object.get("/Names"))
    destinations = resolve(names_root.get("/Dests")) if names_root is not None else None
    if destinations is None or not mutate_destination_tree(destinations):
        raise SystemExit("named-destination mutation target drifted")
elif mode in {"duplicate-named-destination", "conflicting-duplicate-named-destination"}:
    def resolve(value):
        return value.get_object() if isinstance(value, IndirectObject) else value

    def mutate_destination_tree(node) -> bool:
        node = resolve(node)
        names = resolve(node.get("/Names", ArrayObject()))
        if names:
            if str(names[0]) != "AMS.10":
                raise SystemExit("duplicate named-destination first-key target drifted")
            duplicate_value = copy.deepcopy(names[1])
            if mode == "conflicting-duplicate-named-destination":
                duplicate_dictionary = resolve(duplicate_value)
                destination_array = resolve(duplicate_dictionary.get("/D"))
                destination_array[0] = writer.pages[0].indirect_reference
            names.insert(0, duplicate_value)
            names.insert(0, TextStringObject("AMS.10"))
            return True
        for child in resolve(node.get("/Kids", ArrayObject())):
            if mutate_destination_tree(child):
                return True
        return False

    names_root = resolve(writer.root_object.get("/Names"))
    destinations = resolve(names_root.get("/Dests")) if names_root is not None else None
    if destinations is None or not mutate_destination_tree(destinations):
        raise SystemExit("duplicate named-destination mutation target drifted")
elif mode == "misdirect-named-coordinate":
    def resolve(value):
        return value.get_object() if isinstance(value, IndirectObject) else value

    def mutate_destination_tree(node) -> bool:
        node = resolve(node)
        names = resolve(node.get("/Names", []))
        for index in range(0, len(names), 2):
            if str(names[index]) == "AMS.10":
                destination = resolve(names[index + 1])
                destination_array = resolve(destination.get("/D"))
                destination_array[3] = FloatObject("100")
                return True
        for child in resolve(node.get("/Kids", [])):
            if mutate_destination_tree(child):
                return True
        return False

    names_root = resolve(writer.root_object.get("/Names"))
    destinations = resolve(names_root.get("/Dests")) if names_root is not None else None
    if destinations is None or not mutate_destination_tree(destinations):
        raise SystemExit("named-coordinate mutation target drifted")
elif mode == "link-unknown-uri":
    def resolve(value):
        return value.get_object() if isinstance(value, IndirectObject) else value

    mutated = False
    for page in writer.pages:
        for annotation_reference in resolve(page.get("/Annots", [])):
            annotation = resolve(annotation_reference)
            action = resolve(annotation.get("/A"))
            if not isinstance(action, DictionaryObject) or str(action.get("/S")) != "/URI":
                continue
            action[NameObject("/URI")] = TextStringObject(
                "https://example.invalid/undeclared-workflow-source"
            )
            mutated = True
            break
        if mutated:
            break
    if not mutated:
        raise SystemExit("unknown-URI mutation target drifted")
elif mode in {
    "dangling-goto",
    "link-rectangle-outside",
    "link-rectangle-zero-width",
    "link-rectangle-subpoint",
    "link-quadpoints",
    "link-hidden-flag",
    "link-no-view-flag",
}:
    def resolve(value):
        return value.get_object() if isinstance(value, IndirectObject) else value

    mutated = False
    for page in writer.pages:
        for annotation_reference in resolve(page.get("/Annots", [])):
            annotation = resolve(annotation_reference)
            action = resolve(annotation.get("/A"))
            if not isinstance(action, DictionaryObject):
                continue
            if str(action.get("/S")) != "/GoTo":
                continue
            if mode == "dangling-goto":
                action[NameObject("/D")] = TextStringObject("pid-rs.absent-destination")
            elif mode == "link-rectangle-outside":
                rectangle = resolve(annotation.get("/Rect"))
                rectangle[0] = NumberObject(-1)
            elif mode == "link-rectangle-zero-width":
                rectangle = resolve(annotation.get("/Rect"))
                rectangle[2] = rectangle[0]
            elif mode == "link-rectangle-subpoint":
                rectangle = resolve(annotation.get("/Rect"))
                rectangle[2] = FloatObject(float(rectangle[0]) + 0.5)
            elif mode == "link-quadpoints":
                rectangle = resolve(annotation.get("/Rect"))
                x_min, y_min, x_max, y_max = map(float, rectangle)
                annotation[NameObject("/QuadPoints")] = ArrayObject(
                    [
                        FloatObject(x_min),
                        FloatObject(y_max),
                        FloatObject(x_max),
                        FloatObject(y_max),
                        FloatObject(x_min),
                        FloatObject(y_min),
                        FloatObject(x_max),
                        FloatObject(y_min),
                    ]
                )
            elif mode == "link-hidden-flag":
                annotation[NameObject("/F")] = NumberObject(2)
            else:
                annotation[NameObject("/F")] = NumberObject(32)
            mutated = True
            break
        if mutated:
            break
    if not mutated:
        raise SystemExit(f"link mutation target drifted: {mode}")
else:
    raise SystemExit(f"unknown PDF mutation: {mode}")
with destination.open("xb") as stream:
    writer.write(stream)
PY
}

case_file="$TEST_ROOT/report-open-action.pdf"
make_pdf_mutant "$case_file" catalog-open-action
expect_reject \
  "report PDF rejects a catalog OpenAction" \
  "report PDF catalog contains forbidden active/associated content: /OpenAction" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-legacy-dests.pdf"
make_pdf_mutant "$case_file" catalog-legacy-dests
expect_reject \
  "report PDF rejects a competing legacy catalog destination dictionary" \
  "report PDF catalog contains a competing legacy /Dests dictionary" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-page-aa.pdf"
make_pdf_mutant "$case_file" page-additional-actions
expect_reject \
  "report PDF rejects page additional actions" \
  "report PDF page 1 has additional actions or associated files" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-page-cropbox.pdf"
make_pdf_mutant "$case_file" page-cropbox
expect_reject \
  "report PDF rejects a viewer-visible CropBox that clips the MediaBox" \
  "report PDF page 1 CropBox differs from its MediaBox" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-page-artbox.pdf"
make_pdf_mutant "$case_file" page-artbox
expect_reject \
  "report PDF rejects an ArtBox that differs from the MediaBox" \
  "report PDF page 1 ArtBox differs from its MediaBox" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-page-user-unit.pdf"
make_pdf_mutant "$case_file" page-user-unit
expect_reject \
  "report PDF rejects a non-unit page UserUnit" \
  "report PDF page 1 UserUnit differs from 1" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-page-media-origin.pdf"
make_pdf_mutant "$case_file" page-media-origin
expect_reject \
  "report PDF rejects a nonzero MediaBox origin even when every page box agrees" \
  "report PDF page 1 MediaBox origin differs from zero" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-nested-js.pdf"
make_pdf_mutant "$case_file" nested-javascript-key
expect_reject \
  "report PDF deep walk rejects a reachable JavaScript key" \
  "report PDF reachable object contains forbidden active keys" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-nested-action.pdf"
make_pdf_mutant "$case_file" nested-action-object
expect_reject \
  "report PDF deep walk rejects a reachable explicit action object" \
  "report PDF reachable object contains an action outside an authorized /A edge" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-nested-launch.pdf"
make_pdf_mutant "$case_file" nested-launch-action
expect_reject \
  "report PDF deep walk rejects an untyped launch action outside /A" \
  "report PDF reachable object contains an action outside an authorized /A edge" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-presentation-launch.pdf"
make_pdf_mutant "$case_file" page-presentation-launch
expect_reject \
  "report PDF deep walk rejects presentation-step action containers" \
  "report PDF reachable object contains forbidden active keys" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-misdirect-outline.pdf"
make_pdf_mutant "$case_file" misdirect-outline
expect_reject \
  "report PDF rejects an outline redirect to a TOC page that repeats its title" \
  "report PDF outline title/depth/target manifest drifted" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-misdirect-named-destination.pdf"
make_pdf_mutant "$case_file" misdirect-named-destination
expect_reject \
  "cross-toolchain report validation rejects same-inventory named-destination page drift" \
  "report PDF named-destination name/page/type manifest drifted" \
  run_report_validator "$case_file" --cross-toolchain

case_file="$TEST_ROOT/report-misdirect-named-coordinate.pdf"
make_pdf_mutant "$case_file" misdirect-named-coordinate
expect_reject \
  "report PDF rejects same-page named-destination coordinate drift" \
  "report PDF exact named-destination manifest drifted" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-duplicate-named-destination.pdf"
make_pdf_mutant "$case_file" duplicate-named-destination
expect_reject \
  "report PDF rejects a same-value duplicate in the raw destination name tree" \
  "report PDF raw destination name-tree keys are not strictly increasing" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-conflicting-duplicate-named-destination.pdf"
make_pdf_mutant "$case_file" conflicting-duplicate-named-destination
expect_reject \
  "report PDF rejects a conflicting duplicate in the raw destination name tree" \
  "report PDF raw destination name-tree keys are not strictly increasing" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-dangling-goto.pdf"
make_pdf_mutant "$case_file" dangling-goto
expect_reject \
  "report PDF rejects a dangling internal GoTo consumer" \
  "refers to an absent named destination" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-unknown-uri.pdf"
make_pdf_mutant "$case_file" link-unknown-uri
expect_reject \
  "report PDF rejects a rendered HTTPS URI absent from the canonical source" \
  "unknown_rendered_uris=['https://example.invalid/undeclared-workflow-source']" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-rectangle-outside.pdf"
make_pdf_mutant "$case_file" link-rectangle-outside
expect_reject \
  "report PDF rejects a link rectangle outside its page" \
  "link rectangle lies outside its page" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-rectangle-zero-width.pdf"
make_pdf_mutant "$case_file" link-rectangle-zero-width
expect_reject \
  "report PDF rejects a zero-width link rectangle" \
  "link rectangle has a zero or sub-point extent" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-rectangle-subpoint.pdf"
make_pdf_mutant "$case_file" link-rectangle-subpoint
expect_reject \
  "report PDF rejects a positive but sub-point link rectangle" \
  "link rectangle has a zero or sub-point extent" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-quadpoints.pdf"
make_pdf_mutant "$case_file" link-quadpoints
expect_reject \
  "report PDF rejects unreviewed alternate link QuadPoints geometry" \
  "link has unreviewed QuadPoints geometry" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-hidden-flag.pdf"
make_pdf_mutant "$case_file" link-hidden-flag
expect_reject \
  "report PDF rejects a Hidden annotation flag" \
  "link has noncanonical annotation flags: 2" \
  run_report_validator "$case_file" --exact

case_file="$TEST_ROOT/report-link-no-view-flag.pdf"
make_pdf_mutant "$case_file" link-no-view-flag
expect_reject \
  "report PDF rejects a NoView annotation flag" \
  "link has noncanonical annotation flags: 32" \
  run_report_validator "$case_file" --exact

c3_control_count=$((
  C3_BOUNDED_PROBE_COUNT
  + C3_ENTRY_WRAPPER_COUNT
  + C3_RUNTIME_MAP_COUNT
  + C3_FLS_MAP_PATH_COUNT
  + C3_EXECUTABLE_CUSTODY_COUNT
  + C3_FORMAT_CUSTODY_COUNT
))
predecessor_control_count=$((PASS_COUNT - c3_control_count))
if [[ "$C3_ACTIVE_FAMILY" != "" \
    || "$C3_BOUNDED_PROBE_COUNT" -ne "$EXPECTED_C3_BOUNDED_PROBE_COUNT" \
    || "$C3_ENTRY_WRAPPER_COUNT" -ne "$EXPECTED_C3_ENTRY_WRAPPER_COUNT" \
    || "$C3_RUNTIME_MAP_COUNT" -ne "$EXPECTED_C3_RUNTIME_MAP_COUNT" \
    || "$C3_FLS_MAP_PATH_COUNT" -ne "$EXPECTED_C3_FLS_MAP_PATH_COUNT" \
    || "$C3_EXECUTABLE_CUSTODY_COUNT" -ne "$EXPECTED_C3_EXECUTABLE_CUSTODY_COUNT" \
    || "$C3_FORMAT_CUSTODY_COUNT" -ne "$EXPECTED_C3_FORMAT_CUSTODY_COUNT" \
    || "$predecessor_control_count" -ne "$EXPECTED_PREDECESSOR_CONTROL_COUNT" \
    || "$PASS_COUNT" -ne "$EXPECTED_TOTAL_CONTROL_COUNT" ]]; then
  fail "frozen control-family partition drifted: predecessor=$predecessor_control_count, bounded-probe=$C3_BOUNDED_PROBE_COUNT, entry-wrapper=$C3_ENTRY_WRAPPER_COUNT, runtime-map=$C3_RUNTIME_MAP_COUNT, fls-map-path=$C3_FLS_MAP_PATH_COUNT, executable-custody=$C3_EXECUTABLE_CUSTODY_COUNT, format-custody=$C3_FORMAT_CUSTODY_COUNT, total=$PASS_COUNT"
fi

printf 'OK: %d bounded workflow-PDF checker controls/mutations passed; frozen families predecessor=%d, bounded-probe=%d, entry-wrapper=%d, runtime-map=%d, fls-map-path=%d, executable-custody=%d, format-custody=%d; no report compilation was performed\n' \
  "$PASS_COUNT" \
  "$predecessor_control_count" \
  "$C3_BOUNDED_PROBE_COUNT" \
  "$C3_ENTRY_WRAPPER_COUNT" \
  "$C3_RUNTIME_MAP_COUNT" \
  "$C3_FLS_MAP_PATH_COUNT" \
  "$C3_EXECUTABLE_CUSTODY_COUNT" \
  "$C3_FORMAT_CUSTODY_COUNT"
