# #Widget Standard
# #https://docs.pylonsproject.org/projects/deform/en/latest/api.html#module-deform.widget
# widget = widget.HiddenWidget(),
# deform.widget.TextInputWidget(readonly=True),
# deform.widget.SelectWidget(**kw)
#
# #COLANDER DEFFERED
# #base.tools
# STATUS = (
#     (1, 'Aktif'),
#     (0, 'Pasif')
#     )
#
# from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
# from sqlalchemy.orm import relationship, backref
# relationship("Address", backref="user")
#
# #base.views.base_view
# @colander.deferred
# def deferred_status(node, kw):                    ##initialize deffered_status
#   values = kw.get('daftar_status', [])          #varible for get value daftar_status
#   return widget.SelectWidget(values=values)
#
# #SCHEMA
# class AddSchema(colander.Schema):
#     status = colander.SchemaNode(
#                 colander.Integer(),
#                 widget=deferred_status,           ##getting deffered status
#                 title="Status")
#
# #BINDING
# def get_form(request, class_form):
#     schema = class_form()
#     schema = schema.bind(daftar_status=STATUS,) #varianbel daftar_status bind to LIST Value
#
# def tbl_list_value():
#     return DBSEssion.query(table.key, table.value).all()
#
# #base.views.base_view
# @colander.deferred
# def deferred_list_value(node, kw):                    ##initialize deffered_status
#     values = kw.get('list_value', [])               #varible for get value list_value
#     return widget.SelectWidget(values=values)
# #SCHEMA
# class AddSchema(colander.Schema):
#     status = colander.SchemaNode(
#                 colander.Integer(),
#                 widget=deferred_list_value,           ##getting deffered status
#                 title="Status")
#
# #BINDING
# def get_form(request, class_form):
#     schema = class_form()
#     schema = schema.bind(list_value = tbl_list_value(),) #varianbel list_value bind to LIST Value
#
# # <script>
# #         $('#jabatan_nm').typeahead({"minLength": 1, "remote": "/jabatan/hon/act?term=%QUERY", "limit": 8});
# #         $('#jabatan_nm').bind('typeahead:selected', function(obj, datum, name) {
# #           $('#jabatan_id').val(datum.id);
# #         });
# # </script>
#
# #         elif url_dict['act']=='hon':
# #             term   = 'term'   in params and params['term']   or ''
# #             prefix = 'prefix' in params and params['prefix'] or ''
# #             qry = DBSession.query(Jabatan).\
# #                     filter(Jabatan.status == 1).\
# #                     filter(Jabatan.nama.ilike('%%%s%%' % term)).\
# #                     filter(Jabatan.kode.ilike('%s%%' % prefix)).\
# #                     order_by(Jabatan.nama)
# #             r = []
# #             for row in qry.all():
# #                 d=dict(
# #                         id    = row.id,
# #                         value = row.nama,
# #                         kode  = row.kode,
# #                         #nama  = row.nama
# #                         )
# #                 r.append(d)
# #             return r
# # #class
# # <style>
# #   .red-border {
# #       border-color: rgba(255, 0, 0, 0.2);
# #       box-shadow: 0 1px 1px rgba(255, 0, 0, 0.2); inset, 0 0 8px rgba(255, 0, 0, 0.2);
# #       outline: 0 none;
# #   }
# # </style>
# # <script>
# #         $('#source_id').typeahead({"minLength": 1, "remote": "/eis/slide/hon/act?term=%QUERY", "limit": 8});
# #         $('#source_id').bind('typeahead:selected', function(obj, datum, name) {
# #           if (!datum.id){
# #               $('#source_id').addClass("red-border");
# #               return;
# #           }
# #           $('#source_id').removeClass("red-border")
# #           $('#source_id').val(datum.id);
# #         });
# # </script>
# #
# # [handlers]
# # keys = console, filelog
# #
# # [logger_root]
# # level = INFO
# # handlers = console, filelog
# #
# # [handler_filelog]
# # class = FileHandler
# # args = ('%(here)s/../../tmp/pserve.log','a')
# # level = INFO
# # formatter = generic
