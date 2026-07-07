import pyramid_rpc.jsonrpc

# 1. Store a reference to the original, vulnerable endpoint function
original_parse_request = pyramid_rpc.jsonrpc.parse_request_POST

# 2. Create a wrapper that safely handles the Python 3.12 KeyError


def patched_parse_request_POST(request):
    try:
        body = request.json_body
    except ValueError:
        raise pyramid_rpc.jsonrpc.JsonRpcParseError

    try:
        batched = body[:]
    except TypeError:
        batched = None
    except KeyError:
        batched = None


    if batched is not None:
        request.batched_rpc_requests = batched
    else:
        request.rpc_id = body.get('id')
        request.rpc_args = body.get('params', ())
        request.rpc_method = body.get('method')
        request.rpc_version = body.get('jsonrpc')

# 3. Swap the function inside the pyramid_rpc library dynamically
pyramid_rpc.jsonrpc.parse_request_POST = patched_parse_request_POST

# from pyramid.request import Request

# # 1. Define a dict that explicitly forces a TypeError on slice lookups


# class PrePython12Dict(dict):
#     def __getitem__(self, key):
#         if isinstance(key, slice):
#             raise TypeError(
#                 "Slicing not supported on dicts (Pre-Python 3.12 simulation)")
#         return super().__getitem__(key)


# # 2. Save a reference to the original WebOb json_body getter logic
# original_json_body_descriptor = Request.json_body

# # 3. Create a replacement getter property


# @property
# def patched_json_body(self):
#     # Fetch the original dictionary parsed by WebOb
#     body = original_json_body_descriptor.__get__(self, Request)
#     # Wrap it in our custom dictionary class if it's a standard dict
#     if isinstance(body, dict) and not isinstance(body, PrePython12Dict):
#         return PrePython12Dict(body)
#     return body


# # 4. Overwrite the Request class property globally
# Request.json_body = patched_json_body

# from pyramid.events import NewRequest
# class Python12DictPatch(dict):
#     """Forces standard dictionary to drop a TypeError on slicing, mimicking pre-3.12 behavior"""

#     def __getitem__(self, key):
#         if isinstance(key, slice):
#             raise TypeError("Slicing not supported on dictionaries")
#         return super().__getitem__(key)

# # @subscriber(NewRequest)


# def patch_rpc_body(event):
#     request = event.request
#     if request.content_type == 'application/json':
#         try:
#             if isinstance(request.json_body, dict):
#                 # Wrap it in our custom dict to trigger the expected TypeError
#                 request.json_body = Python12DictPatch(request.json_body)
#         except Exception:
#             pass

# # def main(global_config, **settings):
# #     config = Configurator(settings=settings)
# #     # Register the subscriber BEFORE including pyramid_rpc
# #     config.add_subscriber(patch_rpc_body, NewRequest)


def includeme(config, ):
    pass
    # config.add_subscriber(patch_rpc_body, NewRequest)
