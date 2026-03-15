// Hadiths that exist in both Sunni and Shia corpora via PARALLEL_OF relationships.
// Returns pairs of parallel hadiths with their respective collections and topics,
// enabling cross-sectarian comparison of shared traditions.
// Mode: Neo4j Browser or application query
// Params: $limit (default 100)
MATCH (sunni:Hadith)-[p:PARALLEL_OF]-(shia:Hadith)
WHERE sunni.source_corpus IN ['bukhari', 'muslim', 'abu_dawud', 'tirmidhi', 'nasai', 'ibn_majah']
  AND shia.source_corpus IN ['al_kafi', 'tahdhib', 'istibsar', 'man_la_yahduruhu']
MATCH (sunni)-[:APPEARS_IN]->(sc:Collection)
MATCH (shia)-[:APPEARS_IN]->(shc:Collection)
RETURN sunni.id AS sunni_hadith_id,
       sc.id AS sunni_collection,
       sunni.topic_1 AS sunni_topic,
       shia.id AS shia_hadith_id,
       shc.id AS shia_collection,
       shia.topic_1 AS shia_topic,
       p.similarity_score AS similarity
ORDER BY p.similarity_score DESC
LIMIT $limit
