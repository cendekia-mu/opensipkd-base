from sqlalchemy import (Column, Integer, String, DateTime, func, )
from sqlalchemy.orm import (scoped_session, sessionmaker, )
from opensipkd.base import Base
from opensipkd.base.models import CommonModel

factory = sessionmaker(autoflush=True, autocommit=True)
LogDBSession = scoped_session(factory)


class Log(Base, CommonModel):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)  # auto incrementing
    line_id = Column(String(32), nullable=False, unique=True)
    logger = Column(String)  # the name of the logger. (e.g. myapp.views)
    level = Column(String)  # info, debug, or error?
    trace = Column(String)  # the full traceback printout
    msg = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now())  # the current timestamp
