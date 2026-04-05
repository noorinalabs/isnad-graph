"""Tests for shared acquisition and parsing utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.acquire.base import ensure_dir, sha256_file, write_manifest
from src.parse.base import generate_source_id, safe_int, safe_str


class TestEnsureDir:
    def test_creates_nested_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        result = ensure_dir(target)
        assert result == target
        assert target.is_dir()

    def test_returns_existing_dir(self, tmp_path: Path) -> None:
        result = ensure_dir(tmp_path)
        assert result == tmp_path


class TestSha256File:
    def test_computes_correct_hash(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        content = b"hadith corpus data"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert sha256_file(f) == expected

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert sha256_file(f) == expected


class TestWriteManifest:
    def test_writes_valid_json(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.txt"
        f1.write_text("hello")
        f2 = tmp_path / "b.txt"
        f2.write_text("world")

        manifest_path = write_manifest(tmp_path, [f1, f2])
        assert manifest_path == tmp_path / "manifest.json"
        assert manifest_path.exists()

        data = json.loads(manifest_path.read_text())
        assert len(data) == 2
        assert data[0]["path"] == "a.txt"
        assert data[0]["size"] == f1.stat().st_size
        assert data[0]["sha256"] == sha256_file(f1)
        assert data[1]["path"] == "b.txt"


class TestGenerateSourceId:
    def test_basic(self) -> None:
        assert generate_source_id("lk", "bukhari", 1, 1) == "lk:bukhari:1:1"

    def test_string_parts(self) -> None:
        assert generate_source_id("sanadset", "mention", "hid", "0") == "sanadset:mention:hid:0"

    def test_no_extra_parts(self) -> None:
        assert generate_source_id("lk", "muslim") == "lk:muslim"


class TestSafeInt:
    def test_int(self) -> None:
        assert safe_int(42) == 42

    def test_float(self) -> None:
        assert safe_int(3.7) == 3

    def test_str(self) -> None:
        assert safe_int("5") == 5

    def test_none(self) -> None:
        assert safe_int(None) is None

    def test_nan_string(self) -> None:
        assert safe_int("NaN") is None

    def test_nan_lowercase(self) -> None:
        assert safe_int("nan") is None

    def test_empty_string(self) -> None:
        assert safe_int("") is None


class TestSafeStr:
    def test_str(self) -> None:
        assert safe_str("hello") == "hello"

    def test_none(self) -> None:
        assert safe_str(None) is None

    def test_empty(self) -> None:
        assert safe_str("") is None

    def test_nan(self) -> None:
        assert safe_str("nan") is None

    def test_none_string(self) -> None:
        assert safe_str("None") is None

    def test_whitespace(self) -> None:
        assert safe_str("  ") is None

    def test_strips_whitespace(self) -> None:
        assert safe_str("  hello  ") == "hello"
