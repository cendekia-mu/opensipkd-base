import os
import re

import colander
from deform import (widget, )
from opensipkd.tools import create_now
from opensipkd.tools.report import open_rml_row, csv_response, open_rml_pdf, pdf_response
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from sqlalchemy import (func, )
from ziggurat_foundations.models.services.user import UserService

from . import BaseView
from .company import company_widget
from .user_login import (
    regenerate_security_code, send_email_security_code, generate_api_key, )
from ..models import (DBSession, User, Group, UserGroup, ResCompany, )

_ = TranslationStringFactory('user')


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), title="ID", visible=False, searchable=False)
    email = colander.SchemaNode(colander.String())
    user_name = colander.SchemaNode(colander.String())
    status = colander.SchemaNode(colander.Integer(), width=50, searchable=False)
    last_login = colander.SchemaNode(colander.String(), width=100, field="last_login_date", searchable=False)
    registered = colander.SchemaNode(colander.String(), width=100, field="registered_date", searchable=False)


class Views(BaseView):
    def __init__(self, request):
        super(Views, self).__init__(request)
        self.list_schema = ListSchema
        self.list_route = 'user'
        self.table = User
        self.edit_schema = EditSchema
        self.add_schema = AddSchema
        self.list_buttons = self.list_buttons + self.list_report

    def get_bindings(self, row=None):
        status_list = (
            ('1', _('Active')),
            ('0', _('Archived')))
        if row and row.api_key:
            api_key_list = (
                ('', _(row.api_key)),
                ('0', _('Hapus')))
        else:
            api_key_list = (
                ('', _('Tidak ada')),
                ('1', _('Buatkan')))
        group_list = get_group_list()
        return dict(status_list=status_list,
                    group_list=group_list,
                    api_key_list=api_key_list,
                    user=row,
                    company_list=ResCompany.get_list())

    @view_config(
        route_name='user', renderer='templates/table.pt',
        permission='user-view')
    def view_list(self):
        return super(Views, self).view_list()

    @view_config(
        route_name='user-act', renderer='json', permission='user-view')
    def view_act(self):
        return super(Views, self).view_act()

    def next_act(self):
        url_dict = self.req.matchdict
        if url_dict['act'] == 'csv':
            query = query_register()
            row = query.first()
            header = row.keys()
            rows = [list(item) for item in query.all()]
            filename = 'user.csv'
            value = {
                'header': header,
                'rows': rows,
            }
            return csv_response(self.req, value, filename)

        elif url_dict['act'] == 'pdf':
            query = query_register()
            import opensipkd.base
            base_path = os.path.dirname(opensipkd.base.__file__)
            path = os.path.join(base_path, 'reports')
            rml_row = open_rml_row(path + '/user.row.rml')
            rows = [rml_row.format(user_name=r.user_name, email=r.email,
                                   registered_date=r.registered_date) for r in query.all()]
            pdf, filename = open_rml_pdf(path + '/user.rml', rows=rows,
                                         company=self.req.company,
                                         departement=self.req.departement,
                                         address=self.req.address,
                                         base_path=base_path)
            return pdf_response(self.req, pdf, filename)


    def form_validator(self, form, value):
        if "company_id" in value and not value["company_id"]:
            value["company_id"] = None


    def save_request(self, values, row=None):
        request = self.req
        values["email"] = values['email'].lower()
        values["user_name"] = re.sub(' ', '', values['user_name'])  # .lower()
        values["security_code_date"] = create_now()
        company_id = request.user and request.user.company_id or "company_id" in values and values["company_id"] or None
        values["company_id"] = company_id
        if 'is_api_key' in values:
            values["api_key"] = generate_api_key()
        insert = not row
        row = self.save(values, self.req.user, row)
        if insert:
            remain = regenerate_security_code(row)
            if 'password' in values:
                data = dict(username=row.user_name)
                ts = _(
                    'user-added-with-password',
                    default='${username} berhasil ditambahkan.', mapping=data)
            else:
                send_email_security_code(
                    self.req, row, remain, 'Welcome new user', 'email-new-user',
                    'email-new-user.tpl')
                data = dict(email=row.email)
                ts = _(
                    'user-added',
                    default='${email} berhasil ditambahkan dan email untuk ubah ' \
                            'kata kunci sudah dikirim.',
                    mapping=data)
            self.ses.flash(ts)

        if 'password' in values:
            UserService.set_password(row, values['password'])

        DBSession.add(row)
        DBSession.flush()

        existing = user_group_set(row)
        unused = existing - values['groups']
        if unused:
            q = DBSession.query(UserGroup).filter_by(user_id=row.id).filter(
                UserGroup.group_id.in_(unused))
            q.delete(synchronize_session=False)
            for gid in unused:
                reduce_member_count(gid)
        new = values['groups'] - existing
        for gid in new:
            ug = UserGroup()
            ug.user_id = row.id
            ug.group_id = gid
            DBSession.add(ug)
            add_member_count(gid)
        return row


    def after_add(self, row, values):
        pass


    @view_config(
        route_name='user-add', renderer='templates/form.pt',
        permission='user-view')
    def view_add(self):
        return super(Views, self).view_add()
        # user, remain = insert(request, values)


    def get_values(self, row, istime=False):
        d = super(Views, self).get_values(row, istime)
        d["groups"] = user_group_set(row)
        return d


    @view_config(
        route_name='user-edit', renderer='templates/user/edit.pt',
        permission='user-edit')
    def view_edit(self):
        return super(Views, self).view_edit()
        # q = DBSession.query(User).filter_by(id=request.matchdict['id'])
        # if request.user.company_id:
        #     q = q.filter_by(company_id=request.user.company_id)
        # user = q.first()
        # if not user:
        #     return HTTPNotFound()
        # if user.id == request.user.id:
        #     form = get_form(request, AddSchema, user)
        # else:
        # if 'opensipkd.webr.models' in get_modules():
        #     form = get_form(request, EditSchema2, user)
        # else:
        # form = get_form(request, EditSchema, user)

        # resp = dict(title=_('Edit user'))
        # if not request.POST:
        #     d = user.to_dict()
        #     d['groups'] = user_group_set(user)
        #     resp['form'] = form.render(appstruct=d)
        #     return resp
        # if 'save' not in request.POST:
        #     return HTTPFound(location=request.route_url('user'))
        # items = request.POST.items()
        # try:
        #     c = form.validate(items)
        # except ValidationFailure:
        #     resp['form'] = form.render()
        #     return resp
        # update(request, user, dict(c.items()))
        # data = dict(username=user.user_name)
        # ts = _('user-updated', default='${username} profile updated', mapping=data)
        # request.session.flash(ts)
        # return HTTPFound(location=request.route_url('user'))


    @view_config(
        route_name='user-view', renderer='templates/form.pt',
        permission='user-view')
    def view_view(self):
        return super(Views, self).view_view()


    @view_config(
        route_name='user-delete', renderer='templates/form.pt',
        permission='user-edit')
    def view_delete(self):
        return super(Views, self).view_delete()


    def delete_msg(self, row):
        data = dict(uid=row.id, email=row.email)
        return _(
            'user-deleted',
            default='User ${email} ID ${uid} has been deleted',
            mapping=data)


    def before_delete(self, row):
        gid_list = user_group_set(row)
        for gid in gid_list:
            reduce_member_count(gid)


    def query_id(self):
        q = DBSession.query(User).filter_by(id=self.req.matchdict['id'])
        if self.req.user.company_id:
            q = q.filter_by(company_id=self.req.user.company_id)
        return q


