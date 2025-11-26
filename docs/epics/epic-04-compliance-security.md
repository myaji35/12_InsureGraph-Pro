# Epic 4: Compliance & Security

**Epic ID**: EPIC-04
**Priority**: Critical (P0)
**Phase**: Phase 1 (MVP)
**Estimated Duration**: 3-4 weeks
**Team**: Backend Engineers, Security Engineer, Compliance Officer

---

## Executive Summary

Implement security controls and compliance features to meet financial regulatory requirements and protect customer data. This epic is critical for legal operation in the Korean insurance market and earning user trust.

### Business Value

- **Regulatory Approval**: Required for Financial Sandbox designation
- **User Trust**: FPs and customers trust the platform with sensitive data
- **Risk Mitigation**: Prevents data breaches, fines, and lawsuits
- **Market Access**: Enables B2B deals with GA organizations

### Success Criteria

- ✅ Pass Financial Sandbox compliance audit
- ✅ Zero PII leaks in logs or error messages
- ✅ 100% audit trail coverage for sensitive operations
- ✅ Pass penetration testing with no critical vulnerabilities
- ✅ OWASP Top 10 vulnerabilities addressed

---

## User Stories

### Story 4.1: Authentication & Authorization (RBAC)

**Story ID**: STORY-4.1
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As a System Administrator,
I want role-based access control for users,
So that FPs can only access their own data and admins can manage the system.
```

#### Acceptance Criteria

**Given** I am an FP user
**When** I try to access another FP's customer data
**Then** I should be denied with 403 Forbidden error

**Given** I am a GA Manager
**When** I access analytics
**Then** I should see data for all FPs in my GA, but not other GAs

**Given** I am an Admin user
**When** I access system features
**Then** I should be able to:
- Ingest new policies
- View all users
- Access system logs
- Manage user roles

**Given** I am logged in with an expired JWT
**When** I make an API request
**Then** I should:
- Receive 401 Unauthorized
- Be redirected to login page
- Have my refresh token invalidated if it's also expired

#### Technical Tasks

- [ ] Design role hierarchy
  - [ ] Roles: `fp`, `ga_manager`, `admin`, `end_user` (Phase 2)
  - [ ] Permissions: Define granular permissions per resource
- [ ] Implement authentication service
  - [ ] `POST /api/v1/auth/login` - Issue JWT access + refresh tokens
  - [ ] `POST /api/v1/auth/refresh` - Refresh access token
  - [ ] `POST /api/v1/auth/logout` - Revoke tokens
  - [ ] `POST /api/v1/auth/reset-password` - Password reset flow
- [ ] Implement JWT token handling
  - [ ] Generate tokens with role and permissions
  - [ ] Access token expiry: 15 minutes
  - [ ] Refresh token expiry: 24 hours
  - [ ] Token blacklist for logout (Redis)
- [ ] Implement authorization middleware
  - [ ] Verify JWT signature and expiry
  - [ ] Check user role and permissions
  - [ ] Inject user context into request
- [ ] Implement RBAC decorators
  - [ ] `@require_role("fp")` - Require minimum role
  - [ ] `@require_permission("customers:read")` - Require specific permission
- [ ] Write unit tests for auth logic
- [ ] Write integration tests for protected endpoints
- [ ] Security review and penetration testing

#### Dependencies

- PostgreSQL users table created
- Redis for token blacklist

#### Technical Notes

**JWT Payload Structure**:

```json
{
  "sub": "user_uuid",
  "email": "fp@example.com",
  "role": "fp",
  "ga_id": "ga_uuid",
  "tier": "pro",
  "permissions": [
    "customers:read",
    "customers:write",
    "queries:execute",
    "policies:read"
  ],
  "iat": 1700900000,
  "exp": 1700900900
}
```

**FastAPI Authorization Middleware**:

```python
# app/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT and extract user
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check if token is blacklisted
        if is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token revoked")

        return User(
            id=user_id,
            email=payload.get("email"),
            role=payload.get("role"),
            ga_id=payload.get("ga_id"),
            permissions=payload.get("permissions", [])
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    """
    Decorator to require minimum role
    """
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            role_hierarchy = ["end_user", "fp", "ga_manager", "admin"]

            if role_hierarchy.index(current_user.role) < role_hierarchy.index(required_role):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator

def require_permission(required_permission: str):
    """
    Decorator to require specific permission
    """
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if required_permission not in current_user.permissions:
                raise HTTPException(status_code=403, detail=f"Missing permission: {required_permission}")

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator

# Usage in routes
@router.get("/api/v1/customers")
@require_role("fp")
async def list_customers(current_user: User = Depends(get_current_user)):
    """
    FPs can only see their own customers
    """
    return get_customers_for_fp(current_user.id)

@router.post("/api/v1/policies/ingest")
@require_role("admin")
async def ingest_policy(current_user: User = Depends(get_current_user)):
    """
    Only admins can ingest policies
    """
    # ...
```

**Token Blacklist (Redis)**:

```python
def blacklist_token(token: str, expiry_seconds: int):
    """
    Add token to blacklist (for logout)
    """
    redis_client.setex(f"blacklist:{token}", expiry_seconds, "revoked")

def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted
    """
    return redis_client.exists(f"blacklist:{token}")
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] RBAC implemented and tested
- [ ] JWT authentication functional
- [ ] Token refresh working
- [ ] Authorization middleware enforced on all protected routes
- [ ] Unit tests passing (coverage > 90%)
- [ ] Integration tests passing
- [ ] Security review completed
- [ ] Documentation updated

---

### Story 4.2: PII Encryption & Data Protection

**Story ID**: STORY-4.2
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As a Compliance Officer,
I want all PII (Personal Identifiable Information) encrypted at rest,
So that we comply with data protection regulations and prevent data breaches.
```

#### Acceptance Criteria

**Given** a customer record is created
**When** it's stored in the database
**Then**:
- Name should be AES-256 encrypted
- Phone number should be SHA-256 hashed (one-way)
- Only birth year should be stored (not full DOB)
- Consent ID and date should be logged

**Given** an FP queries customer data
**When** the API returns the data
**Then**:
- Name should be decrypted on-the-fly (authorized access only)
- Phone should remain hashed (not reversible)
- Email (if any) should be partially masked (j***@example.com)

**Given** an error occurs with customer data
**When** it's logged
**Then**:
- PII should be stripped from log messages
- Only customer ID (UUID) should be logged
- No full names, phones, or emails in logs

#### Technical Tasks

- [ ] Setup encryption key management
  - [ ] Generate master encryption key (AES-256)
  - [ ] Store key in AWS KMS or HashiCorp Vault
  - [ ] Implement key rotation strategy
- [ ] Implement PII encryption service
  - [ ] `encrypt_name(name: str) -> bytes`
  - [ ] `decrypt_name(encrypted: bytes) -> str`
  - [ ] `hash_phone(phone: str) -> str`
  - [ ] `mask_birth_date(dob: str) -> dict`
  - [ ] `mask_email(email: str) -> str`
- [ ] Update database schema
  - [ ] `customers.name_encrypted BYTEA`
  - [ ] `customers.phone_hash VARCHAR(64)`
  - [ ] `customers.birth_year INTEGER`
  - [ ] Remove any plain-text PII columns
- [ ] Implement logging PII scrubber
  - [ ] Middleware to sanitize log messages
  - [ ] Detect and mask PII patterns (regex)
- [ ] Update API responses to decrypt PII
  - [ ] Only for authorized users
  - [ ] Log all PII accesses (audit trail)
- [ ] Write unit tests for encryption functions
- [ ] Test key rotation scenario
- [ ] Security audit

#### Dependencies

- AWS KMS or Vault provisioned
- Story 4.1 completed (authentication for authorization)

#### Technical Notes

**PII Encryption Service**:

```python
# app/core/pii.py
from cryptography.fernet import Fernet
import hashlib
import os

class PIIProtector:
    """
    Encrypt/decrypt PII with AES-256
    """
    def __init__(self):
        # Load encryption key from KMS
        self.encryption_key = self.load_key_from_kms()
        self.cipher = Fernet(self.encryption_key)

    def load_key_from_kms(self) -> bytes:
        """
        Load encryption key from AWS KMS
        """
        import boto3

        kms = boto3.client('kms')
        response = kms.decrypt(
            CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_KEY']),
            KeyId=os.environ['KMS_KEY_ID']
        )

        return response['Plaintext']

    def encrypt_name(self, name: str) -> bytes:
        """
        Encrypt customer name
        """
        return self.cipher.encrypt(name.encode('utf-8'))

    def decrypt_name(self, encrypted_name: bytes) -> str:
        """
        Decrypt customer name (authorized access only)
        """
        return self.cipher.decrypt(encrypted_name).decode('utf-8')

    @staticmethod
    def hash_phone(phone: str) -> str:
        """
        One-way hash of phone number (for deduplication)
        """
        # Remove non-digit characters
        phone_clean = ''.join(filter(str.isdigit, phone))

        # SHA-256 hash
        return hashlib.sha256(phone_clean.encode('utf-8')).hexdigest()

    @staticmethod
    def mask_birth_date(birth_date: str) -> dict:
        """
        Extract only birth year, discard month/day
        """
        year = birth_date.split('-')[0]
        return {
            'birth_year': int(year),
            'original_masked': True
        }

    @staticmethod
    def mask_email(email: str) -> str:
        """
        Partially mask email for display
        """
        local, domain = email.split('@')
        masked_local = local[0] + '***' if len(local) > 1 else '***'
        return f"{masked_local}@{domain}"

pii_protector = PIIProtector()
```

**Database Insert with Encryption**:

```python
# app/crud/customers.py
def create_customer(customer_data: CustomerCreate, fp_id: str) -> Customer:
    """
    Create customer with PII encryption
    """
    encrypted_name = pii_protector.encrypt_name(customer_data.name)
    phone_hash = pii_protector.hash_phone(customer_data.phone)
    birth_info = pii_protector.mask_birth_date(customer_data.birth_date)

    customer = Customer(
        id=uuid.uuid4(),
        fp_id=fp_id,
        name_encrypted=encrypted_name,
        phone_hash=phone_hash,
        birth_year=birth_info['birth_year'],
        gender=customer_data.gender,
        consent_id=customer_data.consent_id,
        consent_date=datetime.now(),
        created_at=datetime.now()
    )

    db.add(customer)
    db.commit()

    # Audit log (no PII!)
    audit_log(
        user_id=fp_id,
        action="customer_created",
        resource_id=customer.id,
        details={"consent_id": customer_data.consent_id}
    )

    return customer
```

**API Response with Decryption**:

```python
@router.get("/api/v1/customers/{customer_id}")
async def get_customer(customer_id: str, current_user: User = Depends(get_current_user)):
    """
    Get customer with PII decrypted (authorized access only)
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(404, "Customer not found")

    # Check authorization: FP can only access their own customers
    if customer.fp_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "Access denied")

    # Decrypt PII
    decrypted_name = pii_protector.decrypt_name(customer.name_encrypted)

    # Audit log
    audit_log(
        user_id=current_user.id,
        action="customer_pii_accessed",
        resource_id=customer.id
    )

    return {
        "id": customer.id,
        "name": decrypted_name,  # Decrypted for authorized user
        "birth_year": customer.birth_year,
        "gender": customer.gender,
        # Phone hash not returned (not reversible)
    }
