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
            
          



@subscriber(ApplicationCreated)
def neo4j_setup(event):
    pass