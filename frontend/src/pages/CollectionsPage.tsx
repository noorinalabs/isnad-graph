import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchCollections } from '../api/client'

export default function CollectionsPage() {
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['collections', page],
    queryFn: () => fetchCollections(page, 20),
  })

  const sectBadge = (sect: string) => {
    const isSunni = sect.toLowerCase() === 'sunni'
    return {
      background: isSunni ? '#e8f5e9' : '#e3f2fd',
      color: isSunni ? '#2e7d32' : '#1565c0',
      padding: '0.15rem 0.5rem',
      borderRadius: 4,
      fontSize: '0.85rem',
      fontWeight: 600 as const,
    }
  }

  return (
    <div>
      <h2>Collections</h2>

      {isLoading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>}

      {data && (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Name (Arabic)</th>
                <th style={{ padding: '0.5rem' }}>Name (English)</th>
                <th style={{ padding: '0.5rem' }}>Compiler</th>
                <th style={{ padding: '0.5rem' }}>Sect</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Hadiths</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => navigate(`/collections/${c.id}`)}
                  style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                >
                  <td style={{ padding: '0.5rem', direction: 'rtl' }}>{c.name_arabic}</td>
                  <td style={{ padding: '0.5rem' }}>{c.name_english}</td>
                  <td style={{ padding: '0.5rem' }}>{c.compiler ?? '-'}</td>
                  <td style={{ padding: '0.5rem' }}>
                    <span style={sectBadge(c.sect)}>{c.sect}</span>
                  </td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>
                    {c.hadith_count.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {data.page} of {data.pages}
            </span>
            <button disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