```

**Log PII Scrubber**:

```python
import logging
import re

class PIIScrubberFilter(logging.Filter):
    """
    Filter to scrub PII from log messages
    """
    PII_PATTERNS = [
        (r'\b\d{3}-\d{4}-\d{4}\b', '[PHONE_REDACTED]'),  # Phone
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),  # Email
        (r'\b\d{6}-\d{7}\b', '[RRN_REDACTED]'),  # Korean RRN
    ]

    def filter(self, record):
        """
        Scrub PII from log message
        """
        message = record.getMessage()

        for pattern, replacement in self.PII_PATTERNS:
            message = re.sub(pattern, replacement, message)

        record.msg = message
        return True

# Apply to all loggers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.addFilter(PIIScrubberFilter())
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] PII encryption implemented (AES-256)
- [ ] KMS integration working
- [ ] Database schema updated (no plain-text PII)
- [ ] Log scrubbing functional
- [ ] Unit tests passing
- [ ] Key rotation tested
- [ ] Security audit passed
- [ ] Documentation updated

---

### Story 4.3: Comprehensive Audit Logging

**Story ID**: STORY-4.3
**Priority**: Critical (P0)
**Story Points**: 5

#### User Story

```
As a Compliance Officer,
I want comprehensive audit logs of all sensitive operations,
So that I can investigate incidents and demonstrate compliance to regulators.
```

