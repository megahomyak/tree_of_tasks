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
            .order_by(orm_classes.Task.creation_date)
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
        """
        Gets tasks, which passed the filter(s).

        Filters are comparison of a Column and some value, also you can use
        OR or AND operators with corresponding construction.

        Args:
            *filters: comparison of a Column object of class Task and some value

        Returns: List of orm classes Task, which are tasks, that passed the
        filters.
        """
        return (
            self.db_session
            .query(orm_classes.Task)
            .filter(*filters)
            .order_by(orm_classes.Task.creation_date)
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
            .order_by(orm_classes.Task.creation_date)
            .all()
        )

    def check_existence(self, *filters: Any) -> bool:
        """
        Checks if the tasks with the specified parameters exist in the database.

        Args:
            *filters: comparison of a Column object of class Task and some value

        Returns:
            True if any matching task found, else False
        """
        return (
            self.db_session
            .query(orm_classes.Task)
            .filter(filters)
            .exists()
        )
