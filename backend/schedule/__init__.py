from core.database import engine
from .task_example import TaskExample
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
task_example = TaskExample()

def register_schedules():
    # Add new schedules imports below.
    scheduler.add_job(
        task_example.task_for_interval, 
        "interval", 
        seconds=300,
        id="task_example",
        name="Task Example",
        replace_existing=True
    )