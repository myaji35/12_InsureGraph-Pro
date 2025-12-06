# 배포 준비 체크리스트

## ✅ 배포 전 확인사항

### 1. 서버 접속 정보
- [ ] **서버 IP**: 58.225.113.125
- [ ] **SSH 사용자**: _____________ (예: ubuntu, root, admin)
- [ ] **SSH 키 파일**: _____________ (또는 비밀번호)
- [ ] **SSH 접속 테스트 완료**

### 2. API 키 준비
- [ ] **Upstage API Key**: _____________
- [ ] **OpenAI API Key**: _____________
- [ ] **Anthropic API Key**: _____________

### 3. 환경변수 설정
- [ ] `.env.production` 파일 생성 완료
- [ ] 모든 비밀번호를 안전한 값으로 변경
- [ ] SECRET_KEY, JWT_SECRET_KEY 생성 완료

### 4. 서버 요구사항
- [ ] Ubuntu 20.04 이상 (또는 CentOS, Debian)
- [ ] 최소 2GB RAM
- [ ] 최소 20GB 디스크 공간
- [ ] 인터넷 연결

---

## 🚀 배포 방법

### Option 1: 자동 배포 스크립트 사용 (권장)

```bash
# 1. SSH 사용자 설정 (서버 접속 계정)
export DEPLOY_USER=ubuntu  # 또는 root, admin 등

# 2. 배포 스크립트 실행
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"
./deploy-to-server.sh
```

### Option 2: 수동 배포

서버에 직접 접속해서 배포:

```bash
# 1. 서버 접속
ssh your-username@58.225.113.125

# 2. 프로젝트 디렉토리 생성
mkdir -p ~/InsureGraph-Pro
cd ~/InsureGraph-Pro

# 3. 로컬에서 파일 전송 (새 터미널)
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"
scp -r backend frontend docker-compose.prod.yml .env.production your-username@58.225.113.125:~/InsureGraph-Pro/

# 4. 서버에서 Docker 설치 및 실행
ssh your-username@58.225.113.125
cd ~/InsureGraph-Pro
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 📝 배포 후 확인사항

### 1. 서비스 상태 확인
```bash
ssh your-username@58.225.113.125
cd ~/InsureGraph-Pro
docker compose -f docker-compose.prod.yml ps
```

### 2. 헬스 체크
- [ ] **Backend API**: http://58.225.113.125:8000/api/v1/health
- [ ] **Frontend**: http://58.225.113.125:3000
- [ ] **API Docs**: http://58.225.113.125:8000/docs
- [ ] **Neo4j**: http://58.225.113.125:7474

### 3. 로그 확인
```bash
# 전체 로그
docker compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### 4. 방화벽 설정
```bash
# UFW (Ubuntu Firewall)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 3000/tcp # Frontend
sudo ufw allow 8000/tcp # Backend API
sudo ufw allow 7474/tcp # Neo4j Browser (선택)
sudo ufw enable
```

---

## 🔧 트러블슈팅

### 문제 1: 서버 접속 실패
```bash
# SSH 키 파일 사용
ssh -i /path/to/key.pem ubuntu@58.225.113.125

# 또는 비밀번호 사용
ssh ubuntu@58.225.113.125
```

### 문제 2: Docker 권한 오류
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 문제 3: 포트가 이미 사용 중
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 문제 4: 컨테이너 시작 실패
```bash
# 로그 확인
docker compose -f docker-compose.prod.yml logs backend

# 컨테이너 재시작
docker compose -f docker-compose.prod.yml restart backend
```

---

## 📊 배포 파일 구조

```
InsureGraph-Pro/
├── backend/
│   ├── Dockerfile
│   ├── app/
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile.prod
│   ├── src/
│   └── package.json
├── docker-compose.prod.yml  # ✅ 생성됨
├── .env.production           # ✅ 생성됨 (수정 필요)
└── deploy-to-server.sh       # ✅ 생성됨
```

---

## 🔐 보안 권장사항

1. **비밀번호 변경**
   - `.env.production`의 모든 비밀번호를 강력한 값으로 변경
   - 최소 16자 이상, 특수문자 포함

2. **방화벽 설정**
   - 필요한 포트만 개방
   - SSH 포트 변경 권장 (22 → 다른 포트)

3. **SSL/TLS 설정**
   - Let's Encrypt를 사용한 HTTPS 설정 권장
   - Nginx 리버스 프록시 사용

4. **정기 백업**
   - PostgreSQL 백업
   - Neo4j 백업
   - 환경변수 백업

---

## 📞 다음 단계

배포가 완료되면:

1. [ ] 프론트엔드 접속 테스트
2. [ ] API 엔드포인트 테스트
3. [ ] 데이터베이스 마이그레이션 확인
4. [ ] Neo4j 그래프 데이터 확인
5. [ ] 모니터링 설정
6. [ ] 백업 자동화 설정
7. [ ] SSL 인증서 설정

---

**작성일**: 2025-12-05
**대상 서버**: 58.225.113.125
**배포 환경**: Production
