# Resolve Module Profiling Report

**Date:** 2026-03-29
**Author:** Elena Petrova (Staff Data Engineer)
**Issue:** #529
**Environment:** Linux (WSL2), Python 3.14.3, CPU-only (no GPU), faiss-cpu, sentence-transformers

## Executive Summary

The resolve module (Phase 2: Entity Resolution) has three pipeline steps with dramatically different resource profiles. **Dedup is the dominant bottleneck** -- it accounts for >90% of wall-clock time and >85% of peak memory due to sentence-transformer model loading and FAISS index construction. NER and disambiguation are lightweight and scale linearly.

For a full 8-source production run, estimated total time is ~60 seconds with ~350 MB peak memory on CPU. This is well within a single-machine budget and does not require distributed processing.

## Per-Step Timing

All measurements use synthetic data with `tracemalloc` for memory and `time.monotonic` for wall-clock. Dedup at scale=100 includes one-time model load (~18s); subsequent runs amortize this.

| Step | Scale (narrators/hadiths) | Wall Time (s) | Peak Memory (MB) |
|------|--------------------------|---------------|-------------------|
| **NER** | 100 / 200 | 0.038 | 0.96 |
| **NER** | 1,000 / 2,000 | 0.230 | 2.31 |
| **NER** | 5,000 / 10,000 | 1.239 | 10.34 |
| **Disambiguate** | 100 / 200 | 0.023 | 0.08 |
| **Disambiguate** | 1,000 / 2,000 | 0.224 | 0.69 |
| **Disambiguate** | 5,000 / 10,000 | 1.206 | 3.46 |
| **Dedup** | 100 / 200 | 21.208* | 290.87 |
| **Dedup** | 1,000 / 2,000 | 5.130 | 76.67 |
| **Dedup** | 5,000 / 10,000 | 12.631 | 78.58 |

\* Dedup at scale 100 includes ~18s one-time SentenceTransformer model download/load. Warm-cache runs at that scale would be ~3s.

### Scaling characteristics

- **NER:** Linear in hadith count. ~0.12ms per hadith. Rule-based regex extraction, no ML inference.
- **Disambiguate:** O(mentions x candidates). At 5,000 candidates x ~36,000 mentions, runs in ~1.2s. Fuzzy matching (rapidfuzz) is C-optimized and fast. Scales quadratically in theory but the constant is small.
- **Dedup:** Dominated by SentenceTransformer `model.encode()`. Embedding generation is ~0.5ms/hadith on CPU. FAISS IndexFlatIP search is O(n x k x d) but completes in <3s even at 10k vectors.

## FAISS Index Size on Disk

The embedding dimension is 384 (paraphrase-multilingual-MiniLM-L12-v2). Each vector = 384 x 4 bytes = 1,536 bytes.

| Hadiths | FAISS Index (MB) | Embeddings .npy (MB) | Total Disk (MB) |
|---------|-----------------|---------------------|-----------------|
| 200 | 0.29 | 0.29 | 0.58 |
| 2,000 | 2.93 | 2.93 | 5.86 |
| 10,000 | 14.65 | 14.65 | 29.30 |
| **40,000 (est.)** | **~59** | **~59** | **~117** |

The index scales linearly at ~1.5 KB/vector for IndexFlatIP (uncompressed). At 40k hadiths (8-source full run estimate), total disk footprint is ~117 MB -- manageable.

For larger datasets (>100k hadiths), switching to `IndexIVFFlat` would reduce search time at the cost of slightly lower recall. The code already supports this via the `index_type="ivf"` parameter.

## Concurrent vs Sequential Source Processing

Measured with NER on 3 sources x 500 narrators (1,000 hadiths each):

| Mode | Wall Time (s) | Peak Memory (MB) |
|------|--------------|-------------------|
| Sequential (3 sources) | 0.520 | 2.31 |
| Concurrent estimate (3 sources) | 0.208 | 6.23 |

**Memory multiplier for concurrent:** ~2.7x (each process holds its own Parquet tables + intermediate lists).

