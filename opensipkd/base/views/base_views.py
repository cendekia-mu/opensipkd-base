import logging
import os
import re
from datetime import datetime

from datatables import ColumnDT
from dateutil.relativedelta import relativedelta
from opensipkd.pbb.eta import nik_url

from opensipkd.tools.api import JsonRpcInvalidLoginError
from opensipkd.tools.form_api import formfield2dict
from pyramid.security import remember

from opensipkd.tools.captcha import get_captcha
from pyramid.httpexceptions import HTTPFound

from .common import DataTables
from .. import DBSession, get_params
from opensipkd.tools import dmy, dmy_to_date, get_settings, get_ext, \
    date_from_str
import colander
from deform import (widget, Form, ValidationFailure, Button, )
from email.utils import parseaddr

from opensipkd.tools.buttons import btn_save, btn_cancel, btn_close, btn_delete, \
    btn_view, btn_add, btn_edit, btn_csv, \
    btn_pdf

from opensipkd.models import User, Menus
from ..tools.api import auth_from_rpc
from ...detable import DeTable

log = logging.getLogger(__name__)


class BaseView(object):
    def __init__(self, request):
        self.req = request
        self.ses = self.req.session
        self.params = self.req.params
        self.settings = get_settings()
        now = datetime.now()
        self.tahun = 'tahun' in self.ses and self.ses['tahun'] or now.strftime(
            '%Y')
        self.tahun = 'tahun' in self.params and self.params[
            'tahun'] or self.tahun
        self.ses['tahun'] = self.tahun

        self.bulan = 'bulan' in self.ses and self.ses['bulan'] or now.strftime(
            '%m')

        if 'bulan' in self.params and self.params['bulan']:
            self.bulan = self.params['bulan'].strip().zfill(2)
            dt_awal = dmy_to_date(
                '{d}-{m}-{y}'.format(y=self.tahun, m=self.bulan, d='01'))
            dt_akhir = dt_awal + relativedelta(months=1) - relativedelta(days=1)

            self.ses['awal'] = dmy(dt_awal)
            self.ses['akhir'] = dmy(dt_akhir)

        self.ses['bulan'] = int(self.bulan)

        self.posted = 'posted' in self.ses and self.ses['posted'] or 0
        if 'posted' in self.params and self.params['posted']:
            posted = self.params['posted']
            self.posted = ((posted == 'true' or posted == '1') and 1) or (
                    (posted == 'false' or posted == '0') and 0) or 0
        self.ses['posted'] = self.posted

        self.awal = 'awal' in self.ses and self.ses['awal'] or dmy(now)
        awal = 'awal' in self.params and self.params['awal'] or self.awal
        try:
            self.dt_awal = dmy_to_date(awal)
            self.awal = awal
        except:
            self.dt_awal = dmy_to_date(self.awal)

        self.ses['awal'] = self.awal
        self.ses['dt_awal'] = self.dt_awal

        self.akhir = 'akhir' in self.ses and self.ses['akhir'] or dmy(now)
        akhir = 'akhir' in self.params and self.params['akhir'] or self.akhir

        try:
            self.dt_akhir = dmy_to_date(akhir)
            self.akhir = akhir
        except:
            self.dt_akhir = dmy_to_date(self.akhir)

        self.tahun_awal = 'tahun_awal' in self.ses and self.ses[
            'tahun_awal'] or self.tahun
        self.tahun_awal = 'tahun_awal' in self.params and self.params[
            'tahun_awal'] or self.tahun_awal
        self.ses['tahun_awal'] = self.tahun_awal

        self.tahun_akhir = 'tahun_akhir' in self.ses and self.ses[
            'tahun_akhir'] or self.tahun_awal
        self.tahun_akhir = 'tahun_akhir' in self.params and self.params[
            'tahun_akhir'] or self.tahun_akhir
        self.ses['tahun_akhir'] = self.tahun_akhir

        self.departemen_kd = 'departemen_kd' in self.ses and self.ses[
            'departemen_kd'] or '0.0.00'
        self.departemen_nm = 'departemen_nm' in self.ses and self.ses[
            'departemen_nm'] or 'PILIH UNIT'
        self.departemen_id = 'departemen_id' in self.ses and self.ses[
            'departemen_id'] or 0
        self.ses['departemen_kd'] = self.departemen_kd
        self.ses['departemen_nm'] = self.departemen_nm
        self.ses['departemen_id'] = self.departemen_id

        self.jenis = 'jenis' in self.ses and self.ses['jenis'] or 0
        self.jenis = 'jenis' in self.params and self.params[
            'jenis'] or self.jenis
        self.ses['jenis'] = self.jenis
        self.list_route = 'home'
        self.list_col_defs = ""
        self.list_cols = ""
        # self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
        #                     'btn_close'
        self.list_report = (btn_csv, btn_pdf)
        self.list_buttons = (btn_view, btn_add, btn_edit, btn_delete, btn_close)
        self.form_params = dict(scripts="")
        self.list_url = ''
        self.list_route = ''
        self.list_schema = ""
        self.form_scripts = """
         $('#parent_nm').bind('typeahead:selected', function(obj, datum) {
              $('#parent_id').val(datum.id);
              $('#parent_kd').val(datum.kode);

        });"""
        self.edit_schema = ""
        self.add_schema = ""
        self.table = ""
        self.home = self.req.route_url('home')[:-1]
        self.buttons = None
        self.headers = None
        self.bindings = {}
        self.autocomplete = 'on'
        self.action_suffix = "/grid/act"

    def delete_msg(self, row):
        return f'Data ID {row.id} sudah dihapus.'

    def route_list(self, msg=None, error=""):
        if msg:
            self.ses.flash(msg, error)
        if self.headers:
            return HTTPFound(location=self.req.route_url(self.list_route),
                             headers=self.headers)
        else:
            return HTTPFound(location=self.req.route_url(self.list_route))

    def form_validator(self, form, value):
        pass

    def get_params(self, params, default=None):
        return get_params(params, default)

    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel),
                 **kwargs):
        buttons = self.buttons and self.buttons or buttons
        if "bindings" in kwargs and kwargs["bindings"]:
            bindings = kwargs["bindings"]
        else:
            bindings = self.bindings

        if "validator" in kwargs and kwargs["validator"]:
            schema = class_form(validator=kwargs["validator"])
        else:
            schema = class_form(validator=self.form_validator)

        schema = schema.bind(request=self.req, **bindings)
        schema.request = self.req
        if row:
            schema.deserialize(row)
        return Form(schema, buttons=buttons, autocomplete=self.autocomplete)

    def session_failed(self, session_name):
        r = dict(form=self.req.session[session_name])
        del self.req.session[session_name]
        return r

    def view_list(self, arg=None):
        if self.list_schema:
            table = DeTable(self.list_schema(),
                            action=self.req.route_url(self.list_route),
                            action_suffix="/grid/act",
                            buttons=self.list_buttons)
            resources = table.get_widget_resources()
            # resources=dict(css="", js="")
            return dict(form=table.render(), scripts="", css=resources["css"],
                        js=resources["js"])

        arg = arg and arg or {}
        arg.update(url=self.list_url, col_defs=self.list_col_defs,
                   cols=self.list_cols, buttons=self.list_buttons)
        return arg

    def get_bindings(self, row=None):
        return {}

    def view_view(self):  # row = query_id(request).first()
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()
        bindings = self.get_bindings(row)
        form = self.get_form(self.edit_schema, buttons=(btn_close,),
                             bindings=bindings)
        if request.POST:
            return self.route_list()

        form.set_appstruct(self.get_values(row))
        table = self.get_item_table(row)
        return dict(form=form.render(readonly=True),
                    table=table and table.render() or None,
                    scripts=self.form_scripts)

    def before_add(self):
        return {}

    def validation_failure(self, value):
        return value

    def cancel_act(self):
        pass

    def after_add(self, row, values):
        return

    def next_act(self):
        raise NotImplementedError

    def list_join(self, query):
        return query

    def list_filter(self, query):
        return query

    def view_act(self, **kwargs):
        url_dict = self.req.matchdict
        if url_dict['act'] == 'grid':
            url=[]
            columns = []
            for d in self.list_schema():
                global_search = hasattr(d, "searchable") and \
                                hasattr(d, "searchable") == False and False \
                                or True
                if hasattr(d, "field"):
                    if type(d.field) == str:
                        columns.append(
                            ColumnDT(getattr(self.table, d.field), mData=d.name,
                                     global_search=global_search))
                    else:
                        columns.append(ColumnDT(d.field, mData=d.name))
                else:
                    columns.append(
                        ColumnDT(getattr(self.table, d.name), mData=d.name))
                if hasattr(d, "url"):
                    url.append(d.name)
            query = DBSession.query().select_from(self.table)
            query = self.list_join(query)
            if self.req.user and self.req.user.company_id and hasattr(
                    self.table, "company_id"):
                query = query.filter(
                    self.table.company_id == self.req.user.company_id)
            query=self.list_filter(query)
            row_table = DataTables(self.req.GET, query, columns)
            result = row_table.output_result()
            for d in result["data"]:
                for k, v in d.items():
                    if k in url and v:
                        link = "/".join([self.home, nik_url, v])
                        d[k] =f'<a href="{link}" target="_blank">View</a>'
            return result
        else:
            return self.next_act()

    def view_add(self):
        bindings = self.get_bindings()
        form = self.get_form(self.add_schema, bindings=bindings)
        table = self.get_item_table()
        resources = form.get_widget_resources()
        if self.req.POST:
            if 'save' in self.req.POST:
                controls = self.req.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    # value = self.validation_failure(e.cstruct)
                    # value.update(self.before_add())
                    # form.render(appstruct=value)
                    return dict(form=form.render(e.cstruct),
                                table=table and table.render() or None,
                                scripts=self.form_scripts, css=resources["css"],
                                js=resources["js"])
                values = dict(controls)
                row = self.save_request(values)
                self.after_add(row, values)
            elif "cancel" in self.req.POST or 'batal' in self.req.POST:
                self.cancel_act()
            else:
                return self.next_add(form, table=table, resources=resources)

            return self.route_list()
        values = self.before_add()
        form.set_appstruct(values)
        return dict(form=form.render(), table=table and table.render() or None,
                    scripts=self.form_scripts, css=resources["css"],
                    js=resources["js"])

    def save(self, values, user, row=None):
        self.ses["old_email"] = user and user.email or None
        if not row:
            row = self.table()
            row.created = datetime.now()
            row.create_uid = user and user.id or None
        else:
            row.updated = datetime.now()
            row.update_uid = user and user.id or None

        row.from_dict(values)
        row.status = 'status' in values and values['status'] and 1 or 0
        DBSession.add(row)
        DBSession.flush()
        return row

    def save_request(self, values, row=None):
        for k, v in self.req.GET.items():
            if k not in values:
                if v:
                    values[k] = v
        return self.save(values, self.req.user, row)

    def id_not_found(self):
        msg = f"Data yang dicari Tidak Ditemukan ID:" \
              f" {self.req.matchdict['id']}."
        self.req.session.flash(msg, 'error')
        return self.route_list()

    def get_values(self, row, istime=False):
        d = row.to_dict()
        # if 'tanggal' in d and d['tanggal']:
        #     d["tanggal"] = dmy(row.tanggal)
        for f in d:
            if type(d[f]) is str:
                d[f] = d[f].strip()
        return d

    def get_item_table(self, row=None):
        return

    def before_edit(self, form):
        return form

    def view_edit(self):
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()
        if not self.bindings:
            self.bindings = self.get_bindings(row)
        form = self.get_form(self.edit_schema)
        table = self.get_item_table(row)
        resources = form.get_widget_resources()
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(),
                                table=table and table.render() or None,
                                scripts=self.form_scripts, css=resources["css"],
                                js=resources["js"])
                c = dict(controls)
                self.save_request(c, row)
            return self.route_list()
        values = self.get_values(row)
        form.set_appstruct(values)
        form = self.before_edit(form)
        return dict(form=form.render(), table=table and table.render() or None,
                    scripts=self.form_scripts, css=resources["css"],
                    js=resources["js"])

    def before_delete(self, row):
        pass

    def view_delete(self):
        request = self.req
        q = self.query_id()
        row = q.first()
        if not row:
            return self.id_not_found()
        if not self.bindings:
            self.bindings = self.get_bindings(row)
        if request.POST:
            if 'delete' in request.POST:
                msg = self.delete_msg(row)
                self.before_delete(row)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        form = self.get_form(self.edit_schema, buttons=(btn_delete, btn_cancel))
        table = self.get_item_table(row)
        resources = form.get_widget_resources()
        form.set_appstruct(self.get_values(row))
        return dict(form=form.render(readonly=True),
                    table=table and table.render() or None,
                    scripts=self.form_scripts, css=resources["css"],
                    js=resources["js"])

    def query_id(self):
        q = DBSession.query(self.table).filter_by(
            id=self.req.matchdict['id'])
        if hasattr(self.table, 'compnay_id') and self.req.user.company_id:
            q = q.filter_by(company_id=self.req.user.company_id)
        return q

    def filter_company(self, query):
        if self.req.user.company_id:
            return query.filter(
                self.table.company_id == self.req.user.company_id)
        return query

    def next_add(self, form):
        """
        Digunakan untuk memverifikasi button yang lainnya
        :param form:  Object Form
        :return:
        """
        return self.route_list()


@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)


def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')


class Store(dict):
    def preview_url(self, name):
        return ""


username_re = re.compile('^[a-z0-9_]{6,16}$', re.IGNORECASE)


def user_name_validator(node, value):
    if not username_re.match(value):
        raise colander.Invalid(node,
                               'Value must be between 6 and 16 characters and can only contain uppercase and lowercase alphanumeric characters or an underscore')


def need_captcha():
    is_captcha = get_params("reg_captcha")
    return is_captcha == '1' or is_captcha == "True" or is_captcha == "true" or is_captcha == True


def need_verify():
    result = get_params("reg_verify")
    return result == '1' or result == "True" or result == "true" or result == True


def get_url_captcha(request):
    captcha = get_captcha(request)
    return os.path.join(request.route_url('home'), 'captcha', captcha)
