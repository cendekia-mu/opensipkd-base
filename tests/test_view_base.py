import unittest
from pyramid import testing
from pyramid.paster import get_appsettings


class BaseViewTests(unittest.TestCase):
    def setUp(self):
        settings = get_appsettings('..\magelang.ini', name='main')
        from opensipkd.base import get_config, main
        app = main(global_config=None, **settings)
        # self.testapp = TestApp(self.app)
        # self.config = testing.setUp(settings=settings)
        self.config = get_config(settings)

    def tearDown(self):
        testing.tearDown()


class HomeViewTest(BaseViewTests):
    def test_home(self):
        request = testing.DummyRequest()
        request._host = ""
        request.menus = ""
        from opensipkd.base.views import Home
        inst = Home(request)
        response = inst.view_home()
        print(response)
        self.assertEqual("static/img/logo.png", response["logo"])

    def test_login_get(self):
        request = testing.DummyRequest()
        request._host = ""
        request.menus = ""
        request.referrer = ""
        from opensipkd.base.views.user_login import ViewLogin
        inst = ViewLogin(request)
        response = inst.view_login()
        self.assertEqual("Login", response["form"])

    def test_login_post(self):
        from pyramid.csrf import new_csrf_token
        request = testing.DummyRequest(post=True)
        request._host = ""
        request.menus = ""
        request.referrer = ""
        from opensipkd.base.views.user_login import ViewLogin
        inst = ViewLogin(request)
        csrf_token = new_csrf_token(request)
        params = (("user_name", "sa"), ("password", "12345"),
                  ("csrf_token", csrf_token))
        response = inst.view_login()
        self.assertEqual("Login", response["form"])
