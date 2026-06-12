import os
import logging
from pyreportjasper import PyReportJasper
from platform import python_version
from opensipkd.tools import get_random_string
from opensipkd.tools.report import *
from opensipkd.base import get_params
log = logging.getLogger(__name__)
log.warning("Opensipkd.base.tools.pbb depreciated use opensipkd.tools.pbb")


db_driver_port = {
    "postgresql": ["postgres", "5432", "org.postgresql.Driver", ],
    "oracle": ["oracle", "1521", "oracle.jdbc.driver.OracleDriver"],

}


def jasper_compile(input_file):
    pyreportjasper = PyReportJasper()
    pyreportjasper.compile(write_jasper=True)


def jasper_db_conn(db_schema=None, dburl="sqlalchemy.url"):
    db = get_params(dburl).split("@")
    db_driver, db_user, db_password = db[0].split(':')
    db_servers, db_name = db[1].split('/')
    # db_user, db_password = db_users.split(":")
    # db_host = db_server
    # if not jdbc_dir:
    #     java_home = os.getenv("JAVA_HOME")
    # jdbc_dir = os.path.join(java_home, 'lib', db_driver_port[db_driver][2])

    if db_servers.find(':') > 1:
        db_host, db_port = db_servers.split(":")
    else:
        db_host = db_servers
        db_port = db_driver_port[db_driver][1]
    jdbc_dir = get_params("jdbc_dir", "")
    jdbc_driver = db_driver_port[db_driver][2]
    db_driver = db_driver_port[db_driver][0]
    log.debug('JDBCDir: %s', jdbc_dir)
    return {
        'driver': db_driver,
        'username': db_user.strip('/'),
        'password': db_password,
        'host': db_host,
        'database': db_name,
        'db_sid': db_name,  # for oracle: added by Tatang
        'schema': db_schema,
        'port': db_port,
        'jdbc_dir': jdbc_dir,
        'jdbc_driver': jdbc_driver,
    }


def jasper_export(input_file, output_file=None, schema=None,
                  output_formats=["pdf"], dburl="sqlalchemy.url",
                  parameters={}, db_schema=None, report_locale="en_US", use_db=True,
                  out_file=None, jvm_maxmem='1024M'):

    module_file = None
    input_file = input_file.split(":") 
    # Cek apakah input_file berupa module
    # if os.name == 'nt' and len(input_file)>1:
    #     input_file=[input_file[0]]
    # if len(input_file) > 1:
    #     path = __import__()
    #     path = os.path.dirname(path.__file__)
    #     input_file = os.path.join(path, input_file[1])
    # else:
    #     input_file=input_file[0]
    if len(input_file) > 1:
        if os.name == 'nt':
            if len(input_file) > 2:  # Cek apakah file berbentuk "C:\module_folder\filename.jrxml"
                module_file = input_file[0]
                input_file = ":".join([input_file[1], input_file[2]])
            else:
                input_file = ":".join([input_file[0], input_file[1]])
        else:
            module_file = input_file[0]
            input_file = input_file[1]

        if module_file:
            path = __import__(module_file)
            path = os.path.dirname(path.__file__)
            input_file = os.path.join(path, input_file)
    else:
        input_file = input_file[0]

    log.debug(f"Input File: {input_file}")

    if not output_file:
        output_file = get_params("tmp_report", "/tmp")
    if out_file:
        log.debug(f"File name to generate: {out_file}")
        out_file = os.path.splitext(out_file)[0]
        output_file = os.path.join(output_file, out_file)
    else:
        output_file = os.path.join(output_file, get_random_string(32))

    db_connection = use_db and jasper_db_conn(
        db_schema=db_schema, dburl=dburl) or {}
    pyreportjasper = PyReportJasper()
    parameters.update({'python_version': python_version()})
    pyreportjasper.config(
        input_file,
        output_file,
        output_formats=output_formats,
        db_connection=db_connection,
        parameters=parameters,
        locale=report_locale
    )
    pyreportjasper.config.jvm_maxmem = jvm_maxmem

    try:
        log.debug(input_file)
        pyreportjasper.compile(write_jasper=True)
        pyreportjasper.process_report()
    except Exception as e:
        log.debug(e)
        raise
    output_files = [".".join([output_file, f]) for f in output_formats]
    log.debug(output_files)
    return output_files
