import colander
from deform import FileData, widget

from opensipkd.base.views.dati2 import dati2_widget
from opensipkd.base.views.desa import desa_widget
from opensipkd.base.views.kecamatan import kecamatan_widget
from opensipkd.base.views.provinsi import provinsi_widget

from opensipkd.tools import mem_tmp_store


class NamaSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode",
        title="Kode",
        width="100pt")
    nama = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="nama")


class PartnerSchema(NamaSchema):
    nip = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=32),
        oid="nip")
    npwp = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=32),
        oid="npwp")

    idcard = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(mem_tmp_store),
        missing=colander.drop,
        title="ID Card"
    )
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
    # kelurahan = colander.SchemaNode(
    #     colander.String(),
    #     missing=colander.drop,
    #     validator=colander.Length(max=64),
    #     oid="kelurahan")
    # kecamatan = colander.SchemaNode(
    #     colander.String(),
    #     missing=colander.drop,
    #     validator=colander.Length(max=64),
    #     oid="kecamatan")
    # kota = colander.SchemaNode(
    #     colander.String(),
    #     validator=colander.Length(max=64),
    #     missing=colander.drop,
    #     oid="kota")
    # provinsi = colander.SchemaNode(
    #     colander.String(),
    #     validator=colander.Length(max=64),
    #     missing=colander.drop,
    #     oid="provinsi")
    provinsi_id = colander.SchemaNode(
        colander.Integer(),
        widget=provinsi_widget,
        missing=colander.drop,
        oid="provinsi_id",
        slave="dati2_id",
        slave_url="/dati2/select/act?provinsi_id=",
        title="Provinsi",

    )
    dati2_id = colander.SchemaNode(
        colander.Integer(),
        widget=dati2_widget,
        missing=colander.drop,
        slave="kecamatan_id",
        slave_url="/kecamatan/select/act?dati2_id=",
        title="Kab/Kota",
        oid="dati2_id")
    kecamatan_id = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        widget=kecamatan_widget,
        slave="desa_id",
        slave_url="/desa/select/act?kecamatan_id=",
        title="Kecamatan",
        oid="kecamatan_id")
    desa_id = colander.SchemaNode(
        colander.Integer(),
        widget=desa_widget,
        missing=colander.drop,
        title="Desa/Kelurahan",
        oid="desa_id")
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=128),
        oid="email")
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
        missing=colander.drop,
        oid="mobile")
    website = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=128),
        missing=colander.drop,
        oid="website")
    status = colander.SchemaNode(
        colander.Boolean(),
        oid="status")

    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        prefix = request.route_url("home")
        self["provinsi_id"].slave_url=f"{prefix}/dati2/select/act?provinsi_id="
        self["dati2_id"].slave_url=f"{prefix}/kecamatan/select/act?dati2_id="
        self["kecamatan_id"].slave_url = f"{prefix}/desa/select/act?kecamatan_id="

