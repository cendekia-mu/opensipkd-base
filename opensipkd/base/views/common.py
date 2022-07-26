from datatables.clean_regex import clean_regex
from sqlalchemy import (
    String, Text,
    or_,
)
from sqlalchemy.dialects import oracle, mssql
from datatables import DataTables as BaseDataTables, ColumnDT
from opensipkd.base import log


class DataTables(BaseDataTables):
    def __init__(self, request, query, columns, allow_regex_searches=False):
        super().__init__(request, query, columns, allow_regex_searches)

    def _set_global_filter_expression(self):
        # global search filter
        global_search = self.params.get('search[value]', '')
        if global_search == '':
            return

        if (self.allow_regex_searches and
                self.params.get('search[regex]') == 'true'):
            op = self._get_regex_operator()
            val = clean_regex(global_search)

            def filter_for(col):
                return col.sqla_expr.op(op)(val)
        else:
            val = '%' + global_search + '%'

            def filter_for(col):
                if isinstance(self.query.session.bind.dialect, oracle.dialect) or \
                        isinstance(self.query.session.bind.dialect, mssql.dialect):
                    return col.sqla_expr.cast(String(255)).ilike(val)
                return col.sqla_expr.cast(Text).ilike(val)

        global_filter = [filter_for(col)
                         for col in self.columns if col.global_search]
        # global_filter = []
        # for col in self.columns:
        # if col.global_search:
        # global_filter.append(filter_for(col))
        self.filter_expressions.append(or_(*global_filter))

    def output_result(self):
        """Output results in the format needed by DataTables."""
        output = {}
        output['draw'] = str(int(self.params['draw']))
        output['recordsTotal'] = str(self.cardinality)
        output['recordsFiltered'] = str(self.cardinality_filtered)
        if self.error:
            output['error'] = self.error
            return output
        output['data'] = self.results
        for k, v in self.yadcf_params:
            output[k] = v
        return output

    def _set_sort_expressions(self):
        """Construct the query: sorting.

        Add sorting(ORDER BY) on the columns needed to be applied on.
        """
        sort_expressions = []
        i = 0
        while self.params.get('order[{:d}][column]'.format(i), False):
            column_nr = int(self.params.get('order[{:d}][column]'.format(i)))
            field_name = self.params.get(f"columns[{column_nr}][data]")
            i = 0
            # penambahan looping karena data yang dikirim datatable berupa index
            # column bukan nama column
            for c in range(len(self.columns)):
                if self.columns[c].mData == field_name:
                    column = self.columns[c]
                    direction = self.params.get('order[{:d}][dir]'.format(i))
                    sort_expr = column.sqla_expr
                    if direction == 'asc':
                        sort_expr = sort_expr.asc()
                    elif direction == 'desc':
                        sort_expr = sort_expr.desc()
                    else:
                        raise ValueError(
                            'Invalid order direction: {}'.format(direction))
                    if column.nulls_order:
                        if column.nulls_order == 'nullsfirst':
                            sort_expr = sort_expr.nullsfirst()
                        elif column.nulls_order == 'nullslast':
                            sort_expr = sort_expr.nullslast()
                        else:
                            raise ValueError(
                                'Invalid order direction: {}'.format(direction))

                    sort_expressions.append(sort_expr)
            i += 1
            log.info("ORDERING")
            # log.info(dir(sort_expressions))
            # log.info(repr(sort_expressions))
            # log.info(str(sort_expressions))
            for e in sort_expressions:
                print(e)
        self.sort_expressions = sort_expressions
