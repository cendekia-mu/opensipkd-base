import csv
import datetime
import logging
import os
import subprocess
import sys
from getpass import getpass
from pyramid.paster import (get_appsettings, setup_logging, )
from sqlalchemy import (engine_from_config, select, Table, inspect)
from sqlalchemy import text
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql.sqltypes import BOOLEAN
from ziggurat_foundations.models.services.user import UserService

from opensipkd.tools import get_ext

import transaction
from ..models.users import (
    init_model, Group, UserGroup, Permission, GroupPermission, User, 
    UserPermission, ExternalIdentityMixin)
from ..models import (Partner, )
from ..models import (DBSession)
from ..models.handlers import (LogDBSession)
from ..models.meta import Base  
# from ..models import (Base, LogDBSession)
#  Route, Eselon, Jabatan, ResProvinsi, ResDati2, ResKecamatan, ResDesa,
#     Menus, Pangkat


log = logging.getLogger(__name__)


# def routes_callback(typ, **kwargs):
#     if typ == "mapping":
#         return kwargs.get("value")
#     if typ == "value":
#         data = kwargs.get("data")
#         field = kwargs.get("field")
#         splited = data["kode"].split("-")
#         value = None
#         splited_last = splited[len(splited) - 1]
#         if field == "module":
#             value = splited[0]
#         elif field == "def_func":
#             if data["def_func"]:
#                 return data["def_func"]
#             elif splited_last == 'menu':
#                 return None
#             value = splited_last
#         elif field == "class_view":
#             if data["def_func"] == "list" and not data["class_view"] \
#                     or splited_last not in ["add", "edit", "delete", "view", "act", "report", "upload"]:
#                 log.debug(splited[-1:])
#                 log.debug(data)
#                 return "_".join(splited[1:])

#             if splited_last == "menu":
#                 return None
#             value = "_".join(splited[1:-1])

#         elif field == "path":
#             if splited_last == "menu":
#                 return "-".join(splited)
#             elif splited_last in ["act", "report"]:
#                 return "/" + "/".join(splited[:-1]) + "/{act}/" + splited_last
#             elif splited_last == "report":
#                 return "/" + "/".join(splited[:-1]) + "/{act}/act"
#             elif splited_last in ["edit", "view", "delete"]:
#                 return "/" + "/".join(splited[:-1]) + "/{id}/" + splited_last
#             else:
#                 return "/" + "/".join(splited)
#         elif field == "template":
#             if splited_last == "act":
#                 return "json"
#             elif data["template"]:
#                 return data["template"]

#             elif data["def_func"] == "list":
#                 return "list.pt"
#             else:
#                 return "form.pt"

#         return value


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def create_schema(engine, schema):
    with engine.connect() as conn:
        sql = CreateSchema(schema, if_not_exists=True)
        conn.execute(sql)
        conn.commit()


def read_file(filename):
    f = open(filename)
    s = f.read()
    f.close()
    return s


def get_file(filename):
    base_dir = os.path.split(__file__)[0]
    fullpath = os.path.join(base_dir, 'data', filename)
    return open(fullpath)


def restore_csv(table, filename, get_file_func=get_file, db_session=DBSession):
    eng = db_session.get_bind()
    q = db_session.query(table)
    if q.first():
        log.error("Restore discarded")
        return
    with get_file_func(filename) as f:
        reader = csv.DictReader(f)
        filter_ = dict()
        foreigns = dict()
        is_first = True
        fmap = dict()
        for cf in reader:
            if is_first:
                is_first = False
                for fieldname in cf.keys():
                    if not fieldname:
                        continue
                    try:
                        t = fieldname.split('/')
                    except Exception as e:
                        # print(fieldname, cf.keys())
                        raise e

                    fname_orig = t[0]
                    schema = None # "public"
                    if t[1:]:
                        t_array = t[1].split('.')
                        if len(t_array) == 2:
                            foreign_table = t_array[0]
                            foreign_field = t_array[1]
                        else:
                            schema = t_array[0]
                            foreign_table = t_array[1]
                            foreign_field = t_array[2]

                        # foreign_table, foreign_field = t[1].split('.')
                        foreign_table = Table(foreign_table, Base.metadata,
                                              # autoload=True,
                                              autoload_with=eng,
                                              schema=schema)
                        foreign_field = getattr(foreign_table.c, foreign_field)
                        foreigns[fieldname] = (foreign_table, foreign_field)
                    fmap[fieldname] = fname_orig

            row = table()
            for fieldname in cf:
                if fieldname in foreigns:
                    foreign_table, foreign_field = foreigns[fieldname]
                    value = cf[fieldname]
                    # merubah v1.4 ke v.2
                    # sql = select([foreign_table]).where(foreign_field == value)
                    sql = select(foreign_table).where(foreign_field == value)

                    # merubah v1.4 ke v.2
                    # q = Base.metadata.bind.execute(sql)
                    with eng.connect() as conn:
                        q = conn.execute(sql)
                    ft = q.fetchone()
                    val = ft and ft.id or None
                    fieldname = fmap[fieldname]
                else:
                    val = cf[fieldname]

                if not val:
                    continue

                if fieldname == 'user_password':
                    UserService.set_password(row, val)

                try:
                    setattr(row, fieldname, val)
                except:
                    pass

            db_session.add(row)
            db_session.flush()
    return True


