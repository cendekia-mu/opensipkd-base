import os
import re

import colander
import transaction
from datatables import (ColumnDT, DataTables, )
from deform import (Form, widget, ValidationFailure, Button, )
from sqlalchemy.exc import IntegrityError

from opensipkd.tools import create_now
from opensipkd.tools.buttons import btn_cancel, btn_save, btn_close
from opensipkd.tools.report import open_rml_row, csv_response, open_rml_pdf, pdf_response
from pyramid.httpexceptions import (HTTPFound, HTTPNotFound, )
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from sqlalchemy import (func, or_, )
from ziggurat_foundations.models.services.user import UserService

from .company import company_widget
from .user_login import (
    regenerate_security_code, send_email_security_code, generate_api_key, )
from ..models import (DBSession, User, Group, UserGroup, ResCompany, )

_ = TranslationStringFactory('user')


########
# List #
########
@view_config(
    route_name='user', renderer='templates/user/list.pt',
    permission='user-view')
def view_list(request):
    return dict()


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
        username = value  # .lower()
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


def form_validator(form, value):
    # new_password = value.get('new_password')
    # retype_password = value.get('retype_password')
    # if new_password != retype_password:
    #     raise colander.Invalid(form, _('Pengulangan kata kunci tidak sama'))
    pass


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


def get_form(request, class_form, user=None, buttons=(btn_save, btn_cancel)):
    status_list = (
        ('1', _('Active')),
        ('0', _('Archived')))
    if user and user.api_key:
        api_key_list = (
            ('', _(user.api_key)),
            ('0', _('Hapus')))
    else:
        api_key_list = (
            ('', _('Tidak ada')),
            ('1', _('Buatkan')))
    schema = class_form(validator=form_validator)
    group_list = get_group_list()
    schema = schema.bind(
        status_list=status_list, group_list=group_list, user=user,
        api_key_list=api_key_list,
        company_list=ResCompany.get_list()
    )

    return Form(schema, buttons=buttons)


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


def insert(request, values):
    user = User()
    user.email = values['email'].lower()
    user.user_name = re.sub(' ', '', values['user_name'])  # .lower()
    user.security_code_date = create_now()
    company_id = request.user and request.user.company_id or "company_id" in values and values["company_id"] or None
    user.company_id = company_id
    remain = regenerate_security_code(user)
    if 'is_api_key' in values:
        user.api_key = generate_api_key()
    if 'password' in values:
        UserService.set_password(user, values['password'])
    DBSession.add(user)
    try:
        DBSession.flush()
    except IntegrityError as e:
        transaction.abort()
        user.user_name = user.email
        DBSession.add(user)
        DBSession.flush()

    if 'groups' in values and values['groups']:
        for gid in values['groups']:
            ug = UserGroup()
            ug.user_id = user.id
            ug.group_id = gid
            DBSession.add(ug)
            add_member_count(gid)
    return user, remain


@view_config(
    route_name='user-add', renderer='templates/user/add.pt',
    permission='user-view')
def view_add(request):
    # if 'opensipkd.webr.models' in get_modules():
    #     form = get_form(request, AddSchema2)
    # else:
    form = get_form(request, AddSchema)
    resp = dict(title=_('Add user'))
    if not request.POST:
        resp['form'] = form.render()
        return resp
    if 'save' not in request.POST:
        return HTTPFound(location=request.route_url('user'))
    items = request.POST.items()
    try:
        c = form.validate(items)
    except ValidationFailure:
        resp['form'] = form.render()
        return resp
    values = dict(c.items())
    user, remain = insert(request, values)
    if 'password' in values:
        data = dict(username=user.user_name)
        ts = _(
            'user-added-with-password',
            default='${username} berhasil ditambahkan.', mapping=data)
    else:
        send_email_security_code(
            request, user, remain, 'Welcome new user', 'email-new-user',
            'email-new-user.tpl')
        data = dict(email=user.email)
        ts = _(
            'user-added',
            default='${email} berhasil ditambahkan dan email untuk ubah ' \
                    'kata kunci sudah dikirim.',
            mapping=data)
    request.session.flash(ts)
    return HTTPFound(location=request.route_url('user'))


def user_group_set(user):
    q = DBSession.query(UserGroup).filter_by(user_id=user.id)
    r = []
    for ug in q:
        r.append(str(ug.group_id))
    return set(r)


def update(request, user, values):
    user.email = values['email'].lower()
    user.user_name = re.sub(' ', '', values['user_name'])  # .lower())
    if user.id != request.user.id:
        user.status = values['status']
    is_api_key = values.get('is_api_key')
    if is_api_key == '0':
        user.api_key = None
    elif is_api_key == '1':
        user.api_key = generate_api_key()
    if 'password' in values:
        UserService.set_password(user, values['password'])
    company_id = request.user.company_id or 'company_id' in values and values["company_id"] or None
    user.company_id = company_id
    DBSession.add(user)
    existing = user_group_set(user)
    unused = existing - values['groups']
    if unused:
        q = DBSession.query(UserGroup).filter_by(user_id=user.id).filter(
            UserGroup.group_id.in_(unused))
        q.delete(synchronize_session=False)
        for gid in unused:
            reduce_member_count(gid)
    new = values['groups'] - existing
    for gid in new:
        ug = UserGroup()
        ug.user_id = user.id
        ug.group_id = gid
        DBSession.add(ug)
        add_member_count(gid)


