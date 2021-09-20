import logging
import traceback
from datetime import datetime
from hashlib import md5
from opensipkd.base.models.handlers import (
    Log,
    LogDBSession,
    )


class SQLAlchemyHandler(logging.Handler):
    # A very basic logger that commits a LogRecord to the SQL Db
    def emit(self, record):
        trace = None
        exc = record.__dict__['exc_info']
        if exc:
            trace = traceback.format_exc()
        if 'waitress' in record.__dict__['name']:
            return
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
        level = record.__dict__['levelname']
        logger = record.__dict__['name']
        msg = record.__dict__['msg']
        line_id = f'{t} {level} {msg}' 
        line_id = md5(line_id.encode('utf-8'))
        line_id = line_id.hexdigest()
        log = Log(
                line_id=line_id, logger=logger, level=level, trace=trace,
                msg=msg)
        LogDBSession.add(log)
        LogDBSession.flush()
