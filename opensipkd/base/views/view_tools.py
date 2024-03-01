import colander
from pyramid.csrf import new_csrf_token, get_csrf_token

from opensipkd.base.views import widget


class CSRFSchema(colander.Schema):
    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        csrf_token = get_csrf_token(request)
        if not csrf_token:
            csrf_token = new_csrf_token(request)

        self["csrf_token"] = colander.SchemaNode(
            colander.String(), widget=widget.HiddenWidget(),
            default=csrf_token
        )
