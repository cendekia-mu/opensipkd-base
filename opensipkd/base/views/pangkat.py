import colander
from deform import widget
from opensipkd.models import DBSession, Pangkat

def get_pangkat_list():
    r = []
    q = DBSession.query(Pangkat).order_by(Pangkat.kode)
    for row in q:
        g = (str(row.id), f"{row.kode}/ {row.nama}")
        r.append(g)
    return r


@colander.deferred
def pangkat_widget(node, kw):
    values = kw.get('pangkat_list', [])
    return widget.Select2Widget(values=values)


def pangkat_widget_form():
    return widget.AutocompleteInputWidget(
        size=60, min_length=3,
        requirements=(("typeahead", None), ("deform", None),
                      {"js": "opensipkd.base:static/js/form/pangkat_form.js"}),
    )
