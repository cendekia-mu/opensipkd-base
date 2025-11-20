import os

import colander
from deform import (Form, widget, FileData, )
from deform.interfaces import FileUploadTempStore
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from opensipkd.tools import (get_ext, dict_to_str, )
from .base_views import CSRFSchema
# from .. import get_urls


def route_list(request, p={}):
    q = dict_to_str(p)
    return HTTPFound(location=request.route_url('base-upload-logo', _query=q))


##########
# Unggah #
##########
# class UploadLogo(SaveFile):
#     def save(self, fs):
#         input_file = fs.file
#         ext = get_ext(fs.filename)
#         fullpath = self.create_fullpath(ext)
#         output_file = open(fullpath, 'wb')
#         input_file.seek(0)
#         while True:
#             data = input_file.read(2 << 16)
#             if not data:
#                 break
#             output_file.write(data)
#         output_file.close()
#         return fullpath


tmpstore = FileUploadTempStore()


class AddSchema(CSRFSchema):
    upload = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(tmpstore),
        title='Unggah')
    image_for = colander.SchemaNode(
        colander.String(),
        widget=widget.SelectWidget(values=(('oth', "Other"), ('logo', "Logo"),
                                           ('bg', "Background"),
                                           ('mobile', "Mobile Files"),)),
        title='Peruntukan')


def get_form(request, schema_cls):
    schema = schema_cls()
    schema = schema.bind(request=request)
    return Form(schema, buttons=('simpan', 'batal'))


@view_config(route_name='base-upload-logo',
             renderer='templates/form8.pt',
             permission='upload-logo', require_csrf=True)
def view_file(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            input_file = request.POST['upload'].file
            filename = request.POST['upload'].filename.lower()
            ext = get_ext(filename).lower()
            if ext.lower() not in ['.png', '.ico']:
                request.session.flash("File harus format 'png' atau 'ico'", 'error')
                return dict(form=form.render())
            _here = os.path.dirname(__file__)
            static_path = os.path.join(os.path.dirname(_here), 'static')
            fname = filename
            if request.POST["image_for"] == "logo":
                fname = f"logo{ext}"
            elif request.POST["image_for"] == "bg":
                fname = f"background{ext}"
            elif request.POST["image_for"] == "mobile":
                mobile_static_path = request.registry.settings.get(
                    'mobile_static_path', None)
                if not mobile_static_path:
                    request.session.flash("Mobile static path belum dikonfigurasi", 'error')
                    return dict(form=form.render())
                static_path = os.path.join(mobile_static_path)

            typ = ext == '.png' and "img" or 'icon'
            folder = os.path.join(static_path, typ)
            if not os.path.exists(folder):
                os.makedirs(folder)

            fullpath = os.path.join(folder, fname)
            output_file = open(fullpath, 'wb')
            input_file.seek(0)
            while True:
                data = input_file.read(2 << 16)
                if not data:
                    break
                output_file.write(data)
            request.session.flash(f"Sukses upload {fname}")

        return route_list(request)
    return dict(form=form.render(), scripts="")
