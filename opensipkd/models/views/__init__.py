from sqlalchemy import func
from sqlalchemy.sql import sqltypes

from .. import Base
from opensipkd.tools import round_up
from opensipkd.tools.api import JsonRpcDataNotFoundError
from opensipkd.tools.pbb import FixNop, FixKelurahan, FixBlok


class BaseApiTableFilter(object):
    """Function untuk standarisasi filtering table"""

    def __init__(self, orm, data):
        self.orm = orm
        self.data = data

    def filter_nop(self, qry, val):
        kode = FixNop(val)
        return qry.filter_by(kd_propinsi=kode["kd_propinsi"],
                             kd_dati2=kode["kd_dati2"],
                             kd_kecamatan=kode["kd_kecamatan"],
                             kd_kelurahan=kode["kd_kelurahan"],
                             kd_blok=kode["kd_blok"],
                             no_urut=kode["no_urut"],
                             kd_jns_op=kode["kd_jns_op"])

    def filter_desa(self, qry, val):
        kode = FixKelurahan(val)
        return qry.filter_by(kd_propinsi=kode["kd_propinsi"],
                             kd_dati2=kode["kd_dati2"],
                             kd_kecamatan=kode["kd_kecamatan"],
                             kd_kelurahan=kode["kd_kelurahan"]
                             )

    def filter_blok(self, qry, val):
        kode = FixBlok(val)
        return qry.filter_by(kd_propinsi=kode["kd_propinsi"],
                             kd_dati2=kode["kd_dati2"],
                             kd_kecamatan=kode["kd_kecamatan"],
                             kd_kelurahan=kode["kd_kelurahan"],
                             kd_blok=kode["kd_blok"])

    def get_data(self):
        data = self.data
        orm = self.orm
        qry = self.orm.query()
        if "where" in data:
            for w in data["where"]:
                if hasattr(orm, w['key']):
                    key = w["key"]
                    val = w["val"]
                    if key == "nop":
                        qry = self.filter_nop(qry, val)
                    elif key == "desa":
                        qry = self.filter_desa(qry, val)
                    elif key == "blok":
                        qry = self.filter_blok(qry, val)
                    else:
                        key = getattr(orm, key)
                        if isinstance(key.type, sqltypes.String):
                            qry = qry.filter(func.trim(key) == val)
                        else:
                            qry = qry.filter(key == val)

        if "order" in data:
            for o in data["order"]:
                key = getattr(orm, o)
                qry = qry.order_by(key)

        page_size = "page_size" in data and int(data["page_size"]) or 20
        page = "page" in data and int(data["page"]) or 1
        total_page = round_up(qry.count() / page_size)
        if total_page and page > total_page:
            page = int(total_page)

        offset = (page - 1) * page_size
        qry = qry.offset(offset).limit(page_size)
        return qry, page, page_size, total_page


    def get_filter(self):
        qry, page, page_size, total_page = self.get_data()
        row = qry.first()
        if not row:
            raise JsonRpcDataNotFoundError
        result = []
        for row in qry.all():
            result.append(row.to_dict())

        return dict(record=result,
                    total_page=total_page,
                    page=page,
                    page_size=page_size)
