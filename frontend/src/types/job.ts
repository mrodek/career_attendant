// Matches backend API response (camelCase)

export interface Job {
  id: string
  jobUrl: string
  jobTitle: string | null
  companyName: string | null
  
  // LLM-Extracted Fields
  industry: string | null
  seniority: 'intern' | 'junior' | 'mid' | 'senior' | 'staff' | 'principal' | 'director' | 'vp' | 'cxo' | null
  
  // Compensation
  salaryMin: number | null
  salaryMax: number | null
  salaryCurrency: string | null
  salaryPeriod: 'year' | 'month' | 'hour' | null
  salaryRaw: string | null
  
  // Location & Work Arrangement
  location: string | null
  remoteType: 'remote' | 'hybrid' | 'onsite' | null
  roleType: 'full_time' | 'part_time' | 'contract' | null
  
  // Skills & Experience
  requiredSkills: string[] | null
  preferredSkills: string[] | null
  yearsExperienceMin: number | null
  yearsExperienceMax: number | null
  
  // AI-Generated Content
  summary: string | null
  summaryGeneratedAt: string | null
  
  // Metadata
  postingDate: string | null
  source: string | null
  extractionConfidence: number | null
  savedCount: number
  
  // Deprecated (keeping for backwards compat)
  jobDescription?: string | null
  salaryRange?: string | null
  experienceLevel?: string | null
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
