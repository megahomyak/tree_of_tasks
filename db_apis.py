from typing import List, Any

import sqlalchemy.orm
from sqlalchemy import create_engine

import orm_classes


def get_sqlalchemy_db_session(path_to_db: str) -> sqlalchemy.orm.Session:
    sql_engine = create_engine(path_to_db)
    orm_classes.DeclarativeBase.metadata.create_all(sql_engine)
    return sqlalchemy.orm.Session(sql_engine)


class TasksManager:

    def __init__(self, db_session: sqlalchemy.orm.Session) -> None:
        self.db_session = db_session

    def _get_query(self) -> sqlalchemy.orm.Query:
        return (
            self.db_session
            .query(orm_classes.Task)
            .order_by(orm_classes.Task.creation_date)
        )

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
            self._get_query()
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
            self._get_query()
            .filter_by(parent_task_id=None)
            .all()
        )

    def check_existence(self, *filters: Any) -> bool:
        """
        Checks if at least one task with the specified parameters exists in the
        database.

        Args:
            *filters: comparison of a Column object of class Task and some value

        Returns:
            True if any matching task found, else False
        """
        return (
            # I'm not using _get_query here, because it sorts the tasks by
            # creation date
            self.db_session
            .query(orm_classes.Task)
            .filter(filters)
            .first()
        ) is not None

    def get_task_by_id(self, task_id: int) -> orm_classes.Task:
        """
        Gets task by id, if no tasks are found - raises an exception.

        Returns:
            found task

        Raises:
            sqlalchemy.orm.exc.NoResultFound or
            sqlalchemy.orm.exc.MultipleResultsFound
        """
        return (
            self._get_query()
            .filter_by(id=task_id)
            .one()
        )
