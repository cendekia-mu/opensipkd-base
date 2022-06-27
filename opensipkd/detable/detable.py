"""Form."""
# Standard Library
import json
import re
import logging

import colander
from chameleon.utils import Markup
from deform import compat
from deform import field
from . import widget

log = logging.getLogger(__name__)


class DeTable(field.Field):
    """
    Field representing an entire form.

    Arguments:

    schema
        A :class:`colander.SchemaNode` object representing a
        schema to be rendered.  Required.

    action
        The table action (inserted into the ``ajax_url`` attribute of
        the datatable's scripts tag when rendered).  Required.

    # method
    #     The form method (inserted into the ``method`` attribute of
    #     the form's form tag when rendered).  Default: ``POST``.

    buttons
        A sequence of strings or :class:`deform.form.Button`
        objects representing submit buttons that will be placed at
        the bottom of the form.  If any string is passed in the
        sequence, it is converted to
        :class:`deform.form.Button` objects.

    tableid
        The identifier for this table.  This value will be used as the
        HTML ``id`` attribute of the rendered HTML table.  You should
        pass a string value for ``tableid`` when more than one Detable
        table is placed into a single page and both share the same action.
        When one of the tables on the page is posted, your code will to
        be able to decide which of those tables was posted based on the
         differing values of ``__tableid__``.  By default,
          ``tableid`` is ``detable``.

    use_ajax
       If this option is ``True``, the form will use AJAX (actually
       AJAH); when any submit button is clicked, the DOM node related
       to this form will be replaced with the result of the form post
       caused by the submission.  The page will not be reloaded.  This
       feature uses the ``jquery.form`` library ``ajaxForm`` feature
       as per `http://jquery.malsup.com/form/
       <http://jquery.malsup.com/form/>`_.  Default: ``False``.  If
       this option is ``True``, the ``jquery.form.js`` library must be
       loaded in the HTML page which embeds the form.  A copy of it
       exists in the ``static`` directory of the ``deform`` package.

    ajax_options
       A *string* which must represent a JavaScript object
       (dictionary) of extra AJAX options as per
       `http://jquery.malsup.com/form/#tab3
       <http://jquery.malsup.com/form/#tab3>`_.  For
       example:

       .. code-block:: python

           '{"success": function (rText, sText, xhr, form) {alert(sText)};}'

       Default options exist even if ``ajax_options`` is not provided.
       By default, ``target`` points at the DOM node representing the
       form and and ``replaceTarget`` is ``true``.

       A success handler calls the ``deform.processCallbacks`` method
       that will ajaxify the newly written form again.  If you pass
       these values in ``ajax_options``, the defaults will be
       overridden.  If you want to override the success handler, don't
       forget to call ``deform.processCallbacks``, otherwise
       subsequent form submissions won't be submitted via AJAX.

       This option has no effect when ``use_ajax`` is False.

       The default value of ``ajax_options`` is a string
       representation of the empty object.

    The :class:`deform.Form` constructor also accepts all the keyword
    arguments accepted by the :class:`deform.Field` class.  These
    keywords mean the same thing in the context of a Form as they do
    in the context of a Field (a Form is just another kind of Field).
    """

    css_class = "deform"  # bw compat only; pass a widget to override

    def __init__(
            self,
            schema,
            action,
            action_suffix='/grid/act',
            buttons=(),
            tableid="detable",
            sorts='true',
            filters='true',
            paginates='true',
            params="",
            # ajax_options="{}",
            # autocomplete=None,
            # focus="on",
            # cols = None,
            **kw
    ):
        params = params and f"?{params}" or ""
        btn_close_js = "{window.location = '/'; return false;}"
        btn_add_js = "{window.location = o%sUri+'/add%s';}" % (tableid, params)
        btn_edit_js = "{window.location = o%sUri+'/'+m%sID+'/edit%s'}" % (tableid, tableid, params)
        btn_view_js = "{window.location = o%sUri+'/'+m%sID+'/view%s';}" % (tableid, tableid, params)
        btn_delete_js = "{window.location = o%sUri+'/'+m%sID+'/delete%s';}" % (tableid, tableid, params)
        btn_csv_js = "{window.location = o%sUri+'/csv/act%s';}" % (tableid, params)
        btn_pdf_js = "{window.open(o%sUri+'/pdf/act%s');}" % (tableid, params)
        action_suffix = f"{action_suffix}{params}"
        field.Field.__init__(self, schema, **kw)
        _buttons = []
        for button in buttons:
            if isinstance(button, compat.string_types):
                button = Button(button)
            _buttons.append(button)
        buttons = _buttons
        _buttons = []
        _scripts = []
        for button in buttons:
            _buttons.append(
                f"""<button 
                    id="{tableid}{button.name}" 
                    name="{button.name}" 
                    type="{button.type}" 
                    class="btn {button.css_class}"> 
                        {button.title} </button>\n
                    """)
            _scripts.append(f'$("#{tableid + button.name}").click(function ()' +
                            eval('btn_' + button.name + '_js') + ');')
            # <span tal:condition="button.icon" class="glyphicon glyphicon-${button.icon}"></span>

        self.buttons = "','".join(_buttons).replace('\n', "").replace(';', ';\n')
        self.tableid = tableid
        self.scripts = ''.join(_scripts).replace(';', ";\n")
        table_widget = getattr(schema, "widget", None)
        if table_widget is None:
            table_widget = widget.TableWidget()
        self.widget = table_widget
        columns = []
        cols2 = []
        for f in schema:
            d = {'data': f.name}
            data = []

            if hasattr(f, 'width'):
                d["width"] = f.width
                data.append(f"width: '{f.width}'")

            if hasattr(f, 'aligned'):
                d["className"] = f.aligned
                data.append(f"className: '{f.aligned}'")
            if hasattr(f, 'searchable'):
                d["searchable"] = f.searchable
                data.append(f"searchable: {f.searchable}")

            if hasattr(f, 'visible'):
                d["visible"] = f.visible
                data.append(f"visible: {f.visible}")

            if hasattr(f, 'orderable'):
                d["orderable"] = f.orderable
                data.append(f"orderable: {f.orderable}")

            thousand = hasattr(f, 'thousand') and f.thousand or None
            separator = thousand and "separator" in thousand and thousand["separator"] or ','
            decimal = thousand and "decimal" in thousand and thousand["decimal"] or '.'
            point = thousand and "point" in thousand and thousand["point"] or 2
            currency = thousand and "currency" in thousand and thousand["currency"] or ""
            if thousand or type(f.typ) == colander.Float() or type(f.typ) == colander.Integer():
                d[
                    "render"] = f"<script>$.fn.dataTable.render.number( '{separator}', '{decimal}', {point}, '{currency}' )</script>"
                if 'className' not in d:
                    d["className"] = "text-right"
            # if hasattr(f, "edit_link"):
            #     s = """function ( data, type, row, meta ) {
            #                     return '<a href="'+data+'">Download</a>';
            #                     }"""
            #     d["render"] = s

            columns.append(d)
            cols2.append(data)
        # columns.append(dict(title="Action",
        #                     data='id',
        #                     width="40pt",
        #                     orderable=False,
        #                     align="text-center",
        #                     searchable=False))
        self.columns = json.dumps(columns)
        self.columns = self.columns.replace('"<script>', "").replace('</script>"', "").replace("\n", "")
        # self.columns = columns
        # self.columns = json.dumps(cols2)
        self.url = action
        self.url_suffix = action_suffix
        self.sorts = sorts
        self.paginates = paginates
        self.filters = filters


