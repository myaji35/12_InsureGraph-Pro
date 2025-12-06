#!/bin/bash
#
# InsureGraph Pro - 원격 자동 배포 스크립트
# 서버에서 자동으로 실행됩니다
#

set -e

echo "========================================="
echo "InsureGraph Pro 배포 시작"
echo "========================================="
echo ""

# Docker 설치 확인
echo "[1/8] Docker 설치 확인..."
if ! command -v docker &> /dev/null; then
    echo "Docker 설치 중..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh

    echo "Docker Compose 설치 중..."
    apt-get update
    apt-get install -y docker-compose-plugin

    echo "✅ Docker 설치 완료"
else
    echo "✅ Docker가 이미 설치되어 있습니다"
fi

# 프로젝트 디렉토리 생성
echo ""
echo "[2/8] 프로젝트 디렉토리 설정..."
mkdir -p ~/InsureGraph-Pro
cd ~/InsureGraph-Pro

# 기존 파일 백업
if [ -f docker-compose.prod.yml ]; then
    echo "기존 파일 백업 중..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p backups
    tar -czf backups/backup_${timestamp}.tar.gz . 2>/dev/null || true
fi

# 파일 압축 해제
echo "파일 압축 해제 중..."
tar -xzf /tmp/insuregraph-deploy.tar.gz
rm /tmp/insuregraph-deploy.tar.gz
echo "✅ 파일 설정 완료"

# 방화벽 설정
echo ""
echo "[3/8] 방화벽 설정..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 3000/tcp
    ufw allow 8000/tcp
    ufw allow 7474/tcp
    ufw allow 7687/tcp
    ufw --force enable
    echo "✅ 방화벽 설정 완료"
else
    echo "⚠️  UFW가 설치되어 있지 않습니다"
fi

# 기존 컨테이너 중지
echo ""
echo "[4/8] 기존 컨테이너 확인..."
if docker compose -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
    echo "기존 컨테이너 중지 중..."
    docker compose -f docker-compose.prod.yml down
fi
echo "✅ 준비 완료"

# Docker Compose 빌드 및 실행
echo ""
echo "[5/8] Docker 컨테이너 빌드 및 시작... (5-10분 소요)"
docker compose -f docker-compose.prod.yml up -d --build

# 컨테이너 시작 대기
echo ""
echo "[6/8] 컨테이너 시작 대기..."
sleep 15

# 데이터베이스 마이그레이션
echo ""
echo "[7/8] 데이터베이스 마이그레이션..."
docker exec insuregraph-backend alembic upgrade head 2>/dev/null || echo "⚠️  마이그레이션 실패 (새 설치인 경우 정상)"

# 상태 확인
echo ""
echo "[8/8] 서비스 상태 확인..."
echo ""
echo "=== 컨테이너 상태 ==="
docker compose -f docker-compose.prod.yml ps
echo ""

# 헬스 체크
echo "=== 헬스 체크 ==="
sleep 5

BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend API: 정상 (HTTP $BACKEND_STATUS)"
else
    echo "⚠️  Backend API: 시작 중... (HTTP $BACKEND_STATUS)"
fi

FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend: 정상 (HTTP $FRONTEND_STATUS)"
else
    echo "⚠️  Frontend: 시작 중... (HTTP $FRONTEND_STATUS)"
fi

# 완료
echo ""
echo "========================================="
echo "🎉 배포 완료!"
echo "========================================="
echo ""
echo "접속 URL:"
echo "  • Frontend: http://58.225.113.125:3000"
echo "  • Backend API: http://58.225.113.125:8000"
echo "  • API Docs: http://58.225.113.125:8000/docs"
echo "  • Neo4j Browser: http://58.225.113.125:7474"
echo ""
echo "Neo4j 로그인 정보:"
echo "  • Username: neo4j"
echo "  • Password: Neo4j2024!Graph!Secure"
echo ""
echo "관리 명령어:"
echo "  • 로그 확인: docker compose -f docker-compose.prod.yml logs -f"
echo "  • 재시작: docker compose -f docker-compose.prod.yml restart"
echo "  • 중지: docker compose -f docker-compose.prod.yml down"
echo ""
echo "⚠️  서비스가 완전히 시작되기까지 1-2분 더 소요될 수 있습니다."
echo ""
