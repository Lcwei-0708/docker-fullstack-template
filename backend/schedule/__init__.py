from datetime import datetime
from .task_example import TaskExample
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
task_example = TaskExample()

def register_schedules():
    # Add new schedules imports below.
    scheduler.add_job(task_example.task_for_interval, "interval", seconds=10)
    scheduler.add_job(task_example.task_for_cron, "cron", hour=8, minute=0)