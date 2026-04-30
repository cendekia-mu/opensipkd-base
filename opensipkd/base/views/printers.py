import logging
import re
import colander
from deform import (widget,)
from pyramid.i18n import TranslationStringFactory
from ..models import TextPrinters

from . import BaseView, NamaSchema


log = logging.getLogger(__name__)
_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah partner gagal'
SESS_EDIT_FAILED = 'Edit partner gagal'


def print_text(user, text):
    from opensipkd.base.models import TextPrinters
    printer = TextPrinters.query().filter_by(create_uid=user.id, status=1).first()
    if not printer:
        log.error(
            f"User {user.id} does not have an active printer configured.")
        raise Exception("No active printer configured for the user.")

    # Replace with your printer's IP
    hostname = printer.kode if printer else "127.0.0.1"
    queue = printer.queue if printer else "lp"          # Common default queue name
    port = printer.port if printer else 515            # Default LPR port
    timeout = printer.timeout if printer else 10          # Timeout in seconds
    # Set to True if the printer is an Epson model that requires specific control codes
    is_epson = printer.is_epson if printer else False
    from pylpr import LprClient
    with LprClient(
        hostname=hostname,
        port=port,
        timeout=timeout,
        queue=queue,
        #  recv_buffer=args.recv_buffer,
        #  username=args.username,
        #  job_name=args.job_name,
        #  file_name=getattr(args.print_file, 'name', None) if hasattr(
        #      args, 'print_file') and args.print_file else None,
        #  label=args.label,
        #  use_reserved_port=args.use_reserved_port
        ) as lpr:
        #    if args.print_queue:
        #         # Send the 'Print any waiting jobs' command (0x01) to the specified queue
        #         lpr._send_lpr_command(1, queue.encode('ascii'))
        #         print(
        #             f"Sent 'Print any waiting jobs' command to queue '{args.queue}'")
        #         return
        #     if args.status:
        #         lpr._send_lpr_command(
        #             3, (args.queue + " " + args.status).encode('ascii'), noreceive=True)
        #         print(
        #             f"Sent 'Send queue state (short)' command with attributes '{args.status}' to queue '{args.queue}'")
        #         # Receive and print the response from the printer
        #         response = lpr.receive()
        #         print("Received queue state (short) response:")
        #         print(response.decode('utf-8', errors='replace'))
        #         return
        #     if args.longstatus:
        #         lpr._send_lpr_command(
        #             4, (args.queue + " " + args.longstatus).encode('ascii'), noreceive=True)
        #         print(
        #             f"Sent 'Send queue state (long)' command with attributes '{args.longstatus}' to queue '{args.queue}'")
        #         # Receive and print the response from the printer
        #         response = lpr.receive()
        #         print("Received queue state (long) response:")
        #         print(response.decode('utf-8', errors='replace'))
        #         return
        #     if args.remove:
        #         # Send the 'Remove jobs' command (0x05) to the specified queue
        #         lpr._send_lpr_command(
        #             5, (args.queue + " " + args.remove).encode('ascii'))
        #         print(
        #             f"Sent 'Remove jobs' command with attributes '{args.remove}' to queue '{args.queue}'")
        #         return
            if is_epson:
                lpr.send(
                    lpr.EXIT_PACKET_MODE
                    + lpr.INITIALIZE_PRINTER
                    + text.encode('utf-8')
                    + lpr.FF
                )
            else:
                lpr.send(text.encode('utf-8'))
            # lpr.send(text.encode('utf-8'))

class AddSchema(NamaSchema):
    nama = colander.SchemaNode(
        colander.String(),
        title="Nama Printer",
        validator=colander.Length(max=64)
    )
    kode = colander.SchemaNode(
        colander.String(),
        title="IP Address",
        widget=widget.TextInputWidget(mask="999.999.999.999",))

    port = colander.SchemaNode(
        colander.Integer(),
        title="Port",
        default=515)
    is_epson = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        title="Epson Printer",
        default=0)
    queue = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        title="Queue Name",
        default='lp')
    timeout = colander.SchemaNode(
        colander.Integer(),
        title="Timeout",
        default=10)

    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        title="Status")

    def after_bind(self, schema, kw):
        schema["kode"].title = "IP Address"
        schema["kode"].widget = widget.TextInputWidget(
            mask="999.999.999.999",  # Use specialized mask format
            # If required
            mask_mapping={'Z': {'pattern': '[0-9]', 'optional': True}},
            # css_class='ip_address'
        )
        # schema["kode"].validator = colander.Regex(
        #     r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
        # )


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class ListSchema(EditSchema):
    pass


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

    def list_filter(self, query, **kwargs):
        if not self.req.has_permission('admin'):
            query = query.filter_by(create_uid=self.req.user.id)
        return query

    def form_validator(self, form, value):
        exc = colander.Invalid(form, None)
        ip = value['kode'].split('.')
        err = []
        err_format = 'Format IP salah'
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value['kode']):
            err.append(err_format+' 123.123.123.123')
        if len(ip) != 4:
            err.append(err_format+' harus 4 oktet')
        for i in ip:
            if not i.isdigit():
                err.append(err_format)
            if int(i) < 0 or int(i) > 255:
                err.append(err_format+' setiap oktet harus antara 0-255')
            if ip[0] == '0':
                err.append(err_format+' tidak boleh diawali 0')
        if err:
            exc['kode'] = '\n'.join(err)
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
