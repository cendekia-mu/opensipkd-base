from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    UniqueConstraint,
    String,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
)

from ..models import NamaModel, Base, DBSession


class Targets(Base, NamaModel):
    __tablename__ = 'targets'
    __table_args__ = {'extend_existing': True}
    tahun = Column(Integer, nullable=False)
    jenis = Column(Integer, nullable=False)
    m01 = Column(BigInteger, nullable=False)
    m02 = Column(BigInteger, nullable=False)
    m03 = Column(BigInteger, nullable=False)
    m04 = Column(BigInteger, nullable=False)
    m05 = Column(BigInteger, nullable=False)
    m06 = Column(BigInteger, nullable=False)
    m07 = Column(BigInteger, nullable=False)
    m08 = Column(BigInteger, nullable=False)
    m09 = Column(BigInteger, nullable=False)
    m10 = Column(BigInteger, nullable=False)
    m11 = Column(BigInteger, nullable=False)
    m12 = Column(BigInteger, nullable=False)

    @classmethod
    def query_jenis_sum(cls, tahun, jenis):
        return DBSession.query(cls.tahun, cls.jenis,
                               func.sum(cls.m01).label('m01'), func.sum(cls.m02).label('m02'),
                               func.sum(cls.m03).label('m03'), func.sum(cls.m04).label('m04'),
                               func.sum(cls.m05).label('m05'), func.sum(cls.m06).label('m06'),
                               func.sum(cls.m06).label('m07'), func.sum(cls.m08).label('m08'),
                               func.sum(cls.m09).label('m09'), func.sum(cls.m10).label('m10'),
                               func.sum(cls.m11).label('m11'), func.sum(cls.m12).label('m12'),
                               ). \
            group_by(cls.tahun, cls.jenis, ). \
            filter(cls.tahun == tahun, cls.jenis == jenis)


class TargetJenis(Base, NamaModel):
    __tablename__ = 'target_jenis'
    __table_args__ = {'extend_existing': True}
