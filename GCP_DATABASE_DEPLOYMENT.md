# GCP Cloud SQL PostgreSQL 배포 가이드

## 목차
1. [GCP Cloud SQL 인스턴스 생성](#1-gcp-cloud-sql-인스턴스-생성)
2. [데이터베이스 마이그레이션](#2-데이터베이스-마이그레이션)
3. [백엔드 연결 설정](#3-백엔드-연결-설정)
4. [로컬 데이터베이스 정리](#4-로컬-데이터베이스-정리)

---

## 1. GCP Cloud SQL 인스턴스 생성

### 1.1 GCP Console에서 Cloud SQL 생성

```bash
# GCP CLI 설치 (없는 경우)
brew install google-cloud-sdk

# GCP 로그인
gcloud auth login

# 프로젝트 설정
gcloud config set project insuregraph-dev
```

### 1.2 Cloud SQL 인스턴스 생성 (CLI 방법)

```bash
# PostgreSQL 인스턴스 생성
gcloud sql instances create insuregraph-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3 \
  --root-password=YOUR_SECURE_PASSWORD \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --availability-type=zonal

# 데이터베이스 생성
gcloud sql databases create insuregraph \
  --instance=insuregraph-postgres

# 사용자 생성
gcloud sql users create insuregraph_user \
  --instance=insuregraph-postgres \
  --password=YOUR_USER_PASSWORD
```

### 1.3 Cloud SQL 인스턴스 생성 (Console 방법)

1. **GCP Console 접속**: https://console.cloud.google.com/sql
2. **인스턴스 만들기** 클릭
3. **PostgreSQL 선택**
4. **인스턴스 ID**: `insuregraph-postgres`
5. **비밀번호 설정**: 강력한 비밀번호 입력
6. **리전**: `asia-northeast3` (서울)
7. **영역**: 단일 영역
8. **데이터베이스 버전**: PostgreSQL 15
9. **머신 유형**: 
   - 개발: `db-f1-micro` (0.6GB RAM, 공유 CPU)
   - 프로덕션: `db-n1-standard-1` (3.75GB RAM, 1 vCPU)
10. **스토리지**:
    - 유형: SSD
    - 용량: 10GB (자동 증가 활성화)
11. **연결**:
    - 공개 IP: 활성화
    - 승인된 네트워크: 현재 IP 추가 (보안을 위해)
    - 또는 Cloud SQL Proxy 사용 권장
12. **백업**:
    - 자동 백업: 활성화
    - 백업 시간: 03:00 (오전 3시)
    - 트랜잭션 로그 (Point-in-time recovery): 활성화
13. **유지보수**:
    - 유지보수 기간: 일요일 04:00
14. **만들기** 클릭

---

## 2. 데이터베이스 마이그레이션

### 2.1 Cloud SQL Proxy 설치 및 실행

```bash
# Cloud SQL Proxy 다운로드 (Mac)
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
chmod +x cloud_sql_proxy

# Proxy 실행 (백그라운드)
./cloud_sql_proxy -instances=insuregraph-dev:asia-northeast3:insuregraph-postgres=tcp:5433 &

# 또는 포그라운드 실행
./cloud_sql_proxy -instances=insuregraph-dev:asia-northeast3:insuregraph-postgres=tcp:5433
```

**연결 문자열 형식**: `PROJECT_ID:REGION:INSTANCE_NAME=tcp:PORT`

### 2.2 로컬 백업 데이터 복원

```bash
# 백업 파일 확인
ls -lh /tmp/insuregraph_backup.sql

# Cloud SQL로 복원
PGPASSWORD=YOUR_USER_PASSWORD psql \
  -h localhost \
  -p 5433 \
  -U insuregraph_user \
  -d insuregraph \
  -f /tmp/insuregraph_backup.sql

# 또는 공개 IP로 직접 연결 (승인된 네트워크 설정 필요)
PGPASSWORD=YOUR_USER_PASSWORD psql \
  -h YOUR_CLOUD_SQL_PUBLIC_IP \
  -U insuregraph_user \
  -d insuregraph \
  -f /tmp/insuregraph_backup.sql
```

### 2.3 데이터 확인

```bash
# Cloud SQL에 연결
PGPASSWORD=YOUR_USER_PASSWORD psql \
  -h localhost \
  -p 5433 \
  -U insuregraph_user \
  -d insuregraph

# SQL 쿼리 실행
\dt  -- 테이블 목록
SELECT COUNT(*) FROM documents;  -- 문서 개수 확인
SELECT COUNT(*) FROM users;  -- 사용자 개수 확인
\q  -- 종료
```

---

## 3. 백엔드 연결 설정

### 3.1 환경변수 업데이트

**backend/.env 파일 수정**:

```bash
# Database - PostgreSQL (GCP Cloud SQL)
# Cloud SQL Proxy 사용 시
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=insuregraph
POSTGRES_USER=insuregraph_user
POSTGRES_PASSWORD=YOUR_USER_PASSWORD

# 또는 공개 IP 직접 연결 시
# POSTGRES_HOST=YOUR_CLOUD_SQL_PUBLIC_IP
# POSTGRES_PORT=5432
# POSTGRES_DB=insuregraph
# POSTGRES_USER=insuregraph_user
# POSTGRES_PASSWORD=YOUR_USER_PASSWORD
```

### 3.2 Cloud SQL Auth Proxy를 systemd 서비스로 등록 (선택사항)

**Linux/Mac에서 자동 실행 설정**:

```bash
# cloud_sql_proxy를 /usr/local/bin으로 이동
sudo mv cloud_sql_proxy /usr/local/bin/
sudo chmod +x /usr/local/bin/cloud_sql_proxy

# systemd 서비스 파일 생성 (Linux)
sudo nano /etc/systemd/system/cloud-sql-proxy.service
```

**서비스 파일 내용**:
```ini
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
ExecStart=/usr/local/bin/cloud_sql_proxy \
  -instances=insuregraph-dev:asia-northeast3:insuregraph-postgres=tcp:5433
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable cloud-sql-proxy
sudo systemctl start cloud-sql-proxy
sudo systemctl status cloud-sql-proxy
```

### 3.3 백엔드 재시작 및 연결 테스트

```bash
cd backend

# 백엔드 서버 재시작
# (현재 실행 중인 서버 종료 후)
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 3030 --reload

# 또는 다른 터미널에서 헬스 체크
curl http://localhost:3030/api/v1/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "postgres": "connected",
    "redis": "disconnected",
    "neo4j": "disconnected"
  }
}
```

---

## 4. 로컬 데이터베이스 정리

### 4.1 데이터 확인 및 백업 검증

```bash
# Cloud SQL에서 데이터 확인
PGPASSWORD=YOUR_USER_PASSWORD psql \
  -h localhost \
  -p 5433 \
  -U insuregraph_user \
  -d insuregraph \
  -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='public';"

# 로컬 DB와 비교
psql -h localhost -U gangseungsig -d insuregraph \
  -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='public';"
```

### 4.2 로컬 PostgreSQL 데이터 삭제

**⚠️ 주의: Cloud SQL 마이그레이션이 완료되고 테스트가 끝난 후 실행하세요!**

```bash
# 로컬 데이터베이스 삭제
psql -h localhost -U gangseungsig -d postgres -c "DROP DATABASE insuregraph;"

# 데이터베이스 재생성 (필요한 경우)
psql -h localhost -U gangseungsig -d postgres -c "CREATE DATABASE insuregraph;"

# PostgreSQL 데이터 디렉토리 정리 (선택사항)
# Mac Homebrew PostgreSQL의 경우
ls -lh /opt/homebrew/var/postgresql@14/

# 오래된 로그 파일 정리
find /opt/homebrew/var/postgresql@14/log/ -name "*.log" -mtime +7 -delete
```

### 4.3 디스크 공간 확인

```bash
# 디스크 사용량 확인
df -h

# PostgreSQL 데이터 디렉토리 크기 확인
du -sh /opt/homebrew/var/postgresql@14/

# 정리 후 확인
# (데이터 삭제 후 다시 실행)
```

---

## 5. 보안 권장사항

### 5.1 Cloud SQL 보안 설정

1. **Cloud SQL Proxy 사용** (권장)
   - 공개 IP 노출 최소화
   - TLS 암호화 자동 적용
   - IAM 기반 인증

2. **승인된 네트워크 제한**
   - 특정 IP 주소만 허용
   - 개발 환경: 개발자 IP만 허용
   - 프로덕션: 앱 서버 IP만 허용

3. **강력한 비밀번호 사용**
   ```bash
   # 안전한 비밀번호 생성
   openssl rand -base64 32
   ```

4. **SSL/TLS 연결 강제**
   ```bash
   # Cloud SQL에서 SSL 필수로 설정
   gcloud sql instances patch insuregraph-postgres \
     --require-ssl
   ```

### 5.2 환경변수 보안

```bash
# .env 파일 권한 설정
chmod 600 backend/.env

# .gitignore에 추가 (이미 되어있는지 확인)
echo ".env" >> backend/.gitignore
```

---

## 6. 비용 최적화

### 6.1 개발 환경 (월 $7-15)
- **머신 유형**: db-f1-micro (0.6GB RAM)
- **스토리지**: 10GB SSD
- **백업**: 7일 보관
- **사용하지 않을 때**: 인스턴스 중지

```bash
# 인스턴스 중지
gcloud sql instances patch insuregraph-postgres --activation-policy=NEVER

# 인스턴스 재시작
gcloud sql instances patch insuregraph-postgres --activation-policy=ALWAYS
```

### 6.2 프로덕션 환경 (월 $50-100)
- **머신 유형**: db-n1-standard-1 (3.75GB RAM)
- **고가용성**: 활성화 (다중 영역)
- **백업**: 30일 보관
- **읽기 복제본**: 필요 시 추가

---

## 7. 모니터링 및 유지보수

### 7.1 Cloud SQL 모니터링

```bash
# CPU 사용률 확인
gcloud sql instances describe insuregraph-postgres \
  --format="value(settings.tier,stats.cpuUtilization)"

# 스토리지 사용량 확인
gcloud sql instances describe insuregraph-postgres \
  --format="value(settings.dataDiskSizeGb,stats.dataDiskUtilization)"
```

### 7.2 로그 확인

GCP Console > Cloud SQL > insuregraph-postgres > 로그

또는 CLI:
```bash
gcloud logging read "resource.type=cloudsql_database AND resource.labels.database_id=insuregraph-dev:insuregraph-postgres" --limit 50
```

---

## 8. 트러블슈팅

### 문제 1: 연결 실패
```
FATAL: no pg_hba.conf entry for host
```
**해결책**: 
- Cloud SQL Proxy 사용
- 또는 승인된 네트워크에 IP 추가

### 문제 2: 비밀번호 인증 실패
```
FATAL: password authentication failed
```
**해결책**: 
```bash
# 비밀번호 재설정
gcloud sql users set-password insuregraph_user \
  --instance=insuregraph-postgres \
  --password=NEW_PASSWORD
```

### 문제 3: 연결 시간 초과
```
timeout: connect to server
```
**해결책**: 
- 방화벽 규칙 확인
- Cloud SQL Proxy 실행 확인
- 인스턴스 상태 확인

```bash
gcloud sql instances list
```

---

## 9. 백업 및 복구

### 수동 백업 생성
```bash
gcloud sql backups create \
  --instance=insuregraph-postgres \
  --description="Manual backup before migration"
```

### 백업 목록 확인
```bash
gcloud sql backups list --instance=insuregraph-postgres
```

### 백업에서 복구
```bash
gcloud sql backups restore BACKUP_ID \
  --backup-instance=insuregraph-postgres \
  --backup-id=BACKUP_ID
```

---

## 10. 다음 단계

1. ✅ Cloud SQL 인스턴스 생성
2. ✅ 데이터 마이그레이션
3. ✅ 백엔드 연결 테스트
4. ✅ 로컬 데이터베이스 정리
5. 🔄 Neo4j 및 Redis를 GCP로 마이그레이션 (선택사항)
6. 🔄 백엔드를 Cloud Run 또는 GKE에 배포

---

## 참고 자료

- [Cloud SQL 문서](https://cloud.google.com/sql/docs)
- [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Cloud SQL 가격](https://cloud.google.com/sql/pricing)
- [PostgreSQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)

---

**작성일**: 2025-12-02  
**버전**: 1.0  
**작성자**: Claude Code
