import colander
from deform import (
    widget, Button,
)
from pyramid.i18n import TranslationStringFactory
from pyramid.view import (
    view_config,
)

from opensipkd.base import get_id_card_folder
from opensipkd.models import DBSession, Partner
from opensipkd.models import (
    ResProvinsi, ResDati2, ResKecamatan, ResDesa)
from opensipkd.models.common import ResCompany
from opensipkd.tools import Upload, img_exts
from .company import company_widget
from .partner_base import PartnerSchema
# from .. import partner_idcard_url
from ..views import BaseView

_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah partner gagal'
SESS_EDIT_FAILED = 'Edit partner gagal'


class AddSchema(PartnerSchema):
    is_vendor = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        oid="is_vendor",
        title="Vendor")
    is_customer = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        oid="is_customer",
        title="Customer")
    company_id = colander.SchemaNode(
        colander.Integer(),
        widget=company_widget,
        missing=colander.drop,
        oid="company_id",
        title="Company")

    def after_bind(self, schema, kwargs):
        super().after_bind(schema, kwargs)
        request = kwargs["request"]
        if request.user.company_id:
            self["company_id"].widget = widget.HiddenWidget()
            self["company_id"].default = request.user.company_id


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )

    def after_bind(self, schema, kwargs):
        super().after_bind(schema, kwargs)


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(),
                             title=_("action", default="Action"))
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

    email = colander.SchemaNode(
        colander.String(),
        oid="email")
    idcard = colander.SchemaNode(
        colander.String(),
        oid="idcard",
        title="Identitas"
    )
    status = colander.SchemaNode(
        colander.Boolean(),
        widget=widget.CheckboxWidget(),
        oid="status")

    def after_bind(self, schema, kw):
        request = kw.get("request")
        self["idcard"].url = request.static_url(get_id_card_folder("/"))


class ViewPartner(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'partner'
        self.list_route = 'partner'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Partner
        self.list_schema = ListSchema

    ########
    # List #
    ########
    @view_config(route_name='partner', renderer='templates/table.pt',
                 permission='user-view')
    def view_list(self):
        new_buttons = {"kta":
                           {"obj": "kta",
                            "js": """if (m{tableid}ID!=null)  
                                     window.location=o{tableid}Uri+'/'+m{tableid}ID+'/kta?{params}';
                                     else displayEmptyID();
                                     """
                            },
                       "ktp":
                           {"obj": Button("ktp", title=_('KTP'), css_class="btn-danger"),
                            "js": """if (m{tableid}ID!=null)  
                                             window.location=o{tableid}Uri+'/'+m{tableid}ID+'/ktp?{params}';
                                             else displayEmptyID();
                                             """
                            }
                       }
        return super().view_list(new_buttons=new_buttons)

    @view_config(route_name='partner-act', renderer='json',
                 permission='user-view')
    def view_act(self):
        return super().view_act()

    def next_act(self):
        request = self.req
        params = request.params
        url_dict = request.matchdict
        if url_dict['act'] == 'hok':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.kode.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(Partner.is_vendor == 1). \
                order_by(Partner.nama)
            keys = q.first().keys()
            r = []
            for k in q.all():
                d = dict(zip(keys, k))
                r.append(d)
            return r

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                order_by(Partner.nama)
            row = q.first()
            if not row:
                return []

            keys = row.keys()
            r = [dict(zip(keys, k)) for k in q.all()]
            return r

        elif url_dict['act'] == 'vendor':  # vendor only
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(Partner.is_vendor == 1). \
                order_by(Partner.nama)
            keys = q.first().keys()
            r = []
            for k in q.all():
                d = dict(zip(keys, k))
                r.append(d)
            return r

        elif url_dict['act'] == 'customer':  # customer only
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(Partner.is_customer == 1). \
                order_by(Partner.nama)
            keys = q.first().keys()
            r = []
            for k in q.all():
                d = dict(zip(keys, k))
                r.append(d)
            return r

    @view_config(route_name='partner-add', renderer='templates/form.pt',
                 permission='user-edit')
    def view_add(self):
        return super().view_add()

    @view_config(route_name='partner-edit', renderer='templates/form.pt',
                 permission='user-edit')
    def view_edt(self):
        return super().view_edit()

    @view_config(route_name='partner-view', renderer='templates/form.pt',
                 permission='user-edit')
    def view_view(self):
        return super().view_view()

    @view_config(route_name='partner-delete', renderer='templates/form.pt',
                 permission='user-edit')
    def view_delete(self):
        return super().view_delete()

    def form_validator(self, form, value):
        def err_kode():
            raise colander.Invalid(form,
                                   'Kode %s sudah digunakan oleh %s' % (
                                       value['kode'], found.nama))

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Partner).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = Partner.query_kode(value['kode'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        value['is_vendor'] = 'is_vendor' in value and \
                             value['is_vendor'] and 1 or 0
        value['is_customer'] = 'is_customer' in value and \
                               value['is_customer'] and 1 or 0
        value["status"] = 'status' in value and value['status'] and 1 or 0

    def get_bindings(self, row=None):
        provinsi_list = ResProvinsi.get_list()
        dati2_list = row and row.provinsi_id and ResDati2.get_list(
            row.provinsi_id) or []
        kecamatan_list = row and row.dati2_id and ResKecamatan.get_list(
            row.dati2_id) or []
        desa_list = row and row.kecamatan_id and ResDesa.get_list(
            row.kecamatan_id) or []
        return dict(
            provinsi_list=provinsi_list,
            dati2_list=dati2_list,
            kecamatan_list=kecamatan_list,
            desa_list=desa_list,
            company_list=ResCompany.get_list()
        )

    def save_request(self, values, row=None):
        if "idcard" in values and values["idcard"]:
            if str(self.req.POST['upload'].decode('utf-8')) != "":
                folder = self.get_params("idcard_folder", '/tmp/idcard')
                upload = Upload(folder)
                file_name = upload.save(self.req, 'upload', img_exts)
                values["idcard"] = file_name
            else:
                del values["idcard"]

        row = super().save_request(values, row)
        return row

    def get_values(self, row, istime=False):
        d = super().get_values(row, istime)
        if "idcard" in d and d["idcard"]:
            filename = d["idcard"]
            url = self.req.static_url(get_id_card_folder("/"))
            preview_url = "/".join(
                [url, filename])
            d["idcard"] = {"uid": filename.split(".")[0],
                           "filename": filename,
                           "preview_url": preview_url
                           }
        return d


@colander.deferred
def partner_widget(node, kw):
    values = kw.get('partner_list', [])
    return widget.Select2Widget(values=values)
