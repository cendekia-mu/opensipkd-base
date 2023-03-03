import os

import colander
from deform import (
    Form,
    widget,
    FileData,
)
from deform.interfaces import FileUploadTempStore
from opensipkd.tools import (
    get_ext,
    dict_to_str,
)
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from .. import get_urls

# from unggah import DbUpload
def route_list(request, p={}):
    q = dict_to_str(p)
    return HTTPFound(location=get_urls(request.route_url('upload-logo', _query=q)))


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


class AddSchema(colander.Schema):
    upload = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(tmpstore),
        title='Unggah')
    typ = colander.SchemaNode(
        colander.String(),
        widget=widget.SelectWidget(values=(('img', "Image"), ('icon', "Icon"))),
        title='Jenis')


def get_form(schema_cls):
    schema = schema_cls()
    return Form(schema, buttons=('simpan', 'batal'))


@view_config(route_name='upload-logo',
             renderer='templates/upload.pt',
             permission='upload-logo')
def view_file(request):
    form = get_form(AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            input_file = request.POST['upload'].file
            filename = request.POST['upload'].filename.lower()
            ext = get_ext(filename).lower()
            if ext.lower() not in ['.png', '.ico']:
                request.session.flash('File harus format png', 'error')
                return dict(form=form.render())

            _here = os.path.dirname(__file__)
            static_path = os.path.join(os.path.dirname(_here), 'static')
            if filename.startswith('logo'):
                fname = f"logo{ext}"
            elif filename.startswith('background'):
                fname = f"background{ext}"
            else:
                fname = filename

            folder = os.path.join(static_path, request.POST['typ'])
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

        return route_list(request)
    return dict(form=form.render())
