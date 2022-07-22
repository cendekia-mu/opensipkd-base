import logging

from opensipkd.models import (User, UserGroup, DBSession, )

log = logging.getLogger(__name__)


def group_finder(user_id, request):
    if user_id != 'None':
        q = DBSession.query(User).filter_by(id=user_id)
        user = q.first()
    else:
        user = None

    if not user or not user.status:
        log.info("User tidak ditemukan")
        return []

    r = []
    q = DBSession.query(UserGroup).filter_by(user_id=user.id)
    for ug in q:
        acl_name = 'group:{gid}'.format(gid=ug.group_id)
        r.append(acl_name)
    log.debug(r)
    return r


def get_user(request):
    user_id = request.authenticated_userid
    if user_id:
        q = DBSession.query(User).filter_by(id=user_id)
        return q.first()


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
