"""
Tests for Authentication API Endpoints

Story 3.3: Authentication & Authorization 테스트
"""
import pytest
from uuid import UUID
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import UserRole, UserStatus


# TestClient
client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_user_data():
    """테스트 사용자 데이터"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "username": "testuser",
        "full_name": "Test User",
        "phone": "010-1234-5678",
        "organization_name": "Test GA"
    }


@pytest.fixture
def admin_credentials():
    """기본 관리자 계정"""
    return {
        "email": "admin@insuregraph.com",
        "password": "Admin123!"
    }


# ============================================================================
# Test POST /api/v1/auth/register
# ============================================================================


class TestRegister:
    """POST /api/v1/auth/register 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_register_success(self, test_user_data):
        """회원가입 성공"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["username"] == test_user_data["username"]
        assert data["user"]["role"] == "fp"
        assert data["user"]["status"] == "pending"
        assert "message" in data

    def test_register_minimal_fields(self):
        """최소 필드로 회원가입"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "minimal@example.com",
                "password": "Password123!",
                "username": "minimaluser",
                "full_name": "Minimal User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "minimal@example.com"

    def test_register_duplicate_email(self, test_user_data):
        """중복 이메일"""
        # First registration
        client.post("/api/v1/auth/register", json=test_user_data)

        # Duplicate registration
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        data = response.json()
        assert "EMAIL_ALREADY_EXISTS" in data["detail"]["error_code"]

    def test_register_invalid_email(self, test_user_data):
        """잘못된 이메일 형식"""
        test_user_data["email"] = "invalid-email"

        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, test_user_data):
        """짧은 비밀번호"""
        test_user_data["password"] = "short"

        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 422  # Validation error


# ============================================================================
# Test POST /api/v1/auth/login
# ============================================================================


class TestLogin:
    """POST /api/v1/auth/login 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_login_admin_success(self, admin_credentials):
        """관리자 로그인 성공"""
        response = client.post("/api/v1/auth/login", json=admin_credentials)

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "admin"
        assert data["user"]["status"] == "active"

    def test_login_invalid_email(self):
        """존재하지 않는 이메일"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "INVALID_CREDENTIALS" in data["detail"]["error_code"]

    def test_login_invalid_password(self, admin_credentials):
        """잘못된 비밀번호"""
        admin_credentials["password"] = "WrongPassword!"

        response = client.post("/api/v1/auth/login", json=admin_credentials)

        assert response.status_code == 401
        data = response.json()
        assert "INVALID_CREDENTIALS" in data["detail"]["error_code"]

    def test_login_pending_user(self, test_user_data):
        """승인 대기 사용자"""
        # Register user (status: pending)
        client.post("/api/v1/auth/register", json=test_user_data)

        # Try to login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 403
        data = response.json()
        assert "ACCOUNT_PENDING" in data["detail"]["error_code"]


# ============================================================================
# Test POST /api/v1/auth/refresh
# ============================================================================


class TestRefreshToken:
    """POST /api/v1/auth/refresh 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_refresh_success(self, admin_credentials):
        """토큰 갱신 성공"""
        # Login to get refresh token
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # New tokens should be different
        assert data["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self):
        """유효하지 않은 토큰"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401

    def test_refresh_with_access_token(self, admin_credentials):
        """Access token으로 갱신 시도"""
        # Login to get access token
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]

        # Try to refresh with access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )

        assert response.status_code == 401
        data = response.json()
        assert "INVALID_TOKEN_TYPE" in data["detail"]["error_code"]


# ============================================================================
# Test POST /api/v1/auth/logout
# ============================================================================


class TestLogout:
    """POST /api/v1/auth/logout 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_logout_success(self, admin_credentials):
        """로그아웃 성공"""
        # Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Try to refresh with revoked token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 401


# ============================================================================
# Test GET /api/v1/auth/me
# ============================================================================


class TestGetMe:
    """GET /api/v1/auth/me 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_get_me_success(self, admin_credentials):
        """현재 사용자 조회 성공"""
        # Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]

        # Get me
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == admin_credentials["email"]
        assert data["user"]["role"] == "admin"

    def test_get_me_no_token(self):
        """토큰 없이 요청"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No credentials

    def test_get_me_invalid_token(self):
        """유효하지 않은 토큰"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


# ============================================================================
# Test PATCH /api/v1/auth/me
# ============================================================================


class TestUpdateProfile:
    """PATCH /api/v1/auth/me 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_update_profile_success(self, admin_credentials):
        """프로필 수정 성공"""
        # Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]

        # Update profile
        response = client.patch(
            "/api/v1/auth/me",
            json={
                "full_name": "Updated Admin",
                "phone": "010-9999-8888"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Admin"
        assert data["phone"] == "010-9999-8888"

    def test_update_profile_partial(self, admin_credentials):
        """부분 수정"""
        # Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]

        # Update only phone
        response = client.patch(
            "/api/v1/auth/me",
            json={"phone": "010-1111-2222"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "010-1111-2222"


# ============================================================================
# Test POST /api/v1/auth/change-password
# ============================================================================


class TestChangePassword:
    """POST /api/v1/auth/change-password 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_change_password_success(self, admin_credentials):
        """비밀번호 변경 성공"""
        # Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]

        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": admin_credentials["password"],
                "new_password": "NewAdmin123!"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify new password works
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": admin_credentials["email"],
                "password": "NewAdmin123!"
            }
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, admin_credentials):
        """현재 비밀번호 오류"""
        # Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        access_token = login_response.json()["access_token"]

        # Try to change with wrong current password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongPassword!",
                "new_password": "NewAdmin123!"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "INVALID_PASSWORD" in data["detail"]["error_code"]


# ============================================================================
# Integration Tests
# ============================================================================


class TestAuthIntegration:
    """통합 테스트"""

    def setup_method(self):
        """각 테스트 전에 사용자 초기화"""
        from app.api.v1.endpoints.auth import _users, _users_by_email, _refresh_tokens
        # Keep only admin
        admin_email = "admin@insuregraph.com"
        if admin_email in _users_by_email:
            admin_id = _users_by_email[admin_email]
            admin = _users[admin_id]
            _users.clear()
            _users_by_email.clear()
            _refresh_tokens.clear()
            _users[admin_id] = admin
            _users_by_email[admin_email] = admin_id

    def test_full_auth_flow(self, test_user_data):
        """전체 인증 플로우"""
        # 1. Register
        register_response = client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["user"]["user_id"]

        # 2. Try to login (should fail - pending)
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert login_response.status_code == 403

        # 3. Admin approves (admin login first)
        admin_login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@insuregraph.com", "password": "Admin123!"}
        )
        admin_token = admin_login.json()["access_token"]

        approve_response = client.patch(
            f"/api/v1/auth/users/{user_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert approve_response.status_code == 200

        # 4. Login (should succeed)
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # 5. Get profile
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200

        # 6. Update profile
        update_response = client.patch(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert update_response.status_code == 200

        # 7. Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_refresh_token = refresh_response.json()["refresh_token"]

        # 8. Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 200
