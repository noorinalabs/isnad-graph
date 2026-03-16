export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface Narrator {
  id: string
  name_arabic: string
  name_transliterated: string | null
  kunya: string | null
  nisba: string | null
  birth_year: number | null
  death_year: number | null
  generation: string | null
  reliability_grade: string | null
  sect: string | null
  location: string | null
  in_degree: number | null
  out_degree: number | null
  betweenness_centrality: number | null
  pagerank: number | null
  community_id: number | null
}

export interface TopicTag {
  label: string
  confidence: number
}

export interface Hadith {
  id: string
  collection_id: string
  collection_name: string | null
  book_number: number | null
  hadith_number: string
  text_arabic: string
  text_english: string | null
  grade: string | null
  chapter: string | null
  topics: TopicTag[] | null
  parallels: Hadith[] | null
}

export interface Collection {
  id: string
  name_arabic: string
  name_english: string
  compiler: string | null
  sect: string
  hadith_count: number
}

export interface Chain {
  id: string
  hadith_id: string
  narrators: Narrator[]
  is_complete: boolean
}

export interface SearchResult {
  type: 'narrator' | 'hadith' | 'collection'
  id: string
  label: string
  snippet: string
}

export interface TimelineEvent {
  id: string
  name: string
  year_start: number
  year_end: number | null
  description: string | null
  narrators: { id: string; name: string }[]
}

export interface ParallelPair {
  sunni_hadith: Hadith
  shia_hadith: Hadith
  similarity_score: number
}

export interface GraphNode {
  id: string
  label: string
  community_id: number | null
  type: 'narrator' | 'hadith'
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
}

export interface GraphNetwork {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
