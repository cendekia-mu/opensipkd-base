# DeTable

Feature yang digunakan untuk memudahkan merender datatable dalam html


```python
import colander
from opensipkd.detable import DeTable
from opensipkd.tools.buttons import btn_view, btn_add, btn_edit, btn_delete, btn_close

class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), searchable=False, 
                             orderable=False, visible=False)
    kode = colander.SchemaNode(colander.String(), width='100pt')
    nama = colander.SchemaNode(colander.String())

@view_config(route_name='provinsi',
             renderer='templates/list.pt',
             permission='provinsi')
def view_list(self):
    table = DeTable(ListSchema(), action=f"{self.home}/provinsi",
                    buttons=(btn_view, btn_add, btn_edit, btn_delete, btn_close))
    return dict(table=table.render(), scripts="")
```

## DeTable Parameter

Lihat di deklarasi `class DeTable(field.Field):`

## SchemaNode Items
```python
     colander.SchemaNode(
        NodeType, -> colander.Integer(), colander.String()
        searchable=False, 
        orderable=False, 
        visible=False,
        width="20pt",
        thousands=dict(separator='.', decimal=',', point=2) (not implemented),
        widget=widget (not implemented)
        )
    