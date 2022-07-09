import logging

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.renderers import null_renderer
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid_rpc.jsonrpc import (JsonRpcError, JsonRpcMethodNotFound, JsonRpcParamsInvalid,
                                 JsonRpcInternalError, make_error_response, MethodPredicate, BatchedRequestPredicate,
                                 jsonrpc_renderer, add_jsonrpc_method,
                                 DEFAULT_RENDERER,
                                 batched_request_view, Endpoint, EndpointPredicate)
from pyramid_rpc.mapper import ViewMapperArgsInvalid, MapplyViewMapper

log = logging.getLogger(__name__)


class JsonRpcRequestForbidden(JsonRpcError):
    code = -32604
    message = 'request forbidden'


class JsonRpcInvalidLogin(JsonRpcError):
    code = -32605
    message = "Invalid User/Password"

#
# class EndpointPredicate(BaseEndpointPredicate):
#     def __call__(self, info, request):
#         if self.val:
#             # find the endpoint info
#             key = info['route'].name
#             endpoint = request.registry.jsonrpc_endpoints[key]
#
#             # potentially setup either rpc v1 or v2 from the parsed body
#             setup_request(endpoint, request)
#
#             # update request with endpoint information
#             request.rpc_endpoint = endpoint
#
#             # Always return True so that even if it isn't a valid RPC it
#             # will fall through to the notfound_view which will still
#             # return a valid JSON-RPC response.
#             return True


# def setup_request(endpoint, request):
#     """ Parse a JSON-RPC request body."""
#     if request.method == 'GET':
#         parse_request_GET(request)
#     elif request.method == 'POST':
#         parse_request_POST(request)
#     else:
#         log.debug('unsupported request method "%s"', request.method)
#         raise JsonRpcRequestInvalid
#
#     if hasattr(request, 'batched_rpc_requests'):
#         log.debug('handling batched rpc request')
#         # the checks below will look at the subrequests
#         return
#
#     if request.rpc_version != '2.0':
#         log.debug('id:%s invalid rpc version %s',
#                   request.rpc_id, request.rpc_version)
#         raise JsonRpcRequestInvalid
#
#     if request.rpc_method is None:
#         log.debug('id:%s invalid rpc method', request.rpc_id)
#         raise JsonRpcRequestInvalid

    # env = request.environ
    # if 'HTTP_TOKEN' in env:
    #     try:
    #         user_device = token_auth(request)
    #         user = user_device.user
    #         headers = remember(request, user.id)
    #         request.headers["Cookie"] = dict(headers)["Set-Cookie"]
    #         request.headers["token"]=user_device.token
    #         log.debug(request.headers["Cookie"])
    #     except JsonRpcInvalidLoginError as e:
    #         raise JsonRpcInvalidLogin
    #
    # elif ('HTTP_USERID' in env and 'HTTP_SIGNATURE' in env and
    #       'HTTP_KEY' in env):
    #     try:
    #         user = rpc_auth(request)
    #         headers = remember(request, user.id)
    #         request.headers["Cookie"] = dict(headers)["Set-Cookie"]
    #         log.debug(request.headers["Cookie"])
    #     except JsonRpcInvalidLoginError as e:
    #         raise JsonRpcInvalidLogin

    # log.debug('handling id:%s method:%s',
    #           request.rpc_id, request.rpc_method)


def exception_view(exc, request):
    rpc_id = getattr(request, 'rpc_id', None)
    if isinstance(exc, JsonRpcError):
        fault = exc
        log.debug('json-rpc error rpc_id:%s "%s"',
                  rpc_id, exc.message)
    elif isinstance(exc, HTTPNotFound):
        fault = JsonRpcMethodNotFound()
        log.debug('json-rpc method not found rpc_id:%s "%s"',
                  rpc_id, request.rpc_method)
    elif isinstance(exc, HTTPForbidden):
        fault = JsonRpcRequestForbidden()
        log.debug('json-rpc method forbidden rpc_id:%s "%s"',
                  rpc_id, request.rpc_method)
    elif isinstance(exc, ViewMapperArgsInvalid):
        fault = JsonRpcParamsInvalid()
        log.debug('json-rpc invalid method params')
    else:
        fault = JsonRpcInternalError()
        log.exception('json-rpc exception rpc_id:%s "%s"', rpc_id, exc)

    return make_error_response(request, fault, rpc_id)


def add_jsonrpc_endpoint(config, name, *args, **kw):
    """Add an endpoint for handling JSON-RPC.

    ``name``

        The name of the endpoint.

    ``default_mapper``

        A default view mapper that will be passed as the ``mapper``
        argument to each of the endpoint's methods.

    ``default_renderer``

        A default renderer that will be passed as the ``renderer``
        argument to each of the endpoint's methods. This should be the
        string name of the renderer, registered via
        :meth:`pyramid.config.Configurator.add_renderer`.

    A JSON-RPC method also accepts all of the arguments supplied to
    :meth:`pyramid.config.Configurator.add_route`.

    """
    default_mapper = kw.pop('default_mapper', MapplyViewMapper)
    default_renderer = kw.pop('default_renderer', DEFAULT_RENDERER)

    endpoint = Endpoint(
        name,
        default_mapper=default_mapper,
        default_renderer=default_renderer,
    )

    config.registry.jsonrpc_endpoints[name] = endpoint

    kw['jsonrpc_endpoint'] = True
    config.add_route(name, *args, **kw)

    kw = {}
    kw['jsonrpc_batched'] = True
    kw['renderer'] = null_renderer
    config.add_view(batched_request_view, route_name=name,
                    permission=NO_PERMISSION_REQUIRED, **kw)
    config.add_view(exception_view, route_name=name, context=Exception,
                    permission=NO_PERMISSION_REQUIRED)


def includeme(config):
    """ Set up standard configurator registrations.  Use via:

    .. code-block:: python

       config = Configurator()
       config.include('pyramid_rpc.jsonrpc')

    Once this function has been invoked, two new directives will be
    available on the configurator:

    - ``add_jsonrpc_endpoint``: Add an endpoint for handling JSON-RPC.

    - ``add_jsonrpc_method``: Add a method to a JSON-RPC endpoint.

    """
    if not hasattr(config.registry, 'jsonrpc_endpoints'):
        config.registry.jsonrpc_endpoints = {}

    config.add_view_predicate('jsonrpc_method', MethodPredicate)
    config.add_view_predicate('jsonrpc_batched', BatchedRequestPredicate)
    config.add_route_predicate('jsonrpc_endpoint', EndpointPredicate)

    config.add_renderer(DEFAULT_RENDERER, jsonrpc_renderer)
    config.add_directive('add_jsonrpc_endpoint', add_jsonrpc_endpoint)
    config.add_directive('add_jsonrpc_method', add_jsonrpc_method)
    config.add_view(exception_view, context=JsonRpcError,
                    permission=NO_PERMISSION_REQUIRED)
