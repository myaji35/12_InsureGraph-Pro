'use client'

import { useState, useCallback } from 'react'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  accept?: string
  maxSize?: number // in MB
}

export default function FileUpload({
  onFileSelect,
  accept = '.pdf',
  maxSize = 50,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const validateFile = (file: File): boolean => {
    // Check file type
    if (accept && !accept.includes(file.type.split('/')[1]) && !accept.includes(file.name.split('.').pop() || '')) {
      setError(`지원하지 않는 파일 형식입니다. (허용: ${accept})`)
      return false
    }

    // Check file size
    const maxSizeBytes = maxSize * 1024 * 1024
    if (file.size > maxSizeBytes) {
      setError(`파일 크기가 너무 큽니다. (최대: ${maxSize}MB)`)
      return false
    }

    setError(null)
    return true
  }

  const handleFile = (file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file)
      onFileSelect(file)
    }
  }

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    setError(null)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div>
      {!selectedFile ? (
        <div
          role="button"
          tabIndex={0}
          aria-label={`파일 업로드. ${accept} 파일 허용, 최대 크기 ${maxSize}MB`}
          className={`
            relative border-2 border-dashed rounded-lg p-8
            transition-colors duration-200
            ${
              isDragging
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 dark:border-dark-border bg-gray-50 dark:bg-dark-elevated hover:border-primary-400'
            }
          `}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept={accept}
            onChange={handleFileInput}
            aria-label={`파일 선택: ${accept} 파일 (최대 ${maxSize}MB)`}
          />

          <label
            htmlFor="file-upload"
            className="flex flex-col items-center justify-center cursor-pointer"
          >
            <CloudArrowUpIcon
              className={`w-16 h-16 mb-4 ${
                isDragging ? 'text-primary-500' : 'text-gray-400 dark:text-gray-500'
              }`}
              aria-hidden="true"
            />
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
              {isDragging ? '파일을 여기에 놓으세요' : '파일을 드래그하거나 클릭하여 업로드'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {accept} 파일 (최대 {maxSize}MB)
            </p>
          </label>
        </div>
      ) : (
        <div
          className="border border-gray-300 dark:border-dark-border rounded-lg p-6 bg-white dark:bg-dark-surface"
          role="status"
          aria-label="선택된 파일"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <DocumentIcon className="w-12 h-12 text-primary-500" aria-hidden="true" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">{selectedFile.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>
            <button
              onClick={handleRemoveFile}
              className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
              aria-label={`파일 제거: ${selectedFile.name}`}
            >
              <XMarkIcon className="w-6 h-6" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}

      {error && (
        <div
          className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md"
          role="alert"
          aria-live="assertive"
        >
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}
    </div>
  )
}
