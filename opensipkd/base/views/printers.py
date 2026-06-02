from pyramid.httpexceptions import HTTPBadRequest
import logging
import re

import colander
from deform import (widget,)
from pyramid.i18n import TranslationStringFactory
import opensipkd
import platform
import websockets
import json
import os
import asyncio
from opensipkd.base import BASE_CLASS
from opensipkd.tools.buttons import btn_check
from opensipkd.tools import get_random_string
from ..models import TextPrinters, User
from . import BaseView


log = logging.getLogger(__name__)
_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah partner gagal'
SESS_EDIT_FAILED = 'Edit partner gagal'

TEST_PRINT_DATA = \
"""*** TEST PRINT FROM WEB SERVER ***
This is a test print message sent from the server to the client. 

If you see this on your printer, the connection and printing functionality are working
correctly."""


class AddSchema(colander.Schema):
    user_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.SelectWidget(),
        title="User ID",
        global_search=False,
        searchable=True,
        search_method="numeric",
        default=10)
    nama = colander.SchemaNode(
        colander.String(),
        title="Nama Printer",
        validator=colander.Length(max=64),
        global_search=True,
    )
    is_epson = colander.SchemaNode(
        colander.Integer(),
        widget=widget.SelectWidget(),
        title="Printer/Network Type",
        default=0)
    kode = colander.SchemaNode(
        colander.String(),
        title="IP Address",
        widget=widget.TextInputWidget(mask="999.999.999.999",),
        missing="",
        global_search=True,
    )

    port = colander.SchemaNode(
        colander.Integer(),
        title="Port",
        missing=0,
        default=515)

    queue = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        title="Queue Name",
        global_search=True,
        missing="",
        default='lp')
    timeout = colander.SchemaNode(
        colander.Integer(),
        title="Timeout",
        missing=0,
        default=10)

    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        title="Status")

    def after_bind(self, schema, kw):
        schema["kode"].title = "IP Address"
        schema["kode"].widget = widget.TextInputWidget(
            mask="999.999.999.999",  # Use specialized mask format
            mask_mapping={'Z': {'pattern': '[0-9]', 'optional': True}},
        )
        # Use a simple text input for user_id
        schema["user_id"].widget.values = User.get_list()
        schema["user_id"].aligned = "text-left"
        schema["is_epson"].aligned = "text-left"
        epson_values = [
            ("0", "Other"),
            ("1", "Epson Type"),]
        if BASE_CLASS.ws_print_url:
                epson_values.append(("2", "Web Socket"))
        schema["is_epson"].widget.values = epson_values


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class ListSchema(EditSchema):
    def after_bind(self, schema, kw):
        super().after_bind(schema, kw)
        request = kw.get('request')
        if request and not request.has_permission('admin'):
            schema["user_id"].widget = widget.HiddenWidget()
            schema["user_id"].default = request.user.id


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_route = 'base-printer'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = TextPrinters
        self.list_schema = ListSchema
        # self.list_buttons = (btn_delete,)
        self.save_state = True
        self.allow_check = True
        self.list_view_field = 'nama'
        self.filter_columns = True
        self.allow_delete = True
        route_name = request.matched_route.name
        id_ = request.matchdict.get('id')
        if id_ and route_name.endswith('view'):
            import os
            folder = os.path.abspath(opensipkd.base.views.__file__)
            filename = os.path.join(os.path.dirname(
                folder), "js", "printer_form.js")
            url = self.req.route_url(self.list_route)+f'/check/act?id={id_}'
            with open(filename, "r", encoding="utf-8") as f:
                self.form_scripts = f.read() % url

    def list_filter(self, query, **kwargs):
        if not self.req.has_permission('admin'):
            query = query.filter_by(create_uid=self.req.user.id)
        return query

    def form_validator(self, form, value):
        err = {}
        err_format = 'Format IP harus 123.123.123.123'
        found = TextPrinters.query().filter(
            TextPrinters.nama == value['nama'],
            TextPrinters.user_id == value['user_id']
        ).first()
        if found:
            if str(found.id) != self.req.matchdict.get('id'):
                err["nama"] = 'Nama printer sudah digunakan untuk user ini'
        is_epson = value['is_epson']
        if is_epson < 2:
            if not value.get('port'):
                err["port"] = 'Port harus diisi untuk tipe Web Socket'
            if not value.get('queue'):
                err["queue"] = 'Queue harus diisi untuk tipe Web Socket'
            if (not value.get('kode')
                    or not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value['kode'])):
                err["kode"] = 'Kode harus diisi untuk tipe Web Socket'
            else:
                ip = value['kode'].split('.')
                if len(ip) != 4:
                    err["kode"] = err_format+' terdiri dari 4 oktet'
                else:
                    for i in ip:
                        if not i.isdigit():
                            err["kode"] = err_format + \
                                ' setiap oktet harus angka'
                            break
                        if int(i) < 0 or int(i) > 255:
                            err["kode"] = err_format + \
                                ' setiap oktet harus antara 0-255'
                            break
                        if ip[0] == '000':
                            err["kode"] = err_format+' tidak boleh diawali 000'
                            break
        if err:
            exc = colander.Invalid(form, None)
            for key, val in err.items():
                exc[key] = val
            raise exc

    def after_save(self, values, row):
        self.db_session.flush()
        if values['status'] == 1:
            printers = TextPrinters.query().filter_by(create_uid=row.create_uid).all()
            for printer in printers:
                if printer.id == row.id:
                    continue
                printer.status = 0
                self.db_session.add(printer)
        self.db_session.flush()
        return row

    def view_buttons(self, row):
        buttons = super().view_buttons(row)

        buttons += (btn_check,)
        return buttons

    def next_act(self, **kwargs):
        id_ = self.req.GET.get('id')
        try:
            return asyncio.run(print_text(print_id=id_, text="Test Print"))
            # return {'success': True,
            #         'message': "Print job sent successfully."}
        except Exception as e:
            raise HTTPBadRequest(explanation=str(e)) from e


