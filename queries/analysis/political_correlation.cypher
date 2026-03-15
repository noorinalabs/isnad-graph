// Succession/imamate topic hadiths grouped by narrator's active caliphate period.
// Correlates politically sensitive topics with the historical context in which
// the narrator was active, revealing potential political bias in transmission.
// Mode: Neo4j Browser or application query
// Params: none
MATCH (n:Narrator)-[:NARRATED]->(h:Hadith)
WHERE h.topic_1 = 'succession/imamate'
   OR h.topic_2 = 'succession/imamate'
   OR h.topic_3 = 'succession/imamate'
OPTIONAL MATCH (n)-[:ACTIVE_DURING]->(e:HistoricalEvent)
WITH n, h, e,
     CASE
       WHEN e IS NOT NULL THEN e.name_en
       WHEN n.death_year_ah <= 40 THEN 'Rashidun'
       WHEN n.death_year_ah <= 132 THEN 'Umayyad'
       WHEN n.death_year_ah <= 656 THEN 'Abbasid'
       ELSE 'Unknown'
     END AS period
RETURN period,
       count(DISTINCT h) AS hadith_count,
       count(DISTINCT n) AS narrator_count,
       collect(DISTINCT n.name_en)[..5] AS sample_narrators,
       collect(DISTINCT h.id)[..5] AS sample_hadiths
ORDER BY hadith_count DESC
