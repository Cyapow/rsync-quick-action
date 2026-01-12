from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

ProgressCallback = Callable[[dict], None]


@dataclass
class RsyncResult:
    success: bool
    returncode: int | None
    output: list[str]
    errors: list[str]
    cancelled: bool = False


class RsyncRunner:
    def __init__(self, popen_factory: Callable[..., subprocess.Popen] = subprocess.Popen) -> None:
        self._popen_factory = popen_factory

    def run(
        self,
        command: Iterable[str],
        on_progress: Optional[ProgressCallback] = None,
        cancel_event: Optional[threading.Event] = None,
        cwd: str | None = None,
    ) -> RsyncResult:
        process = self._popen_factory(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=cwd,
        )

        if cancel_event and cancel_event.is_set():
            self._terminate_process(process)
            return RsyncResult(False, process.returncode, [], [], cancelled=True)

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        try:
            for line in process.stdout or []:
                if cancel_event and cancel_event.is_set():
                    self._terminate_process(process)
                    return RsyncResult(False, process.returncode, stdout_lines, stderr_lines, cancelled=True)

                stdout_lines.append(line.rstrip())
                if on_progress:
                    progress = self._parse_progress_line(line)
                    if progress:
                        on_progress(progress)

            stderr_lines.extend([line.rstrip() for line in process.stderr or []])
            returncode = process.wait()
            return RsyncResult(returncode == 0, returncode, stdout_lines, stderr_lines, cancelled=False)
        except Exception:
            self._terminate_process(process)
            raise

    @staticmethod
    def _parse_progress_line(line: str) -> dict | None:
        # Basic parser for progress2 lines: "   102,400  20%    1.23MB/s    0:00:10"
        if "%" not in line:
            return None
        parts = line.strip().split()
        if len(parts) < 2 or not parts[1].endswith("%"):
            return None
        try:
            percent = float(parts[1].strip("%"))
        except ValueError:
            return None

        return {"percent": percent, "raw": line.strip()}

    @staticmethod
    def _terminate_process(process: subprocess.Popen) -> None:
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
                process.wait(timeout=2)
            except Exception:
                # Last resort: let the process be cleaned up by the OS if it persists
                pass
