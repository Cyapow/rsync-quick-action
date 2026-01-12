from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


class InvalidRsyncConfiguration(ValueError):
    """Raised when rsync command construction fails due to invalid input."""


@dataclass(frozen=True)
class SyncOptions:
    preserve_permissions: bool = True
    preserve_timestamps: bool = True
    include_hidden_files: bool = True
    handle_existing_files: str = "update"  # overwrite | skip | update
    follow_symlinks: bool = False
    dry_run: bool = False

    def __post_init__(self) -> None:
        valid_existing = {"overwrite", "skip", "update"}
        if self.handle_existing_files not in valid_existing:
            raise InvalidRsyncConfiguration(
                f"handle_existing_files must be one of {sorted(valid_existing)}, "
                f"got {self.handle_existing_files}"
            )


class RsyncCommandBuilder:
    def __init__(self, binary: str = "rsync") -> None:
        self.binary = binary

    def build(
        self,
        sources: Iterable[Path | str],
        destination: Path | str,
        options: SyncOptions | None = None,
    ) -> List[str]:
        opts = options or SyncOptions()
        source_paths = [Path(src) for src in sources]
        if not source_paths:
            raise InvalidRsyncConfiguration("At least one source path is required")

        dest_path = Path(destination)
        command: list[str] = [self.binary, "-r", "--info=progress2", "--human-readable"]

        if opts.preserve_permissions:
            command.append("-p")
        if opts.preserve_timestamps:
            command.append("-t")

        if opts.follow_symlinks:
            command.append("-L")
        else:
            command.append("-l")

        if opts.handle_existing_files == "skip":
            command.append("--ignore-existing")
        elif opts.handle_existing_files == "update":
            command.append("--update")

        if not opts.include_hidden_files:
            command.append("--exclude=.*")

        if opts.dry_run:
            command.append("--dry-run")

        command.append("--")
        command.extend(str(path) for path in source_paths)
        command.append(str(dest_path))
        return command