#######
# Add #
#######
@colander.deferred
def status_widget(node, kw):
    values = kw.get('status_list', [])
    return widget.SelectWidget(values=values)


@colander.deferred
def group_widget(node, kw):
    values = kw.get('group_list', [])
    return widget.CheckboxChoiceWidget(values=values)


@colander.deferred
def api_key_widget(node, kw):
    values = kw.get('api_key_list', [])
    return widget.SelectWidget(values=values)


class Validator:
    def __init__(self, user):
        self.user = user


class EmailValidator(colander.Email, Validator):
    def __init__(self, user):
        colander.Email.__init__(self)
        Validator.__init__(self, user)

    def __call__(self, node, value):
        if self.match_object.match(value) is None:
            raise colander.Invalid(node, _('Invalid email format'))
        email = value.lower()
        if self.user and self.user.email == email:
            return
        q = DBSession.query(User).filter_by(email=email)
        found = q.first()
        if not found:
            return
        data = dict(email=email, uid=found.id)
        ts = _(
            'email-already-used',
            default='Email ${email} already used by user ID ${uid}',
            mapping=data)
        raise colander.Invalid(node, ts)


REGEX_ONLY_CONTAIN = re.compile('([A-Za-z0-9-]*)')
REGEX_BEGIN_END_ALPHANUMERIC = re.compile('^[A-Za-z0-9]+(?:[-][A-Za-z0-9]+)*$')


