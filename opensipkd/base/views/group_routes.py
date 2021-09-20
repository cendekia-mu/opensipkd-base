import os
import uuid
# from okeuangan.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, or_, and_
from pyramid.view import (
    view_config,
)
from pyramid.httpexceptions import (
    HTTPFound,
)
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
)
from ..models import DBSession, GroupRoutePermission, Group, Route
from ..views.common import ColumnDT, DataTables

# from okeuangan.views.base_view import BaseViews


SESS_ADD_FAILED = 'Tambah routes gagal'
SESS_EDIT_FAILED = 'Edit routes gagal'


def deferred_source_type(node, kw):
    values = kw.get('perm_choice', [])
    return widget.SelectWidget(values=values)


class AddSchema(colander.Schema):
    group_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/group/headofnama/act',
        min_length=1)

    route_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/routes/headof/act',
        min_length=1)

    group_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.HiddenWidget(),
        oid='group_id')
    group_nm = colander.SchemaNode(
        colander.String(),
        # widget = group_widget,
        title='Group',
        oid='group_nm')
    # route_id  = colander.SchemaNode(
    # colander.Integer(),
    # #widget = widget.HiddenWidget(),
    # oid = 'route_id')
    # route_nm  = colander.SchemaNode(
    # colander.String(),
    # #widget = route_widget,
    # title ='Route',
    # oid = 'route_nm')


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


########
# List #
########    
@view_config(route_name='group-routes', renderer='templates/group-routes/list.pt',
             permission='group-routes')
def view_list(request):
    return dict(a={})


##########                    
# Action #
##########    
@view_config(route_name='group-routes-act', renderer='json',
             permission='group-routes-act')
def view_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict

    if url_dict['act'] == 'grid':
        columns = []
        columns.append(ColumnDT(GroupRoutePermission.group_id, mData="group_id", global_search=False))
        columns.append(ColumnDT(GroupRoutePermission.route_id, mData="route_id", global_search=False))
        columns.append(ColumnDT(Group.group_name, mData="group_nama"))
        columns.append(ColumnDT(Route.nama, mData="route_nama"))
        columns.append(ColumnDT(Route.path, mData="route_path"))
        query = DBSession.query().select_from(
            GroupRoutePermission, Group, Route).join(Group).join(Route)
        rowTable = DataTables(req.GET, query, columns)
        return rowTable.output_result()

    elif url_dict['act'] == 'grid-add':
        group_id = 'group_id' in params and params['group_id'] or -1
        # ambil route_id berdasarkan table
        group_route = DBSession.query(GroupRoutePermission). \
            filter(GroupRoutePermission.group_id == group_id).subquery()
        columns = []
        columns.append(ColumnDT(Route.id, mData="id", global_search=False))
        columns.append(ColumnDT(Route.kode, mData="kode"))
        columns.append(ColumnDT(Route.nama, mData="nama"))
        columns.append(ColumnDT(Route.path, mData="path"))
        columns.append(ColumnDT(group_route.c.route_id, mData="route_id", global_search=False))
        query = DBSession.query().select_from(Route). \
            outerjoin(group_route, and_(Route.id == group_route.c.route_id))
        if group_id == -1:
            query = query.filter(Route.id == group_id)
        rowTable = DataTables(req.GET, query, columns)
        return rowTable.output_result()

    elif url_dict['act'] == 'changeid':
        row = GroupRoutePermission.get_by_id('routes_id' in params and params['routes_id'] or 0)
        if row:
            ses['routes_id'] = row.id
            ses['routes_kd'] = row.kode
            ses['routes_nm'] = row.nama
            return {'success': True}


#######
# Add #
#######
def form_validator(form, value):
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(GroupRoutePermission).filter_by(id=uid)
        routes = q.first()
    else:
        routes = None


def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=('simpan', 'batal'))


def save(values, user, route_ids, group_route_ids, row=None, ):
    for route_id in route_ids:
        query = query_id(values['group_id'], route_id)
        row = query.first()
        if row:
            query.delete()
            DBSession.flush()

    for group_route_id in group_route_ids:
        query = query_id(values['group_id'], group_route_id)
        row = query.first()
        if not row:
            row = GroupRoutePermission()
        values['route_id'] = group_route_id
        row.from_dict(values)
        DBSession.add(row)
        DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']

    route_ids = request.params.getall("route_id")
    group_route_ids = request.params.getall("group_route_id")
    row = save(values, request.user, route_ids, group_route_ids, row)
    request.session.flash('Group Permission sudah disimpan.')

