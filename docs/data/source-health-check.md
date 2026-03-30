# Data Source Health Check Report

**Date:** 2026-03-29
**Author:** Elena Petrova (Staff Data Engineer, Data Lead)
**Issue:** #528

## Summary

Verified all 8 data source downloaders in `src/acquire/`. Of 8 sources, **5 are healthy**, **1 requires an API key** (cannot verify without credentials but code is correct), and **2 are broken** (upstream sources removed).

## Health Check Results

| # | Source | Module | Type | Status | Notes |
|---|--------|--------|------|--------|-------|
| 1 | Sunnah.com API | `sunnah_api.py` | REST API | HEALTHY (needs key) | API live at `api.sunnah.com/v1`; returns 403 without `SUNNAH_API_KEY` (expected). Code structure correct. |
| 2 | Thaqalayn | `thaqalayn.py` | REST API + GitHub fallback | DEGRADED | API v2 endpoint (`thaqalayn.net/api/v2/allbooks`) returns **404**. Website is live (rebuilt with Next.js) but REST API removed. GitHub fallback (`MohammedArab1/ThaqalaynAPI`) is still accessible. |
| 3 | Open Hadith Data | `open_hadith.py` | GitHub clone | HEALTHY | Repo `mhashim6/Open-Hadith-Data` accessible. HEAD: `1515f6c`. |
| 4 | LK Hadith Corpus | `lk_corpus.py` | GitHub clone | HEALTHY | Repo `ShathaTm/LK-Hadith-Corpus` accessible. HEAD: `c45fa64`. |
| 5 | Sanadset (Kaggle) | `sanadset.py` | Kaggle CLI | BROKEN | Both datasets (`fahd09/hadith-dataset` and `fahd09/hadith-narrators`) return **HTTP 404** on Kaggle. Datasets have been removed or made private. |
| 6 | Muhaddithat | `muhaddithat.py` | GitHub clone | HEALTHY | Repo `muhaddithat/isnad-datasets` accessible. HEAD: `e7946d1`. |
| 7 | Fawaz Hadith API | `fawaz.py` | CDN (jsdelivr) | HEALTHY | Both `editions.json` (73 editions across 10 collections) and `info.json` (grading metadata) are accessible via jsdelivr CDN. |
| 8 | Sunnah.com Scraper | `sunnah_scraper.py` | Web scraper | HEALTHY | Website `sunnah.com` is live and functional. 9 primary + 9 secondary collections available. robots.txt check built into code. |

## Detailed Findings

### 1. Sunnah.com API (`sunnah_api.py`)

- **Endpoint:** `https://api.sunnah.com/v1`
- **Auth:** Requires `X-API-Key` header via `SUNNAH_API_KEY` env var
- **Test result:** HTTP 403 (`MissingAuthenticationTokenException`) without key -- expected
- **Code review:** Correctly handles missing API key (returns `None`), uses paginated fetch with rate limiting (200ms), idempotent file caching
- **Verdict:** Code is correct. Cannot fully verify without API key, but endpoint is live.

### 2. Thaqalayn (`thaqalayn.py`)

- **API endpoint:** `https://thaqalayn.net/api/v2/allbooks`
- **Test result:** HTTP 404 -- API has been removed
- **Root cause:** Thaqalayn.net has been rebuilt as a Next.js application. The REST API v2 is no longer available. The website itself is functional (serving Shia hadith content) but no longer exposes a public API.
- **Fallback:** GitHub clone of `MohammedArab1/ThaqalaynAPI` still works (HEAD: `323cd90`). The downloader code already has this fallback built in -- it will catch the API failure and clone the repo instead.
- **Code review:** Circuit breaker pattern (5 consecutive 5xx errors triggers fallback) works correctly for this scenario. The 404 will be caught by `httpx.HTTPStatusError`, triggering the GitHub fallback.
- **Action needed:** File sub-issue to update the API URL or make GitHub the primary source. The current fallback will work but adds unnecessary latency from failed API attempts.

### 3. Open Hadith Data (`open_hadith.py`)

- **Source:** `https://github.com/mhashim6/Open-Hadith-Data.git`
- **Test result:** Accessible (HEAD: `1515f6cba21efed20d8916bf55acef1dffa0d2d5`)
- **Code review:** Shallow clone, validates >= 9 CSV files, idempotent
- **Verdict:** Healthy, no changes needed.

