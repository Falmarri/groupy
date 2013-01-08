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
        self.db = Resource._db
        self.request = request



class Cypher(Resource):
    pass

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
    _idx_name = 'people'
    _key = 'username'
    _idxs = (_key, 'uid', 'cn', 'sn', 'givenname', 'mail', 'displayname')

    def __init__(self, request):
        Resource.__init__(self, request)
        self.idx = self.db.node.indexes.get(self._idx_name)

    def _query(self, *args, **kwargs):
        hits = self.idx.query(' '.join(map(lambda x: '*:{0}'.format(x), args)))

    def _get_user(self, username):
        ''' `username` should be unique, so we can
        just get it instead of having to query'''
        pass

    def __getitem__(self, key):
        user = self.idx.query('{0}:{1}'.format(Users._key, key.lower())).single
        if user:
            return User(self.request, user, self, key.lower())

        raise KeyError(key)
    
@implementer(IGroups)
class Groups(Resource):
    _idx_name = 'groups'
    _key = 'groupname'
    _idxs = (_key, 'cn', 'displayname',)
    def __init__(self, request):
        Resource.__init__(self, request)
        self.idx = self.db.node.indexes.get(self._idx_name)

    def __getitem__(self, key):
        group = self.idx.query('{0}:{1}'.format(Groups._key, key.lower())).single
        if group:
            return Group(self.request, group, self, key.lower())
        logging.warning("Could not find group %s. %s", key, group)
        raise KeyError(key)




class Node(Resource):

    def __new__(self, request, node, parent=None, name=''):
        if 'groupname' in node:
            pass
        elif 'username' in self.node:
            pass

    
    def __init__(self, request, node, parent=None, name=''):
        self.node = node
        self.request = request
        self.__parent__ = parent
        self.__name = name
        Resource.__init__(self, request)

    def __getattr__(self, key):
        return getattr(self.node, key)

    def __setitem__(self, key, value):
        self.node[key] = value

@implementer(IUser)
class User(Node):
    pass


@implementer(IUser)
class LdapNode(Node):
    from ldap import modlist
    import ldap
    def push(self):

        with self.cm as conn:
            current_ldap = conn.search_s(self['dn'], ldap.SCOPE_BASE)
            if current_ldap and len(current_ldap) == 1:
                current_ldap = current_ldap[0][1]
            else:
                raise Exception('Error looking up user in ldap')
            mods = modlist.modifyModlist(current_ldap, {k: list(v) for (k,v) in self.items()}, ['groupname', 'username', 'dn', 'uid'])
            conn.modify_s(self['dn'], mods)

    def pull(self):
        pass


@implementer(IGroup)
class Group(Node):

    def __getitem__(self, key):
        for u in self.node.MEMBER_OF.incoming:
            if u.start['username'] == key.lower():
                return User(self.request, u.start, self, key.lower())
        else:
            raise KeyError(key)



SCHEMA = {
        'people' : Groups._idxs,
        'groups' : Users._idxs

    }