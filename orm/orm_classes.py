from datetime import datetime
from typing import List

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
    creator_vk_id = Column(Integer)

    nested_tasks: List["Task"] = relationship(
        "Task", cascade="save-update, delete"
    )

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

    def check_for_subtask(self, subtask_id: int) -> bool:
        if subtask_id in (task.id for task in self.nested_tasks):
            return True
        for task in self.nested_tasks:
            if task.check_for_subtask(subtask_id):
                return True
        return False


class UserSettings:

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    auto_showing = Column(Boolean, nullable=False, default=True)
    user_vk_id = Column(Integer)
