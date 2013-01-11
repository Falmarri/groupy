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
            import os
            if not os.environ.get('NEO4J_PYTHON_JVMARGS') and request.registry.settings.get('neo4j.jvmargs'):
                os.environ['NEO4J_PYTHON_JVMARGS'] = request.registry.settings.get('neo4j.jvmargs')

            if not os.environ.get('JAVA_HOME') and request.registry.settings.get('neo4j.java_home'):
                os.environ['JAVA_HOME'] = request.registry.settings.get('neo4j.java_home')

            if request.registry.settings.get('neo4j.properties'):
                import jprops
                with open(request.registry.settings.get('neo4j.properties')) as fp:
                    conf = jprops.load_properties(fp)
            
                
            Resource._db = get_graphdb(request.registry.settings['neo4j.location'])
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
        if not self.db.node.indexes.exists(self._idx_name):
            log.error('Could not get database index from %s. Did you set the right location in your settings file?', request.registry.settings['neo4j.location'])
            self.idx = None
        else:
            self.idx = self.db.node.indexes.get(self._idx_name)

    def _query(self, *args, **kwargs):
        hits = self.idx.query(' '.join(map(lambda x: '*:{0}'.format(x), args)))

    def _get_user(self, username):
        ''' `username` should be unique, so we can
        just get it instead of having to query'''
        pass

    def __getitem__(self, key):
        if self.idx is None:
            raise KeyError(key)
        
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



class NodeFactory(object):

    def __call__(self, request, node, parent=None, name=''):
        if 'groupname' in node.keys():
            pass

        elif 'username' in node.keys():
            pass

        if node['source'] == 'ldap':
            pass
        elif node['source'] == 'unknown':
            pass
            

Node = NodeFactory()


class _Node(Resource):

    #def __new__(self, request, node, parent=None, name=''):
        #if 'groupname' in node:
            #pass
        #elif 'username' in self.node:
            #pass


    def create(self, *args, **kwargs):
        for k,v in kwargs.items():
            self.node[k] = v
    
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
class User(_Node):
    pass


@implementer(IUser)
class LdapNode(_Node):
    from ldap import modlist
    import ldap
 
    def push(self):

        with self.cm as conn:
            current_ldap = conn.search_s(self['dn'], ldap.SCOPE_BASE)
            if current_ldap and len(current_ldap) == 1:
                current_ldap = current_ldap[0][1]
            else:
                raise Exception('Error looking up user in ldap')
            mods = modlist.modifyModlist(current_ldap, dict((k, list(v)) for k,v in self.items()), ['groupname', 'username', 'dn', 'uid'])
            conn.modify_s(self['dn'], mods)

    def pull(self):
        with self.cm as conn:
            current_ldap = conn.search_s(self['dn'], ldap.SCOPE_BASE)
            if current_ldap and len(current_ldap) == 1:
                current_ldap = current_ldap[0][1]
            else:
                raise Exception('Error looking up user in ldap')

            for attr, val in current_ldap.items():
                try:
                    if len(val) != 1:
                        self[attr] = [unicode(v, 'utf-8') for v in val]
                    else:
                        self[attr] = unicode(val[0], 'utf-8')[0]
                except TypeError as e:
                    pass

@implementer(IGroup)
class Group(_Node):

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