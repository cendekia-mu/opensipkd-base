# from opensipkd.models import Base, User, Departemen, DefaultModel, UserGroup, Group
# from sqlalchemy import ForeignKey, Integer, Column
# from sqlalchemy.orm import relationship, backref
#
#
# class UserDepartemen(DefaultModel, Base):
#     __tablename__ = "user_dep"
#     __table_args__ = {'extend_existing': True}
#     user_id = Column(Integer, ForeignKey(User.id))
#     departemen_id = Column(Integer, ForeignKey(Departemen.id))
#     allow_sub = Column(Boolean)
#     departemen = relationship(Departemen, backref=backref("user_dep"))
#     user = relationship(User, backref=backref("user_area"))
#
#     def validator(self, values):
#         pass
#
#     @classmethod
#     def _allowed(cls, kode):
#         departemen=[]
#         rows = cls.query().filter(cls.kode.ilike(f"{row.kode}%"))
#         for row in rows.all():
#             departemen.append(row.id)
#             if row.allow_sub:
#                 departemen.extend(self._allowed(row.kode))
#         return departemen
#
#     @classmethod
#     def allowed(cls, user_id):
#         rows = cls.query().filter(cls.user_id==user_id)
#         departemen = []
#         for row in rows.all():
#             departemen.append(departemen_id)
#             if row.allow_sub:
#                 departemen.extend(cls._allowed(row.kode))
#
#         return departemen
#
#     @classmethod
#     def allow_area(cls, user_id, departemen_id=None,
#                    group_names=("Superuser", "pbbm-admin"), ):
#
#         if user and user.id:
#             return True
#
#         if not desa_id and not desa_kd:
#             raise Exception("parameter desa_id atau desa_kd wajib dikirim")
#
#         if desa_id:
#             rs = cls.query().filter(cls.user_id == user_id, cls.desa_id == desa_id)
#             if rs and rs.id:
#                 return True
#         if desa_kd:
#             rs = cls.query().filter(cls.user_id == user_id) \
#                 .outerjoin(ResDesa, ResDesa.id == cls.desa_id).filter(
#                 ResDesa.kode == desa_kd).first()
#             if rs and rs.id:
#                 return True
#
#         return False
#
#     @classmethod
#     def get_by_user_id(cls, user_id):
#         return cls.query().filter_by(user_id=user_id).all()
