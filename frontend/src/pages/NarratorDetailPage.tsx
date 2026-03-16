import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchNarrator, fetchNarratorChains } from '../api/client'

export default function NarratorDetailPage() {
  const { id } = useParams<{ id: string }>()

  const {
    data: narrator,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['narrator', id],
    queryFn: () => fetchNarrator(id!),
    enabled: !!id,
  })

  const { data: chains } = useQuery({
    queryKey: ['narrator-chains', id],
    queryFn: () => fetchNarratorChains(id!),
    enabled: !!id,
  })

  if (isLoading) return <p>Loading...</p>
  if (error) return <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>
  if (!narrator) return <p>Narrator not found.</p>

  return (
    <div>
      <Link to="/narrators" style={{ color: '#1a73e8' }}>
        &larr; Back to Narrators
      </Link>

      <h2 style={{ direction: 'rtl', textAlign: 'right', marginTop: '1rem' }}>
        {narrator.name_arabic}
      </h2>
      {narrator.name_transliterated && (
        <h3 style={{ color: '#555', fontWeight: 400 }}>{narrator.name_transliterated}</h3>
      )}

      <section style={{ marginTop: '1.5rem' }}>
        <h3>Biography</h3>
        <table style={{ borderCollapse: 'collapse' }}>
          <tbody>
            {[
              ['Kunya', narrator.kunya],
              ['Nisba', narrator.nisba],
              ['Birth Year', narrator.birth_year != null ? `${narrator.birth_year} AH` : null],
              ['Death Year', narrator.death_year != null ? `${narrator.death_year} AH` : null],
              ['Generation', narrator.generation],
              ['Reliability', narrator.reliability_grade],
              ['Sect', narrator.sect],
              ['Location', narrator.location],
            ].map(
              ([label, value]) =>
                value && (
                  <tr key={label as string} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '0.4rem 1rem 0.4rem 0', fontWeight: 600 }}>
                      {label}
                    </td>
                    <td style={{ padding: '0.4rem 0' }}>{value}</td>
                  </tr>
                ),
            )}
          </tbody>
        </table>
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h3>Network Statistics</h3>
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          {[
            ['In-Degree', narrator.in_degree],
            ['Out-Degree', narrator.out_degree],
            ['Betweenness', narrator.betweenness_centrality?.toFixed(4)],
            ['PageRank', narrator.pagerank?.toFixed(4)],
            ['Community', narrator.community_id != null ? `#${narrator.community_id}` : null],
          ].map(
            ([label, value]) =>
              value != null && (
                <div
                  key={label as string}
                  style={{
                    padding: '0.75rem 1rem',
                    border: '1px solid #ddd',
                    borderRadius: 4,
                    minWidth: 100,
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', color: '#666' }}>{label}</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{value}</div>
                </div>
              ),
          )}
        </div>
      </section>

      {chains && chains.length > 0 && (
        <section style={{ marginTop: '1.5rem' }}>
          <h3>Chains ({chains.length})</h3>
          <ul style={{ paddingLeft: '1.25rem' }}>
            {chains.map((chain) => (
              <li key={chain.id} style={{ marginBottom: '0.5rem' }}>
                <Link to={`/hadiths/${chain.hadith_id}`} style={{ color: '#1a73e8' }}>
                  Hadith {chain.hadith_id}
                </Link>
                {!chain.is_complete && (
                  <span style={{ color: '#999', marginLeft: '0.5rem' }}>(incomplete chain)</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
