// Transmission paths mapped to narrator locations — tracks geographic flow of hadith.
// Shows how traditions moved between cities/regions through the narrator network,
// revealing centers of learning and transmission corridors.
// Mode: Neo4j Browser or application query
// Params: $min_transmissions (default 3)
MATCH (a:Narrator)-[:TRANSMITTED_TO]->(b:Narrator)
WHERE a.death_location_id IS NOT NULL
  AND b.death_location_id IS NOT NULL
MATCH (loc_a:Location {id: a.death_location_id})
MATCH (loc_b:Location {id: b.death_location_id})
WHERE loc_a.id <> loc_b.id
WITH loc_a, loc_b, count(*) AS transmissions
WHERE transmissions >= $min_transmissions
RETURN loc_a.id AS from_location_id,
       loc_a.name_en AS from_location,
       loc_b.id AS to_location_id,
       loc_b.name_en AS to_location,
       transmissions
ORDER BY transmissions DESC
