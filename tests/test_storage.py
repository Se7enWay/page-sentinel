"""Unit tests for storage and state persistence module."""

import json
from pathlib import Path

import storage


def test_get_default_state():
    state = storage.get_default_state()
    assert state["known_files"] == []
    assert state["first_run"] is True
    assert state["check_count"] == 0


def test_atomic_save_and_load(tmp_path: Path):
    test_file = tmp_path / "state.json"
    state = {
        "known_files": ["DocA.pdf", "DocB.pdf"],
        "check_count": 5,
        "first_run": True,
    }

    storage.save_state(state, path=test_file)
    assert test_file.exists()

    loaded = storage.load_state(path=test_file)
    assert loaded["known_files"] == ["DocA.pdf", "DocB.pdf"]
    assert loaded["check_count"] == 5
    assert loaded["first_run"] is False  # save_state sets first_run to False
    assert loaded["last_checked"] is not None


def test_get_new_files_order_and_dedup():
    state = {"known_files": ["Existing1.pdf", "Existing2.pdf"]}
    current = ["Existing1.pdf", "NewAlpha.pdf", "NewBeta.pdf", "NewAlpha.pdf", "Existing2.pdf"]

    new_items = storage.get_new_files(current, state)
    assert new_items == ["NewAlpha.pdf", "NewBeta.pdf"]


def test_corrupted_state_recovery(tmp_path: Path):
    test_file = tmp_path / "corrupt_state.json"
    test_file.write_text("NOT_VALID_JSON{{{", encoding="utf-8")

    # Should recover gracefully by returning a clean default state without crashing
    state = storage.load_state(path=test_file)
    assert state["known_files"] == []
    assert state["first_run"] is True
