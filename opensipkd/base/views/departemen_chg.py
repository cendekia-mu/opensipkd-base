import colander
from deform import (widget, )
from opensipkd.models import Departemen
from deform.exception import (ValidationFailure)
from pyramid.httpexceptions import (HTTPFound)
from urllib3 import request
from ..views import BaseView
SESS_ADD_FAILED = 'Tambah departemen gagal'
SESS_EDIT_FAILED = 'Edit departemen gagal'



class AddSchema(colander.Schema):
    departemen_id = colander.SchemaNode(
        colander.Integer(),
        widget = widget.Select2Widget(),
    )
    
    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        schema["departemen_id"].widget.values = kwargs.get("departemens", [])

class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.add_schema = AddSchema
        self.table = Departemen

    def get_bindings(self, row=None):
        departemens = self.table.get_list()
        return {"departemens": departemens}
    
    def view_change(self):
        next_url = self.req.params.get('next')
        if not next_url:
            next_url = self.req.referrer or self.req.route_url('base-home')

            return HTTPFound(self.req.route_url('departemen-chg', _query={'next': next_url}))
        if self.req.POST:
            if 'save' in self.req.POST:
                form = self.get_form(self.add_schema)
                controls = self.req.POST.items()
                try:
                    appstruct = form.validate(controls)
                except ValidationFailure as e:
                    return self.returned_form(e)
            
                departemen_id = appstruct['departemen_id']
                row = self.table.query_id(departemen_id).first()
                self.ses['departemen_id'] = departemen_id
                self.ses['departemen_nm'] = row and row.nama or "Select Departemen"
                self.ses['departemen_kd']= row and row.kode or ""
                self.ses["dept_id"] = departemen_id
            return HTTPFound(next_url)
            
        return super().view_add()