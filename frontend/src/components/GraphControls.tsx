'use client'

import { useState, useEffect } from 'react'
import { useDocumentStore } from '@/store/document-store'
import { NodeType } from '@/types'
import {
  FunnelIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'

interface GraphControlsProps {
  selectedDocumentIds: string[]
  selectedNodeTypes: NodeType[]
  searchQuery: string
  onDocumentIdsChange: (ids: string[]) => void
  onNodeTypesChange: (types: NodeType[]) => void
  onSearchQueryChange: (query: string) => void
  onApplyFilters: () => void
}

const nodeTypeOptions: { value: NodeType; label: string }[] = [
  { value: 'document', label: '문서' },
  { value: 'entity', label: '엔티티' },
  { value: 'concept', label: '개념' },
  { value: 'clause', label: '조항' },
]

export default function GraphControls({
  selectedDocumentIds,
  selectedNodeTypes,
  searchQuery,
  onDocumentIdsChange,
  onNodeTypesChange,
  onSearchQueryChange,
  onApplyFilters,
}: GraphControlsProps) {
  const { documents, fetchDocuments } = useDocumentStore()
  const [isExpanded, setIsExpanded] = useState(true)

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

  const handleToggleDocument = (documentId: string) => {
    if (selectedDocumentIds.includes(documentId)) {
      onDocumentIdsChange(selectedDocumentIds.filter((id) => id !== documentId))
    } else {
      onDocumentIdsChange([...selectedDocumentIds, documentId])
    }
  }

  const handleToggleNodeType = (nodeType: NodeType) => {
    if (selectedNodeTypes.includes(nodeType)) {
      onNodeTypesChange(selectedNodeTypes.filter((t) => t !== nodeType))
    } else {
      onNodeTypesChange([...selectedNodeTypes, nodeType])
    }
  }

  return (
    <div className="card" role="region" aria-label="그래프 필터 컨트롤">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FunnelIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" aria-hidden="true" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">필터</h3>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 font-medium"
          aria-expanded={isExpanded}
          aria-controls="filter-content"
          aria-label={isExpanded ? '필터 접기' : '필터 펼치기'}
        >
          {isExpanded ? '접기' : '펼치기'}
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-6" id="filter-content">
          {/* Search */}
          <div role="search">
            <label
              htmlFor="node-search"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              노드 검색
            </label>
            <div className="relative">
              <MagnifyingGlassIcon
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500"
                aria-hidden="true"
              />
              <input
                id="node-search"
                type="text"
                placeholder="노드 이름으로 검색..."
                className="input-field pl-10"
                value={searchQuery}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                aria-label="노드 이름 검색"
              />
            </div>
          </div>

          {/* Node Types */}
          <fieldset>
            <legend className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              노드 유형 ({selectedNodeTypes.length}개 선택)
            </legend>
            <div className="space-y-2" role="group" aria-label="노드 유형 선택">
              {nodeTypeOptions.map((option) => {
                const isSelected = selectedNodeTypes.includes(option.value)
                return (
                  <div
                    key={option.value}
                    role="checkbox"
                    tabIndex={0}
                    aria-checked={isSelected}
                    aria-label={`${option.label} 노드 유형`}
                    onClick={() => handleToggleNodeType(option.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleToggleNodeType(option.value)
                      }
                    }}
                    className={`
                      flex items-center gap-3 p-3 rounded-lg border cursor-pointer
                      transition-colors duration-150
                      ${
                        isSelected
                          ? 'bg-primary-50 border-primary-200'
                          : 'bg-white dark:bg-dark-surface border-gray-200 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-dark-hover'
                      }
                    `}
                  >
                    <div
                      className={`
                        w-5 h-5 rounded border-2 flex items-center justify-center
                        ${
                          isSelected
                            ? 'bg-primary-600 border-primary-600'
                            : 'bg-white dark:bg-dark-surface border-gray-300 dark:border-dark-border'
                        }
                      `}
                      aria-hidden="true"
                    >
                      {isSelected && <CheckIcon className="w-3 h-3 text-white" />}
                    </div>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{option.label}</span>
                  </div>
                )
              })}
            </div>
          </fieldset>

          {/* Documents */}
          <fieldset>
            <legend className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              문서 ({selectedDocumentIds.length}개 선택)
            </legend>
            <div className="max-h-60 overflow-y-auto space-y-2" role="group" aria-label="문서 선택">
              {documents.map((doc) => {
                const isSelected = selectedDocumentIds.includes(doc.document_id)
                return (
                  <div
                    key={doc.document_id}
                    role="checkbox"
                    tabIndex={0}
                    aria-checked={isSelected}
                    aria-label={`${doc.product_name} - ${doc.insurer}`}
                    onClick={() => handleToggleDocument(doc.document_id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleToggleDocument(doc.document_id)
                      }
                    }}
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
                    <div
                      className={`
                        w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5
                        ${
                          isSelected
                            ? 'bg-primary-600 border-primary-600'
                            : 'bg-white dark:bg-dark-surface border-gray-300 dark:border-dark-border'
                        }
                      `}
                      aria-hidden="true"
                    >
                      {isSelected && <CheckIcon className="w-3 h-3 text-white" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {doc.product_name}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{doc.insurer}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </fieldset>

          {/* Apply Button */}
          <button
            onClick={onApplyFilters}
            className="btn-primary w-full"
            disabled={selectedDocumentIds.length === 0}
            aria-label={`선택된 ${selectedDocumentIds.length}개 문서로 그래프 생성`}
            aria-disabled={selectedDocumentIds.length === 0}
          >
            그래프 생성
          </button>
        </div>
      )}
    </div>
  )
}
