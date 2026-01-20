import { useState } from 'react'
import { FileText, Star, Trash2, MoreVertical, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import type { Resume } from '../../types/resume'
import { useDeleteResume, useUpdateResume } from '../../hooks/use-resumes'

interface ResumeCardProps {
  resume: Resume
  onSelect?: (resume: Resume) => void
}

export default function ResumeCard({ resume, onSelect }: ResumeCardProps) {
  const [showMenu, setShowMenu] = useState(false)
  const deleteResume = useDeleteResume()
  const updateResume = useUpdateResume()

  const handleDelete = () => {
    if (confirm(`Delete "${resume.resume_name}"?`)) {
      deleteResume.mutate(resume.id)
    }
    setShowMenu(false)
  }

  const handleSetPrimary = () => {
    updateResume.mutate({
      id: resume.id,
      updates: { is_primary: true },
    })
    setShowMenu(false)
  }

  const statusIcon = {
    pending: <Clock className="w-4 h-4 text-slate-400" />,
    processing: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
    completed: <CheckCircle className="w-4 h-4 text-green-500" />,
    failed: <AlertCircle className="w-4 h-4 text-red-500" />,
  }

  const statusLabel = {
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Ready',
    failed: 'Failed',
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div
      className={`relative bg-white border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer ${
        resume.is_primary ? 'border-blue-500 ring-1 ring-blue-500' : 'border-slate-200'
      }`}
      onClick={() => onSelect?.(resume)}
    >
      {/* Primary badge */}
      {resume.is_primary && (
        <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
          <Star className="w-3 h-3 fill-current" />
          Primary
        </div>
      )}

      {/* Menu button */}
      <div className="absolute top-2 right-2">
        <button
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
          className="p-1 hover:bg-slate-100 rounded"
        >
          <MoreVertical className="w-4 h-4 text-slate-500" />
        </button>

        {/* Dropdown menu */}
        {showMenu && (
          <div className="absolute right-0 mt-1 w-40 bg-white border border-slate-200 rounded-lg shadow-lg z-10">
            {!resume.is_primary && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleSetPrimary()
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <Star className="w-4 h-4" />
                Set as Primary
              </button>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDelete()
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex items-start gap-3">
        <div className="p-2 bg-slate-100 rounded-lg">
          <FileText className="w-6 h-6 text-slate-600" />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-slate-900 truncate pr-8">
            {resume.resume_name}
          </h3>
          <p className="text-sm text-slate-500 truncate">{resume.file_name}</p>

          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
            <span>{formatFileSize(resume.file_size)}</span>
            <span>{formatDate(resume.created_at)}</span>
            <span className="flex items-center gap-1">
              {statusIcon[resume.processing_status]}
              {statusLabel[resume.processing_status]}
            </span>
          </div>

          {resume.processing_status === 'failed' && resume.error_message && (
            <p className="mt-2 text-xs text-red-600 truncate">
              {resume.error_message}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
