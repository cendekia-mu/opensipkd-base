from sqlalchemy import (Column, Integer, ForeignKey,
                        String, SmallInteger, text)
from sqlalchemy.orm import (relationship, backref, declared_attr)
from ..models import DBSession, Base
from ..models import (NamaModel, TABLE_ARGS, SCHEMA)

class _Departemen(NamaModel):
    __table_args__ = (TABLE_ARGS,)
    __tablename__ = 'departemen'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey(SCHEMA+'.departemen.id'))
    kategori = Column(String(32))
    alamat = Column(String(255))
    singkat = Column(String(32))
    level_id = Column(SmallInteger)

    @declared_attr
    def children(self):
        return relationship(
            "Departemen", backref=backref('parent', remote_side=[self.id]))

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
    def cte_get(cls, search=None, **kwargs):
        # tahun = kwargs.get('tahun', self.req.params.get(
        #     'tahun', datetime.datetime.now().year-1))
        parent_id = kwargs.get('id', None)
        str_where = parent_id and " parent_id={} ".format(
            parent_id) or " parent_id IS NULL"
        eng = cls.db_session.get_bind()
        if eng.dialect.name.lower() == "oracle":
            sql = """
                SELECT
                    --LPAD(' ', (LEVEL - 1) * 2) || nama AS hierarchy,
                    SYS_CONNECT_BY_PATH(nama, '/') AS hierarchy,
                    id,
                    kode,
                    nama,
                    parent_id,
                    status,
                    (LEVEL - 1) AS lvl,
                    SYS_CONNECT_BY_PATH(id, ',') AS path
                FROM
                    departemen
                START WITH 
                    parent_id IS NULL
                CONNECT BY 
                    PRIOR id = parent_id
                ORDER SIBLINGS BY 
                    id """
        else:
            sql = """
                WITH RECURSIVE dep_tree AS (
                SELECT
                    id,
                    kode,
                    nama::text AS nama,
                    parent_id,
                    status,
                    0 AS lvl,
                    ARRAY[id] AS path
                FROM departemen

                UNION ALL

                SELECT
                    c.id,
                    c.kode,
                    ct.nama || '/' || c.nama::text AS nama,
                    c.parent_id,
                    c.status,
                    ct.lvl + 1,
                    ct.path || c.id
                FROM departemen c
                JOIN dep_tree ct ON c.parent_id = ct.id
                )
                SELECT DISTINCT ON (kode)
                id,
                kode,
                nama as hierarchy,
                parent_id,
                status,
                lvl,
                path
                FROM dep_tree
                """
            #.format(str_where=str_where)

            if search:
                sql = f"{sql} WHERE nama ILIKE :search "

            sql = sql+"""ORDER BY kode, path """
        if search:
            return cls.db_session.execute(text(sql), {"search": search}).fetchall()
        else:
            return cls.db_session.execute(text(sql)).fetchall()



class Departemen(_Departemen, Base):
    db_session = DBSession
