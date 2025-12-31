import { useState } from 'react'
import { X, ExternalLink, Calendar, MapPin, DollarSign, Briefcase, Sparkles, Code, Building2, Clock, TrendingUp } from 'lucide-react'
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

  const formatSalary = (min: number | null, max: number | null, currency: string | null) => {
    if (!min && !max) return null
    const fmt = (n: number) => {
      if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
      if (n >= 1000) return `${Math.round(n / 1000)}K`
      return n.toString()
    }
    const curr = currency || 'USD'
    const symbol = curr === 'USD' ? '$' : curr === 'GBP' ? '£' : curr === 'EUR' ? '€' : `${curr} `
    if (min && max) return `${symbol}${fmt(min)} - ${symbol}${fmt(max)}`
    if (min) return `${symbol}${fmt(min)}+`
    if (max) return `Up to ${symbol}${fmt(max)}`
    return null
  }

  const formatSeniority = (seniority: string | null) => {
    if (!seniority) return null
    const labels: Record<string, string> = {
      intern: 'Intern',
      junior: 'Junior',
      mid: 'Mid-Level',
      senior: 'Senior',
      staff: 'Staff',
      principal: 'Principal',
      director: 'Director',
      vp: 'VP',
      cxo: 'C-Level',
    }
    return labels[seniority] || seniority
  }

  const formatExperience = (min: number | null, max: number | null) => {
    if (!min && !max) return null
    if (min && max) return `${min}-${max} years`
    if (min) return `${min}+ years`
    if (max) return `Up to ${max} years`
    return null
  }

  const salaryDisplay = formatSalary(job.job.salaryMin, job.job.salaryMax, job.job.salaryCurrency)
  const seniorityDisplay = formatSeniority(job.job.seniority)
  const experienceDisplay = formatExperience(job.job.yearsExperienceMin, job.job.yearsExperienceMax)

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
            {salaryDisplay && (
              <div className="flex items-center gap-1">
                <DollarSign size={14} />
                <span>{salaryDisplay}</span>
              </div>
            )}
            {job.job.remoteType && (
              <div className="flex items-center gap-1">
                <Briefcase size={14} />
                <span className="capitalize">{job.job.remoteType}</span>
              </div>
            )}
            {seniorityDisplay && (
              <div className="flex items-center gap-1">
                <TrendingUp size={14} />
                <span>{seniorityDisplay}</span>
              </div>
            )}
            {job.job.industry && (
              <div className="flex items-center gap-1">
                <Building2 size={14} />
                <span>{job.job.industry}</span>
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

          {/* AI Summary */}
          {job.job.summary && (
            <section>
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                <Sparkles size={14} className="text-purple-500" />
                AI Summary
              </h3>
              <div className="text-sm text-slate-700 bg-gradient-to-br from-purple-50 to-blue-50 p-4 rounded-lg border border-purple-100">
                <div className="prose prose-sm prose-slate max-w-none">
                  {job.job.summary.split('\n').map((line, i) => {
                    if (line.startsWith('## ')) {
                      return <h4 key={i} className="font-semibold text-slate-800 mt-3 mb-1">{line.replace('## ', '')}</h4>
                    }
                    if (line.startsWith('- ')) {
                      return <p key={i} className="ml-4 my-0.5">• {line.replace('- ', '')}</p>
                    }
                    if (line.startsWith('# ')) {
                      return <h3 key={i} className="font-bold text-slate-900 mb-2">{line.replace('# ', '')}</h3>
                    }
                    if (line.trim()) {
                      return <p key={i} className="my-1">{line}</p>
                    }
                    return null
                  })}
                </div>
              </div>
            </section>
          )}

          {/* Job Signals */}
          <section>
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <Code size={14} className="text-blue-500" />
              Job Signals
            </h3>
            <div className="space-y-4">
              {/* Experience & Role Type */}
              <div className="grid grid-cols-2 gap-4">
                {experienceDisplay && (
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                      <Clock size={12} />
                      Experience
                    </div>
                    <div className="font-medium text-slate-800">{experienceDisplay}</div>
                  </div>
                )}
                {job.job.roleType && (
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <div className="text-slate-500 text-xs mb-1">Role Type</div>
                    <div className="font-medium text-slate-800 capitalize">
                      {job.job.roleType.replace('_', ' ')}
                    </div>
                  </div>
                )}
              </div>

              {/* Required Skills */}
              {job.job.requiredSkills && job.job.requiredSkills.length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Required Skills</div>
                  <div className="flex flex-wrap gap-2">
                    {job.job.requiredSkills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Preferred Skills */}
              {job.job.preferredSkills && job.job.preferredSkills.length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Nice to Have</div>
                  <div className="flex flex-wrap gap-2">
                    {job.job.preferredSkills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
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
