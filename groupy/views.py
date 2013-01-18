from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
import json
import logging
import os
import models

log = logging.getLogger(__name__)


@view_config(context=models.Root, renderer='templates/mytemplate.pt')
def my_view(context, request):
    return {'project':'groupy'}


@view_config(context=models.Root, name='dbinit', request_method='POST', renderer='json')
def init_db(context, request):
    import db.neo4j
    with request.ldap.connection() as ld:
        db.neo4j.init(context.db, ld)
    return Response()

@view_config(name='cypher', context=models.Root, request_method='POST', renderer='json')
def cypher_post(context, request):
    query = request.params['query']
    db = context.db
    result = db.query(query)
    columns = result.keys()

    for row in result:
        for c in columns:
            row[c]

@view_config(name='cypher', context=models.Root, request_method='GET')
def cypher_get(context, request):
    pass


class BaseView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.filter = None if not 'filter' in self.request.params or not self.request.params['filter'] else self.request.params['filter'].split(',')
        self.search = None

    def node_to_dict(self, node):
        if self.filter:
            k = {}
            for f in self.filter:
                if f in node.keys():
                    k[f.lower()] = node[f.lower()]
            return k
        else:
            return dict(((k, v) for k, v in sorted(node.items()) if not k.startswith('meta.')))
     

class BaseMultiView(BaseView):
    from profilehooks import profile
    from string import Template
    fastQuery = Template("""start n = node:${idx}({k}) return n""")
    
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.search = None if 'search' not in self.request.params or not self.request.params['search'] else self.request.params['search']
        if not self.search:
            self._query = '{0}:*'.format(self.context._key)
        elif ':' in self.search:
            self._query = self.search
        else:
            self._query = ' '.join(map(lambda x: '{0}:{1}'.format(x, self.search), self.context._idxs))
        log.debug("Group query: %s", self._query)

    #@profile(filename='multi.prof', immediate=True)
    def __call__(self):
        
        hits = self.context.db.query(BaseMultiView.fastQuery.substitute(idx=self.context._idx_name), k=self._query)['n']

        return {'data': sorted([self.node_to_dict(ret) for ret in hits])}
    
    def create(self):
        pass

class BaseSingleView(BaseView):

    def __call__(self):

        return self.node_to_dict(self.context.node)


    def update(self):
        content = self.request.json_body
        if 'dn' in content and content['dn'] != self.context.node['dn']:
            raise Exception("Cannot update ldap DN! You should create a new entity instead")
        with self.context.db.transaction as tx:
            for k, v in content.items():
                self.context[k] = v
        try:
            self.context.save()
        except Exception as e:
            log.exception("Exception saving context. The underlying source (eg ldap) may not have been updated for this entity.")
        return self.node_to_dict(self.context.node)
    
    def join_group(self):
        ''' In subclass so groups can be subgroups'''
        pass

    def leave_group(self):
        ''' In subclass so groups can be subgroups'''
        pass



@view_defaults(context=models.User, renderer='json')
@view_config(request_method='GET')
@view_config(request_method=('POST', 'PUT'), attr='update')
class UserView(BaseSingleView):

    @view_config(name='groups')
    def groups(self):
        return {'data' : sorted([dict((('name', ret.end['groupname']), ('attributes', dict(ret.items())))) for ret in self.context.node.MEMBER_OF.outgoing], key=lambda k: k['name'])}



    
@view_defaults(context=models.Group, renderer='json')
@view_config(request_method='GET')
@view_config(request_method=('POST', 'PUT'), attr='update')
class GroupView(BaseSingleView):

    @view_config(name='members')
    def members(self):
        return { 'data': sorted([dict((('name', ret.start['username']), ('attributes', dict(ret.items())))) for ret in self.context.node.MEMBER_OF.incoming], key=lambda k: k['name'])}

    def remove_user(self):
        pass

@view_defaults(context=models.Users, renderer='json')
@view_config(request_method='GET')
@view_config(request_method='POST', attr='create')
class UsersView(BaseMultiView):
    pass


@view_defaults(context=models.Groups, renderer='json')
@view_config(request_method='GET', renderer='templates/groups.mustache', name='view' )
@view_config(request_method='GET')
@view_config(request_method='POST', attr='create')
class GroupsView(BaseMultiView):
    pass

    

