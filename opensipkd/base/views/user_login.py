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
from random import Random
import re
from datetime import timedelta, datetime
from importlib import import_module

from pyramid.request import Response
import colander
from deform import widget, Form, ValidationFailure, Button
from pyramid.csrf import new_csrf_token, get_csrf_token
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPNotAcceptable
from pyramid.renderers import render_to_response
from pyramid.security import remember, forget
from pyramid_mailer.message import Message
from ziggurat_foundations.models.services.external_identity import \
    ExternalIdentityService
from ziggurat_foundations.models.services.user import UserService

from opensipkd.base import BASE_CLASS, DBSession, get_params
from . import one_hour, two_minutes
from ..models.users import User, ExternalIdentity
from ..models import Partner
# , Partner
from opensipkd.tools import create_now, set_user_log, get_settings
from opensipkd.tools.buttons import btn_cancel
# from .. import get_urls
from .base_views import CSRFSchema, BaseView
from pyramid.i18n import TranslationStringFactory
from ..widgets import widget_os
_ = TranslationStringFactory('login')

log = __import__("logging").getLogger(__name__)


class Login(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(
            placeholder="User Name"),
        oid="username",
    )
    password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())

    def after_bind(self, schema, kwargs):
        # super().after_bind(schema, kwargs)
        request = kwargs["request"]
        if BASE_CLASS.login_captcha:
            self["captcha"] = colander.SchemaNode(
                colander.String(),
                widget=widget_os.CaptchaWidget(
                    request=request,
                    url=request.static_url(BASE_CLASS.captcha_files)),
                oid="captcha", title=_("Captcha"))


# http://deformdemo.repoze.org/interfield/
def login_validator(form, value):
    pass


def get_login_headers(request, user):
    UserService.regenerate_security_code(user)
    headers = remember(request, user.id)
    headers.append(("Token", user.security_code))
    log.debug(headers)
    user.last_login_date = create_now()
    DBSession.add(user)
    DBSession.flush()
    return headers


class LoginUser(object):
    def __init__(self, request):
        # self.user = user
        self.request = request
        # self.identity=identity
        self.message = "Sukses Login"
        self.user = None

    def login(self, values, user=None):
        self.user = user and user or User.get_by_identity(values["username"])
        if not self.user or not UserService.check_password(
                self.user, values["password"]):
            self.message = "Login Gagal"
            set_user_log(self.message, self.request, log, values["username"])
            return
        for g in self.user.groups:
            log.debug(f"Group: {g.id} as {g.group_name}")

        # generate security_code dan simpan dalam session
        regenerate_security_code(self.user, 0.03)  # berlaku selama 1.8 menit
        # dicek pada module security get_user
        self.request.session["token"] = self.user.security_code
        return True


class Oauth2ParseExc(Exception):
    """Error parsing"""


class Oauth2UserExc(Exception):
    """Error User Found"""

from google.oauth2 import id_token
from google.auth.transport import requests

def verify_android_token(token, web_client_id):
    """
    Verifies a Google ID token from an Android client on the backend.
    
    Args:
        token (str): The ID token string received from the Android app.
        web_client_id (str): The Client ID for your *web application* in 
                             Google Cloud Console.

    Returns:
        dict: The decoded user information (claims) if the token is valid.
        Raises: ValueError if the token is invalid or unverified.
    """
    try:
        # Create a request object for making HTTP requests to Google's servers
        request = requests.Request()

        # Verify the token against Google's public keys
        # The function automatically checks the token's signature, expiry, 
        # and if it was issued by accounts.google.com.
        id_info = id_token.verify_oauth2_token(
            token, 
            request, 
            web_client_id
        )

        # Optional: Check if the token belongs to a specific Google Workspace domain (if required)
        # if id_info.get('hd') != 'yourdomain.com':
        #     raise ValueError('Not a valid hosted domain.')

        # Extract user information
        user_id = id_info['sub']
        email = id_info.get('email')
        
        print(f"Token verified for User ID: {user_id}, Email: {email}")
        return id_info

    except ValueError as e:
        # Invalid token (e.g., signature mismatch, expired, wrong audience)
        print(f"Invalid token: {e}")
        raise
    

