import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useSubscription } from '../hooks/useSubscription'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const { isExpired, isLoading: subLoading } = useSubscription()
  const location = useLocation()

  if (loading || subLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (isExpired) {
    return <Navigate to="/trial-expired" replace />
  }

  return <Outlet />
}
