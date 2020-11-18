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

    nested_tasks: List["Task"] = relationship(
        "Task", cascade="save-update, delete"
    )

    def change_state_recursively(self, is_checked: bool) -> bool:
        """
        Changes is_checked attribute of the current task and all of its nested
        tasks to the specified value.

        Args:
            is_checked: state of the current task and nested tasks

        Returns:
            bool: something is changed or not
        """
        something_is_changed_in_subtasks = False
        for task in self.nested_tasks:
            something_is_changed_in_subtasks = task.change_state_recursively(
                is_checked
            )
        if self.is_checked != is_checked:
            self.is_checked = is_checked
            return True
        return something_is_changed_in_subtasks

    def check_for_subtask(self, subtask_id: int) -> bool:
        if subtask_id in (task.id for task in self.nested_tasks):
            return True
        for task in self.nested_tasks:
            if task.check_for_subtask(subtask_id):
                return True
        return False
