from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPNotFound
import json
import logging
import os
import models

log = logging.getLogger(__name__)


@view_config(name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'groupy'}



@view_config(name='cypher', request_method='POST', renderer='json')
def cypher_post(context, request):
    query = request.params['query']
    db = context.db
    result = db.query(query)
    columns = result.keys()

    for row in result:
        for c in columns:
            row[c]

@view_config(name='cypher', request_method='GET')
def cypher_get(request):
    pass


@view_defaults(context=models.User, renderer='json')
@view_config()
class UserView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return dict(self.context.items())

    @view_config(name='groups')
    def groups(self):
        return sorted([(ret.end['groupname'], dict(ret.items())) for ret in self.context.MEMBER_OF.outgoing])

    def collaborators(self):
        pass

    def delete(self):
        pass

    def join(self):
        pass

    def update(self):
        pass
    
@view_defaults(context=models.Group, renderer='json')
@view_config()
class GroupView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return dict(self.context.items())

    @view_config(name='members')
    def members(self):
        return sorted([(ret.start['username'], dict(ret.items())) for ret in self.context.MEMBER_OF.incoming])

    def add(self):
        pass

@view_defaults(context=models.Users, renderer='json')
@view_config()
class UsersView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        pass

    @view_config(name='search')
    def search(self):
        pass


@view_defaults(context=models.Groups, renderer='json')
@view_config()
class GroupsView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        pass

    
    @view_config(name='search')
    def search(self):
        pass
    

