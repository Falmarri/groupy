from pyramid.authentication import *

@implementer(IAuthenticationPolicy)
class GroupyAuthenticationPolicy(SessionAuthenticationPolicy):
    """ An object representing a Pyramid authentication policy. """

    def __init__(self, prefix='auth.', neo4j_db = None, ldap_connection =None, debug=False):
        self.prefix = prefix or ''
        self.userid_key = prefix + 'userid'
        self.debug = debug

    def authenticated_userid(self, request):
        """ Return the authenticated userid or ``None`` if no
        authenticated userid can be found. This method of the policy
        should ensure that a record exists in whatever persistent store is
        used related to the user (the user should not have been deleted);
        if a record associated with the current id does not exist in a
        persistent store, it should return ``None``."""

    def unauthenticated_userid(self, request):
        """ Return the *unauthenticated* userid.  This method performs the
        same duty as ``authenticated_userid`` but is permitted to return the
        userid based only on data present in the request; it needn't (and
        shouldn't) check any persistent store to ensure that the user record
        related to the request userid exists."""

    def effective_principals(self, request):
        """ Return a sequence representing the effective principals
        including the userid and any groups belonged to by the current
        user, including 'system' groups such as
        ``pyramid.security.Everyone`` and
        ``pyramid.security.Authenticated``. """


    def callback(self, username, request):
        pass

import ldap
import ldappool 
cm = ldappool.ConnectionManager('ldap://ldap.iplantcollaborative.org')


class _Decoder(object):
    """
    Stolen from django-auth-ldap.

    Encodes and decodes strings in a nested structure of lists, tuples, and
    dicts. This is helpful when interacting with the Unicode-unaware
    python-ldap.
    """

    ldap = ldap

    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def decode(self, value):
        try:
            if isinstance(value, str):
                value = value.decode(self.encoding)
            elif isinstance(value, list):
                value = self._decode_list(value)
            elif isinstance(value, tuple):
                value = tuple(self._decode_list(value))
            elif isinstance(value, dict):
                value = self._decode_dict(value)
        except UnicodeDecodeError:
            pass

        return value

    def _decode_list(self, value):
        return [self.decode(v) for v in value]

    def _decode_dict(self, value):
        # Attribute dictionaries should be case-insensitive. python-ldap
        # defines this, although for some reason, it doesn't appear to use it
        # for search results.
        decoded = self.ldap.cidict.cidict()

        for k, v in value.iteritems():
            decoded[self.decode(k)] = self.decode(v)

        return decoded

def _get_groups(conn, group):
    return conn.search_s('ou=groups,dc=iplantcollaborative,dc=org', ldap.SCOPE_SUBTREE,'(cn=*)')

def _query_person(conn, user):

    ret =  conn.search_s('ou=people,dc=iplantcollaborative,dc=org', ldap.SCOPE_SUBTREE, '(uid={username})'.format(username=user))
    if len(ret) == 1:
        return ret[0]

    

def auth(username, password):
    '''Gets the associated ldap user info as well as neo4j info'''
    user_info = {}
    with cm.connection() as conn:
        ret = _query_person(username)
    try:
        with cm.connection(ret[0], password) as conn:
            user_info['ldap'] = _Decoder().decode(ret)
    except ldap.LDAPError:
        pass


    

