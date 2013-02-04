from pyramid.events import ApplicationCreated
from pyramid.events import subscriber, NewRequest
from ldap.ldapobject import ReconnectLDAPObject
import ldap
from contextlib import contextmanager
import logging

log = logging.getLogger(__name__)

class ConnectionManager(object):
    '''
    Hack to work around ldappool not allowing anonymous connections
    '''
    def __init__(self, uri, timeout=None, *args, **kwargs):
        self.uri = uri
        if timeout:
            ldap.set_option(ldap.OPT_TIMEOUT, timeout)
            ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, timeout)

        self.conn = ReconnectLDAPObject(self.uri, retry_max=2)

    @contextmanager
    def connection(self, *args, **kwargs):
        print "connection %s" % self.conn
        try:
            yield self.conn
        finally:
           pass
            
          
def sync(db, ld, settings, update=False):

    dns = set((s for s in db.query('START r = node:people({q}) return r.dn', q='uid:*')['r.dn']))
    import ipdb
    ipdb.set_trace()

    for (dn, attrs) in ld.search_s(
                                settings['groupy.ldap.people.base']
                                ,ldap.SCOPE_SUBTREE, settings['groupy.ldap.people.search']
                                ,settings['groupy.ldap.attrs']):
        if dn not in dns:
            log.debug("Did not find %s in the database... adding.", dn)
            pass


def init(db, ld, settings=None, reset=True):

    from collections import defaultdict
    ret = defaultdict(int)
    
    with db.transaction:
        
        if not db.node.indexes.exists('groups'):
            groups_idx = db.node.indexes.create('groups', type='exact', to_lower_case='true')
        else:
            groups_idx = db.node.indexes.get('groups')

        if not db.node.indexes.exists('people'):
            people_idx = db.node.indexes.create('people', type='exact', to_lower_case='true')
        else:
            people_idx = db.node.indexes.get('people')


        indexable = settings.get('neo4j.index.people.keys') or ('uid', 'cn', 'sn', 'givenname', 'mail', 'displayname', 'title')

        for (dn, attrs) in ld.search_s(
                                settings['groupy.ldap.people.base']
                                ,ldap.SCOPE_SUBTREE, settings['groupy.ldap.people.search']
                                ,settings['groupy.ldap.attrs']):
            ret['users'] += 1
            node = db.node(username=unicode(attrs['uid'][0], 'utf-8').lower(), source="ldap", dn=unicode(dn, 'utf-8'))
            for attr, val in attrs.iteritems():
                ret['attributes'] += 1
                attr = attr.lower()
                try:
                    if not isinstance(val, basestring):
                        if len(val) == 1:
                            node[attr] = unicode(val[0], 'utf-8')
                        else:
                            node[attr] = [unicode(v, 'utf-8') for v in val]
                    else:
                        node[attr] = unicode(val, 'utf-8')
                except TypeError as e:
                    pass
                    
            try:
                people_idx['username'][node['username']] = node
            except Exception as e:
                import ipdb
                ipdb.set_trace()
            people_idx['dn'][node['dn']] = node
            for i in indexable:
                ind = node.get(i)
                if ind:
                    if isinstance(ind, basestring):
                        people_idx[i][ind.lower()] = node
                    else:
                        for l in ind:
                            people_idx[i][l.lower()] = node
                    
    log.debug("Added users")

    with db.transaction:
        indexable = settings.get('neo4j.index.people.keys') or ('uid', 'cn', 'sn', 'givenname', 'mail', 'displayname', 'title')

        for (dn, attrs) in ld.search_s(
                                settings['groupy.ldap.groups.base']
                                ,ldap.SCOPE_SUBTREE, settings['groupy.ldap.groups.search']
                                ,settings['groupy.ldap.attrs'] + [settings['groupy.ldap.group.membership']]):
            ret['groups'] += 1
            node = db.node(groupname=unicode(attrs['cn'][0], 'utf-8').lower(), source="ldap", dn=unicode(dn, 'utf-8'))
            for attr, val in attrs.iteritems():
                ret['attributes'] += 1
                attr = attr.lower()
                if attr != settings['groupy.ldap.group.membership'].lower():
                    try:
                        if not isinstance(val, basestring):
                            if len(val) == 1:
                                node[attr] = unicode(val[0], 'utf-8')
                            else:
                                node[attr] = [unicode(v, 'utf-8') for v in val]
                        else:
                            node[attr] = unicode(val, 'utf-8')
                    except TypeError as e:
                        pass

            groups_idx['groupname'][node['groupname']] = node
            groups_idx['dn'][node['dn']] = node
            for i in indexable:
                ind = node.get(i)
                if ind:
                    if isinstance(ind, basestring):
                        groups_idx[i][ind.lower()] = node
                    else:
                        for l in ind:
                            groups_idx[i][l.lower()] = node

            
            members = attrs.get(settings['groupy.ldap.group.membership'])
            if members:
                unknown = []
                for member in members:
                    ret['relations'] += 1
                    m = people_idx['username'][unicode(member, 'utf-8').lower()]
                    if m.single:
                        m.single.MEMBER_OF(node)
                    elif not m:
                        unknown.append((member, dn))
                        unknown_user = db.node(username=unicode(member, 'utf-8').lower(), source='unknown')
                        people_idx['username'][unknown_user['username'].lower()] = unknown_user
                        unknown_user.MEMBER_OF(node)
                    else:
                        import json
                        log.warning("Found multiple hits for unique username %s", json.dumps([u.items() for u in m], indent=2))
                    m.close()
                if unknown:
                    ret['unknown_users'] = unknown
    return ret



db = None

@subscriber(ApplicationCreated)
def neo4j_setup(event):
    import os
    if not os.environ.get('NEO4J_PYTHON_JVMARGS') and event.app.registry.settings.get('neo4j.jvmargs'):
        os.environ['NEO4J_PYTHON_JVMARGS'] = event.app.registry.settings.get('neo4j.jvmargs')

    if not os.environ.get('JAVA_HOME') and event.app.registry.settings.get('neo4j.java_home'):
        os.environ['JAVA_HOME'] = event.app.registry.settings.get('neo4j.java_home')

    import neo4j
    event.app.registry.db = neo4j.GraphDatabase(os.path.abspath(event.app.registry.settings['neo4j.location']))
