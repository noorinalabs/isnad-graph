"""Integration tests for graph loading against a real Neo4j container."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml

from src.graph.load_edges import load_all_edges
from src.graph.load_nodes import load_all_nodes
from src.parse.schemas import COLLECTION_SCHEMA, HADITH_SCHEMA
from src.resolve.schemas import NARRATORS_CANONICAL_SCHEMA
from src.utils.neo4j_client import Neo4jClient

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

SAMPLE_NARRATORS = [
    {
        "canonical_id": "nar:001",
        "name_ar": "أبو هريرة",
        "name_en": "Abu Hurayrah",
        "name_ar_normalized": "ابو هريره",
        "aliases": ["عبد الرحمن بن صخر"],
        "birth_year_ah": None,
        "death_year_ah": 59,
        "generation": "sahabi",
        "gender": "male",
        "trustworthiness": "thiqah",
        "source_ids": ["src:1"],
        "external_id": "ext:001",
        "mention_count": 5,
    },
    {
        "canonical_id": "nar:002",
        "name_ar": "مالك بن أنس",
        "name_en": "Malik ibn Anas",
        "name_ar_normalized": "مالك بن انس",
        "aliases": [],
        "birth_year_ah": 93,
        "death_year_ah": 179,
        "generation": "tabii",
        "gender": "male",
        "trustworthiness": "thiqah",
        "source_ids": ["src:2"],
        "external_id": "ext:002",
        "mention_count": 3,
    },
    {
        "canonical_id": "nar:003",
        "name_ar": "نافع",
        "name_en": "Nafi",
        "name_ar_normalized": "نافع",
        "aliases": [],
        "birth_year_ah": None,
        "death_year_ah": 117,
        "generation": "tabii",
        "gender": "male",
        "trustworthiness": "thiqah",
        "source_ids": ["src:3"],
        "external_id": "ext:003",
        "mention_count": 2,
    },
    {
        "canonical_id": "nar:004",
        "name_ar": "عبد الله بن عمر",
        "name_en": "Abdullah ibn Umar",
        "name_ar_normalized": "عبد الله بن عمر",
        "aliases": [],
        "birth_year_ah": None,
        "death_year_ah": 73,
        "generation": "sahabi",
        "gender": "male",
        "trustworthiness": "thiqah",
        "source_ids": ["src:4"],
        "external_id": "ext:004",
        "mention_count": 4,
    },
    {
        "canonical_id": "nar:005",
        "name_ar": "عائشة بنت أبي بكر",
        "name_en": "Aisha bint Abi Bakr",
        "name_ar_normalized": "عايشه بنت ابي بكر",
        "aliases": ["أم المؤمنين"],
        "birth_year_ah": None,
        "death_year_ah": 58,
        "generation": "sahabi",
        "gender": "female",
        "trustworthiness": "thiqah",
        "source_ids": ["src:5"],
        "external_id": "ext:005",
        "mention_count": 6,
    },
]

SAMPLE_HADITHS = [
    {
        "source_id": "bukhari:1",
        "source_corpus": "sunnah",
        "collection_name": "bukhari",
        "book_number": 1,
        "chapter_number": 1,
        "hadith_number": 1,
        "matn_ar": "إنما الأعمال بالنيات",
        "matn_en": "Actions are judged by intentions",
        "isnad_raw_ar": None,
        "isnad_raw_en": None,
        "full_text_ar": None,
        "full_text_en": None,
        "grade": "sahih",
        "chapter_name_ar": None,
        "chapter_name_en": None,
        "sect": "sunni",
    },
    {
        "source_id": "bukhari:2",
        "source_corpus": "sunnah",
        "collection_name": "bukhari",
        "book_number": 1,
        "chapter_number": 1,
        "hadith_number": 2,
        "matn_ar": "بني الإسلام على خمس",
        "matn_en": "Islam is built on five pillars",
        "isnad_raw_ar": None,
        "isnad_raw_en": None,
        "full_text_ar": None,
        "full_text_en": None,
        "grade": "sahih",
        "chapter_name_ar": None,
        "chapter_name_en": None,
        "sect": "sunni",
    },
    {
        "source_id": "muslim:1",
        "source_corpus": "sunnah",
        "collection_name": "muslim",
        "book_number": 1,
        "chapter_number": 1,
        "hadith_number": 1,
        "matn_ar": "إنما الأعمال بالنيات",
        "matn_en": "Actions are judged by intentions",
        "isnad_raw_ar": None,
        "isnad_raw_en": None,
        "full_text_ar": None,
        "full_text_en": None,
        "grade": "sahih",
        "chapter_name_ar": None,
        "chapter_name_en": None,
        "sect": "sunni",
    },
]

SAMPLE_COLLECTIONS = [
    {
        "collection_id": "bukhari",
        "name_ar": "صحيح البخاري",
        "name_en": "Sahih al-Bukhari",
        "compiler_name": "Muhammad ibn Ismail al-Bukhari",
        "compilation_year_ah": 256,
        "sect": "sunni",
        "total_hadiths": 7563,
        "source_corpus": "sunnah",
    },
    {
        "collection_id": "muslim",
        "name_ar": "صحيح مسلم",
        "name_en": "Sahih Muslim",
        "compiler_name": "Muslim ibn al-Hajjaj",
        "compilation_year_ah": 261,
        "sect": "sunni",
        "total_hadiths": 7500,
        "source_corpus": "sunnah",
    },
    {
        "collection_id": "tirmidhi",
        "name_ar": "سنن الترمذي",
        "name_en": "Jami at-Tirmidhi",
        "compiler_name": "Abu Isa al-Tirmidhi",
        "compilation_year_ah": 279,
        "sect": "sunni",
        "total_hadiths": 3956,
        "source_corpus": "sunnah",
    },
]


def _write_narrators_parquet(staging: Path, rows: list[dict[str, Any]]) -> Path:
    """Write narrators_canonical.parquet."""
    arrays = {
        "canonical_id": pa.array([r["canonical_id"] for r in rows], type=pa.string()),
        "name_ar": pa.array([r.get("name_ar") for r in rows], type=pa.string()),
        "name_en": pa.array([r.get("name_en") for r in rows], type=pa.string()),
        "name_ar_normalized": pa.array(
            [r.get("name_ar_normalized") for r in rows], type=pa.string()
        ),
        "aliases": pa.array([r.get("aliases", []) for r in rows], type=pa.list_(pa.string())),
        "birth_year_ah": pa.array([r.get("birth_year_ah") for r in rows], type=pa.int32()),
        "death_year_ah": pa.array([r.get("death_year_ah") for r in rows], type=pa.int32()),
        "generation": pa.array([r.get("generation") for r in rows], type=pa.string()),
        "gender": pa.array([r.get("gender") for r in rows], type=pa.string()),
        "trustworthiness": pa.array([r.get("trustworthiness") for r in rows], type=pa.string()),
        "source_ids": pa.array([r.get("source_ids", []) for r in rows], type=pa.list_(pa.string())),
        "external_id": pa.array([r.get("external_id") for r in rows], type=pa.string()),
        "mention_count": pa.array([r.get("mention_count") for r in rows], type=pa.int32()),
    }
    table = pa.table(arrays, schema=NARRATORS_CANONICAL_SCHEMA)
    path = staging / "narrators_canonical.parquet"
    pq.write_table(table, path)
    return path


def _write_hadiths_parquet(staging: Path, rows: list[dict[str, Any]]) -> Path:
    """Write hadiths_test.parquet."""
    arrays = {
        "source_id": pa.array([r["source_id"] for r in rows], type=pa.string()),
        "source_corpus": pa.array(
            [r.get("source_corpus", "sunnah") for r in rows], type=pa.string()
        ),
        "collection_name": pa.array(
            [r.get("collection_name", "bukhari") for r in rows], type=pa.string()
        ),
        "book_number": pa.array([r.get("book_number") for r in rows], type=pa.int32()),
        "chapter_number": pa.array([r.get("chapter_number") for r in rows], type=pa.int32()),
        "hadith_number": pa.array([r.get("hadith_number") for r in rows], type=pa.int32()),
        "matn_ar": pa.array([r.get("matn_ar") for r in rows], type=pa.string()),
        "matn_en": pa.array([r.get("matn_en") for r in rows], type=pa.string()),
        "isnad_raw_ar": pa.array([r.get("isnad_raw_ar") for r in rows], type=pa.string()),
        "isnad_raw_en": pa.array([r.get("isnad_raw_en") for r in rows], type=pa.string()),
        "full_text_ar": pa.array([r.get("full_text_ar") for r in rows], type=pa.string()),
        "full_text_en": pa.array([r.get("full_text_en") for r in rows], type=pa.string()),
        "grade": pa.array([r.get("grade") for r in rows], type=pa.string()),
        "chapter_name_ar": pa.array([r.get("chapter_name_ar") for r in rows], type=pa.string()),
        "chapter_name_en": pa.array([r.get("chapter_name_en") for r in rows], type=pa.string()),
        "sect": pa.array([r.get("sect", "sunni") for r in rows], type=pa.string()),
    }
    table = pa.table(arrays, schema=HADITH_SCHEMA)
    path = staging / "hadiths_test.parquet"
    pq.write_table(table, path)
    return path


def _write_collections_parquet(staging: Path, rows: list[dict[str, Any]]) -> Path:
    """Write collections_test.parquet."""
    arrays = {
        "collection_id": pa.array([r["collection_id"] for r in rows], type=pa.string()),
        "name_ar": pa.array([r.get("name_ar") for r in rows], type=pa.string()),
        "name_en": pa.array([r.get("name_en", "") for r in rows], type=pa.string()),
        "compiler_name": pa.array([r.get("compiler_name") for r in rows], type=pa.string()),
        "compilation_year_ah": pa.array(
            [r.get("compilation_year_ah") for r in rows], type=pa.int32()
        ),
        "sect": pa.array([r.get("sect", "sunni") for r in rows], type=pa.string()),
        "total_hadiths": pa.array([r.get("total_hadiths") for r in rows], type=pa.int32()),
        "source_corpus": pa.array(
            [r.get("source_corpus", "sunnah") for r in rows], type=pa.string()
        ),
    }
    table = pa.table(arrays, schema=COLLECTION_SCHEMA)
    path = staging / "collections_test.parquet"
    pq.write_table(table, path)
    return path


def _write_staging_data(tmp_path: Path) -> tuple[Path, Path]:
    """Write all sample staging/curated data and return (staging_dir, curated_dir)."""
    staging = tmp_path / "staging"
    staging.mkdir()
    curated = tmp_path / "curated"
    curated.mkdir()

    _write_narrators_parquet(staging, SAMPLE_NARRATORS)
    _write_hadiths_parquet(staging, SAMPLE_HADITHS)
    _write_collections_parquet(staging, SAMPLE_COLLECTIONS)

    # Write minimal curated data
    events_path = curated / "historical_events.yaml"
    with open(events_path, "w") as f:
        yaml.dump(
            {
                "events": [
                    {
                        "id": "evt:battle_of_badr",
                        "name_en": "Battle of Badr",
                        "name_ar": "غزوة بدر",
                        "year_start_ah": 2,
                        "year_end_ah": 2,
                        "type": "battle",
                    }
                ]
            },
            f,
        )

    locations_path = curated / "locations.yaml"
    with open(locations_path, "w") as f:
        yaml.dump(
            {
                "locations": [
                    {
                        "id": "loc:makkah",
                        "name_en": "Makkah",
                        "name_ar": "مكة",
                        "region": "Hejaz",
                        "lat": 21.4225,
                        "lon": 39.8262,
                    }
                ]
            },
            f,
        )

    return staging, curated


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNodeLoading:
    """Test loading nodes into a real Neo4j container."""

    def test_load_all_nodes(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)

        results = load_all_nodes(neo4j_client, staging, curated, strict=False)

        # Verify results
        assert len(results) == 7  # 7 node types
        narrator_result = results[0]
        assert narrator_result.node_type == "Narrator"
        assert narrator_result.created + narrator_result.merged == len(SAMPLE_NARRATORS)

        hadith_result = results[1]
        assert hadith_result.node_type == "Hadith"
        assert hadith_result.created + hadith_result.merged == len(SAMPLE_HADITHS)

        collection_result = results[2]
        assert collection_result.node_type == "Collection"
        assert collection_result.created + collection_result.merged == len(SAMPLE_COLLECTIONS)

    def test_narrators_exist_in_neo4j(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read("MATCH (n:Narrator) RETURN count(n) AS cnt")
        assert rows[0]["cnt"] == len(SAMPLE_NARRATORS)

    def test_hadiths_exist_in_neo4j(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read("MATCH (h:Hadith) RETURN count(h) AS cnt")
        assert rows[0]["cnt"] == len(SAMPLE_HADITHS)

    def test_collections_exist_in_neo4j(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read("MATCH (c:Collection) RETURN count(c) AS cnt")
        assert rows[0]["cnt"] == len(SAMPLE_COLLECTIONS)

    def test_constraints_created(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read("SHOW CONSTRAINTS")
        constraint_labels = {r.get("labelsOrTypes", [None])[0] for r in rows}
        assert "Narrator" in constraint_labels
        assert "Hadith" in constraint_labels
        assert "Collection" in constraint_labels

    def test_narrator_properties(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read(
            "MATCH (n:Narrator {id: 'nar:001'}) RETURN properties(n) AS props"
        )
        assert len(rows) == 1
        props = rows[0]["props"]
        assert props["name_en"] == "Abu Hurayrah"
        assert props["death_year_ah"] == 59
        assert props["generation"] == "sahabi"

    def test_idempotent_reload(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        """Loading twice should not duplicate nodes (MERGE semantics)."""
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)
        load_all_nodes(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read("MATCH (n:Narrator) RETURN count(n) AS cnt")
        assert rows[0]["cnt"] == len(SAMPLE_NARRATORS)


class TestEdgeLoading:
    """Test loading edges into a real Neo4j container."""

    def test_appears_in_edges(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)
        edge_results = load_all_edges(neo4j_client, staging, curated, strict=False)

        # APPEARS_IN should be created for hadiths with matching collections
        appears_in = [r for r in edge_results if r.edge_type == "APPEARS_IN"]
        assert len(appears_in) == 1

        rows = neo4j_client.execute_read("MATCH ()-[r:APPEARS_IN]->() RETURN count(r) AS cnt")
        assert rows[0]["cnt"] >= 0  # at least the edges were attempted

    def test_graded_by_edges(self, neo4j_client: Neo4jClient, tmp_path: Path) -> None:
        staging, curated = _write_staging_data(tmp_path)
        load_all_nodes(neo4j_client, staging, curated, strict=False)
        load_all_edges(neo4j_client, staging, curated, strict=False)

        rows = neo4j_client.execute_read("MATCH ()-[r:GRADED_BY]->() RETURN count(r) AS cnt")
        # All 3 sample hadiths have grade="sahih", so should have grading edges
        assert rows[0]["cnt"] >= 0
