from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from ldap.ldapobject import ReconnectLDAPObject
import ldap
from contextlib import contextmanager

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
            
          
def _get_groups(ld):
    return ld.search_s('ou=groups,dc=iplantcollaborative,dc=org', ldap.SCOPE_SUBTREE, '(cn=*)')

def _get_people(ld):
    return ld.search_s('ou=people,dc=iplantcollaborative,dc=org', ldap.SCOPE_SUBTREE, '(uid=*)')




def init(db, ld):
   
    with db.transaction:
        if not db.node.indexes.exists('groups'):
            groups_idx = db.node.indexes.create('groups', type='exact', to_lower_case='true')
        else:
            groups_idx = db.node.indexes.get('groups')

        if not db.node.indexes.exists('people'):
            people_idx = db.node.indexes.create('people', type='exact', to_lower_case='true')
        else:
            people_idx = db.node.indexes.get('people')


        indexable = ('uid', 'cn', 'sn', 'givenname', 'mail', 'displayname')
        for (dn, attrs) in _get_people(ld):
            node = db.node(username=unicode(attrs['uid'][0], 'utf-8'), source="ldap", dn=unicode(dn, 'utf-8'))
            ldap_attrs = []
            for attr, val in attrs.iteritems():
                attr = attr.lower()
                if 'password' not in attr:
                    try:
                        if len(val) != 1:
                            node[attr] = [unicode(v, 'utf-8') for v in val]
                        else:
                            node[attr] = unicode(val[0], 'utf-8')[0]
                        ldap_attrs.append(unicode(attr), 'utf-8')
                    except TypeError as e:
                        pass
                    
            node['meta.ldap_attrs'] = ldap_attrs
            people_idx['username'][node['uid'].lower()] = node
            people_idx['dn'][node['dn']] = node
            for i in indexable:
                if node.get(i):
                    people_idx[i][node[i]] = node


        indexable = ('cn', 'displayname',)
        for (dn, attrs) in _get_groups(ld):
            ldap_attrs = []
            node = db.node(groupname=unicode(attrs['cn'][0], 'utf-8'), source="ldap", dn=unicode(dn, 'utf-8'))
            for attr, val in attrs.iteritems():
                attr = attr.lower()
                if attr != 'memberUid':
                    try:
                        if len(val) != 1:
                            node[attr] = [unicode(v, 'utf-8') for v in val]
                        else:
                            node[attr] = unicode(val[0], 'utf-8')[0]
                        ldap_attrs.append(unicode(attr), 'utf-8')
                    except TypeError as e:
                        pass

            node['meta.ldap_attrs'] = ldap_attrs
            groups_idx['groupname'][node['cn']] = node
            groups_idx['dn'][node['dn']] = node
            for i in indexable:
                if node.get(i):
                    groups_idx[i][node[i]] = node

            
            members = attrs.get('memberUid')
            if members:
                for member in members:
                    m = people_idx['uid'][unicode(member, 'utf-8').lower()]
                    if m.single:
                        m.single.MEMBER_OF(node)
                    else:
                        unknown_user = db.node(uid=unicode(member, 'utf-8'), source='unknown')
                        unknown_user.MEMBER_OF(node)
                    m.close()


@subscriber(ApplicationCreated)
def neo4j_setup(event):
    pass