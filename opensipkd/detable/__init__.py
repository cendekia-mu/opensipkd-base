"""Detable."""
import os

from deform import (
    ZPTRendererFactory,  # API
    default_renderer,  # API
)
from deform.field import Field  # API
from pkg_resources import resource_filename

from . import detable  # API
from .detable import (
    Button,  # API
    DeTable,  # API
)

deform_templates = resource_filename('deform', 'templates')
path = os.path.dirname(__file__)
path = os.path.join(path, 'templates')
search_path = (path, deform_templates) #,
# renderer = ZPTRendererFactory(search_path)
DeTable.set_zpt_renderer(search_path)
