// Resume types matching backend API

export interface Resume {
  id: string
  user_id: string
  resume_name: string
  file_name: string
  file_path: string
  file_size: number
  file_type: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  raw_text: string | null
  llm_extracted_json: ResumeExtractedData | null
  is_primary: boolean
  created_at: string
  updated_at: string
}

export interface ResumeExtractedData {
  contact_info?: {
    name?: string
    email?: string
    phone?: string
    location?: string
    linkedin?: string
    github?: string
    portfolio?: string
  }
  summary?: string
  skills?: {
    technical?: string[]
    soft?: string[]
    languages?: string[]
    certifications?: string[]
  }
  experience?: {
    company: string
    title: string
    location?: string
    start_date?: string
    end_date?: string
    current?: boolean
    highlights?: string[]
  }[]
  education?: {
    institution: string
    degree: string
    field?: string
    graduation_date?: string
    gpa?: string
  }[]
}

export interface ResumeUploadPayload {
  resume_name: string
  is_primary?: boolean
  file: File
}

export interface ResumeUpdatePayload {
  resume_name?: string
  is_primary?: boolean
}
