from sqlalchemy import (Column, Integer, ForeignKey, String, SmallInteger)
from sqlalchemy.orm import (relationship, backref)
from ..models import DBSession, Base
from ..models import (NamaModel, TABLE_ARGS)


class Departemen(Base, NamaModel):
    __tablename__ = 'departemen'
    __table_args__ = (TABLE_ARGS,)
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('public.departemen.id'))
    kategori = Column(String(32))
    alamat = Column(String(255))
    singkat = Column(String(32))
    level_id = Column(SmallInteger)
    children = relationship(
        "Departemen", backref=backref('parent', remote_side=[id]))

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
