from deform.widget import *


class _FieldStorage(SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct in (null, None, '', b''):
            return null
        # weak attempt at duck-typing
        if not hasattr(cstruct, 'file'):
            raise Invalid(node, "%s is not a FieldStorage instance" % cstruct)
        return cstruct
