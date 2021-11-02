from datetime import datetime

import sqlalchemy as sa
import ziggurat_foundations.models
# from pyramid.security import (Allow, Authenticated, ALL_PERMISSIONS)
from pyramid.authorization import (Allow, Authenticated, ALL_PERMISSIONS)
from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, String, SmallInteger, func)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship, backref)
from ziggurat_foundations import ziggurat_model_init
from ziggurat_foundations.models.base import BaseModel
from ziggurat_foundations.models.external_identity import ExternalIdentityMixin
from ziggurat_foundations.models.group import GroupMixin
from ziggurat_foundations.models.group_permission import GroupPermissionMixin
from ziggurat_foundations.models.group_resource_permission import GroupResourcePermissionMixin
from ziggurat_foundations.models.resource import ResourceMixin
from ziggurat_foundations.models.services.user import UserService
from ziggurat_foundations.models.services.external_identity import ExternalIdentityService
from ziggurat_foundations.models.user import UserMixin
from ziggurat_foundations.models.user_group import UserGroupMixin
from ziggurat_foundations.models.user_permission import UserPermissionMixin
from ziggurat_foundations.models.user_resource_permission import UserResourcePermissionMixin
from zope.sqlalchemy import register

from .meta import Base
from opensipkd.tools import as_timezone

session_factory = sessionmaker()
DBSession = scoped_session(session_factory)
# ZTE = ZopeTransactionExtension()
# DBSession = scoped_session(sessionmaker(extension=ZTE))
register(DBSession)
ziggurat_foundations.models.DBSession = DBSession

TABLE_ARGS = dict(extend_existing=True, schema="public")


# Base = declarative_base()
##############
# Base model #
##############
class CommonModel(object):
    def to_dict_hybrid(self):
        values = {}
        for item in sa_inspect(self.__class__).all_orm_descriptors:
            if type(item) == hybrid_property:
                value = getattr(self, item.__name__)
                print(item.__name__, value)
                if value:
                    values[item.__name__] = value
        return values

    def to_dict(self, null=False):  # Elixir like
        values = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if value or null:
                values[column.name] = value

        return values

    def to_dict_without_none(self):
        values = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if value is not None:
                values[column.name] = value
        return values

    def from_dict(self, values):
        for column in self.__table__.columns:
            if column.name in values:
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
    def query(cls, db_session=DBSession):
        return db_session.query(cls)

    @classmethod
    def query_id(cls, id, db_session=DBSession):
        return cls.query(db_session).filter_by(id=id)

    @classmethod
    def delete(cls, id, db_session=DBSession):
        cls.query_id(id, db_session).delete()


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


class Group(GroupMixin, Base, DefaultModel):
    @classmethod
    def query_group_name(cls, group_name):
        return DBSession.query(cls).filter_by(group_name=group_name)


class GroupPermission(GroupPermissionMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base, CommonModel):
    @classmethod
    def _get_by_user(cls, user):
        return DBSession.query(cls).filter_by(user_id=user.id).all()

    @classmethod
    def get_by_user(cls, user):
        groups = []
        for g in cls._get_by_user(user):
            groups.append(g.group_id)
        return groups


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "group_id",
            "resource_id",
            "perm_name",
            name="pk_group_resources_permissions ",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8"},
    )


class Resource(ResourceMixin, Base):
    pass


class UserPermission(UserPermissionMixin, Base):
    pass


class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass


