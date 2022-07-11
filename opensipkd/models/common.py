from sqlalchemy import Column, String, SmallInteger, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from ziggurat_foundations.tests import User

from .meta import Base
from .base import NamaModel, DefaultModel, DBSession, KodeModel
from .partner import Partner


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


class Holiday(Base, DefaultModel):
    __tablename__ = 'holiday'
    tanggal = Column(DateTime)

    @classmethod
    def query_tanggal(cls, tanggal, db_session=DBSession):
        return db_session.query(cls).filter_by(tanggal=tanggal)


class UserDeviceModel(Base, KodeModel):
    __tablename__ = 'user_device'
    user_id = Column(Integer, ForeignKey(User.id))
    kode = Column(String(256))
    token = Column(String(256))
    logged_in = Column(Integer)
    las_login_date = Column(DateTime(timezone=True))
    expired = Column(DateTime(timezone=True))
    user = relationship(User, backref=backref("devices"))

class ResCompany(Base, NamaModel):
    __tablename__ = 'company'
    partner_id = Column(Integer, ForeignKey(Partner.id))
    partner = relationship(Partner, backref=backref("company"))
