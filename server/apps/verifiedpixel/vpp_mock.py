# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from httmock import urlmatch, HTTMock, all_requests
import json

from pprint import pprint  # noqa

from urllib3.connectionpool import HTTPConnectionPool
orig_urlopen = HTTPConnectionPool.urlopen
orig_http = HTTPConnectionPool


from urllib3_mock import Responses  # noqa
import re  # noqa
from unittest.mock import ANY  # noqa


@urlmatch(scheme='https', netloc='www.izitru.com', path='/scripts/uploadAPI.pl')
def izitru_request(url, request):
    print("DEBUG========================requests-IZITRU")
    with open('./izitru_response.json', 'r') as f:
        return {'status_code': 200,
                'content': json.load(f),
                }


@all_requests
def debug_request(url, request):
    print("####### DEBUG ########")
    print(url)
    return {'status_code': 200, 'content': b'{"foo": "bar"}', }


def setup_vpp_mock(context):
    context.mock = HTTMock(*[izitru_request, debug_request, ])
    context.mock.__enter__()


def teardown_vpp_mock(context):
    if hasattr(context, 'mock'):
        context.mock.__exit__(None, None, None)


###############################################################################

responses = Responses('urllib3')


def print_debug(request):
    print("DEBUG========================urllib3-TINEYE")
    with open('./tineye_response.json', 'rb') as f:
        return (200, {}, f.read())


url_re = re.compile(r'.*/rest/search/.*')
responses.add_callback('POST', url_re, callback=print_debug)


def pass_through(req):
    print("DEBUG========================urllib3-pass-through")
    print((req.method, req.host, req.port, req.url, ))

    new_params = {}
    for key in ['method', 'headers', 'body', 'url']:
        new_params[key] = getattr(req, key)

    http = orig_http(host=req.host, port=req.port)
    res = orig_urlopen(http, **new_params)
    result = (res.status, res.getheaders(), res.data)
    return result

responses.add_callback(ANY, re.compile(r'/.*'), callback=pass_through)
###############################################################################
