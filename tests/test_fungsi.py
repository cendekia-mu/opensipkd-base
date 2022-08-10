import unittest
from pyramid import testing
from pyramid.paster import get_appsettings

class MyTest(unittest.TestCase):
    def setUp(self):
        settings = get_appsettings('../test.ini', name='main')
        from opensipkd.base import main
        self.app = TestApp(main(global_config = None, **settings))


        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_view_fn_query_table(self):
        from pyramid.httpexceptions import HTTPForbidden
        from opensipkd.models import query_table
        res = query_table('routes', ['id'])
        print(res.first())
        # , [('id', '=', 1)]
        # self.config.testing_securitypolicy(userid='hank',
        #                                    permissive=False)
        # request = testing.DummyRequest()
        # request.context = testing.DummyResource()
        # self.assertRaises(HTTPForbidden, view_fn, request)

    # def test_view_fn_allowed(self):
    #     from my.package import view_fn
    #     self.config.testing_securitypolicy(userid='hank',
    #                                        permissive=True)
    #     request = testing.DummyRequest()
    #     request.context = testing.DummyResource()
    #     response = view_fn(request)
    #     self.assertEqual(response, {'greeting':'hello'})
