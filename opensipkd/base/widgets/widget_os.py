from pyramid.csrf import new_csrf_token, get_csrf_token
from iso8601.iso8601 import ISO8601_REGEX
# from deform.widget import str
import json
import logging
from pyramid.csrf import new_csrf_token, get_csrf_token
from iso8601.iso8601 import ISO8601_REGEX


from colander import SchemaNode, null, Mapping, Invalid  # , str
# from colander import compat # tidak ada di colander 2.0
from deform import widget
# from deform.compat import sequence_types, text_type, text_
from deform.form import Button
from deform.i18n import _
from deform.widget import (
    Widget, _StrippedString, Select2Widget,  _normalize_choices, OptGroup,
    DateInputWidget as WidgetDateInputWidget, AutocompleteInputWidget)
from opensipkd.tools.captcha import img_captcha
_logging = logging.getLogger(__name__)

sequence_types = (list, range,  tuple)
class DokumenWidget(Widget):
    template = "opensipkd.base:/widgets/templates/dokumen.pt"
    readonly_template = "opensipkd.base:/widgets/templates/readonly/dokumen.pt"
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
                raise Invalid(field.schema, f"Invalid pstruct: {exc}")
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
    template = "opensipkd.base:/widgets/templates/formulir.pt"
    readonly_template = "opensipkd.base:/widgets/templates/readonly/formulir.pt"
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
                raise Invalid(field.schema, f"Invalid pstruct: {exc}")
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
    template = "opensipkd.base:./widgets/templates/blok_kav_no.pt"
    readonly_template = "opensipkd.base:./widgets/templates/readonly/blok_kav_no.pt"

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
                raise Invalid(field.schema, f"Invalid pstruct: {exc}")
            blok_kav_no = validated["blok_kav_no"]
            rt = validated["rt"]
            rw = validated["rw"]

            if not blok_kav_no and not rt and not rw:
                return null

            result = "|".join([blok_kav_no, rt, rw])

            if not rt or not rt.isdigit() or len(rt) < 3:
                raise Invalid(
                    field.schema, "RT harus angka. Minimal 000", result)

            if not rw or not rw.isdigit() or len(rw) < 2:
                raise Invalid(
                    field.schema, "RW harus angka. Minimal 00", result)

            # if not blok_kav_no or not rt or not rw:
            #     raise Invalid(field.schema, "Blok Kav No RT/RW tidak lengkap",
            #                   result)

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

    url = ""
    slave = ""
    template = "select2_ms.pt"


class AutocompleteMsInputWidget(AutocompleteInputWidget):
    """
    Renders ``<select>`` field based on a predefined set of values using
    `select2 <https://select2.org/>`_ library.

    **Attributes/Arguments**

    Same as :func:`~deform.widget.Select2Widget`, with some extra options
    listed here.
    url: url for slave select
    slave: id of slave  select
    widget = widget_os.AutocompleteMsInputWidget(url="https://slave_item_url?item_key=selected_value,
                                        slave="slave_id")

    Saat ini untuk slave baru bisa ke select2ms atau select2 atau select

    """

    url = ""
    slave = ""
    template = "autocomplete_input_ms"

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="auto_id"),
        SchemaNode(_StrippedString(), name="auto_value"),
    )

    def serialize(self, field, cstruct, **kw):
        if "delay" in kw or getattr(self, "delay", None):
            raise ValueError(
                "AutocompleteWidget does not support *delay* parameter "
                "any longer."
            )

        if cstruct is null:
            auto_id = ""
            auto_value = ""
        else:
            auto_id, auto_value = cstruct.split("|", 2)

        kw.setdefault("auto_id", auto_id)
        kw.setdefault("auto_value", auto_value)
        self.values = self.values or []
        readonly = kw.get("readonly", self.readonly)

        options = {}
        if isinstance(self.values, str):
            options["remote"] = "%s?term=%%QUERY" % self.values
        else:
            # vals = []
            # for v in self.values:
            #     if not isinstance(v, str):
            #         vals.append(v[1])
            # if not vals:
            # vals = self.values

            options["local"] = self.values

        options["minLength"] = kw.pop("min_length", self.min_length)
        options["limit"] = kw.pop("items", self.items)
        kw["options"] = json.dumps(options)
        kw["data"] = self.values

        template = readonly and self.readonly_template or self.template
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, "Invalid pstruct: %s" % exc)
            auto_id = validated["auto_id"]
            auto_value = validated["auto_value"]

            if not auto_id and not auto_value:
                return null

            result = "|".join([auto_id, auto_value])
            if not auto_id or not auto_value:
                raise Invalid(field.schema, _("Incomplete Data"), result)

            return result


