from sqlalchemy import (
    Column,
    Integer,
    ForeignKey, UniqueConstraint, String
)
from sqlalchemy.orm import relationship

from ..models import NamaModel, Base, TABLE_ARGS


class Provinsi(Base, NamaModel):
    __tablename__ = 'provinsi'
    __table_args__ = (
        UniqueConstraint('kode'),
        TABLE_ARGS
    )


class Kota(Base, NamaModel):
    __tablename__ = 'kota'
    provinsi_id = Column(Integer, ForeignKey(Provinsi.id))
    __table_args__ = (
        UniqueConstraint('provinsi_id', 'kode'),
        TABLE_ARGS
    )
    provinsi = relationship('Provinsi', backref='kota')


class Kecamatan(Base, NamaModel):
    __tablename__ = 'kecamatan'
    kota_id = Column(Integer, ForeignKey(Kota.id))
    __table_args__ = (
        UniqueConstraint('kota_id', 'kode'),
        TABLE_ARGS
    )
    kota = relationship('Kota', backref='kecamatan')


class Kelurahan(Base, NamaModel):
    __tablename__ = 'kelurahan'
    kecamatan_id = Column(Integer, ForeignKey(Kecamatan.id))
    __table_args__ = (
        UniqueConstraint('kecamatan_id', 'kode'),
        TABLE_ARGS
    )
    kecamatan = relationship('Kecamatan', backref='kelurahan')

class AlamatModel(object):
    alamat = Column(String(255))
    alamat2 = Column(String(255))
    kelurahan_id = Column(Integer, ForeignKey(Kelurahan.id))
    kecamatan_id = Column(Integer, ForeignKey(Kecamatan.id))
    kota_id = Column(Integer, ForeignKey(Kota.id))
    provinsi_id = Column(Integer, ForeignKey(Provinsi.id))
