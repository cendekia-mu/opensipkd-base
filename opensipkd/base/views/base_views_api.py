from datetime import datetime

from deform import ValidationFailure, Form, Button
from opensipkd.models import flush, DBSession, Menus
from pyramid_rpc.jsonrpc import JsonRpcError
from opensipkd.tools.form_api import formfield2dict


class BaseApi(object):
    def __init__(self, request):
        self.request = request
        self.url = request.home + '/rpc/pbb/eta'
        self.add_schema = {}
        self.buttons = ()
        self.data = {}
        
    def make_response(self, data, **kwargs):
        resp = {"data": data}
        code = kwargs.get("code")
        message = kwargs.get("message")
        if code: resp.update({"code":code})
        if message: resp.update({"message":message})
        return resp

    def get_form(self, class_form, row=None, **kwargs):
        bindings = kwargs.get("bindings")
        validator = kwargs.get("validator")
        self.buttons = kwargs.get("buttons", self.buttons)
        if "url" in kwargs:
            url = kwargs.get("url", "")
        else:
            url = self.url
        if validator:
            schema = class_form(validator=validator)
        else:
            schema = class_form()  # validator=validator
        if bindings:
            schema = schema.bind(request=self.request, **bindings)
        else:
            schema = schema.bind(request=self.request)

        if row:
            schema.deserialize(row)

        return Form(schema, url=url, buttons=self.buttons)

    def validate_field(self, form):
        resp = {}
        controls = ((k, v) for k, v in self.data.items())
        try:
            c = form.validate(controls)
        except ValidationFailure as e:
            form.set_appstruct(e.cstruct)
            resp.update(formfield2dict(form))
            message = "\n".join([v for k, v in e.error.asdict().items()])
            raise JsonRpcError(message=message, data=resp)
        return dict(c)

    def get_menu_buttons(self, kode):
        qry = Menus.get(kode).order_by(Menus.order_id)
        if self.request.user:
            qry = qry.filter_by(need_login=1)
        else:
            qry = qry.filter(Menus.need_login!=1)

        buttons = []
        for row in qry.all():
            if not self.request.user:
                if row.need_login:
                    continue
            if row.permissions:
                if not self.request.user or not self.request.has_permission(
                        row.permissions):
                    continue

            buttons.append(Button(row.kode, title=row.nama, type="button",
                                  value=row.url, icon=row.icon, attributes=dict(method=row.url)))
        return tuple(buttons)

    def update_headers(self, headers):
        self.request.headers.update(headers)
        self.request.response.headers.update(headers)

    def _view_add(self, **kwargs):
        form = self.get_form(self.add_schema, **kwargs)
        self.action = self.data.get("action","")
        if 'save' == self.action:
            values = self.validate_field(form)
            row = self.save_request(values)
        elif "cancel" == self.action or 'batal' == self.action:
            self.cancel_act()
        else:
            return self.next_add(form)

        return self.route_list()
        values = self.before_add()
        form.set_appstruct(values)
        return form

    def view_add_api(self, **kwargs):
        form = self._view_add(**kwargs)
        resp = formfield2dict(form)
        return dict(data=resp)

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
        flush(row)
        return row

    def save_request(self, values, row=None):
        for k, v in self.request.GET.items():
            if k not in values:
                if v:
                    values[k] = v
        return self.save(values, self.request.user, row)

    def id_not_found(self):
        msg = f"Data yang dicari Tidak Ditemukan ID:" \
              f" {self.request.matchdict['id']}."
        self.request.session.flash(msg, 'error')
        return self.route_list()

    def next_add(self, form):
        """
        Digunakan untuk memverifikasi button yang lainnya
        :param form:  Object Form
        :return:
        """
        return self.route_list()

    def query_id(self):
        q = DBSession.query(self.table).filter_by(
            id=self.req.matchdict['id'])
        if hasattr(self.table, 'company_id') and self.req.user.company_id:
            q = q.filter_by(company_id=self.req.user.company_id)
        return q

    def route_list(self, msg=None, error=""):
        if msg:
            self.ses.flash(msg, error)
        if self.headers:
            return HTTPFound(location=self.req.route_url(self.list_route),
                             headers=self.headers)
        else:
            return HTTPFound(location=self.req.route_url(self.list_route))

    def before_add(self):
        return {}