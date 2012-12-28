from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
import json
import logging
import os
import models

log = logging.getLogger(__name__)


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'groupy'}



@view_config(route_name='cypher', request_method='POST', renderer='json')
def cypher_post(context, request):
    query = request.params['query']
    db = context.db
    result = db.query(query)
    columns = result.keys()

    for row in result:
        for c in columns:
            row[c]

@view_config(route_name='cypher', request_method='GET')
def cypher_get(request):
    pass



@view_config(
def users_view(context, request):
    return {}
