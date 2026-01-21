import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Resume, ResumeUploadPayload, ResumeUpdatePayload } from '../types/resume'
import { apiClient } from '../lib/api-client'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'
const RESUMES_QUERY_KEY = ['resumes']

// Fetch all resumes for current user
export function useResumes() {
  return useQuery({
    queryKey: RESUMES_QUERY_KEY,
    queryFn: async (): Promise<Resume[]> => {
      const response = await apiClient(`${API_BASE_URL}/resumes/`)
      return response.json()
    },
  })
}

// Get a single resume by ID
export function useResume(id: string | null) {
  return useQuery({
    queryKey: [...RESUMES_QUERY_KEY, id],
    queryFn: async (): Promise<Resume> => {
      const response = await apiClient(`${API_BASE_URL}/resumes/${id}`)
      return response.json()
    },
    enabled: !!id,
  })
}

// Upload a new resume
export function useUploadResume() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ResumeUploadPayload): Promise<Resume> => {
      const formData = new FormData()
      formData.append('resume_name', payload.resume_name)
      formData.append('is_primary', String(payload.is_primary ?? false))
      formData.append('file', payload.file)

      const response = await apiClient(`${API_BASE_URL}/resumes/`, {
        method: 'POST',
        body: formData,
      })

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RESUMES_QUERY_KEY })
    },
  })
}

// Update resume metadata
export function useUpdateResume() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: ResumeUpdatePayload }): Promise<Resume> => {
      const response = await apiClient(`${API_BASE_URL}/resumes/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      })

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RESUMES_QUERY_KEY })
    },
  })
}

// Delete a resume
export function useDeleteResume() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await apiClient(`${API_BASE_URL}/resumes/${id}`, {
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RESUMES_QUERY_KEY })
    },
  })
}
