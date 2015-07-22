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
import time
from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
from pytineye.api import TinEyeAPIRequest
from pytineye.exceptions import TinEyeAPIError  # noqa @TODO: retry
from requests import request
from PIL import Image
from io import BytesIO

import superdesk
from superdesk.celery_app import celery


# @TODO: for debug purpose
from pprint import pprint  # noqa


# @TODO: read from env vars
TINEYE_API_URL = 'http://api.tineye.com/rest/'
TINEYE_PUBLIC_KEY = 'LCkn,2K7osVwkX95K4Oy'
TINEYE_SECRET_KEY = '6mm60lsCNIB,FwOWjJqA80QZHh9BMwc-ber4u=t^'

IZITRU_PRIVATE_KEY = '11d30480-a579-46e6-a33e-02330b94ce94'
IZITRU_ACTIVATION_KEY = '20faaa56-edc1-4395-a2d9-1eb6248f0922'
IZITRU_API_URL = 'https://www.izitru.com/scripts/uploadAPI.pl'


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)

tineye_api = TinEyeAPIRequest(
    api_url=TINEYE_API_URL,
    public_key=TINEYE_PUBLIC_KEY,
    private_key=TINEYE_SECRET_KEY
)


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


@celery.task
def get_tineye_results(content):
    response = tineye_api.search_data(content)
    # pprint(response)
    if response.total_results > 0:
        return response
    raise TinEyeGracefulException(response)


def get_gris_results(content):
    GRIS_API_KEY = 'AIzaSyCUvaKjv5CjNd9Em54HS4jNRVR2AuHr-U4'  # noqa
    return {}


@celery.task
def get_izitru_results(content):
    IZITRU_SECURITY_DATA = int(time.time())
    m = hashlib.md5()
    m.update(str(IZITRU_SECURITY_DATA).encode())
    m.update(IZITRU_PRIVATE_KEY.encode())
    IZITRU_SECURITY_HASH = m.hexdigest()

    logger.info('generated {}'.format(IZITRU_SECURITY_HASH))

    converted_image = BytesIO()
    img = Image.open(BytesIO(content))
    img.save(converted_image, 'JPEG')
    img.close()

    data = {
        'activationKey': IZITRU_ACTIVATION_KEY,
        'securityData': IZITRU_SECURITY_DATA,
        'securityHash': IZITRU_SECURITY_HASH,
        'exactMatch': 'true',
        'nearMatch': 'false',
        'storeImage': 'true',
    }
    files = {'upFile': converted_image.getvalue()}

    response = request('POST', IZITRU_API_URL, data=data, files=files)
    converted_image.close()
    print(response.text)

    return {}


@celery.task
def process_item(item):
    '''
    @TODO:
    attempt api lookups 3 times
    '''
    filename = item['slugline']
    try:
        content = get_original_image(item)
    except ImageNotFoundException:
        return
    logger.info('VerifiedPixel: found new ingested item: "{}"'.format(filename))

    izitru_results = get_izitru_results(content)

    gris_results = get_gris_results(content)

    try:
        tineye_results = get_tineye_results(content)
    except TinEyeGracefulException:
        pass
    else:
        logger.info('VerifiedPixel: "{}" - found smth on tineye'.format(filename))

    # TODO: append verification data to item:
    result = {}
    result['tineye'] = tineye_results
    result['izitru'] = izitru_results
    result['gris'] = gris_results


@celery.task
def verify_ingest():
    logger.info(
        'VerifiedPixel: Checking for new ingested images for verification...')

    '''
    TODO: lookup image items with no verification metadata
          attempt api lookups 3 times
    '''
    lookup = {'type': 'picture'}
    items = superdesk.get_resource_service('ingest').get(
        req=ParsedRequest(), lookup=lookup
    )
    for item in items:
        process_item(item)
