
API
---

.. http:get:: /users

    Get a list of all the users in the system. Note: this can take some time depending on the amount of results
    returned.

    **Example request**:

    .. sourcecode:: http

        GET /users HTTP/1.1
        Host: example.com

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json; charset=UTF-8
        
        {
        "data" : [
            {
                "username":"dknapp",
                "cn":"David Knapp",
                "uid":"dknapp",
                "shadowinactive":"10",
                "homedirectory":"/home/dknapp",
                "shadowwarning":"10",
                "shadowmin":"1",
                "title":"Software Engineer",
                "loginshell":"/bin/bash",
                "uidnumber":"12942",
                "shadowmax":"730",
                "source":"ldap",
                "test.extra_field":"test",
                "dn":"uid=dknapp,ou=People,dc=iplantcollaborative,dc=org",
                "mail":"davidcknapp@gmail.com",
                "givenname":"David",
                "shadowlastchange":"15460",
                "departmentnumber":"Omg Development 5",
                "objectclass":[
                "shadowAccount",
                "posixAccount",
                "inetOrgPerson"
                ],
                "o":"Ephibian",
                "gidnumber":"10013",
                "sn":"Knapp"
            },
            {
                "username":"lenards",
                "cn":"Andrew Lenards",
                "uid":"lenards",
                "shadowinactive":"10",
                "sambasid":"S-1-5-21-7623811015-3361044348-030300820-21042",
                "homedirectory":"/home/lenards",
                "shadowmax":"730",
                "shadowwarning":"10",
                "shadowmin":"1",
                "title":"University staff",
                "loginshell":"/bin/bash",
                "uidnumber":"10021",
                "sambaprimarygroupsid":"S-1-5-21-7623811015-3361044348-030300820-21001",
                "source":"ldap",
                "mail":"lenards@email.arizona.edu",
                "sambapwdlastset":"1236616914",
                "dn":"uid=lenards,ou=People,dc=iplantcollaborative,dc=org",
                "displayname":"Andrew Lenards",
                "sambadomainname":"junk",
                "sambaacctflags":"[XU         ]",
                "givenname":"Andrew",
                "shadowlastchange":"15491",
                "departmentnumber":"BIO5 Institute",
                "objectclass":[
                "sambaSamAccount",
                "shadowAccount",
                "posixAccount",
                "inetOrgPerson"
                ],
                "sambahomedrive":"U:",
                "o":"University of Arizona",
                "gidnumber":"10013",
                "sn":"Lenards"
            }
        ]
        }

    :query search: Supports full `lucene <http://lucene.apache.org/core/3_6_2/queryparsersyntax.html>`_ search syntax (not 100% tested)
    :query filter: Filters object fields from search results. Comma separated list



    **Multiple Field Search**:

    .. sourcecode:: http

        GET /users?search=(dknap* or lenards) HTTP/1.1

    **Fuzzy search**:

    .. sourcecode:: http

        GET /users?search=uid:dknapp~0.8 HTTP/1.1

    **Search and Filter**:

    .. sourcecode:: http

        GET /users?search=uid:dknapp&filter=dn,cn,title HTTP/1.1

.. http:get:: /users/{username}

    Returns the user information of the user if it exists

    :query filter: Filters object fields from search results. Comma separated list


.. http:get:: /users/{username}/groups

    The membership information of all the groups this user belongs to. The return value is a tuple (groupname, relationship_attributes).
    This format can be discussed and changed if needed.

    **Example request**:

    .. sourcecode:: http

        GET /users/dknapp/groups HTTP/1.1
        Host: example.com

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json; charset=UTF-8

        {
        "data":[
            {
            "attributes":{ },
            "name":"atmo-user"
            },
            {
            "attributes":{ },
            "name":"community"
            },
            {
            "attributes":{ },
            "name":"core-services"
            },
            {
            "attributes":{ },
            "name":"de-preview-access"
            },
            {
            "attributes":{ },
            "name":"myplant-users"
            },
            {
            "attributes":{ },
            "name":"staff"
            },
            {
            "attributes":{ },
            "name":"support"
            },
            {
            "attributes":{ },
            "name":"uofa"
            }
        ]
        }

.. http:get:: /groups

    See :http:get:`/users`


.. http:get:: /groups/{groupname}

    Returns the group object. See :http:get:`/users/{username}`

.. http:get:: /groups/{groupname}/members

    See :http:get:`/users/{username}/groups`

.. http:get:: /groups/{groupname}/{username}

    Returns the user object if that user is a member of this group.
    This URI is functionally equivalent to :http:get:`/users/{username}`
    Therefore this is valid :http:get:`/groups/{groupname}/{username}/groups`
   

.. http:post:: /cypher

    Allows full cypher access into the underlying data. Please don't use this yet as it has full read/write access to the entire database

.. http:post:: /dbinit

    Initializes the database. THIS IS DESTRUCTIVE. It will clear ALL data in the current database and recreate it from ldap data
