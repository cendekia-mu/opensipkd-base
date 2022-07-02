# from pyramid_rpc.amfgateway import PyramidGateway
from pyramid_rpc.jsonrpc import jsonrpc_method
from opensipkd.tools.api import JsonRpcInvalidDataError, JsonRpcInvalidLoginError
from ziggurat_foundations.models.services.user import UserService

from ..models import Partner, User


def get_profile_(user):
    partner = Partner.query().filter_by(email=user.email).first()
    if not partner:
        raise JsonRpcInvalidDataError

    result = dict(user_name=user.user_name,
                  nik=partner.kode,
                  email=partner.email,
                  mobile=partner.mobile,
                  nama=partner.nama, )
    return dict(data=result)


@jsonrpc_method(method='get_profile', endpoint='rpc-user')
def get_profile(request, data):
    """
    Digunakan untuk memperoleh profile user yang sedang login
    parameter
    @param request: Request
    @param data: Dict(user_name=user_name/email, password=password)
    @return:
    """
    user = request.user
    print("User", user)
    data = type(data) == list and data[0] or data
    user = User.get_by_identity(data["user_name"])
    if not user or not UserService.check_password(user, data['password']):
        raise JsonRpcInvalidLoginError
    return get_profile_(user)


# services = {
#     'get_profile.echo': get_profile
#     could include other functions as well
# }
#
# echoGateway = PyramidGateway(services)


