"""Profile the resolve module (NER, disambiguation, dedup) at varying scales.

Generates synthetic data at 100/1000/5000 narrator scales, measures wall-clock
time, peak memory (tracemalloc), and FAISS index size on disk. Reports whether
each step is parallelizable per source and estimates 8-source full-run costs.

Usage:
    uv run python scripts/profile_resolve.py
"""

from __future__ import annotations

import json
import tempfile
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

_ARABIC_NAMES = [
    "عبد الله بن عمر",
    "أبو هريرة",
    "عائشة بنت أبي بكر",
    "أنس بن مالك",
    "جابر بن عبد الله",
    "ابن عباس",
    "علي بن أبي طالب",
    "سعيد بن المسيب",
    "الزهري",
    "مالك بن أنس",
    "سفيان الثوري",
    "شعبة بن الحجاج",
    "أبو بكر الصديق",
    "عمر بن الخطاب",
    "عثمان بن عفان",
    "طلحة بن عبيد الله",
    "الحسن البصري",
    "قتادة بن دعامة",
    "ابراهيم النخعي",
    "عبد الرحمن بن مهدي",
]

_ENGLISH_NAMES = [
    "Abdullah ibn Umar",
    "Abu Hurayrah",
    "Aisha bint Abi Bakr",
    "Anas ibn Malik",
    "Jabir ibn Abdullah",
    "Ibn Abbas",
    "Ali ibn Abi Talib",
    "Said ibn al-Musayyab",
    "al-Zuhri",
    "Malik ibn Anas",
    "Sufyan al-Thawri",
    "Shuba ibn al-Hajjaj",
    "Abu Bakr al-Siddiq",
    "Umar ibn al-Khattab",
    "Uthman ibn Affan",
    "Talha ibn Ubaydullah",
    "al-Hasan al-Basri",
    "Qatada ibn Diama",
    "Ibrahim al-Nakhai",
    "Abd al-Rahman ibn Mahdi",
]

_CORPORA = ["sanadset", "lk", "thaqalayn", "sunnah", "fawaz", "open_hadith"]

_SAMPLE_MATNS = [
    "The Prophet said: Actions are judged by intentions.",
    "He who believes in Allah and the Last Day should speak good or keep silent.",
    "None of you truly believes until he loves for his brother what he loves for himself.",
    "The strong man is not the one who can overpower others, but the one who controls himself.",
    "Leave that which makes you doubt for that which does not make you doubt.",
]


def _gen_narrator_bio(i: int) -> dict:
    """Generate a single synthetic narrator bio record."""
    rng = np.random.default_rng(seed=i)
    name_idx = i % len(_ARABIC_NAMES)
    suffix = f"_{i}" if i >= len(_ARABIC_NAMES) else ""
    return {
        "bio_id": f"bio_{i:06d}",
        "name_ar": _ARABIC_NAMES[name_idx] + suffix,
        "name_en": _ENGLISH_NAMES[name_idx] + suffix,
        "name_ar_normalized": _ARABIC_NAMES[name_idx] + suffix,
        "kunya": None,
        "nisba": None,
        "birth_year_ah": int(rng.integers(1, 200)),
        "death_year_ah": int(rng.integers(50, 300)),
        "birth_location": None,
        "death_location": None,
        "generation": f"gen_{i % 12}",
        "gender": "male" if rng.random() > 0.15 else "female",
        "trustworthiness": "thiqa" if rng.random() > 0.3 else "daif",
        "external_id": f"ext_{i}" if rng.random() > 0.5 else None,
        "source": "synthetic",
    }


def _gen_hadiths(n: int, corpus: str) -> list[dict]:
    """Generate n synthetic hadith records for a given corpus."""
    rng = np.random.default_rng(seed=hash(corpus) & 0xFFFFFFFF)
    rows = []
    for i in range(n):
        chain_len = int(rng.integers(2, 6))
        names = [_ARABIC_NAMES[int(rng.integers(0, len(_ARABIC_NAMES)))] for _ in range(chain_len)]
        isnad = " عن ".join(names)
        matn_idx = int(rng.integers(0, len(_SAMPLE_MATNS)))
        rows.append(
            {
                "source_id": f"{corpus}_{i:06d}",
                "source_corpus": corpus,
                "isnad_raw_ar": isnad,
                "isnad_raw_en": None,
                "full_text_ar": isnad + " قال رسول الله: " + _SAMPLE_MATNS[matn_idx],
                "full_text_en": None,
                "matn_en": _SAMPLE_MATNS[matn_idx] + f" (variant {i})",
            }
        )
    return rows


