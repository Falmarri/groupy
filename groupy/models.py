from zope.interface import implementer
from zope.interface import Interface
import logging
import os


def get_graphdb(location):
    import atexit
    from neo4j import GraphDatabase
    location = os.path.abspath(location)
    _db = GraphDatabase(location)
    atexit.register(lambda d: d.shutdown(), _db)
    return _db

class IResource(Interface):

    def __getitem__(item):
        pass

class IResourceList(Interface):
        pass


class Resource(object):
    _db = None
    def __init__(self, request):
        if Resource._db is None:
            logging.debug("Creating database object from %s", request.registry.settings['neo4j_location'])
            Resource._db = get_graphdb(request.registry.settings['neo4j_location'])
        self.db = Resource._db

@implementer(IResource)
class Group(Resource):

    def __init__(self, request, group):
        self.group = group

    def __getitem__(self, key):
        if key == 'members':
            pass
        elif key == 'roles':
            pass
        elif key == 'filter':
            pass
        try:
            return getattr(self, key)()
        except Exception as e:
            raise KeyError(key)

    def members(self):
        self.group.MEMBER_OF.incoming


    def roles(self):
        pass



    def filter(self):
        pass

    
@implementer(IResource)
class User(Resource):

    def __init__(self, request, user):
        self.user = user

    def __getitem__(self, key):
        if key == 'memberships':
            pass

    def memberships(self):
        pass


class Membership(Resource):

    def __init__(self, request, user):
        self.user = user

    def __getitem__(self, key):
        if key == 'memberships':
            pass


        

@implementer(IResource)
class Users(object):
    pass


@implementer(IResource)
class Groups(object):
    pass


