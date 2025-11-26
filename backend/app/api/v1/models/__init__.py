"""
API Models Package
"""
from app.api.v1.models.query import (
    QueryRequest,
    QueryResponse,
    QueryStatusResponse,
    QueryMetrics,
    StreamChunk,
    ErrorResponse,
    HealthCheckResponse,
    QueryStrategyAPI,
)

from app.api.v1.models.document import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentMetadata,
    DocumentListResponse,
    DocumentListItem,
    DocumentContentResponse,
    DocumentUpdateRequest,
    DocumentStatsResponse,
    DocumentErrorResponse,
    DocumentStatus,
    DocumentType,
)

from app.api.v1.models.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    TokenResponse,
    LogoutResponse,
    MeResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    AuthErrorResponse,
)

__all__ = [
    # Query models
    "QueryRequest",
    "QueryResponse",
    "QueryStatusResponse",
    "QueryMetrics",
    "StreamChunk",
    "ErrorResponse",
    "HealthCheckResponse",
    "QueryStrategyAPI",
    # Document models
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "DocumentMetadata",
    "DocumentListResponse",
    "DocumentListItem",
    "DocumentContentResponse",
    "DocumentUpdateRequest",
    "DocumentStatsResponse",
    "DocumentErrorResponse",
    "DocumentStatus",
    "DocumentType",
    # Auth models
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "RegisterResponse",
    "RefreshTokenRequest",
    "TokenResponse",
    "LogoutResponse",
    "MeResponse",
    "ChangePasswordRequest",
    "UpdateProfileRequest",
    "AuthErrorResponse",
]