def _write_bio_parquet(bios: list[dict], staging_dir: Path) -> None:
    """Write narrators_bio_synthetic.parquet."""
    table = pa.table(
        {
            "bio_id": [b["bio_id"] for b in bios],
            "name_ar": [b["name_ar"] for b in bios],
            "name_en": [b["name_en"] for b in bios],
            "name_ar_normalized": [b["name_ar_normalized"] for b in bios],
            "kunya": [b["kunya"] for b in bios],
            "nisba": [b["nisba"] for b in bios],
            "birth_year_ah": pa.array([b["birth_year_ah"] for b in bios], type=pa.int32()),
            "death_year_ah": pa.array([b["death_year_ah"] for b in bios], type=pa.int32()),
            "birth_location": [b["birth_location"] for b in bios],
            "death_location": [b["death_location"] for b in bios],
            "generation": [b["generation"] for b in bios],
            "gender": [b["gender"] for b in bios],
            "trustworthiness": [b["trustworthiness"] for b in bios],
            "external_id": [b["external_id"] for b in bios],
            "source": [b["source"] for b in bios],
        }
    )
    pq.write_table(table, staging_dir / "narrators_bio_synthetic.parquet")


def _write_hadith_parquet(hadiths: list[dict], corpus: str, staging_dir: Path) -> None:
    """Write hadiths_{corpus}.parquet."""
    table = pa.table(
        {
            "source_id": [h["source_id"] for h in hadiths],
            "source_corpus": [h["source_corpus"] for h in hadiths],
            "isnad_raw_ar": [h["isnad_raw_ar"] for h in hadiths],
            "isnad_raw_en": [h["isnad_raw_en"] for h in hadiths],
            "full_text_ar": [h["full_text_ar"] for h in hadiths],
            "full_text_en": [h["full_text_en"] for h in hadiths],
            "matn_en": [h["matn_en"] for h in hadiths],
        }
    )
    pq.write_table(table, staging_dir / f"hadiths_{corpus}.parquet")


# ---------------------------------------------------------------------------
# Profiling helpers
# ---------------------------------------------------------------------------


@dataclass
class StepResult:
    """Timing and memory for a single profiled step."""

    name: str
    scale: int
    wall_seconds: float
    peak_memory_mb: float
    extra: dict = field(default_factory=dict)


def _profile_step(name: str, scale: int, fn, *args, **kwargs) -> StepResult:
    """Time a callable and measure peak memory with tracemalloc."""
    tracemalloc.start()
    t0 = time.monotonic()
    result = fn(*args, **kwargs)
    elapsed = time.monotonic() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return StepResult(
        name=name,
        scale=scale,
        wall_seconds=round(elapsed, 3),
        peak_memory_mb=round(peak / (1024 * 1024), 2),
        extra=result if isinstance(result, dict) else {},
    )


# ---------------------------------------------------------------------------
# Individual step profilers
# ---------------------------------------------------------------------------


def _profile_ner(staging_dir: Path, output_dir: Path, scale: int) -> StepResult:
    """Profile the NER step."""
    from src.resolve import ner

    def _run():
        return ner.run(staging_dir, output_dir)

    # We need to handle that ner.run expects specific source files.
    # For synthetic data, the extraction will use thaqalayn (Arabic source).
    return _profile_step("ner", scale, _run)


def _profile_disambiguate(staging_dir: Path, output_dir: Path, scale: int) -> StepResult:
    """Profile the disambiguation step."""
    from src.resolve import disambiguate

    def _run():
        return disambiguate.run(staging_dir, output_dir)

    return _profile_step("disambiguate", scale, _run)


