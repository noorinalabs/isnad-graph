// Louvain communities annotated with aggregate narrator attributes.
// Characterizes each detected community by its dominant generation,
// sect affiliation, geographic center, and trustworthiness distribution.
// Mode: Neo4j Browser or application query
// Params: $min_community_size (default 5)
MATCH (n:Narrator)
WHERE n.community_id IS NOT NULL
WITH n.community_id AS community,
     collect(n) AS members
WHERE size(members) >= $min_community_size
UNWIND members AS m
WITH community,
     size(members) AS community_size,
     m.generation AS gen,
     m.sect_affiliation AS sect,
     m.trustworthiness_consensus AS trust,
     m.death_location_id AS loc
RETURN community,
       count(DISTINCT m) AS member_count,
       collect(DISTINCT gen) AS generations,
       collect(DISTINCT sect) AS sects,
       collect(DISTINCT loc)[..5] AS top_locations,
       collect(DISTINCT trust) AS trust_grades
ORDER BY member_count DESC
