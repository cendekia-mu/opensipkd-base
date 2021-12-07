from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey

from opensipkd.base.models import Kelurahan, Kecamatan, Kota, Provinsi
from . import Partner
from ..models import DBSession, Base
from ..models import (NamaModel,
                      TABLE_ARGS)


class Company(Base, NamaModel):
    __tablename__ = 'company'
    kategori = Column(String(32))
    partner_id = Column(Integer, ForeignKey(Partner.id))
    logo = Column(String(255))
    alamat = Column(String(255))
    alamat2 = Column(String(255))
    kelurahan_id = Column(Integer, ForeignKey(Kelurahan.id))
    kecamatan_id = Column(Integer, ForeignKey(Kecamatan.id))
    kota_id = Column(Integer, ForeignKey(Kota.id))
    provinsi_id = Column(Integer, ForeignKey(Provinsi.id))
    __table_args__ = (TABLE_ARGS,)

    @classmethod
    def save(cls, values, user, row=None, **kwargs):
        if not row:
            row = Company()
            row.created = datetime.now()
            row.create_uid = user.id

        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = user.id
        row.status = 'status' in values and values['status'] and 1 or 0
        DBSession.add(row)
        DBSession.flush()
        return row

    @classmethod
    def kategori_get(cls):
        return (("kota", "Kota"),
                ("kab", "Kabupaten"),
                ("prov", "Provinsi"))
