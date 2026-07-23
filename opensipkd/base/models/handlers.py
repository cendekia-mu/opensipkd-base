from sqlalchemy import (Column, Integer, String, DateTime, func, Text)
from sqlalchemy.orm import (scoped_session, sessionmaker, )
from ..models.base import CommonModel
from ..models.meta import Base

factory = sessionmaker(autoflush=True, autocommit=True)
LogDBSession = scoped_session(factory)


class Log(Base, CommonModel):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)  # auto incrementing
    line_id = Column(String(32), nullable=False, unique=True)
    logger = Column(Text)  # the name of the logger. (e.g. myapp.views)
    level = Column(Text)  # info, debug, or error?
    trace = Column(Text)  # the full traceback printout
    msg = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now())  # the current timestamp
