from datetime import datetime

import pytz
import sqlalchemy as sa
from opensipkd.tools import as_timezone
from pyramid.authorization import (Allow, Authenticated, ALL_PERMISSIONS)
from sqlalchemy import (
    Column, Integer, DateTime, String)
from sqlalchemy.orm import (relationship, backref)
from ziggurat_foundations import ziggurat_model_init
from ziggurat_foundations.models.base import BaseModel
from ziggurat_foundations.models.external_identity import ExternalIdentityMixin
from ziggurat_foundations.models.group import GroupMixin
from ziggurat_foundations.models.group_permission import GroupPermissionMixin
from ziggurat_foundations.models.group_resource_permission import \
    GroupResourcePermissionMixin
from ziggurat_foundations.models.resource import ResourceMixin
from ziggurat_foundations.models.services.user import UserService
from ziggurat_foundations.models.user import UserMixin
from ziggurat_foundations.models.user_group import UserGroupMixin
from ziggurat_foundations.models.user_permission import UserPermissionMixin
from ziggurat_foundations.models.user_resource_permission import \
    UserResourcePermissionMixin

from .base import CommonModel, DBSession, DefaultModel
from .meta import Base
from .base import TABLE_ARGS

class GroupPermission(GroupPermissionMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base, CommonModel):
    @classmethod
    def _get_by_user(cls, user):
        return DBSession.query(cls).filter_by(user_id=user.id).all()
    
    @classmethod
    def query(cls):
        return DBSession.query(cls)

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


class User(UserMixin, BaseModel, DefaultModel, Base):
    last_login_date = Column(DateTime(timezone=True), nullable=True)
    registered_date = Column(DateTime(timezone=True),
                             nullable=False,
                             default=datetime.utcnow)
    security_code_date = Column(DateTime(timezone=True),
                                default=datetime(2000, 1, 1,
                                                 tzinfo=pytz.timezone(
                                                     'Asia/Jakarta')),
                                server_default="2000-01-01 01:01+7",
                                )
    api_key = Column(String(256))
    partner_id = Column(Integer)  # , ForeignKey(Partner.id))
    company_id = Column(Integer)  # , ForeignKey(Partner.id))

    # partners = relationship(Partner, backref=backref('users'))

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

    # @classmethod
    # def query(cls):
    #     return DBSession.query(cls)

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
    def query_register(cls):
        return cls.query_from(columns=[cls.email, cls.user_name, cls.registered_date,
                                       cls.last_login_date])

    @classmethod
    def query_list(cls):
        return DBSession.query(cls.id, cls.user_name).order_by(cls.user_name)

    @classmethod
    def get_list(cls):
        qry = cls.query_list()
        return qry.all()

    # @classmethod
    # def get_departemen_id(cls, user_id):
    #     partner = Partner.query_user_id(user_id).first()
    #     return partner and partner.departemen and partner.departemen.id or None
    #
    # @classmethod
    # def get_departemen_kd(cls, user_id):
    #     partner = Partner.query_user_id(user_id).first()
    #     return partner and partner.departemen and partner.departemen.kode or None
    #
    # @classmethod
    # def get_departemen_id(cls, user_id):
    #     partner = Partner.query_user_id(user_id).first()
    #     return partner and partner.departemen and partner.departemen.id or None
    #
    # @classmethod
    # def get_departemen_nm(cls, user_id):
    #     partner = Partner.query_user_id(user_id).first()
    #     return partner and partner.departemen and partner.departemen.nama or None

    # @classmethod
    # def get_list_by_departemen(cls, departemen_id):
    #     rows = DBSession.query(User.id, Partner.nama) \
    #         .join(Partner, User.id == Partner.user_id) \
    #         .filter(Partner.departemen_id == departemen_id).all()
    #     result = list(((row[0], row[1]) for row in rows))
    #     result.insert(0, (0, "All"))
    #     return result


class ExternalIdentity(ExternalIdentityMixin, CommonModel, Base):
    user = relationship(User, backref=backref("external"),
                        overlaps="external_identities,owner")

    @classmethod
    def query(cls):
        return DBSession.query(cls)

    @classmethod
    def query_user(cls, user):
        return cls.query().filter_by(local_user_id=user.id)

    @classmethod
    @classmethod
    def external(cls, user):
        return cls.query_user(user).count() > 0


# class GroupRoutePermission(Base, CommonModel):
#     __tablename__ = 'groups_routes_permissions'
#     __table_args__ = {'extend_existing': True, }
#     route_id = Column(Integer, ForeignKey("routes.id"), nullable=False, primary_key=True)
#     group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, primary_key=True)
#     routes = relationship("Route", backref=backref('routepermission'))
#     groups = relationship("Group", backref=backref('grouppermission'))


class Permission(Base, CommonModel):
    __tablename__ = 'permissions'
    __table_args__ = ({'extend_existing': True, },
                      TABLE_ARGS)
    id = Column(Integer, primary_key=True)
    perm_name = Column(String(64), nullable=False, unique=True)
    description = Column(String(64), nullable=False, unique=True)


class Group(GroupMixin, Base, DefaultModel):
    member_count = Column(Integer, nullable=True, default=0)

    @classmethod
    def query_group_name(cls, group_name):
        return DBSession.query(cls).filter_by(group_name=group_name)


# It is used when there is a web request.
class RootFactory:
    def __init__(self, request):
        gr = DBSession.query(Group).filter_by(group_name="Superuser").first()
        gr_id = gr and gr.id or 1
        self.__acl__ = [
            (Allow, f'group:{gr_id}', ALL_PERMISSIONS),
            (Allow, Authenticated, 'view')]
        for gp in DBSession.query(GroupPermission):
            acl_name = 'group:{}'.format(gp.group_id)
            self.__acl__.append((Allow, acl_name, gp.perm_name))


def init_model():
    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                        UserResourcePermission, GroupResourcePermission,
                        Resource,
                        ExternalIdentity, passwordmanager=None)