// Matches backend API response (camelCase)

export interface Job {
  id: string
  jobUrl: string
  jobTitle: string | null
  companyName: string | null
  jobDescription: string | null
  salaryRange: string | null
  location: string | null
  remoteType: string | null
  roleType: string | null
  experienceLevel: string | null
  savedCount: number
}

export interface SavedJob {
  id: string
  job: Job
  // Flattened fields (backward compat)
  jobUrl: string
  jobTitle: string | null
  companyName: string | null
  location: string | null
  salaryRange: string | null
  remoteType: string | null
  roleType: string | null
  // User-specific tracking
  interestLevel: 'high' | 'medium' | 'low' | null
  applicationStatus: 'saved' | 'applied' | 'interviewing' | 'offer' | 'rejected' | null
  applicationDate: string | null
  notes: string | null
  jobFitScore: 'very_strong' | 'strong' | 'good' | 'fair' | 'weak' | null
  jobFitReason: string | null
  targetedResumeUrl: string | null
  targetedCoverLetterUrl: string | null
  workflowStatus: string | null
  createdAt: string
  updatedAt: string
}

export type SortField = 
  | 'jobTitle' 
  | 'companyName' 
  | 'interestLevel' 
  | 'applicationStatus' 
  | 'jobFitScore'
  | 'createdAt'

export type SortDirection = 'asc' | 'desc'
