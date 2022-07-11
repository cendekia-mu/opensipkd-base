import colander
from deform import widget
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config

from . import BaseView
from opensipkd.models import (
    DBSession,
    Group,
    Permission,
    GroupPermission,
)

_ = TranslationStringFactory('user')


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


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
                             widget=widget.HiddenWidget(readonly=True),
                             missing=colander.drop)


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), visible=False)
    group_name = colander.SchemaNode(
        colander.String(), )
    description = colander.SchemaNode(colander.String())


class Views(BaseView):
    def __init__(self, request):
        super(Views, self).__init__(request)
        self.list_schema = ListSchema
        self.list_route = "group"
        self.table = Group
        self.add_schema = AddSchema
        self.edit_schema = EditSchema

    def get_bindings(self, row=None):
        return dict(group=row,
                    permissions_list=get_permissions_list())

    @view_config(
        route_name='group', renderer='templates/table.pt',
        permission='user-view')
    def view_list(self):
        return super(Views, self).view_list()

    @view_config(
        route_name='group-act', renderer='json', permission='user-view')
    def view_act(self):
        return super(Views, self).view_act()

    def next_act(self):
        request = self.req
        url_dict = request.matchdict
        params = self.params
        if url_dict['act'] == 'hon':
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

    @view_config(
        route_name='group-add', renderer='templates/form.pt',
        permission='user-edit')
    def view_add(self):
        return super(Views, self).view_add()

    def save_request(self, values, row=None):
        insert = not row
        row = self.save(values, self.req.user, row)
        existing = group_permission_set(row)
        unused = existing - values['permissions']
        if unused:
            q = DBSession.query(GroupPermission).filter_by(group_id=row.id). \
                filter(GroupPermission.perm_name.in_(unused))
            q.delete(synchronize_session=False)
        new = values['permissions'] - existing
        for perm_name in new:
            gp = GroupPermission()
            gp.group_id = row.id
            gp.perm_name = perm_name
            DBSession.add(gp)
        data = dict(group_name=row.group_name)
        if insert:
            ts = _('group-added', default='{group_name} group has been added.', mapping=data)

        else:
            ts = _('group-updated', default='${group_name} group profile updated', mapping=data)
        self.ses.flash(ts)
        return row

    def get_values(self, row, istime=False):
        values = super(Views, self).get_values(row, istime)
        values['permissions'] = group_permission_set(row)
        return values

    @view_config(
        route_name='group-view', renderer='templates/form.pt',
        permission='user-view')
    def view_view(self):
        return super(Views, self).view_view()

    @view_config(
        route_name='group-edit', renderer='templates/form.pt',
        permission='user-edit')
    def view_edit(self):
        return super(Views, self).view_edit()

    def delete_msg(self, row):
        data = dict(group_name=row.group_name)
        ts = _(
            'group-deleted',
            default='{group_name} group has been deleted.',
            mapping=data)
        self.ses.flash(ts)

    @view_config(
        route_name='group-delete', renderer='templates/form.pt',
        permission='user-edit')
    def view_delete(self):
        return super(Views, self).view_delete()


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


def group_permission_set(group):
    q = DBSession.query(GroupPermission).filter_by(group_id=group.id)
    r = []
    for gp in q:
        r.append(gp.perm_name)
    return set(r)
