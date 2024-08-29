import logging
from datetime import datetime

import ziggurat_foundations.models
from opensipkd.tools import as_timezone
from sqlalchemy import Column, String, SmallInteger, Integer, DateTime, func, Numeric
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (scoped_session, sessionmaker, Session)
from zope.sqlalchemy import register


class MySession(Session):
    def execute(self, clause, params=None, mapper=None, **kw):
        # Your magic with clause here
        # print("Session:", clause, params, mapper, kw)
        return Session.execute(self, clause, params)  # , mapper


session_factory = sessionmaker(class_=MySession)
DBSession = scoped_session(session_factory)
register(DBSession)
ziggurat_foundations.models.DBSession = DBSession
TABLE_ARGS = dict(extend_existing=True, schema="public")


def flush(row, db_session=DBSession):
    db_session.add(row)
    db_session.flush()


class CommonModel(object):
    def to_dict_hybrid(self):
        values = {}
        for item in sa_inspect(self.__class__).all_orm_descriptors:
            if hybrid_property == type(item):
                value = getattr(self, item.__name__)
                print(item.__name__, value)
                if value:
                    values[item.__name__] = value
        return values

    def to_dict(self, null=False, date_format="%d-%m-%Y"):  # Elixir like
        values = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if value:
                if type(column.type) is DateTime and date_format:
                    if value:
                        values[column.name] = value.strftime(date_format)
                else:
                    values[column.name] = value
            else:
                if Integer in type(column.type).__mro__ or Numeric in type(column.type).__mro__:
                    values[column.name] = 0
        return values

    def to_dict_without_none(self):
        values = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if value is not None:
                values[column.name] = value
        return values

    def from_dict(self, values, date_format="%d-%m-%Y"):
        for column in self.__table__.columns:
            if column.name in values:
                if type(column.type) is DateTime and date_format:

                    if values[column.name] and type(values[column.name]) is String:
                        setattr(self, column.name,
                                datetime.strptime(values[column.name], date_format))
                        continue
                setattr(self, column.name, values[column.name])

    def as_timezone(self, fieldname):
        date_ = getattr(self, fieldname)
        return date_ and as_timezone(date_) or None


class DefaultModel(CommonModel):
    id = Column(Integer, primary_key=True)

    @classmethod
    def save(cls, values, row=None, **kwargs):
        if not row:
            row = cls()
        row.from_dict(values)
        return row

    @classmethod
    def count(cls, db_session=DBSession):
        return db_session.query(func.count('id')).scalar()

    @classmethod
    def query(cls, db_session=DBSession, filters=None):
        query = db_session.query(cls)
        if filters:
            filter_expressions = []
            for d in filters:
                field = getattr(cls, d[0])
                operator = d[1]
                value = d[2]
                filter_expressions.append(field.op(operator)(value))
            query = query.filter(
                *[e for i, e in enumerate(filter_expressions) if e is not None])
        return query

    @classmethod
    def query_from(cls, db_session=DBSession, columns=None, filters=None):
        query = db_session.query().select_from(cls)
        for c in columns:
            query = query.add_columns(c)
        return query

    @classmethod
    def query_id(cls, row_id, db_session=DBSession):
        return cls.query(db_session).filter_by(id=row_id)

    @classmethod
    def delete(cls, row_id, db_session=DBSession):
        cls.query_id(row_id, db_session).delete()

    @classmethod
    def flush(cls, row, db_session=DBSession):
        db_session.add(row)
        db_session.flush()


class StandarModel(DefaultModel):
    status = Column(SmallInteger, nullable=False, default=0)
    created = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated = Column(DateTime, nullable=True)
    create_uid = Column(Integer, nullable=True, default=1)
    update_uid = Column(Integer, nullable=True)

    # New Method
    @classmethod
    def query_status(cls, status=0, db_session=DBSession):
        return cls.query(db_session).filter_by(status=status)

    @classmethod
    def disabled(cls):
        return cls.query_status(status=0)

    @classmethod
    def active(cls):
        return cls.query_status(status=1)

    @classmethod
    def draft(cls):
        return cls.disabled()

    @classmethod
    def processed(cls):
        return cls.query_status(status=1)

    @classmethod
    def canceled(cls):
        return cls.query_status(status=9)

    @classmethod
    def get_active(cls):
        return cls.query_status(status=1).all()

    @classmethod
    def get_disabled(cls):
        return cls.query_status(status=0).all()

    @classmethod
    def get_archived(cls, db_session=DBSession):
        return cls.query_status(status=0, db_session=db_session).all()


class KodeModel(StandarModel):
    kode = Column(String(32))

    @classmethod
    def query_kode(cls, kode, db_session=DBSession):
        return cls.query(db_session).filter_by(kode=kode)

    @classmethod
    def get_by_kode(cls, kode, db_session=DBSession):
        return cls.query_kode(kode, db_session).first()


class UraianModel(StandarModel):
    nama = Column(String(128))

    @classmethod
    def query_nama(cls, nama, db_session=DBSession):
        return cls.query(db_session).filter_by(nama=nama)

    @classmethod
    def get_by_nama(cls, nama, db_session=DBSession):
        return cls.query_nama(nama, db_session).first()

    @classmethod
    def get_list(cls):
        return DBSession.query(cls.id, cls.nama).order_by(cls.nama).all()


class NamaModel(KodeModel):
    nama = Column(String(128))

    @classmethod
    def query_nama(cls, nama, db_session=DBSession):
        return cls.query(db_session).filter_by(nama=nama)

    @classmethod
    def get_by_nama(cls, nama, db_session=DBSession):
        return cls.query_nama(nama, db_session).first()

    @classmethod
    def query_list(cls):
        return DBSession.query(cls.id, cls.nama).order_by(cls.nama)

    @classmethod
    def get_list(cls):
        return cls.query_list().all()
