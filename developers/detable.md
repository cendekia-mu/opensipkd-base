# DeTable

Feature yang digunakan untuk memudahkan merender datatable dalam html

```python
import colander
from opensipkd.detable import DeTable
from opensipkd.tools.buttons import btn_view, btn_add, btn_edit, btn_delete, btn_close
from datatables import ColumnDT

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
                    action_suffix="/grid/act",
                    buttons=(btn_view, btn_add, btn_edit, btn_delete, btn_close))
    return dict(table=table.render(), scripts="")


# /provinsi/add
@view_config(route_name='provinsi-add',
             renderer='templates/form_input.pt',
             permission='provinsi')
def view_add(request):
    pass


# /provinsi/{id}/edit
@view_config(route_name='provinsi-edit',
             renderer='templates/form_input.pt',
             permission='provinsi')
def view_edit(request):
    pass


# /provinsi/{id}/delete
@view_config(route_name='provinsi-delete',
             renderer='templates/form_input.pt',
             permission='provinsi')
def view_delete(request):
    pass


# /provinsi/{id}/view
@view_config(route_name='provinsi-view',
             renderer='templates/form_input.pt',
             permission='provinsi')
def view_view(request):
    pass


# /provinsi/{act}/act
@view_config(route_name='provinsi-act',
             renderer='json',
             permission='provinsi')
def view_act(request):
    url_dict = request.matchdict
    if url_dict['act'] == 'grid':
        columns = [ColumnDT(ResProvinsi.id, mData='id'),
                   ColumnDT(ResProvinsi.kode, mData='kode'),
                   ColumnDT(ResProvinsi.nama, mData='nama'),
                   ColumnDT(ResProvinsi.status, mData='status'), ]
        query = DBSession.query().select_from(ResProvinsi)
        row_table = DataTables(request.GET, query, columns)
        return row_table.output_result()
```

## Contoh HTML

```html

<html metal:use-macro="load: ./base3.1.pt"
      tal:define="
        home request.route_url('home');">
<div metal:fill-slot="content">
    <div class="jarviswidget jarviswidget-color-blueLight"> <!-- jarviswidget -->
        <div tal:content="structure table"></div>
    </div>
</div>
</html>
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
    