import unittest
from pyramid import testing


class MyTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_view_fn_query_table(self):
        from pyramid.httpexceptions import HTTPForbidden
        from opensipkd.base.models import query_table
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
