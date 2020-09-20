from typing import List, Any

import sqlalchemy.orm
from sqlalchemy import create_engine

import orm_classes


def get_sqlalchemy_db_session(path_to_db: str) -> sqlalchemy.orm.Session:
    sql_engine = create_engine(path_to_db)
    orm_classes.DeclarativeBase.metadata.create_all(sql_engine)
    return sqlalchemy.orm.Session(sqlalchemy)


class TasksManager:

    def __init__(self, db_session: sqlalchemy.orm.Session) -> None:
        self.db_session = db_session

    def get_tasks(self) -> List[orm_classes.Task]:
        return (
            self.db_session
            .query(orm_classes.Task)
            .all()
        )

    def append(self, *tasks: orm_classes.Task) -> None:
        self.db_session.add_all(tasks)

    def commit(self) -> None:
        self.db_session.commit()

    def delete(self, *tasks: orm_classes.Task) -> None:
        for task in tasks:
            self.db_session.delete(task)

    def get_filtered_tasks(self, *filters: Any) -> List[orm_classes.Task]:
        return (
            self.db_session
            .query(orm_classes.Task)
            .filter(*filters)
            .all()
        )

    def get_root_tasks(self) -> List[orm_classes.Task]:
        """
        Gets all tasks, which have no parent task, aka root tasks.

        Returns: List of Tasks, which is orm classes' objects, so you can
        change them and then commit changes to the database.
        """
        return (
            self.db_session
            .query(orm_classes.Task)
            .filter(orm_classes.Task.parent_task_id is None)
            .all()
        )
