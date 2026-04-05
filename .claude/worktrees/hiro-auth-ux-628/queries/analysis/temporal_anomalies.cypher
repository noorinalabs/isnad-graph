// Chains where narrator death dates make transmission impossible.
// A narrator who died before the next narrator in the chain was born
// cannot have transmitted to them, indicating a broken or fabricated chain.
// Mode: Neo4j Browser or application query
// Params: none
MATCH (a:Narrator)-[:TRANSMITTED_TO]->(b:Narrator)
WHERE a.death_year_ah IS NOT NULL
  AND b.birth_year_ah IS NOT NULL
  AND a.death_year_ah < b.birth_year_ah
RETURN a.id AS transmitter_id,
       a.name_en AS transmitter_name,
       a.death_year_ah AS transmitter_death,
       b.id AS receiver_id,
       b.name_en AS receiver_name,
       b.birth_year_ah AS receiver_birth,
       (b.birth_year_ah - a.death_year_ah) AS gap_years
ORDER BY gap_years DESC
