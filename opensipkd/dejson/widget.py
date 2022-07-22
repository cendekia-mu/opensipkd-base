"""Widget."""
# Standard Library
import csv
import json
import random

# Pyramid
from colander import Invalid
from colander import Mapping
from colander import SchemaNode
from colander import SchemaType
from colander import Sequence
from colander import String
from colander import null
from iso8601.iso8601 import ISO8601_REGEX
from translationstring import TranslationString

from deform.widget import MappingWidget
from deform.compat import text_
from .i18n import _

_BLANK = text_("")


class TableWidget(MappingWidget):
    """
    The top-level widget; represents an entire table.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``detable``.

    """

    template = "detable"
    readonly_template = "readonly/detable"
    requirements = (("deform", None),
                    {"js": "opensipkd.base:static/v3/js/plugin/datatables/jquery.dataTables.min.js"})
