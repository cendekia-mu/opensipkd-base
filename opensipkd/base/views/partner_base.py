from sqlalchemy import true
import colander
from deform import FileData, widget
from opensipkd.tools import mem_tmp_store
from translationstring import TranslationStringFactory

# from opensipkd.base.views.dati2 import dati2_widget
# from opensipkd.base.views.desa import desa_widget
# from opensipkd.base.views.kecamatan import kecamatan_widget
# from opensipkd.base.views.provinsi import provinsi_widget
# from opensipkd.models import Partner
from . import Validator
# from .. import get_urls
from ..models import Partner


_ = TranslationStringFactory('partner')


class PartnerEmailValidator(colander.Email, Validator):
    def __init__(self, row):
        Validator.__init__(self, row)
        colander.Email.__init__(self)

    def __call__(self, node, value):
        def email_found():
            data = dict(email=email, rid=found.id, rname=found.nama)
            ts = _(
                'email-already-used',
                default='Email ${email} already used by Partner ID ${rid}: ${rname}',
                mapping=data)
            raise colander.Invalid(node, ts)

        if self.match_object.match(value) is None:
            raise colander.Invalid(node, _('Invalid email format'))

        email = value.lower()
        q = Partner.query().filter_by(email=email)
        found = q.first()
        if found and (not self.row or self.row.email != found.email):
            email_found()


@colander.deferred
def partner_email_validator(node, kw):
    return PartnerEmailValidator(kw['row'])


class PartnerKodeValidator(Validator):
    def __init__(self, row):
        Validator.__init__(self, row)

    def __call__(self, node, value):
        def err_found():
            data = dict(kode=val, rid=found.id, rnama=found.nama)
            ts = _(
                'kode-already-used',
                default='Kode ${kode} already used by Partner ID ${rid}: ${rnama}',
                mapping=data)
            raise colander.Invalid(node, ts)

        val = value
        q = Partner.query().filter_by(kode=val)
        found = q.first()
        if found and (not self.row or self.row.kode != found.kode):
            err_found()


@colander.deferred
def partner_kode_validator(node, kw):
    return PartnerKodeValidator(kw['row'])


class NamaSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=partner_kode_validator,
        oid="kode",
        title="NIK",
        width="100pt")
    nama = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="nama")
    mobile = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        oid="mobile")

    email = colander.SchemaNode(
        colander.String(),
        validator=partner_email_validator,
        oid="email")


class PartnerSchema(NamaSchema):
    nip = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=32),
        oid="nip")
    # npwp = colander.SchemaNode(
    #     colander.String(),
    #     missing=colander.drop,
    #     validator=colander.Length(max=32),
    #     oid="npwp")


    alamat_1 = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=128),
        oid="alamat_1")
    alamat_2 = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=128),
        oid="alamat_2")
    kelurahan = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=64),
        oid="kelurahan")
    kecamatan = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=64),
        oid="kecamatan")
    kota = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        missing=colander.drop,
        oid="kota")
    provinsi = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        missing=colander.drop,
        oid="provinsi")
    # provinsi_id = colander.SchemaNode(
    #     colander.Integer(),
    #     widget=provinsi_widget,
    #     missing=colander.drop,
    #     oid="provinsi_id",
    #     slave="dati2_id",
    #     slave_url="/dati2/select/act?provinsi_id=",
    #     title="Provinsi",

    # )
    # dati2_id = colander.SchemaNode(
    #     colander.Integer(),
    #     widget=dati2_widget,
    #     missing=colander.drop,
    #     slave="kecamatan_id",
    #     slave_url="/kecamatan/select/act?dati2_id=",
    #     title="Kab/Kota",
    #     oid="dati2_id")
    # kecamatan_id = colander.SchemaNode(
    #     colander.Integer(),
    #     missing=colander.drop,
    #     widget=kecamatan_widget,
    #     slave="desa_id",
    #     slave_url="/desa/select/act?kecamatan_id=",
    #     title="Kecamatan",
    #     oid="kecamatan_id")
    # desa_id = colander.SchemaNode(
    #     colander.Integer(),
    #     widget=desa_widget,
    #     missing=colander.drop,
    #     title="Desa/Kelurahan",
    #     oid="desa_id")

    phone = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        missing=colander.drop,
        oid="phone")
    fax = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        missing=colander.drop,
        oid="fax")
    mobile = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        oid="mobile")
    website = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=128),
        missing=colander.drop,
        oid="website")
    idcard = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(mem_tmp_store),
        missing=colander.drop,
        title="ID Card"
    )
    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        oid="status")

    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
    #     prefix = request.route_url("base-home")
    #     self["provinsi_id"].slave_url = f"{prefix}/dati2/select/act?provinsi_id="
    #     self["dati2_id"].slave_url = f"{prefix}/kecamatan/select/act?dati2_id="
    #     self["kecamatan_id"].slave_url = f"{prefix}/desa/select/act?kecamatan_id="
