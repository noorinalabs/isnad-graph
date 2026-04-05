# Pipeline Smoke Test Results

**Date:** 2026-03-29
**Runner:** Rashid Osei-Mensah
**Script:** `scripts/pipeline_smoke.py`
**Sources tested:** open_hadith, lk_corpus, muhaddithat

## Summary

| Source | Acquire | Parse | Validate | Notes |
|--------|---------|-------|----------|-------|
| open_hadith | PASS | PASS | PASS | 124,320 hadiths parsed, schema valid |
| lk_corpus | PASS | FAIL | -- | Per-chapter CSV structure not matched by parser |
| muhaddithat | PASS | FAIL | -- | Narrator CSV filename (`variousnarrators.csv`) not matched by parser |

**Overall: 1/3 sources fully passing end-to-end.**

## Detailed Results

### open_hadith (PASS)

- **Acquire:** 0.47s -- shallow-cloned 18 CSV files from `mhashim6/Open-Hadith-Data`
- **Parse:** 0.84s -- produced `hadiths_open_hadith.parquet` with 124,320 rows
- **Validate:** Schema conforms to `HADITH_SCHEMA` (16 columns, all types correct)
- **Warning:** No diacritics-specific CSVs detected (filenames lack "tashkeel"/"diacritics"); parser fell back to all 18 CSVs. `text_col` resolved to `None` for all files, meaning text is stored in `full_text_ar` via fallback rather than `matn_ar`.

### lk_corpus (FAIL at parse)

- **Acquire:** Succeeded (initial attempt timed out at 120s default; manual retry with longer timeout succeeded). Repository contains per-book directories (`Bukhari/`, `Muslim/`, `AbuDaud/`, `Tirmizi/`, `Nesai/`, `IbnMaja/`) with per-chapter CSVs (e.g., `Chapter1.csv`, `Chapter2.csv`).
- **Parse failure:** The parser's `_derive_collection_name()` function maps filenames like `albukhari.csv` to canonical names. Per-chapter filenames like `Chapter1.csv` do not match any entry in `FILENAME_TO_COLLECTION`, so all CSVs are skipped with `lk_unknown_csv` warnings. The parser then finds 0 hadiths and raises `FileNotFoundError`.
- **Root cause:** The LK corpus repository structure changed from single-file-per-book to per-chapter files. The parser needs to derive the collection name from the **parent directory** (e.g., `Bukhari/Chapter1.csv` -> `bukhari`) rather than the filename alone.
- **Recommended fix:** Update `_derive_collection_name()` to check `csv_path.parent.name` against a directory-to-collection mapping when the filename does not match.

### muhaddithat (FAIL at parse)

- **Acquire:** 0.55s -- shallow-cloned `muhaddithat/isnad-datasets`. Found 2 data CSV files: `data/hadiths.csv` and `data/variousnarrators.csv`.
- **Parse failure:** The parser searches for narrator CSVs matching `narrators.csv`, `scholars.csv`, or `narrator*.csv` (glob). The actual file is named `variousnarrators.csv`, which does not match `narrator*.csv` because glob requires the pattern to match from the start of the filename.
- **Root cause:** The glob pattern `narrator*.csv` matches `narrator_foo.csv` but not `variousnarrators.csv`. The pattern needs to be `*narrator*.csv` to match embedded occurrences.
- **Recommended fix:** Add `*narrator*.csv` or `variousnarrators.csv` to the search patterns in `muhaddithat.py:247-249`.

## Timing

| Stage | open_hadith | lk_corpus | muhaddithat |
|-------|-------------|-----------|-------------|
| Acquire | 0.47s (cached) | ~5s (cached) | 0.55s (cached) |
| Parse | 0.84s | N/A | N/A |
| Validate | 0.01s | N/A | N/A |
| **Total** | **1.32s** | -- | -- |

Note: First-run acquire times are significantly longer due to git clone operations. The LK corpus clone timed out at the default 120s timeout on first attempt.

## Data Quality Observations

1. **open_hadith text column detection:** The parser's diacritics filename filter (`tashkeel`/`diacritics`) found zero matches, suggesting the upstream repo may have changed its naming conventions. All 18 CSVs were parsed via the fallback path.

2. **open_hadith column mapping:** `text_col` resolved to `None` for all parsed CSVs, meaning hadith text was stored in `full_text_ar` rather than `matn_ar`. This may affect downstream consumers that expect `matn_ar` to be populated.

3. **LK corpus clone timeout:** The default 120s clone timeout is insufficient for the LK Hadith Corpus repository. Consider increasing the timeout or implementing partial/sparse checkout for large repos.

4. **LK corpus structure change:** The repository now uses per-chapter CSVs within book directories instead of single files per book. This is a breaking change for the parser.

5. **muhaddithat narrator file naming:** The narrator file is named `variousnarrators.csv` instead of the expected `narrators.csv`. The glob patterns in the parser are too restrictive.

## Recommendations

1. **P0 -- Fix LK parser:** Update `_derive_collection_name()` to handle per-chapter CSV structures by mapping parent directory names to collection names.
2. **P0 -- Fix muhaddithat parser:** Add `*narrator*.csv` to the search patterns for narrator CSV files.
3. **P1 -- Fix open_hadith text mapping:** Investigate CSV column headers and update `_TEXT_COLUMNS` candidates if needed so that `matn_ar` is populated instead of `full_text_ar`.
4. **P2 -- Increase clone timeout:** Make the git clone timeout configurable or increase the default for large repositories like LK.