def oauth2_login(request, params=None):
    provider_name = params and params["provider_name"] or request.params["provider_name"]
    if provider_name == "google":
        client_platform = params and params.get("platform") or request.params.get("platform") or "web"
        web_client_id = request.google_signin_client_id
        if client_platform == "android":
            id_info = verify_android_token(
                params and params["id_token"] or request.params["id_token"],
                web_client_id
            )
        else:

            from .base_google import googlesignin
            try:
                id_info = googlesignin(request, params)
            except Exception as e:
                raise Oauth2ParseExc(str(e))

        request.session["id_info"] = id_info
    
    else:
        id_info = None

    iss = id_info and re.sub(r'https?://', '', id_info['iss']) or None
    user = id_info and ExternalIdentityService.user_by_external_id_and_provider(
        id_info['sub'], iss)
    log.debug("Users : %s", user)
    log.debug("IdInfo : %s", id_info)
    if id_info and not user:
        # Insert ke
        values = {'email': id_info['email'],
                  "user_name": id_info["email"],
                  "status": 1,
                  "registered_date": datetime.now()}
        user = User.get_by_identity(values.get("email"))
        # partner = Partner.query_email(values.get("email")).first()
        # log.debug("User  : %s", user)
        # log.debug("Partner : %s", partner)
        # if user or partner:
        #     raise Oauth2UserExc(
        #         "Email sudah terdaftar silahkan login standard")

        user = User()
        user.from_dict(values)
        DBSession.add(user)
        DBSession.flush()
        DBSession.refresh(user)
        values = {'external_id': id_info['sub'],
                  'external_user_name': id_info["name"],
                  'external_email': id_info["email"],
                  'provider_name': iss,
                  "local_user_id": user.id,
                  "status": 1}
        external = ExternalIdentity()
        external.from_dict(values)
        DBSession.add(external)
        DBSession.flush()
    if user and user.status != 1:
        raise Oauth2UserExc(
            "User anda masih menunggu verifikasi atau lagi di blokir")
    #     # todo: what is this????
    #     # values['access_token']
    #     # values['alt_token']
    #     # values['token_secret']
    return user


