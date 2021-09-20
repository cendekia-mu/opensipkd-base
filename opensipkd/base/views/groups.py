from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
)
from pyramid.i18n import TranslationStringFactory
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    Button,
)
from datatables import (
    ColumnDT,
    DataTables,
)
from opensipkd.tools.buttons import btn_save, btn_cancel, btn_close

from ..models import (
    DBSession,
    Group,
    Permission,
    GroupPermission,
)

_ = TranslationStringFactory('user')


# class NameValidator:
#     def __init__(self, group):
#         self.group = group
#
#     def __call__(self, node, value):
#         group_name = clean_name(value)
#         if self.group and self.group.group_name.lower() == group_name.lower():
#             return
#         q = DBSession.query(Group). \
#             filter(Group.group_name.ilike(group_name))
#         found = q.first()
#         if not found:
#             return
#         data = dict(group_name=group_name, gid=found.id)
#         ts = _(
#             'group-name-already-used',
#             default='Group name ${group_name} already used by ID ${gid}',
#             mapping=data)
#         raise colander.Invalid(node, ts)


@colander.deferred
def name_validator(node, kw):
    return NameValidator(kw['group'])


@colander.deferred
def permissions_widget(node, kw):
    values = kw.get('permissions_list', [])
    return widget.CheckboxChoiceWidget(values=values)


class AddSchema(colander.Schema):
    group_name = colander.SchemaNode(
        colander.String(), validator=name_validator)
    description = colander.SchemaNode(colander.String(), missing=colander.drop)
    permissions = colander.SchemaNode(
        colander.Set(), widget=permissions_widget, title='Hak akses')


########
# List #
########
@view_config(
    route_name='group', renderer='templates/group/list.pt',
    permission='user-view')
def view_list(request):
    return dict()


##########
# Action #
##########
@view_config(
    route_name='group-act', renderer='json', permission='user-view')
def view_act(request):
    params = request.params
    url_dict = request.matchdict
    if url_dict['act'] == 'grid':
        columns = [ColumnDT(Group.id, mData="id"),
                   ColumnDT(Group.group_name, mData="name"),
                   ColumnDT(Group.description, mData="desc"),
                   ColumnDT(Group.member_count, mData="member")]
        q = DBSession.query().select_from(Group).order_by(Group.group_name)
        rowTable = DataTables(request.GET, q, columns)
        return rowTable.output_result()
    elif url_dict['act'] == 'hon':
        term = 'term' in params and params['term'] or ''
        q = DBSession.query(Group.id, Group.description).filter(
            Group.description.ilike('%{}%'.format(term))). \
            order_by(Group.group_name)
        rows = q.all()
        r = []
        for k in rows:
            d = dict(id=k[0], value=k[1])
            r.append(d)
        return r


#######
# Add #
#######
def clean_name(s):
    s = s.strip()
    while s.find('  ') > -1:
        s = s.replace('  ', ' ')
    return s


class NameValidator:
    def __init__(self, group):
        self.group = group

    def __call__(self, node, value):
        group_name = clean_name(value)
        if self.group and self.group.group_name.lower() == group_name.lower():
            return
        q = DBSession.query(Group). \
            filter(Group.group_name.ilike(group_name))
        found = q.first()
        if not found:
            return
        data = dict(group_name=group_name, gid=found.id)
        ts = _(
            'group-name-already-used',
            default='Group name ${group_name} already used by ID ${gid}',
            mapping=data)
        raise colander.Invalid(node, ts)


@colander.deferred
def name_validator(node, kw):
    return NameValidator(kw['group'])


@colander.deferred
def permissions_widget(node, kw):
    values = kw.get('permission_list', [])
    return widget.CheckboxChoiceWidget(values=values)


def get_permissions_list():
    q = DBSession.query(Permission)
    r = []
    for perm in q.order_by(Permission.description):
        row = (perm.perm_name, perm.description)
        r.append(row)
    return r


def get_form(request, group=None, buttons=(btn_save, btn_cancel)):
    schema = AddSchema()
    schema = schema.bind(permissions_list=get_permissions_list(), group=group)
    # btn_save = Button('save', _('Simpan'))
    # btn_cancel = Button('cancel', _('Batal'))
    # buttons = (btn_save, btn_cancel)
    return Form(schema, buttons=buttons)


