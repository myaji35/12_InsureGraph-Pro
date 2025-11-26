# InsureGraph Pro API Guide

**Version**: 1.0.0
**Base URL**: `http://localhost:8000`
**API Version**: v1

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Best Practices](#best-practices)

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Test API

```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/api/v1/
```

---

## 🔐 Authentication

### Overview

InsureGraph Pro uses **JWT (JSON Web Tokens)** for authentication.

**Token Types**:
- **Access Token**: Short-lived (15 minutes), used for API requests
- **Refresh Token**: Long-lived (1 day), used to obtain new access tokens

### Authentication Flow

```
1. Register    → POST /api/v1/auth/register
2. Admin Approval → PATCH /api/v1/auth/users/{id}/approve
3. Login       → POST /api/v1/auth/login (get tokens)
4. Use API     → Add "Authorization: Bearer {access_token}" header
5. Refresh     → POST /api/v1/auth/refresh (when access token expires)
```

### Example: Complete Authentication

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fp@example.com",
    "password": "SecurePassword123!",
    "username": "fp_kim",
    "full_name": "김설계"
  }'

# Response: status: "pending" (waiting for admin approval)

# 2. Admin approves (using admin credentials)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@insuregraph.com",
    "password": "Admin123!"
  }'

# Get admin token, then approve
curl -X PATCH http://localhost:8000/api/v1/auth/users/{user_id}/approve \
  -H "Authorization: Bearer {admin_token}"

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fp@example.com",
    "password": "SecurePassword123!"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}

# 4. Use API with access token
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer {access_token}"

# 5. Refresh token when expired
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "{refresh_token}"
  }'
```

**See [AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md) for details.**

---

## 📡 API Endpoints

### System Endpoints

#### Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "app": "InsureGraph Pro",
  "version": "1.0.0",
  "environment": "development"
}
```

#### API Root
```
GET /api/v1/
```

**Response**: List of all available endpoints

---

### Authentication Endpoints

#### Register
```
POST /api/v1/auth/register
```

**Request**:
```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "username": "user_name",
  "full_name": "Full Name",
  "phone": "010-1234-5678",
  "organization_name": "Organization"
}
```

**Response**:
```json
{
  "user": {
    "user_id": "...",
    "email": "user@example.com",
    "status": "pending"
  },
  "message": "Registration successful. Please wait for admin approval."
}
```

#### Login
```
POST /api/v1/auth/login
```

**Request**:
```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```

**Response**:
```json
{
  "user": {...},
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Get Current User
```
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "user": {
    "user_id": "...",
    "email": "user@example.com",
    "role": "fp",
    "status": "active"
  }
}
```

---

### Query Endpoints

#### Execute Query (Synchronous)
```
POST /api/v1/query
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "query": "급성심근경색증 보장 금액은?",
  "strategy": "standard",
  "max_results": 10,
  "include_citations": true,
  "include_follow_ups": true
}
```

**Response**:
```json
{
  "query_id": "a1b2c3d4",
  "query": "급성심근경색증 보장 금액은?",
  "answer": "급성심근경색증의 경우 진단비 5,000만원이 보장됩니다.",
  "format": "text",
  "confidence": 0.92,
  "citations": [...],
  "follow_up_suggestions": ["대기기간은 얼마나 되나요?"],
  "metrics": {
    "total_duration_ms": 287.5,
    "cache_hit": false
  }
}
```

#### Execute Query (Asynchronous)
```
POST /api/v1/query/async
Authorization: Bearer {access_token}
```

**Response** (202 Accepted):
```json
{
  "query_id": "a1b2c3d4",
  "status": "pending",
  "progress": 0
}
```

#### Get Query Status
```
GET /api/v1/query/{query_id}/status
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "query_id": "a1b2c3d4",
  "status": "completed",
  "progress": 100,
  "result": {...}
}
```

---

### Document Endpoints

#### Upload Document
```
POST /api/v1/documents/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request** (multipart/form-data):
```
file: [PDF file]
insurer: 삼성화재
product_name: 슈퍼마일리지보험
product_code: P12345
launch_date: 2023-01-15
description: 종신보험 상품
document_type: insurance_policy
tags: 종신보험,CI,암
```

**Response** (201 Created):
```json
{
  "document_id": "123e4567-...",
  "job_id": "abc12345-...",
  "status": "processing",
  "message": "Document uploaded successfully",
  "gcs_uri": "gs://..."
}
```

