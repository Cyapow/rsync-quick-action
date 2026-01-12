from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class UserPreferences:
    preserve_permissions: bool = True
    preserve_timestamps: bool = True
    include_hidden_files: bool = True
    follow_symlinks: bool = False
    handle_existing_files: str = "update"  # overwrite | skip | update


class PreferencesStore:
    def __init__(self, base_directory: Path | None = None) -> None:
        self.base_directory = base_directory or Path.home() / ".rsync_quick_action"
        self.base_directory.mkdir(parents=True, exist_ok=True)
        self.preferences_path = self.base_directory / "preferences.json"

    def load(self) -> UserPreferences:
        try:
            data = json.loads(self.preferences_path.read_text())
            return self._from_dict(data)
        except FileNotFoundError:
            return UserPreferences()
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            # Corrupted file or invalid schema; fall back to defaults.
            return UserPreferences()

    def save(self, preferences: UserPreferences) -> None:
        payload = asdict(preferences)
        self.preferences_path.write_text(json.dumps(payload, indent=2))

    @staticmethod
    def _from_dict(data: Dict[str, Any]) -> UserPreferences:
        return UserPreferences(
            preserve_permissions=bool(data.get("preserve_permissions", True)),
            preserve_timestamps=bool(data.get("preserve_timestamps", True)),
            include_hidden_files=bool(data.get("include_hidden_files", True)),
            follow_symlinks=bool(data.get("follow_symlinks", False)),
            handle_existing_files=str(data.get("handle_existing_files", "update")),
        )


def load_preferences(base_directory: Path | None = None) -> UserPreferences:
    return PreferencesStore(base_directory=base_directory).load()


def save_preferences(preferences: UserPreferences, base_directory: Path | None = None) -> None:
    PreferencesStore(base_directory=base_directory).save(preferences)
