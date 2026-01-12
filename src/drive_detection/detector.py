from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Tuple

import psutil


@dataclass(frozen=True)
class MountedDrive:
    name: str
    path: Path
    total_space: int
    free_space: int
    volume_type: str
    is_writable: bool
    is_removable: bool


class DriveDetector:
    def __init__(
        self,
        volume_root: Path | str = Path("/Volumes"),
        listdir: Callable[[Path], Iterable[str]] = os.listdir,
        disk_usage: Callable[[Path], os.stat_result | os.statvfs_result | shutil._ntuple_diskusage] = shutil.disk_usage,
        is_mount: Callable[[Path], bool] = os.path.ismount,
        access: Callable[[Path, int], bool] = os.access,
        metadata_provider: Callable[[Path], Tuple[str, bool]] | None = None,
        system_drive_names: tuple[str, ...] | None = None,
    ) -> None:
        self.volume_root = Path(volume_root)
        self.listdir = listdir
        self.disk_usage = disk_usage
        self.is_mount = is_mount
        self.access = access
        self.metadata_provider = metadata_provider or self._default_metadata_provider
        self.system_drive_names = tuple(name.lower() for name in (system_drive_names or ("macintosh hd", "system")))

    def enumerate_drives(self) -> list[MountedDrive]:
        try:
            entries = list(self.listdir(self.volume_root))
        except FileNotFoundError:
            return []

        drives: list[MountedDrive] = []
        for name in entries:
            if name.startswith("."):
                continue

            path = self.volume_root / name
            if self._is_system_drive(name):
                continue

            try:
                if not self.is_mount(path):
                    continue
            except OSError:
                continue

            try:
                writable = self.access(path, os.W_OK)
            except OSError:
                writable = False

            if not writable:
                continue

            try:
                usage = self.disk_usage(path)
                total = getattr(usage, "total", 0)
                free = getattr(usage, "free", 0)
            except OSError:
                total = 0
                free = 0

            volume_type, is_removable = self.metadata_provider(path)
            drives.append(
                MountedDrive(
                    name=name,
                    path=path,
                    total_space=int(total),
                    free_space=int(free),
                    volume_type=volume_type,
                    is_writable=writable,
                    is_removable=is_removable,
                )
            )

        return drives

    def _default_metadata_provider(self, path: Path) -> tuple[str, bool]:
        for partition in psutil.disk_partitions(all=True):
            if Path(partition.mountpoint) == path:
                opts = partition.opts or ""
                volume_type = partition.fstype or "unknown"
                return volume_type, "removable" in opts.lower()
        return "unknown", False

    def _is_system_drive(self, name: str) -> bool:
        return name.lower() in self.system_drive_names
