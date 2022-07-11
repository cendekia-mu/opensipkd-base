import sys
import re
import pytz
import transaction
from zope.sqlalchemy import register
from datetime import datetime
from hashlib import md5
from opensipkd.base import Base
from opensipkd.tools import create_datetime
from pyramid.paster import get_appsettings
from sqlalchemy import (
    engine_from_config,
    exc,
    )
from sqlalchemy.orm import sessionmaker
from opensipkd.models.handlers import (
    Log,
    LogDBSession,
    )


FIRST_LINE_PATTERN = r'^([\d]*)-([\d]*)-([\d]*) '\
                     r'([\d]*):([\d]*):([\d]*),([\d]*) '\
                     '(INFO|ERROR|WARNI) (.*)'
REGEX_FIRST_LINE = re.compile(FIRST_LINE_PATTERN)


def usage(argv):
    print("command config log_file")
    exit(1)


def main(argv=sys.argv):
    def save():
        if not line_id:
            return
        logger = loggers[0]
        if logger.find('waitress') > -1:
            return
        msg = '\n'.join(lines)
        row = Log(
                created_at=created_at, msg=msg, line_id=line_id, level=level,
                logger=logger)
        LogDBSession.add(row)
        try:
            LogDBSession.flush()
        except exc.IntegrityError as e:
            s = str(e)
            if s.find('duplicate key') == -1:
                raise e

    if len(argv) != 3:
        usage(argv)
    config_uri = argv[1]
    settings = get_appsettings(config_uri)
    tz = pytz.timezone(settings['timezone'])
    engine = engine_from_config(settings, 'sqlalchemy.')
    LogDBSession.configure(bind=engine)
    log_file = argv[2]
    lines = []
    line_id = None
    no = 0
    with open(log_file, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                save()
                break
            s = line.rstrip()
            match = REGEX_FIRST_LINE.search(s)
            if match:
                save()
                del lines[:]
                line_id = md5(line.encode('utf-8')).hexdigest()
                year, month, day, hour, minute, sec, msec, level, s = \
                    match.groups()
                t = s.split()
                s = ' '.join(t[1:])
                loggers = t[0].strip('[]')
                loggers = loggers.split('][')
                without_tz = datetime(
                                int(year), int(month), int(day), int(hour),
                                int(minute), int(sec), int(msec)*1000)
                created_at = tz.localize(without_tz)  # with time zone
                no += 1
                print(f'#{no} {created_at}')
            lines.append(s)
