# Data Validation Runbook

## Prerequisites

Before running the full pipeline against real data:

1. **Docker services** must be running:
   ```bash
   make infra
   docker compose ps  # verify neo4j, postgres, redis are healthy
   ```

2. **API keys** configured in `.env`:
   - `SUNNAH_API_KEY` — required for Sunnah.com API downloads
   - `KAGGLE_USERNAME` and `KAGGLE_KEY` — required for Kaggle datasets
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` — graph database credentials
   - `PG_DSN` — PostgreSQL connection string

3. **Disk space**: at least 5 GB free for raw downloads and staging Parquet files.

4. **Python environment**:
   ```bash
   make setup  # installs all dependencies via uv
   ```

## Running the Full Pipeline

### Option A: Automated validation script

```bash
make validate-pipeline
# or directly:
bash scripts/validate_pipeline.sh
```

This runs all pipeline phases in order: acquire, parse, validate-staging, resolve, load, enrich, validate.

### Option B: Step-by-step

```bash
make acquire          # Download raw data sources
make parse            # Parse to staging Parquet
make validate-staging # Check staging file schemas and integrity
make resolve          # Entity resolution (NER, disambiguation, dedup)
make load             # Load graph into Neo4j
make enrich           # Compute metrics, topics, historical overlay
```

## Data Profiling

Profile staging Parquet files to inspect row counts, null rates, and schema conformance:

```bash
make profile-data
# or directly:
uv run python scripts/data_profile.py
```

The profiler outputs a JSON report to stdout and writes `data/staging/profile_report.json`.

### Interpreting the Profile Report

Each file entry includes:
- **rows**: total row count
- **columns**: per-column type, null count, null rate, and unique value count
- **schema_conformance**: PASS if columns match the expected PyArrow schema, FAIL if mismatched, UNKNOWN if no schema mapping exists

Key things to check:
- **Null rates**: `matn_ar` and `isnad_raw_ar` may have high null rates for English-only sources; this is expected. `source_id` and `source_corpus` should never be null.
- **Row counts**: see "Expected Output Sizes" below for approximate ranges.
- **Schema issues**: missing or extra columns indicate a parser drift from the canonical schema.

## Expected Output Sizes

Approximate row counts per source after parsing (these vary as upstream data evolves):

| Source | Staging Table | Approximate Rows |
|--------|--------------|-----------------|
| Sunnah.com API | hadith | 40,000-60,000 |
| Open Hadith | hadith | 10,000-30,000 |
| Muhaddithat | narrator_bio | 5,000-10,000 |
| LK Corpus | hadith, narrator_mention | 20,000-40,000 |
| SanadSet | network_edge | 50,000-100,000 |
| Thaqalayn | hadith | 10,000-20,000 |
| Fawaz corpus | hadith, narrator_bio | 5,000-15,000 |

## Known Data Quality Risks

### Arabic text normalization
Different sources use inconsistent diacritics, alif/hamza forms, and taa marbuta. The `src.utils.arabic` module normalizes these, but edge cases may slip through. Check `name_ar_normalized` null rates in narrator tables.

### Duplicate hadith across sources
The same hadith may appear in multiple sources with different IDs. Phase 2 entity resolution (dedup step) handles this, but coverage depends on text similarity thresholds. High duplicate rates in the graph validation step may indicate threshold tuning is needed.

### Missing isnad chains
Some sources provide matn (text) only, without explicit isnad (chain) data. These hadiths will have null `isnad_raw_ar` / `isnad_raw_en` and will not produce narrator_mention or network_edge records.

### API rate limiting
The Sunnah.com API has rate limits. If acquisition fails partway through, re-running `make acquire` is safe (downloaders are idempotent) and will resume from where it left off.

### Neo4j memory
Loading the full graph requires adequate Neo4j heap and page cache. If loading fails with memory errors, increase `NEO4J_HEAP_SIZE` and `NEO4J_PAGECACHE` in `docker-compose.yml`.

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `validate-staging` reports missing columns | Parser output drifted from schema | Check parser against `src/parse/schemas.py` |
| Low row counts after parse | Raw download incomplete | Re-run `make acquire`, check API keys |
| Graph validation FAIL on orphan nodes | Edges not loaded or endpoints missing | Run `make load` with full data; check resolve output |
| Enrichment steps fail | Neo4j GDS plugin not installed | Ensure `neo4j-graph-data-science` plugin is in Docker config |
| Profile report shows 0 files | Staging directory empty | Run `make parse` first |
