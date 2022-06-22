from google.auth.transport import requests
from google.oauth2 import id_token
from opensipkd.base import get_params
from pyramid.view import (view_config, )

from ..models import User
from opensipkd.tools import get_settings
import json


def validate_user(request, idinfo):
    """
    Digunakan untuk memvalidasi token google dalam password
    Langkah yang dilakukan query email dan simpan sebagai session
    :param idinfo:
    :return:

    {
        // These six fields are included in all Google ID Tokens.
         "iss": "https://accounts.google.com",
         "sub": "110169484474386276334",
         "azp": "1008719970978-hb24n2dstb40o45d4feuo2ukqmcc6381.apps.googleusercontent.com",
         "aud": "1008719970978-hb24n2dstb40o45d4feuo2ukqmcc6381.apps.googleusercontent.com",
         "iat": "1433978353",
         "exp": "1433981953",

         // These seven fields are only included when the user has granted the "profile" and
         // "email" OAuth scopes to the application.
         "email": "testuser@gmail.com",
         "email_verified": "true",
         "name" : "Test User",
         "picture": "https://lh4.googleusercontent.com/-kYgzyAWpZzJ/ABCDEFGHI/AAAJKLMNOP/tIXL9Ir44LE/s99-c/photo.jpg",
         "given_name": "Test",
         "family_name": "User",
         "locale": "en"
    }
    """
    email = 'email' in idinfo and idinfo['email']
    if not email:
        raise ValueError('Mail tidak ditemukan')

    user = User.get_by_identity(email)
    return user


@view_config(route_name='googleOauth2', renderer='json')
def google_oauth2(request):
    return dict()


@view_config(route_name='googlesignin', renderer='json')
def googlesignin(request):
    # (Receive token by HTTPS POST)
    # ...
    CLIENT_IDS = request.google_signin_client_ids
    # CLIENT_IDS =     get_params('google-signin-client-id')
    KEY = get_params('google-signin-client-secret')
    # Specify the CLIENT_ID of the app that accesses the backend:
    # idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

    # Or, if multiple clients access the backend server:
    gtoken = json.loads(request.params['id_token'])
    # idinfo = id_token.verify_oauth2_token(gtoken, requests.Request())
    # test
    import jwt
    idinfo = jwt.decode(gtoken["credential"], options={"verify_signature": False})  # KEY, algorithms=["RS256"]) #
    if idinfo['aud'] not in CLIENT_IDS or idinfo['azp'] not in CLIENT_IDS:
        raise ValueError('Could not verify audience.')

    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        raise ValueError('Wrong issuer.')

    return idinfo
