from sqlalchemy.orm import relationship, backref

from opensipkd.models import Base, User, ResDesa, DefaultModel
from sqlalchemy import ForeignKey, Integer, Column, String


class UserArea(DefaultModel, Base):
    __tablename__ = "user_area"
    __table_args__ = {'extend_existing': True}
    user_id = Column(Integer, ForeignKey(User.id))
    desa_id = Column(Integer, ForeignKey(ResDesa.id))
    desa = relationship(ResDesa, backref=backref("user_area"))
    user = relationship(User, backref=backref("user_area"))
    def validator(self, values):
        pass


