import logging
import hashlib
import hmac
import base64
import time
import datetime
import calendar
import json
import urllib.request
import urllib.parse
import urllib.error
from gridfs import GridFS
from eve.utils import ParsedRequest
from requests import request
from PIL import Image
from io import BytesIO
from hashlib import sha1 as sha
from flask import current_app as app

import superdesk

from .exceptions import APIGracefulException

# @TODO: for debug purpose
from pprint import pprint  # noqa


def get_incandescent_results(href):
    uid = app.config['INCANDESCENT_UID']
    apiKey = app.config['INCANDESCENT_APIKEY']
    expires = datetime.datetime.now() - datetime.timedelta(minutes=110)
    utc_expires = calendar.timegm(expires.timetuple())
    to_string = str(uid) + "\n" + str(utc_expires)
    binary_signature = hmac.new(apiKey.encode(), to_string.encode(), sha)
    signature = urllib.parse.quote_plus(
        base64.b64encode(binary_signature.digest()))
    images = [href]
    add_data = {
        'uid': uid,
        'expires': utc_expires,
        'signature': signature,
        'images': images
    }
    add_headers = {'Content-type': 'application/json'}
    add_response = request(
        'POST', 'https://incandescent.xyz/api/add/', data=json.dumps(add_data), headers=add_headers)
    if add_response.status_code != 200:
        raise APIGracefulException(add_response)

    add_result = add_response.json()
    if not add_result['project_id']:
        raise APIGracefulException(add_result)

    get_data = {
        'uid': uid,
        'expires': utc_expires,
        'signature': signature,
        'project_id': add_result['project_id']
    }
    get_headers = {'Content-type': 'application/json'}
    results = None
    while not results:
        get_response = request(
            'POST', 'https://incandescent.xyz/api/get/', data=json.dumps(get_data), headers=get_headers)
        get_result = get_response.json()
        if get_result.get('status') == 710:
            results = None
        else:
            results = get_result

    return results

results = get_incandescent_results(
    'http://vppmaster.dev.superdesk.org/api/upload/55c9fdfb6cdb31004e08aa5f/raw?_schema=http')
print(results)
