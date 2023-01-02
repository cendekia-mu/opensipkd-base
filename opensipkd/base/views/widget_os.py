import json
import logging

from colander import SchemaNode, null, Mapping, Invalid, text_, string_types
from deform.widget import Widget, _StrippedString, Select2Widget

_logging = logging.getLogger(__name__)


class DokumenWidget(Widget):
    template = "opensipkd.base:/views/widgets/dokumen.pt"
    readonly_template = "opensipkd.base:/views/widgets/readonly/dokumen.pt"
    assume_y2k = True

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="jenis"),
        SchemaNode(_StrippedString(), name="year"),
        SchemaNode(_StrippedString(), name="bundle"),
        SchemaNode(_StrippedString(), name="seq"),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            jenis = ""
            year = ""
            bundle = ""
            seq = ""
        else:
            jenis, year, bundle, seq = cstruct.split(".", 3)

        kw.setdefault("jenis", jenis)
        kw.setdefault("year", year)
        kw.setdefault("bundle", bundle)
        kw.setdefault("seq", seq)

        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            jenis = validated["jenis"]
            year = validated["year"]
            bundle = validated["bundle"]
            seq = validated["seq"]

            if not year and not bundle and not seq:
                return null

            if self.assume_y2k and len(year) == 2:
                year = "20" + year
            result = ".".join([jenis, year, bundle, seq])

            if not year or not bundle or not seq:
                raise Invalid(field.schema, "No Dokumen tidak lengkap", result)

            return result


class FormulirWidget(Widget):
    template = "opensipkd.base:/views/widgets/formulir.pt"
    readonly_template = "opensipkd.base:/views/widgets/readonly/formulir.pt"
    assume_y2k = True

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="year"),
        SchemaNode(_StrippedString(), name="bundle"),
        SchemaNode(_StrippedString(), name="seq"),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            year = ""
            bundle = ""
            seq = ""
        else:
            year, bundle, seq = cstruct.split(".", 3)

        kw.setdefault("year", year)
        kw.setdefault("bundle", bundle)
        kw.setdefault("seq", seq)

        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            year = validated["year"]
            bundle = validated["bundle"]
            seq = validated["seq"]

            if not year and not bundle and not seq:
                return null

            if self.assume_y2k and len(year) == 2:
                year = "20" + year
            result = ".".join([year, bundle, seq])

            if not year or not bundle or not seq:
                raise Invalid(field.schema, "No Dokumen tidak lengkap", result)

            return result


class BlokKavNoWidget(Widget):
    template = "opensipkd.base:/views/widgets/blok_kav_no.pt"
    readonly_template = "opensipkd.base:/views/widgets/readonly/blok_kav_no.pt"

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="blok_kav_no"),
        SchemaNode(_StrippedString(), name="rt"),
        SchemaNode(_StrippedString(), name="rw")
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            blok_kav_no = ""
            rt = "000"
            rw = "00"
        else:
            blok_kav_no, rt, rw = cstruct.split("|", 3)

        kw.setdefault("blok_kav_no", blok_kav_no)
        kw.setdefault("rt", rt)
        kw.setdefault("rw", rw)

        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            blok_kav_no = validated["blok_kav_no"]
            rt = validated["rt"]
            rw = validated["rw"]

            if not blok_kav_no and not rt and not rw:
                return null

            result = "|".join([blok_kav_no, rt, rw])

            if not blok_kav_no or not rt or not rw:
                raise Invalid(field.schema, "Blok Kav No RT/RW tidak lengkap",
                              result)

            return result


class Select2MsWidget(Select2Widget):
    """
    Renders ``<select>`` field based on a predefined set of values using
    `select2 <https://select2.org/>`_ library.

    **Attributes/Arguments**

    Same as :func:`~deform.widget.Select2Widget`, with some extra options
    listed here.
    url: url for slave select
    slave: id of slave  select
    widget = widget_os.Select2MsWidget(url="https://slave_item_url?item_key=selected_value,
                                        slave="slave_id")

    """

    template = "select2_ms.pt"


class QtyWidget(Widget):
    template = "opensipkd.base:/views/widgets/qty.pt"
    readonly_template = "opensipkd.base:/views/widgets/readonly/qty.pt"

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="qty"),
        SchemaNode(_StrippedString(), name="measure"),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            qty = 0
            measure = 0
        else:
            qty, measure = cstruct.split("|", 3)

        kw.setdefault("qty", qty)
        kw.setdefault("measure", measure)
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            qty = validated["qty"]
            measure = validated["measure"]

            if not qty and not measure:
                return null

            result = "|".join([str(qty), str(measure)])

            if not qty or not measure:
                raise Invalid(field.schema, "Data tidak lengkap", result)

            return result


