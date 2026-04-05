// Hadith count per narrator, broken down by collection and composite grade.
// Useful for identifying prolific narrators and grade distribution per source.
// Mode: Neo4j Browser or application query
// Params: $min_count (default 5) — minimum hadiths to include a narrator
MATCH (n:Narrator)-[:NARRATED]->(h:Hadith)-[:APPEARS_IN]->(c:Collection)
WITH n, c, h.grade_composite AS grade, count(h) AS hadith_count
WHERE hadith_count >= $min_count
RETURN n.id AS narrator_id,
       n.name_en AS name,
       c.id AS collection_id,
       grade,
       hadith_count
ORDER BY hadith_count DESC
