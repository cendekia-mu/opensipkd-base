# from pyramid_rpc.amfgateway import PyramidGateway
from pyramid_rpc.jsonrpc import jsonrpc_method
from opensipkd.tools.api import JsonRpcInvalidDataError, JsonRpcInvalidLoginError
from ziggurat_foundations.models.services.user import UserService

from ..models import Partner, User





# services = {
#     'get_profile.echo': get_profile
#     could include other functions as well
# }
#
# echoGateway = PyramidGateway(services)


