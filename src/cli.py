from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

from gui import RsyncQuickActionApp


def parse_sources(args: Iterable[str]) -> List[Path]:
    sources = [Path(arg).expanduser() for arg in args]
    if not sources:
        raise ValueError("At least one source path is required")
    return sources


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the Rsync Quick Action GUI.")
    parser.add_argument(
        "sources",
        nargs="+",
        help="Source file or folder paths provided by the Quick Action.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    parser = build_arg_parser()
    parsed = parser.parse_args(argv)

    try:
        sources = parse_sources(parsed.sources)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    app = RsyncQuickActionApp(sources)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
