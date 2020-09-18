import sqlalchemy.orm
from sqlalchemy import create_engine

import orm_classes


def get_sqlalchemy_db_session(path_to_db: str) -> sqlalchemy.orm.Session:
    sql_engine = create_engine(path_to_db)
    orm_classes.DeclarativeBase.metadata.create_all(sql_engine)
    return sqlalchemy.orm.Session(sqlalchemy)
