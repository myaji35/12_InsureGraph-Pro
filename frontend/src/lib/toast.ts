import toast from 'react-hot-toast'

/**
 * Toast notification utilities
 * Centralized error and success message handling
 */

export const showSuccess = (message: string, duration = 4000) => {
  toast.success(message, {
    duration,
    position: 'top-right',
    className: 'dark:bg-dark-surface dark:text-gray-100',
    iconTheme: {
      primary: '#10b981',
      secondary: '#fff',
    },
  })
}

export const showError = (message: string, duration = 5000) => {
  toast.error(message, {
    duration,
    position: 'top-right',
    className: 'dark:bg-dark-surface dark:text-gray-100',
    iconTheme: {
      primary: '#ef4444',
      secondary: '#fff',
    },
  })
}

export const showLoading = (message: string) => {
  return toast.loading(message, {
    position: 'top-right',
    className: 'dark:bg-dark-surface dark:text-gray-100',
  })
}

export const showInfo = (message: string, duration = 4000) => {
  toast(message, {
    duration,
    position: 'top-right',
    icon: 'ℹ️',
    className: 'dark:bg-dark-surface dark:text-gray-100',
  })
}

export const dismissToast = (toastId: string) => {
  toast.dismiss(toastId)
}

export const dismissAllToasts = () => {
  toast.dismiss()
}

/**
 * Error code to user-friendly message mapping
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  'AUTH_INVALID_CREDENTIALS': '이메일 또는 비밀번호가 올바르지 않습니다.',
  'AUTH_USER_NOT_FOUND': '사용자를 찾을 수 없습니다.',
  'AUTH_EMAIL_ALREADY_EXISTS': '이미 사용 중인 이메일입니다.',
  'AUTH_WEAK_PASSWORD': '비밀번호는 최소 8자 이상이어야 합니다.',
  'AUTH_TOKEN_EXPIRED': '세션이 만료되었습니다. 다시 로그인해주세요.',
  'AUTH_UNAUTHORIZED': '인증이 필요합니다.',

  // Document errors
  'DOCUMENT_NOT_FOUND': '문서를 찾을 수 없습니다.',
  'DOCUMENT_UPLOAD_FAILED': '문서 업로드에 실패했습니다.',
  'DOCUMENT_INVALID_FORMAT': '지원하지 않는 파일 형식입니다.',
  'DOCUMENT_TOO_LARGE': '파일 크기가 너무 큽니다. (최대 10MB)',
  'DOCUMENT_PROCESSING_FAILED': '문서 처리에 실패했습니다.',

  // Query errors
  'QUERY_FAILED': '질의 처리에 실패했습니다.',
  'QUERY_NO_DOCUMENTS': '질의할 문서를 선택해주세요.',
  'QUERY_TIMEOUT': '질의 처리 시간이 초과되었습니다.',

  // Graph errors
  'GRAPH_LOAD_FAILED': '그래프 로드에 실패했습니다.',
  'NODE_NOT_FOUND': '노드를 찾을 수 없습니다.',

  // Customer errors
  'CUSTOMER_NOT_FOUND': '고객을 찾을 수 없습니다.',
  'CUSTOMER_CREATE_FAILED': '고객 생성에 실패했습니다.',
  'CUSTOMER_UPDATE_FAILED': '고객 정보 수정에 실패했습니다.',

  // Network errors
  'NETWORK_ERROR': '네트워크 오류가 발생했습니다.',
  'SERVER_ERROR': '서버 오류가 발생했습니다.',
  'TIMEOUT': '요청 시간이 초과되었습니다.',

  // Generic
  'UNKNOWN_ERROR': '알 수 없는 오류가 발생했습니다.',
}

/**
 * Handle API error and show appropriate toast
 */
export const handleApiError = (error: any) => {
  let message = ERROR_MESSAGES['UNKNOWN_ERROR']

  // Check if error has a response with error code
  if (error?.response?.data?.error_code) {
    const errorCode = error.response.data.error_code
    message = ERROR_MESSAGES[errorCode] || error.response.data.message || message
  }
  // Check if error has a message
  else if (error?.response?.data?.message) {
    message = error.response.data.message
  }
  // Check if error is a string
  else if (typeof error === 'string') {
    message = error
  }
  // Network error
  else if (error?.message === 'Network Error') {
    message = ERROR_MESSAGES['NETWORK_ERROR']
  }
  // Timeout error
  else if (error?.code === 'ECONNABORTED') {
    message = ERROR_MESSAGES['TIMEOUT']
  }

  showError(message)
}

/**
 * Success message helpers
 */
export const SUCCESS_MESSAGES = {
  // Authentication
  LOGIN_SUCCESS: '로그인 성공!',
  REGISTER_SUCCESS: '회원가입이 완료되었습니다.',
  LOGOUT_SUCCESS: '로그아웃되었습니다.',

  // Documents
  DOCUMENT_UPLOADED: '문서가 업로드되었습니다.',
  DOCUMENT_DELETED: '문서가 삭제되었습니다.',

  // Query
  QUERY_SUCCESS: '질의가 완료되었습니다.',

  // Customer
  CUSTOMER_CREATED: '고객이 생성되었습니다.',
  CUSTOMER_UPDATED: '고객 정보가 수정되었습니다.',
  CUSTOMER_DELETED: '고객이 삭제되었습니다.',
}