# def append_csv(table, filename, keys, t_func=get_file):
# def append_csv(table, filename, keys, get_file_func=get_file, db_session=DBSession):
# Feb 10, 2018 by aagusti
# penambahan parameter db_sesion apabila caller mempunyai db_sesion yang berbeda
# modified by tatang 12-02-2019
# alasan: bila terjadi kesalahan append,
# masih memungkinkan update yg sudah ada dgn syarat is value dari keys masih sama
# sperti salah route url asalkan kode msh sama
def append_csv(table, filename, keys, get_file_func=get_file,
               db_session=DBSession, base=Base, **args):
    eng = db_session.get_bind()

    update_exist = args.get("update_exist") or args.get("update")
    callback = args.get("callback")
    delimiter = args.get("delimiter")
    ext = get_ext(filename).lower()
    # log.debug(f"Extension: {ext.strip()}")
    # log.debug(f"Extension: {ext.strip() == '.tsv'}")
    if not delimiter:
        delimiter = ","
        if ext.strip() == '.tsv':
            delimiter = "\t"

    # log.debug(f"Delimiter: {delimiter}")
    insp = inspect(db_session.connection())
    # print(dir(table.__table__))
    # print("____")
    schema = hasattr(
        table.__table__, "schema") and table.__table__.schema or None # "public"
    columns_table = insp.get_columns(table.__tablename__, schema)
    fields = {}
    for c in columns_table:
        fields[c["name"]] = c["type"]
    # raise Exception(columns_table)

    with get_file_func(filename) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        filter_ = dict()
        foreigns = dict()
        is_first = True
        fmap = dict()
        for cf in reader:
            # log.debug(f"Column Field: {cf}")
            if is_first:
                is_first = False
                for fname in cf.keys():
                    if not fname:
                        continue
                    try:
                        t = fname.split('/')
                    except Exception as e:
                        # log.debug(fname, cf.keys())
                        raise e

                    fname_orig = t[0]
                    schema = None # "public"
                    if t[1:]:
                        t_array = t[1].split('.')
                        if len(t_array) == 2:
                            foreign_table = t_array[0]
                            foreign_field = t_array[1]
                        else:
                            schema = t_array[0]
                            foreign_table = t_array[1]
                            foreign_field = t_array[2]
                        log.debug("%s.%s", schema, foreign_table)
                        foreign_table = Table(foreign_table, base.metadata,
                                              # autoload=True, # merubah v1.4 ke v.2
                                              autoload_with=eng,
                                              schema=schema)
                        foreign_field = getattr(foreign_table.c, foreign_field)
                        foreigns[fname] = (foreign_table, foreign_field)

                    fmap[fname] = fname_orig
            data = dict()

            for fname in cf:
                if not fname:
                    continue
                # Buka Tabel Foreign
                if fname in foreigns:
                    foreign_table, foreign_field = foreigns[fname]
                    value = cf[fname]
                    if callback:
                        value = callback("mapping", table=foreign_table, field=foreign_field,
                                         value=value)

                    # merubah v1.4 ke v.2
                    # sql = select([foreign_table]).where(foreign_field == value)
                    sql = select(foreign_table).where(foreign_field == value)
                    log.debug(f"Query Foreignkey: {str(sql)}")
                    # merubah v1.4 ke v.2
                    # q = Base.metadata.bind.execute(sql)
                    with eng.connect() as conn:
                        q = conn.execute(sql)
                    row = q.fetchone()
                    # if not row:
                    #     raise Exception(f"Foreign key value '{value}' not found in table '{foreign_table.name}' for field '{fname}'")
                    value = row and row.id or None
                    q.close()
                    # connection.close()
                else:
                    value = cf[fname]

                fname_orig = fmap[fname]
                if not value and callback:
                    value = callback("value", data=cf, field=fname_orig)
                data[fname_orig] = value

            for key in keys:
                if key not in data or not data[key]:
                    raise Exception(f"Key Field '{key}' wajib ada")
                filter_[key] = data[key]
            q = db_session.query(table).filter_by(**filter_)
            row = q.first()
            if row:
                if not update_exist:
                    continue
            else:
                row = table()
            user = False
            for fname in cf:
                if not fname:
                    continue
                fname_orig = fmap[fname]
                val = data[fname_orig]
                if not val:
                    continue
                if fname_orig == "user_password":
                    user = True
                    password = val
                
                else:
                    if fname_orig in fields and type(fields[fname_orig]) is BOOLEAN:
                        val = (val == 'true' or val ==
                               '1' or val == 1) and True or False
                    setattr(row, fname_orig, val)

            # Penambahan checking field nullable false wajib ada datanya 2024-09-05
            for c in columns_table:
                # if (not c["nullable"] and c["name"] not in data and c["name"] != "id"):
                if (not c["nullable"] and c["name"] not in data and c["name"] != "id") and c["default"] is None:
                    if c["name"]=="registered_date":
                        setattr(row, c["name"], datetime.datetime.now())
                        continue

                    # update: tambah periksa nilai default.
                    # Jika default=None berarti wajib ada nilainya
                    # by tatang 2024-10-12
                    # log.debug(data)
                    raise Exception(
                        f"Table {str(table.__name__)} Field '{c['name']}' wajib ada {c['type']} ")

            db_session.add(row)
            db_session.flush()
            if user:
                print("Table: ", table.__name__, filter_)
                user_ = db_session.query(User).filter_by(id=row.id).first()
                init_model()
                # UserService.set_password(user_, password)
                user_.password = password
                db_session.add(user_)
                db_session.flush()

        transaction.commit()  # diperlukan commit per record khususnya untuk yang internal link


