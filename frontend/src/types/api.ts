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
  birth_year: number | null
  death_year: number | null
  generation: string | null
  reliability_grade: string | null
  sect: string | null
  location: string | null
}

export interface Hadith {
  id: string
  collection_id: string
  book_number: number | null
  hadith_number: string
  text_arabic: string
  text_english: string | null
  grade: string | null
  chapter: string | null
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
