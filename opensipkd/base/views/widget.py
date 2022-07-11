import json

from deform.widget import (
    SchemaType,
    DateInputWidget as DeformDateInputWidget)
from colander import null, Invalid

class _FieldStorage(SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct in (null, None, '', b''):
            return null
        # weak attempt at duck-typing
        if not hasattr(cstruct, 'file'):
            raise Invalid(node, "%s is not a FieldStorage instance" % cstruct)
        return cstruct


class DateInputWidget(DeformDateInputWidget):
    """
    Renders a date picker widget.

    The default rendering is as a native HTML5 date input widget,
    falling back to pickadate (https://github.com/amsul/pickadate.js.)

    Most useful when the schema node is a ``colander.Date`` object.

    **Attributes/Arguments**

    options
        Dictionary of options for configuring the widget (eg: date format)

    template
        The template name used to render the widget.  Default:
        ``dateinput``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/textinput``.
    """
    default_options = (
        ("format", "yyyy-mm-dd"),
        ("selectMonths", True),
        ("selectYears", True),
        ("formatSubmit", "yyyy-mm-dd"),
    )
    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        options = dict(
            kw.get("options") or self.options or self.default_options
        )
        kw.setdefault("options_json", json.dumps(options))
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct in ("", null):
            return null
        try:
            validated = self._pstruct_schema.deserialize(pstruct)
        except Invalid as exc:
            raise Invalid(field.schema, "Invalid pstruct: %s" % exc)
        return validated["date_submit"] or validated["date"]