#### List Documents
```
GET /api/v1/documents?page=1&page_size=20&insurer=삼성화재
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `insurer` (optional): Filter by insurer
- `status` (optional): Filter by status
- `document_type` (optional): Filter by type
- `search` (optional): Search by product name
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Page size

**Response**:
```json
{
  "documents": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

#### Get Document
```
GET /api/v1/documents/{document_id}
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "document_id": "...",
  "insurer": "삼성화재",
  "product_name": "슈퍼마일리지보험",
  "status": "completed",
  "total_pages": 45,
  "total_articles": 123
}
```

#### Get Document Content
```
GET /api/v1/documents/{document_id}/content
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "document_id": "...",
  "total_articles": 123,
  "articles": [
    {
      "article_num": "제1조",
      "title": "용어의 정의",
      "page": 5
    }
  ]
}
```

#### Delete Document
```
DELETE /api/v1/documents/{document_id}
Authorization: Bearer {access_token}
```

**Response**: 204 No Content

---

### Monitoring Endpoints

#### Prometheus Metrics
```
GET /api/v1/monitoring/metrics
```

**Response** (text/plain):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/"} 150
```

#### System Stats
```
GET /api/v1/monitoring/stats
```

**Response**:
```json
{
  "stats": {
    "uptime_seconds": 3600,
    "total_requests": 1234,
    "error_rate": 0.01,
    "response_time": {
      "p50_ms": 45.2,
      "p95_ms": 125.8,
      "p99_ms": 250.3
    }
  }
}
```

#### Detailed Health Check
```
GET /api/v1/monitoring/health/detailed
```

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "database": "ok",
    "cache": "ok",
    "api": "ok"
  },
  "metrics": {...}
}
```

---

## ⚠️ Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": {
    "error_code": "ERROR_CODE",
    "error_message": "Human-readable message",
    "details": {}
  }
}
```

### Common Error Codes

**Authentication (401)**:
- `INVALID_CREDENTIALS`: Wrong email/password
- `INVALID_TOKEN`: Invalid or expired token
- `USER_NOT_FOUND`: User doesn't exist

**Authorization (403)**:
- `ACCOUNT_PENDING`: Account pending approval
- `ACCOUNT_INACTIVE`: Account suspended
- `ACCESS_DENIED`: Insufficient permissions

**Not Found (404)**:
- `DOCUMENT_NOT_FOUND`: Document doesn't exist
- `QUERY_NOT_FOUND`: Query doesn't exist

**Validation (422)**:
- Pydantic validation errors

**Rate Limiting (429)**:
- `RATE_LIMIT_EXCEEDED`: Too many requests

**Server Error (500)**:
- `INTERNAL_SERVER_ERROR`: Unexpected error

### Example Error Response

```json
{
  "detail": {
    "error_code": "INVALID_CREDENTIALS",
    "error_message": "Invalid email or password",
    "timestamp": "2025-11-25T20:30:00"
  }
}
```

---

## 🚦 Rate Limiting

### Default Limits

- **Global**: 100 requests per minute (per IP)
- **Login**: 5 requests per 5 minutes
- **Query**: 20 requests per minute (per user)
- **Upload**: 10 requests per hour (per user)

### Rate Limit Headers

Every response includes:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 2025-11-25T21:00:00Z
```

### When Limit Exceeded

**Status**: 429 Too Many Requests

**Response**:
```json
{
  "detail": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "error_message": "Too many requests. Please try again later.",
    "limit": 100,
    "reset": "2025-11-25T21:00:00Z"
  }
}
```

**Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
Retry-After: 60
```

---

## ✅ Best Practices

### 1. Always Use HTTPS in Production

```bash
# Development
http://localhost:8000

# Production
https://api.insuregraph.com
```

### 2. Store Tokens Securely

**❌ Don't**:
```javascript
localStorage.setItem('token', token); // XSS vulnerable
```

**✅ Do**:
```javascript
// Use httpOnly cookies
document.cookie = `token=${token}; HttpOnly; Secure; SameSite=Strict`;
```

### 3. Handle Token Expiration

```javascript
async function apiCall(url, options) {
  let response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  // If 401, try to refresh
  if (response.status === 401) {
    const newToken = await refreshToken();
    response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${newToken}`
      }
    });
  }

  return response;
}
```

### 4. Respect Rate Limits

```javascript
// Check rate limit headers
const remaining = response.headers.get('X-RateLimit-Remaining');
if (remaining < 10) {
  console.warn('Approaching rate limit!');
}
```

### 5. Use Pagination

```javascript
// Always paginate large datasets
const response = await fetch('/api/v1/documents?page=1&page_size=20');
```

### 6. Handle Errors Gracefully

```javascript
try {
  const response = await fetch('/api/v1/query', {...});
  const data = await response.json();

  if (!response.ok) {
    // Handle API error
    console.error(data.detail.error_code, data.detail.error_message);
  }
} catch (error) {
  // Handle network error
  console.error('Network error:', error);
}
```

### 7. Use Appropriate HTTP Methods

- `GET`: Retrieve data
- `POST`: Create resource
- `PATCH`: Update resource (partial)
- `PUT`: Update resource (complete)
- `DELETE`: Delete resource

### 8. Include Request IDs for Debugging

Every response has `X-Request-ID` header:

```javascript
const requestId = response.headers.get('X-Request-ID');
console.log('Request ID:', requestId); // For debugging
```

---

## 📚 Additional Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Authentication Guide**: [AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md)
- **GitHub Repository**: https://github.com/your-org/insuregraph-pro

---

## 🆘 Support

For issues or questions:

1. Check the [API Documentation](http://localhost:8000/docs)
2. Review error messages and codes
3. Contact support: support@insuregraph.com

---

**Last Updated**: 2025-11-25
**API Version**: 1.0.0
