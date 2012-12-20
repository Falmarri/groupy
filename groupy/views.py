from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
import json
import logging
import os

log = logging.getLogger(__name__)


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'groupy'}


@view_config(route_name='group', renderer='json')
class GroupView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.groups_idx = self.context.db.node.indexes.get('groups')

    def __call__(self):
        group = self.groups_idx['groupname'][self.request.matchdict['group']].single
        if not group:
            return HTTPNotFound()
        return dict(group.items())
    
    @view_config(route_name='group_search', renderer='json')
    def search(self):
        pass

    @view_config(route_name='group_members', renderer='json')
    def members(self):
        group = self.groups_idx['groupname'][self.request.matchdict['group']].single
        if not group:
            return HTTPNotFound()

        users = [dict(m.start.items()) for m in group.MEMBER_OF.incoming]

        return users


    @view_config(route_name='groups', renderer='json')
    def groups(self):
        hits = self.groups_idx.query('groupname:*')
        r = [dict(u.items()) for u in hits]
        hits.close()
        return r

    def add_member(self):
        pass

    def delete_member(self):
        pass


@view_config(route_name='user', renderer='json')
class UserView(object):

    indexed = ('uid', 'cn', 'sn', 'givenname', 'mail', 'displayname', 'username')
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.users_idx = self.context.db.node.indexes.get('people')

    def __call__(self):
        hits = self.users_idx['username'][self.request.matchdict['user']].single
        if not hits:
            return HTTPNotFound()
        
        return dict(hits.items())

    @view_config(route_name='user_search', renderer='json')
    def search(self):

        q = ''
        for s in UserView.indexed:
            r = self.request.params.get(s)
            if r:
                q += '{0}:{1}'.format(s, r)

        log.debug('Searching users records with query: %s', q)
        if q:
            hits = self.users_idx.query(q)

            r = [{k: v for k, v in u.items() if k in ('username', 'cn', 'mail')} for u in hits]

            hits.close()

            return r
    
    @view_config(route_name='user_memberships', renderer='json')
    def memberships(self):
        user = self.users_idx['username'][self.request.matchdict['user']].single
        if not user:
            return HTTPNotFound()
        
        groups = [dict(m.end.items()) for m in user.MEMBER_OF.outgoing]

        return groups
        

        

    @view_config(route_name='users', renderer='json')
    def users(self):
        hits = self.users_idx.query('username:*')
        r = [dict(u.items()) for u in hits]
        hits.close()
        return r

    def create_group(self):
        pass

    def delete_group(self):
        pass
        


def users_view(context, request):
    return {}
