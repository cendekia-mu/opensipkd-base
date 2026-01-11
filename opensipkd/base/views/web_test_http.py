import colander
from pyramid.httpexceptions import HTTPFound
from deform.exception import ValidationFailure
from . import base_views

class ViewSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Int(),
        title="ID",
        description="Unique identifier for the test.",
    )

class Views(base_views.BaseView):
    """ Test HTTP View """
    def __init__(self, request):
        super(Views, self).__init__(request)
        self.add_schema = ViewSchema

    def view_test(self):
        form = self.get_form(self.add_schema)
        # if self.req.POST:
        #     return HTTPFound(location=self.req.route_url('base-test'))
        return {'form': form.render()}
    
    def next_add(self, form, **kwargs):
        return super().next_add(form, **kwargs)
    