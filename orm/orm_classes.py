from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DeclarativeBase = declarative_base()


class Task(DeclarativeBase):

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    is_checked = Column(Boolean, default=False, nullable=False)
    is_collapsed = Column(Boolean, default=False, nullable=False)
    parent_id = Column(Integer, ForeignKey("tasks.id"), default=None)
    creation_date = Column(DateTime, default=datetime.now)

    nested_tasks = relationship("Task", cascade="save-update, delete")

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
