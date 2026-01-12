from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given

from rsync_wrapper import RsyncCommandBuilder, RsyncRunner, SyncOptions


@dataclass
class FakeProcess:
    stdout_lines: list[str]
    returncode: int = 0

    def __post_init__(self) -> None:
        self.stdout = iter(self.stdout_lines)
        self.stderr = iter([])
        self.terminated = False
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9


def path_segment_strategy():
    return st.text(alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz0123456789_-")), min_size=1, max_size=12)


@given(
    sources=st.lists(path_segment_strategy(), min_size=1, max_size=4, unique=True),
    destination=path_segment_strategy(),
    preserve_permissions=st.booleans(),
    preserve_timestamps=st.booleans(),
    include_hidden=st.booleans(),
    follow_symlinks=st.booleans(),
    handle_existing=st.sampled_from(["overwrite", "skip", "update"]),
    dry_run=st.booleans(),
)
def test_rsync_command_construction(
    sources,
    destination,
    preserve_permissions,
    preserve_timestamps,
    include_hidden,
    follow_symlinks,
    handle_existing,
    dry_run,
):
    """
    Feature: rsync-quick-action, Property 5: Rsync command construction
    """
    builder = RsyncCommandBuilder()
    options = SyncOptions(
        preserve_permissions=preserve_permissions,
        preserve_timestamps=preserve_timestamps,
        include_hidden_files=include_hidden,
        handle_existing_files=handle_existing,
        follow_symlinks=follow_symlinks,
        dry_run=dry_run,
    )

    source_paths = [Path("/src") / s for s in sources]
    dest_path = Path("/dest") / destination
    command = builder.build(source_paths, dest_path, options)

    assert command[0] == "rsync"
    assert command[-1] == str(dest_path)
    assert "--" in command
    separator_index = command.index("--")
    assert command[separator_index + 1 : -1] == [str(path) for path in source_paths]

    assert ("-p" in command) == preserve_permissions
    assert ("-t" in command) == preserve_timestamps
    assert ("-L" in command) == follow_symlinks
    assert ("-l" in command) == (not follow_symlinks)

    assert ("--ignore-existing" in command) == (handle_existing == "skip")
    assert ("--update" in command) == (handle_existing == "update")
    assert ("--exclude=.*" in command) == (not include_hidden)
    assert ("--dry-run" in command) == dry_run


@given(cancel_before_start=st.booleans())
def test_cancellation_safety(cancel_before_start: bool):
    """
    Feature: rsync-quick-action, Property 7: Cancellation safety
    """
    process = FakeProcess(stdout_lines=["0% 0/1", "50% 1/2", "100% 2/2"])

    def fake_popen(*args, **kwargs):
        return process

    runner = RsyncRunner(popen_factory=fake_popen)
    cancel_event = threading.Event()

    if cancel_before_start:
        cancel_event.set()
        result = runner.run(["rsync", "--progress"], cancel_event=cancel_event)
    else:
        def on_progress(_progress: dict) -> None:
            cancel_event.set()

        result = runner.run(["rsync", "--progress"], cancel_event=cancel_event, on_progress=on_progress)

    assert result.cancelled
    assert process.terminated or process.killed
