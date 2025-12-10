#!/bin/bash

##############################################################################
# InsureGraph Pro - 개발 환경 중지 스크립트
#
# 이 스크립트는:
# 1. Backend API 서버를 중지합니다
# 2. Frontend 개발 서버를 중지합니다
# 3. 관련 프로세스를 정리합니다
##############################################################################

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  InsureGraph Pro 개발 환경 중지${NC}"
echo -e "${BLUE}=====================================${NC}\n"

##############################################################################
# Backend 서버 중지
##############################################################################

echo -e "${YELLOW}[1/3]${NC} Backend API 서버 중지 중..."

# PID 파일에서 읽기
if [ -f "$PROJECT_ROOT/.backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/.backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend 서버 중지 완료 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend 프로세스가 이미 종료되었습니다${NC}"
    fi
    rm "$PROJECT_ROOT/.backend.pid"
else
    # PID 파일이 없으면 포트로 찾기
    if lsof -ti :8000 >/dev/null 2>&1; then
        lsof -ti :8000 | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✅ Backend 서버 중지 완료 (포트 8000)${NC}"
    else
        echo -e "${YELLOW}⚠️  실행 중인 Backend 서버가 없습니다${NC}"
    fi
fi

echo ""

##############################################################################
# Frontend 서버 중지
##############################################################################

echo -e "${YELLOW}[2/3]${NC} Frontend 개발 서버 중지 중..."

# PID 파일에서 읽기
if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend 서버 중지 완료 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend 프로세스가 이미 종료되었습니다${NC}"
    fi
    rm "$PROJECT_ROOT/.frontend.pid"
else
    # PID 파일이 없으면 포트로 찾기
    for port in 3000 3001; do
        if lsof -ti :$port >/dev/null 2>&1; then
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
            echo -e "${GREEN}✅ Frontend 서버 중지 완료 (포트 $port)${NC}"
        fi
    done

    if ! lsof -ti :3000 >/dev/null 2>&1 && ! lsof -ti :3001 >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  실행 중인 Frontend 서버가 없습니다${NC}"
    fi
fi

echo ""

##############################################################################
# 관련 프로세스 정리
##############################################################################

echo -e "${YELLOW}[3/3]${NC} 관련 프로세스 정리 중..."

# uvicorn 프로세스 정리
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    echo -e "${GREEN}✅ 남은 uvicorn 프로세스 정리 완료${NC}"
fi

# next dev 프로세스 정리
if pgrep -f "next dev" > /dev/null; then
    pkill -f "next dev" 2>/dev/null || true
    echo -e "${GREEN}✅ 남은 Next.js 프로세스 정리 완료${NC}"
fi

echo ""

##############################################################################
# 완료 메시지
##############################################################################

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  개발 환경 중지 완료!${NC}"
echo -e "${GREEN}=====================================${NC}\n"

echo -e "${BLUE}💡 다시 시작하려면:${NC}"
echo -e "   ${BLUE}./dev-start.sh${NC}\n"
