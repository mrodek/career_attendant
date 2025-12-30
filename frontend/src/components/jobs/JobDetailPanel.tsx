import { useState } from 'react'
import { X, ExternalLink, Calendar, MapPin, DollarSign, Briefcase } from 'lucide-react'
import type { SavedJob } from '../../types/job'
import { useUpdateJob } from '../../hooks/use-jobs'

interface JobDetailPanelProps {
  job: SavedJob
  onClose: () => void
}

const INTEREST_OPTIONS = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

const STATUS_OPTIONS = [
  { value: 'saved', label: 'Saved' },
  { value: 'applied', label: 'Applied' },
  { value: 'interviewing', label: 'Interviewing' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
]

const FIT_OPTIONS = [
  { value: 'very_strong', label: 'Very Strong' },
  { value: 'strong', label: 'Strong' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'weak', label: 'Weak' },
]

export default function JobDetailPanel({ job, onClose }: JobDetailPanelProps) {
  const updateJob = useUpdateJob()
  const [notes, setNotes] = useState(job.notes || '')
  const [interestLevel, setInterestLevel] = useState(job.interestLevel || '')
  const [applicationStatus, setApplicationStatus] = useState(job.applicationStatus || '')
  const [jobFitScore, setJobFitScore] = useState(job.jobFitScore || '')

  const handleSave = () => {
    updateJob.mutate({
      id: job.id,
      updates: {
        notes,
        interestLevel: interestLevel as SavedJob['interestLevel'],
        applicationStatus: applicationStatus as SavedJob['applicationStatus'],
        jobFitScore: jobFitScore as SavedJob['jobFitScore'],
      },
    })
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="fixed inset-0 bg-black/20 flex justify-end z-50">
      {/* Backdrop click to close */}
      <div className="flex-1" onClick={onClose} />
      
      {/* Panel */}
      <div className="w-[600px] bg-white h-full shadow-xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-start justify-between">
            <div className="flex-1 pr-4">
              <h2 className="text-xl font-bold text-slate-900">
                {job.job.jobTitle || 'Untitled Position'}
              </h2>
              <p className="text-slate-600 mt-1">{job.job.companyName || 'Unknown Company'}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              <X size={20} />
            </button>
          </div>
          
          {/* Quick info row */}
          <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-600">
            {job.job.location && (
              <div className="flex items-center gap-1">
                <MapPin size={14} />
                <span>{job.job.location}</span>
              </div>
            )}
            {job.job.salaryRange && (
              <div className="flex items-center gap-1">
                <DollarSign size={14} />
                <span>{job.job.salaryRange}</span>
              </div>
            )}
            {job.job.remoteType && (
              <div className="flex items-center gap-1">
                <Briefcase size={14} />
                <span>{job.job.remoteType}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Calendar size={14} />
              <span>Saved {formatDate(job.createdAt)}</span>
            </div>
          </div>

          {/* External link */}
          <a
            href={job.job.jobUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
          >
            <ExternalLink size={16} />
            View Original Posting
          </a>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          {/* Tracking section */}
          <section>
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
              Tracking
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-slate-600 mb-1">Interest Level</label>
                <select
                  value={interestLevel}
                  onChange={(e) => setInterestLevel(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Not set</option>
                  {INTEREST_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-600 mb-1">Status</label>
                <select
                  value={applicationStatus}
                  onChange={(e) => setApplicationStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Not set</option>
                  {STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-600 mb-1">Job Fit</label>
                <select
                  value={jobFitScore}
                  onChange={(e) => setJobFitScore(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Not set</option>
                  {FIT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Notes section */}
          <section>
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
              Notes
            </h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this job..."
              rows={4}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </section>

          {/* Job Description */}
          {job.job.jobDescription && (
            <section>
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
                Job Description
              </h3>
              <div className="text-sm text-slate-600 whitespace-pre-wrap bg-slate-50 p-4 rounded-lg max-h-64 overflow-auto">
                {job.job.jobDescription}
              </div>
            </section>
          )}

          {/* Job Fit Reason */}
          {job.jobFitReason && (
            <section>
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
                Why This Job Fits
              </h3>
              <div className="text-sm text-slate-600 bg-blue-50 p-4 rounded-lg">
                {job.jobFitReason}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-200 bg-slate-50">
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-slate-600 hover:text-slate-800 text-sm font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={updateJob.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium disabled:opacity-50"
            >
              {updateJob.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
