"""Phase 4: Graph metrics (centrality, PageRank, Louvain) and topic classification.

This package provides enrichment operations that compute derived properties
on the Neo4j graph using the Graph Data Science (GDS) library.
"""

from src.enrich.metrics import run_metrics
from src.enrich.topics import run_topics

__all__ = ["run_metrics", "run_topics"]
