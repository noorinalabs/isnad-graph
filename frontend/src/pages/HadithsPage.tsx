import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchHadiths } from '../api/client'

export default function HadithsPage() {
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['hadiths', page],
    queryFn: () => fetchHadiths(page, 20),
  })

  return (
    <div>
      <h2>Hadiths</h2>

      {isLoading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>}

      {data && (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Collection</th>
                <th style={{ padding: '0.5rem' }}>Number</th>
                <th style={{ padding: '0.5rem' }}>Grade</th>
                <th style={{ padding: '0.5rem' }}>Topics</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((h) => (
                <tr
                  key={h.id}
                  onClick={() => navigate(`/hadiths/${h.id}`)}
                  style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                >
                  <td style={{ padding: '0.5rem' }}>{h.collection_name ?? h.collection_id}</td>
                  <td style={{ padding: '0.5rem' }}>{h.hadith_number}</td>
                  <td style={{ padding: '0.5rem' }}>
                    {h.grade && (
                      <span
                        style={{
                          padding: '0.15rem 0.5rem',
                          borderRadius: 4,
                          fontSize: '0.85rem',
                          background: h.grade.toLowerCase() === 'sahih' ? '#e6f4ea' : '#fef7e0',
                          color: h.grade.toLowerCase() === 'sahih' ? '#137333' : '#b06000',
                        }}
                      >
                        {h.grade}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.5rem' }}>
                    {h.topics?.map((t) => (
                      <span
                        key={t.label}
                        style={{
                          display: 'inline-block',
                          marginRight: '0.25rem',
                          padding: '0.1rem 0.4rem',
                          borderRadius: 3,
                          fontSize: '0.8rem',
                          background: '#e8eaf6',
                          color: '#283593',
                        }}
                      >
                        {t.label}
                      </span>
                    ))}
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
