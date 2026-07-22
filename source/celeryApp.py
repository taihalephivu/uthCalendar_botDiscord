# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# celery.py

from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv('CELERY_BROKER_URL', 'redis://uth_redis:6379/0')

app = Celery('uth_bot', broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
    task_routes={
        'tasks.portalTask': {'queue': 'high_priority'},
        'tasks.deadlineTask': {'queue': 'high_priority'},
        'tasks.registrationTask': {'queue': 'high_priority'},
        'tasks.notifySingleClassTask': {'queue': 'high_priority'},
        'tasks.customDeadlineTask': {'queue': 'high_priority'},
        'tasks.portalWeekTask': {'queue': 'high_priority'},
        
        'tasks.periodicPortalTask': {'queue': 'low_priority'},
        'tasks.periodicCourseTask': {'queue': 'low_priority'},
        'tasks.scheduleClassRemindersTask': {'queue': 'low_priority'},
        'tasks.updateWeatherTask': {'queue': 'low_priority'},
    }
)

app.conf.beat_schedule = {
    'update-weather-hourly': {
        'task': 'tasks.updateWeatherTask',
        'schedule': crontab(minute=0, hour='4-22'),
    },
    'notify-tomorrow-classes': {
        'task': 'tasks.cron_notifyTomorrowClasses',
        'schedule': crontab(minute=0, hour=21),
    },
    'schedule-today-classes': {
        'task': 'tasks.cron_scheduleTodayClasses',
        'schedule': crontab(minute=0, hour=1),
    },
    'scan-deadlines-weekly': {
        'task': 'tasks.cron_autoScanAllUsers',
        'schedule': crontab(minute=0, hour=19, day_of_week=1),
    },
}