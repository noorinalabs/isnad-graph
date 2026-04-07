import { useQuery } from '@tanstack/react-query'
import { fetchSubscription } from '../api/client'
import type { SubscriptionResponse } from '../types/api'
import { useAuth } from './useAuth'

export function useSubscription() {
  const { user } = useAuth()

  const { data, isLoading, error } = useQuery<SubscriptionResponse>({
    queryKey: ['subscription'],
    queryFn: fetchSubscription,
    enabled: !!user,
    staleTime: 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  })

  return {
    subscription: data ?? null,
    isLoading,
    error,
    isExpired: data?.status === 'expired',
    isTrial: data?.status === 'trial',
    isActive: data?.status === 'active',
    daysRemaining: data?.days_remaining ?? 0,
  }
}
