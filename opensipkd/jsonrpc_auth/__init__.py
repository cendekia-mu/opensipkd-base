import logging

import venusian
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid_rpc.jsonrpc import jsonrpc_method as json_rpc_base, MethodPredicate, BatchedRequestPredicate, \
    EndpointPredicate, jsonrpc_renderer, DEFAULT_RENDERER, add_jsonrpc_endpoint, add_jsonrpc_method, JsonRpcError, \
    exception_view, JsonRpcRequestInvalid, parse_request_GET, parse_request_POST

from opensipkd.base.tools.api import auth_from_rpc
from opensipkd.base.views.user_login import get_login_headers

log = logging.getLogger(__name__)

def setup_request(endpoint, request):
    """ Parse a JSON-RPC request body."""
    if request.method == 'GET':
        parse_request_GET(request)
    elif request.method == 'POST':
        parse_request_POST(request)
    else:
        log.debug('unsupported request method "%s"', request.method)
        raise JsonRpcRequestInvalid

    if hasattr(request, 'batched_rpc_requests'):
        log.debug('handling batched rpc request')
        # the checks below will look at the subrequests
        return

    if request.rpc_version != '2.0':
        log.debug('id:%s invalid rpc version %s',
                  request.rpc_id, request.rpc_version)
        raise JsonRpcRequestInvalid

    if request.rpc_method is None:
        log.debug('id:%s invalid rpc method', request.rpc_id)
        raise JsonRpcRequestInvalid

    log.debug('handling id:%s method:%s',
              request.rpc_id, request.rpc_method)

class MethodPredicate(object):
    def __init__(self, val, config):
        self.method = val

    def text(self):
        return 'jsonrpc method = %s' % self.method

    phash = text

    def __call__(self, context, request):
        user = auth_from_rpc(request)
        headers = get_login_headers(request, user)
        response = HTTPFound(location=request.route_url('home'), headers=headers)
        # response = request.response
        request.response.set_cookie('userid', value=str(user.id), max_age=31536000)  # max_age = year
        return getattr(request, 'rpc_method', None) == self.method

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
