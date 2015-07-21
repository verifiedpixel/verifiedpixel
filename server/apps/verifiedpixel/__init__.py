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
from pytineye.api import TinEyeAPIRequest
from pytineye.exceptions import TinEyeAPIError
from pprint import pprint

import superdesk
from superdesk.celery_app import celery


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


TINEYE_API_URL = 'http://api.tineye.com/rest/'
TINEYE_PUBLIC_KEY = 'LCkn,2K7osVwkX95K4Oy'
TINEYE_SECRET_KEY = '6mm60lsCNIB,FwOWjJqA80QZHh9BMwc-ber4u=t^'
tineye_api = TinEyeAPIRequest(
    api_url=TINEYE_API_URL,
    public_key=TINEYE_PUBLIC_KEY,
    private_key=TINEYE_SECRET_KEY)



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
        logger.warning(message)


def get_tineye_results(content):
    response = tineye_api.search_data(content)
    #pprint(response)
    if response.total_results > 0:
        return response
    raise TinEyeGracefulException(result)


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
        logger.info('VerifiedPixel: found new ingested item: "{}"'.format(filename))
        izitru_results = get_izitru_results(content)
        gris_results = get_gris_results(content)
        try:
            tineye_results = get_tineye_results(content)
        except TinEyeGracefulException:
            pass
        # TODO:append verification data to item
