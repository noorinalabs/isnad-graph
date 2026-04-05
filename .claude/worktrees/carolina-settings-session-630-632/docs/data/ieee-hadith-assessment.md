# IEEE Hadith Dataset Assessment

**Issue:** #578
**Assessed by:** Mei-Lin Chang (Data Scientist)
**Date:** 2026-03-29
**Dataset URL:** https://ieee-dataport.org/documents/hadith-dataset
**DOI:** 10.21227/3bg6-pm63

## Dataset Summary

| Field | Value |
|-------|-------|
| Title | hadith dataset |
| Author | Astried Astried (Universitas Riau) |
| Published | 2026-02-22 |
| Format | CSV (`authentic hadith.csv`) |
| Size | 7.59 MB |
| Access | IEEE DataPort subscription required |
| License/Funding | FRGS/1/2022/ICT02/UKM/02/3 |
| Keywords | authentic hadith |
| Category | Artificial Intelligence |

## Inferred Schema

Based on the dataset description page and related literature, the CSV likely contains:

| Field | Description |
|-------|-------------|
| Hadith text (matn) | The body text of the hadith, likely in Arabic |
| Chain of transmission (isnad) | Narrator chain, possibly as a single text field |
| Source reference | Book name and/or hadith number |
| Authenticity label | Classification label (authentic vs non-authentic) |

The dataset description emphasizes "authenticated Islamic traditions" meeting classical
scholarship standards: continuous chains, morally reliable narrators with precise memory,
and text free from contradiction and hidden defects.

## Size and Scope Estimate

At 7.59 MB for a single CSV, this is a small-to-medium dataset. For comparison:

- A typical hadith record with Arabic matn + isnad + metadata is roughly 500-1500 bytes
- **Estimated record count: ~5,000-15,000 hadiths**
- This aligns with similar datasets in the literature (e.g., the "authentic hadith dataset"
  pattern of ~8,500 hadiths from Sahih al-Bukhari + fabricated samples)

The focus on "authentic" hadiths suggests this is likely drawn from the canonical Sunni
collections (primarily Sahih al-Bukhari and possibly Sahih Muslim), with potential
fabricated/weak hadiths for classification contrast.

## Overlap Analysis with Existing Sources

Our platform currently ingests from 8 sources:

| Source | Coverage | Overlap Risk |
|--------|----------|-------------|
| **sunnah_api** (Sunnah.com) | All 6 canonical Sunni books + extras | **High** -- likely full superset of IEEE authentic hadiths |
| **sunnah_scraper** | Same as above, scraped variant | **High** |
| **lk_corpus** (LK Hadith) | Large multi-collection corpus | **High** |
| **open_hadith** | 9 books including the Six Books | **High** |
| **fawaz** (Kaggle) | Bukhari/Muslim + classification labels | **Very high** -- same use case (classification) |
| **sanadset** | 650K narrator records, chain metadata | **Moderate** -- different focus (narrators vs text) |
| **thaqalayn** | Shia collections | **Low** -- different sectarian scope |
| **muhaddithat** | Female narrator biographical data | **Low** -- different focus |

**Assessment:** The IEEE dataset almost certainly overlaps heavily with our existing Sunni
hadith text sources (sunnah_api, lk_corpus, open_hadith, fawaz). Its primary value
proposition -- authenticity labels for classification -- is already covered by the fawaz
Kaggle dataset and by the grading metadata we ingest from Sunnah.com.

## Unique Value Potential

### Possibly Unique
- Specific authenticity labeling methodology from the author's research
- Potential inclusion of fabricated/weak hadiths for contrastive classification
- Structured isnad field (if parsed into individual narrators rather than raw text)

### Likely Not Unique
- Hadith matn text (covered by 4+ existing sources)
- Source references (covered by sunnah_api, open_hadith)
- Basic authentic/non-authentic labels (covered by fawaz, sunnah_api gradings)

## Access Considerations

- **IEEE DataPort subscription required** -- not freely downloadable
- No open mirror found on Kaggle, HuggingFace, or GitHub
- No associated published paper found for the author that would provide
  detailed schema documentation
- The dataset is very recent (February 2026), so limited community adoption

## Recommendation: SKIP

**Rationale:**

1. **High overlap:** The dataset's scope (authentic Sunni hadiths) is fully covered by
   our existing sources, particularly sunnah_api (comprehensive API with grading metadata)
   and fawaz (Kaggle dataset with classification labels).

2. **Small incremental value:** At ~7.59 MB, this is a fraction of the data we already
   ingest. Even if it contains a structured isnad field, our sanadset source provides
   650K narrator records with far richer chain metadata.

3. **Access friction:** Requiring an IEEE DataPort subscription adds procurement overhead
   and potential licensing constraints for a dataset that is unlikely to provide novel data.

4. **No published methodology:** Without an associated paper describing the collection
   and labeling methodology, we cannot assess data quality or verify that the authenticity
   labels follow a rigorous standard compatible with our existing grading taxonomy.

5. **No community adoption:** Published February 2026 with no citations or community
   usage yet, making it difficult to validate independently.

### If Revisited Later

Should the dataset prove to contain genuinely novel content (e.g., if a paper is published
revealing unique narrator disambiguation or structured isnad parsing), a downloader would
need:

- IEEE DataPort API or manual download authentication
- CSV parser mapping columns to our staging Parquet schema
- Deduplication against existing sunnah_api and fawaz records
- Isnad text parsing if the chain field is unstructured

**Action:** Close issue #578 as not-planned.
