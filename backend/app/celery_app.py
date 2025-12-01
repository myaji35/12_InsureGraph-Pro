"""
Celery Application Configuration

백그라운드 작업 처리를 위한 Celery 설정
"""
import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Celery 인스턴스 생성
celery_app = Celery(
    "insuregraph",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1시간 제한
    task_soft_time_limit=3300,  # 55분 소프트 제한
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat 스케줄 설정 (Story 1.0)
celery_app.conf.beat_schedule = {
    # 매일 새벽 2시에 모든 보험사 크롤링
    "crawl-all-insurers-daily": {
        "task": "crawler.crawl_all_insurers",
        "schedule": crontab(hour=2, minute=0),  # 매일 02:00 KST
        "options": {
            "expires": 3600,  # 1시간 후 만료
        },
    },
    # 매주 일요일 새벽 3시에 오래된 다운로드 파일 정리
    "cleanup-old-downloads-weekly": {
        "task": "downloader.cleanup_old_downloads",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # 일요일 03:00 KST
        "options": {
            "expires": 1800,  # 30분 후 만료
        },
    },
}

# Task 자동 발견
celery_app.autodiscover_tasks(["app.tasks"])
