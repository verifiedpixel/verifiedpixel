# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from httmock import urlmatch, HTTMock
import json
import logging

from pprint import pprint  # noqa

from urllib3.connectionpool import HTTPConnectionPool
orig_urlopen = HTTPConnectionPool.urlopen


from urllib3_mock import Responses  # noqa
import re  # noqa
from unittest.mock import ANY  # noqa


logger = logging.getLogger('superdesk')
logger.setLevel(logging.DEBUG)


def activate_izitru_mock(fixture_path):
    @urlmatch(
        scheme='https', netloc='www.izitru.com', path='/scripts/uploadAPI.pl'
    )
    def izitru_request(url, request):
        logger.debug("served requests mock for IZITRU")
        with open(fixture_path, 'r') as f:
            return {'status_code': 200, 'content': json.load(f), }

    def wrap(f):
        def test_new(*args):
            with HTTMock(izitru_request):
                f(*args)
        return test_new
    return wrap


def activate_tineye_mock(fixture_path):
    responses = Responses('urllib3')

    def tineye_response(request):
        logger.debug("served urllib3 mock for TINEYE")
        with open(fixture_path, 'rb') as f:
            return (200, {}, f.read())
    responses.add_callback(
        'POST', re.compile(r'.*api\.tineye\.com/rest/search/.*'),
        callback=tineye_response
    )

    def pass_through(req):
        '''
        workaround for elasticsearch which uses urllib3 as well
        '''
        '''
        logger.debug("urllib3-PASS-THROUGH: " + str(
            (req.method, req.host, req.port, req.url, )
        ))
        '''
        new_params = {}
        for key in ['method', 'headers', 'body', 'url']:
            new_params[key] = getattr(req, key)
        http = HTTPConnectionPool(host=req.host, port=req.port)
        res = orig_urlopen(http, **new_params)
        return (res.status, res.getheaders(), res.data)
    responses.add_callback(ANY, re.compile(r'/.*'), callback=pass_through)

    def wrap(f):
        @responses.activate
        def test_new(*args):
            f(*args)
        return test_new
    return wrap
