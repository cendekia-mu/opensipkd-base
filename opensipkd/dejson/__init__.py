"""Detable."""
import os

from pkg_resources import resource_filename

from . import detable  # API
from deform.field import Field  # API
from .detable import Button  # API
from .detable import DeTable  # API
from deform import ZPTRendererFactory  # API
from deform import default_renderer  # API
deform_templates = resource_filename('deform', 'templates')
path = os.path.dirname(__file__)
path = os.path.join(path, 'templates')
search_path = (path, deform_templates) #,
# renderer = ZPTRendererFactory(search_path)
DeTable.set_zpt_renderer(search_path)
