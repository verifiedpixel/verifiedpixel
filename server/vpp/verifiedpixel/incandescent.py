import hmac
import base64
import json
import time
import urllib.parse
from requests import request
from hashlib import sha1 as sha
from flask import current_app

import superdesk

from .exceptions import APIGracefulException

# @TODO: for debug purpose
from pprint import pprint  # noqa


def get_incandescent_results(href):
    with superdesk.app.app_context():
        uid = current_app.config['INCANDESCENT_UID']
        apiKey = current_app.config['INCANDESCENT_APIKEY']
    utc_expires = int(time.time()) + 300
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
    raw_results = get_response.json()
    if raw_results.get('status', None) == 710:
        raise(APIGracefulException(raw_results))
    if raw_results.get('status', None) == 755:
        apis = ['google', 'bing', 'baidu', 'yandex', 'other']
        return {
            'stats': {
                "total_{api}".format(api=api): 0
                for api in apis
            },
            'results': {}
        }

    verification_results = {}
    verification_stats = {}
    try:
        for url, data in raw_results.items():
            for page_n, page in data['pages'].items():
                source = page['source']
                key = url.replace('.', '_') + "_" + page_n
                if source not in verification_results:
                    verification_results[source] = {}
                    verification_stats["total_{}".format(source)] = 0
                verification_stats["total_{}".format(source)] += 1
                verification_results[source][key] = page
    except (TypeError, KeyError) as e:
        raise(APIGracefulException((e, raw_results, )))
    return {
        'stats': verification_stats,
        'results': verification_results
    }
