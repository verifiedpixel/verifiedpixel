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
import json
import time
import requests
import datetime
from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
# from eve.io.mongo.media import GridFSMediaStorage
from pytineye import TinEyeAPIRequest
from apiclient.discovery import build

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
                href = v['href']
                return (href, content)
    raise ImageNotFoundException()


class TinEyeGracefulException(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)


def get_tineye_results(filename, content):
    TINEYE_API_URL = 'https://api.tineye.com/rest/'
    #TINEYE_PUBLIC_KEY = 'Q6oV_*ayv-NxRrT8jd=2'
    #TINEYE_SECRET_KEY = 'EtqaAOtzYOUkfnWU0mlJT2dIDGEgLX3c_JbddB=Z'
    # This are test keys
    TINEYE_PUBLIC_KEY = 'LCkn,2K7osVwkX95K4Oy'
    TINEYE_SECRET_KEY = '6mm60lsCNIB,FwOWjJqA80QZHh9BMwc-ber4u=t^'
    api = TinEyeAPIRequest(TINEYE_API_URL, TINEYE_PUBLIC_KEY, TINEYE_SECRET_KEY)
    response = api.search_data(data=content)

    return response.get_json_results()
    

def get_gris_results(href):
    GRIS_API_KEY = 'AIzaSyCUvaKjv5CjNd9Em54HS4jNRVR2AuHr-U4'
    service = build('customsearch', 'v1',
            developerKey=GRIS_API_KEY)
    res = service.cse().list(
        q=href,
        searchType='image',
        cx='008702632149434239236:xljn9isiv1i',
    ).execute()
    
    return res 


class IzitruGracefulException(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)


def get_izitru_results(filename, content):
    IZITRU_PRIVATE_KEY = '11d30480-a579-46e6-a33e-02330b94ce94'
    IZITRU_ACTIVATION_KEY = '20faaa56-edc1-4395-a2d9-1eb6248f0922'
    IZITRU_API_URL = 'https://www.izitru.com/scripts/uploadAPI.pl'
    IZITRU_SECURITY_DATA = int(time.time())
    m = hashlib.md5()
    m.update(str(IZITRU_SECURITY_DATA).encode())
    m.update(IZITRU_PRIVATE_KEY.encode())
    IZITRU_SECURITY_HASH = m.hexdigest()

    data = {
        'activationKey': IZITRU_ACTIVATION_KEY,
        'securityData': IZITRU_SECURITY_DATA,
        'securityHash': IZITRU_SECURITY_HASH,
        'exactMatch': 'true',
        'nearMatch': 'false',
        'storeImage': 'true',
        'image': filename
    }
    
    files = {'upFile': (filename, content, 'image/jepg', {'Expires': '0'})}

    response = requests.post(IZITRU_API_URL, files=files, data=data)
    result = response.json()
    status_code = response.status_code

    if status_code not in [200]:
        raise IzitruGracefulException(result)
    return result


@celery.task
def verify_ingest():
    logger.info(
        'VerifiedPixel: Checking for new ingested images for verification...')

    '''
    TODO: lookup image items with no verification metadata
          maintain counter for retries and only attempt api lookups 3 times
    '''
    lookup = {
        'type': 'picture',
        'verification': { '$exists': False }
    }
    ingest_service = superdesk.get_resource_service('ingest')
    items = ingest_service.get_from_mongo(
        req=None, lookup=lookup
    )
    for item in items:
        verification = {
            'tineye': {},
            'gris': {},
            'izitru': {},
            'attempts': 1,
            'last_attempt': datetime.datetime.now()
        }

        item['verification'] = verification
        # save the attempt first
        ingest_service.put(item['_id'], item)

        filename = item['slugline']
        try:
            href, content = get_original_image(item)
        except ImageNotFoundException:
            continue

        verification['izitru'] = izitru_results = get_izitru_results(filename, content)
        verification['gris'] = get_gris_results(href)
        verification['tineye'] = get_tineye_results(filename, content)

        # save updated verification dict to item
        ingest_service.put(item['_id'], item)
    else:
        logger.info('no ingest items found for {}'.format(lookup))
