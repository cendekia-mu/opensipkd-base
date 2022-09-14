import logging

# from opensipkd.tools import get_params
from opensipkd.models import (User, UserGroup, DBSession, )
from pyramid.security import remember, forget

log = logging.getLogger(__name__)


def group_finder(user_id, request):
    if user_id != 'None':
        q = DBSession.query(User).filter_by(id=user_id)
        user = q.first()
    else:
        user = None

    if not user or not user.status:
        log.debug(f"user_id {user_id} not found or archived")
        return []

    r = []
    q = DBSession.query(UserGroup).filter_by(user_id=user.id)
    for ug in q:
        acl_name = 'group:{gid}'.format(gid=ug.group_id)
        r.append(acl_name)
    return r


def get_user(request):
    user_id = request.authenticated_userid
    if user_id:
        q = DBSession.query(User).filter_by(id=user_id)
        row = q.first()
        #todo restrict multi browser
        # if row and "g_state" not in request.cookies and \
        #         ("token" not in request.session or
        #             not request.session["token"] or
        #             row.security_code != request.session["token"]):
        #     request.session.flash("Silahkan login ulang")
        #     headers = forget(request)
        #     request.session.delete()
        #     request.response.headers.update(headers)
        #     if "g_state" in request.cookies:
        #         request.response.delete_cookie("g_state", '/')
        #     return
        return row


# def get_user(request):
#     user_id = request.unauthenticated_userid
#     if user_id is not None:
#         user = DBSession.query(User).get(user_id)
#         return user


from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper, Authenticated, Everyone


class MySecurityPolicy:
    def __init__(self, secret):
        self.helper = AuthTktCookieHelper(secret)

    def identity(self, request):
        identity = self.helper.identify(request)
        if identity is None:
            return None

        userid = identity['userid']
        principals = group_finder(userid, request)
        if principals is not None:
            return {
                'userid': userid,
                'principals': principals,
            }

    def authenticated_userid(self, request):
        identity = request.identity
        if identity is not None:
            return identity['userid']

    def permits(self, request, context, permission):
        identity = request.identity
        principals = set([Everyone])

        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity['userid'])
            principals.update(identity['principals'])
        return ACLHelper().permits(context, principals, permission)

    def remember(self, request, userid, **kw):
        return self.helper.remember(request, userid, **kw)

    def forget(self, request, **kw):
        return self.helper.forget(request, **kw)
