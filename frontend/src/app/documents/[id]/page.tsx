'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { useDocumentStore } from '@/store/document-store'
import {
  ArrowLeftIcon,
  TrashIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import { formatDate, formatDateTime } from '@/lib/utils'

export default function DocumentDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const { currentDocument, isLoading, fetchDocument, deleteDocument } = useDocumentStore()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    loadDocument()
  }, [params.id])

  const loadDocument = async () => {
    try {
      await fetchDocument(params.id)
    } catch (error) {
      console.error('Failed to load document:', error)
    }
  }

  const handleDelete = async () => {
    try {
      setIsDeleting(true)
      await deleteDocument(params.id)
      router.push('/documents')
    } catch (error) {
      console.error('Failed to delete document:', error)
      setIsDeleting(false)
    }
  }

  const getStatusDisplay = (status: string) => {
    const statusMap: Record<
      string,
      { icon: React.ComponentType<{ className?: string }>; color: string; text: string }
    > = {
      pending: { icon: ClockIcon, color: 'text-yellow-600', text: '대기 중' },
      processing: { icon: ClockIcon, color: 'text-blue-600', text: '처리 중' },
      ready: { icon: CheckCircleIcon, color: 'text-green-600', text: '완료' },
      failed: { icon: XCircleIcon, color: 'text-red-600', text: '실패' },
    }

    const { icon: Icon, color, text } = statusMap[status] || {
      icon: ClockIcon,
      color: 'text-gray-600',
      text: status,
    }

    return (
      <div className="flex items-center gap-2">
        <Icon className={`w-5 h-5 ${color}`} />
        <span className={`font-medium ${color}`}>{text}</span>
      </div>
    )
  }

  if (isLoading || !currentDocument) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/documents')}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            문서 목록으로
          </button>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <DocumentTextIcon className="w-16 h-16 text-primary-500" />
              <div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  {currentDocument.product_name}
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400">{currentDocument.insurer}</p>
              </div>
            </div>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="btn-secondary text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <TrashIcon className="w-5 h-5" />
              삭제
            </button>
          </div>
        </div>

        {/* Status */}
        <div className="card mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">문서 상태</p>
              {getStatusDisplay(currentDocument.status)}
            </div>
            {currentDocument.error_message && (
              <div className="flex items-center gap-2 text-red-600">
                <ExclamationTriangleIcon className="w-5 h-5" />
                <span className="text-sm">{currentDocument.error_message}</span>
              </div>
            )}
          </div>
        </div>

        {/* Basic Information */}
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-6">기본 정보</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">보험사</p>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100">{currentDocument.insurer}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">상품명</p>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                {currentDocument.product_name}
              </p>
            </div>
            {currentDocument.product_code && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">상품 코드</p>
                <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                  {currentDocument.product_code}
                </p>
              </div>
            )}
            {currentDocument.launch_date && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">출시일</p>
                <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                  {formatDate(currentDocument.launch_date)}
                </p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">문서 유형</p>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                {currentDocument.document_type || '약관'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">파일명</p>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100">{currentDocument.filename}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">업로드</p>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                {formatDateTime(currentDocument.created_at)}
              </p>
            </div>
            {currentDocument.processed_at && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">처리 완료</p>
                <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                  {formatDateTime(currentDocument.processed_at)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        {currentDocument.description && (
          <div className="card mb-6">
            <h3 className="text-lg font-semibold mb-4">설명</h3>
            <p className="text-gray-700 dark:text-gray-300">{currentDocument.description}</p>
          </div>
        )}

        {/* Tags */}
        {currentDocument.tags && currentDocument.tags.length > 0 && (
          <div className="card mb-6">
            <h3 className="text-lg font-semibold mb-4">태그</h3>
            <div className="flex flex-wrap gap-2">
              {currentDocument.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-primary-100 text-primary-700 text-sm rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Statistics */}
        {currentDocument.status === 'ready' && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-6">문서 통계</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                <p className="text-3xl font-bold text-primary-600">
                  {currentDocument.chunk_count || 0}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">청크 수</p>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                <p className="text-3xl font-bold text-blue-600">
                  {currentDocument.entity_count || 0}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">엔티티 수</p>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                <p className="text-3xl font-bold text-green-600">
                  {currentDocument.relationship_count || 0}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">관계 수</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">문서 삭제</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              정말로 이 문서를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary"
                disabled={isDeleting}
              >
                취소
              </button>
              <button
                onClick={handleDelete}
                className="btn-primary bg-red-600 hover:bg-red-700"
                disabled={isDeleting}
              >
                {isDeleting ? '삭제 중...' : '삭제'}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
