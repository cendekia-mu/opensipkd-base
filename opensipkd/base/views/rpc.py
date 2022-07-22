from pyramid_rpc.jsonrpc import jsonrpc_method

from opensipkd.models import Menus


@jsonrpc_method(method='get_menu', endpoint='rpc')
def get_menu(request, data):
    """
    Digunakan untuk login pada aplikasi lain
    :param request:
    :param data:
    {
        "user_name": "user_name",
        "password": "password"
    }
    :return:
        result: "data":
        {
            "user_name": "user_name",
            "nik": nik,
            "nama": nik,
            "group": [group],
            "departemens": [departemen]
        }
        error:"error":{}
    """
    is_list = type(data) is list
    data = is_list and data[0] or data
    level_id = data.get("level")
    group = data.get("group")
    qry = Menus.query()
    if level_id:
        qry = qry.filter(Menus.level_id == level_id or Menus.level_id == None)
    if group:
        grp = Menus.query().filter(kode=group).first()
        if grp:
            qry = qry.filter(
                Menus.parent_id == grp.id or Menus.parent_id == None)
    if request.user:
        qry = qry.filter_by(need_login=True)
    else:
        qry = qry.filter_by(need_login=False)
    resp = [
        {
            "type": "link",
            "label": row.nama,
            "className": row.class_name,
            "name": row.kode,
            "id": row.kode,
            "url": row.url,
            "icon": row.icon
        }
        for row in qry.all()]

    result = is_list and [resp] or resp
    return result