class UsernameValidator(Validator):
    def __call__(self, node, value):
        username = value
        if self.user and self.user.user_name == username:
            return
        match = REGEX_ONLY_CONTAIN.search(username)
        if not match or match.group(1) != username or username != value:
            ts = _(
                'username-only-contain',
                default='Only A-Z a-z, 0-9, and - characters are allowed')
            raise colander.Invalid(node, ts)
        match = REGEX_BEGIN_END_ALPHANUMERIC.search(username)
        if not match:
            ts = _(
                'username-first-end-alphanumeric',
                default='Only A-Z a-z or 0-9 at the start and end')
            raise colander.Invalid(node, ts)
        q = DBSession.query(User).filter_by(user_name=username)
        found = q.first()
        if not found:
            return

        data = dict(username=username, uid=found.id)
        ts = _(
            'username-already-used',
            default='Username ${username} already used by ID ${uid}',
            mapping=data)
        raise colander.Invalid(node, ts)


@colander.deferred
def email_validator(node, kw):
    return EmailValidator(kw['user'])


@colander.deferred
def username_validator(node, kw):
    return UsernameValidator(kw['user'])


def save_user(values, user, row=None):
    if not row:
        row = User()
        row.status = 0

    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    if 'password' in values and values['password']:
        UserService.set_password(row, values['password'])
    return row


class AddSchema(colander.Schema):
    email = colander.SchemaNode(
        colander.String(), title=_('Email'),
        validator=email_validator)
    user_name = colander.SchemaNode(colander.String(), title=_('Username'),
                                    validator=username_validator)
    groups = colander.SchemaNode(
        colander.Set(), widget=group_widget, title=_('Group'))
    is_api_key = colander.SchemaNode(
        colander.String(), widget=api_key_widget, title=_('API Key'),
        missing=colander.drop)
    password = colander.SchemaNode(
        colander.String(), widget=widget.CheckedPasswordWidget(),
        missing=colander.drop)
    company_id = colander.SchemaNode(
        colander.Integer(), widget=company_widget,
        title="Company",
        missing=colander.drop)


class EditSchema(AddSchema):
    status = colander.SchemaNode(
        colander.String(), widget=status_widget, title=_('Status'))


def get_group_list():
    r = []
    q = DBSession.query(Group).order_by(Group.group_name)
    for row in q:
        g = (str(row.id), _(row.description))
        r.append(g)
    return r


def add_member_count(gid):
    q = DBSession.query(Group).filter_by(id=gid)
    group = q.first()
    group.member_count += 1
    DBSession.add(group)


def reduce_member_count(gid):
    q = DBSession.query(Group).filter_by(id=gid)
    group = q.first()
    group.member_count -= 1
    DBSession.add(group)


def user_group_set(user):
    q = DBSession.query(UserGroup).filter_by(user_id=user.id)
    r = []
    for ug in q:
        r.append(str(ug.group_id))
    return set(r)


def query_register():
    return DBSession.query(User.user_name, User.email,
                           func.to_char(User.registered_date, "DD-MM-YYYY").label("registered_date")).order_by(
        User.user_name)
