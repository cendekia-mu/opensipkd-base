import unittest
from pyramid import testing
from pyramid.paster import get_appsettings
from webtest import TestApp


class BaseFunctionalTests(unittest.TestCase):
    def setUp(self):
        settings = get_appsettings('..\magelang.ini', name='main')
        from opensipkd.base import main
        app = main(global_config=None, **settings)
        self.testapp = TestApp(app)
        # self.config = testing.setUp()


class HomeFunctionalTests(BaseFunctionalTests):
    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertIn(
            b'<h1>ABOUT <span class="bold">OPENSIPKD</span></h1>', res.body)

    def test_login(self):
        from pyramid.csrf import new_csrf_token
        # request = testing.DummyRequest()
        # Bagaimana masukin registry disini???
        request = self.testapp.RequestClass.blank("/login")
        request.registry = None
        csrf_token = new_csrf_token(request)
        params = (("user_name", "sa"), ("password", "12345"),
                  ("csrf_token", csrf_token)
                  )
        res = self.testapp.post('/login', params=params, status=200)
        print(res)
