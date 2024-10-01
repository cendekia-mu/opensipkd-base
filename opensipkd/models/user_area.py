from opensipkd.models import Base, User, ResDesa, DefaultModel, UserGroup, Group
from sqlalchemy import ForeignKey, Integer, Column
from sqlalchemy.orm import relationship, backref


class UserArea(DefaultModel, Base):
    __tablename__ = "user_area"
    __table_args__ = {'extend_existing': True}
    user_id = Column(Integer, ForeignKey(User.id))
    desa_id = Column(Integer, ForeignKey(ResDesa.id))
    desa = relationship(ResDesa, backref=backref("user_area"))
    user = relationship(User, backref=backref("user_area"))

    def validator(self, values):
        pass

    @classmethod
    def allow_area(cls, user_id, desa_id=None, desa_kd=None,
                   group_names=("Superuser", "pbbm-admin"), ):
        user = UserGroup.query().filter_by(user_id == user_id).outerjoin(
            Group, Group.id == UserGroup.group_id).filter(
            UserGroup.group_name._in(*group_names)).first()
        if user and user.id:
            return True

        if desa_id:
            rs = cls.query().filter(cls.user_id == user_id, cls.desa_id == desa_id)
            if rs and rs.id:
                return True
        if desa_kd:
            rs = cls.query().filter(cls.user_id == user_id) \
                .outerjoin(ResDesa, ResDesa.id == cls.desa_id).filter(
                ResDesa.kode == desa_kd).first()
            if rs and rs.id:
                return True

        return False

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.query().filter_by(user_id=user_id).all()
