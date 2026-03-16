import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchCollection, fetchCollectionHadiths } from '../api/client'

export default function CollectionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [page, setPage] = useState(1)

  const {
    data: collection,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['collection', id],
    queryFn: () => fetchCollection(id!),
    enabled: !!id,
  })

  const { data: hadiths } = useQuery({
    queryKey: ['collection-hadiths', id, page],
    queryFn: () => fetchCollectionHadiths(id!, page, 20),
    enabled: !!id,
  })

  if (isLoading) return <p>Loading...</p>
  if (error) return <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>
  if (!collection) return <p>Collection not found.</p>

  const isSunni = collection.sect.toLowerCase() === 'sunni'

  return (
    <div>
      <Link to="/collections" style={{ color: '#1a73e8' }}>
        &larr; Back to Collections
      </Link>

      <h2 style={{ marginTop: '1rem' }}>
        {collection.name_english}
        <span
          style={{
            marginLeft: '0.75rem',
            padding: '0.15rem 0.5rem',
            borderRadius: 4,
            fontSize: '0.9rem',
            fontWeight: 600,
            background: isSunni ? '#e8f5e9' : '#e3f2fd',
            color: isSunni ? '#2e7d32' : '#1565c0',
          }}
        >
          {collection.sect}
        </span>
      </h2>

      <p style={{ direction: 'rtl', textAlign: 'right', fontSize: '1.1rem', color: '#555' }}>
        {collection.name_arabic}
      </p>

      <div style={{ color: '#666', marginBottom: '1.5rem' }}>
        {collection.compiler && <span>Compiler: {collection.compiler}</span>}
        {collection.compiler && <span style={{ margin: '0 0.5rem' }}>|</span>}
        <span>{collection.hadith_count.toLocaleString()} hadiths</span>
      </div>

      {hadiths && (
        <>
          <h3>Hadiths</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Number</th>
                <th style={{ padding: '0.5rem' }}>Chapter</th>
                <th style={{ padding: '0.5rem' }}>Grade</th>
              </tr>
            </thead>
            <tbody>
              {hadiths.items.map((h) => (
                <tr key={h.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.5rem' }}>
                    <Link to={`/hadiths/${h.id}`} style={{ color: '#1a73e8' }}>
                      #{h.hadith_number}
                    </Link>
                  </td>
                  <td style={{ padding: '0.5rem' }}>{h.chapter ?? '-'}</td>
                  <td style={{ padding: '0.5rem' }}>{h.grade ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {hadiths.page} of {hadiths.pages}
            </span>
            <button disabled={page >= hadiths.pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
