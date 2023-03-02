import json
import logging

from deform.widget import (
    SchemaType,
    DateInputWidget as DeformDateInputWidget,
    default_resources, ResourceRegistry, default_resource_registry)
from colander import null, Invalid

_logging = logging.getLogger(__name__)
class _FieldStorage(SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct in (null, None, '', b''):
            return null
        # weak attempt at duck-typing
        if not hasattr(cstruct, 'file'):
            raise Invalid(node, "%s is not a FieldStorage instance" % cstruct)
        return cstruct


# class DateInputWidget(DeformDateInputWidget):
#     """
#     Renders a date picker widget.
#
#     The default rendering is as a native HTML5 date input widget,
#     falling back to pickadate (https://github.com/amsul/pickadate.js.)
#
#     Most useful when the schema node is a ``colander.Date`` object.
#
#     **Attributes/Arguments**
#
#     options
#         Dictionary of options for configuring the widget (eg: date format)
#
#     template
#         The template name used to render the widget.  Default:
#         ``dateinput``.
#
#     readonly_template
#         The template name used to render the widget in read-only mode.
#         Default: ``readonly/textinput``.
#     """
#     requirements = {
#             "js": (
#                 "deform:static/scripts/modernizr.custom.input-types-and-atts.js",
#                 "static/pickadate/lib/picker.js",
#                 "static/pickadate/lib/picker.date.js",
#                 "static/pickadate/lib/picker.time.js",
#                 "static/pickadate/lib/legacy.js",
#             ),
#             "css": (
#                 "static/pickadate/lib/themes/default.css",
#                 "static/pickadate/lib/themes/default.date.css",
#                 "static/pickadate/lib/themes/default.time.css",
#             ),
#         }
#     default_options = (
#             ("format", "yyyy-mm-dd"),
#             ("selectMonths", True),
#             ("selectYears", True),
#             ("formatSubmit", "yyyy-mm-dd"),
#         )
#     def serialize(self, field, cstruct, **kw):
#         if cstruct in (null, None):
#             cstruct = ""
#         readonly = kw.get("readonly", self.readonly)
#         template = readonly and self.readonly_template or self.template
#         options = dict(
#             kw.get("options") or self.options or self.default_options
#         )
#         kw.setdefault("options_json", json.dumps(options))
#         values = self.get_template_values(field, cstruct, kw)
#         return field.renderer(template, **values)
#
#     def deserialize(self, field, pstruct):
#         logging.debug(f"widget: {field} {pstruct}")
#         if pstruct in ("", null):
#             return null
#         try:
#             validated = self._pstruct_schema.deserialize(pstruct)
#         except Invalid as exc:
#             raise Invalid(field.schema, "Invalid pstruct: %s" % exc)
#         return validated["date_submit"] or validated["date"]

# default_resources["pickadate"] = \
#     {
#         None: {
#             "js": (
#                 "static/pickadate/lib/picker.js",
#                 "static/pickadate/lib/picker.date.js",
#                 "static/pickadate/lib/picker.time.js",
#                 "static/pickadate/lib/legacy.js",
#             ),
#             "css": (
#                 "static/pickadate/lib/themes/default.css",
#                 "static/pickadate/lib/themes/default.date.css",
#                 "static/pickadate/lib/themes/default.time.css",
#             ),
#         }
#     }
# default_resources = {
#     "jquery.form": {None: {"js": "deform:static/scripts/jquery.form-3.09.js"}},
#     "jquery.maskedinput": {
#         None: {"js": "deform:static/scripts/jquery.maskedinput-1.3.1.min.js"}
#     },
#     "jquery.maskMoney": {
#         None: {"js": "deform:static/scripts/jquery.maskMoney-3.1.1.min.js"}
#     },
#     "deform": {
#         None: {
#             "js": (
#                 "deform:static/scripts/jquery.form-3.09.js",
#                 "deform:static/scripts/deform.js",
#             )
#         }
#     },
#     "typeahead": {
#         None: {
#             "js": "deform:static/scripts/typeahead.min.js",
#             "css": "deform:static/css/typeahead.css",
#         }
#     },
#     "modernizr": {
#         None: {
#             "js": "deform:static/scripts/modernizr.custom.input-types-and-atts.js"  # noQA
#         }
#     },
#     "pickadate": {
#         None: {
#             "js": (
#                 "static/pickadate/lib/picker.js",
#                 "static/pickadate/lib/picker.date.js",
#                 "static/pickadate/lib/picker.time.js",
#                 "static/pickadate/lib/legacy.js",
#             ),
#             "css": (
#                 "static/pickadate/lib/themes/default.css",
#                 "static/pickadate/lib/themes/default.date.css",
#                 "static/pickadate/lib/themes/default.time.css",
#             ),
#         }
#     },
# }
#
# default_resource_registry = ResourceRegistry()
