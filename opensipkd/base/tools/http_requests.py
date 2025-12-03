import json
import os
import requests
import pyramid
from threading import Thread
from requests.utils import default_headers
from logging import getLogger
log = getLogger(__name__)
# irul @ 20240529
def join_headers(d):
    return ''.join(f' - {k}: {v}' for k, v in d.items()).strip()
def parse_json(text_message: str):
    try:
        if isinstance(text_message, str):
            text_message = json.loads(text_message)
        return json.dumps(text_message, default=str)
    except:
        return
def is_json_rpc(json_rpc_message):
    if not isinstance(json_rpc_message, dict):
        try:
            json_rpc_message = json.loads(json_rpc_message)
        except ValueError:
            return
    if 'jsonrpc' not in json_rpc_message:
        # raise ValueError("Missing 'jsonrpc' key")
        return
    if json_rpc_message['jsonrpc'] not in ['2.0', '2.1']:
        # raise ValueError("Invalid JSON-RPC version")
        return
    return True
def response_hooks(resp, *args, **kwargs):
    resp_json = parse_json(resp.text)
    resp_body = resp_json or resp.text
    max_resp_length = 1_000
    if not resp_json and len(resp_body) > max_resp_length:
        resp_body = resp_body[:max_resp_length] + " [response text more than %s characters...]" % max_resp_length
    resp_body = os.linesep.join([s for s in resp_body.splitlines() if s]) if not resp_json else resp_body
    if resp.status_code == 302:
        resp_body = "masked(**Moved Temporarily**)"
    if is_json_rpc(resp_body):
        msg_tpl = "🠈 Recv JSON-RPC Response [%s %s] %s %s"
    else:
        msg_tpl = "🠈 Recv HTTP Response [%s %s] %s %s"
    resp_msg = msg_tpl % (
        resp.status_code, resp.reason, resp_body, join_headers(resp.headers))
    log.info(resp_msg)
def requests_log(prep):
    req = prep
    req_body = req.body if req.body else ""
    req_body = req_body.decode() if hasattr(req_body, "decode") else req_body
    if is_json_rpc(req_body):
        msg_tpl = "🠊 Send JSON-RPC Request  [%s %s] %s %s"
    else:
        msg_tpl = "🠊 Send HTTP Request  [%s %s] %s %s"
    req_msg = msg_tpl % (req.method, req.url, req_body, join_headers(req.headers))
    log.info(req_msg)
class MyRequests(requests.Session):
    def __init__(self, base_url=""):
        requests.Session.__init__(self)
        self._base_url = base_url
    # override
    def request(self, method, url,
                params=None, data=None, headers=None, cookies=None, files=None, auth=None, timeout=30,
                allow_redirects=True, proxies=None, hooks=None, stream=None, verify=False, cert=None, json=None):
        # Response Hooks
        resp_hooks = [response_hooks]
        # Create the Request
        req = requests.Request(
            method=method.upper(),
            url=self._base_url + url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            # hooks=hooks,
            hooks={'response': resp_hooks}
        )
        prep = self.prepare_request(req)
        # Request Hooks
        requests_log(prep)
        proxies = proxies or {}
        settings = self.merge_environment_settings(
            prep.url, proxies, stream, verify, cert
        )
        send_kwargs = {
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        }
        send_kwargs.update(settings)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # Send the request.
        resp = self.send(prep, **send_kwargs)
        return resp
if __name__ == '__main__':
    url = 'https://httpbin.org'
    payload = {
        "name": "irul",
        "address": "depok",
    }
    headers = default_headers()
    headers.update({"X-USERID": "irul"})
    session = MyRequests(url)
    resp = session.post("/post", json=payload, headers=headers)
    if not resp:
        exit(1)
    print("RESP:", resp.text)


def background_task(func):
    """Decorator that do threading on a function"""
    def wrap(*args, **kwargs):
        pyramid_thread_locals = pyramid.threadlocal.manager.get()
        kwargs["tlocal"] = pyramid_thread_locals
        """
        
        Jadi, agar threadlocal-nya pyramid terbaca dari dalam Thread yang akan dibuat
        maka bisa dikirim sebagai kwargs `tlocal` yang mana menyimpan threadlocal-nya pyramid.
        Namun pastikan pada fungsi yang akan dijalankan oleh Thread, ditambahkan kwargs parameter
        jika belum ada. Kemudian selain itu, di dalam fungsi yang akan dipanggil tersebut juga perlu
        ditambahkan script berikut:
        
        `pyramid.threadlocal.manager.push(kwargs["tlocal"])`
        
        fyi: https://johncylee.github.io/2012/08/30/multi-thread-testing-in-pyramid/
        
        """
        # Thread(target=func, args=args, kwargs=kwargs).start()
        t = Thread(target=func, args=args, kwargs=kwargs)
        # t.name = "t." + func.__name__
        t.daemon = True  # automatically terminated if the main app stop/exit
        t.start()
    return wrap
