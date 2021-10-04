from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
    String,
    SmallInteger,
    DateTime
)

from . import DefaultModel
from sqlalchemy.orm import (
    relationship,
    backref
)

from ..models import (Base, TABLE_ARGS)
from ..models import (NamaModel, User, Departemen)


class PartnerModel(NamaModel):
    status = Column(Integer, default=1)  # 0 Inaktif - 1 Aktif
    # no_urut       = Column(Integer)
    alamat_1 = Column(String(128))
    alamat_2 = Column(String(128))
    email = Column(String(40))
    phone = Column(String(16))
    fax = Column(String(16))
    mobile = Column(String(16))
    website = Column(String(64))
    pic = Column(String(16))
    pic_mobile = Column(String(16))
    pic_email = Column(String(16))
    pic_jabatan = Column(String(16))

    @classmethod
    def query_email(cls, email):
        return cls.query().filter_by(email=email)

    @classmethod
    def query_mobile(cls, mobile):
        return cls.query().filter_by(mobile=mobile)


class Partner(Base, PartnerModel):
    __tablename__ = 'partner'
    kelurahan = Column(String(128))
    kecamatan = Column(String(128))
    kota = Column(String(128))
    provinsi = Column(String(128))
    is_vendor = Column(SmallInteger, nullable=False, )
    is_customer = Column(SmallInteger, nullable=False, )
    bank = Column(String(16))
    bank_accnt = Column(String(16))
    user_id = Column(Integer, ForeignKey(User.id), nullable=True)  # referensi ke login
    departemen_id = Column(Integer, ForeignKey(Departemen.id))  # referensi ke default skpd
    users = relationship("User", backref=backref('partner'))
    departemen = relationship('Departemen', backref=backref('partner'))
    rt = Column(String(3))
    rw = Column(String(3))
    tempat_lahir = Column(String(128))
    tgl_lahir = Column(DateTime(timezone=False))
    jenis_kelamin = Column(String(1))
    gol_darah = Column(String(2))
    agama = Column(String(32))
    perkawinan = Column(String(2))
    pekerjaan = Column(String(32))
    kewarganegaraan = Column(String(10))
    # npwp        = Column(String(16))
    # npwpd       = Column(String(16))

    @classmethod
    def query_user_id(cls, user_id):
        return cls.query().filter_by(user_id=user_id)

    @classmethod
    def query_user(cls, user):
        return cls.query_user_id(user.id)

    @classmethod
    def query_identity(cls, ident):
        row = cls.query().filter_by(kode=ident).first()
        if not row:
            row = cls.query().filter_by(email=ident).first()
        if not row:
            row = cls.query().filter_by(mobile=ident).first()
        return row

class PartnerUserModel(Base, DefaultModel):
    __tablename__ = 'partner_user'
    partner_id = Column(Integer, ForeignKey(Partner.id))
    user_id = Column(Integer, ForeignKey(User.id))