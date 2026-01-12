from __future__ import annotations

import os
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given

from drive_detection import DriveDetector, validate_destination


DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])


@dataclass(frozen=True)
class FakeVolume:
    name: str
    is_mount: bool
    writable: bool
    total: int
    free: int
    volume_type: str
    is_removable: bool
    is_system: bool


class FakeFS:
    def __init__(self, volumes: list[FakeVolume]) -> None:
        self.volumes = {Path("/Volumes") / vol.name: vol for vol in volumes}

    def listdir(self, root: Path) -> list[str]:
        return [path.name for path in self.volumes.keys()]

    def is_mount(self, path: Path) -> bool:
        volume = self.volumes.get(path)
        return volume.is_mount if volume else False

    def access(self, path: Path, mode: int) -> bool:
        volume = self.volumes.get(path)
        return volume.writable if volume and mode == os.W_OK else False

    def disk_usage(self, path: Path) -> DiskUsage:
        volume = self.volumes[path]
        used = max(volume.total - volume.free, 0)
        return DiskUsage(volume.total, used, volume.free)

    def metadata(self, path: Path) -> tuple[str, bool]:
        volume = self.volumes.get(path)
        if volume is None:
            return "unknown", False
        return volume.volume_type, volume.is_removable

    def get_volume(self, path: Path) -> FakeVolume:
        return self.volumes[path]


def _volume_strategy():
    @st.composite
    def _builder(draw):
        total = draw(st.integers(min_value=1, max_value=10**9))
        free = draw(st.integers(min_value=0, max_value=total))
        is_system = draw(st.booleans())
        name = draw(
            st.sampled_from(["Macintosh HD", "System", "Data"])
            if is_system
            else st.text(alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz0123456789_-")), min_size=1, max_size=12)
        )
        return FakeVolume(
            name=name,
            is_mount=draw(st.booleans()),
            writable=draw(st.booleans()),
            total=total,
            free=free,
            volume_type=draw(st.sampled_from(["apfs", "exfat", "ntfs", "unknown"])),
            is_removable=draw(st.booleans()),
            is_system=is_system,
        )

    return _builder()


@given(st.lists(_volume_strategy(), min_size=1, max_size=8, unique_by=lambda v: v.name.lower()))
def test_drive_enumeration_accuracy(volumes: list[FakeVolume]):
    """
    Feature: rsync-quick-action, Property 3: Drive enumeration accuracy
    """
    fs = FakeFS(volumes)
    detector = DriveDetector(
        volume_root=Path("/Volumes"),
        listdir=fs.listdir,
        disk_usage=fs.disk_usage,
        is_mount=fs.is_mount,
        access=fs.access,
        metadata_provider=fs.metadata,
        system_drive_names=("macintosh hd", "system", "data"),
    )

    drives = detector.enumerate_drives()
    expected = [
        vol
        for vol in volumes
        if vol.is_mount and vol.writable and not vol.is_system and not vol.name.startswith(".")
    ]

    assert {drive.name for drive in drives} == {vol.name for vol in expected}
    for drive in drives:
        volume = fs.get_volume(drive.path)
        assert drive.free_space == volume.free
        assert drive.total_space == volume.total
        assert drive.volume_type == volume.volume_type
        assert drive.is_removable == volume.is_removable
        assert drive.is_writable


@given(
    path_segment=st.text(alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz0123456789_-")), min_size=1, max_size=12),
    writable=st.booleans(),
    parent_writable=st.booleans(),
)
def test_permission_validation(path_segment: str, writable: bool, parent_writable: bool):
    """
    Feature: rsync-quick-action, Property 4: Permission validation
    """
    target = Path("/Volumes") / path_segment
    permissions = {
        target: writable,
        target.parent: parent_writable,
    }

    def fake_access(path: Path, mode: int) -> bool:
        return permissions.get(path, False) if mode == os.W_OK else False

    result = validate_destination(target, access=fake_access)
    expected_allowed = writable or parent_writable
    assert result.allowed == expected_allowed
    if not expected_allowed:
        assert "No write permission" in (result.reason or "")
