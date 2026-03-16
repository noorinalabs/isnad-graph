import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import NarratorsPage from './pages/NarratorsPage'
import HadithsPage from './pages/HadithsPage'
import CollectionsPage from './pages/CollectionsPage'
import SearchPage from './pages/SearchPage'
import TimelinePage from './pages/TimelinePage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/narrators" replace />} />
            <Route path="narrators" element={<NarratorsPage />} />
            <Route path="hadiths" element={<HadithsPage />} />
            <Route path="collections" element={<CollectionsPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="timeline" element={<TimelinePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
