import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api-client'
import type { SavedJob } from '../types/job'

const JOBS_QUERY_KEY = ['jobs']

interface EntriesResponse {
  items: SavedJob[]
  total: number
}

// Fetch all saved jobs for current user
export function useJobs() {
  return useQuery({
    queryKey: JOBS_QUERY_KEY,
    queryFn: async () => {
      // TODO: Add auth header when Clerk is integrated
      const response = await api.get<EntriesResponse>('/entries/')
      return response.items
    },
  })
}

// Update a saved job
export function useUpdateJob() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: Partial<SavedJob> }) => {
      return api.patch<SavedJob>(`/entries/${id}`, updates)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY })
    },
  })
}

// Delete a saved job
export function useDeleteJob() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/entries/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY })
    },
  })
}
