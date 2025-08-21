from . import api_base
from ..models import Partner

class Views(api_base.ApiViews):
    def __init__(self, request):
        super().__init__(request)
        self.table = Partner
    
    def filter_ids(self, query):
        return query.filter(Partner.email == self.request.user.email)