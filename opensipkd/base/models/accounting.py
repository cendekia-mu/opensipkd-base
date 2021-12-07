# from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, UniqueConstraint, String
# from sqlalchemy.orm import relationship, backref
#
# from . import Base, NamaModel, TABLE_ARGS
#
#
# class Rekening(NamaModel, Base):
#     __tablename__ = 'rekening'
#     # level_id = Column(SmallInteger, default=1)
#     parent_id = Column(Integer, ForeignKey('rekening.id'), )
#     path = Column(String(255))
#     status = Column(SmallInteger, default=1)
#     category = Column(String(32))
#     children = relationship(
#         "Rekening", backref=backref('parent_id', remote_side='Rekening.id'))
#     parent = relationship("Rekening", remote_side=[parent_id])
#     __table_args__ = (
#         UniqueConstraint('kode', name='rekening_uq'), TABLE_ARGS)
#
#     @classmethod
#     def get_next_level(cls, cid):
#         return cls.query_id(cid).first().level_id + 1