def insert(values):
    group = Group()
    group.group_name = values['group_name']
    if 'description' in values:
        group.description = values['description']
    DBSession.add(group)
    DBSession.flush()
    for perm_name in values['permissions']:
        gp = GroupPermission()
        gp.group_id = group.id
        gp.perm_name = perm_name
        DBSession.add(gp)
    return group


@view_config(
    route_name='group-add', renderer='templates/group/add.pt',
    permission='user-edit')
def view_add(request):
    form = get_form(request)
    if not request.POST:
        return dict(form=form.render())
    if 'save' not in request.POST:
        return HTTPFound(location=request.route_url('group'))
    items = request.POST.items()
    try:
        c = form.validate(items)
    except ValidationFailure as e:
        return dict(form=e.render())
    group = insert(dict(c.items()))
    data = dict(group_name=group.group_name)
    ts = _(
        'group-added',
        default='${group_name} group has been added.',
        mapping=data)
    request.session.flash(ts)
    return HTTPFound(location=request.route_url('group'))


########
# Edit #
########
def group_permission_set(group):
    q = DBSession.query(GroupPermission).filter_by(group_id=group.id)
    r = []
    for gp in q:
        r.append(gp.perm_name)
    return set(r)


def update(group, values):
    group.group_name = values['group_name']
    if 'description' in values:
        group.description = values['description']
    DBSession.add(group)
    existing = group_permission_set(group)
    unused = existing - values['permissions']
    if unused:
        q = DBSession.query(GroupPermission).filter_by(group_id=group.id). \
            filter(GroupPermission.perm_name.in_(unused))
        q.delete(synchronize_session=False)
    new = values['permissions'] - existing
    for perm_name in new:
        gp = GroupPermission()
        gp.group_id = group.id
        gp.perm_name = perm_name
        DBSession.add(gp)


@view_config(
    route_name='group-edit', renderer='templates/group/edit.pt',
    permission='user-edit')
def view_edit(request):
    q = DBSession.query(Group).filter_by(id=request.matchdict['id'])
    group = q.first()
    if not group:
        return HTTPNotFound()
    form = get_form(request, group)
    resp = dict(title=_('Edit group'))
    if not request.POST:
        d = group.to_dict_without_none()
        d['permissions'] = group_permission_set(group)
        resp['form'] = form.render(appstruct=d)
        return resp
    if 'save' not in request.POST:
        return HTTPFound(location=request.route_url('group'))
        # resp['form'] = form.render()
    items = request.POST.items()
    try:
        c = form.validate(items)
    except ValidationFailure:
        resp['form'] = form.render()
        return resp
    update(group, dict(c.items()))
    data = dict(group_name=group.group_name)
    ts = _('group-updated', default='${group_name} group profile updated', mapping=data)
    request.session.flash(ts)
    return HTTPFound(location=request.route_url('group'))


@view_config(
    route_name='group-view', renderer='templates/group/edit.pt',
    permission='user-view')
def view_VIEW(request):
    q = DBSession.query(Group).filter_by(id=request.matchdict['id'])
    group = q.first()
    if not group:
        return HTTPNotFound()
    form = get_form(request, group, buttons=(btn_close,))
    resp = dict(title=_('View group'))
    if not request.POST:
        d = group.to_dict_without_none()
        d['permissions'] = group_permission_set(group)
        resp['form'] = form.render(appstruct=d, readonly=True)
        return resp
    return HTTPFound(location=request.route_url('group'))


##########
# Delete #
##########
@view_config(
    route_name='group-delete', renderer='templates/group/delete.pt',
    permission='user-edit')
def view_delete(request):
    q = DBSession.query(Group).filter_by(id=request.matchdict['id'])
    group = q.first()
    if not group:
        return HTTPNotFound()
    if not request.POST:
        btn_delete = Button('delete', _('Delete'))
        btn_cancel = Button('cancel', _('Cancel'))
        buttons = (btn_delete, btn_cancel)
        form = Form(colander.Schema(), buttons=buttons)
        return dict(form=form.render(), row=group)
    if 'delete' not in request.POST:
        return HTTPFound(location=request.route_url('group'))
    data = dict(group_name=group.group_name)
    ts = _(
        'group-deleted',
        default='{group_name} group has been deleted.',
        mapping=data)
    q.delete()
    request.session.flash(ts)
    return HTTPFound(location=request.route_url('group'))
