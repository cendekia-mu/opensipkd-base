"""Form."""
# Standard Library
import json
import logging
import re

import colander
# import deform
from deform import compat, widget as deform_widget, field

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
            server_side=True,
            state_save=True,
            data=[],
            allow_edit=True,
            allow_delete=True,
            allow_view=True,
            allow_post=False,
            allow_unpost=False,
            allow_check=False,
            check_field=False,
            filter_columns=False,
            scroll_x=False,
            scroll_y=False,
            **kw
    ):
        kw.pop("parent", None)
        super().__init__(schema, **kw)
        self.request = kw.get("request")
        self.rows = kw.get("rows")
        self.action = action
        self.tableid = tableid
        self.data = data
        self.allow_edit = json.dumps(allow_edit)
        self.allow_delete = json.dumps(allow_delete)
        self.allow_view = json.dumps(allow_view)
        self.allow_post = json.dumps(allow_post)
        self.allow_unpost = json.dumps(allow_unpost)
        self.allow_check = json.dumps(allow_check)
        self.check_field = json.dumps(check_field)
        self.filter_columns = filter_columns
        self.scroll_x = json.dumps(scroll_x)
        self.scroll_y = json.dumps(scroll_y)

        # self.widget = None
        # Button yang dikirim sebagai tambahan
        html_buttons = kw.get("html_buttons", None)
        new_buttons = kw.get("new_buttons") or {}
        action_suffix = f"{action_suffix}{params}"

        close_url = self.action
        if close_url[:4] != "http":
            close_url = self.action.split("/")
            close_url = "/".join(close_url[:-1])
            close_url.replace(":/", "://")
        params = params and f"?{params}" or ""
        dict_buttons = {
            "close": "{window.location = '" + close_url + "'; return false;}",
            "add": "{window.location = o%sUri+'/add%s';}" % (tableid, params),
            "edit": """{
                if (m%sID) window.location = o%sUri+'/'+m%sID+'/edit%s';
                else alert('Pilih Baris');
                }""" % (tableid, tableid, tableid, params),
            "view": "{window.location = o%sUri+'/'+m%sID+'/view%s';}" % (
                tableid, tableid, params),
            "delete": not self.allow_check and "{window.location = o%sUri+'/'+m%sID+'/delete%s';}" % (
                tableid, tableid, params) or
            """{
                        var cnt = m%sCheckList.length;
                        if (cnt > 0){
                        if (confirm('Menghapus '+cnt+' data, pastikan data yang dipilih sudah benar!')){
                            ids = m%sCheckList.join(',');
                            window.location = o%sUri+'/all/delete?ids='+ids;
                        };
                        }else{ alert('Pilih Baris'); }

                        event.stopPropagation();
                    }""" % (tableid, tableid, tableid),
            "csv": "{window.location = o%sUri+'/csv/act%s';}" % (
                tableid, params),
            "pdf": "{window.open(o%sUri+'/pdf/act%s');}" % (tableid, params),
            "upload": "{window.location = o%sUri+'/upload%s';}" % (
                tableid, params),
        }

        for k in new_buttons:
            buttons += (new_buttons[k]["obj"],)
            dict_buttons[k] = '{' + new_buttons[k]["js"].format(tableid=tableid,
                                                                params=params) + '}'

        obj_buttons = []  # Adalah Header Buttone
        _scripts = []
        # buttons = Params Buttons
        for button in buttons:
            if isinstance(button, compat.string_types):
                button = Button(button)
            obj_buttons.append(button)
        header_buttons = []
        for button in obj_buttons:
            header_buttons.append(
                f"""<button 
                    id="{tableid}{button.name}" 
                    name="{button.name}" 
                    type="{button.type}" 
                    class="btn {button.css_class}"> 
                        {button.title} </button>\n
                    """)
            if dict_buttons.get(button.name):
                _scripts.append(f'$("#{tableid + button.name}").click(function ()' +
                                dict_buttons[button.name] + ');')
            else:
                url = "{window.location = o%sUri+'/" % tableid
                url += f"{button.name}';"+"}"
                _scripts.append(f'$("#{tableid + button.name}").click(function ()' +
                                url +
                                ');')

        if html_buttons:
            for html in html_buttons:
                header_buttons.append(html["obj"])
                _scripts.append(html["js"])

        if filter_columns:
            button = f"""
                        <a href="#{tableid}-form-filter"
                            data-toggle="collapse"
                            class= "btn btn-warning dropdown">Filters</a>
                    """
            header_buttons.insert(0, button)
        edit_buttons = []
        # if allow_check:
        #     button = f"""
        #     <input type="checkbox" class="{tableid}checkAll form-control"> All</input>
        #     """
        #     edit_buttons.append(button)

        self.buttons = "','".join(header_buttons).replace('\n', ""). \
            replace(';', ';\n')
        self.edit_buttons = "','".join(edit_buttons).replace('\n', ""). \
            replace(';', ';\n')
        self.tableid = tableid
        self.scripts = ''.join(_scripts).replace(';', ";\n")

        table_widget = getattr(schema, "widget", None)
        if table_widget is None:
            table_widget = widget.TableWidget()

        self.widget = table_widget
        self.server_side = json.dumps(server_side)
        self.data = data
        columns = []
        headers = []
        cols2 = []

        filter_form = ""
        field_index = 0
        filter_scripts = ""
        for f in schema:
            field_index += 1
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

            if hasattr(f, "url"):
                d["url"] = f.url
            #     # request = kw.get("request")
            #     # if request:
            #     #     d["url"] = request.static_url(f.url)
            #     #     log.debug(d["url"])

            if hasattr(f, "action"):
                d["action"] = f.action
            else:
                d["action"] = True
            if hasattr(f, "search_method"):
                d["search_method"] = f.search_method

            if isinstance(f.widget, deform_widget.HiddenWidget):
                d["visible"] = False
            elif isinstance(f.widget, deform_widget.CheckboxWidget):
                d.update(self.widget_checkbox(f))
            elif isinstance(f.widget, deform_widget.SelectWidget):
                d.update(self.widget_select(f))
            else:
                d["wg_checkbox"] = False
                d["wg_select"] = False
            if hasattr(f, "url"):
                url = f.url
                d["render"] = """
                    function(data){
                        let result = "No Data"
                        if (data != null)
                            result = '<a href="' + url + data + '" target="_blank">Link</a>&nbsp;';
                        return result;
                    }"""
            if f.name == "id" and self.action:
                if not d.get("orderable"):
                    d["orderable"] = True
                d["width"] = "30pt"
                d["className"] = "text-center"
                d["visible"] = True
                d["render"] = """
                function (id) {
                                        
                    return %s;
                    }
                """ % self.action_url(f)

            if filter_columns and hasattr(f, "searchable") and getattr(f, "searchable"):
                filter_form += self.get_filter_form(f, field_index)

            # if type(f.typ) == colander.Integer:
            #     d["field_typ"] = f"int"
            # elif type(f.typ) == colander.Boolean:
            #     d["field_typ"] = f"bool"
            # elif type(f.typ) in (colander.Float, colander.Money):
            #     d["field_typ"] = f"float"
            # else:
            #     d["field_typ"] = f"str"

            thousand = hasattr(f, 'thousand') and f.thousand or None
            separator = thousand and "separator" in thousand \
                and thousand["separator"] or ','
            decimal = thousand and "decimal" in thousand and thousand[
                "decimal"] or '.'
            point = thousand and thousand.get("point", 0) or 0
            point = thousand and thousand.get("precision", point) or point
            currency = thousand and "currency" in thousand and \
                thousand["currency"] or ""
            if thousand or isinstance(f.typ, colander.Float) or \
                    isinstance(f.typ, colander.Integer):
                d["render"] = \
                    f"<script>$.fn.dataTable.render.number( '{separator}', " \
                    f"'{decimal}', {point}, '{currency}' )</script>"
                if 'className' not in d:
                    d["className"] = "text-right"

            columns.append(d)
            headers.append(f.title)
            # cols2.append(data)
            filter_scripts = self.get_filter_scripts(f)

        self.filter_scripts = filter_scripts

        self.filter_form = filter_form

        self.headers = headers
        self.head = headers
        self.columns = json.dumps(columns)
        self.columns = self.columns.replace('"<script>', "").replace(
            '</script>"', "").replace("\n", "")
        self.url = action
        self.url_suffix = action_suffix
        self.sorts = sorts
        self.paginates = paginates
        self.filters = filters
        self.state_save = json.dumps(state_save)

    def widget_checkbox(self, column):
        d = {}
        d["wg_checkbox"] = True
        d["wg_checkbox_val"] = [column.widget.true_val, column.widget.false_val]
        d["className"] = "text-center"
        d["width"] = "30pt"
        # d["render"] = """
        #   function(value){
        #     if (typeof value == = "string" & & value.length > 0)
        #         return render_checkbox(value)
        #     if (["", false, 0, null].indexOf(value) === -1)
        #         return render_checkbox(true);
        #
        #     return render_checkbox(false);
        #   }"""

        return d

    def widget_select(self, column):
        d = {}
        d["wg_select"] = True
        d["wg_select_val"] = type(column.widget.values) == list and dict(
            column.widget.values) or column.widget.values
        if column.widget.values:
            for val in column.widget.values:
                if hasattr(column, f"color_{val}"):
                    d[f"color_{val}"] = getattr(column, f"color_{val}")
        return d

    def action_url(self, f):
        act = ""
        if self.allow_view:
            act = f"""
                                '<a href="{self.action}/' + id + '/view">'+
                                '<i class="fas fa-eye" aria-hidden="true" title="View"></i></a>';\n
                            """
        if self.allow_edit:
            act += f"""
                                '<a href="{self.action}/' + id + '/edit">'+
                                '<i class="fas fa-edit" aria-hidden="true" title="Edit"></i></a>';\n
                            """
        if self.allow_delete:
            act += f"""
                                '<a href="{self.action}/' + id + '/delete">'+
                                '<i class="fas fa-trash" aria-hidden="true" title="Delete"></i></a>';\n
                            """
        if self.allow_post:
            act += f"""
                                '<a href="{self.action}/' + id + '/post">'+
                                '<i class="fas fa-signs-post" aria-hidden="true" title="Post"></i></a>';\n
                            """
        if self.allow_unpost:
            act += f"""
                                '<a href="{self.action}/' + id + '/unpost">'+
                                '<i class="fas fa-delete-left" aria-hidden="true" title="Unpost"></i></a>';\n
                            """
        return act

    def get_filter_form(self, f, field_index):
        field_index -= 1
        html = ""
        col_id = f"{self.tableid}-{f.name}"
        txt = f'id="{col_id}" data-index={field_index} '
        html += '<div class="form-group">'
        if isinstance(f.widget, deform_widget.CheckboxWidget):
            wg_check_val = [f.widget.true_val, f.widget.false_val]
            radio_val = [["", 'Semua'], [wg_check_val[0],
                                         'Aktif'], [wg_check_val[1], 'Pasif']]
            html += '<label class="" for="' + col_id + '">' + f.title + '</label>'
            html += '<div class="input-group" id="' + col_id + '">'
            for rdo in range(len(radio_val)):
                # selected = (col_val == = radioVal[rdo][0]) ? "checked": "";
                log.debug(f"{rdo}, {radio_val[rdo]}")
                txt = f'id="{col_id}-{radio_val[rdo][0]}" value="{radio_val[rdo][0]}" '
                txt += f'class="{self.tableid}-control-filter" data-index="{field_index}" '
                txt += f'name="{col_id}" '
                html += '<label class="radio-inline">'
                html += f'<input type="radio" {txt}/>'
                html += f'<label for="{col_id}-{radio_val[rdo][0]}">'
                html += f'{radio_val[rdo][1]}</label>'
                html += '</label>'
            html += '</div>'
        elif isinstance(f.widget, deform_widget.SelectWidget):
            wg_select_val = f.widget.values
            html += f'<select class="form-control {self.tableid}-control-filter"'
            html += f'placeholder="{f.title}" {txt}/>'
            html += '<option value="">Semua</option>'
            if type(wg_select_val) == list:
                wg_select_val = dict(wg_select_val)

            for key in wg_select_val:
                html += f'<option value="{key}">{wg_select_val[key]}</option>'
            html += '</select>'

        elif isinstance(f.typ, colander.Date):
            search_method = getattr(f, "search_method", None)
            if search_method == "date":
                # html += f'<div class="tooltip">'
                html += f'<label class="form-label" style="font-size:12px">{f.title}</label>'
                html += f'<input type="date" class="form-control {self.tableid}-control-filter"'
                html += f'{txt}/>'
                # html += f'<span class="tooltiptext">{f.title}</span>'
                # html += f'</div>'
            else:
                html += f'<div class="form-group" {txt}>'
                html += f'<label class="form-label" style="font-size:12px">{f.title}</label>'
                html += f'<div class="input-group input-daterange" style="padding: 3px 0px 7px !important;">'
                html += f'<input type="date" class="form-control {self.tableid}-control-filter hasDatePicker"'
                html += f'data-index={field_index} placeholder="{f.title} Awal"'
                html += f'name="{col_id}" id="{col_id}-min"/>'
                html += f'<div class="input-group-addon">-</div>'
                html += f'<input type="date" class="form-control {self.tableid}-control-filter hasDatePicker"'
                html += f'data-index={field_index} placeholder="{f.title} Akhir" '
                html += f'name="{col_id}" id="{col_id}-max" /></span>'
                html += f'</div>'
                html += f'</div>'
        elif getattr(f, "search_method", None) == "yadcf_range_number":
            html += f'<div class="form-group" {txt}>'
            html += f'<label class="form-label" style="font-size:12px">{f.title}</label>'
            html += f'<div class="input-group" style="padding: 3px 0px 7px !important;">'
            html += f'<input type="number" class="form-control {self.tableid}-control-filter"'
            html += f'data-index={field_index} placeholder="{f.title} Min" '
            html += f'name="{col_id}" id="{col_id}-min"/>'
            html += f'<div class="input-group-addon">-</div>'
            html += f'<input type="number" class="form-control {self.tableid}-control-filter"'
            html += f'data-index={field_index} placeholder="{f.title} Max" '
            html += f'name="{col_id}" id="{col_id}-max" /></span>'
            html += f'</div>'
            html += f'</div>'

        else:
            html += f'<input type="text" class="form-control {self.tableid}-control-filter"'
            html += f'placeholder="{f.title}" {txt}/>'
        html += '</div>'
        return html

    def get_filter_scripts(self, f):
        return ""


"""
for (let co in ${tableid}Columns) {
    if (${tableid}Columns[co].checkbox === true) {

    } else if (${tableid}Columns[co].hasOwnProperty("url")) {

    } else
      ${tableid}Columns[co].width = "30pt";
      ${tableid}Columns[co].orderable = false;
      ${tableid}Columns[co].className = "text-center";
      ${tableid}Columns[co].visible = true;
      //columns[1].order = "order_asc";
    }
"""


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
