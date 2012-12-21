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


class IUser(Interface):
    pass
class IGroup(Interface):
    pass
class IUsers(Interface):
    pass
class IGroups(Interface):
    pass

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

    def __init__(self, request, group=None, parent=None):
        self.group = group
        self.__name__ = group['groupname'] if group else ''
        self.__parent__ = parent

    def __getitem__(self, key):
        if key == 'members':
            return self.members()
        elif key == 'roles':
            pass
        elif key == 'filter':
            pass
        try:
            return self.get_member(key)
        except KeyError as e:
            raise
        except Exception as e:
            logging.exception("Could not look up path %s", key)
            raise KeyError(key)


    def get_member(self, member, on_fail=None):
        for r in self.group.MEMBER_OF.incoming:
            if r.start['username'] == member:
                return User(self.request, r, self)
            elif r.start['groupname'] == member:
                return Group(self.request, r, self)
        raise KeyError(member)


    def members(self, direct=True):
        membership_nodes = [(rel, rel.start) for rel in self.group.MEMBER_OF.incoming]


    def roles(self):
        pass



    def filter(self):
        pass

    
@implementer(IResource)
class User(Resource):

    def __init__(self, request, user=None, parent=None):
        self.user = user
        self.__name__ = user['username'] if user else ''
        self.__parent__ = parent

    def __getitem__(self, key):
        if key == 'memberships':
            pass

    def memberships(self):
        membership_nodes = [(rel, rel.end) for rel in self.group.MEMBER_OF.outgoing]


class Membership(object):

    def __init__(self, request, user, group):
        self.user = user
        self.group = group






@implementer(IResource)
class Users(object):
    pass


@implementer(IResource)
class Groups(object):
    pass


