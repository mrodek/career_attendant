import { useState, useRef } from 'react'
import { useUploadResume } from '../../hooks/use-resumes'
import { Upload, FileText, X, Loader2 } from 'lucide-react'

interface ResumeUploadFormProps {
  onSuccess?: () => void
}

export default function ResumeUploadForm({ onSuccess }: ResumeUploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [resumeName, setResumeName] = useState('')
  const [isPrimary, setIsPrimary] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  
  const uploadResume = useUploadResume()

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFile = (file: File) => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a PDF or DOCX file')
      return
    }
    
    setFile(file)
    // Auto-fill resume name from filename (without extension)
    if (!resumeName) {
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '')
      setResumeName(nameWithoutExt)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file || !resumeName.trim()) {
      alert('Please provide a file and resume name')
      return
    }

    try {
      await uploadResume.mutateAsync({
        file,
        resume_name: resumeName.trim(),
        is_primary: isPrimary,
      })
      
      // Reset form
      setFile(null)
      setResumeName('')
      setIsPrimary(false)
      if (inputRef.current) {
        inputRef.current.value = ''
      }
      
      onSuccess?.()
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  const clearFile = () => {
    setFile(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Drop zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : file
            ? 'border-green-500 bg-green-50'
            : 'border-slate-300 hover:border-slate-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText className="w-8 h-8 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-slate-900">{file.name}</p>
              <p className="text-sm text-slate-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              type="button"
              onClick={clearFile}
              className="p-1 hover:bg-slate-200 rounded"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-10 h-10 text-slate-400 mx-auto" />
            <p className="text-slate-600">
              <span className="font-medium text-blue-600">Click to upload</span>{' '}
              or drag and drop
            </p>
            <p className="text-sm text-slate-500">PDF or DOCX (max 10MB)</p>
          </div>
        )}
      </div>

      {/* Resume name input */}
      <div>
        <label htmlFor="resume-name" className="block text-sm font-medium text-slate-700 mb-1">
          Resume Name
        </label>
        <input
          id="resume-name"
          type="text"
          value={resumeName}
          onChange={(e) => setResumeName(e.target.value)}
          placeholder="e.g., Software Engineer Resume 2025"
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
      </div>

      {/* Primary checkbox */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isPrimary}
          onChange={(e) => setIsPrimary(e.target.checked)}
          className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
        />
        <span className="text-sm text-slate-700">Set as primary resume</span>
      </label>

      {/* Error message */}
      {uploadResume.isError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {uploadResume.error?.message || 'Failed to upload resume'}
        </div>
      )}

      {/* Submit button */}
      <button
        type="submit"
        disabled={!file || !resumeName.trim() || uploadResume.isPending}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
      >
        {uploadResume.isPending ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Uploading...
          </>
        ) : (
          <>
            <Upload className="w-4 h-4" />
            Upload Resume
          </>
        )}
      </button>
    </form>
  )
}
