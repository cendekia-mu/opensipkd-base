from datetime import datetime, timezone
import sqlalchemy as sa


class ForceUTCDatetime(sa.TypeDecorator):
    """Ensures datetimes are timezone-aware UTC objects across both DBs."""
    impl = sa.TIMESTAMP(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                # Interpret naive datetime as UTC or handle according to business logic
                value = value.replace(tzinfo=timezone.utc)
            else:
                # Convert any other timezone directly to UTC
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            # Force the Python object to be aware if Oracle stripped the offset
            return value.replace(tzinfo=timezone.utc)
        return value

from .meta import * 
from .common import *
from .base import *
from .users import *
from .users import _User, _UserGroup
from .wilayah import *
from .partner import *
from .targets import *
from .user_area import *
from .departmen import _Departemen, Departemen
from .pegawai import *
from .utils import TextPrinters