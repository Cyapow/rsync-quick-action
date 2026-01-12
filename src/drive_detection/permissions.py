from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class PermissionCheck:
    allowed: bool
    reason: str | None = None


def validate_destination(
    destination: Path | str,
    access: Callable[[Path, int], bool] = os.access,
) -> PermissionCheck:
    target = Path(destination)
    try:
        if access(target, os.W_OK):
            return PermissionCheck(True, None)

        parent = target.parent
        if parent != target and access(parent, os.W_OK):
            return PermissionCheck(True, None)

        return PermissionCheck(False, f"No write permission for {target}")
    except OSError as exc:
        return PermissionCheck(False, f"Permission check failed: {exc}")
