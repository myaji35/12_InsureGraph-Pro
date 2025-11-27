"""
Celery Application Configuration

백그라운드 작업 처리를 위한 Celery 설정
"""
import os
from celery import Celery
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

# Task 자동 발견
celery_app.autodiscover_tasks(["app.tasks"])
