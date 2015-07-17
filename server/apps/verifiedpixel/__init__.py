# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import logging
import hashlib
# from hashlib import sha1
import hmac
import json
import random
import string
import time
import urllib
import urllib3
from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
# from eve.io.mongo.media import GridFSMediaStorage

import superdesk
from superdesk.celery_app import celery


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


class ImageNotFoundException(Exception):
    pass


def get_original_image(item):
    if item['renditions']:
        driver = app.data.mongo
        px = driver.current_mongo_prefix('ingest')
        _fs = GridFS(driver.pymongo(prefix=px).db)
        for k, v in item['renditions'].items():
            if k == 'original':
                _file = _fs.get(ObjectId(v['media']))
                content = _file.read()
                return content
    raise ImageNotFoundException()


class TinEyeGracefulException(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)


def get_tineye_results(filename, content):
    TINEYE_API_URL = 'http://api.tineye.com/rest/search/'
    TINEYE_PUBLIC_KEY = 'Q6oV_*ayv-NxRrT8jd=2y'
    TINEYE_SECRET_KEY = 'EtqaAOtzYOUkfnWU0mlJT2dIDGEgLX3c_JbddB=Z'
    t = int(time.time())
    nonce = ''.join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    boundary = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    to_sign = TINEYE_SECRET_KEY + 'POST' + \
        'multipart/form-data; boundary=' + boundary + \
        urllib.parse.quote_plus(filename) + str(t) + nonce + TINEYE_API_URL
    signature = hmac.new(
        TINEYE_SECRET_KEY.encode(), to_sign.encode()).hexdigest()

    logger.info('signature {}'.format(signature))

    data = {
        'api_key': TINEYE_PUBLIC_KEY,
        'date': t,
        'nonce': nonce,
        'api_sig': signature
    }
    response = urllib3.connection_from_url(TINEYE_API_URL).request_encode_body(
        'POST', TINEYE_API_URL + '?' + urllib.parse.urlencode(data),
        fields={'image_upload': content}, multipart_boundary=boundary
    )
    result = json.loads(response.data.decode("utf-8"))
    status_code = response.status
    if status_code not in [200]:
        raise TinEyeGracefulException(result)
    return result


def get_gris_results(content):
    GRIS_API_KEY = 'AIzaSyCUvaKjv5CjNd9Em54HS4jNRVR2AuHr-U4'
    return {}


def get_izitru_results(content):
    IZITRU_PRIVATE_KEY = '11d30480-a579-46e6-a33e-02330b94ce94'
    IZITRU_ACTIVATION_KEY = '20faaa56-edc1-4395-a2d9-1eb6248f0922'
    IZITRU_API_URL = 'https://www.izitru.com/scripts/uploadAPI.pl'
    IZITRU_SECURITY_DATA = int(time.time())
    m = hashlib.md5()
    m.update(str(IZITRU_SECURITY_DATA).encode())
    m.update(IZITRU_PRIVATE_KEY.encode())
    IZITRU_SECURITY_HASH = m.hexdigest()

    logger.info('generated {}'.format(IZITRU_SECURITY_HASH))

    data = {
        'activationKey': IZITRU_ACTIVATION_KEY,
        'securityData': IZITRU_SECURITY_DATA,
        'securityHash': IZITRU_SECURITY_HASH,
        'exactMatch': 'true',
        'nearMatch': 'false',
        'storeImage': 'true',
        'upFile': content
    }

    return {}


@celery.task
def verify_ingest():
    logger.info(
        'VerifiedPixel: Checking for new ingested images for verification...')

    '''
    TODO: lookup image items with no verification metadata
          maintain counter for retries and only attempt api lookups 3 times
    '''
    lookup = {'type': 'picture'}
    items = superdesk.get_resource_service('ingest').get(
        req=ParsedRequest(), lookup=lookup
    )
    for item in items:
        filename = item['slugline']
        try:
            content = get_original_image(item)
        except ImageNotFoundException:
            continue

        izitru_results = get_izitru_results(content)
        gris_results = get_gris_results(content)
        tineye_results = get_tineye_results(filename, content)

        # TODO:appeed verification data to item

        logger.info('found {}'.format(item.get('renditions')))
    else:
        logger.info('no ingest items found for {}'.format(lookup))
