import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Resume, ResumeUploadPayload, ResumeUpdatePayload } from '../types/resume'
import { api } from '../lib/api-client'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'
const RESUMES_QUERY_KEY = ['resumes']

// Fetch all resumes for current user
export function useResumes() {
  return useQuery({
    queryKey: RESUMES_QUERY_KEY,
    queryFn: async (): Promise<Resume[]> => {
      const response = await api.get<Resume[]>(`${API_BASE_URL}/resumes/`)
      return response
    },
  })
}

// Get a single resume by ID
export function useResume(id: string | null) {
  return useQuery({
    queryKey: [...RESUMES_QUERY_KEY, id],
    queryFn: async (): Promise<Resume> => {
      const response = await api.get<Resume>(`${API_BASE_URL}/resumes/${id}`)
      return response
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

      const response = await api.post<Resume>(`${API_BASE_URL}/resumes/`, formData, {
        headers: {}, // Let browser set Content-Type for FormData
      })

      return response
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
      const response = await api.patch<Resume>(`${API_BASE_URL}/resumes/${id}`, updates)
      return response
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
      await api.delete(`${API_BASE_URL}/resumes/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RESUMES_QUERY_KEY })
    },
  })
}
