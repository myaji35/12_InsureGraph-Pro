# Authentication Guide

Complete guide for authentication and authorization in InsureGraph Pro API.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [User Roles](#user-roles)
3. [Authentication Flow](#authentication-flow)
4. [API Reference](#api-reference)
5. [Code Examples](#code-examples)
6. [Security Best Practices](#security-best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🔐 Overview

InsureGraph Pro uses **JWT (JSON Web Tokens)** for stateless authentication.

### Token Types

| Token Type | Lifetime | Purpose | Storage |
|------------|----------|---------|---------|
| **Access Token** | 15 minutes | API authentication | Memory/httpOnly cookie |
| **Refresh Token** | 1 day | Renew access token | httpOnly cookie |

### Token Format

**Access Token Payload**:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "fp",
  "exp": 1640000000,
  "type": "access"
}
```

**Refresh Token Payload**:
```json
{
  "sub": "user_id",
  "exp": 1640086400,
  "type": "refresh"
}
```

---

## 👥 User Roles

### Role Hierarchy

```
ADMIN (관리자)
└─ All permissions
   ├─ User management
   ├─ System settings
   └─ Access all data

FP_MANAGER (GA 지점장)
└─ Branch management
   ├─ Manage FPs in branch
   ├─ View branch stats
   └─ Access team data

FP (보험설계사)
└─ Personal workspace
   ├─ Own documents
   ├─ Own queries
   └─ Profile management

USER (일반 사용자)
└─ Limited access
   ├─ View public docs
   └─ Basic queries
```

### Default Role Assignment

- New registrations → `FP` role
- Status → `pending` (requires admin approval)

---

## 🔄 Authentication Flow

### Complete Flow Diagram

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. POST /auth/register
     ├──────────────────────────►┌──────────┐
     │                            │  Server  │
     │◄──────────────────────────┤          │
     │   status: "pending"        └──────────┘
     │
     │ 2. Admin approves
     ├──────────────────────────►┌──────────┐
     │                            │  Admin   │
     │◄──────────────────────────┤          │
     │   status: "active"         └──────────┘
     │
     │ 3. POST /auth/login
     ├──────────────────────────►┌──────────┐
     │                            │  Server  │
     │◄──────────────────────────┤          │
     │   access_token             └──────────┘
     │   refresh_token
     │
     │ 4. Use API (with access_token)
     ├──────────────────────────►┌──────────┐
     │   Authorization: Bearer    │   API    │
     │◄──────────────────────────┤          │
     │   Response + data          └──────────┘
     │
     │ 5. Access token expires
     │ POST /auth/refresh
     ├──────────────────────────►┌──────────┐
     │   refresh_token            │  Server  │
     │◄──────────────────────────┤          │
     │   new access_token         └──────────┘
     │   new refresh_token
     │
     │ 6. Logout
     │ POST /auth/logout
     ├──────────────────────────►┌──────────┐
     │   refresh_token            │  Server  │
     │◄──────────────────────────┤          │
     │   Token revoked            └──────────┘
```

---

## 📡 API Reference

### 1. Register

**Endpoint**: `POST /api/v1/auth/register`

**Request**:
```json
{
  "email": "fp@example.com",
  "password": "SecurePassword123!",
  "username": "fp_kim",
  "full_name": "김설계",
  "phone": "010-1234-5678",
  "organization_name": "삼성GA 강남지점"
}
```

**Response** (201 Created):
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "fp@example.com",
    "username": "fp_kim",
    "full_name": "김설계",
    "role": "fp",
    "status": "pending",
    "organization_name": "삼성GA 강남지점",
    "created_at": "2025-11-25T10:00:00",
    "is_email_verified": false
  },
  "message": "Registration successful. Please wait for admin approval."
}
```

**Password Requirements**:
- Minimum 8 characters
- Recommended: Mix of upper/lower case, numbers, symbols

---

### 2. Login

**Endpoint**: `POST /api/v1/auth/login`

**Request**:
```json
{
  "email": "fp@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "fp@example.com",
    "role": "fp",
    "status": "active"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:

- **401 Unauthorized** - Invalid credentials
- **403 Forbidden** - Account pending/suspended

---

### 3. Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Note**: Old refresh token is revoked, new one is issued.

---

### 4. Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "fp@example.com",
    "username": "fp_kim",
    "full_name": "김설계",
    "role": "fp",
    "status": "active",
    "last_login_at": "2025-11-25T14:30:00"
  }
}
```

---

### 5. Update Profile

**Endpoint**: `PATCH /api/v1/auth/me`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "full_name": "김설계 (수정)",
  "phone": "010-9999-8888"
}
```

**Response** (200 OK):
```json
{
  "user_id": "...",
  "full_name": "김설계 (수정)",
  "phone": "010-9999-8888"
}
```

---

### 6. Change Password

**Endpoint**: `POST /api/v1/auth/change-password`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

---

### 7. Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

---

## 💻 Code Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "fp@example.com",
        "password": "SecurePassword123!",
        "username": "fp_kim",
        "full_name": "김설계"
    }
)
print(response.json())