class ViewAuth(BaseView):
    def view_login(self):
        request = self.req
        log.debug("Referrer: %s", request.referrer)
        request.session["login"] = True
        next_url = request.params.get('next', request.referrer)
        login_tpl = BASE_CLASS.login_tpl
        if not next_url:
            next_url = request.home

        if request.authenticated_userid and not request.is_xhr:  # (request):
            message = 'Anda sudah login'
            if request.is_xhr:
                user = request.user
                headers = get_login_headers(request, user)
                return xhr_response(user, headers)
                # return Response(json={"error": 
                #                       {"code": "0000",
                #                       "msg": message},
                #                       "data":[]})

            request.session.flash('Anda sudah login', 'error')
            return HTTPFound(location=f"{request.home}")

        schema = Login(request=request)
        schema = schema.bind(request=self.req)
        buttons = (Button('login', _('Login')),)
        if BASE_CLASS.allow_register:
            buttons += (Button('register', _('Register')),)
        buttons += (Button('reset', _('Reset')), btn_cancel,)

        form = Form(schema, buttons=buttons)
        message = ""
        if 'cancel' in request.POST:
            return HTTPFound(location=request.home)
        elif 'login' in request.POST:
            identity = request.POST.get('username')
            user = schema.user = User.get_by_identity(identity)
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                msg = 'Login gagal'
                set_user_log(msg, request, log, identity)
                if self.req.is_xhr:
                    d = {"error": e.error.asdict()}
                    return Response(json=d)
                    # d = self.form2dict(e.field)
                    # return Response(json={"data": d["children"]})
                request.session.flash(msg, 'error')
                return HTTPFound(location=request.route_url('base-login'))

            values = dict(c)

            # start cek external module
            pckgs = get_params('external-uim')
            if user:
                external_user = DBSession.query(ExternalIdentity).\
                    filter_by(local_user_id=user.id,
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
                    return HTTPFound(location=request.route_url('base-login'))

            else:
                login = LoginUser(self.req)
                if not login.login(values, user):
                    request.session.flash(login.message, "error")
                    if self.req.is_xhr:
                        return Response(json={"error": {"code": -1,
                                                        "msg": login.message},
                                              "data":[]})

                    next_url = f"{request.route_url('base-login')}?next={next_url}"
                    return HTTPFound(location=next_url)
            return redirect_login(request, user)

        elif 'register' in request.POST:
            return HTTPFound(location=request.route_url(BASE_CLASS.reg_form))
        elif 'reset' in request.POST:
            return HTTPFound(location=request.route_url('base-password-reset'))
        elif 'login failed' in request.session:
            r = dict(form=request.session['login failed'])
            del request.session['login failed']
            return r

        elif "provider_name" in request.params and request.params["provider_name"]:
            try:
                user = oauth2_login(request)
            except Oauth2ParseExc as e:
                login = ""
                request.session.flash(str(e), "error")
                if self.req.is_xhr:
                    # return Response(form.render())
                    d = self.form2dict(form)
                    return Response(json={"data": d["children"]})
                return render_to_response(
                    login_tpl, dict(
                        form=form,
                        message=message,
                        url=request.route_url('base-login'),
                        next_url=next_url,
                        login=login, ),
                    request=request)
            except Oauth2UserExc as e:
                request.session.flash(str(e), 'error')
                return HTTPFound(location=request.route_url('base-login'))
            if user and user.status == 1:
                return redirect_login(request, user)
        # values = {"csrf_token": new_csrf_token(request)}
        login = ""
        # if login_tpl == 'templates/login.pt':
        #     return dict(form=form.render(),
        #                 message=message,
        #                 url=get_urls(request.route_url('login')),
        #                 next_url=next_url,
        #                 login=login, )
        
        if self.req.is_xhr:
            form.set_appstruct({})
            struct = form.cstruct

            csrf_token = get_csrf_token(request)
            if not csrf_token:
                csrf_token = new_csrf_token(request)

            struct["csrf_token"] = csrf_token 
            log.debug("CSRF Token: %s", csrf_token)
            log.info("Form Struct: %s", struct)
            return self.resp_xhr({"data": struct})

            # d = self.form2dict(form)
            # d = d["children"]
            # d["permission"]=user.get_permissions()
            # return Response(json={"data": d})
        if login_tpl:

            return render_to_response(
                renderer_name=login_tpl,
                request=request,
                value=dict(form=form,
                           message=message,
                           url=request.route_url('base-login'),
                           next_url=next_url,
                           login=login, ),
            )
        return dict(form=form.render(), scripts="")

    def view_logout(self):
        request = self.req
        if not request.user:
            if "g_state" in request.cookies:
                request.response.delete_cookie("g_state", '/')

        form = self.get_form(LogoutSchema, buttons=(btn_cancel, btn_logout))
        if 'cancel' in request.POST or "home" in request.POST:
            return HTTPFound(location=request.home)

        elif "logout" in request.POST:
            form = self.get_form(LogoutSchema, buttons=(btn_home,))
            set_user_log("Logout", request, log)
            headers = forget(request)
            request.session.delete()
            request.response.headers.update(headers)
            if "g_state" in request.cookies:
                request.response.delete_cookie("g_state", '/')
            if self.req.is_xhr:
                return Response(json={"success": True,
                                      "message": "Sukses Logout",
                                      "data": []},
                                headerlist=headers)
            form.set_appstruct({"message": "Sukses Logout"})
            request.session["login"] = False

        return dict(form=form.render())

def xhr_response(user, headers):
    partner = Partner.query_email(user.email).first()
    mobile = partner and partner.mobile or ""
    nama = partner and partner.nama or ""
    data = {
        "data": 
            [{
                "user_id": user.user_name,
                "permission": user.get_permissions(),
                "token": user.security_code,
                "mobile": mobile,
                "email": user.email,
                "nama": nama,
            }]
        

    }
    return Response(json=data, headerlist=headers)

def redirect_login(request, user):
    set_user_log("Login Sukses", request, log, user.user_name)
    for g in user.groups:
        log.debug(f"Group: {g.id} as {g.group_name}")

    headers = get_login_headers(request, user)
    if request.is_xhr:
        return xhr_response(user, headers)
    next_url = request.params.get('next')

    if not next_url and request.matched_route.name == 'login':
        url = get_params('modules_default', 'base-home')
        return HTTPFound(location=request.route_url(url),
                         headers=headers)
    if not next_url:
        next_url = request.home

    return HTTPFound(location=next_url, headers=headers)


class LogoutSchema(colander.Schema):
    message = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(readonly=True),
        title=""
    )


btn_logout = Button("logout", css_class="btn-danger")
btn_home = Button("home", css_class="btn-success")


# class ViewLogout(BaseView):
# @view_config(route_name='logout', renderer="templates/logout.pt", require_csrf=False)


