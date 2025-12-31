import { useState, useMemo } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, Edit2, Trash2 } from 'lucide-react'
import type { SavedJob, SortField, SortDirection } from '../../types/job'

interface JobsTableProps {
  jobs: SavedJob[]
  onSelectJob: (job: SavedJob) => void
  onDeleteJob: (id: string) => void
}

export default function JobsTable({ jobs, onSelectJob, onDeleteJob }: JobsTableProps) {
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedJobs = useMemo(() => {
    if (!sortField) return jobs

    return [...jobs].sort((a, b) => {
      let aVal: string | null = null
      let bVal: string | null = null

      switch (sortField) {
        case 'jobTitle':
          aVal = a.job.jobTitle
          bVal = b.job.jobTitle
          break
        case 'companyName':
          aVal = a.job.companyName
          bVal = b.job.companyName
          break
        case 'interestLevel':
          aVal = a.interestLevel
          bVal = b.interestLevel
          break
        case 'applicationStatus':
          aVal = a.applicationStatus
          bVal = b.applicationStatus
          break
        case 'jobFitScore':
          aVal = a.jobFitScore
          bVal = b.jobFitScore
          break
        case 'createdAt':
          aVal = a.createdAt
          bVal = b.createdAt
          break
      }

      if (aVal === null && bVal === null) return 0
      if (aVal === null) return 1
      if (bVal === null) return -1
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
  }, [jobs, sortField, sortDirection])

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ChevronDown size={14} className="opacity-30" />
    return sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
  }

  const getStatusColor = (status: string | null) => {
    const colors: Record<string, string> = {
      saved: 'bg-blue-50 text-blue-600',
      applied: 'bg-blue-100 text-blue-700',
      interviewing: 'bg-blue-200 text-blue-800',
      offer: 'bg-blue-300 text-blue-900',
      rejected: 'bg-slate-100 text-slate-600',
    }
    return colors[status || ''] || 'bg-slate-100 text-slate-700'
  }

  const getInterestColor = (level: string | null) => {
    const colors: Record<string, string> = {
      high: 'bg-blue-300 text-blue-900',
      medium: 'bg-blue-200 text-blue-800',
      low: 'bg-blue-100 text-blue-700',
    }
    return colors[level || ''] || 'bg-slate-100 text-slate-700'
  }

  const getFitColor = (score: string | null) => {
    const colors: Record<string, string> = {
      veryStrong: 'bg-blue-400 text-blue-950',
      strong: 'bg-blue-300 text-blue-900',
      good: 'bg-blue-200 text-blue-800',
      fair: 'bg-blue-100 text-blue-700',
      weak: 'bg-blue-50 text-blue-600',
    }
    return colors[score || ''] || 'bg-slate-100 text-slate-700'
  }

  const formatLabel = (str: string | null) => {
    if (!str) return '—'
    return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }

  const formatSalary = (min: number | null, max: number | null) => {
    if (!min && !max) return '—'
    const fmt = (n: number) => {
      if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
      if (n >= 1000) return `${Math.round(n / 1000)}K`
      return n.toString()
    }
    if (min && max) return `$${fmt(min)}-${fmt(max)}`
    if (min) return `$${fmt(min)}+`
    if (max) return `Up to $${fmt(max)}`
    return '—'
  }

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this job?')) {
      onDeleteJob(id)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            <th
              className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100"
              onClick={() => handleSort('jobTitle')}
            >
              <div className="flex items-center gap-2">
                Job Title <SortIcon field="jobTitle" />
              </div>
            </th>
            <th
              className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100"
              onClick={() => handleSort('companyName')}
            >
              <div className="flex items-center gap-2">
                Company <SortIcon field="companyName" />
              </div>
            </th>
            <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">
              Salary
            </th>
            <th
              className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100"
              onClick={() => handleSort('interestLevel')}
            >
              <div className="flex items-center gap-2">
                Interest <SortIcon field="interestLevel" />
              </div>
            </th>
            <th
              className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100"
              onClick={() => handleSort('applicationStatus')}
            >
              <div className="flex items-center gap-2">
                Status <SortIcon field="applicationStatus" />
              </div>
            </th>
            <th
              className="px-6 py-4 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100"
              onClick={() => handleSort('jobFitScore')}
            >
              <div className="flex items-center gap-2">
                Fit Score <SortIcon field="jobFitScore" />
              </div>
            </th>
            <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedJobs.map((savedJob) => (
            <tr
              key={savedJob.id}
              className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition"
              onClick={() => onSelectJob(savedJob)}
            >
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-900">
                    {savedJob.job.jobTitle || 'Untitled'}
                  </span>
                  <a
                    href={savedJob.job.jobUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-slate-400 hover:text-blue-600"
                  >
                    <ExternalLink size={14} />
                  </a>
                </div>
              </td>
              <td className="px-6 py-4 text-slate-600">
                {savedJob.job.companyName || '—'}
              </td>
              <td className="px-6 py-4 text-slate-600 text-sm">
                {formatSalary(savedJob.job.salaryMin, savedJob.job.salaryMax)}
              </td>
              <td className="px-6 py-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getInterestColor(savedJob.interestLevel)}`}>
                  {formatLabel(savedJob.interestLevel)}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(savedJob.applicationStatus)}`}>
                  {formatLabel(savedJob.applicationStatus)}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getFitColor(savedJob.jobFitScore)}`}>
                  {formatLabel(savedJob.jobFitScore)}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onSelectJob(savedJob)
                    }}
                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, savedJob.id)}
                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {sortedJobs.length === 0 && (
        <div className="p-12 text-center text-slate-500">
          No saved jobs yet. Use the browser extension to save jobs!
        </div>
      )}
    </div>
  )
}
