import type {
  AdminUser,
  UserUpdateRequest,
  SystemHealth,
  ContentStats,
  UsageAnalytics,
} from '../types/admin'
import type { PaginatedResponse } from '../types/api'

import { API_BASE } from '../config'

const ADMIN_BASE = `${API_BASE}/admin`

async function fetchAdminJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    credentials: 'include',
    headers: { ...init?.headers },
  })
  if (res.status === 401 || res.status === 403) {
    throw new Error('Unauthorized: admin access required')
  }
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function fetchAdminUsers(
  page = 1,
  limit = 20,
  search?: string,
  role?: string,
): Promise<PaginatedResponse<AdminUser>> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) })
  if (search) params.set('search', search)
  if (role) params.set('role', role)
  return fetchAdminJson(`${ADMIN_BASE}/users?${params}`)
}

export async function fetchAdminUser(userId: string): Promise<AdminUser> {
  return fetchAdminJson(`${ADMIN_BASE}/users/${encodeURIComponent(userId)}`)
}

export async function updateAdminUser(
  userId: string,
  body: UserUpdateRequest,
): Promise<AdminUser> {
  return fetchAdminJson(`${ADMIN_BASE}/users/${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  return fetchAdminJson(`${ADMIN_BASE}/health/ready`)
}

export async function fetchContentStats(): Promise<ContentStats> {
  return fetchAdminJson(`${ADMIN_BASE}/stats`)
}

export async function fetchUsageAnalytics(): Promise<UsageAnalytics> {
  return fetchAdminJson(`${ADMIN_BASE}/analytics`)
}