def ask_password(name):
    while True:
        pass1 = getpass('Tulis password untuk {}: '.format(name))
        if not pass1:
            continue
        pass2 = getpass('Ulangi password untuk {}: '.format(name))
        if pass1 == pass2:
            return pass1
        print('Maaf kedua password tidak sama')


def reset_sequence_(cls, seq):
    q = DBSession.query(cls)
    if not q.first():
        sql = "SELECT setval('{}', 1, false)".format(seq)
        # DBSession.bind.execute(sql)
        # sqlalchemy 2
        DBSession.execute(text(sql))


def reset_sequences():
    pass
    # reset_sequence_(User, 'users_id_seq')
    # reset_sequence_(Group, 'groups_id_seq')


def alembic_run(ini_file, name=None):
    bin_path = os.path.split(sys.executable)[0]
    alembic_bin = os.path.join(bin_path, 'alembic')
    if not name:
        command = (
            alembic_bin, '-c', ini_file, '-n', 'alembic_ziggurat', 'upgrade',
            'head')
        if subprocess.call(command) != 0:
            sys.exit()
    else:
        command = (alembic_bin, '-c', ini_file, '-n', name, 'upgrade', 'head')
        if subprocess.call(command) != 0:
            sys.exit()


# def alembic_run(ini_file, name='alembic_base'):
#     bin_path = os.path.split(sys.executable)[0]
#     alembic_bin = os.path.join(bin_path, 'alembic')
#     command = (alembic_bin, '-c', ini_file, '-n', name, 'upgrade', 'head')
#     if subprocess.call(command) != 0:
#         sys.exit()


def base_alembic_run(ini_file):
    alembic_run(ini_file)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    LogDBSession.configure(bind=engine)
    # Base.metadata.create_all(bind=engine)
    alembic_run(config_uri, "alembic_base")
    # base_alembic_run(config_uri)

    reset_sequences()
    Base.metadata.bind = engine
    with transaction.manager:
        if restore_csv(User, 'users.csv'):
            DBSession.flush()
            q = DBSession.query(User).filter_by(id=1)
            user = q.first()
            init_model()
            if user:
                password = ask_password(user.user_name)
                UserService.set_password(user, password)
        append_csv(Group, 'groups.csv', ['group_name'])
        restore_csv(UserGroup, 'users_groups.csv')
        append_csv(Permission, 'permissions.csv', ['perm_name'])
        append_csv(GroupPermission, 'group_permission.csv',
                   ['group_id', 'perm_name'])
        # append_csv(Route, 'routes.csv', ['kode'])
        # append_csv(Menus, 'menus.csv', ['kode'])
        # append_csv(Eselon, 'eselon.csv', ['kode'])
        # append_csv(Jabatan, 'jabatan.csv', ['kode'])
        # restore_csv(Pangkat, 'pangkat.csv')
        # restore_csv(ResProvinsi, 'provinsi.csv')
        # transaction.commit()
        # restore_csv(ResDati2, 'dati2.csv')
        # transaction.commit()
        # restore_csv(ResKecamatan, 'kecamatan.csv')
        # transaction.commit()
        # restore_csv(ResDesa, 'desa.csv')


# def delete_route(module):
#     try:
#         routes = Route.query().filter(Route.module == module).\
#             order_by(desc(Route.parent_id), desc(Route.order_id), ).limit(100)
#         for route in routes:
#             try:
#                 Route.query_id(route.id).delete()
#                 transaction.commit()
#             except Exception as e:
#                 # print(str(e))
#                 # print(route.nama, route.id, route.parent_id, )
#                 # print("Error")
#                 transaction.abort()
#     except Exception as e:
#         print(str(e))

if __name__ == '__main__':
    main(sys.argv)