from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid_beaker import session_factory_from_settings
import models
import logging
import os

log = logging.getLogger(__name__)







def group_root_factory(request):
    return models.Groups(request)

def user_root_factory(request):
    return models.Users(request)



from pyramid.security import (
    Allow,
    Authenticated,
    remember,
    forget,
)



def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    import ldap
    import ldapurl
    my_session_factory = session_factory_from_settings(settings)

    
    config = Configurator(settings=settings, root_factory=models.Root, session_factory=my_session_factory)
    
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy

    if settings.get('groupy.ldap.user'):
        
        from ldappool import ConnectionManager as CM
    else:
        from .db.neo4j import ConnectionManager as CM

    timeout = int(settings.get('groupy.ldap.timeout', -1))
    settings['groupy.ldap.timeout'] = timeout
    
    cm = CM(ldapurl.LDAPUrl(hostport=settings.get('groupy.ldap.url'), dn=settings.get('groupy.ldap.dn')).unparse(),
                            bind=settings.get('groupy.ldap.user'),
                            passwd=settings.get('groupy.ldap.password'), timeout=timeout, use_pool=False)

    config.add_request_method((lambda r: cm), name='ldap', property=True)
    config.add_static_view('static', 'static', cache_max_age=3600)
    
    #config.add_route('user_search', '/users/search' )
    #config.add_route('users', '/users/*traverse', factory=user_root_factory)
    ##config.add_route('user_memberships', '/users/{user}/memberships')

    
    #config.add_route('group_search', '/groups/search')
    #config.add_route('groups', '/groups/*traverse', factory=group_root_factory)
    #config.add_route('group_members', '/groups/{group}/members')



    
    #config.add_route('cypher', '/cypher')
    config.scan()
    return config.make_wsgi_app()
