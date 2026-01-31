# celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery = Celery(
    "video_manager",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

celery.autodiscover_tasks(["notifications"])
