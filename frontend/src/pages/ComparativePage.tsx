import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchParallels } from '../api/client'

export default function ComparativePage() {
  const [page, setPage] = useState(1)

  const { data, isLoading, error } = useQuery({
    queryKey: ['parallels', page],
    queryFn: () => fetchParallels(page, 10),
  })

  return (
    <div>
      <h2>Comparative Analysis</h2>
      <p style={{ color: '#666', marginBottom: '1rem' }}>
        Side-by-side comparison of parallel Sunni and Shia hadiths (PARALLEL_OF relationships).
      </p>

      {isLoading && <p>Loading parallels...</p>}
      {error && <p style={{ color: 'red' }}>Error: {(error as Error).message}</p>}

      {data && (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {data.items.map((pair, idx) => (
              <div
                key={`${pair.sunni_hadith.id}-${pair.shia_hadith.id}`}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: 8,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    padding: '0.5rem 1rem',
                    background: '#f5f5f5',
                    borderBottom: '1px solid #ddd',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>Parallel #{(page - 1) * 10 + idx + 1}</span>
                  <SimilarityBadge score={pair.similarity_score} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 120 }}>
                  <HadithPanel label="Sunni" hadith={pair.sunni_hadith} color="#1a73e8" />
                  <HadithPanel label="Shia" hadith={pair.shia_hadith} color="#e8501a" />
                </div>
              </div>
            ))}
          </div>

          <div
            style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}
          >
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

function SimilarityBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const bg = score >= 0.8 ? '#2ca02c' : score >= 0.5 ? '#ff7f0e' : '#d62728'
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '0.15rem 0.5rem',
        borderRadius: 12,
        background: bg,
        color: '#fff',
        fontSize: '0.8rem',
        fontWeight: 600,
      }}
    >
      {pct}% similar
    </span>
  )
}

function HadithPanel({
  label,
  hadith,
  color,
}: {
  label: string
  hadith: {
    collection_name: string | null
    hadith_number: string
    text_arabic: string
    text_english: string | null
    grade: string | null
  }
  color: string
}) {
  return (
    <div style={{ padding: '1rem', borderRight: '1px solid #eee' }}>
      <div style={{ marginBottom: '0.5rem' }}>
        <span
          style={{
            fontWeight: 600,
            color,
            fontSize: '0.85rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {label}
        </span>
        {hadith.collection_name && (
          <span style={{ marginLeft: '0.5rem', color: '#666', fontSize: '0.8rem' }}>
            {hadith.collection_name} #{hadith.hadith_number}
          </span>
        )}
        {hadith.grade && (
          <span
            style={{
              marginLeft: '0.5rem',
              padding: '0.1rem 0.4rem',
              background: '#eee',
              borderRadius: 4,
              fontSize: '0.75rem',
            }}
          >
            {hadith.grade}
          </span>
        )}
      </div>
      <p style={{ direction: 'rtl', textAlign: 'right', lineHeight: 1.8, margin: '0.5rem 0' }}>
        {hadith.text_arabic}
      </p>
      {hadith.text_english && (
        <p style={{ color: '#555', fontSize: '0.9rem', margin: '0.5rem 0' }}>
          {hadith.text_english}
        </p>
      )}
    </div>
  )
}
