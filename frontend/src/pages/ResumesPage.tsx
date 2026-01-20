import { useState } from 'react'
import { Plus, FileText } from 'lucide-react'
import { useResumes } from '../hooks/use-resumes'
import ResumeUploadForm from '../components/resumes/ResumeUploadForm'
import ResumeCard from '../components/resumes/ResumeCard'
import type { Resume } from '../types/resume'

export default function ResumesPage() {
  const { data: resumes, isLoading, error } = useResumes()
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null)

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-48 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-slate-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Failed to load resumes. Make sure the API is running.
        </div>
      </div>
    )
  }

  const primaryResume = resumes?.find((r) => r.is_primary)
  const otherResumes = resumes?.filter((r) => !r.is_primary) || []

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">My Resumes</h1>
          <p className="text-slate-600 mt-1">
            {resumes?.length || 0} resume{resumes?.length !== 1 ? 's' : ''} uploaded
          </p>
        </div>
        <button
          onClick={() => setShowUploadForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Upload Resume
        </button>
      </div>

      {/* Upload Modal */}
      {showUploadForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-900">Upload Resume</h2>
              <button
                onClick={() => setShowUploadForm(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>
            <ResumeUploadForm
              onSuccess={() => setShowUploadForm(false)}
            />
          </div>
        </div>
      )}

      {/* Resume Detail Panel */}
      {selectedResume && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-900">{selectedResume.resume_name}</h2>
              <button
                onClick={() => setSelectedResume(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">File:</span>
                  <p className="font-medium">{selectedResume.file_name}</p>
                </div>
                <div>
                  <span className="text-slate-500">Status:</span>
                  <p className="font-medium capitalize">{selectedResume.processing_status}</p>
                </div>
                <div>
                  <span className="text-slate-500">Uploaded:</span>
                  <p className="font-medium">
                    {new Date(selectedResume.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Primary:</span>
                  <p className="font-medium">{selectedResume.is_primary ? 'Yes' : 'No'}</p>
                </div>
              </div>

              {selectedResume.llm_extracted_json && (
                <div className="border-t pt-4">
                  <h3 className="font-medium text-slate-900 mb-2">Extracted Information</h3>
                  <pre className="bg-slate-100 p-4 rounded-lg text-xs overflow-auto max-h-64">
                    {JSON.stringify(selectedResume.llm_extracted_json, null, 2)}
                  </pre>
                </div>
              )}

              {selectedResume.raw_text && (
                <div className="border-t pt-4">
                  <h3 className="font-medium text-slate-900 mb-2">Raw Text</h3>
                  <pre className="bg-slate-100 p-4 rounded-lg text-xs overflow-auto max-h-64 whitespace-pre-wrap">
                    {selectedResume.raw_text}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {(!resumes || resumes.length === 0) && (
        <div className="text-center py-16 border-2 border-dashed border-slate-200 rounded-xl">
          <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No resumes yet</h3>
          <p className="text-slate-600 mb-4">
            Upload your resume to get started with AI-powered job matching
          </p>
          <button
            onClick={() => setShowUploadForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Upload Your First Resume
          </button>
        </div>
      )}

      {/* Primary Resume */}
      {primaryResume && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-3">Primary Resume</h2>
          <div className="max-w-md">
            <ResumeCard
              resume={primaryResume}
              onSelect={setSelectedResume}
            />
          </div>
        </div>
      )}

      {/* Other Resumes */}
      {otherResumes.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-slate-900 mb-3">
            {primaryResume ? 'Other Resumes' : 'All Resumes'}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {otherResumes.map((resume) => (
              <ResumeCard
                key={resume.id}
                resume={resume}
                onSelect={setSelectedResume}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
