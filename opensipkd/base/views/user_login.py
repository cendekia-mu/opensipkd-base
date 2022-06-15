"""
Perubahan Mendasar dari fungsi login adalah:
1. Penambahan parameter external-uim
2. Apabila parameter external-uim != None maka akan load module sesuai dengan
   isi dari external-uim
3. Dengan adanya parameter ini saat terjadi login maka yang pertama kali di cek
    - Jika user tidak ada dalam lokal maka akan diforward login ke
      (external_uim).login
    - Jika user ada
        - Jika user terdapat dan ExternalIdentity maka user lofin akan diforward
          ke module External Identity
    - Jika tidak memenuhi syarat diatas maka akan login seperti normal login

4. Module external-uim harus terdapat function
    def login(user_id, password, user=None):
        ............
        ............
        return user

    result object dari fungsi tersebut harus berupa class User()
"""
import os
from importlib import import_module

import colander
from deform import widget, Form, ValidationFailure, Button
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.security import remember, forget
from pyramid.view import view_config
from ziggurat_foundations.models.services.external_identity import ExternalIdentityService
from ziggurat_foundations.models.services.user import UserService

from opensipkd.base import DBSession, get_params
from opensipkd.base.models import User, ExternalIdentity
from opensipkd.tools import create_now, set_user_log, get_settings
from opensipkd.base.views import _, one_hour, two_minutes
from pyramid_mailer.message import Message

log = __import__("logging").getLogger(__name__)


class Login(colander.Schema):
    username = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())


# http://deformdemo.repoze.org/interfield/
def login_validator(form, value):
    pass


def get_login_headers(request, user):
    headers = remember(request, user.id)
    user.last_login_date = create_now()
    DBSession.add(user)
    DBSession.flush()
    return headers


@view_config(route_name='login', renderer='templates/login.pt')
def view_login(request):
    next_url = request.params.get('next', request.referrer)
    login_tpl = get_params('login_tpl', 'templates/login.pt')
    if not next_url:
        next_url = request.route_url('home')  # get_params('_host')+

    if request.authenticated_userid:  # (request):
        request.session.flash('Anda sudah login', 'error')
        return HTTPFound(location=f"{request.route_url('home')}")

    schema = Login(validator=login_validator)
    form = Form(schema, buttons=('login',))
    if 'login' in request.POST:
        identity = request.POST.get('username')
        user = schema.user = User.get_by_identity(identity)
        controls = request.POST.items()
        try:
            c = form.validate(controls)
        except ValidationFailure as e:
            msg = 'Login gagal'
            set_user_log(msg, request, log, identity)
            request.session.flash(msg, 'error')
            return HTTPFound(location=request.route_url('login'))

        values = dict(c)
        # start cek external module
        pckgs = get_params('external-uim')
        if user:
            external_user = DBSession.query(ExternalIdentity) \
                .filter_by(local_user_id=user.id,
                           external_user_name=identity).first()
            pckgs = external_user and pckgs or None

        if pckgs:
            # user_name = user and user.user_name or ""
            m = import_module(pckgs)
            try:
                user = m.login(identity, values['password'], user)
            except Exception as e:
                log.warn(str(e))
                request.session.flash(str(e), "error")
                return HTTPFound(location=request.route_url('login'))

        else:
            if not user or not UserService.check_password(user, values['password']):
                msg = "Login Gagal"
                set_user_log(msg, request, log, identity)
                request.session.flash(msg, "error")
                next_url = f"{request.route_url('login')}?next={next_url}"
                return HTTPFound(location=next_url)

        return redirect_login(request, user)

    elif 'register' in request.POST:
        register_form = get_params("register_form", 'register-external')
        return HTTPFound(location=request.route_url(register_form))

    elif 'login failed' in request.session:
        r = dict(form=request.session['login failed'])
        del request.session['login failed']
        return r

    elif "provider_name" in request.params and request.params["provider_name"]:
        provider_name = request.params["provider_name"]
        if provider_name == "google":
            from .base_google import googlesignin

            # user = googlesignin(request)
            id_info = googlesignin(request)
            request.session["id_info"] = id_info
            try:
                pass
            except ValueError as e:
                request.session.flash(e, 'error')
                raise HTTPNotFound
        else:
            id_info = None

        user = id_info and ExternalIdentityService. \
            user_by_external_id_and_provider(id_info['sub'], id_info['iss'])
        if id_info and not user:
            request.session.flash('Silahkan Melakukan Registrasi')
            register_form = get_params("register_form", 'register-external')
            return HTTPFound(location=request.route_url(register_form, _query=id_info), detail=id_info)

        if user:
            return redirect_login(request, user)
    message = ""
    login = ""
    return render_to_response(login_tpl,
                              dict(form=form.render(),
                                   message=message,
                                   url=request.route_url('login'),
                                   next_url=next_url,
                                   login=login, ),
                              request=request)

    # return dict(
    # )


def redirect_login(request, user):
    set_user_log("Login Sukses", request, log, user.user_name)
    headers = get_login_headers(request, user)
    request.session.flash("Sukses Login")
    next_url = request.params.get('next')
    if not next_url and request.matched_route.name == 'login':
        url = get_params('modules_default', 'home')
        return HTTPFound(location=request.route_url(url),
                         headers=headers)
    return HTTPFound(location=next_url, headers=headers)


@view_config(route_name='logout', renderer="templates/logout.pt")
def view_logout(request):
    if 'batal' in request.POST:
        log.info(request.route_url('home'))
        return HTTPFound(location=f"{request.route_url('home')}", )
    elif request.POST:
        set_user_log("Logout", request, log)
        headers = forget(request)
        request.session.delete()
        return HTTPFound(location=f"{request.route_url('home')}",
                         headers=headers)

    return dict()


