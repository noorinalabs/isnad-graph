import type { PaginatedResponse, Narrator, Hadith, Collection, SearchResult } from '../types/api'

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
): Promise<PaginatedResponse<Narrator>> {
  return fetchJson(`${API_BASE}/narrators?page=${page}&limit=${limit}`)
}

export async function fetchNarrator(id: string): Promise<Narrator> {
  return fetchJson(`${API_BASE}/narrators/${encodeURIComponent(id)}`)
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

export async function fetchCollections(
  page = 1,
  limit = 20,
): Promise<PaginatedResponse<Collection>> {
  return fetchJson(`${API_BASE}/collections?page=${page}&limit=${limit}`)
}

export async function fetchCollection(id: string): Promise<Collection> {
  return fetchJson(`${API_BASE}/collections/${encodeURIComponent(id)}`)
}

export async function searchAll(
  query: string,
  limit = 20,
): Promise<SearchResult[]> {
  return fetchJson(
    `${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  )
}