class User(UserMixin, BaseModel, CommonModel, Base):
    last_login_date = Column(DateTime(timezone=True), nullable=True)
    registered_date = Column(DateTime(timezone=True),
                             nullable=False,
                             default=datetime.utcnow)
    api_key = Column(String(256))

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = UserService.set_password(self, password)

    password = property(_get_password, _set_password)

    def get_groups(self):
        return UserGroup.get_by_user(self)

    def last_login_date_tz(self):
        return as_timezone(self.last_login_date)

    def registered_date_tz(self):
        return as_timezone(self.registered_date)

    def nice_username(self):
        return self.user_name or self.email

    def kode(self):
        pass

    @classmethod
    def query(cls):
        return DBSession.query(cls)

    @classmethod
    def get_by_email(cls, email):
        return DBSession.query(cls).filter_by(email=email).first()

    @classmethod
    def get_by_name(cls, name):
        return DBSession.query(cls).filter_by(user_name=name).first()

    @classmethod
    def get_by_identity(cls, identity):
        if identity.find('@') > -1:
            return cls.get_by_email(identity)
        return cls.get_by_name(identity)

    @classmethod
    def get_by_token(cls, token):
        return DBSession.query(cls).filter_by(security_code=token)

    @classmethod
    def get_departemen_id(cls, user_id):
        partner = Partner.query_user_id(user_id).first()
        return partner and partner.departemen and partner.departemen.id or None

    @classmethod
    def get_departemen_kd(cls, user_id):
        partner = Partner.query_user_id(user_id).first()
        return partner and partner.departemen and partner.departemen.kode or None

    @classmethod
    def get_departemen_id(cls, user_id):
        partner = Partner.query_user_id(user_id).first()
        return partner and partner.departemen and partner.departemen.id or None

    @classmethod
    def get_departemen_nm(cls, user_id):
        partner = Partner.query_user_id(user_id).first()
        return partner and partner.departemen and partner.departemen.nama or None

    @classmethod
    def get_list_by_departemen(cls, departemen_id):
        rows = DBSession.query(User.id, Partner.nama) \
            .join(Partner, User.id == Partner.user_id) \
            .filter(Partner.departemen_id == departemen_id).all()
        result = list(((row[0], row[1]) for row in rows))
        result.insert(0, (0, "All"))
        return result


class ExternalIdentity(ExternalIdentityMixin, CommonModel, Base):
    pass


# It is used when there is a web request.
class RootFactory:
    def __init__(self, request):
        self.__acl__ = [
            (Allow, 'group:1', ALL_PERMISSIONS),
            (Allow, Authenticated, 'view')]
        for gp in DBSession.query(GroupPermission):
            acl_name = 'group:{}'.format(gp.group_id)
            self.__acl__.append((Allow, acl_name, gp.perm_name))


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


class NamaModel(KodeModel):
    nama = Column(String(128))

    @classmethod
    def query_nama(cls, nama, db_session=DBSession):
        return cls.query(db_session).filter_by(nama=nama)

    @classmethod
    def get_by_nama(cls, nama, db_session=DBSession):
        return cls.query_nama(nama, db_session).first()


class Route(Base, NamaModel):
    __tablename__ = 'routes'
    __table_args__ = {'extend_existing': True}
    kode = Column(String(128), unique=True)
    path = Column(String(256), nullable=False, unique=True)
    status = Column(Integer, nullable=False, server_default='1')
    type = Column(SmallInteger, nullable=False, server_default='0')
    app_id = Column(SmallInteger, nullable=False, server_default='0')


class Parameter(Base, NamaModel):
    __tablename__ = 'parameters'
    __table_args__ = {'extend_existing': True}
    value = Column(String(256), nullable=False)


class GroupRoutePermission(Base, CommonModel):
    __tablename__ = 'groups_routes_permissions'
    __table_args__ = {'extend_existing': True, }
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, primary_key=True)
    routes = relationship("Route", backref=backref('routepermission'))
    groups = relationship("Group", backref=backref('grouppermission'))


class Permission(Base, CommonModel):
    __tablename__ = 'permissions'
    __table_args__ = {'extend_existing': True, }
    id = Column(Integer, primary_key=True)
    perm_name = Column(String(64), nullable=False, unique=True)
    description = Column(String(64), nullable=False, unique=True)


class Holiday(Base, DefaultModel):
    __tablename__ = 'holiday'
    tanggal = Column(DateTime)

    @classmethod
    def query_tanggal(cls, tanggal, db_session=DBSession):
        return db_session.query(cls).filter_by(tanggal=tanggal)


class UserDeviceModel(Base, KodeModel):
    __tablename__ = 'user_device'
    user_id=Column(Integer, ForeignKey(User.id))
    kode = Column(String(256))
    token = Column(String(256))
    logged_in = Column(Integer)
    las_login_date = Column(DateTime)

# from .ws_user import WsUser
from .targets import Targets
from .departemen import Departemen, DepartemenUser
from .partner import Partner
from .pegawai import Jabatan, Eselon, PartnerLogin, PartnerDepartemen


def init_model():
    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                        UserResourcePermission, GroupResourcePermission, Resource,
                        ExternalIdentity, passwordmanager=None)
