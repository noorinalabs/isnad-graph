// Top-N narrators by betweenness centrality — identifies madār (common-link) narrators
// These are narrators who appear disproportionately often as single points in
// transmission chains, acting as bottlenecks through which many isnads converge.
// Mode: Neo4j Browser or application query
// Params: $limit (default 20)
MATCH (n:Narrator)
WHERE n.betweenness_centrality IS NOT NULL
RETURN n.id AS narrator_id,
       n.name_en AS name,
       n.betweenness_centrality AS betweenness,
       n.pagerank AS pagerank,
       n.community_id AS community_id
ORDER BY n.betweenness_centrality DESC
LIMIT $limit
