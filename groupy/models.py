from zope.interface import implementer
from zope.interface import Interface
import logging
import os

log = logging.getLogger(__name__)

def get_graphdb(location):
    import atexit
    from neo4j import GraphDatabase
    location = os.path.abspath(location)
    _db = GraphDatabase(location)
    atexit.register(lambda d: d.shutdown(), _db)
    return _db


class IUser(Interface):
    pass
class IGroup(Interface):
    pass
class IUsers(Interface):
    pass
class IGroups(Interface):
    pass


class Resource(object):
    
    _db = None
    def __init__(self, request):
        # NOT THREAD SAFE. IF RUNNING ON PYPY SHOULD PROBABLY CEHCK NEO4J
        if Resource._db is None:
            Resource._db = get_graphdb(request.registry.settings['neo4j_location'])
        object.__setattr__(self, 'db', Resource._db)
        object.__setattr__(self, 'request', request)



class Root(Resource,dict):

    def __init__(self, request):
        #super(Root, self).__init__(self)
        #self.db = get_graphdb(request.registry.settings['neo4j_location'])
        #self.request = request
        Resource.__init__(self, request)
        dict.__init__(self)
        self['users'] =  Users(request)
        self['groups'] = Groups(request)
        

@implementer(IUsers)
class Users(Resource):

    _key = 'username'

    def __init__(self, request):
        Resource.__init__(self, request)
        self.idx = self.db.node.indexes.get('people')

    def __getitem__(self, key):
        user = self.idx.query('{0}:{1}'.format(Users._key, key)).single
        if user:
            return User(self.request, user, self, key.lower())

        raise KeyError(key)
    
@implementer(IGroups)
class Groups(Resource):

    _key = 'groupname'

    def __init__(self, request):
        Resource.__init__(self, request)
        self.idx = self.db.node.indexes.get('groups')

    def __getitem__(self, key):
        group = self.idx.query('{0}:{1}'.format(Groups._key, key)).single
        if group:
            return Group(self.request, group, self, key.lower())
        logging.warning("Could not find group %s. %s", key, group)
        raise KeyError(key)




class Node(Resource):
    
    def __init__(self, request, node, parent=None, name=''):
        Resource.__setattr__(self, 'node', node)
        Resource.__setattr__(self, 'request', request)
        Resource.__setattr__(self, '__parent__', parent)
        Resource.__setattr__(self, '__name__', name)
        Resource.__init__(self, request)

    def __getattr__(self, key):
        return getattr(self.node, key)

    def __setattr__(self, key, value):
        if key in self.__dict__:
            return Resource.__setattr__(self, key, value)
        else:
            ret = setattr(self.node, key, value)
            return ret

@implementer(IUser)
class User(Node):
    pass


class LdapSource(object):

    def __init__(self, request):
        pass

@implementer(IUser)
class LdapUser(User):

    def __setattr__(self, key, value):
        User.__setattr__(self, key, value)
        



@implementer(IGroup)
class Group(Node):

    def __getitem__(self, key):
        for u in self.node.MEMBER_OF.incoming:
            if u.start['username'] == key.lower():
                return User(self.request, u.start, self, key.lower())
        else:
            raise KeyError(key)


