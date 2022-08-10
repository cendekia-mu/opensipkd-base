import unittest
from pyramid import testing
from pyramid.paster import get_appsettings
from webtest import TestApp

class MyTest(unittest.TestCase):
    def setUp(self):
        settings = get_appsettings('test.ini', name='main')
        from opensipkd.base import main
        self.app = TestApp(main(global_config = None, **settings))


        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

class TestHome(MyTest):
    def _callFUT(self, context, request):
        from opensipkd.base.views import Home
        home=Home(request)
        return home.view_home()

        
            
    def test_home(self):
        page = testing.DummyResource()
        page['IDoExist'] = testing.DummyResource()
        context = testing.DummyResource()
        context.__parent__ = page
        context.__name__ = 'home'
        request = testing.DummyRequest()
        info = self._callFUT(context, request)
        assert info['page'] == context
        print(info["page_text"])