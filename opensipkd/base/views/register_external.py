# # Module ini digunakan untuk registrasi user external
# # Restriction dari module ini tidak boleh diubah emailnya
# from email.utils import parseaddr
# import colander
# from deform import (Form, widget, ValidationFailure, Button)
# from opensipkd.tools.api import custom_error
# from opensipkd.base.views.user_login import get_login_headers
# from opensipkd.base.views.user import insert as save_user
# from pyramid.httpexceptions import HTTPFound
# from pyramid.i18n import TranslationStringFactory
# from pyramid.view import view_config
# from ziggurat_foundations.models.services.user import UserService
#
# # from . import get_login_headers
# # from .register import mobile_found_partner, save_partner, nik_found
# from .user_group import save as save_groups
# from opensipkd.models import DBSession, Partner, Group, ExternalIdentity, User, ExternalIdentityService
# from opensipkd.tools import get_settings
# from opensipkd.tools.captcha import get_captcha
# from ..views import BaseView
#
# # from .user import email_validator
# _ = TranslationStringFactory('user')
#
#
# def email_validator(node, value):
#     name, email = parseaddr(value)
#     if not email or email.find('@') < 0:
#         raise colander.Invalid(node, 'Invalid email format')
#
#
# class PrimarySchema(colander.Schema):
#     kode = colander.SchemaNode(
#         colander.String(),
#         widget=widget.TextInputWidget(),
#         oid="kode",
#         title="NIK"
#     )
#
#     email = colander.SchemaNode(
#         colander.String(),
#         widget=widget.TextInputWidget(readonly=True),
#         missing=colander.drop,
#         title="E-mail",
#         validator=email_validator,
#         oid="email")
#
#
# class SecondarySchema(colander.Schema):
#     nama = colander.SchemaNode(
#         colander.String(),
#         oid="nama")
#     alamat_1 = colander.SchemaNode(
#         colander.String(),
#         title="Alamat",
#         oid="alamat_1")
#     alamat_2 = colander.SchemaNode(
#         colander.String(),
#         title="",
#         missing=colander.drop,
#         oid="alamat_2")
#
#
# class RegSchema(colander.Schema):
#     primari = PrimarySchema()
#     mobile = colander.SchemaNode(
#         colander.String(),
#         widget=widget.TextInputWidget(),
#         oid="mobile")
#     secondari = SecondarySchema()
#     captcha = colander.SchemaNode(
#         colander.String(),
#         oid="captcha")
#
#
# class RegEditSchema(colander.Schema):
#     primari = PrimarySchema()
#     mobile = colander.SchemaNode(
#         colander.String(),
#         widget=widget.TextInputWidget(readonly=True),
#         missing=colander.drop,
#         oid="mobile")
#     secondari = SecondarySchema()
#     id = colander.SchemaNode(
#         colander.Integer(),
#         missing=colander.drop,
#         widget=widget.HiddenWidget(),
#         )
#
#
# def form_validator(form, value):
#     # value.update(value['secondari'])
#     # value.update(value['primari'])
#
#     def err_captcha():
#         msg = 'Captcha harus diisi'
#         raise colander.Invalid(form, msg)
#
#     def err_email():
#         raise colander.Invalid(
#             form, 'e-mail %s sudah ada yang menggunakan' % value['email'])
#
#     def err_nik(kode):
#         raise colander.Invalid(
#             form, 'NIK %s sudah ada yang menggunakan' % kode)
#
#     def err_login():
#         raise colander.Invalid(
#             form, 'User atau Password tidak sesuai')
#
#     def err_mobile():
#         raise colander.Invalid(
#             form, 'Nomor %s sudah ada yang menggunakan' % value['mobile'])
#
#     request = form.request
#     # Cek Login
#     if 'password' in value:
#         user = form.request.user
#         if not user or not UserService.check_password(user, value['password']):
#             err_login()
#
#     if not request.user:
#         if 'captcha' not in value or not value['captcha'] \
#                 or 'captcha' not in request.session or not request.session['captcha']:
#             err_captcha()
#
#         captcha = 'captcha' in value and value['captcha'].upper() or None
#
#         if not captcha or captcha != request.session['captcha']:
#             err_captcha()
#
#     if 'id' in request.matchdict:
#         uid = request.matchdict['id']
#         q = DBSession.query(Partner).filter_by(id=uid)
#         partner = q.first()
#     else:
#         partner = None
#
#     # CEK NIK apakah Sudah Ada di tabel Partner?
#
#     primari = value['primari']
#     kode = 'kode' in primari and primari['kode'] or ""
#     if not kode:
#         kode = primari["email"]
#
#     found_nik = nik_found(primari['kode'])
#     if partner:
#         if found_nik and found_nik.id != partner.id:
#             err_nik(kode)
#     elif found_nik:
#         err_nik(kode)
#
#     if 'mobile' in value and value['mobile']:
#         mobile = value['mobile']
#
#         found = mobile_found_partner(mobile).first()
#         if partner:
#             if found and found.id != partner.id:
#                 err_mobile()
#         elif found:
#             err_mobile()
#
#     # user = email_found_user(email)
#     # # jika ada user dan statusnya register di buat error
#     # if user and not form.request.user:
#     #     err_email()
#     #
#     # # jika update periksa apakah email digunakan oleh user lain
#     # if user and form.request.user:
#     #     if user.id != form.request.user.id:
#     #         err_email()
#
#
# def get_form(request, class_form, buttons=None, validator=form_validator):
#     schema = class_form(validator=validator)
#     schema = schema.bind()
#     schema.request = request
#     if buttons:
#         return Form(schema, buttons=buttons)
#     return Form(schema, buttons=('batal', 'simpan'))
#
#
# def save(values, user=None, row=None, request=None):
#     """
#     Digunakan untuk menyimpan User External
#     :param values: dictionary of
#         external_id
#         external_user_name
#         provider_name
#         access_token
#         alt_token
#         token_secret
#
#     :param user: object user if none create new user
#     :param row: object external_identify if none create new
#     :return: user objek
#     """
#     if not user:
#         user_ = dict(user_name=values['external_user_name'],
#                      email=values['external_email'])
#         user, remail = save_user(request, user_)
#
#     if not row:
#         row = ExternalIdentity()
#
#     row.from_dict(values)
#     # try:
#     # except:
#     #     transaction.rollback()
#
#     row.local_user_id = user.id
#     DBSession.add(row)
#     DBSession.flush()
#     return user
#
#
# def save_request(values, request, row=None):
#     if 'id' in request.matchdict:
#         values['id'] = request.matchdict['id']
#
#     id_info = request.session['id_info']
#     user = ExternalIdentityService.user_by_external_id_and_provider(
#         id_info['sub'], id_info['iss'])
#     if not user:
#         user = save(values, user, row, request)
#
#     partner = Partner.query_email(id_info['email']).first()
#     # if not partner:
#     values['email'] = id_info['email']
#     if 'kode' not in values and not values['kode']:
#         values['kode'] = id_info['email']
#     values['user_id'] = user.id
#     save_partner(values, partner)
#     ##Untuk SIMKEL##
#     settings = get_settings()
#     if 'default_group'in settings:
#         groups = settings['default_group'].split(',')
#         for group in groups:
#             group_data = Group.query_group_name(group).first()
#             if not group_data:
#                 raise custom_error(-1,"Group Not Found.")
#             data=dict(group_id= group_data.id,
#                         user_id= user.id)
#             save_groups(data,None)
#     return user
#
#
# def route_list(request):
#     return HTTPFound(location=request.route_url('home'))
#
#
# def reg_buttons():
#     btn_register = Button(name='register', css_class='btn-success', type="submit")
#     btn_cancel = Button(name='batal', css_class='btn-primary', type="submit")
#     return btn_cancel, btn_register
#
#
# class RegistrasiExternal(BaseView):
#     @view_config(route_name='register-external', renderer='templates/register.pt')
#     def view_add(self):
#         request = self.req
#         if 'id_info' not in request.session:
#             return HTTPFound(location=request.route_url("login"))
#
#         if request.user:
#             partner = Partner.query_email(request.user.email).first()
#             if partner:
#                 return HTTPFound(location=request.route_url("profile-external",
#                                                             id=partner.id))
#
#         id_info = request.session['id_info']
#         form = get_form(request, RegSchema, reg_buttons())
#         if request.POST:
#             if 'register' in request.POST:
#                 controls = request.POST.items()
#                 try:
#                     controls = form.validate(controls)
#                 except ValidationFailure as e:
#                     values = e.cstruct
#                     values['primari']['email'] = id_info['email']
#                     # values['detail']['captcha']
#                     form.set_appstruct(values)
#                     return dict(form=form, captcha=get_captcha(request), scripts="")
#
#                 dicts = dict(controls)
#                 values = dicts['primari']
#                 values.update(dicts['secondari'])
#                 values['mobile'] = dicts['mobile']
#                 values['email'] = id_info['email']
#                 values['external_id'] = id_info['sub']
#                 values['external_user_name'] = id_info["name"]
#                 values['external_email'] = id_info["email"]
#                 values['provider_name'] = id_info["iss"]
#                 # todo: what is this????
#                 # values['access_token']
#                 # values['alt_token']
#                 # values['token_secret']
#                 user = save_request(values, request)
#
#                 headers = get_login_headers(request, user)
#                 request.session.flash('Registrasi Sukses.')
#                 if 'captcha' in request.session:
#                     del(request.session['captcha'])
#                 return HTTPFound(location=request.route_url('home'), headers=headers)
#
#         values = dict()
#         values['primari'] = dict(
#             email=id_info['email'])
#
#         values['secondari'] = dict(
#             nama=id_info['name'])
#
#         if request.user:
#             partner = Partner.query_user_id(request.user.id).first()
#             if partner:
#                 values['primari'].update(partner.to_dict())
#                 values['secondari'].update(partner.to_dict())
#
#         form.set_appstruct(values)
#         # return dict()
#         # return dict(captcha=get_captcha(request))
#         return dict(form=form.render(), captcha=get_captcha(request), scripts="")
#
#     @view_config(route_name='profile-external', renderer='templates/register.pt',
#                  permission='view')
#     def profile_external(self):
#         request = self.req
#         query = query_id(request)
#         row = query.first()
#         if not row:
#             return HTTPFound(location=request.route_url("register-external"))
#
#         form = get_form(request, RegEditSchema)
#         if request.POST:
#             if 'simpan' in request.POST:
#                 controls = request.POST.items()
#                 try:
#                     controls = form.validate(controls)
#                 except ValidationFailure as e:
#                     values = e.cstruct
#                     form.set_appstruct(values)
#                     return dict(form=form)
#                 values = dict(controls)
#                 save_request(values['secondari'], request, row)
#                 request.session.flash('Sukses Update Profile.')
#
#             return route_list(request)
#
#         values = row.to_dict()
#         email = row.email
#         emails = email.split('@')
#         result = emails[0][:3]
#         for a in range(3, len(emails[0])):
#             result = "".join([result, "*"])
#
#         n = emails[1].find(".")
#         provider = emails[1][:n]
#         ext = emails[1][n:]
#         result = "".join([result, '@', provider[:3]])
#
#         for a in range(3, len(provider)):
#             result = "".join([result, "*"])
#
#         result = "".join([result, ext])
#         mobile = row.mobile
#         result2 = "".join([mobile[:4], "****", mobile[8:]])
#         # values['email'] = result
#         values['secondari'] = row.to_dict()
#         values['primari'] = row.to_dict()
#         values['primari']["email"] = result
#         values["mobile"] = result2
#
#         form.set_appstruct(values)
#         return dict(form=form, captcha=None)
#
#
# ########
# # Edit #
# ########
# def query_id(request):
#     return DBSession.query(Partner).\
#         join(User, Partner.user_id == User.id).\
#         filter(User.id == request.user.id)
#
#
# def id_not_found(request):
#     msg = 'Register ID %s Tidak Ditemukan.' % request.matchdict['id']
#     request.session.flash(msg, 'error')
#     return route_list(request)
