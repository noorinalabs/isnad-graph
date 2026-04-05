"""Tests for the pipeline manifest system."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.pipeline.manifest import (
    LAST_LOADED_MANIFEST_FILENAME,
    MANIFEST_FILENAME,
    ChangedFiles,
    compare_manifests,
    generate_manifest,
    load_manifest,
    save_manifest,
)


def _write_parquet(path: Path, num_rows: int = 5) -> None:
    """Write a minimal Parquet file with *num_rows* rows."""
    table = pa.table({"id": list(range(num_rows)), "value": [f"v{i}" for i in range(num_rows)]})
    pq.write_table(table, path)


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    staging = tmp_path / "staging"
    staging.mkdir()
    curated = tmp_path / "curated"
    curated.mkdir()
    return tmp_path


class TestGenerateManifest:
    def test_empty_dirs(self, data_dir: Path) -> None:
        result = generate_manifest(data_dir)
        assert result == {}

    def test_generates_entries_for_parquet_files(self, data_dir: Path) -> None:
        _write_parquet(data_dir / "staging" / "hadiths_bukhari.parquet", num_rows=10)
        _write_parquet(data_dir / "curated" / "narrators.parquet", num_rows=3)

        manifest = generate_manifest(data_dir)
        assert len(manifest) == 2
        assert "staging/hadiths_bukhari.parquet" in manifest
        assert "curated/narrators.parquet" in manifest

        entry = manifest["staging/hadiths_bukhari.parquet"]
        assert entry["rows"] == 10
        assert entry["size_bytes"] > 0
        assert len(entry["md5"]) == 32
        assert "last_modified" in entry

    def test_ignores_non_parquet(self, data_dir: Path) -> None:
        (data_dir / "staging" / "notes.txt").write_text("not a parquet file")
        _write_parquet(data_dir / "staging" / "data.parquet")

        manifest = generate_manifest(data_dir)
        assert len(manifest) == 1
        assert "staging/data.parquet" in manifest


class TestCompareManifests:
    def test_all_new(self) -> None:
        current = {"staging/a.parquet": {"md5": "abc", "rows": 1, "size_bytes": 100}}
        diff = compare_manifests(current, {})
        assert diff.added == ["staging/a.parquet"]
        assert diff.modified == []
        assert diff.unchanged == []
        assert diff.removed == []
        assert diff.has_changes is True

    def test_modified_file(self) -> None:
        prev = {"staging/a.parquet": {"md5": "abc", "rows": 1, "size_bytes": 100}}
        curr = {"staging/a.parquet": {"md5": "def", "rows": 2, "size_bytes": 200}}
        diff = compare_manifests(curr, prev)
        assert diff.modified == ["staging/a.parquet"]
        assert diff.unchanged == []
        assert diff.has_changes is True

    def test_unchanged_file(self) -> None:
        m = {"staging/a.parquet": {"md5": "abc", "rows": 1, "size_bytes": 100}}
        diff = compare_manifests(m, m)
        assert diff.unchanged == ["staging/a.parquet"]
        assert diff.has_changes is False

    def test_removed_file(self) -> None:
        prev = {"staging/a.parquet": {"md5": "abc", "rows": 1, "size_bytes": 100}}
        diff = compare_manifests({}, prev)
        assert diff.removed == ["staging/a.parquet"]
        assert diff.has_changes is True

    def test_mixed_changes(self) -> None:
        prev = {
            "staging/kept.parquet": {"md5": "aaa", "rows": 1, "size_bytes": 10},
            "staging/changed.parquet": {"md5": "bbb", "rows": 2, "size_bytes": 20},
            "staging/gone.parquet": {"md5": "ccc", "rows": 3, "size_bytes": 30},
        }
        curr = {
            "staging/kept.parquet": {"md5": "aaa", "rows": 1, "size_bytes": 10},
            "staging/changed.parquet": {"md5": "ddd", "rows": 4, "size_bytes": 40},
            "staging/new.parquet": {"md5": "eee", "rows": 5, "size_bytes": 50},
        }
        diff = compare_manifests(curr, prev)
        assert diff.added == ["staging/new.parquet"]
        assert diff.modified == ["staging/changed.parquet"]
        assert diff.unchanged == ["staging/kept.parquet"]
        assert diff.removed == ["staging/gone.parquet"]
        assert diff.changed_files == ["staging/new.parquet", "staging/changed.parquet"]

    def test_changed_files_property(self) -> None:
        diff = ChangedFiles(added=["a"], modified=["b"], unchanged=["c"], removed=["d"])
        assert diff.changed_files == ["a", "b"]


class TestSaveLoadManifest:
    def test_round_trip(self, tmp_path: Path) -> None:
        manifest = {"staging/test.parquet": {"md5": "abc123", "rows": 42, "size_bytes": 1024}}
        path = tmp_path / MANIFEST_FILENAME
        save_manifest(manifest, path)
        loaded = load_manifest(path)
        assert loaded == manifest

    def test_load_missing_returns_empty(self, tmp_path: Path) -> None:
        result = load_manifest(tmp_path / "nonexistent.json")
        assert result == {}

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "dir" / MANIFEST_FILENAME
        save_manifest({"a": {"md5": "x"}}, path)
        assert path.exists()

    def test_last_loaded_manifest_filename(self) -> None:
        assert LAST_LOADED_MANIFEST_FILENAME == ".last_loaded_manifest.json"


class TestIncrementalDetection:
    """End-to-end: generate, save, modify, regenerate, compare."""

    def test_detect_change_after_modification(self, data_dir: Path) -> None:
        _write_parquet(data_dir / "staging" / "hadiths.parquet", num_rows=5)
        manifest_v1 = generate_manifest(data_dir)
        save_manifest(manifest_v1, data_dir / MANIFEST_FILENAME)

        # Modify the file
        _write_parquet(data_dir / "staging" / "hadiths.parquet", num_rows=10)
        manifest_v2 = generate_manifest(data_dir)

        diff = compare_manifests(manifest_v2, manifest_v1)
        assert diff.modified == ["staging/hadiths.parquet"]
        assert diff.has_changes is True
