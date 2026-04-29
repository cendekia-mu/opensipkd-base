import logging
import re
import colander
from deform import (widget,)
from pyramid.i18n import TranslationStringFactory
from ..models import TextPrinters

from . import BaseView, NamaSchema


log = logging.getLogger(__name__)
_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah partner gagal'
SESS_EDIT_FAILED = 'Edit partner gagal'


class AddSchema(NamaSchema):
    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        title="Status")

    def after_bind(self, schema, kw):
        schema["kode"].title = "IP Address"
        schema["kode"].widget = widget.TextInputWidget(
            mask="999.999.999.999",  # Use specialized mask format
            # If required
            mask_mapping={'Z': {'pattern': '[0-9]', 'optional': True}},
            # css_class='ip_address'
        )
        # schema["kode"].validator = colander.Regex(
        #     r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
        # )


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class ListSchema(EditSchema):
    pass


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_route = 'base-printer'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = TextPrinters
        self.list_schema = ListSchema
        # self.list_buttons = (btn_delete,)
        self.save_state = True
        self.allow_check = True
        self.list_view_field = 'nama'

    def list_filter(self, query, **kwargs):
        if not self.req.has_permission('admin'):
            query = query.filter_by(create_uid=self.req.user.id)
        return query
    

    def form_validator(self, form, value):
        exc = colander.Invalid(form, None)
        ip = value['kode'].split('.')
        err = []
        err_format = 'Format IP salah'
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value['kode']):
            err.append(err_format+' 123.123.123.123')
        if len(ip) != 4:
            err.append(err_format+' harus 4 oktet')
        for i in ip:
            if not i.isdigit():
                err.append(err_format)
            if int(i) < 0 or int(i) > 255:
                err.append(err_format+' setiap oktet harus antara 0-255')
            if ip[0] == '0':
                err.append(err_format+' tidak boleh diawali 0')
        if err:
            exc['kode'] = '\n'.join(err)
            raise exc
        
    def after_save(self, values, row):
        self.db_session.flush()
        if values['status'] == 1:
            printers  = TextPrinters.query().filter_by(create_uid=row.create_uid).all()
            for printer in printers:
                if printer.id == row.id:
                    continue
                printer.status = 0
                self.db_session.add(printer)
        self.db_session.flush()
        return row
