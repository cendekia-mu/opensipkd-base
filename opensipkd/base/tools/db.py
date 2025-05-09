from sqlalchemy import func
from opensipkd.base.models import Parameter


def column_concat(cols=None):
    if not cols:
        return ''
    elif len(cols) == 1:
        return cols[0]
    # saat ini menggunakan recursive spertinya ada syntax pythonic
    # func.concat(cols[i], for col in cols)
    return func.concat(cols[0], column_concat(cols[1:]))


def column_date(field, dt_format='YYYY-MM-DD HH:MI:SS'):
    return func.to_char(field, dt_format)


def get_parameter(kode):
    return Parameter.query_kode(kode).first()


def get_parameter_pasar(kode):
    return Parameter.query_kode(kode).all()


def get_parameter_kebersihan(kode):
    return Parameter.query_kode(kode).all()