class CaptchaWidget(Widget):
    """
    Renders an ``<input type="text"/>`` widget.

    **Attributes/Arguments**

    template
       The template name used to render the widget.  Default:
        ``textinput``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/textinput``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    """

    template = "opensipkd.base:views/widgets/captcha.pt"
    readonly_template = "textinput"
    strip = True
    requirements = ()

    def __init__(self, **kw):
        super(CaptchaWidget, self).__init__(**kw)

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        elif not isinstance(pstruct, string_types):
            raise Invalid(field.schema, "Pstruct is not a string")
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct


class ImageWidget(Widget):
    """
    Renders an ``<img src="src"/>`` widget.

    **Attributes/Arguments**

    template
       The template name used to render the widget.  Default:
        ``image``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/image``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    """

    template = "opensipkd.base:views/widgets/image.pt"
    readonly_template = "image"
    strip = True
    requirements = ()
    height = "30px"

    def __init__(self, **kw):
        super().__init__(**kw)

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        elif not isinstance(pstruct, string_types):
            raise Invalid(field.schema, "Pstruct is not a string")
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct


class MapWidget(Widget):
    """
    Renders an ``<div id="map"/>`` widget.

    **Attributes/Arguments**

    template
       The template name used to render the widget.  Default:
        ``textinput``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/textinput``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    """

    template = "opensipkd.base:views/widgets/gmap.pt"
    readonly_template = "opensipkd.base:views/widgets/readonly/gmap.pt"
    map_center = [0, 0]
    map_zoom = 12
    gmap_key = None
    gmap_control = ['Point', 'Polygon', 'LineString']
    gmap_height = "400px"
    gmap_width = "100%"
    strip = True
    html_info = {}
    gmap_data_style = {
        "editable": True,
        "draggable": True,
        "clickable": True,
        "removable": True,
    }
    gmap_edit_url = ""
    show_options = False
    requirements = (('deform', None),
                    {
                        "js": "opensipkd.base:static/js/gmap.js",
                        "css": "deform:static/select2/select2.css",
                    },)

    def __init__(self, **kw):
        super().__init__(**kw)
        _logging.info(self.gmap_data_style)
        self.gmap_data_style = json.dumps(self.gmap_data_style)

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        _logging.debug(self.gmap_data_style)
        # if readonly:
        gmap_data_style = {
            "editable": not readonly,
            "draggable": not readonly,
            "clickable": True,
            "removable": not readonly,
        }
        self.gmap_data_style = json.dumps(gmap_data_style)
        _logging.info(self.gmap_data_style)

        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        elif not isinstance(pstruct, string_types):
            raise Invalid(field.schema, "Pstruct is not a string")
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct


class LeafMapWidget(Widget):
    """
    Renders an ``<div id="map"/>`` widget.

    **Attributes/Arguments**

    template
       The template name used to render the widget.  Default:
        ``textinput``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/textinput``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    """

    template = "opensipkd.base:views/widgets/leafmap.pt"
    readonly_template = "opensipkd.base:views/widgets/readonly/leafmap.pt"
    map_center = [0, 0]
    map_zoom = 12
    # gmap_control = ['Point', 'Polygon', 'LineString']
    map_height = "400px"
    map_width = "100%"
    strip = True
    html_info = {}
    # gmap_data_style = {
    #     "editable": True,
    #     "draggable": True,
    #     "clickable": True,
    #     "removable": True,
    # }
    # gmap_edit_url = ""
    show_options = True
    requirements = (
        ('deform', None),
        {
            "js": ["opensipkd.base:static/v3/map/leaflet/leaflet.js",
                   "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/0.4.2/leaflet.draw.js"],
            "css": ["opensipkd.base:static/v3/map/leaflet/leaflet.css",
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/0.4.2/leaflet.draw.css"],
        })

    def __init__(self, **kw):
        super().__init__(**kw)
        # _logging.info(self.gmap_data_style)
        # self.gmap_data_style = json.dumps(self.gmap_data_style)

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        # _logging.debug(self.gmap_data_style)
        # if readonly:
        gmap_data_style = {
            "editable": not readonly,
            "draggable": not readonly,
            "clickable": True,
            "removable": not readonly,
        }
        # self.gmap_data_style = json.dumps(gmap_data_style)
        # _logging.info(self.gmap_data_style)

        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        elif not isinstance(pstruct, string_types):
            raise Invalid(field.schema, "Pstruct is not a string")
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct
