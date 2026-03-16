import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchParallelPairs } from '../api/client'

export default function ComparativePage() {
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['parallel-pairs', page],
    queryFn: () => fetchParallelPairs(page, 20),
  })

  const totalPages = data ? Math.ceil(data.total / data.limit) : 0

  return (
    <div>
      <h2>Comparative Analysis</h2>
      <p style={{ color: '#666', marginBottom: '1rem' }}>
        Browse cross-sectarian parallel hadith pairs (PARALLEL_OF relationships).
      </p>

      {isLoading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>}

      {data && (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Sunni Hadith</th>
                <th style={{ padding: '0.5rem' }}>Shia Hadith</th>
                <th style={{ padding: '0.5rem' }}>Similarity</th>
                <th style={{ padding: '0.5rem' }}>Variant Type</th>
                <th style={{ padding: '0.5rem' }}>Cross-Sect</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((pair, idx) => (
                <tr
                  key={`${pair.hadith_a_id}-${pair.hadith_b_id}-${idx}`}
                  style={{ borderBottom: '1px solid #eee' }}
                >
                  <td
                    style={{ padding: '0.5rem', cursor: 'pointer', color: '#1a73e8' }}
                    onClick={() => navigate(`/hadiths/${pair.hadith_a_id}`)}
                  >
                    {pair.hadith_a_id}
                    <br />
                    <small style={{ color: '#888' }}>{pair.hadith_a_corpus}</small>
                  </td>
                  <td
                    style={{ padding: '0.5rem', cursor: 'pointer', color: '#1a73e8' }}
                    onClick={() => navigate(`/hadiths/${pair.hadith_b_id}`)}
                  >
                    {pair.hadith_b_id}
                    <br />
                    <small style={{ color: '#888' }}>{pair.hadith_b_corpus}</small>
                  </td>
                  <td style={{ padding: '0.5rem' }}>
                    {pair.similarity_score != null ? (
                      <span
                        style={{
                          background: pair.similarity_score > 0.8 ? '#e6f4ea' : '#fef7e0',
                          padding: '0.15rem 0.4rem',
                          borderRadius: 4,
                          fontSize: '0.875rem',
                        }}
                      >
                        {(pair.similarity_score * 100).toFixed(1)}%
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td style={{ padding: '0.5rem' }}>{pair.variant_type ?? '-'}</td>
                  <td style={{ padding: '0.5rem' }}>{pair.cross_sect ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div
            style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}
          >
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {data.page} of {totalPages}
            </span>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