**Conclusion:** NER is embarrassingly parallel per source. Concurrent processing gives ~2.5x speedup but at ~3x memory cost. At current data sizes, sequential is fine -- the total NER time even at 8 sources is <5 seconds.

## 8-Source Full Run Projections

Based on 5,000-scale measurements, extrapolating to 8 sources (4x scale factor from the 2-source benchmark):

| Step | Projected Wall Time (s) | Projected Peak Memory (MB) |
|------|------------------------|---------------------------|
| NER | ~5 | ~41 |
| Disambiguate | ~5 | ~14 |
| Dedup (warm model) | ~50 | ~314 |
| Dedup (cold model start) | ~68 | ~314 |
| **Total** | **~60-78** | **~350** |

**Disk artifacts:** ~117 MB (FAISS index + embeddings + Parquet outputs)

## Bottleneck Identification

### Primary bottleneck: Dedup embedding generation

- **What:** `SentenceTransformer.encode()` accounts for ~80% of total pipeline time
- **Why:** CPU-bound transformer inference, no GPU acceleration
- **Impact:** Dominates end-to-end latency at any meaningful scale

### Secondary bottleneck: Dedup model load

- **What:** First-time `SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")` download
- **Why:** ~90 MB model download + tokenizer initialization
- **Impact:** ~18s one-time cost, cached on subsequent runs

### Non-bottlenecks

- **NER:** <2s even at 10k hadiths. Pure regex, no ML. Not worth optimizing.
- **Disambiguate:** <2s even at 5k candidates x 36k mentions. rapidfuzz is C-optimized. The O(m*c) loop could be optimized with indexing but is not worth it at current scale.
- **FAISS search:** <3s at 10k vectors. IndexFlatIP is brute-force but sufficient up to ~100k vectors.

## Recommendations

### Must-have (before full E2E run)

1. **Pre-download SentenceTransformer model** -- add `model.save()` to setup or Docker image build so the first run doesn't pay the download penalty. The model is cached at `~/.cache/torch/sentence_transformers/`.

2. **Set memory limit for dedup worker** -- peak memory of ~350 MB is reasonable, but add a `--max-memory` guard (e.g., via `resource.setrlimit`) to prevent OOM on constrained environments. The Docker container should allocate at least 1 GB for the resolve pipeline.

3. **Validate with real data sample** -- synthetic data has low text diversity (5 matns). Real hadith texts are longer and more varied, which will increase embedding time by an estimated 1.5-2x. Run `scripts/sample_real_data.py` to extract a representative sample for validation.

### Nice-to-have (optimization opportunities)

4. **GPU acceleration for dedup** -- if a CUDA-capable GPU is available, `model.encode(device="cuda")` would reduce embedding time by ~10x. Not required for current dataset sizes.

5. **Batch-parallel embedding generation** -- `model.encode()` already accepts `batch_size`. Current default (256) is reasonable for CPU. On GPU, increase to 512-1024.

6. **IVF index for >50k hadiths** -- switch `index_type="ivf"` to trade ~2% recall for ~5x search speedup. The code already supports this.

7. **NER source parallelism** -- use `multiprocessing.Pool` for NER across sources. Saves ~3s on an 8-source run (from ~5s to ~2s). Low priority given the small absolute saving.

8. **Disambiguate candidate indexing** -- build a trie or hash index on `name_ar_normalized` to avoid O(candidates) scan per mention. Would reduce disambiguate time from ~5s to <1s at 8-source scale. Low priority.

## Profiling Script

The profiling script is at `scripts/profile_resolve.py`. Run with:

```bash
uv run python scripts/profile_resolve.py
```

Raw JSON data is written to `docs/data/resolve-profiling-data.json`.

## Follow-up Issues

- [ ] Pre-download SentenceTransformer model in Docker image build
- [ ] Add `--max-memory` guard for resolve pipeline
- [ ] Validate profiling with real data sample after Phase 1 acquisition
