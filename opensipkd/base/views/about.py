from pyramid.view import view_config
from pyramid.renderers import render_to_response

@view_config(route_name='home-about', renderer='templates/about.pt')
def view_about(request):
    templates = 'templates/about.pt'
    if request.matchdict['id']=='eta':
        templates = 'templates/eta.pt'
    #return dict(request=request)
    return render_to_response(templates,
                              dict(about='about'),
                              request=request)
    

