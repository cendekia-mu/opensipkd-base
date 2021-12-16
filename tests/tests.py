import unittest
from configparser import ConfigParser

import transaction
from pyramid import testing
from sqlalchemy import create_engine
from opensipkd.base.models import (
    DBSession,
    Base
)
from opensipkd.base import main


# def _initTestingDB():


# engine = create_engine('postgresql://aagusti:a@localhost/demo')
# Base.metadata.create_all(engine)
# DBSession.configure(bind=engine)
# # with transaction.manager:
# #     model = Page('FrontPage', 'This is the front page')
# #     DBSession.add(model)
# return DBSession

def settings():
    config = ConfigParser()
    config.read('/home/aagusti/apps/base/test.ini')
    dictionary = {}
    for section in config.sections():
        dictionary[section] = {}
        for option in config.options(section):
            try:
                dictionary[section][option] = config.get(section, option)
            except:
                pass

    return dictionary


class PageModelTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        config = settings()
        main(self.config, **config['app:main'])

    def tearDown(self):
        # self.session.remove()
        testing.tearDown()

    def test_view_fn_query_table(self):
        from pyramid.httpexceptions import HTTPForbidden
        from opensipkd.base.models import query_table
        res = query_table('routes', ['id'])
        row = res.first()
        assert row.id == 1

    def test_view_fn_query_table2(self):
        from pyramid.httpexceptions import HTTPForbidden
        from opensipkd.base.models import query_table
        res = query_table('routes', ['id', 'nama'], [('id', '=', 2)])
        row = res.first()
        assert row.id == 2


if __name__ == "__main__":
    print("START")
    config = testing.setUp()
    cfg = settings()
    main(config, **cfg['app:main'])
    from opensipkd.base.models import query_table

    res = query_table('routes', ['id', 'nama', 'kode'],
                      [('|', ('nama', 'ilike', "a%"),
                        ('kode', 'ilike', 'g%'))])
    for row in res.all():
        print(row.id, row.nama, row.kode)
