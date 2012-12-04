from pyramid.config import Configurator
from pyramid.renderers import JSON
import logging
import os

log = logging.getLogger(__name__)




def _memoize(obj):
    import functools
    _cache = obj.cache = {}
    @functools.wraps(obj)
    def memoizer(location):
        location = os.path.abspath(location)
        if location not in _cache:
            _cache[location] = obj(location)
            return _cache[location]
        return memoizer
    
    

def get_graphdb(location):
    import atexit
    from neo4j import GraphDatabase
    location = os.path.abspath(location)
    _db = GraphDatabase(location)
    atexit.register(lambda d: d.shutdown(), _db)
    return _db

class Resource(object):
    _db = None
    def __init__(self, request):
        if Resource._db is None:
            log.debug("Creating database object from %s", request.registry.settings['neo4j_location'])
            Resource._db = get_graphdb(request.registry.settings['neo4j_location'])
        self.db = Resource._db

class Group(Resource):


    def __getitem__(self, group):
        raise KeyError()

class User(Resource):
    
    def __getitem__(self, user):
        raise KeyError()


def group_root_factory(request):
    return {}

def user_root_factory(request):
    return {}


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    
    config = Configurator(settings=settings, root_factory=Resource)

    
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    
    config.add_route('user_search', '/users/search')
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
