import logging
from .models import (
    User,
    UserGroup,
    DBSession,
    )

log = logging.getLogger(__name__)
# It is used by RootFactory
def group_finder(user_id, request):
    q = DBSession.query(User).filter_by(id=user_id)
    user = q.first()
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