### 4. LK Hadith Corpus (`lk_corpus.py`)

- **Source:** `https://github.com/ShathaTm/LK-Hadith-Corpus.git`
- **Test result:** Accessible (HEAD: `c45fa64aa40bf1d4a34b9b35359640a583b02881`)
- **Code review:** Shallow clone, validates >= 6 CSV files (Kutub al-Sittah), idempotent
- **Verdict:** Healthy, no changes needed.

### 5. Sanadset / Kaggle (`sanadset.py`)

- **Datasets:** `fahd09/hadith-dataset` (~650K hadiths), `fahd09/hadith-narrators`
- **Test result:** Both return HTTP 404 on Kaggle
- **Root cause:** Datasets have been removed from Kaggle or made private by the owner.
- **Impact:** HIGH -- this is the largest single source (~650K hadiths with SANAD/MATN/NAR XML tags) and the only source of structured narrator biographies. Loss of this dataset significantly reduces narrator resolution capabilities.
- **Code review:** Code structure is correct (Kaggle CLI download, idempotent, row count validation). The `kaggle` CLI package is not currently installed in the environment.
- **Action needed:** File sub-issue to find alternative sources for this data. Options:
  1. Check if the dataset is mirrored on HuggingFace or other platforms
  2. Contact the dataset author (fahd09) to request re-publication
  3. Check Wayback Machine / Google Dataset Search for cached copies
  4. Consider using SanadSet paper citations to find alternate mirrors

### 6. Muhaddithat (`muhaddithat.py`)

- **Source:** `https://github.com/muhaddithat/isnad-datasets.git`
- **Test result:** Accessible (HEAD: `e7946d133a9d1e5b1a543d2921bc96e29702cafb`)
- **Code review:** Shallow clone, validates `hadiths.csv` exists, idempotent
- **Verdict:** Healthy, no changes needed.

### 7. Fawaz Hadith API (`fawaz.py`)

- **Source:** jsdelivr CDN mirror of `fawazahmed0/hadith-api`
- **Test result:**
  - `editions.json`: Accessible, 73 editions across 10 collections (bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah, malik, nawawi, qudsi, dehlawi)
  - `info.json`: Accessible, contains grading metadata for 5,274+ hadiths
- **Code review:** Downloads `eng-*` and `ara-*` editions, validates >= 10 English editions, idempotent with existing file check
- **Verdict:** Healthy, no changes needed.

### 8. Sunnah.com Scraper (`sunnah_scraper.py`)

- **Source:** `https://sunnah.com` (HTML scraping)
- **Test result:** Website accessible, 18 collections visible
- **Target collections:** musnad-ahmad, sunan-darimi, riyadussalihin, adab, shamail, mishkat, bulugh, hisn
- **Code review:** robots.txt compliance check, rate limiting (500ms), resumable progress tracking, CSS selector fallbacks for site redesigns, idempotent
- **Verdict:** Healthy. CSS selectors should be re-validated during first actual scrape run since the site may have updated its markup since selectors were written.

## Risk Summary

| Risk | Severity | Source | Mitigation |
|------|----------|--------|------------|
| Kaggle datasets removed | HIGH | sanadset | Find mirror or alternative dataset; file sub-issue |
| Thaqalayn API removed | MEDIUM | thaqalayn | GitHub fallback works; update to use GitHub as primary |
| Sunnah.com CSS changes | LOW | sunnah_scraper | Selector fallbacks built in; validate on first run |
| API key not configured | LOW | sunnah_api | Expected; document in setup instructions |

## Recommendations

1. **Immediate (blocks Wave 1):**
   - File sub-issue for Sanadset Kaggle dataset removal -- find alternative source
   - Determine if narrator biography data can be sourced elsewhere

2. **Soon (before full pipeline run):**
   - File sub-issue to update Thaqalayn downloader to use GitHub as primary (skip API attempt)
   - Verify `SUNNAH_API_KEY` is valid and not expired

3. **Low priority:**
   - Re-validate sunnah.com CSS selectors during first scrape
   - Install `kaggle` CLI package if/when Kaggle source is restored
