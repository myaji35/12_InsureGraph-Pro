#!/bin/bash
set -e

COOLIFY_SERVER="34.64.191.91"
PLATFORM="linux/amd64"
PROJECT_DIR="/opt/insuregraph"

echo "🚀 InsureGraph Pro 배포 시작..."
echo "📍 서버: $COOLIFY_SERVER (Linux AMD64)"

# 1. 소스코드 전송
echo "📦 소스코드 전송 중..."
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude 'venv' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.git' \
  ./ root@$COOLIFY_SERVER:$PROJECT_DIR/

# 2. 환경변수 전송
echo "🔧 환경변수 설정 중..."
scp .coolify.env root@$COOLIFY_SERVER:$PROJECT_DIR/.env

# 3. 배포 실행
echo "🐳 Docker 컨테이너 빌드 및 시작 중..."
ssh root@$COOLIFY_SERVER << EOF
  cd $PROJECT_DIR

  # 기존 컨테이너 중지 (첫 배포시는 무시)
  docker-compose -f docker-compose.coolify.yml down 2>/dev/null || true

  # AMD64 플랫폼으로 빌드 및 실행
  DOCKER_DEFAULT_PLATFORM=$PLATFORM \
    docker-compose -f docker-compose.coolify.yml up -d --build

  echo "⏳ 서비스 시작 대기 중..."
  sleep 15

  # 데이터베이스 마이그레이션
  echo "🗄️  데이터베이스 마이그레이션 실행 중..."
  docker-compose -f docker-compose.coolify.yml exec -T backend alembic upgrade head

  # 상태 확인
  echo "📊 서비스 상태:"
  docker-compose -f docker-compose.coolify.yml ps
EOF

# 4. 헬스체크
echo "🏥 헬스체크 실행 중..."
sleep 5

if curl -f http://$COOLIFY_SERVER:18001/health > /dev/null 2>&1; then
  echo "✅ Backend: http://$COOLIFY_SERVER:18001 (정상)"
else
  echo "❌ Backend: 응답 없음"
fi

if curl -f http://$COOLIFY_SERVER:18000 > /dev/null 2>&1; then
  echo "✅ Frontend: http://$COOLIFY_SERVER:18000 (정상)"
else
  echo "❌ Frontend: 응답 없음"
fi

echo ""
echo "🎉 배포 완료!"
echo "🌐 통합 도메인 URL (권장):"
echo "   메인:       https://InsureGraphPro.$COOLIFY_SERVER"
echo "   Frontend:   https://InsureGraphPro.$COOLIFY_SERVER/"
echo "   Backend:    https://InsureGraphPro.$COOLIFY_SERVER/api"
echo "   API Docs:   https://InsureGraphPro.$COOLIFY_SERVER/api/docs"
echo "   Neo4j:      https://InsureGraphPro.$COOLIFY_SERVER/neo4j"
echo ""
echo "🌐 포트 직접 접속 (대체):"
echo "   Frontend:  http://$COOLIFY_SERVER:18000"
echo "   Backend:   http://$COOLIFY_SERVER:18001"
echo "   API Docs:  http://$COOLIFY_SERVER:18001/docs"
echo "   Neo4j:     http://$COOLIFY_SERVER:17474"