#### Acceptance Criteria

**Given** any sensitive operation occurs
**When** the operation completes (success or failure)
**Then** an audit log entry should be created with:
- Timestamp (ISO 8601)
- User ID and role
- Action performed (e.g., "customer_pii_accessed")
- Resource ID (e.g., customer UUID)
- IP address
- User agent
- Result (success/failure)
- No PII in the log

**Given** I am a GA Manager or Admin
**When** I query audit logs
**Then** I should be able to:
- Filter by date range, user, action type
- Export logs as CSV
- See aggregate statistics

**Given** an audit log query is made
**When** I export the results
**Then** the export should:
- Be tamper-evident (signed/hashed)
- Include export metadata (who, when)

#### Technical Tasks

- [ ] Design audit log schema (PostgreSQL table)
  - [ ] Columns: id, timestamp, user_id, action, resource_type, resource_id, ip_address, user_agent, result, details (JSONB)
  - [ ] Indexes: timestamp, user_id, action
- [ ] Implement audit logging service
  - [ ] `audit_log(user_id, action, resource_id, details)`
  - [ ] Async logging (don't block main request)
  - [ ] Batch inserts for performance
- [ ] Define auditable actions
  - [ ] `auth:login`, `auth:logout`, `auth:failed_login`
  - [ ] `customer:created`, `customer:updated`, `customer:pii_accessed`
  - [ ] `query:executed`, `policy:ingested`
  - [ ] `user:role_changed`, `system:config_changed`
- [ ] Implement audit log API
  - [ ] `GET /api/v1/audit/logs` - Query logs
  - [ ] `GET /api/v1/audit/export` - Export as CSV
- [ ] Add audit log middleware (FastAPI)
  - [ ] Automatically log all API requests
  - [ ] Extract user context from JWT
- [ ] Implement log retention policy
  - [ ] Keep logs for 7 years (regulatory requirement)
  - [ ] Archive old logs to S3
- [ ] Write unit tests
- [ ] Integration tests for audit log API

#### Dependencies

- Story 4.1 completed (authentication for user context)
- PostgreSQL audit_logs table

#### Technical Notes

**Audit Log Schema**:

```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  user_id UUID REFERENCES users(id),
  role VARCHAR(50),
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id VARCHAR(255),
  ip_address INET,
  user_agent TEXT,
  result VARCHAR(20),  -- 'success', 'failure'
  details JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
```

**Audit Logging Service**:

```python
# app/core/audit.py
from datetime import datetime
from typing import Optional

class AuditLogger:
    """
    Centralized audit logging service
    """
    def __init__(self, db_session):
        self.db = db_session

    def log(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: str = "success",
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Create audit log entry
        """
        log_entry = AuditLog(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(log_entry)
        self.db.commit()

# Middleware to auto-log all requests
from fastapi import Request

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    """
    Automatically log all API requests
    """
    # Skip health check endpoints
    if request.url.path in ["/health", "/ready"]:
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    # Extract user from JWT (if present)
    user_id = None
    if auth_header := request.headers.get("Authorization"):
        try:
            token = auth_header.replace("Bearer ", "")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
        except:
            pass

    # Log request
    audit_logger.log(
        user_id=user_id,
        action=f"{request.method}:{request.url.path}",
        result="success" if response.status_code < 400 else "failure",
        details={
            "status_code": response.status_code,
            "duration_ms": duration,
            "method": request.method,
            "path": request.url.path
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )

    return response
```

**Audit Log Query API**:

```python
@router.get("/api/v1/audit/logs")
@require_role("ga_manager")
async def get_audit_logs(
    start_date: datetime,
    end_date: datetime,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Query audit logs (GA managers and admins only)
    """
    query = db.query(AuditLog).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.timestamp <= end_date
    )

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if action:
        query = query.filter(AuditLog.action == action)

    # GA managers can only see logs for their GA
    if current_user.role == "ga_manager":
        # Get FP IDs in this GA
        fp_ids = get_fps_in_ga(current_user.ga_id)
        query = query.filter(AuditLog.user_id.in_(fp_ids))

    logs = query.order_by(AuditLog.timestamp.desc()).limit(1000).all()

    return {
        "logs": [log.to_dict() for log in logs],
        "count": len(logs)
    }
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Audit logging functional for all sensitive operations
- [ ] Middleware auto-logs API requests
- [ ] Audit log query API working
- [ ] CSV export functional
- [ ] Retention policy configured
- [ ] Unit tests passing
- [ ] Documentation updated

---

### Story 4.4: Sales Script Compliance Validation

**Story ID**: STORY-4.4
**Priority**: High (P1)
**Story Points**: 8

#### User Story

```
As a Compliance Officer,
I want AI-generated sales scripts validated for regulatory compliance,
So that FPs don't accidentally make misleading claims to customers.
```

#### Acceptance Criteria

**Given** an FP generates a sales script using AI
**When** the script is created
**Then** it should be automatically validated for:
- Forbidden phrases ("100% 보장", "무조건", etc.)
- Required disclaimers (면책기간, 보험사 최종 판단)
- Misleading claims (over-promising)
- Missing mandatory disclosures

**Given** validation fails
**When** the script is flagged
**Then** the system should:
- Highlight problematic phrases
- Suggest corrections
- Block script from being sent to customer
- Log the violation for review

**Given** validation passes
**When** the script is approved
**Then** it should:
- Be marked as "compliant"
- Allow FP to send to customer
- Log the approval in audit trail

#### Technical Tasks

- [ ] Define compliance rules
  - [ ] Forbidden phrase library (Korean)
  - [ ] Required phrase patterns
  - [ ] Risk scoring algorithm
- [ ] Implement ScriptValidator class
  - [ ] `validate_script(script: str) -> ValidationResult`
  - [ ] Forbidden phrase detection (regex + NLP)
  - [ ] Required phrase detection
  - [ ] Misleading claim detection (LLM-based)
- [ ] Implement `POST /api/v1/compliance/validate-script` endpoint
- [ ] Implement correction suggestion engine
  - [ ] Use LLM to suggest compliant alternatives
- [ ] Add validation UI in frontend
  - [ ] Highlight violations
  - [ ] Show suggestions
- [ ] Write unit tests for validation logic
- [ ] Test with real script samples

#### Dependencies

- Story 2.4 completed (LLM integration available)

#### Technical Notes

**Compliance Validator**:

```python
# app/services/compliance/script_validator.py

class ScriptValidator:
    """
    Validate sales scripts for compliance
    """
    FORBIDDEN_PHRASES = [
        '100% 보장',
        '무조건',
        '절대',
        '확실히',
        '당연히',
        '반드시 나옵니다',
        '보장받을 수 있습니다',  # Too definitive
    ]

    REQUIRED_PHRASES = [
        '약관에 따라',
        '보험사가 최종 판단',
        '면책기간',
    ]

    def validate(self, script: str, context: dict) -> dict:
        """
        Validate script for compliance
        """
        violations = []

        # Check 1: Forbidden phrases
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in script:
                violations.append({
                    'type': 'forbidden_phrase',
                    'severity': 'critical',
                    'phrase': phrase,
                    'reason': '절대적 단언 표현 금지',
                    'suggestion': self.get_compliant_alternative(phrase)
                })

        # Check 2: Required disclaimers
        missing_phrases = []
        for phrase in self.REQUIRED_PHRASES:
            if phrase not in script:
                missing_phrases.append(phrase)

        if missing_phrases:
            violations.append({
                'type': 'missing_disclaimer',
                'severity': 'high',
                'missing_phrases': missing_phrases,
                'reason': '필수 설명 의무 누락'
            })

        # Check 3: Misleading claims (LLM-based)
        if context.get('product_id'):
            misleading_claims = self.detect_misleading_claims_llm(script, context)
            violations.extend(misleading_claims)

        # Calculate risk score
        risk_score = self.calculate_risk_score(violations)

        # Determine compliance status
        is_compliant = len([v for v in violations if v['severity'] == 'critical']) == 0

        return {
            'is_compliant': is_compliant,
            'violations': violations,
            'risk_score': risk_score,  # 0-100
            'corrected_script': self.generate_corrected_script(script, violations) if not is_compliant else None
        }

    def detect_misleading_claims_llm(self, script: str, context: dict) -> list:
        """
        Use LLM to detect misleading claims
        """
        prompt = f"""
        다음 세일즈 스크립트에서 오해의 소지가 있거나 과장된 표현을 찾아주세요.

        스크립트:
        {script}

        상품 정보:
        {context}

        오해의 소지가 있는 표현을 JSON 배열로 반환하세요:
        [
          {{
            "phrase": "문제가 되는 표현",
            "reason": "왜 문제인지 설명",
            "correct_version": "올바른 표현"
          }}
        ]
        """

        response = llm.generate(prompt)
        misleading = json.loads(response)

        return [
            {
                'type': 'misleading_claim',
                'severity': 'high',
                'phrase': item['phrase'],
                'reason': item['reason'],
                'suggestion': item['correct_version']
            }
            for item in misleading
        ]

    def get_compliant_alternative(self, forbidden_phrase: str) -> str:
        """
        Get compliant alternative for forbidden phrase
        """
        alternatives = {
            '100% 보장': '약관에 따라 보장될 수 있습니다',
            '무조건': '조건을 충족하는 경우',
            '확실히': '약관 제X조에 따르면',
            '반드시 나옵니다': '지급 조건을 충족하면 보험금이 지급됩니다',
        }

        return alternatives.get(forbidden_phrase, '보다 신중한 표현으로 수정하세요')

    def generate_corrected_script(self, script: str, violations: list) -> str:
        """
        Generate corrected script with fixes applied
        """
        corrected = script

        for violation in violations:
            if violation['type'] == 'forbidden_phrase':
                corrected = corrected.replace(
                    violation['phrase'],
                    violation['suggestion']
                )

        # Add missing disclaimers at the end
        missing = [v for v in violations if v['type'] == 'missing_disclaimer']
        if missing:
            corrected += "\n\n※ 본 내용은 약관에 따라 달라질 수 있으며, 최종 판단은 보험사가 합니다."

        return corrected

    def calculate_risk_score(self, violations: list) -> int:
        """
        Calculate compliance risk score (0-100, higher = riskier)
        """
        severity_weights = {
            'critical': 30,
            'high': 15,
            'medium': 5,
            'low': 1
        }

        score = sum(severity_weights.get(v['severity'], 0) for v in violations)
        return min(100, score)
```

**API Endpoint**:

```python
@router.post("/api/v1/compliance/validate-script")
async def validate_script(
    request: ScriptValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Validate sales script for compliance
    """
    validator = ScriptValidator()

    result = validator.validate(
        script=request.script,
        context={
            'product_id': request.product_id,
            'fp_id': current_user.id
        }
    )

    # Audit log
    audit_log(
        user_id=current_user.id,
        action="compliance:script_validated",
        result="pass" if result['is_compliant'] else "fail",
        details={
            'risk_score': result['risk_score'],
            'violation_count': len(result['violations'])
        }
    )

    return result
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Script validator implemented
- [ ] Forbidden phrase detection working
- [ ] LLM-based misleading claim detection functional
- [ ] API endpoint tested
- [ ] UI integration complete
- [ ] Unit tests passing
- [ ] Tested with 50+ real script samples
- [ ] Documentation updated

---

### Story 4.5: Infrastructure Security & Network Isolation

**Story ID**: STORY-4.5
**Priority**: High (P1)
**Story Points**: 13

#### User Story

```
As a Security Engineer,
I want the infrastructure secured with network isolation and encryption,
So that we meet financial regulatory requirements and prevent attacks.
```

#### Acceptance Criteria

**Given** the application is deployed
**When** I inspect the infrastructure
**Then** I should verify:
- Application servers in private subnet (no direct internet access)
- Database servers in private subnet (only accessible from app servers)
- All traffic encrypted in transit (TLS 1.2+)
- All data encrypted at rest (AES-256)
- WAF (Web Application Firewall) enabled
- DDoS protection enabled (AWS Shield)

**Given** an attacker tries to access the database directly
**When** they attempt connection
**Then** they should be blocked by network security groups

**Given** an SQL injection attempt is made
**When** malicious input is sent to API
**Then** it should be:
- Blocked by WAF
- Logged as security incident
- Trigger alert to security team

#### Technical Tasks

- [ ] Design VPC architecture (AWS)
  - [ ] Public subnet for load balancer
  - [ ] Private subnet for application servers
  - [ ] Private subnet for databases (isolated)
  - [ ] NAT Gateway for outbound internet (API calls)
- [ ] Configure security groups
  - [ ] ALB: Allow 443 from internet
  - [ ] App servers: Allow 8000 from ALB only
  - [ ] Databases: Allow 5432/7687 from app servers only
- [ ] Setup TLS certificates (AWS ACM)
  - [ ] Auto-renewal
  - [ ] Force HTTPS (redirect HTTP → HTTPS)
- [ ] Enable encryption at rest
  - [ ] RDS PostgreSQL: Enable encryption
  - [ ] S3 buckets: Enable SSE-S3 or SSE-KMS
  - [ ] EBS volumes: Enable encryption
- [ ] Setup WAF rules (AWS WAF)
  - [ ] SQL injection protection
  - [ ] XSS protection
  - [ ] Rate limiting (per IP)
  - [ ] Geo-blocking (if needed)
- [ ] Enable AWS Shield Standard (free DDoS protection)
- [ ] Setup VPC Flow Logs (monitoring)
- [ ] Setup CloudWatch alarms
  - [ ] High error rate
  - [ ] Unusual traffic patterns
  - [ ] Failed login attempts
- [ ] Security group audit
- [ ] Penetration testing
- [ ] Document infrastructure

#### Dependencies

- AWS account with appropriate IAM roles
- Terraform or CloudFormation for IaC

#### Technical Notes

**VPC Architecture Diagram**:

```
Internet
    ↓
[CloudFront CDN] + WAF
    ↓
[Application Load Balancer] (Public Subnet)
    ↓
[EKS Pods - FastAPI] (Private Subnet)
    ↓
[RDS PostgreSQL] + [Neo4j] + [Redis] (Private Subnet - Data Tier)

[NAT Gateway] ← App Servers (for outbound API calls)
```

**Terraform Security Groups**:

```hcl
# terraform/security_groups.tf

resource "aws_security_group" "alb" {
  name        = "insuregraph-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from internet (redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app" {
  name        = "insuregraph-app-sg"
  description = "Security group for application servers"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "FastAPI from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound internet (via NAT Gateway)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database" {
  name        = "insuregraph-db-sg"
  description = "Security group for databases"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from app servers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description     = "Neo4j from app servers"
    from_port       = 7687
    to_port         = 7687
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  # No egress - databases don't need outbound internet
}
```

**WAF Rules**:

```hcl
# terraform/waf.tf

resource "aws_wafv2_web_acl" "main" {
  name  = "insuregraph-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rule 1: Block SQL injection
  rule {
    name     = "block-sql-injection"
    priority = 1

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLInjectionRule"
    }
  }

  # Rule 2: Block XSS
  rule {
    name     = "block-xss"
    priority = 2

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "XSSRule"
    }
  }

  # Rule 3: Rate limiting
  rule {
    name     = "rate-limit"
    priority = 3

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    action {
      block {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
    }
  }
}
```

#### Definition of Done

- [ ] Terraform code merged
- [ ] VPC with private/public subnets created
- [ ] Security groups configured
- [ ] TLS certificates provisioned
- [ ] Encryption at rest enabled (all databases, S3)
- [ ] WAF rules active
- [ ] CloudWatch alarms configured
- [ ] Penetration testing completed (no critical vulnerabilities)
- [ ] Infrastructure documentation updated
- [ ] Runbook for incident response created

---

### Story 4.6: Security Testing & Vulnerability Management

**Story ID**: STORY-4.6
**Priority**: High (P1)
**Story Points**: 5

#### User Story

```
As a Security Engineer,
I want continuous security testing and vulnerability scanning,
So that we catch security issues before they reach production.
```

#### Acceptance Criteria

**Given** code is committed to the repository
**When** CI/CD pipeline runs
**Then** it should:
- Run SAST (Static Application Security Testing)
- Scan dependencies for known vulnerabilities
- Block deployment if critical vulnerabilities found

**Given** the application is running in production
**When** weekly scans execute
**Then** they should:
- Run DAST (Dynamic Application Security Testing)
- Scan for OWASP Top 10 vulnerabilities
- Generate security report

**Given** a vulnerability is discovered
**When** it's reported
**Then** the system should:
- Create a ticket with severity rating
- Notify security team
- Track remediation progress

#### Technical Tasks

- [ ] Setup SAST in CI/CD pipeline
  - [ ] Tool: Semgrep, Bandit (Python), or SonarQube
  - [ ] Fail build on critical/high severity issues
- [ ] Setup dependency scanning
  - [ ] Tool: Safety (Python), npm audit, Dependabot
  - [ ] Auto-create PRs for dependency updates
- [ ] Setup DAST
  - [ ] Tool: OWASP ZAP or Burp Suite
  - [ ] Run weekly scans against staging
- [ ] Setup vulnerability management workflow
  - [ ] Integrate with Jira or GitHub Issues
  - [ ] Define SLA for remediation (critical: 7 days, high: 30 days)
- [ ] Setup security dashboard
  - [ ] Aggregate vulnerabilities from all tools
  - [ ] Track remediation progress
- [ ] Document security testing process
- [ ] Train team on security best practices

#### Dependencies

- CI/CD pipeline setup (GitHub Actions or GitLab CI)

#### Technical Notes

**GitHub Actions SAST Workflow**:

```yaml
# .github/workflows/security-scan.yml

name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install bandit safety

      - name: Run Bandit (SAST)
        run: |
          bandit -r backend/app -f json -o bandit-report.json
          bandit -r backend/app

      - name: Run Safety (dependency check)
        run: |
          safety check --json

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json

  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Trivy (container scanning)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

**Dependency Scanning (requirements.txt)**:

```bash
# Run Safety to check for known vulnerabilities
safety check --file=backend/requirements.txt

# Example output:
# +==============================================================================+
# |                                                                              |
# |                               /$$$$$$            /$$                         |
# |                              /$$__  $$          | $$                         |
# |           /$$$$$$$  /$$$$$$ | $$  \__//$$$$$$  /$$$$$$   /$$   /$$          |
# |          /$$_____/ |____  $$| $$$$   /$$__  $$|_  $$_/  | $$  | $$          |
# |         |  $$$$$$   /$$$$$$$| $$_/  | $$$$$$$$  | $$    | $$  | $$          |
# |          \____  $$ /$$__  $$| $$    | $$_____/  | $$ /$$| $$  | $$          |
# |          /$$$$$$$/|  $$$$$$$| $$    |  $$$$$$$  |  $$$$/|  $$$$$$$          |
# |         |_______/  \_______/|__/     \_______/   \___/   \____  $$          |
# |                                                            /$$  | $$          |
# |                                                           |  $$$$$$/          |
# |  by pyup.io                                                \______/           |
# |                                                                              |
# +==============================================================================+
#
# VULNERABILITIES FOUND:
# -> cryptography version 3.4.7 has known vulnerability (CVE-2023-XXXXX)
#    Upgrade to cryptography>=40.0.0
```

#### Definition of Done

- [ ] SAST integrated in CI/CD
- [ ] Dependency scanning active
- [ ] DAST scheduled for weekly runs
- [ ] Security dashboard created
- [ ] Vulnerability management process documented
- [ ] Team trained on security practices
- [ ] All critical vulnerabilities resolved

---

## Epic Dependencies

```
Story 4.1 (Authentication & RBAC)
    ↓
Story 4.2 (PII Encryption) ────────┐
    ↓                              │
Story 4.3 (Audit Logging) ◄────────┤
                                   │
Story 4.4 (Script Validation)      │
                                   │
Story 4.5 (Infrastructure Security)│
    ↓                              │
Story 4.6 (Security Testing) ◄─────┘
```

---

## Technical Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Encryption key compromise** | Critical | Low | Use AWS KMS; rotate keys quarterly; access logs |
| **PII leak in logs** | Critical | Medium | Log scrubbing middleware; regular audits; training |
| **Failed compliance audit** | Critical | Low | Regular self-audits; compliance checklist; external review |
| **OWASP vulnerability** | High | Medium | SAST/DAST in CI/CD; dependency scanning; bug bounty program |
| **Data breach** | Critical | Low | Penetration testing; incident response plan; insurance |

---

## Sprint Recommendations

### Sprint 13 (2 weeks)
- Story 4.1 (Authentication & RBAC)
- Story 4.2 (PII Encryption)

### Sprint 14 (2 weeks)
- Story 4.3 (Audit Logging)
- Story 4.4 (Script Validation)

### Sprint 15 (2 weeks)
- Story 4.5 (Infrastructure Security)
- Story 4.6 (Security Testing)

### Sprint 16 (1 week)
- Security audit & penetration testing
- Compliance documentation
- Final fixes

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Security Vulnerabilities** | 0 critical, < 5 high | SAST/DAST reports |
| **PII Leaks** | 0 incidents | Log audits |
| **Failed Auth Attempts** | < 1% | Monitoring dashboard |
| **Audit Log Coverage** | 100% of sensitive ops | Code review |
| **Compliance Audit** | Pass all criteria | External audit |
| **Penetration Test** | 0 critical findings | External pentest |

---

## Compliance Checklist

- [ ] Financial Sandbox designation obtained
- [ ] PII encrypted at rest (AES-256)
- [ ] All traffic encrypted in transit (TLS 1.2+)
- [ ] Audit logs for all sensitive operations
- [ ] RBAC enforced on all endpoints
- [ ] Network isolation (private subnets)
- [ ] WAF and DDoS protection enabled
- [ ] Incident response plan documented
- [ ] Security training completed for all team members
- [ ] External security audit passed

---

**Epic Owner**: Security Engineer / Backend Tech Lead
**Stakeholders**: Compliance Officer, Legal Team, Product Manager
**Next Review**: After Sprint 15 completion
**Critical Path**: This epic must be completed before production launch