class ViewPassword(BaseView):
    def reset_password(self):
        request = self.req
        if request.authenticated_userid:
            return HTTPFound(location=f"{request.home}")

        resp = dict(title=_('Reset password'))
        resp['scripts'] = ""
        schema = ResetPassword(validator=reset_password_validator)
        btn_submit = Button('submit', _('Send password reset email'))
        form = Form(schema, buttons=(btn_submit, btn_cancel))
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
            set_user_log("Reset password to {}".format(user.email), request, log,
                         user.user_name)
            send_email_security_code(
                request, user, remain, 'Reset password', 'reset-password-body',
                'reset-password-body.tpl')
            self.ses.flash(
                'Email reset password sudah dikirim ke {}'.format(user.email))
            return HTTPFound(location=request.home)
        elif 'cancel' in request.POST:
            return HTTPFound(location=request.route_url('base-login'))

        resp['form'] = form.render()
        return resp

    def change_password(self):
        """
        Digunakan untuk change password 
        1. Jika sudah login maka redirect ke home
        2. Jika form valid maka akan menyimpan password baru ke database
        3. User di logout dan di redirect ke home
        """
        request = self.req

        schema = ChangePassword(validator=change_password_validator)
        btn_save = Button('save', _('Simpan'))
        btn_cancel = Button('cancel', _('Batalkan'))
        buttons = (btn_save, btn_cancel)
        form = Form(schema, buttons=buttons)
        if not request.POST:
            return dict(form=form.render(), scripts="")

        if 'save' not in request.POST:
            return HTTPFound(location=request.route_url('base-login'))

        items = request.POST.items()
        try:
            c = form.validate(items)
        except ValidationFailure as e:
            return dict(form=e.render())

        user = request.user
        user.security_code = None
        if not UserService.check_password(user, c['password']):
            request.session.flash('Password lama tidak sesuai', 'error')
            return HTTPFound(location=request.route_url('base-password'))

        UserService.set_password(user, c['new_password'])
        self.db_session.add(user)
        self.db_session.flush()
        headers = forget(request)
        request.session.flash('Password baru Anda sudah disimpan.')
        set_user_log("Change Password", request, log)
        return HTTPFound(location=f"{request.home}", headers=headers)

    def change_password_request(self):
        """
        Digunakan untuk change password url dari email (register, reset password)
        1. Jika sudah login maka redirect ke home
        2. Jika code tidak ada atau tidak valid maka akan redirect ke get code 
        2. Jika code valid maka akan menampilkan form untuk change password
        3. Jika form valid maka akan menyimpan password baru ke database
        """
        request = self.req
        if request.authenticated_userid:
            request.session.flash('Anda sudah login', 'error')
            return HTTPFound(location=f"{request.home}")
        code = request.matchdict['code']
        q = DBSession.query(User).filter_by(security_code=code)
        user = q.first()
        now = create_now()
        if not user or now - user.security_code_date > one_hour:
            request.session.flash('Security code expired', 'error')
            return HTTPFound(location=request.route_url('base-login'))

        schema = ChangePasswordRequest(validator=change_password_validator)
        btn_save = Button('save', _('Simpan'))
        btn_cancel = Button('cancel', _('Batalkan'))
        buttons = (btn_save, btn_cancel)
        form = Form(schema, buttons=buttons)
        if not request.POST:
            return dict(form=form.render(), scripts="")
        if 'save' not in request.POST:
            return HTTPFound(location=request.route_url('base-login'))

        items = request.POST.items()
        try:
            c = form.validate(items)
        except ValidationFailure as e:
            return dict(form=e.render())

        user.security_code = None
        UserService.set_password(user, c['new_password'])
        DBSession.add(user)
        headers = get_login_headers(request, user)
        request.session.flash('Password baru Anda sudah disimpan.')
        set_user_log("Change Password", request, log)
        return HTTPFound(location=f"{request.home}", headers=headers)

    def view_recreate_api_key(self):
        request = self.req
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
            return HTTPFound(location=f"{request.home}")
        request.user.api_key = api_key = generate_api_key()
        DBSession.add(request.user)
        msg = 'API Key Anda yang baru {}'.format(api_key)
        request.session.flash(msg)
        return HTTPFound(location=f"{request.home}")

    def get_passcode(self):
        if not self.req.authenticated_userid:
            return HTTPNotFound("Anda harus login dahulu")
        
        if "mail.sender_name" not in self.settings or 'mail.username' not in self.settings:
            return HTTPNotAcceptable("Anda harus login dahulu")

        user = self.req.user
        user.security_code = Random().randint(10000, 99999)
        DBSession.add(user)
        DBSession.flush()
        minutes = two_minutes
        data = dict(passcode=user.security_code, minutes=minutes)
        here = os.path.abspath(os.path.dirname(__file__))
        body_file = os.path.join(here, 'passcode-body.tpl')
        with open(body_file, encoding='utf-8') as f:
            body_tpl = f.read()
        subject = f'{user.security_code} Verifikasi Passcode'
        body_msg_id = 'passcode-body'
        body = _(body_msg_id, default=body_tpl, mapping=data)
        sending_mail(self.req, user, subject, body)
        return dict(data={"message": "Passcode sudah dikirim ke email Anda"})