class QtyWidget(Widget):
    template = "opensipkd.base:/widgets/templates/qty.pt"
    readonly_template = "opensipkd.base:/widgets/templates/readonly/qty.pt"

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
                raise Invalid(field.schema, f"Invalid pstruct: {exc}")
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

    template = "opensipkd.base:widgets/templates/captcha.pt"
    readonly_template = "opensipkd.base:widgets/templates/captcha.pt"
    strip = True
    requirements = ()
    request = None
    url = ""

    # def __init__(self, **kw):
    #     super(CaptchaWidget, self).__init__(**kw)

    def serialize(self, field, cstruct, **kw):
        file_name = ""
        # if not cstruct:
        request = field.parent.schema.request
        kode_captcha, file_name = img_captcha(request)
        request.session["captcha_code"] = kode_captcha
        _logging.debug("Generated captcha code: %s", kode_captcha)
        _logging.debug(self.request.session.items())

        # cstruct = cstruct or self.url+file_name
        cstruct = self.url+file_name
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        elif not isinstance(pstruct, str):
            raise Invalid(field.schema, "Pstruct is not a string")
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null

        captcha_session = self.request.session.get("captcha_code", "")
        if captcha_session:
            captcha_message = "Captcha tidak sesuai"
            if pstruct != captcha_session:
                _logging.error(
                    "Captcha tidak sesuai terkirim: %s session %s", pstruct, captcha_session)
                _logging.error(self.request.session.items())
                self.request.session.pop("captcha_code", None)
                raise Invalid(field.schema, msg=captcha_message)
        else:
            captcha_message = "Captcha tidak ditemukan"
            _logging.error("Captcha session not found for input: %s", pstruct)
            _logging.error(self.request.session.items())

            raise Invalid(field.schema, msg=captcha_message)

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

    template = "opensipkd.base:/widgets/templates/image.pt"
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
        elif not isinstance(pstruct, str):
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

    template = "opensipkd.base:/widgets/templates/gmap.pt"
    readonly_template = "opensipkd.base:/widgets/templates/gmap.pt"
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
        _logging.debug(self.gmap_data_style)
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
        _logging.debug(self.gmap_data_style)

        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        elif not isinstance(pstruct, str):
            raise Invalid(field.schema, "Pstruct is not a string")
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct


# class LeafMapWidget(Widget):
#     """
#     Renders an ``<div id="map"/>`` widget.

#     **Attributes/Arguments**

#     template
#        The template name used to render the widget.  Default:
#         ``textinput``.

#     readonly_template
#         The template name used to render the widget in read-only mode.
#         Default: ``readonly/textinput``.

#     strip
#         If true, during deserialization, strip the value of leading
#         and trailing whitespace (default ``True``).

#     """

#     template = "opensipkd.base:views/widgets/leafmap.pt"
#     readonly_template = "opensipkd.base:views/widgets/readonly/leafmap.pt"
#     map_center = [0, 0]
#     map_zoom = 12
#     # gmap_control = ['Point', 'Polygon', 'LineString']
#     map_height = "400px"
#     map_width = "100%"
#     strip = True
#     html_info = {}
#     # gmap_data_style = {
#     #     "editable": True,
#     #     "draggable": True,
#     #     "clickable": True,
#     #     "removable": True,
#     # }
#     # gmap_edit_url = ""
#     show_options = True
#     requirements = (
#         ('deform', None),
#         {
#             "js": ["opensipkd.base:static/v3/map/leaflet/leaflet.js",
#                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/0.4.2/leaflet.draw.js"],
#             "css": ["opensipkd.base:static/v3/map/leaflet/leaflet.css",
#                     "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/0.4.2/leaflet.draw.css"],
#         })

#     def __init__(self, **kw):
#         super().__init__(**kw)
#         # _logging.info(self.gmap_data_style)
#         # self.gmap_data_style = json.dumps(self.gmap_data_style)

#     def serialize(self, field, cstruct, **kw):
#         if cstruct in (null, None):
#             cstruct = ""
#         readonly = kw.get("readonly", self.readonly)
#         template = readonly and self.readonly_template or self.template
#         # _logging.debug(self.gmap_data_style)
#         # if readonly:
#         gmap_data_style = {
#             "editable": not readonly,
#             "draggable": not readonly,
#             "clickable": True,
#             "removable": not readonly,
#         }
#         # self.gmap_data_style = json.dumps(gmap_data_style)
#         # _logging.info(self.gmap_data_style)

#         values = self.get_template_values(field, cstruct, kw)
#         return field.renderer(template, **values)

#     def deserialize(self, field, pstruct):
#         if pstruct is null:
#             return null
#         elif not isinstance(pstruct, str):
#             raise Invalid(field.schema, "Pstruct is not a string")
#         if self.strip:
#             pstruct = pstruct.strip()
#         if not pstruct:
#             return null
#         return pstruct


