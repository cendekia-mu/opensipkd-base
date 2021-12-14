from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    SmallInteger,
)

from ..models import Base
from ..models import (NamaModel,
                      TABLE_ARGS)

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


class ResKecamatan(Base, NamaModel):
    __tablename__ = 'res_kecamatan'
    __table_args__ = (TABLE_ARGS,)
    ibu_kota = Column(String(64))
    dati2_id = Column(SmallInteger, ForeignKey(ResDati2.id))


kategori_desa = (
    ("desa", "Desa"),
    ("kelurahan", "Kelurahan")
)


class ResDesa(Base, NamaModel):
    __tablename__ = 'res_desa'
    __table_args__ = (TABLE_ARGS,)
    kategori = Column(String(32))
    kecamatan_id = Column(SmallInteger, ForeignKey(ResKecamatan.id))
