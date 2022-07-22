from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    SmallInteger, Boolean,
)
from sqlalchemy.orm import (
    relationship,
    backref
)

from ..models import DBSession, Base
from ..models import (NamaModel,
                      TABLE_ARGS)


class Menus(Base, NamaModel):
    __tablename__ = 'menus'
    __table_args__ = (TABLE_ARGS,)
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('public.menus.id'))
    level_id = Column(SmallInteger)
    order_id = Column(SmallInteger)
    url = Column(String(256))
    icon = Column(String(256))
    class_name = Column(String(256))
    need_login = Column(SmallInteger, server_default="1")
    permissions = Column(String(128), server_default="")
    children = relationship(
        "Menus", backref=backref('parent', remote_side=[id]))

    def get_parents(self, start=False):
        allparents = []
        if start:
            allparents.append(self.nama)
        p = self.parent
        while p:
            allparents.append(p.nama)
            p = p.parent
        return allparents

    @property
    def parents(self, start=False):
        return self.get_parents()

    @property
    def name_get(self):
        allparents = self.get_parents(True)
        return '/'.join(reversed(allparents))

    @property
    def uraian_all(self):
        allparents = self.get_parents(True)
        return '/'.join(reversed(allparents))

    @classmethod
    def get_list(cls):
        return DBSession.query(cls.id, cls.nama).order_by(cls.nama).all()

    @classmethod
    def query_grid(cls):
        return DBSession.query().select_from(cls)

    @classmethod
    def get(cls, parent=None):
        if not parent:
            return cls.query().filter(cls.parent_id == None)
        else:
            row = cls.query().filter(cls.kode == parent).first()
            if row:
                return cls.query().filter(cls.parent_id == row.id)

