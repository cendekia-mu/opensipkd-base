import logging
import datatables
import datatables.clean_regex
from sqlalchemy import (
    String,
    Text,
    or_,
)
from sqlalchemy.dialects import mssql, oracle

log = logging.getLogger(__name__)
log.warning("opensipkd.base.captcha depreciated use opensipkd.tools.captcha")

ColumnDT = datatables.ColumnDT
BaseDataTables = datatables.DataTables
clean_regex = datatables.clean_regex.clean_regex


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
