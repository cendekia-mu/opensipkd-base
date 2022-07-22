import os
import sys
import csv
from collections import defaultdict

import transaction
import subprocess
from getpass import getpass
from sqlalchemy import (engine_from_config, select, Table, )
from sqlalchemy.schema import CreateSchema
from ziggurat_foundations.models.services.user import UserService
from pyramid.paster import (get_appsettings, setup_logging, )

from opensipkd.models.handlers import LogDBSession
from opensipkd.models import (
    init_model, DBSession, Base, Group, UserGroup, Permission, GroupPermission,
    User, Route, Eselon, Jabatan, ResProvinsi, ResDati2, ResKecamatan, ResDesa,
    Menus)

from sqlalchemy.dialects import oracle
from sqlalchemy import text

# , mssql
# from .tools import mkdir


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def create_schema(engine, schema):
    sql = select([text('schema_name')]).select_from(
        text('information_schema.schemata')).where(
        text("schema_name = '%s'" % schema))
    if isinstance(engine.dialect, oracle.dialect):
        sql = select(['owner']).select_from('dba_segments').where(
            "owner = '%s'" % schema.upper())
    print(sql)
    q = engine.execute(sql)
    if not q.fetchone():
        engine.execute(CreateSchema(schema))


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
    q = db_session.query(table)
    if q.first():
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
                        print(fieldname, cf.keys())
                        raise e

                    fname_orig = t[0]
                    schema = "public"
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
                                              autoload=True, schema=schema)
                        foreign_field = getattr(foreign_table.c, foreign_field)
                        foreigns[fieldname] = (foreign_table, foreign_field)
                    fmap[fieldname] = fname_orig

            row = table()
            for fieldname in cf:
                if fieldname in foreigns:
                    foreign_table, foreign_field = foreigns[fieldname]
                    value = cf[fieldname]
                    sql = select([foreign_table]).where(foreign_field == value)
                    q = Base.metadata.bind.execute(sql)
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


# def append_csv(table, filename, keys, get_file_func=get_file):
# def append_csv(table, filename, keys, get_file_func=get_file, db_session=DBSession):
# Feb 10, 2018 by aagusti
# penambahan parameter db_sesion apabila caller mempunyai db_sesion yang berbeda
# modified by tatang 12-02-2019
# alasan: bila terjadi kesalahan append,
# masih memungkinkan update yg sudah ada dgn syarat is value dari keys masih sama 
# sperti salah route url asalkan kode msh sama
def append_csv(table, filename, keys, get_file_func=get_file,
               db_session=DBSession, update_exist=False):
    with get_file_func(filename) as f:
        reader = csv.DictReader(f)
        filter_ = dict()
        foreigns = dict()
        is_first = True
        fmap = dict()
        for cf in reader:
            if is_first:
                is_first = False
                for fname in cf.keys():
                    if not fname:
                        continue
                    try:
                        t = fname.split('/')
                    except Exception as e:
                        print(fname, cf.keys())
                        raise e

                    fname_orig = t[0]
                    schema = "public"
                    if t[1:]:
                        t_array = t[1].split('.')
                        if len(t_array) == 2:
                            foreign_table = t_array[0]
                            foreign_field = t_array[1]
                        else:
                            schema = t_array[0]
                            foreign_table = t_array[1]
                            foreign_field = t_array[2]

                        foreign_table = Table(foreign_table, Base.metadata,
                                              autoload=True, schema=schema)
                        foreign_field = getattr(foreign_table.c, foreign_field)
                        foreigns[fname] = (foreign_table, foreign_field)

                    fmap[fname] = fname_orig
            data = dict()
            for fname in cf:
                if not fname:
                    continue

                if fname in foreigns:
                    foreign_table, foreign_field = foreigns[fname]
                    value = cf[fname]
                    sql = select([foreign_table]).where(foreign_field == value)
                    q = Base.metadata.bind.execute(sql)
                    row = q.fetchone()
                    value = row and row.id or None

                else:
                    value = cf[fname]
                fname_orig = fmap[fname]
                data[fname_orig] = value
            for key in keys:
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
                    setattr(row, fname_orig, val)

            db_session.add(row)
            db_session.flush()
            if user:
                row = db_session.query(User).filter_by(id=row.id).first()
                init_model()
                UserService.set_password(row, password)
                db_session.add(row)
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
        DBSession.bind.execute(sql)


def reset_sequences():
    reset_sequence_(User, 'users_id_seq')
    reset_sequence_(Group, 'groups_id_seq')


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


def alembic_run(ini_file, name='alembic_base'):
    bin_path = os.path.split(sys.executable)[0]
    alembic_bin = os.path.join(bin_path, 'alembic')
    command = (alembic_bin, '-c', ini_file, '-n', name, 'upgrade', 'head')
    if subprocess.call(command) != 0:
        sys.exit()


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
    alembic_run(config_uri)
    Base.metadata.create_all(engine)
    base_alembic_run(config_uri)

    reset_sequences()
    Base.metadata.bind = engine
    with transaction.manager:
        if restore_csv(User, 'users.csv'):
            DBSession.flush()
            q = DBSession.query(User).filter_by(id=1)
            user = q.first()
            init_model()
            password = ask_password(user.user_name)
            UserService.set_password(user, password)
        append_csv(Group, 'groups.csv', ['group_name'])
        restore_csv(UserGroup, 'users_groups.csv')
        append_csv(Permission, 'permissions.csv', ['perm_name'])
        append_csv(GroupPermission, 'group_permission.csv',
                   ['group_id', 'perm_name'])
        append_csv(Route, 'routes.csv', ['kode'])
        append_csv(Menus, 'menus.csv', ['kode'])
        append_csv(Eselon, 'eselon.csv', ['kode'])
        append_csv(Jabatan, 'jabatan.csv', ['kode'])
        restore_csv(ResProvinsi, 'provinsi.csv')
        transaction.commit()
        restore_csv(ResDati2, 'dati2.csv')
        transaction.commit()
        restore_csv(ResKecamatan, 'kecamatan.csv')
        transaction.commit()
        restore_csv(ResDesa, 'desa.csv')