class BootStrapDateInputWidget(Widget):
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
    template = "bootstrapdateinput"
    readonly_template = "readonly/textinput"
    type_name = "text"
    req_path = "opensipkd.base:static/v3/js/plugin"
    requirements = (
        ('deform', None),
        {
            "js": (
                f"{req_path}/bootstrap-datepicker/js/bootstrap-datepicker.min.js",
                f"{req_path}/bootstrap-timepicker/bootstrap-timepicker.min.js",
                f"{req_path}/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
            ),
            "css": (
                f"{req_path}/bootstrap-datepicker/css/bootstrap-datepicker.min.css",
                # f"{req_path}/bootstrap-timepicker/css/bootstrap-timepicker.min.css",
                f"{req_path}/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
            ),
        }
    )
    default_options = (
        ("format", "yyyy-mm-dd"),
        ("zIndexOffset", "910"),

    )
    # ("selectMonths", True),
    # ("selectYears", True),
    options = None

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="date"),
        SchemaNode(_StrippedString(), name="date_submit", missing=""),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        options = dict(
            kw.get("options") or self.options or self.default_options
        )
        options["formatSubmit"] = "yyyy-mm-dd"
        kw.setdefault("options_json", json.dumps(options))
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct in ("", null):
            return null
        try:
            _logging.debug(f"Date:{self._pstruct_schema}")
            validated = self._pstruct_schema.deserialize(pstruct)
        except Invalid as exc:
            raise Invalid(field.schema, "Invalid pstruct: %s" % exc)
        return validated["date_submit"] or validated["date"]


class BootStrapDateTimeInputWidget(Widget):
    """
    Renders a datetime picker widget.

    The default rendering is as a pair of inputs (a date and a time) using
    pickadate.js (https://github.com/amsul/pickadate.js).

    Used for ``colander.DateTime`` schema nodes.

    **Attributes/Arguments**

    date_options
        A dictionary of date options passed to pickadate.

    time_options
        A dictionary of time options passed to pickadate.

    template
        The template name used to render the widget.  Default:
        ``dateinput``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/textinput``.
    """

    template = "datetimeinput"
    readonly_template = "readonly/datetimeinput"
    type_name = "datetime"
    requirements = (("modernizr", None), ("pickadate", None))
    default_date_options = (
        ("format", "yyyy-mm-dd"),
        ("selectMonths", True),
        ("selectYears", True),
    )
    date_options = None
    default_time_options = (("format", "h:i A"), ("interval", 30))
    time_options = None

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="date"),
        SchemaNode(_StrippedString(), name="time"),
        SchemaNode(_StrippedString(), name="date_submit", missing=""),
        SchemaNode(_StrippedString(), name="time_submit", missing=""),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        if cstruct:
            parsed = ISO8601_REGEX.match(cstruct)
            if parsed:  # strip timezone if it's there
                timezone = parsed.groupdict()["timezone"]
                if timezone and cstruct.endswith(timezone):
                    cstruct = cstruct[: -len(timezone)]

        try:
            date, time = cstruct.split("T", 1)
            try:
                # get rid of milliseconds
                time, _ = time.split(".", 1)
            except ValueError:
                pass
            kw["date"], kw["time"] = date, time
        except ValueError:  # need more than one item to unpack
            kw["date"] = kw["time"] = ""

        date_options = dict(
            kw.get("date_options")
            or self.date_options
            or self.default_date_options
        )
        date_options["formatSubmit"] = "yyyy-mm-dd"
        kw["date_options_json"] = json.dumps(date_options)

        time_options = dict(
            kw.get("time_options")
            or self.time_options
            or self.default_time_options
        )
        time_options["formatSubmit"] = "HH:i"
        kw["time_options_json"] = json.dumps(time_options)

        values = self.get_template_values(field, cstruct, kw)
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, "Invalid pstruct: %s" % exc)
            # seriously pickadate?  oh.  right.  i forgot.  you're javascript.
            date = validated["date_submit"] or validated["date"]
            time = validated["time_submit"] or validated["time"]

            if not time and not date:
                return null

            result = "T".join([date, time])

            if not date:
                raise Invalid(field.schema, _("Incomplete date"), result)

            if not time:
                raise Invalid(field.schema, _("Incomplete time"), result)

            return result


class TextInputWidget(widget.TextInputWidget):
    template = "textinput_btn"
    button = None
    js = None

    def __init__(self, **kw):
        super(TextInputWidget, self).__init__(**kw)

        # if isinstance(self.button, compat.str):
        if self.button:
            if isinstance(self.button, str):
                self.button = Button(self.button, type="button")


class DateInputWidget(WidgetDateInputWidget):
    type_name = "text"