# 2. Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "fp@example.com",
        "password": "SecurePassword123!"
    }
)
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 3. Use API with token
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(
    f"{BASE_URL}/auth/me",
    headers=headers
)
print(response.json())

# 4. Refresh token
response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": refresh_token}
)
new_tokens = response.json()

# 5. Logout
response = requests.post(
    f"{BASE_URL}/auth/logout",
    json={"refresh_token": refresh_token},
    headers=headers
)
```

---

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// 1. Register
async function register() {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: 'fp@example.com',
      password: 'SecurePassword123!',
      username: 'fp_kim',
      full_name: '김설계'
    })
  });
  return await response.json();
}

// 2. Login
async function login() {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: 'fp@example.com',
      password: 'SecurePassword123!'
    })
  });
  const data = await response.json();

  // Store tokens securely
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data;
}

// 3. Use API with token
async function getProfile() {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  return await response.json();
}

// 4. Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({refresh_token: refreshToken})
  });

  const data = await response.json();

  // Update tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data;
}

// 5. Auto-refresh logic
async function apiCall(url, options = {}) {
  let accessToken = localStorage.getItem('access_token');

  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`
    }
  });

  // If 401, try to refresh
  if (response.status === 401) {
    await refreshToken();
    accessToken = localStorage.getItem('access_token');

    response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`
      }
    });
  }

  return response;
}
```

---

### React Hook

```typescript
// useAuth.ts
import { useState, useEffect } from 'react';

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export function useAuth() {
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [user, setUser] = useState(null);

  // Login
  async function login(email: string, password: string) {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });

    const data = await response.json();

    setTokens({
      accessToken: data.access_token,
      refreshToken: data.refresh_token
    });
    setUser(data.user);

    // Store in localStorage or cookies
    localStorage.setItem('tokens', JSON.stringify(data));
  }

  // Logout
  async function logout() {
    if (tokens) {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokens.accessToken}`
        },
        body: JSON.stringify({refresh_token: tokens.refreshToken})
      });
    }

    setTokens(null);
    setUser(null);
    localStorage.removeItem('tokens');
  }

  // Auto-refresh
  useEffect(() => {
    if (!tokens) return;

    const interval = setInterval(async () => {
      // Refresh 5 minutes before expiry
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({refresh_token: tokens.refreshToken})
      });

      const data = await response.json();
      setTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token
      });
    }, 10 * 60 * 1000); // Every 10 minutes

    return () => clearInterval(interval);
  }, [tokens]);

  return {
    user,
    tokens,
    login,
    logout,
    isAuthenticated: !!tokens
  };
}
```

---

## 🔒 Security Best Practices

### 1. Token Storage

**❌ Don't**:
```javascript
// XSS vulnerable
localStorage.setItem('token', token);
```

**✅ Do**:
```javascript
// Use httpOnly cookies (set by server)
// Or encrypt before storing
```

### 2. Token Transmission

**Always use HTTPS in production**:
```
✅ https://api.insuregraph.com
❌ http://api.insuregraph.com
```

### 3. Token Rotation

The API automatically rotates refresh tokens:
- Old refresh token is revoked
- New refresh token is issued
- Prevents token replay attacks

### 4. Password Security

**Requirements**:
- Minimum 8 characters
- Use strong passwords

**Server-side** (automatic):
- Passwords hashed with bcrypt
- Salted hashing
- No plain-text storage

### 5. Rate Limiting

Login endpoint is rate-limited:
- **5 requests per 5 minutes**
- Prevents brute-force attacks

### 6. CORS

Configure CORS properly:
```python
# settings
CORS_ORIGINS = "https://app.insuregraph.com"
```

---

## 🐛 Troubleshooting

### "INVALID_CREDENTIALS" Error

**Cause**: Wrong email/password

**Solution**:
1. Double-check credentials
2. Ensure account is active (not pending/suspended)

---

### "ACCOUNT_PENDING" Error

**Cause**: Account awaiting admin approval

**Solution**:
1. Wait for admin approval
2. Contact admin

---

### "Token has expired" Error

**Cause**: Access token expired (> 15 minutes)

**Solution**:
1. Use refresh token to get new access token
2. Implement auto-refresh logic

---

### "REFRESH_TOKEN_REVOKED" Error

**Cause**: Refresh token was already used or logout

**Solution**:
1. Login again
2. Don't reuse old refresh tokens

---

### 401 on Protected Endpoint

**Cause**: Missing or invalid token

**Solution**:
1. Check `Authorization` header format: `Bearer {token}`
2. Ensure token hasn't expired
3. Verify token is access token (not refresh)

---

## 🆘 Support

For authentication issues:

1. Check error response for `error_code`
2. Review this guide for solutions
3. Contact support: support@insuregraph.com

---

**Last Updated**: 2025-11-25
