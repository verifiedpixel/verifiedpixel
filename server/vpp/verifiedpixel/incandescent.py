import logging  # noqa @TODO:
import hmac
import base64
import datetime
import calendar
import json
import urllib.parse
from requests import request
from hashlib import sha1 as sha
import superdesk

from .exceptions import APIGracefulException

# @TODO: for debug purpose
from pprint import pprint  # noqa


def get_incandescent_results(href):
    uid = superdesk.app.config['INCANDESCENT_UID']
    apiKey = superdesk.app.config['INCANDESCENT_APIKEY']
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
    if 'project_id' not in add_result:
        raise APIGracefulException(add_result)
    get_data = {
        'uid': uid,
        'expires': utc_expires,
        'signature': signature,
        'project_id': add_result['project_id']
    }
    return get_data


def get_incandescent_results_callback(get_data):
    get_headers = {'Content-type': 'application/json'}
    get_response = request(
        'POST', 'https://incandescent.xyz/api/get/', data=json.dumps(get_data), headers=get_headers
    )
    get_result = get_response.json()
    if get_result.get('status') == 710:
        raise(APIGracefulException(get_result))
    return get_result
