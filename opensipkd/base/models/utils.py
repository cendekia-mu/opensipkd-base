from sqlalchemy import Column, Integer, String
from . import Base, NamaModel, TABLE_ARGS


class TextPrinters(Base, NamaModel):
    __tablename__ = 'text_printers'
    __table_args__ = TABLE_ARGS
    is_epson = Column(Integer(), default=0)
    queue = Column(String(16), default='lp')
    port = Column(Integer(), default=515)
    timeout = Column(Integer(), default=10)
    user_id = Column(Integer(), nullable=False)
