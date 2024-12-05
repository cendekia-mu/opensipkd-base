import colander

from opensipkd.base.views import BaseView
from opensipkd.base.views.user import AddSchema


class AddSchema(colander.Schema):
    test = colander.SchemaNode(colander.String())


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.add_schema = AddSchema

    def view_reports(self):
        c
        return super().view_add()

    def view_report(self):
        c
        return super().view_add()