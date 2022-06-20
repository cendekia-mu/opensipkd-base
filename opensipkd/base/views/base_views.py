import os
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from opensipkd.tools.captcha import get_captcha
from pyramid.httpexceptions import HTTPFound

from .. import DBSession, get_params
from opensipkd.tools import dmy, dmy_to_date, get_settings, get_ext
import colander
from deform import (widget, Form, ValidationFailure, )
from email.utils import parseaddr

from opensipkd.tools.buttons import btn_save, btn_cancel, btn_close, btn_delete

from ..models import User


class BaseView(object):
    def __init__(self, request):
        if not "test" in request.session:
            request.session["test"]='TEST'
            print("********8 Session test not found")
        else:
            print("********9 Session", request.session["test"])

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

        self.ses['akhir'] = self.akhir
        self.ses['dt_akhir'] = self.dt_akhir

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
        self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
                            'btn_close'
        self.form_params = dict(scripts="")
        self.list_url = ''
        self.list_route = ''
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
        # self.captcha = ""

    def route_list(self, msg=None, error=""):
        if msg:
            self.ses.flash(msg, error)
        if self.headers:
            return HTTPFound(location=self.req.route_url(self.list_route), headers=self.headers)
        else:
            return HTTPFound(location=self.req.route_url(self.list_route))

    def form_validator(self, form, value):
        pass

    def get_params(self, params):
        return get_params(params)

    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel), **bindings):
        buttons = self.buttons and self.buttons or buttons
        bindings = self.bindings and self.bindings or bindings
        schema = class_form(validator=self.form_validator)  #
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
        arg = not arg and {} or arg
        arg.update(url=self.list_url, col_defs=self.list_col_defs,
                   cols=self.list_cols, buttons=self.list_buttons)
        return arg

    def view_view(self):  # row = query_id(request).first()
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()
        bindings = hasattr(self, "get_bindings") and self.get_bindings() or None
        form = self.get_form(self.edit_schema, buttons=(btn_close,), bindings=bindings)
        if request.POST:
            return self.route_list()

        form.set_appstruct(self.get_values(row))
        table = self.get_item_table(row)
        return dict(form=form.render(readonly=True), table=table and table.render() or None,
                    scripts=self.form_scripts)

    def before_add(self):
        return

    def validation_failure(self, value):
        return value

    def view_add(self):
        print("*************** view_add", self.ses)
        form = self.get_form(self.add_schema)
        if self.req.POST:
            print("*************** view_add_pos", self.ses)
            if 'save' in self.req.POST:
                controls = self.req.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    value = self.validation_failure(e.cstruct)
                    value.update(self.before_add())
                    print("*************** on error", self.ses)
                    form.render(appstruct=value)
                    return dict(form=form.render(), scripts=self.form_scripts)
                self.save_request(dict(controls))
            return self.route_list()
        values = self.before_add()
        print("*************** on view", self.ses)
        form.set_appstruct(values)
        table = self.get_item_table()
        return dict(form=form.render(), table=table and table.render() or None,
                    scripts=self.form_scripts)

    def before_save(self, row, values):
        return row

    def after_save(self, row, values):
        pass

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
        row = self.before_save(row, values)
        DBSession.add(row)
        DBSession.flush()
        self.after_save(row, values)
        return row

    def save_request(self, values, row=None):
        params = self.req.params
        for p in params:
            values[p] = params[p]

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
        form = self.get_form(self.edit_schema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(), scripts=self.form_scripts)

                self.save_request(dict(controls), row)
            return self.route_list()
        values = self.get_values(row)
        form.set_appstruct(values)
        form = self.before_edit(form)
        table = self.get_item_table(row)
        return dict(form=form.render(), table=table and table.render() or None, scripts=self.form_scripts)

    def view_delete(self):
        request = self.req
        q = self.query_id()
        row = q.first()
        if not row:
            return self.id_not_found()
        if request.POST:
            if 'delete' in request.POST:
                msg = f'Data ID {row.id} sudah dihapus.'
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        form = self.get_form(self.edit_schema, buttons=(btn_delete, btn_cancel))
        form.set_appstruct(self.get_values(row))
        table = self.get_item_table(row)
        return dict(form=form.render(), table=table and table.render() or None, scripts=self.form_scripts)

    def query_id(self):
        q = DBSession.query(self.table).filter_by(
            id=self.req.matchdict['id'])
        if hasattr(self.table, 'compnay_id') and self.req.user.company_id:
            q = q.filter_by(company_id=self.req.user.company_id)
        return q


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


store = Store()
reg_exts = ['.png', '.jpg', '.pdf', '.jpeg']


def image_validator(node, value):
    ext = get_ext(value["filename"])
    if ext not in reg_exts:
        raise colander.Invalid(node, f'Extension harus salahsatu dari {reg_exts}')


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