class MoneyInputWidget(widget.MoneyInputWidget):
    readonly_template = "readonly/moneyinput.pt"

    def get_template_values(self, field, cstruct, kw):
        options = json.loads(kw.get("mask_options", "{}"))
        if options:
            decimal = options.get("decimal", '.')
            precision = options.get("precision", 2)
            thousands = options.get("thousands", ',')
            cstr = cstruct and float(cstruct) or 0
            cstruct = f"{cstr:,.{precision}f}"\
                .replace(".", "%")\
                .replace(",", thousands)\
                .replace("%", decimal)

        values = {"cstruct": cstruct, "field": field}
        values.update(kw)
        values.pop("template", None)
        return values


class FilterWidget(Widget):
    template = "opensipkd.base:/views/widgets/filters.pt"
    readonly_template = "opensipkd.base:/views/widgets/readonly/filters.pt"
    null_value = ""
    values = ()
    size = None
    multiple = False
    optgroup_class = OptGroup
    long_label_generator = None
    selectize_options = None
    default_selectize_options = (("allowEmptyOption", True),)

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="fields"),
        SchemaNode(_StrippedString(), name="equality"),
        SchemaNode(_StrippedString(), name="nilai"),
        SchemaNode(_StrippedString(), name="condition"),
    )

    def get_select_value(self, cstruct, value):
        """Choose whether <opt> is selected or not.

        Incoming value is always string, as it has been passed through HTML.
        However, our values might be given as integer, UUID.
        """

        if self.multiple:
            if value in map(str, cstruct): # text_type
                return "selected"
        else:
            if value == str(cstruct): #text_type
                return "selected"
        return None

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            condition = ""
            fields = ""
            equality = ""
            nilai = ""
        else:
            fields, equality, nilai, condition = cstruct.split(".", 4)
        # if cstruct in (null, None):
        #     cstruct = self.null_value
        kw.setdefault("condition", condition)
        kw.setdefault("fields", fields)
        kw.setdefault("equality", equality)
        kw.setdefault("nilai", nilai)

        readonly = kw.get("readonly", self.readonly)
        values = kw.get("values", self.values)
        if not isinstance(values, sequence_types):
            e = "Values must be a sequence type (list, tuple, or range)."
            raise TypeError(e)

        template = readonly and self.readonly_template or self.template
        kw["values"] = _normalize_choices(values)
        selectize_options = dict(
            kw.get("selectize_options")
            or self.selectize_options
            or self.default_selectize_options
        )
        kw["selectize_options_json"] = json.dumps(selectize_options)
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, f"Invalid pstruct: {exc}")
            condition = validated["condition"]
            fields = validated["fields"]
            equality = validated["equality"]
            nilai = validated["nilai"]

            # if not year and not bundle and not seq:
            #     return null
            #
            # if self.assume_y2k and len(year) == 2:
            #     year = "20" + year
            result = ".".join([fields, equality, nilai, condition])
            #
            # if not year or not bundle or not seq:
            #     raise Invalid(field.schema, "No Dokumen tidak lengkap", result)

            return result

# class AutocompleteInputWidget(widget.AutocompleteInputWidget):
#     targets = None
# def serialize(self, field, cstruct, **kw):
#     item_id = kw.get("item_id", None)
#     super().serialize(field, cstruct, **kw)
#     if "delay" in kw or getattr(self, "delay", None):
#         raise ValueError(
#             "AutocompleteWidget does not support *delay* parameter "
#             "any longer."
#         )
#     if cstruct in (null, None):
#         cstruct = ""
#     self.values = self.values or []
#     readonly = kw.get("readonly", self.readonly)
#
#     options = {}
#     if isinstance(self.values, str):
#         options["remote"] = "%s?term=%%QUERY" % self.values
#     else:
#         options["local"] = self.values
#
#     options["minLength"] = kw.pop("min_length", self.min_length)
#     options["limit"] = kw.pop("items", self.items)
#     kw["options"] = json.dumps(options)
#     tmpl_values = self.get_template_values(field, cstruct, kw)
#     template = readonly and self.readonly_template or self.template
#     return field.renderer(template, **tmpl_values)
#


class CSRFWidget(widget.HiddenWidget):

    def serialize(self, field, cstruct, **kw):
        request = field.parent.schema.request
        cstruct = get_csrf_token(request)
        if not cstruct:
            cstruct = new_csrf_token(request)
        values = self.get_template_values(field, cstruct, kw)
        _logging.debug("CSRF Token session: %s", cstruct)
        return field.renderer(self.template, **values)

    def deserialize(self, field, pstruct):
        request = field.parent.schema.request
        cstruct = get_csrf_token(request)
        if pstruct is null:
            return null
        elif not isinstance(pstruct, str):
            raise Invalid(field.schema, "Pstruct is not a string")
        if not pstruct:
            return null
        _logging.debug("CSRF Token received: %s", pstruct)
        _logging.debug("CSRF Token session: %s", cstruct)
        return pstruct
