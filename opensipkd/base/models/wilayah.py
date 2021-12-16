from opensipkd.base.models import TABLE_ARGS
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    SmallInteger,
)

from .meta import Base
from .common import (NamaModel)

kategori_provinsi = (
    ("provinsi", "Provinsi"),
    ("provinsi administratif", "Provinsi Administratif"),
)


class ResProvinsi(Base, NamaModel):
    __tablename__ = 'res_provinsi'
    __table_args__ = (TABLE_ARGS,)
    kategori = Column(String(32))
    ibu_kota = Column(String(64))


kategori_dati2 = (
    ("kota", "Kota"),
    ("kabupaten", "Kabupaten"),
    ("kota administratif", "Kota Administratif"),
    ("kabupaten administratif", "Kabupaten Administratif"),
)


class ResDati2(Base, NamaModel):
    __tablename__ = 'res_dati2'
    __table_args__ = (TABLE_ARGS,)
    kategori = Column(String(32))
    ibu_kota = Column(String(64))
    provinsi_id = Column(SmallInteger, ForeignKey(ResProvinsi.id))

    @classmethod
    def get_list(cls, provinsi_id):
        qry = cls.query_list()
        if provinsi_id:
            qry = qry.filter(cls.provinsi_id == provinsi_id)
        return qry.all()

class ResKecamatan(Base, NamaModel):
    __tablename__ = 'res_kecamatan'
    __table_args__ = (TABLE_ARGS,)
    ibu_kota = Column(String(64))
    dati2_id = Column(SmallInteger, ForeignKey(ResDati2.id))
    @classmethod
    def get_list(cls, dati2_id):
        qry = cls.query_list()
        if dati2_id:
            qry = qry.filter(cls.dati2_id == dati2_id)
        return qry.all()


kategori_desa = (
    ("desa", "Desa"),
    ("kelurahan", "Kelurahan")
)


class ResDesa(Base, NamaModel):
    __tablename__ = 'res_desa'
    __table_args__ = (TABLE_ARGS,)
    kategori = Column(String(32))
    kecamatan_id = Column(SmallInteger, ForeignKey(ResKecamatan.id))

    @classmethod
    def get_list(cls, kecamatan_id):
        qry = cls.query_list()
        if kecamatan_id:
            qry = qry.filter(cls.kecamatan_id == kecamatan_id)
        return qry.all()