class ChangePassword(colander.Schema):
    new_password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())
    retype_password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())


def change_password_validator(form, value):
    if value['new_password'] != value['retype_password']:
        raise colander.Invalid(form, 'Retype mismatch.')


@view_config(route_name='change-password', renderer='templates/change-password.pt')
def view_change_password(request):
    if request.authenticated_userid:
        request.session.flash('Anda sudah login', 'error')
        return HTTPFound(location=f"{request.route_url('home')}")
    schema = ChangePassword(validator=change_password_validator)
    btn_save = Button('save', _('Simpan'))
    btn_cancel = Button('cancel', _('Batalkan'))
    buttons = (btn_save, btn_cancel)
    form = Form(schema, buttons=buttons)
    if not request.POST:
        return dict(form=form.render())
    if 'save' not in request.POST:
        return HTTPFound(location=request.route_url('login'))
    items = request.POST.items()
    try:
        c = form.validate(items)
    except ValidationFailure as e:
        return dict(form=e.render())
    code = request.matchdict['code']
    q = DBSession.query(User).filter_by(security_code=code)
    user = q.first()
    if not user or \
            create_now() - user.security_code_date > one_hour:
        request.session.flash('Security code expired', 'error')
        return HTTPFound(location=request.route_url('login'))
    user.security_code = None
    UserService.set_password(user, c['new_password'])
    DBSession.add(user)
    headers = get_login_headers(request, user)
    request.session.flash('Password baru Anda sudah disimpan.')
    set_user_log("Change Password", request, log)
    return HTTPFound(location=f"{request.route_url('home')}", headers=headers)


######################
# Buat ulang API Key #
######################
class APIKey(colander.Schema):
    api_key = colander.SchemaNode(
        colander.String(), widget=widget.TextInputWidget(readonly=True))


def generate_api_key():
    return UserService.generate_random_string(64)


@view_config(
    route_name='recreate-api-key', renderer='templates/recreate-api-key.pt', permission='view')
def view_recreate_api_key(request):
    if not request.user.api_key:
        return HTTPNotFound()
    schema = APIKey()
    btn_submit = Button('recreate', _('Buat ulang'))
    btn_cancel = Button('cancel', _('Batalkan'))
    buttons = (btn_submit, btn_cancel)
    form = Form(schema, buttons=buttons)
    if not request.POST:
        d = dict(api_key=request.user.api_key)
        return dict(form=form.render(appstruct=d))
    if 'recreate' not in request.POST:
        return HTTPFound(location=f"{request.route_url('home')}")
    request.user.api_key = api_key = generate_api_key()
    DBSession.add(request.user)
    msg = 'API Key Anda yang baru {}'.format(api_key)
    request.session.flash(msg)
    return HTTPFound(location=f"{request.route_url('home')}")


##################
# Reset password #
##################
class ResetPassword(colander.Schema):
    email = colander.SchemaNode(
        colander.String(), title=_('Email'),
        description=_(
            'email-reset-password',
            default='Enter your email address and we will send you ' \
                    'a link to reset your password.')
    )


def reset_password_validator(form, value):
    user = form.user
    if not user or not user.status:
        raise colander.Invalid(form, _('Invalid email'))


def security_code_age(user):
    return create_now() - user.security_code_date


def send_email_security_code(
        request, user, time_remain, subject, body_msg_id, body_default_file):
    settings = get_settings()
    if 'mail.sender_name' not in settings \
            or 'mail.username' not in settings:
        return

    # if 'base_url' not in settings:
    #     return

    url = '{}password/{}'.format(
        request.route_url('home'), user.security_code)
    minutes = int(time_remain.seconds / 60)
    data = dict(url=url, minutes=minutes)
    here = os.path.abspath(os.path.dirname(__file__))
    body_file = os.path.join(here, body_default_file)
    with open(body_file) as f:
        body_tpl = f.read()
    body = _(body_msg_id, default=body_tpl, mapping=data)
    body = request.localizer.translate(body)
    sender = '{} <{}>'.format(
        settings['mail.sender_name'], settings['mail.username'])
    subject = request.localizer.translate(_(subject))
    message = Message(
        subject=subject, sender=sender, recipients=[user.email], body=body)
    mailer = request.registry['mailer']
    mailer.send(message)


def regenerate_security_code(user):
    age = security_code_age(user)
    remain = one_hour - age
    if user.security_code and age < one_hour and remain > two_minutes:
        return remain
    UserService.regenerate_security_code(user)
    user.security_code_date = create_now()
    DBSession.add(user)
    return one_hour


@view_config(route_name='reset-password', renderer='templates/reset-password.pt')
def view_reset_password(request):
    if request.authenticated_userid:
        return HTTPFound(location=f"{request.route_url('home')}")

    resp = dict(title=_('Reset password'))
    schema = ResetPassword(validator=reset_password_validator)
    btn_submit = Button('submit', _('Send password reset email'))
    form = Form(schema, buttons=(btn_submit,))
    if 'submit' in request.POST:
        controls = request.POST.items()
        identity = request.POST.get('email')
        q = DBSession.query(User).filter_by(email=identity)
        schema.user = user = q.first()
        try:
            c = form.validate(controls)
        except ValidationFailure:
            resp['form'] = form.render()
            return resp
        remain = regenerate_security_code(user)
        set_user_log("Reset password to {}".format(user.email), request, log, user.user_name)
        send_email_security_code(
            request, user, remain, 'Reset password', 'reset-password-body',
            'reset-password-body.tpl')
        return HTTPFound(location=request.route_url('reset-password-sent'))
    resp['form'] = form.render()
    return resp


@view_config(
    route_name='reset-password-sent', renderer='templates/reset-password-sent.pt')
def view_reset_password_sent(request):
    return dict(title=_('Reset password'))
