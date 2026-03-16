import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchHadith, fetchHadithParallels } from '../api/client'

export default function HadithDetailPage() {
  const { id } = useParams<{ id: string }>()

  const {
    data: hadith,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['hadith', id],
    queryFn: () => fetchHadith(id!),
    enabled: !!id,
  })

  const { data: parallels } = useQuery({
    queryKey: ['hadith-parallels', id],
    queryFn: () => fetchHadithParallels(id!),
    enabled: !!id,
  })

  if (isLoading) return <p>Loading...</p>
  if (error) return <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>
  if (!hadith) return <p>Hadith not found.</p>

  return (
    <div>
      <Link to="/hadiths" style={{ color: '#1a73e8' }}>
        &larr; Back to Hadiths
      </Link>

      <h2 style={{ marginTop: '1rem' }}>
        {hadith.collection_name ?? hadith.collection_id} #{hadith.hadith_number}
      </h2>

      {hadith.grade && (
        <span
          style={{
            display: 'inline-block',
            padding: '0.2rem 0.6rem',
            borderRadius: 4,
            fontSize: '0.9rem',
            background: hadith.grade.toLowerCase() === 'sahih' ? '#e6f4ea' : '#fef7e0',
            color: hadith.grade.toLowerCase() === 'sahih' ? '#137333' : '#b06000',
            marginBottom: '1rem',
          }}
        >
          {hadith.grade}
        </span>
      )}

      <section style={{ marginTop: '1.5rem' }}>
        <h3>Matn (Arabic)</h3>
        <div
          style={{
            direction: 'rtl',
            textAlign: 'right',
            padding: '1rem',
            background: '#fafafa',
            borderRadius: 4,
            lineHeight: 1.8,
            fontSize: '1.1rem',
          }}
        >
          {hadith.text_arabic}
        </div>
      </section>

      {hadith.text_english && (
        <section style={{ marginTop: '1.5rem' }}>
          <h3>English Translation</h3>
          <div
            style={{
              padding: '1rem',
              background: '#fafafa',
              borderRadius: 4,
              lineHeight: 1.6,
            }}
          >
            {hadith.text_english}
          </div>
        </section>
      )}

      {hadith.topics && hadith.topics.length > 0 && (
        <section style={{ marginTop: '1.5rem' }}>
          <h3>Topics</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {hadith.topics.map((t) => (
              <span
                key={t.label}
                style={{
                  padding: '0.3rem 0.6rem',
                  borderRadius: 4,
                  background: '#e8eaf6',
                  color: '#283593',
                  fontSize: '0.9rem',
                }}
              >
                {t.label}{' '}
                <span style={{ color: '#666', fontSize: '0.8rem' }}>
                  ({(t.confidence * 100).toFixed(0)}%)
                </span>
              </span>
            ))}
          </div>
        </section>
      )}

      {parallels && parallels.length > 0 && (
        <section style={{ marginTop: '1.5rem' }}>
          <h3>Parallel Hadiths ({parallels.length})</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Collection</th>
                <th style={{ padding: '0.5rem' }}>Number</th>
                <th style={{ padding: '0.5rem' }}>Grade</th>
              </tr>
            </thead>
            <tbody>
              {parallels.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.5rem' }}>
                    <Link to={`/hadiths/${p.id}`} style={{ color: '#1a73e8' }}>
                      {p.collection_name ?? p.collection_id}
                    </Link>
                  </td>
                  <td style={{ padding: '0.5rem' }}>{p.hadith_number}</td>
                  <td style={{ padding: '0.5rem' }}>{p.grade ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}
