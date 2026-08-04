#!/usr/bin/env python3
"""Hostile focused tests for sync-mathematical-workflow-tex.py."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Callable, ContextManager
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().with_name("sync-mathematical-workflow-tex.py")
MODULE_NAME = "_pid_rs_mathematical_workflow_sync_under_test"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load {SCRIPT}")
SYNC = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = SYNC
SPEC.loader.exec_module(SYNC)


class Fixture:
    markdown_bytes = b"# Canonical workflow\n\nExact body.\n"
    stale_tex_bytes = (
        b"\\documentclass{article}\n"
        b"framing before\n"
        + SYNC.BEGIN
        + b"stale body\n"
        + SYNC.END
        + b"\nframing after\n"
    )

    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="pid-rs-workflow-sync-self-test-"
        )
        self.root = Path(self.temporary.name)
        self.markdown = self.root / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
        self.tex = self.root / "audit/formal/latex/mathematical-problem-solving-workflow.tex"
        self.tex.parent.mkdir(parents=True)
        self.write_regular(self.markdown, self.markdown_bytes)
        self.write_regular(self.tex, self.stale_tex_bytes)

    @staticmethod
    def write_regular(path: Path, data: bytes) -> None:
        path.write_bytes(data)
        path.chmod(SYNC.CANONICAL_DATA_MODE)

    @property
    def expected_tex_bytes(self) -> bytes:
        return SYNC.synchronized_bytes(self.markdown_bytes, self.stale_tex_bytes)

    def invoke(self, argument: str) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.object(sys, "argv", [str(SCRIPT), argument]):
            with redirect_stdout(output), redirect_stderr(output):
                result = SYNC.main()
        return result, output.getvalue()

    def temporary_outputs(self) -> list[Path]:
        return sorted(self.tex.parent.glob(f".{self.tex.name}.tmp-*"))

    def close(self) -> None:
        self.temporary.cleanup()


class SynchronizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        patches = (
            mock.patch.object(SYNC, "ROOT", self.fixture.root),
            mock.patch.object(SYNC, "MARKDOWN", self.fixture.markdown),
            mock.patch.object(SYNC, "TEX", self.fixture.tex),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def attack_before_snapshot_check(
        self,
        label: str,
        attack: Callable[[], None],
    ) -> ContextManager[object]:
        original = SYNC._assert_snapshot_unchanged
        fired = False

        def wrapper(
            directory_descriptor: int,
            name: str,
            baseline: object,
            current_label: str,
        ) -> object:
            nonlocal fired
            if not fired and current_label == label:
                fired = True
                attack()
            return original(directory_descriptor, name, baseline, current_label)

        return mock.patch.object(SYNC, "_assert_snapshot_unchanged", new=wrapper)

    def test_exact_embedding_deterministic_mode_and_idempotence(self) -> None:
        previous_umask = os.umask(0o077)
        try:
            result, output = self.fixture.invoke("--write")
        finally:
            os.umask(previous_umask)
        self.assertEqual(result, 0)
        self.assertIn("UPDATED:", output)
        self.assertEqual(self.fixture.tex.read_bytes(), self.fixture.expected_tex_bytes)
        self.assertEqual(
            stat.S_IMODE(self.fixture.tex.stat().st_mode),
            SYNC.CANONICAL_DATA_MODE,
        )
        before = self.fixture.tex.stat()
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )

        result, output = self.fixture.invoke("--write")
        after = self.fixture.tex.stat()
        self.assertEqual(result, 0)
        self.assertIn("OK:", output)
        self.assertEqual(
            identity_before,
            (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ),
        )
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_check_accepts_exact_and_rejects_stale_without_writing(self) -> None:
        stale_identity = self.fixture.tex.stat()
        with self.assertRaisesRegex(RuntimeError, "stale"):
            self.fixture.invoke("--check")
        after_stale_check = self.fixture.tex.stat()
        self.assertEqual(self.fixture.tex.read_bytes(), self.fixture.stale_tex_bytes)
        self.assertEqual(stale_identity.st_ino, after_stale_check.st_ino)

        self.assertEqual(self.fixture.invoke("--write")[0], 0)
        exact_identity = self.fixture.tex.stat()
        result, output = self.fixture.invoke("--check")
        self.assertEqual(result, 0)
        self.assertIn("OK:", output)
        self.assertEqual(exact_identity.st_ino, self.fixture.tex.stat().st_ino)

    def test_malformed_sentinels_fail_closed(self) -> None:
        valid_body = SYNC.BEGIN + b"body\n" + SYNC.END
        malformed = (
            b"no enclosure\n",
            SYNC.BEGIN + b"body\n",
            b"body\n" + SYNC.END,
            SYNC.BEGIN + valid_body + SYNC.END,
            SYNC.END + b"body\n" + SYNC.BEGIN,
            SYNC.BEGIN_TOKEN + b"body without required line break" + SYNC.END,
            SYNC.BEGIN + b"body\n" + SYNC.END + b"\n" + SYNC.BEGIN_TOKEN,
        )
        for tex in malformed:
            with self.subTest(tex=tex):
                with self.assertRaises(RuntimeError):
                    SYNC.synchronized_bytes(self.fixture.markdown_bytes, tex)
        with self.assertRaisesRegex(RuntimeError, "reserved"):
            SYNC.synchronized_bytes(
                self.fixture.markdown_bytes + SYNC.END + b"\n",
                valid_body,
            )

    def test_hostile_destination_symlink_replacement_is_rejected(self) -> None:
        victim = self.fixture.root / "victim.tex"
        Fixture.write_regular(victim, b"must remain untouched\n")

        def attack() -> None:
            self.fixture.tex.unlink()
            self.fixture.tex.symlink_to(victim)

        with self.attack_before_snapshot_check("TeX destination", attack):
            with self.assertRaises((OSError, RuntimeError)):
                self.fixture.invoke("--write")
        self.assertTrue(self.fixture.tex.is_symlink())
        self.assertEqual(victim.read_bytes(), b"must remain untouched\n")
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_source_same_byte_identity_replacement_is_rejected(self) -> None:
        original_destination = self.fixture.tex.read_bytes()

        def attack() -> None:
            replacement = self.fixture.root / "replacement-source"
            Fixture.write_regular(replacement, self.fixture.markdown_bytes)
            os.replace(replacement, self.fixture.markdown)

        with self.attack_before_snapshot_check("Markdown source", attack):
            with self.assertRaisesRegex(RuntimeError, "identity or bytes changed"):
                self.fixture.invoke("--write")
        self.assertEqual(self.fixture.tex.read_bytes(), original_destination)
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_destination_same_byte_identity_replacement_is_rejected(self) -> None:
        original_destination = self.fixture.tex.read_bytes()

        def attack() -> None:
            replacement = self.fixture.tex.parent / "replacement-destination"
            Fixture.write_regular(replacement, original_destination)
            os.replace(replacement, self.fixture.tex)

        with self.attack_before_snapshot_check("TeX destination", attack):
            with self.assertRaisesRegex(RuntimeError, "identity or bytes changed"):
                self.fixture.invoke("--write")
        self.assertEqual(self.fixture.tex.read_bytes(), original_destination)
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_hardlinked_source_and_destination_are_rejected(self) -> None:
        for target, data in (
            (self.fixture.markdown, self.fixture.markdown_bytes),
            (self.fixture.tex, self.fixture.stale_tex_bytes),
        ):
            with self.subTest(target=target.name):
                peer = target.with_name(f"{target.name}.peer")
                Fixture.write_regular(peer, data)
                target.unlink()
                os.link(peer, target)
                with self.assertRaisesRegex(RuntimeError, "single-link regular"):
                    self.fixture.invoke("--check")
                target.unlink()
                peer.unlink()
                Fixture.write_regular(target, data)

    def test_post_exchange_corruption_is_caught_and_rolled_back(self) -> None:
        real_exchange = SYNC._atomic_exchange_at
        fired = False

        def corrupting_exchange(
            directory_descriptor: int,
            source: str,
            destination: str,
        ) -> None:
            nonlocal fired
            real_exchange(directory_descriptor, source, destination)
            if fired:
                return
            fired = True
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_TRUNC,
                dir_fd=directory_descriptor,
            )
            try:
                os.write(descriptor, b"hostile post-exchange corruption\n")
            finally:
                os.close(descriptor)

        with mock.patch.object(SYNC, "_atomic_exchange_at", new=corrupting_exchange):
            with self.assertRaisesRegex(RuntimeError, "read-back"):
                self.fixture.invoke("--write")
        self.assertEqual(self.fixture.tex.read_bytes(), self.fixture.stale_tex_bytes)
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_post_exchange_type_change_preserves_concurrent_path_and_recovery(self) -> None:
        real_exchange = SYNC._atomic_exchange_at
        fired = False
        target = "concurrent-post-exchange-target"

        def replacing_exchange(
            directory_descriptor: int,
            source: str,
            destination: str,
        ) -> None:
            nonlocal fired
            real_exchange(directory_descriptor, source, destination)
            if not fired:
                fired = True
                self.fixture.tex.unlink()
                self.fixture.tex.symlink_to(target)

        with mock.patch.object(SYNC, "_atomic_exchange_at", new=replacing_exchange):
            with self.assertRaisesRegex(RuntimeError, "rollback failed"):
                self.fixture.invoke("--write")
        self.assertTrue(self.fixture.tex.is_symlink())
        self.assertEqual(os.readlink(self.fixture.tex), target)
        recovery = self.fixture.temporary_outputs()
        self.assertEqual(len(recovery), 1)
        self.assertEqual(recovery[0].read_bytes(), self.fixture.stale_tex_bytes)

    def test_final_compare_and_swap_race_preserves_concurrent_destination(self) -> None:
        real_exchange = SYNC._atomic_exchange_at
        fired = False
        concurrent = b"concurrent destination wins the race\n"

        def racing_exchange(
            directory_descriptor: int,
            source: str,
            destination: str,
        ) -> None:
            nonlocal fired
            if not fired:
                fired = True
                replacement = self.fixture.tex.parent / "concurrent-destination"
                Fixture.write_regular(replacement, concurrent)
                os.replace(replacement, self.fixture.tex)
            real_exchange(directory_descriptor, source, destination)

        with mock.patch.object(SYNC, "_atomic_exchange_at", new=racing_exchange):
            with self.assertRaisesRegex(RuntimeError, "compare-and-swap window"):
                self.fixture.invoke("--write")
        self.assertEqual(self.fixture.tex.read_bytes(), concurrent)
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_final_compare_and_swap_race_restores_concurrent_symlink(self) -> None:
        real_exchange = SYNC._atomic_exchange_at
        fired = False
        target = "concurrent-symlink-target"

        def racing_exchange(
            directory_descriptor: int,
            source: str,
            destination: str,
        ) -> None:
            nonlocal fired
            if not fired:
                fired = True
                self.fixture.tex.unlink()
                self.fixture.tex.symlink_to(target)
            real_exchange(directory_descriptor, source, destination)

        with mock.patch.object(SYNC, "_atomic_exchange_at", new=racing_exchange):
            with self.assertRaisesRegex(RuntimeError, "compare-and-swap window"):
                self.fixture.invoke("--write")
        self.assertTrue(self.fixture.tex.is_symlink())
        self.assertEqual(os.readlink(self.fixture.tex), target)
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_final_compare_and_swap_race_restores_concurrent_hardlink(self) -> None:
        real_exchange = SYNC._atomic_exchange_at
        fired = False
        concurrent = b"concurrent hard-link destination wins the race\n"
        peer = self.fixture.tex.parent / "concurrent-hardlink-peer"

        def racing_exchange(
            directory_descriptor: int,
            source: str,
            destination: str,
        ) -> None:
            nonlocal fired
            if not fired:
                fired = True
                Fixture.write_regular(peer, concurrent)
                self.fixture.tex.unlink()
                os.link(peer, self.fixture.tex)
            real_exchange(directory_descriptor, source, destination)

        with mock.patch.object(SYNC, "_atomic_exchange_at", new=racing_exchange):
            with self.assertRaisesRegex(RuntimeError, "compare-and-swap window"):
                self.fixture.invoke("--write")
        destination_status = self.fixture.tex.stat()
        peer_status = peer.stat()
        self.assertEqual(self.fixture.tex.read_bytes(), concurrent)
        self.assertEqual(
            (destination_status.st_dev, destination_status.st_ino),
            (peer_status.st_dev, peer_status.st_ino),
        )
        self.assertEqual(destination_status.st_nlink, 2)
        self.assertEqual(self.fixture.temporary_outputs(), [])

    def test_file_and_parent_directory_are_fsynced(self) -> None:
        real_fsync = os.fsync
        synced_types: list[int] = []

        def recording_fsync(descriptor: int) -> None:
            synced_types.append(os.fstat(descriptor).st_mode)
            real_fsync(descriptor)

        with mock.patch.object(SYNC.os, "fsync", new=recording_fsync):
            self.assertEqual(self.fixture.invoke("--write")[0], 0)
        self.assertTrue(any(stat.S_ISREG(mode) for mode in synced_types))
        self.assertTrue(any(stat.S_ISDIR(mode) for mode in synced_types))


if __name__ == "__main__":
    unittest.main(verbosity=2)
