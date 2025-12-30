import { useState } from 'react'
import { useJobs, useDeleteJob } from '../hooks/use-jobs'
import JobsTable from '../components/jobs/JobsTable'
import JobDetailPanel from '../components/jobs/JobDetailPanel'
import type { SavedJob } from '../types/job'

export default function SavedJobsPage() {
  const { data: jobs, isLoading, error } = useJobs()
  const deleteJob = useDeleteJob()
  const [selectedJob, setSelectedJob] = useState<SavedJob | null>(null)

  const handleSelectJob = (job: SavedJob) => {
    setSelectedJob(job)
    // TODO: Open job detail panel
  }

  const handleDeleteJob = (id: string) => {
    deleteJob.mutate(id)
  }

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-48 mb-6"></div>
          <div className="h-64 bg-slate-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Failed to load jobs. Make sure the API is running.
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Saved Jobs</h1>
          <p className="text-slate-600 mt-1">
            {jobs?.length || 0} jobs tracked
          </p>
        </div>
      </div>

      <JobsTable
        jobs={jobs || []}
        onSelectJob={handleSelectJob}
        onDeleteJob={handleDeleteJob}
      />

      {selectedJob && (
        <JobDetailPanel
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  )
}