async def print_text(user_id=None, print_id=None, text=None, filename=None,
                     ws_url=BASE_CLASS.ws_print_url):
    if not user_id and not print_id:
        log.error("User ID or Print ID must be provided.")
        raise Exception("User ID or Print ID must be provided.")
    if user_id:
        printer = TextPrinters.query().filter_by(user_id=user_id, status=1).first()
    else:
        printer = TextPrinters.query().filter_by(id=print_id, status=1).first()
    if not printer:
        log.error(
            f"User {user_id} or Print ID {print_id} does not have an active printer configured.")
        raise Exception("No active printer configured for the user.")
    is_ws = printer.is_epson == 2 if printer else False
    timeout = printer.timeout if printer else 10          # Timeout in seconds
    if is_ws:
        printer_name = printer.nama if printer else "unknown"
        printer_name = BASE_CLASS.ws_print_id+'_'+ printer_name
        ws_url = ws_url or BASE_CLASS.ws_print_url
        if not ws_url:
            log.error("WebSocket URL is not configured.")
            raise Exception("WebSocket URL is not configured.")

        try:
            async with websockets.connect(ws_url) as websocket:
                # Send user on connect
                log.info(f"Connected to server at {ws_url} as {printer_name}")
                data = {"login": BASE_CLASS.ws_print_id}
                await websocket.send(json.dumps(data))
                text = await websocket.recv()
                log.info(f"Received from server: {text}")
                # Wait for server to process login

                if filename and os.path.isfile(filename):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in {".prn", ".txt"}:
                        with open(filename, "r", encoding="utf-8") as f:
                            message = f.read()
                    else:
                        with open(filename, "rb") as file:
                            message = file.read()

                else:
                    message = TEST_PRINT_DATA
                data = {"action": "print",
                        "printer": printer_name,
                        "filename": os.path.basename(filename) if filename else "test_print.txt",
                        "message": message
                        }
                await websocket.send(json.dumps(data))
                resp = await websocket.recv()
                data = json.loads(resp)
                if not data.get("status"):
                    log.error(
                        f"Server returned an error: {data.get('message')}")
                    raise Exception(f"Server error: {data.get('message')}")
                # Wait for any response from server
                log.info(f"Received from server: {resp}")
                return data

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            raise Exception(
                f"Failed to connect to WebSocket server: {e}") from e

    # Replace with your printer's IP
    ip = printer.kode if printer else "127.0.0.1"
    ips = ip.split(".")  # Support multiple IPs separated by commas
    # Clean up whitespace and empty entries
    ips = [int(ip.strip()) for ip in ips if ip.strip()]
    hostname = ".".join(map(str, ips)) if ips else "127.0.0.1"
    queue = printer.queue if printer else "lp"          # Common default queue name
    port = printer.port if printer else 515            # Default LPR port
    # Set to True if the printer is an Epson model that requires specific control codes
    is_epson = printer.is_epson == 1 if printer else False
    if not BASE_CLASS.is_pylpr:
        current_os = platform.system().lower()
        if current_os == "windows":
            cmd = 'lpr'
        else:  # Darwin is macOS
            cmd = 'rlpr'
        if text and not filename:
            filename = os.path.join(BASE_CLASS.temp_files,
                                    get_random_string(16) + ".txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
        try:
            import subprocess
            subprocess.run(
                [cmd, f"--printer={queue}@{hostname}:{port}", filename], check=True)
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to print using {cmd}: {e}")
            raise Exception(
                f"Failed to print the document. {e}, {hostname}, {port}, {queue}") from e
        finally:
            if filename and os.path.isfile(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    log.warning(f"Failed to delete temp file {filename}: {e}")
    else:
        from pylpr import LprClient
        with LprClient(
            hostname=hostname,
            port=port,
            timeout=timeout,
            queue=queue,
        ) as lpr:
            if is_epson:
                lpr.send(
                    lpr.EXIT_PACKET_MODE
                    + lpr.INITIALIZE_PRINTER
                    + text.encode('utf-8')
                    + lpr.FF
                )
            else:
                try:
                    lpr.send(text.encode('utf-8'))
                except Exception as e:
                    log.error(f"Failed to send print job: {e}")
                    raise Exception(
                        f"Failed to print the document.  {e}, {hostname}, {port}, {queue}") from e

            lpr.send(text.encode('utf-8'))
