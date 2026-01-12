from __future__ import annotations

from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given

from cli import parse_sources


def path_segment_strategy():
    return st.text(alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz0123456789/_-")), min_size=1, max_size=20)


@given(path_segment_strategy())
def test_source_path_preservation(segment: str):
    """
    Feature: rsync-quick-action, Property 1: Source path preservation
    """
    source = f"/Volumes/Drive/{segment}"
    parsed = parse_sources([source])
    assert parsed == [Path(source)]


@given(st.lists(path_segment_strategy(), min_size=2, max_size=6, unique=True))
def test_batch_selection_handling(segments):
    """
    Feature: rsync-quick-action, Property 2: Batch selection handling
    """
    sources = [f"/Volumes/Drive/{s}" for s in segments]
    parsed = parse_sources(sources)
    assert parsed == [Path(s) for s in sources]