def _profile_dedup(staging_dir: Path, scale: int) -> StepResult:
    """Profile the dedup step (FAISS + sentence-transformers)."""
    from src.resolve.dedup import run_dedup

    def _run():
        run_dedup(staging_dir, batch_size=64, top_k=10, threshold=0.70)
        extra = {}
        # Measure FAISS index size
        faiss_path = staging_dir / "hadith_embeddings.faiss"
        if faiss_path.exists():
            extra["faiss_index_bytes"] = faiss_path.stat().st_size
            extra["faiss_index_mb"] = round(faiss_path.stat().st_size / (1024 * 1024), 2)
        npy_path = staging_dir / "hadith_embeddings.npy"
        if npy_path.exists():
            extra["embeddings_bytes"] = npy_path.stat().st_size
            extra["embeddings_mb"] = round(npy_path.stat().st_size / (1024 * 1024), 2)
        return extra

    return _profile_step("dedup", scale, _run)


def _profile_concurrent_sources(
    n_narrators: int, n_hadiths_per_source: int, sources: list[str]
) -> dict[str, StepResult]:
    """Profile sequential vs concurrent (multiprocessing) source processing for NER."""

    results: dict[str, StepResult] = {}

    # Create per-source staging dirs
    tmpdir = tempfile.mkdtemp(prefix="resolve_concurrent_")
    source_dirs = {}
    for corpus in sources:
        sdir = Path(tmpdir) / corpus / "staging"
        odir = Path(tmpdir) / corpus / "output"
        sdir.mkdir(parents=True, exist_ok=True)
        odir.mkdir(parents=True, exist_ok=True)

        bios = [_gen_narrator_bio(i) for i in range(n_narrators)]
        _write_bio_parquet(bios, sdir)
        hadiths = _gen_hadiths(n_hadiths_per_source, corpus)
        _write_hadith_parquet(hadiths, corpus, sdir)
        source_dirs[corpus] = (sdir, odir)

    # Sequential
    tracemalloc.start()
    t0 = time.monotonic()
    for corpus in sources:
        sdir, odir = source_dirs[corpus]
        from src.resolve import ner

        ner.run(sdir, odir)
    seq_elapsed = time.monotonic() - t0
    _, seq_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results["sequential"] = StepResult(
        name="ner_sequential",
        scale=n_narrators * len(sources),
        wall_seconds=round(seq_elapsed, 3),
        peak_memory_mb=round(seq_peak / (1024 * 1024), 2),
    )

    # Note: true multiprocessing profiling is limited inside tracemalloc
    # (only tracks main process). We estimate based on sequential per-source times.
    per_source_time = seq_elapsed / len(sources)
    results["concurrent_estimate"] = StepResult(
        name="ner_concurrent_estimate",
        scale=n_narrators * len(sources),
        wall_seconds=round(per_source_time * 1.2, 3),  # ~20% overhead estimate
        peak_memory_mb=round(seq_peak / (1024 * 1024) * len(sources) * 0.9, 2),
        extra={
            "note": "Estimated: wall ~= single-source + 20% overhead; "
            "memory ~= N * per-source * 0.9"
        },
    )

    return results


# ---------------------------------------------------------------------------
# Main profiling loop
# ---------------------------------------------------------------------------


