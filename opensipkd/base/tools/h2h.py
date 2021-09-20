from opensipkd.base import get_settings
from opensipkd.base.tools.api import (JsonRpcBillerNotFoundError,
                                      JsonRpcCaNotRegisteredError, get_mandatory)
from datetime import datetime

import logging

log = logging.getLogger(__name__)
ERR_MAX_LOOP = '*** Max loop for create payment ID. ' \
               'Call your programmer please.'


class H2hIso8583(object):
    def __init__(self, data):
        self.data = data
        log.info("Request: {}".format(self.data))
        ca = self.ca_allowed()
        if not ca:
            raise JsonRpcCaNotRegisteredError
        self.bank_id = ca.id
        self.inv_no = self.data["bit_061"].strip()
        self.inv_id = None
        self.tgl = self.get_tanggal()
        self.settings = get_settings()
        self.calc = None
        self.invoice_profile = {}
        self.cur_tahun = datetime.now().date().year

    def ca_allowed(self):
        return

    def hitung_denda(self, pokok, expire, now=datetime.now().date()):
        jatuh_tempo = expire
        kini = now
        x = (kini.year - jatuh_tempo.year) * 12
        y = kini.month - jatuh_tempo.month
        bln_tunggakan = x + y + 1
        if kini.day <= jatuh_tempo.day:
            bln_tunggakan -= 1
        if bln_tunggakan < 1:
            bln_tunggakan = 0
        if bln_tunggakan > 24:
            bln_tunggakan = 24
        return bln_tunggakan * self.persen_denda / 100.0 * self.tagihan

    def get_tanggal(self):
        dt = "{}{}{}".format(datetime.now().strftime("%Y"),
                             self.data["bit_013"], self.data["bit_012"])
        return datetime.strptime(dt, "%Y%m%d%H%M%S")

    def get_amt(self):
        return self.data["bit_004"]

    def get_acquirer(self):
        return self.data["bit_032"]

    def get_ntb(self):
        return self.data["bit_037"]

    def get_stan(self):
        return self.data["bit_011"]

    def get_bank(self):
        return self.data["bit_033"]

    def get_channel(self):
        return self.data["bit_018"]

    def set_amt(self, amt):
        self.data["bit_004"] = amt

    def set_response_ok(self):
        self.data["bit_039"] = "00"

    def set_profile(self):
        self.data["bit_062"] = self.invoice_profile

    def set_ntp(self, ntp):
        self.data["bit_048"] = ntp

    def write_resp(self, prefix):
        log.warning("{} CA {}".format(prefix, self.data))

    def inquiry(self):
        self.write_resp("INQ req")
        get_mandatory(self.data, ["bit_061", "bit_012",
                                  "bit_013", "bit_018", "bit_033", ])

    def get_ntp(self):
        pass

    def payment(self):
        self.write_resp("PAY req")
        get_mandatory(self.data, ["bit_004", "bit_007", "bit_012",
                                  "bit_013", "bit_015", "bit_018",
                                  "bit_032", "bit_033", "bit_037",
                                  "bit_061", "bit_062"])

    def reversal(self):
        self.write_resp("REV req")
        get_mandatory(self.data, ["bit_004", "bit_007", "bit_012",
                                  "bit_013", "bit_015", "bit_018",
                                  "bit_032", "bit_033", "bit_037",
                                  "bit_061", "bit_062"])

    def advice(self):
        self.write_resp("ADV req")
        get_mandatory(self.data, ["bit_004", "bit_007", "bit_012",
                                  "bit_013", "bit_015", "bit_018",
                                  "bit_032", "bit_033", "bit_037",
                                  "bit_061", "bit_062"])
