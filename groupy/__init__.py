from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid_beaker import session_factory_from_settings
import models
import logging
import os

log = logging.getLogger(__name__)







def group_root_factory(request):
    return {}

def user_root_factory(request):
    return {}


from pyramid_ldap import (
    get_ldap_connector,
    groupfinder,
)

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
    my_session_factory = session_factory_from_settings(settings)

    
    config = Configurator(settings=settings, root_factory=models.Resource, session_factory=my_session_factory)
    
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    
    #config.set_authentication_policy(SessionAuthenticationPolicy(callback=groupfinder))
    #config.set_authorization_policy(ACLAuthorizationPolicy())

    #config.ldap_setup(
        #'ldap://ldap.iplantcollaborative.org',
    #)

    #config.ldap_set_login_query(
        #base_dn='CN=people,DC=iplantcollaborative,DC=org',
        #filter_tmpl='(uid=%(login)s)',
        #scope = ldap.SCOPE_ONELEVEL,
    #)

    #config.ldap_set_groups_query(
    #base_dn='CN=people,DC=iplantcollaborative,DC=org',
        #filter_tmpl='(&(objectCategory=group)(member=%(userdn)s))',
        #scope = ldap.SCOPE_SUBTREE,
        #cache_period = 600,
    #)
    
    
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    
    config.add_route('user_search', '/users/search' )
    config.add_route('user', '/users/{user}')
    config.add_route('users', '/users/')
    config.add_route('user_memberships', '/users/{user}/memberships')

    
    config.add_route('group_search', '/groups/search')
    config.add_route('group', '/groups/{group}')
    config.add_route('groups', '/groups/')
    config.add_route('group_members', '/groups/{group}/members')



    
    config.add_route('cypher', '/cypher')
    config.scan()
    return config.make_wsgi_app()