def _setup_synthetic(n_narrators: int, n_hadiths: int, tmpdir: str) -> tuple[Path, Path]:
    """Create synthetic staging data for a given scale."""
    staging = Path(tmpdir) / "staging"
    output = Path(tmpdir) / "output"
    staging.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)

    bios = [_gen_narrator_bio(i) for i in range(n_narrators)]
    _write_bio_parquet(bios, staging)

    # Generate hadiths across 2 corpora (thaqalayn for Arabic, sunnah for English)
    for corpus in ["thaqalayn", "sunnah"]:
        hadiths = _gen_hadiths(n_hadiths // 2, corpus)
        _write_hadith_parquet(hadiths, corpus, staging)

    return staging, output


def main() -> None:
    scales = [
        (100, 200),  # 100 narrators, 200 hadiths
        (1000, 2000),  # 1000 narrators, 2000 hadiths
        (5000, 10000),  # 5000 narrators, 10000 hadiths
    ]

    all_results: list[StepResult] = []

    print("=" * 70)
    print("RESOLVE MODULE PROFILING")
    print("=" * 70)

    for n_narrators, n_hadiths in scales:
        print(f"\n--- Scale: {n_narrators} narrators, {n_hadiths} hadiths ---")

        with tempfile.TemporaryDirectory(prefix=f"resolve_profile_{n_narrators}_") as tmpdir:
            staging, output = _setup_synthetic(n_narrators, n_hadiths, tmpdir)

            # NER
            r = _profile_ner(staging, output, n_narrators)
            all_results.append(r)
            print(f"  NER:            {r.wall_seconds:>8.3f}s  |  {r.peak_memory_mb:>8.2f} MB peak")

            # Disambiguation (needs NER output)
            r = _profile_disambiguate(staging, output, n_narrators)
            all_results.append(r)
            print(f"  Disambiguate:   {r.wall_seconds:>8.3f}s  |  {r.peak_memory_mb:>8.2f} MB peak")

            # Dedup (independent of NER/disambig)
            r = _profile_dedup(staging, n_narrators)
            all_results.append(r)
            faiss_mb = r.extra.get("faiss_index_mb", "N/A")
            embed_mb = r.extra.get("embeddings_mb", "N/A")
            print(f"  Dedup:          {r.wall_seconds:>8.3f}s  |  {r.peak_memory_mb:>8.2f} MB peak")
            print(f"    FAISS index:  {faiss_mb} MB on disk")
            print(f"    Embeddings:   {embed_mb} MB on disk")

    # Concurrent vs sequential profiling
    print("\n--- Concurrent vs Sequential (NER, 3 sources x 500 narrators) ---")
    conc_results = _profile_concurrent_sources(500, 1000, ["thaqalayn", "sunnah", "open_hadith"])
    for label, r in conc_results.items():
        note = r.extra.get("note", "")
        print(f"  {label:25s}: {r.wall_seconds:>8.3f}s  |  {r.peak_memory_mb:>8.2f} MB peak")
        if note:
            print(f"    {note}")
        all_results.append(r)

    # Projections for 8-source full run
    print("\n" + "=" * 70)
    print("8-SOURCE FULL RUN PROJECTIONS")
    print("=" * 70)

    # Use 5000-scale results for projection
    scale_5k = [r for r in all_results if r.scale == 5000]
    if scale_5k:
        ner_5k = next((r for r in scale_5k if r.name == "ner"), None)
        dis_5k = next((r for r in scale_5k if r.name == "disambiguate"), None)
        ded_5k = next((r for r in scale_5k if r.name == "dedup"), None)

        # 8 sources => ~4x hadiths (5k was 2 sources)
        scale_factor = 4.0
        if ner_5k:
            t = ner_5k.wall_seconds * scale_factor
            m = ner_5k.peak_memory_mb * scale_factor
            print(f"  NER (8 sources):       ~{t:.1f}s wall, ~{m:.0f} MB peak")
        if dis_5k:
            t = dis_5k.wall_seconds * scale_factor
            m = dis_5k.peak_memory_mb * scale_factor
            print(f"  Disambiguate (8 src):  ~{t:.1f}s wall, ~{m:.0f} MB peak")
        if ded_5k:
            t = ded_5k.wall_seconds * scale_factor
            m = ded_5k.peak_memory_mb * scale_factor
            print(f"  Dedup (8 src):         ~{t:.1f}s wall, ~{m:.0f} MB peak")
            faiss_proj = (ded_5k.extra.get("faiss_index_mb", 0) or 0) * scale_factor
            embed_proj = (ded_5k.extra.get("embeddings_mb", 0) or 0) * scale_factor
            print(f"  FAISS index (8 src):   ~{faiss_proj:.1f} MB on disk")
            print(f"  Embeddings (8 src):    ~{embed_proj:.1f} MB on disk")

    # Write JSON results for programmatic consumption
    results_path = Path(__file__).parent.parent / "docs" / "data" / "resolve-profiling-data.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    json_data = []
    for r in all_results:
        json_data.append(
            {
                "name": r.name,
                "scale": r.scale,
                "wall_seconds": r.wall_seconds,
                "peak_memory_mb": r.peak_memory_mb,
                "extra": r.extra,
            }
        )
    with open(results_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"\nRaw data written to {results_path}")

    # Summary of parallelization potential
    print("\n" + "=" * 70)
    print("PARALLELIZATION ANALYSIS")
    print("=" * 70)
    print("  NER:           Per-source parallelizable (reads its own Parquet)")
    print("  Disambiguate:  NOT easily parallelizable (all mentions + candidates)")
    print("                 Could shard by corpus but temporal filter needs chains")
    print("  Dedup:         NOT parallelizable (global FAISS index needed)")
    print("                 Embedding gen is batch-parallelizable (GPU/MP)")


if __name__ == "__main__":
    main()
