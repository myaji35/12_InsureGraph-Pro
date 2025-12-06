#!/bin/bash

# InsureGraph Pro 서버 배포 스크립트
# Target: 58.225.113.125:8000

set -e  # 에러 발생 시 중단

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="58.225.113.125"
SERVER_USER="${DEPLOY_USER:-root}"
PROJECT_DIR="InsureGraph-Pro"
REPO_URL="https://github.com/YOUR_USERNAME/InsureGraph-Pro.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}InsureGraph Pro 배포 시작${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "서버: ${BLUE}${SERVER_IP}${NC}"
echo -e "사용자: ${BLUE}${SERVER_USER}${NC}"
echo ""

# Step 1: 환경변수 확인
echo -e "${YELLOW}[1/7] 환경변수 확인...${NC}"
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ .env.production 파일이 없습니다.${NC}"
    echo -e "${YELLOW}샘플 파일을 생성합니다...${NC}"
    cat > .env.production << EOF
POSTGRES_PASSWORD=insure2024!secure!change-me
NEO4J_PASSWORD=neo4j2024!secure!change-me
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)
UPSTAGE_API_KEY=your-upstage-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
EOF
    echo -e "${RED}⚠️  .env.production 파일을 수정한 후 다시 실행하세요!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 환경변수 파일 확인 완료${NC}"

# Step 2: SSH 접속 확인
echo -e "${YELLOW}[2/7] 서버 접속 확인...${NC}"
if ! ssh -o ConnectTimeout=5 ${SERVER_USER}@${SERVER_IP} "echo 'Connection OK'" > /dev/null 2>&1; then
    echo -e "${RED}❌ 서버 접속 실패: ${SERVER_IP}${NC}"
    echo -e "${YELLOW}SSH 키를 사용하는 경우:${NC}"
    echo -e "  ssh -i /path/to/key.pem ${SERVER_USER}@${SERVER_IP}"
    echo -e "${YELLOW}또는 DEPLOY_USER 환경변수를 설정하세요:${NC}"
    echo -e "  DEPLOY_USER=ubuntu ./deploy-to-server.sh"
    exit 1
fi
echo -e "${GREEN}✅ 서버 접속 확인 완료${NC}"

# Step 3: 파일 압축
echo -e "${YELLOW}[3/7] 프로젝트 파일 압축...${NC}"
tar -czf /tmp/insuregraph-deploy.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='backend/venv' \
    --exclude='backend/__pycache__' \
    --exclude='backend/.pytest_cache' \
    --exclude='backend/logs' \
    --exclude='frontend/.next' \
    --exclude='frontend/out' \
    --exclude='.turbo' \
    --exclude='*.pyc' \
    backend/ frontend/ docker-compose.prod.yml .env.production
echo -e "${GREEN}✅ 파일 압축 완료${NC}"

# Step 4: 서버로 파일 전송
echo -e "${YELLOW}[4/7] 서버로 파일 전송...${NC}"
scp /tmp/insuregraph-deploy.tar.gz ${SERVER_USER}@${SERVER_IP}:/tmp/
echo -e "${GREEN}✅ 파일 전송 완료${NC}"

# Step 5: 서버에서 Docker 설치 및 배포
echo -e "${YELLOW}[5/7] 서버 환경 설정 및 Docker 설치...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
set -e

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "Docker 설치 중..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker 설치 완료"
else
    echo "Docker가 이미 설치되어 있습니다."
fi

# Docker Compose 설치 확인
if ! docker compose version &> /dev/null; then
    echo "Docker Compose 설치 중..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "Docker Compose 설치 완료"
else
    echo "Docker Compose가 이미 설치되어 있습니다."
fi

# 프로젝트 디렉토리 생성
mkdir -p ~/InsureGraph-Pro
cd ~/InsureGraph-Pro

# 기존 파일 백업 (있는 경우)
if [ -f docker-compose.prod.yml ]; then
    echo "기존 파일 백업 중..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p backups
    tar -czf backups/backup_${timestamp}.tar.gz \
        docker-compose.prod.yml .env.production 2>/dev/null || true
fi