# edit-------
def edit_save(values, user, route_ids, group_route_ids, row=None, ):
    # for route_id in route_ids:
    #     query = query_id(values['group_id'], route_id)
    #     row = query.first()
    #     if row:
    #         query.delete()
    #         DBSession.flush()
        
    for group_route_id in group_route_ids:
        query = query_id(values['group_id'], group_route_id)
        row = query.first()
        if not row:
            row = GroupRoutePermission()
        values['route_id'] = group_route_id
        row.from_dict(values)
        DBSession.delete(row)
        DBSession.flush()
    return row

def edit_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
        
    route_ids = request.params.getall("route_id")
    group_route_ids = request.params.getall("group_route_id")
    row = edit_save(values, request.user, route_ids, group_route_ids, row)
    request.session.flash('Group Permission sudah disimpan.')
    
def routes_list(request):
    return HTTPFound(location=request.route_url('group-routes'))


def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r


@view_config(route_name='group-routes-add', renderer='templates/group-routes/add.pt',
             permission='group-routes-add')
def view_add(request):
    req = request
    ses = request.session
    form = get_form(request, AddSchema)
    if req.POST:
        if 'simpan' in req.POST:
            controls = list(req.POST.items())
            try:
                controls = form.validate(controls)
            except ValidationFailure as e:
                return dict(form=form)              
                #return HTTPFound(location=req.route_url('group-routes-add'))
                
            save_request(request, dict(controls))
        return routes_list(request)
    elif SESS_ADD_FAILED in req.session:
        return session_failed(request, SESS_ADD_FAILED)
    # return dict(form=form.render())
    return dict(form=form)


########
# Edit #
########
def query_id(group_id, route_id):
    return DBSession.query(GroupRoutePermission). \
        filter_by(group_id=group_id,
                  route_id=route_id)
    # return DBSession.query(GroupRoutePermission).filter_by(group_id=request.matchdict['id'],
    #          route_id=request.matchdict['id2'])


def id_not_found(request):
    msg = 'Group ID %s Routes ID %s Tidak Ditemukan.' % (request.matchdict['id'], request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return routes_list()


@view_config(route_name='group-routes-edit', renderer='templates/group-routes/edit.pt',
             permission='group-routes-edit')
def view_edit(request):
    #request = request
    request = request
    url_dict = request.matchdict

    q = query_id(url_dict['group_id'], url_dict['route_id'])
    row = q.first()

    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = list(request.POST.items())
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                request.session[SESS_EDIT_FAILED] = e.render()
                return HTTPFound(location=request.route_url('group-routes-edit',
                                  id=row.id))
            edit_request(request, dict(controls), row)
        return routes_list(request)

    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    # return dict(form=form.render(appstruct=values))
    form.set_appstruct(values)
    return dict(form=form)

def query_id(group_id, route_id):
    return DBSession.query(GroupRoutePermission).\
                          filter_by(group_id = group_id,
                                    route_id = route_id)
    #return DBSession.query(GroupRoutePermission).filter_by(group_id=request.matchdict['id'],
    #          route_id=request.matchdict['id2'])
    
def id_not_found(request):    
    msg = 'Group ID %s Routes ID %s Tidak Ditemukan.' % (request.matchdict['id'], request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return routes_list()

##########
# Delete #
##########    
@view_config(route_name='group-routes-delete', renderer='templates/group-routes/delete.pt',
             permission='group-routes-delete')
def view_delete(request):
    request = request
    url_dict = request.matchdict

    q = query_id(url_dict['group_id'], url_dict['route_id'])
    row = q.first()

    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus', 'batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Group ID %d Routes ID %d sudah dihapus.' % (row.group_id, row.route_id)
            try:
                q.delete()
                DBSession.flush()
            except:
                msg = 'Group ID %d Routes ID %d  tidak dapat dihapus.' % (row.id, row.route_id)
            request.session.flash(msg)
        return routes_list(request)
    return dict(row=row,
                form=form.render())
