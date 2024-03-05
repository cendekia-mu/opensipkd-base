from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    SmallInteger,
)
from sqlalchemy.orm import (
    relationship,
    backref
)

from . import ResCompany
from ..models import DBSession, Base
from ..models import (NamaModel,
                      TABLE_ARGS)


class Departemen(Base, NamaModel):
    __tablename__ = 'departemen'
    __table_args__ = (TABLE_ARGS,)
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('public.departemen.id'))
    kategori = Column(String(32))
    alamat = Column(String(255))
    singkat = Column(String(32))
    level_id = Column(SmallInteger)
    children = relationship(
        "Departemen", backref=backref('parent', remote_side=[id]))
    company_id = Column(Integer, ForeignKey(ResCompany.id))

    def get_parents(self, start=False):
        allparents = []
        if start:
            allparents.append(self.nama)
        p = self.parent
        while p:
            allparents.append(p.nama)
            p = p.parent
        return allparents

    @property
    def parents(self, start=False):
        return self.get_parents()

    @property
    def name_get(self):
        allparents = self.get_parents(True)
        return '/'.join(reversed(allparents))

    @property
    def uraian_all(self):
        allparents = self.get_parents(True)
        return '/'.join(reversed(allparents))

    @classmethod
    def get_list(cls):
        return DBSession.query(cls.id, cls.nama).order_by(cls.nama).all()

# class DepartemenUser(Base, DefaultModel):
#     __tablename__ = 'departemen_user'
#     user_id = Column(Integer, ForeignKey(User.id), unique=True)
#     departemen_id = Column(Integer, ForeignKey(Departemen.id))
#     sub_departemen = Column(SmallInteger, nullable=True)
#     departemen = relationship("Departemen", backref="user_departemen")
#     user = relationship("User", backref="user_departemen")
#     __table_args__ = TABLE_ARGS
#
#     @classmethod
#     def query_user_id(cls, user_id):
#         return DBSession.query(cls).filter_by(user_id=user_id)
#
#     @classmethod
#     def get_kode(cls, user_id):
#         row = cls.query_user_id(user_id).first()
#         return row and row.departemen.kode or None
#
#     @classmethod
#     def ids(cls, user_id):
#         r = ()
#         departemens = DBSession.query(cls.departemen_id, cls.sub_departemen, Departemen.kode
#                                       ).join(Departemen).filter(cls.departemen_id == Departemen.id,
#                                                                 cls.user_id == user_id).all()
#         for departemen in departemens:
#             if departemen.sub_departemen:
#                 rows = DBSession.query(Departemen.id).filter(Departemen.kode.ilike('%s%%' % departemen.kode)).all()
#             else:
#                 rows = DBSession.query(Departemen.id).filter(Departemen.kode == departemen.kode).all()
#             for i in range(len(rows)):
#                 r = r + (rows[i])
#         return r
#
#     @classmethod
#     def departemen_granted(cls, user_id, departemen_id):
#         departemens = DBSession.query(cls.departemen_id, cls.sub_departemen, Departemen.kode
#                                       ).join(Departemen).filter(cls.departemen_id == Departemen.id,
#                                                                 cls.user_id == user_id).all()
#         for departemen in departemens:
#             if departemen.sub_departemen:
#                 rows = DBSession.query(Departemen.id).filter(Departemen.kode.ilike('%s%%' % departemen.kode)).all()
#             else:
#                 rows = DBSession.query(Departemen.id).filter(Departemen.kode == departemen.kode).all()
#             for i in range(len(rows)):
#                 if int(rows[i][0]) == int(departemen_id):
#                     return True
#         return False
#
#     @classmethod
#     def get_filtered(cls, request):
#         filter = "'%s' LIKE public.departemens.kode||'%%'" % request.session['departemen_kd']
#         q1 = DBSession.query(Departemen.kode, UserDepartemen.sub_departemen).join(UserDepartemen). \
#             filter(UserDepartemen.user_id == request.user.id,
#                    UserDepartemen.departemen_id == Departemen.id,
#                    text(filter))
#         return q1.first()
