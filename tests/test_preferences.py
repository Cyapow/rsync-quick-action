from __future__ import annotations

import json

import hypothesis.strategies as st
from hypothesis import given

from configuration import PreferencesStore, UserPreferences


@given(
    preserve_permissions=st.booleans(),
    preserve_timestamps=st.booleans(),
    include_hidden_files=st.booleans(),
    follow_symlinks=st.booleans(),
    handle_existing_files=st.sampled_from(["overwrite", "skip", "update"]),
)
def test_preferences_roundtrip(
    tmp_path,
    preserve_permissions,
    preserve_timestamps,
    include_hidden_files,
    follow_symlinks,
    handle_existing_files,
):
    """
    Feature: rsync-quick-action, Property 8: Configuration persistence
    """
    store = PreferencesStore(base_directory=tmp_path)
    prefs = UserPreferences(
        preserve_permissions=preserve_permissions,
        preserve_timestamps=preserve_timestamps,
        include_hidden_files=include_hidden_files,
        follow_symlinks=follow_symlinks,
        handle_existing_files=handle_existing_files,
    )

    store.save(prefs)
    loaded = store.load()
    assert loaded == prefs


def test_preferences_corruption_handled(tmp_path):
    store = PreferencesStore(base_directory=tmp_path)
    store.preferences_path.write_text("{ invalid json")
    loaded = store.load()
    assert isinstance(loaded, UserPreferences)
