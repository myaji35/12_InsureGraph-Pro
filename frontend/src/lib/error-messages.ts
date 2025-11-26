export const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  NETWORK_ERROR: '네트워크 연결을 확인해주세요',
  TIMEOUT: '요청 시간이 초과되었습니다',
  SERVER_UNAVAILABLE: '서버에 연결할 수 없습니다',

  // Auth errors
  UNAUTHORIZED: '로그인이 필요합니다',
  FORBIDDEN: '권한이 없습니다',
  INVALID_CREDENTIALS: '이메일 또는 비밀번호가 올바르지 않습니다',
  TOKEN_EXPIRED: '세션이 만료되었습니다. 다시 로그인해주세요',
  TOKEN_INVALID: '유효하지 않은 토큰입니다',
  EMAIL_ALREADY_EXISTS: '이미 사용 중인 이메일입니다',
  WEAK_PASSWORD: '비밀번호는 최소 8자 이상이어야 합니다',

  // Document errors
  FILE_TOO_LARGE: '파일 크기는 10MB 이하여야 합니다',
  INVALID_FILE_TYPE: 'PDF 파일만 업로드 가능합니다',
  DOCUMENT_NOT_FOUND: '문서를 찾을 수 없습니다',
  UPLOAD_FAILED: '파일 업로드에 실패했습니다',
  DOCUMENT_PROCESSING_FAILED: '문서 처리 중 오류가 발생했습니다',
  OCR_FAILED: '문서 인식(OCR)에 실패했습니다',
  EXTRACTION_FAILED: '문서 정보 추출에 실패했습니다',

  // Query errors
  QUERY_FAILED: '질의 처리에 실패했습니다',
  NO_DOCUMENTS_SELECTED: '문서를 선택해주세요',
  QUERY_TIMEOUT: '질의 처리 시간이 초과되었습니다',
  INVALID_QUERY: '유효하지 않은 질의입니다',
  NO_ANSWER_FOUND: '답변을 찾을 수 없습니다',

  // Customer errors
  CUSTOMER_NOT_FOUND: '고객을 찾을 수 없습니다',
  CUSTOMER_ALREADY_EXISTS: '이미 등록된 고객입니다',
  INVALID_CUSTOMER_DATA: '유효하지 않은 고객 정보입니다',

  // Graph errors
  GRAPH_NOT_FOUND: '그래프 데이터를 찾을 수 없습니다',
  NODE_NOT_FOUND: '노드를 찾을 수 없습니다',
  GRAPH_QUERY_FAILED: '그래프 조회에 실패했습니다',

  // Validation errors
  VALIDATION_ERROR: '입력값이 유효하지 않습니다',
  REQUIRED_FIELD: '필수 항목입니다',
  INVALID_EMAIL: '유효하지 않은 이메일 주소입니다',
  INVALID_PHONE: '유효하지 않은 전화번호입니다',
  INVALID_DATE: '유효하지 않은 날짜입니다',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요',

  // Generic errors
  INTERNAL_SERVER_ERROR: '서버 오류가 발생했습니다',
  BAD_REQUEST: '잘못된 요청입니다',
  NOT_FOUND: '요청한 리소스를 찾을 수 없습니다',
  METHOD_NOT_ALLOWED: '허용되지 않는 요청 방식입니다',
  CONFLICT: '충돌이 발생했습니다',
  UNKNOWN_ERROR: '알 수 없는 오류가 발생했습니다',
  SERVICE_UNAVAILABLE: '서비스를 일시적으로 사용할 수 없습니다',
}

export const getErrorMessage = (errorCode?: string, defaultMessage?: string): string => {
  if (!errorCode) {
    return defaultMessage || ERROR_MESSAGES.UNKNOWN_ERROR
  }

  // Convert error code to uppercase and replace spaces/dashes with underscores
  const normalizedCode = errorCode.toUpperCase().replace(/[\s-]/g, '_')

  return ERROR_MESSAGES[normalizedCode] || defaultMessage || ERROR_MESSAGES.UNKNOWN_ERROR
}

// HTTP status code to error message mapping
export const getErrorMessageFromStatus = (status: number): string => {
  const statusMessages: Record<number, string> = {
    400: ERROR_MESSAGES.BAD_REQUEST,
    401: ERROR_MESSAGES.UNAUTHORIZED,
    403: ERROR_MESSAGES.FORBIDDEN,
    404: ERROR_MESSAGES.NOT_FOUND,
    405: ERROR_MESSAGES.METHOD_NOT_ALLOWED,
    408: ERROR_MESSAGES.TIMEOUT,
    409: ERROR_MESSAGES.CONFLICT,
    429: ERROR_MESSAGES.RATE_LIMIT_EXCEEDED,
    500: ERROR_MESSAGES.INTERNAL_SERVER_ERROR,
    502: ERROR_MESSAGES.SERVER_UNAVAILABLE,
    503: ERROR_MESSAGES.SERVICE_UNAVAILABLE,
    504: ERROR_MESSAGES.TIMEOUT,
  }

  return statusMessages[status] || ERROR_MESSAGES.UNKNOWN_ERROR
}
