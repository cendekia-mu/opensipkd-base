from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    String,
    SmallInteger, func
)
from sqlalchemy.orm import (
    relationship,
    backref
)

from opensipkd.models import Partner
from ..models import DBSession, Base
from ..models import (DefaultModel, NamaModel, TABLE_ARGS,
                      User, Departemen)


class Eselon(Base, NamaModel):
    __tablename__ = 'eselon'
    pangkat = Column(String(32))
    ruang = Column(String(1))
    tunjangan = Column(BigInteger)
    __table_args__ = TABLE_ARGS

    def __init__(self):
        pass


class Jabatan(Base, NamaModel):
    __tablename__ = 'jabatan'
    jenis = Column(SmallInteger)
    nama_lain = Column(String(128))
    nama_pendek = Column(String(128))
    eselon_id = Column(SmallInteger, ForeignKey(Eselon.id))
    __table_args__ = TABLE_ARGS

    def __init__(self):
        pass


# class Pangkat(Base, NamaModel):
#     __tablename__ = 'pangkat'
#     pangkat = Column(String(32))
#     ruang = Column(String(1))
#     __table_args__ = TABLE_ARGS
#
#     def __init__(self):
#         pass


class PartnerDepartemen(Base, DefaultModel):
    __tablename__ = 'partner_departemen'
    partner_id = Column(Integer, ForeignKey(Partner.id))
    departemen_id = Column(Integer, ForeignKey(Departemen.id))
    # fungsional_id = Column(Integer, ForeignKey(Jabatan.id))
    jabatan_id = Column(SmallInteger, ForeignKey(Jabatan.id))
    mulai = Column(DateTime(timezone=False))
    selesai = Column(DateTime(timezone=False))

    partner = relationship(Partner, backref=backref("partner_departemen"))
    departemen = relationship(Departemen, foreign_keys=[departemen_id], backref=backref("partner_departemen"))
    # fungsional = relationship(Jabatan, foreign_keys=[fungsional_id], backref=backref("partner_funsional"), )
    jabatan = relationship(Jabatan, foreign_keys=[jabatan_id], backref=backref("partner_jabatan", ))
    __table_args__ = (UniqueConstraint('partner_id', 'departemen_id', 'jabatan_id',
                                       'mulai', name='partner_dept_uq'),
                      TABLE_ARGS)

    @classmethod
    def query_jabatan(cls, partner_id, tanggal):
        query = DBSession.query(cls). \
            filter(cls.partner_id == partner_id,
                   tanggal >= cls.mulai,
                   tanggal <= cls.selesai)
        return query


# class PartnerPangkat(Base, DefaultModel):
#     __tablename__ = 'partner_pangkat'
#     partner_id = Column(Integer, ForeignKey(Partner.id))
#     pangkat_id = Column(Integer, ForeignKey(Pangkat.id))
#     tmt = Column(DateTime(timezone=False))
#     partner = relationship(Partner, backref=backref("partner_pangkat"))
#     pangkat = relationship(Pangkat, backref=backref("partner_pangkat"))
#     __table_args__ = (UniqueConstraint('partner_id', 'pangkat_id'),
#                       TABLE_ARGS)

    # @classmethod
    # def query_pangkat(cls, partner_id, tanggal):
    #     tmt = DBSession.query(func.max(cls.tmt)). \
    #         filter(
    #         cls.partner_id == partner_id,
    #         cls.tmt <= tanggal).first()
    #     return DBSession.query(cls). \
    #         filter(cls.partner_id == partner_id,
    #                cls.tmt <= tmt)
    #

# class PartnerLogin(Base):
#     __tablename__ = 'partner_login'
#     partner_id = Column(Integer, ForeignKey(Partner.id), unique=True)
#     user_id = Column(Integer, ForeignKey(User.id), primary_key=True, )  # ,
#     partner = relationship(Partner, backref=backref('partner_login'))
#     users = relationship(User, backref=backref('partner_login'))
#     __table_args__ = TABLE_ARGS
#
#     @classmethod
#     def query_user(cls, user_id):
#         return DBSession.query(cls).filter_by(user_id=user_id)
