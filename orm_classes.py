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

    nested_tasks = relationship("Task", cascade="save-update, delete")
