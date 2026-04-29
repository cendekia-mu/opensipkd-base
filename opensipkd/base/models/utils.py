from sqlalchemy import Column
from . import Base, NamaModel, TABLE_ARGS


class TextPrinters(Base, NamaModel):
    __tablename__ = 'text_printers'
    __table_args__ = TABLE_ARGS
