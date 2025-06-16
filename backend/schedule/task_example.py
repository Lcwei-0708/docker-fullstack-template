import logging

class TaskExample:
    def __init__(self):
        self.logger = logging.getLogger("schedule")

    def task_for_interval(self):
        try:
            self.logger.info(f"This is a task for interval!")
        except Exception as e:
            self.logger.error(f"This is a task for interval error: {e}")

    def task_for_cron(self):
        try:
            self.logger.info(f"This is a task for cron!")
        except Exception as e:
            self.logger.error(f"This is a task for cron error: {e}")