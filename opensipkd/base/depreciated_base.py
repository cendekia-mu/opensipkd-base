
from opensipkd.base import get_params


def get_company(request):
    return get_params('company', 'openSIPKD').upper()


def get_departement(request):
    return get_params('departement', 'DEPARTEMEN INFORMATION TEKNOLOGI').upper()


def get_ibukota(request):
    return get_params('ibukota', 'BEKASI')


def get_address(request):
    return get_params('address_1', 'ALAMAT DEPARTEMEN BARIS 1')


def get_address2(request):
    return get_params('address_2', 'ALAMAT DEPARTEMEN BARIS 2')


def get_app_name(request):
    return get_params('app_name', 'openSIPKD Application')


def is_devel(request):
    return get_params('devel') == 'true'
