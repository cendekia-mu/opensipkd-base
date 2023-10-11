import json
import logging

from deform.widget import (
    SchemaType,
    DateInputWidget as DeformDateInputWidget,
    DateInputWidget
    default_resources, ResourceRegistry, default_resource_registry, _StrippedString, Widget)
from colander import null, Invalid, SchemaNode, Mapping

_logging = logging.getLogger(__name__)


class _FieldStorage(SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct in (null, None, '', b''):
            return null
        # weak attempt at duck-typing
        if not hasattr(cstruct, 'file'):
            raise Invalid(node, "%s is not a FieldStorage instance" % cstruct)
        return cstruct


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