class ChangePasswordRequest(colander.Schema):
    new_password = colander.SchemaNode(
        colander.String(), widget=widget.CheckedPasswordWidget())


class ChangePassword(ChangePasswordRequest):
    new_password = colander.SchemaNode(
        colander.String(), widget=widget.CheckedPasswordWidget())
    password = colander.SchemaNode(colander.String(),
                                   widget=widget.PasswordWidget(),
                                   title=_("Old Password"))


def change_password_validator(form, value):
    pass
    # exc = colander.Invalid(form, '')
    # user = form.request.user
    # if not UserService.check_password(user, value["password"]):
    # exc["password"] = 'Login Failed'
    # raise exc

    # if value['new_password'] != value['retype_password']:
    # exc["new_password"] = 'Retype mismatch.'
    # exc["retype_password"] = 'Retype mismatch.'
    # raise exc


######################
# Buat ulang API Key #
######################
class APIKey(colander.Schema):
    api_key = colander.SchemaNode(
        colander.String(), widget=widget.TextInputWidget(readonly=True))


def generate_api_key():
    return UserService.generate_random_string(64)


##################
# Reset password #
##################
class ResetPassword(colander.Schema):
    email = colander.SchemaNode(
        colander.String(), title=_('Email'),
        description=_(
            'email-reset-password',
            default='Enter your email address and we will send you '
                    'a link to reset your password.')
    )


def reset_password_validator(form, value):
    user = form.user
    if not user or not user.status:
        raise colander.Invalid(form, _('Invalid email'))


def security_code_age(user):
    now = create_now()
    if user.security_code_date:
        return now - user.security_code_date
    return timedelta(minutes=1)


def send_email_security_code(
        request, user, time_remain, subject, body_msg_id, body_default_file,
        **kwargs):
    settings = get_settings()
    password = kwargs.get("password", "")
    if 'mail.sender_name' not in settings or 'mail.username' not in settings:
        return

    url = '{}/password/{}/request?key={}'.format(
        request.home, user.security_code, password)

    minutes = int(time_remain.seconds / 60)
    data = dict(url=url, minutes=minutes)
    here = os.path.abspath(os.path.dirname(__file__))
    body_file = os.path.join(here, body_default_file)
    with open(body_file) as f:
        body_tpl = f.read()
    body = _(body_msg_id, default=body_tpl, mapping=data)
    # body = request.localizer.translate(body)
    # sender = '{} <{}>'.format(
    #     settings['mail.sender_name'], settings['mail.username'])
    # subject = request.localizer.translate(_(subject))
    # message = Message(
    #     subject=subject, sender=sender, recipients=[user.email], body=body)
    # mailer = request.registry['mailer']
    # mailer.send(message)
    sending_mail(request, user, subject, body)


def sending_mail(request, user, subject, body):
    settings = get_settings()
    body = request.localizer.translate(body)
    sender = '{} <{}>'.format(
        settings['mail.sender_name'], settings['mail.username'])
    subject = request.localizer.translate(_(subject))
    message = Message(
        subject=subject, sender=sender, recipients=[user.email], body=body)
    mailer = request.registry['mailer']
    mailer.send(message)


def send_email_pending(
        request, user, subject, body_msg_id, body_default_file):
    settings = get_settings()
    if 'mail.sender_name' not in settings or 'mail.username' not in settings:
        return

    here = os.path.abspath(os.path.dirname(__file__))
    body_file = os.path.join(here, body_default_file)
    with open(body_file) as f:
        body_tpl = f.read()
    body = _(body_msg_id, default=body_tpl)
    sending_mail(request, user, subject, body)


def regenerate_security_code(user, hour=1.0):
    hour = timedelta(float(hour) / 24.0)
    age = security_code_age(user)
    remain = hour - age
    if user.security_code and age < hour and remain > two_minutes:
        log.debug("Security code: %s", user.security_code)
        return remain
    UserService.regenerate_security_code(user)
    user.security_code_date = create_now()
    log.debug("Security code: %s", user.security_code)
    DBSession.add(user)
    return hour