# 새 파일 압축 해제
echo "파일 압축 해제 중..."
tar -xzf /tmp/insuregraph-deploy.tar.gz
rm /tmp/insuregraph-deploy.tar.gz

echo "서버 환경 설정 완료"
ENDSSH
echo -e "${GREEN}✅ 서버 환경 설정 완료${NC}"

# Step 6: Docker Compose 실행
echo -e "${YELLOW}[6/7] Docker 컨테이너 시작...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
set -e
cd ~/InsureGraph-Pro

# 기존 컨테이너 중지 (있는 경우)
if docker compose -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
    echo "기존 컨테이너 중지 중..."
    docker compose -f docker-compose.prod.yml down
fi

# 새 컨테이너 시작
echo "Docker 컨테이너 빌드 및 시작 중..."
docker compose -f docker-compose.prod.yml up -d --build

# 잠시 대기 (컨테이너 시작 대기)
echo "컨테이너 시작 대기 중..."
sleep 10

# 컨테이너 상태 확인
echo ""
echo "=== 컨테이너 상태 ==="
docker compose -f docker-compose.prod.yml ps

# 데이터베이스 마이그레이션
echo ""
echo "데이터베이스 마이그레이션 실행 중..."
docker exec insuregraph-backend alembic upgrade head || echo "마이그레이션 실패 (새 설치인 경우 정상)"

echo ""
echo "=== 최근 로그 ==="
docker compose -f docker-compose.prod.yml logs --tail=50
ENDSSH
echo -e "${GREEN}✅ Docker 컨테이너 시작 완료${NC}"

# Step 7: 헬스 체크
echo -e "${YELLOW}[7/7] 서비스 헬스 체크...${NC}"
sleep 5

echo -e "${BLUE}Backend API 헬스 체크...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER_IP}:8000/api/v1/health || echo "000")
if [ "${HTTP_CODE}" == "200" ]; then
    echo -e "${GREEN}✅ Backend API: 정상 (HTTP 200)${NC}"
else
    echo -e "${YELLOW}⚠️  Backend API: 응답 대기 중 (HTTP ${HTTP_CODE})${NC}"
fi

echo -e "${BLUE}Frontend 헬스 체크...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER_IP}:3000 || echo "000")
if [ "${HTTP_CODE}" == "200" ]; then
    echo -e "${GREEN}✅ Frontend: 정상 (HTTP 200)${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend: 응답 대기 중 (HTTP ${HTTP_CODE})${NC}"
fi

# 완료
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}접속 URL:${NC}"
echo -e "  • Frontend: ${GREEN}http://${SERVER_IP}:3000${NC}"
echo -e "  • Backend API: ${GREEN}http://${SERVER_IP}:8000${NC}"
echo -e "  • API Docs: ${GREEN}http://${SERVER_IP}:8000/docs${NC}"
echo -e "  • Neo4j Browser: ${GREEN}http://${SERVER_IP}:7474${NC}"
echo ""
echo -e "${BLUE}관리 명령어:${NC}"
echo -e "  • 로그 확인: ${YELLOW}ssh ${SERVER_USER}@${SERVER_IP} 'cd ~/InsureGraph-Pro && docker compose -f docker-compose.prod.yml logs -f'${NC}"
echo -e "  • 서비스 재시작: ${YELLOW}ssh ${SERVER_USER}@${SERVER_IP} 'cd ~/InsureGraph-Pro && docker compose -f docker-compose.prod.yml restart'${NC}"
echo -e "  • 서비스 중지: ${YELLOW}ssh ${SERVER_USER}@${SERVER_IP} 'cd ~/InsureGraph-Pro && docker compose -f docker-compose.prod.yml down'${NC}"
echo ""
echo -e "${YELLOW}⚠️  주의사항:${NC}"
echo -e "  1. 방화벽에서 포트 3000, 8000을 개방해야 합니다."
echo -e "  2. .env.production 파일의 API 키를 확인하세요."
echo -e "  3. 프로덕션 환경에서는 HTTPS를 사용하는 것을 권장합니다."
echo ""

# 임시 파일 정리
rm -f /tmp/insuregraph-deploy.tar.gz

exit 0
