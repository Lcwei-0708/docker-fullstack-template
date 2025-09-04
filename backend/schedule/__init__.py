from core.database import engine
from .cleanup_tasks import CleanupTasks
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

executors = {
    'default': AsyncIOExecutor(),
}
jobstores = {
    'default': SQLAlchemyJobStore(engine=engine)
}
scheduler = AsyncIOScheduler(jobstores=jobstores, executors=executors)
cleanup_tasks = CleanupTasks()

def register_schedules():
    # Add new schedules imports below.
    scheduler.add_job(
        cleanup_tasks.cleanup_expired_sessions,
        "cron",
        hour=0,
        minute=0,
        id="cleanup_expired_sessions",
        name="Cleanup Expired Sessions",
        replace_existing=True
    )