@view_config(
    route_name='user-edit', renderer='templates/user/edit.pt',
    permission='user-edit')
def view_edit(request):
    q = DBSession.query(User).filter_by(id=request.matchdict['id'])
    if request.user.company_id:
        q = q.filter_by(company_id=request.user.company_id)
    user = q.first()
    if not user:
        return HTTPNotFound()
    if user.id == request.user.id:
        form = get_form(request, AddSchema, user)
    else:
        # if 'opensipkd.webr.models' in get_modules():
        #     form = get_form(request, EditSchema2, user)
        # else:
        form = get_form(request, EditSchema, user)

    resp = dict(title=_('Edit user'))
    if not request.POST:
        d = user.to_dict()
        d['groups'] = user_group_set(user)
        resp['form'] = form.render(appstruct=d)
        return resp
    if 'save' not in request.POST:
        return HTTPFound(location=request.route_url('user'))
    items = request.POST.items()
    try:
        c = form.validate(items)
    except ValidationFailure:
        resp['form'] = form.render()
        return resp
    update(request, user, dict(c.items()))
    data = dict(username=user.user_name)
    ts = _('user-updated', default='${username} profile updated', mapping=data)
    request.session.flash(ts)
    return HTTPFound(location=request.route_url('user'))


@view_config(
    route_name='user-view', renderer='templates/user/edit.pt',
    permission='user-view')
def view_view(request):
    q = DBSession.query(User).filter_by(id=request.matchdict['id'])
    if request.user.company_id:
        q = q.filter_by(company_id=request.user.company_id)
    user = q.first()
    if not user:
        return HTTPNotFound()
    if user.id == request.user.id:
        form = get_form(request, AddSchema, user)
    else:
        form = get_form(request, EditSchema, user, buttons=(btn_close,))

    resp = dict(title=_('View user'))
    if not request.POST:
        d = user.to_dict()
        d['groups'] = user_group_set(user)
        resp['form'] = form.render(appstruct=d, readonly=True)
        return resp
    return HTTPFound(location=request.route_url('user'))


@view_config(
    route_name='user-delete', renderer='templates/user/delete.pt',
    permission='user-edit')
def view_delete(request):
    q = DBSession.query(User).filter_by(id=request.matchdict['id'])
    if request.user.company_id:
        q = q.filter_by(company_id=request.user.company_id)
    user = q.first()
    if not user:
        return HTTPNotFound()
    if not request.POST:
        btn_delete = Button('delete', _('Delete'))
        btn_cancel = Button('cancel', _('Cancel'))
        buttons = (btn_delete, btn_cancel)
        form = Form(colander.Schema(), buttons=buttons)
        return dict(title=_('Delete user'), user=user, form=form.render())
    if 'delete' not in request.POST:
        return HTTPFound(location=request.route_url('user'))
    gid_list = user_group_set(user)
    for gid in gid_list:
        reduce_member_count(gid)
    data = dict(uid=user.id, email=user.email)
    ts = _(
        'user-deleted',
        default='User ${email} ID ${uid} has been deleted',
        mapping=data)
    q.delete()
    request.session.flash(ts)
    return HTTPFound(location=request.route_url('user'))


@view_config(
    route_name='user-act', renderer='json', permission='user-view')
def view_act(request):
    req = request
    url_dict = req.matchdict
    if url_dict['act'] == 'grid':
        columns = [
            ColumnDT(User.id, mData='id'),
            ColumnDT(User.email, mData='email'),
            ColumnDT(User.user_name, mData='name'),
            ColumnDT(User.status, mData='status'),
            ColumnDT(func.to_char(User.last_login_date, 'DD-MM-YYYY HH24:MI:SS'),
                     mData='last_login'),
            ColumnDT(func.to_char(User.registered_date, 'DD-MM-YYYY HH24:MI:SS'),
                     mData='registered'),
        ]
        query = DBSession.query().select_from(User)
        if request.user.company_id:
            query = query.filter(User.company_id == request.user.company_id)

        row_table = DataTables(req.GET, query, columns)
        return row_table.output_result()

    elif url_dict['act'] == 'csv':
        query = query_register()
        row = query.first()
        header = row.keys()
        rows = []
        for item in query.all():
            rows.append(list(item))

        filename = 'user.csv'
        value = {
            'header': header,
            'rows': rows,
        }
        return csv_response(request, value, filename)
    elif url_dict['act'] == 'pdf':
        # todo ganti rml jadi openoffice
        query = query_register()
        _here = os.path.dirname(__file__)  # get current folder -> views
        path = os.path.dirname(_here)  # mundur 1 level
        path = os.path.join(path, 'reports')
        rml_row = open_rml_row(path + '/user.row.rml')
        rows = []
        for r in query.all():
            s = rml_row.format(user_name=r.user_name, email=r.email,
                               registered_date=r.registered_date)
            rows.append(s)
        pdf, filename = open_rml_pdf(path + '/user.rml', rows=rows,
                                     company=request.company,
                                     departement=request.departement,
                                     address=request.address)
        return pdf_response(request, pdf, filename)


def query_register():
    return DBSession.query(User.user_name, User.email,
                           func.to_char(User.registered_date, "DD-MM-YYYY").label("registered_date")).order_by(
        User.user_name)
