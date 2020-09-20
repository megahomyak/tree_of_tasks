from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DeclarativeBase = declarative_base()


class Task(DeclarativeBase):

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    text = Column(String)
    is_checked = Column(Boolean)
    nested_tasks_is_shown = Column(Boolean)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    creation_date = Column(DateTime, default=datetime.now())

    nested_task = relationship("Task", cascade="save-update, delete")

    def set_is_checked_recursively(self, state: bool) -> None:
        """
        Changes is_checked attribute of the current task and all of its nested
        tasks to the specified value.

        Args:
            state: state of the current task and nested tasks
        """
        for task in self.nested_tasks:
            task.set_is_checked_to(state)
        self.is_checked = state
