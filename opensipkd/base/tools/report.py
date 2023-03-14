from opensipkd.tools.report import *
from opensipkd.base import log

log.warning("Opensipkd.base.tools.pbb depreciated use opensipkd.tools.pbb")

# -*- coding: utf-8 -*-
import os
from platform import python_version
from opensipkd.base import get_settings, get_params
from opensipkd.base.tools import get_random_string
from pyreportjasper import PyReportJasper

db_driver_port = {
    "postgresql": ["postgres", "5432", "org.postgresql.Driver", "jdbc:postgresql://localhost:5432/pjdl_ciamis"],
    "oracle": ["oracle", "1512", "oracle.jdbc.driver.OracleDriver"],

}


def jasper_compile(input_file):
    # REPORTS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'reports')
    # input_file = os.path.join(input_file)
    # file_ext = os.path.splitext(input_file)
    # output_file = os.path.join(REPORTS_DIR, 'csv')
    pyreportjasper = PyReportJasper()
    pyreportjasper.compile(write_jasper=True)


def jasper_export(input_file, output_file=None, schema=None,
                  output_formats=["pdf"], dburl="sqlalchemy.url",
                  parameters={}, db_schema=None):
    db = get_params(dburl).split("@")
    db_driver, db_user, db_password = db[0].split(':')
    db_servers, db_name = db[1].split('/')
    # db_user, db_password = db_users.split(":")
    if db_servers.find(':') > 1:
        db_host, db_port = db_servers.split(":")
    else:
        db_host = db_servers
        db_port = db_driver_port[db_driver][1]

    # db_host = db_server
    jdbc_dir = get_params("jdbc_dir", "")
    # if not jdbc_dir:
    #     java_home = os.getenv("JAVA_HOME")
        # jdbc_dir = os.path.join(java_home, 'lib', db_driver_port[db_driver][2])

    jdbc_driver = db_driver_port[db_driver][2]
    db_driver = db_driver_port[db_driver][0]
    log.info(jdbc_dir)
    if not output_file:
        tmp_report = get_params("tmp_report", "/tmp")
        output_file = os.path.join(tmp_report, get_random_string(32))

    conn = {
        'driver': db_driver,
        'username': db_user.strip('/'),
        'password': db_password,
        'host': db_host,
        'database': db_name,
        'schema': db_schema,
        'port': db_port,
        'jdbc_dir': jdbc_dir,
        'jdbc_driver': jdbc_driver,
    }
    pyreportjasper = PyReportJasper()
    # log.info(input_file)
    # log.info(output_file)
    # log.info(conn)
    # log.info(output_formats)

    pyreportjasper.config(
        input_file,
        output_file,
        db_connection=conn,
        output_formats=output_formats,
        parameters={'python_version': python_version()},
        locale='en_US'
    )
    # pyreportjasper.compile(write_jasper=True)
    pyreportjasper.process_report()
    output_files = [".".join([output_file, f]) for f in output_formats]
    log.info(output_files)
    return output_files
