#!/bin/bash

##############################################################################
# InsureGraph Pro - 개발 환경 시작 스크립트
#
# 이 스크립트는:
# 1. Docker Desktop을 시작합니다
# 2. Backend API 서버를 시작합니다 (백그라운드)
# 3. Frontend 개발 서버를 시작합니다 (백그라운드)
# 4. 모든 서비스의 상태를 확인합니다
##############################################################################

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  InsureGraph Pro 개발 환경 시작${NC}"
echo -e "${BLUE}=====================================${NC}\n"

##############################################################################
# Step 1: Docker Desktop 확인 및 시작
##############################################################################

echo -e "${YELLOW}[1/5]${NC} Docker Desktop 확인 중..."

if docker ps &> /dev/null; then
    echo -e "${GREEN}✅ Docker Desktop이 이미 실행 중입니다${NC}\n"
else
    echo -e "${YELLOW}⚠️  Docker Desktop을 시작합니다...${NC}"
    open -a Docker

    # Docker가 시작될 때까지 대기
    echo -e "${YELLOW}    Docker 시작 대기 중 (최대 30초)...${NC}"
    for i in {1..30}; do
        if docker ps &> /dev/null; then
            echo -e "${GREEN}✅ Docker Desktop이 시작되었습니다${NC}\n"
            break
        fi
        sleep 1
        echo -n "."
    done

    if ! docker ps &> /dev/null; then
        echo -e "\n${RED}❌ Docker Desktop 시작 실패${NC}"
        echo -e "${YELLOW}    수동으로 Docker Desktop을 시작한 후 다시 시도하세요${NC}"
        exit 1
    fi
fi

##############################################################################
# Step 2: 필수 컨테이너 확인
##############################################################################

echo -e "${YELLOW}[2/5]${NC} 필수 컨테이너 확인 중..."

# PostgreSQL 확인
if docker ps --filter "name=.*postgres" --format "{{.Names}}" | grep -q postgres; then
    echo -e "${GREEN}✅ PostgreSQL 컨테이너 실행 중${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL 컨테이너가 없습니다${NC}"
    echo -e "${YELLOW}    docker-compose.yml을 사용하여 시작하세요:${NC}"
    echo -e "${BLUE}    docker compose up -d postgres${NC}"
fi

# Redis 확인
if docker ps --filter "name=.*redis" --format "{{.Names}}" | grep -q redis; then
    echo -e "${GREEN}✅ Redis 컨테이너 실행 중${NC}"
else
    echo -e "${YELLOW}⚠️  Redis 컨테이너가 없습니다${NC}"
    echo -e "${YELLOW}    docker-compose.yml을 사용하여 시작하세요:${NC}"
    echo -e "${BLUE}    docker compose up -d redis${NC}"
fi

echo ""

##############################################################################
# Step 3: Backend 서버 시작
##############################################################################

echo -e "${YELLOW}[3/5]${NC} Backend API 서버 시작 중..."

# 포트 8000 확인
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  포트 8000이 이미 사용 중입니다${NC}"
    echo -e "${YELLOW}    기존 프로세스를 종료하고 다시 시작합니다...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

cd "$PROJECT_ROOT/backend"

# Virtual environment 확인
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment가 없습니다${NC}"
    echo -e "${YELLOW}    다음 명령어로 생성하세요:${NC}"
    echo -e "${BLUE}    python -m venv venv${NC}"
    echo -e "${BLUE}    source venv/bin/activate${NC}"
    echo -e "${BLUE}    pip install -r requirements.txt${NC}"
    exit 1
fi

# Backend 서버 시작 (백그라운드)
source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Backend 시작 확인
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend API 서버 시작 완료 (PID: $BACKEND_PID)${NC}"
    echo -e "${BLUE}   URL: http://localhost:8000${NC}"
    echo -e "${BLUE}   Docs: http://localhost:8000/docs${NC}"
else
    echo -e "${RED}❌ Backend 서버 시작 실패${NC}"
    echo -e "${YELLOW}    로그 확인: tail -f backend/backend.log${NC}"
    exit 1
fi

echo ""

##############################################################################
# Step 4: Frontend 서버 시작
##############################################################################

echo -e "${YELLOW}[4/5]${NC} Frontend 개발 서버 시작 중..."

cd "$PROJECT_ROOT/frontend"

# 포트 3000/3001 확인
for port in 3000 3001; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  포트 $port이 이미 사용 중입니다${NC}"
        echo -e "${YELLOW}    기존 프로세스를 종료하고 다시 시작합니다...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
done

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules가 없습니다${NC}"
    echo -e "${YELLOW}    의존성을 설치합니다...${NC}"
    npm install
fi

# Frontend 서버 시작 (백그라운드)
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 5

# Frontend 시작 확인
if ps -p $FRONTEND_PID > /dev/null; then
    # 실제 사용 중인 포트 확인 (3000 또는 3001)
    if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        FRONTEND_PORT=3001
    else
        FRONTEND_PORT=3000
    fi

    echo -e "${GREEN}✅ Frontend 개발 서버 시작 완료 (PID: $FRONTEND_PID)${NC}"
    echo -e "${BLUE}   URL: http://localhost:$FRONTEND_PORT${NC}"
else
    echo -e "${RED}❌ Frontend 서버 시작 실패${NC}"
    echo -e "${YELLOW}    로그 확인: tail -f frontend/frontend.log${NC}"
    exit 1
fi

echo ""

##############################################################################
# Step 5: 상태 확인
##############################################################################

echo -e "${YELLOW}[5/5]${NC} 서비스 상태 확인 중..."
sleep 2

# Backend health check
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API: 정상 작동${NC}"
else
    echo -e "${RED}❌ Backend API: 응답 없음${NC}"
fi

# Frontend health check
if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend: 정상 작동${NC}"
else
    echo -e "${RED}❌ Frontend: 응답 없음${NC}"
fi

echo ""

##############################################################################
# 완료 메시지
##############################################################################

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  개발 환경 시작 완료!${NC}"
echo -e "${GREEN}=====================================${NC}\n"

echo -e "${BLUE}📍 서비스 URL:${NC}"
echo -e "   Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "   Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "   API Docs: ${BLUE}http://localhost:8000/docs${NC}\n"

echo -e "${BLUE}📝 로그 확인:${NC}"
echo -e "   Backend:  ${BLUE}tail -f $PROJECT_ROOT/backend/backend.log${NC}"
echo -e "   Frontend: ${BLUE}tail -f $PROJECT_ROOT/frontend/frontend.log${NC}\n"

echo -e "${BLUE}🛑 서버 중지:${NC}"
echo -e "   ${BLUE}./dev-stop.sh${NC}\n"

echo -e "${BLUE}💾 PID 저장:${NC}"
echo "$BACKEND_PID" > "$PROJECT_ROOT/.backend.pid"
echo "$FRONTEND_PID" > "$PROJECT_ROOT/.frontend.pid"
echo -e "   Backend PID: $BACKEND_PID"
echo -e "   Frontend PID: $FRONTEND_PID\n"

# 브라우저 열기 (선택)
read -p "브라우저에서 Frontend를 여시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "http://localhost:$FRONTEND_PORT"
fi
