# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from superdesk.resource import Resource


class SessionsResource(Resource):
    schema = {
        'user': Resource.rel('users', True),
        'session_preferences': {'type': 'dict'}
    }
    datasource = {
        'source': 'auth',
        'default_sort': [('_created', -1)]
    }
    resource_methods = ['GET', 'POST']
    item_methods = ['GET', 'DELETE', 'PATCH']
    embedded_fields = ['user']
