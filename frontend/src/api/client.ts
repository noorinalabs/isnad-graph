import type {
  PaginatedResponse,
  Narrator,
  Hadith,
  Collection,
  Chain,
  SearchResult,
  TimelineEvent,
  ParallelPair,
  GraphNetwork,
} from '../types/api'

const API_BASE = '/api/v1'

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function fetchNarrators(
  page = 1,
  limit = 20,
  search?: string,
): Promise<PaginatedResponse<Narrator>> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) })
  if (search) params.set('q', search)
  return fetchJson(`${API_BASE}/narrators?${params}`)
}

export async function fetchNarrator(id: string): Promise<Narrator> {
  return fetchJson(`${API_BASE}/narrators/${encodeURIComponent(id)}`)
}

export async function fetchNarratorChains(id: string): Promise<Chain[]> {
  return fetchJson(`${API_BASE}/narrators/${encodeURIComponent(id)}/chains`)
}

export async function fetchHadiths(
  page = 1,
  limit = 20,
): Promise<PaginatedResponse<Hadith>> {
  return fetchJson(`${API_BASE}/hadiths?page=${page}&limit=${limit}`)
}

export async function fetchHadith(id: string): Promise<Hadith> {
  return fetchJson(`${API_BASE}/hadiths/${encodeURIComponent(id)}`)
}

export async function fetchHadithParallels(id: string): Promise<Hadith[]> {
  return fetchJson(`${API_BASE}/hadiths/${encodeURIComponent(id)}/parallels`)
}

export async function fetchCollections(
  page = 1,
  limit = 20,
): Promise<PaginatedResponse<Collection>> {
  return fetchJson(`${API_BASE}/collections?page=${page}&limit=${limit}`)
}

export async function fetchCollection(id: string): Promise<Collection> {
  return fetchJson(`${API_BASE}/collections/${encodeURIComponent(id)}`)
}

export async function fetchCollectionHadiths(
  id: string,
  page = 1,
  limit = 20,
): Promise<PaginatedResponse<Hadith>> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) })
  return fetchJson(`${API_BASE}/collections/${encodeURIComponent(id)}/hadiths?${params}`)
}

export async function fetchTimeline(
  yearStart?: number,
  yearEnd?: number,
): Promise<TimelineEvent[]> {
  const params = new URLSearchParams()
  if (yearStart != null) params.set('year_start', String(yearStart))
  if (yearEnd != null) params.set('year_end', String(yearEnd))
  const qs = params.toString()
  return fetchJson(`${API_BASE}/timeline${qs ? `?${qs}` : ''}`)
}

export async function fetchParallels(
  page = 1,
  limit = 20,
): Promise<PaginatedResponse<ParallelPair>> {
  return fetchJson(`${API_BASE}/parallels?page=${page}&limit=${limit}`)
}

export async function fetchGraphNetwork(
  narratorId: string,
  depth = 1,
): Promise<GraphNetwork> {
  const params = new URLSearchParams({
    narrator_id: narratorId,
    depth: String(depth),
  })
  return fetchJson(`${API_BASE}/graph/network?${params}`)
}

export async function searchAll(
  query: string,
  mode: 'fulltext' | 'semantic' = 'fulltext',
  limit = 20,
): Promise<SearchResult[]> {
  const params = new URLSearchParams({
    q: query,
    mode,
    limit: String(limit),
  })
  return fetchJson(`${API_BASE}/search?${params}`)
}