class Button(object):
    """
    A class representing a form submit button.  A sequence of
    :class:`deform.widget.Button` objects may be passed to the
    constructor of a :class:`deform.form.Form` class when it is
    created to represent the buttons renderered at the bottom of the
    form.

    Arguments:

    name
        The string or unicode value used as the ``name`` of the button
        when rendered (the ``name`` attribute of the button or input
        tag resulting from a form rendering).  Default: ``submit``.

    title
        The value used as the title of the button when rendered (shows
        up in the button inner text).  Default: capitalization of
        whatever is passed as ``name``.  E.g. if ``name`` is passed as
        ``submit``, ``title`` will be ``Submit``.

    type
        The value used as the type of button. The HTML spec supports
        ``submit``, ``reset`` and ``button``.  A special value of
        ``link`` will create a regular HTML link that's styled to look
        like a button.  Default: ``submit``.

    value
        The value used as the value of the button when rendered (the
        ``value`` attribute of the button or input tag resulting from
        a form rendering).  If the button ``type`` is ``link`` then
        this setting is used as the URL for the link button.
        Default: same as ``name`` passed.

    icon
        glyph icon name to include as part of button.  (Ex. If you
        wanted to add the glyphicon-plus to this button then you'd pass
        in a value of ``plus``)  Default: ``None`` (no icon is added)

    disabled
        Render the button as disabled if True.

    css_class
        The name of a CSS class to attach to the button. In the default
        form rendering, this string will replace the default button type
        (either ``btn-primary`` or ``btn-default``) on the the ``class``
        attribute of the button. For example, if ``css_class`` was
        ``btn-danger`` then the resulting default class becomes
        ``btn btn-danger``. Default: ``None`` (use default class).

    attributes
        HTML5 attributes passed in as a dictionary. This is especially
        useful for a Cancel button where you do not want the client to
        validate the form inputs, for example
        ``attributes={"formnovalidate": "formnovalidate"}``.
    """

    def __init__(
            self,
            name="view",
            oid=None,
            title=None,
            type="button",  # noQA
            css_class=None,
            icon=None,
            attributes=None,
            disabled=None
    ):
        if attributes is None:
            attributes = {}
        if title is None:
            title = name.capitalize()
        name = re.sub(r"\s", "_", name)
        if oid is None:
            self.oid = f"detable_btn_{name}"
        self.name = name
        self.title = title
        self.type = type  # noQA
        self.disabled = disabled
        self.css_class = css_class
        self.icon = icon
        self.attributes = attributes
