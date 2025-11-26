'use client'

import { useEffect, useState } from 'react'
import { useDocumentStore } from '@/store/document-store'
import { Document } from '@/types'
import { CheckIcon, DocumentTextIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'

interface DocumentSelectorProps {
  selectedDocumentIds: string[]
  onSelectionChange: (documentIds: string[]) => void
}

export default function DocumentSelector({
  selectedDocumentIds,
  onSelectionChange,
}: DocumentSelectorProps) {
  const { documents, isLoading, fetchDocuments } = useDocumentStore()
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      await fetchDocuments({ status: 'ready', page_size: 100 })
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  const filteredDocuments = documents.filter((doc) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        doc.product_name.toLowerCase().includes(query) ||
        doc.insurer.toLowerCase().includes(query)
      )
    }
    return true
  })

  const handleToggleDocument = (documentId: string) => {
    if (selectedDocumentIds.includes(documentId)) {
      onSelectionChange(selectedDocumentIds.filter((id) => id !== documentId))
    } else {
      onSelectionChange([...selectedDocumentIds, documentId])
    }
  }

  const handleSelectAll = () => {
    if (selectedDocumentIds.length === filteredDocuments.length) {
      onSelectionChange([])
    } else {
      onSelectionChange(filteredDocuments.map((doc) => doc.document_id))
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
        <input
          type="text"
          placeholder="문서 검색..."
          className="input-field pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Select All */}
      <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-dark-border">
        <span className="text-sm text-gray-700 dark:text-gray-300">
          {selectedDocumentIds.length}개 선택됨
        </span>
        <button
          onClick={handleSelectAll}
          className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 font-medium"
        >
          {selectedDocumentIds.length === filteredDocuments.length
            ? '선택 해제'
            : '전체 선택'}
        </button>
      </div>

      {/* Document List */}
      <div className="max-h-96 overflow-y-auto space-y-2">
        {filteredDocuments.length === 0 ? (
          <div className="text-center py-8">
            <DocumentTextIcon className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {searchQuery ? '검색 결과가 없습니다' : '사용 가능한 문서가 없습니다'}
            </p>
          </div>
        ) : (
          filteredDocuments.map((doc) => {
            const isSelected = selectedDocumentIds.includes(doc.document_id)

            return (
              <div
                key={doc.document_id}
                onClick={() => handleToggleDocument(doc.document_id)}
                className={`
                  flex items-start gap-3 p-3 rounded-lg border cursor-pointer
                  transition-colors duration-150
                  ${
                    isSelected
                      ? 'bg-primary-50 border-primary-200'
                      : 'bg-white dark:bg-dark-surface border-gray-200 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-dark-hover'
                  }
                `}
              >
                <div className="flex-shrink-0 mt-1">
                  <div
                    className={`
                      w-5 h-5 rounded border-2 flex items-center justify-center
                      ${
                        isSelected
                          ? 'bg-primary-600 border-primary-600'
                          : 'bg-white dark:bg-dark-surface border-gray-300 dark:border-dark-border'
                      }
                    `}
                  >
                    {isSelected && <CheckIcon className="w-3 h-3 text-white" />}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {doc.product_name}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{doc.insurer}</p>
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {doc.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-0.5 bg-gray-100 dark:bg-dark-elevated text-gray-600 dark:text-gray-400 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {doc.tags.length > 3 && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          +{doc.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
