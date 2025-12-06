# 🚀 InsureGraph Pro - 즉시 배포 가이드

## ✅ 준비 완료!

배포 파일이 준비되었습니다:
- 📦 **파일**: `/tmp/insuregraph-deploy.tar.gz` (615MB)
- 🌐 **서버**: 58.225.113.125
- 👤 **사용자**: root
- 🔑 **비밀번호**: gmldnjs!00

---

## 🎯 배포 방법 (선택하세요)

### 방법 1: 터미널에서 단계별 실행 (권장) ⭐

새 터미널을 열고 아래 명령어를 **순서대로** 복사해서 실행하세요:

#### Step 1: 서버로 파일 전송

```bash
# 파일 전송 (비밀번호: gmldnjs!00)
scp /tmp/insuregraph-deploy.tar.gz root@58.225.113.125:/tmp/
```

비밀번호를 입력하면 파일 전송이 시작됩니다 (약 2-3분 소요).

#### Step 2: 서버 접속

```bash
# 서버 접속 (비밀번호: gmldnjs!00)
ssh root@58.225.113.125
```

#### Step 3: Docker 설치 (서버에서 실행)

서버에 접속한 상태에서:

```bash
# Docker 설치 스크립트 실행
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

# Docker Compose 설치
apt-get update && apt-get install -y docker-compose-plugin

# 설치 확인
docker --version
docker compose version
```

#### Step 4: 프로젝트 설정

```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/InsureGraph-Pro && cd ~/InsureGraph-Pro

# 파일 압축 해제
tar -xzf /tmp/insuregraph-deploy.tar.gz

# 파일 확인
ls -la
```

#### Step 5: 방화벽 설정

```bash
# 방화벽 포트 개방
ufw allow 22/tcp   # SSH
ufw allow 3000/tcp # Frontend
ufw allow 8000/tcp # Backend
ufw allow 7474/tcp # Neo4j Browser
ufw allow 7687/tcp # Neo4j Bolt
ufw --force enable

# 상태 확인
ufw status
```

#### Step 6: Docker 컨테이너 시작

```bash
# Docker Compose 실행 (5-10분 소요)
cd ~/InsureGraph-Pro
docker compose -f docker-compose.prod.yml up -d --build

# 진행 상황 실시간 확인
docker compose -f docker-compose.prod.yml logs -f
```

> 💡 **팁**: 로그를 보다가 `Ctrl+C`를 눌러도 컨테이너는 백그라운드에서 계속 실행됩니다.

#### Step 7: 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
docker exec insuregraph-backend alembic upgrade head
```

#### Step 8: 상태 확인

```bash
# 컨테이너 상태
docker compose -f docker-compose.prod.yml ps

# Backend 헬스 체크
curl http://localhost:8000/api/v1/health

# Frontend 확인
curl -I http://localhost:3000
```

✅ **배포 완료!** 이제 브라우저에서 접속하세요:
- Frontend: http://58.225.113.125:3000
- Backend API: http://58.225.113.125:8000
- API Docs: http://58.225.113.125:8000/docs

---

### 방법 2: 원클릭 배포 스크립트

파일 전송만 수동으로 하고, 나머지는 자동으로 실행하는 방법:

#### Step 1: 파일 전송

```bash
scp /tmp/insuregraph-deploy.tar.gz root@58.225.113.125:/tmp/
```

#### Step 2: 원클릭 스크립트 실행

```bash
ssh root@58.225.113.125 'bash -s' < "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/remote-deploy.sh"
```

---

## 🔍 배포 후 확인사항

### 로컬 Mac에서 테스트

새 터미널을 열고:

```bash
# Backend API 테스트
curl http://58.225.113.125:8000/api/v1/health

# 예상 결과: {"status":"healthy",...}

# Frontend 접속
open http://58.225.113.125:3000

# API 문서
open http://58.225.113.125:8000/docs

# Neo4j 브라우저
open http://58.225.113.125:7474
# Username: neo4j
# Password: Neo4j2024!Graph!Secure
```

---

## 📊 관리 명령어 (서버에서)

### 로그 확인

```bash
# 실시간 로그
docker compose -f docker-compose.prod.yml logs -f

# 특정 서비스
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### 서비스 재시작

```bash
# 전체 재시작
docker compose -f docker-compose.prod.yml restart

# 특정 서비스
docker compose -f docker-compose.prod.yml restart backend
```

### 서비스 중지

```bash
# 중지
docker compose -f docker-compose.prod.yml stop

# 중지 및 삭제
docker compose -f docker-compose.prod.yml down
```

---

## 🆘 문제 해결

### 컨테이너가 시작 안 됨

```bash
# 상태 확인
docker compose -f docker-compose.prod.yml ps

# 로그 확인
docker compose -f docker-compose.prod.yml logs backend

# 재시작
docker compose -f docker-compose.prod.yml restart
```

### 포트 충돌

```bash
# 포트 사용 확인
netstat -tulpn | grep :8000

# Docker 완전 재시작
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 재시작
docker compose -f docker-compose.prod.yml restart postgres

# 로그 확인
docker compose -f docker-compose.prod.yml logs postgres
```

---

## 📞 접속 정보 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| **Frontend** | http://58.225.113.125:3000 | 메인 웹사이트 |
| **Backend API** | http://58.225.113.125:8000 | REST API |
| **API Docs** | http://58.225.113.125:8000/docs | Swagger UI |
| **Neo4j Browser** | http://58.225.113.125:7474 | 그래프 DB 관리 |

**Neo4j 로그인 정보**:
- Username: `neo4j`
- Password: `Neo4j2024!Graph!Secure`

---

## ✅ 배포 체크리스트

배포 진행 상황을 체크하세요:

- [ ] 파일 전송 완료
- [ ] 서버 접속 성공
- [ ] Docker 설치 완료
- [ ] 파일 압축 해제
- [ ] 방화벽 설정 완료
- [ ] Docker Compose 실행
- [ ] 모든 컨테이너 정상 실행
- [ ] 데이터베이스 마이그레이션 성공
- [ ] Backend API 헬스 체크 통과
- [ ] Frontend 접속 확인
- [ ] Neo4j 접속 확인

---

**배포 준비 완료 시각**: 2025-12-05 16:19
**배포 파일 크기**: 615MB
**예상 배포 시간**: 10-15분

🎉 **축하합니다!** 배포가 완료되면 InsureGraph Pro를 사용할 수 있습니다!
