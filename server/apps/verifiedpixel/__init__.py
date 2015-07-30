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
from apiclient.discovery import build

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

GRIS_API_KEY = 'AIzaSyCUvaKjv5CjNd9Em54HS4jNRVR2AuHr-U4'
GRIS_API_CX = '008702632149434239236:xljn9isiv1i'


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
                href = v['href']
                return (href, content)
    raise ImageNotFoundException()


class APIGracefulException(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)
        logger.warning(message)


def get_tineye_results(content):
    response = tineye_api.search_data(content)
    if response.total_results > 0:
        return response.json_results
    raise APIGracefulException(response)


def get_gris_results(href):
    service = build('customsearch', 'v1',
                    developerKey=GRIS_API_KEY)
    res = service.cse().list(
        q=href,
        searchType='image',
        cx=GRIS_API_CX,
    ).execute()
    return res


def get_izitru_results(filename, content):
    IZITRU_SECURITY_DATA = int(time.time())
    m = hashlib.md5()
    m.update(str(IZITRU_SECURITY_DATA).encode())
    m.update(IZITRU_PRIVATE_KEY.encode())
    IZITRU_SECURITY_HASH = m.hexdigest()

    upfile = content
    img = Image.open(BytesIO(content))
    if img.format != 'JPEG':
        exif = img.info.get('exif', b"")
        converted_image = BytesIO()
        img.save(converted_image, 'JPEG', exif=exif)
        upfile = converted_image.getvalue()
        converted_image.close()
    img.close()

    data = {
        'activationKey': IZITRU_ACTIVATION_KEY,
        'securityData': IZITRU_SECURITY_DATA,
        'securityHash': IZITRU_SECURITY_HASH,
        'exactMatch': 'true',
        'nearMatch': 'false',
        'storeImage': 'true',
    }
    files = {'upFile': (filename, upfile, 'image/jpeg', {'Expires': '0'})}
    response = request('POST', IZITRU_API_URL, data=data, files=files)
    return response.json()


@celery.task
def append_api_results_to_item(item, api_name, api_getter, args):
    filename = item['slugline']
    logger.info(
        "VerifiedPixel: {api}: searching matches for {file}...".format(
            api=api_name, file=filename
        ))
    try:
        verification_result = api_getter(*args)
    except APIGracefulException:
        logger.warning(
            "VerifiedPixel: {api}: no matches found for {file}.".format(
                api=api_name, file=filename
            ))
        # @TODO: retry a task here too?
    else:
        logger.info(
            "VerifiedPixel: {api}: matchs found for {file}.".format(
                api=api_name, file=filename
            ))
        superdesk.get_resource_service('ingest').patch(
            item['_id'],
            {'verification.%s' % api_name: verification_result},
        )


@celery.task
def process_item(item):
    '''
    TODO: attempt api lookups 3 times
    '''
    filename = item['slugline']
    try:
        href, content = get_original_image(item)
    except ImageNotFoundException:
        return
    logger.info(
        'VerifiedPixel: found new ingested item: "{}"'.format(filename)
    )
    for api_name, api_getter, args in [
        ('izitru', get_izitru_results, (filename, content,)),
        ('tineye', get_tineye_results, (content,)),
        ('gris', get_gris_results, (href,)),
    ]:
        append_api_results_to_item(item, api_name, api_getter, args)

    # Auto fetch items to the 'Verified Imges' desk
    desk = superdesk.get_resource_service('desks').find_one(req=None, name='Verified Images')
    desk_id = str(desk['_id'])
    item_id = str(item['_id'])
    logger.info('Fetching item: {} into desk: {}'.format(item_id, desk_id))
    superdesk.get_resource_service('fetch').fetch([{'_id': item_id, 'desk': desk_id}])

    # Delete the ingest item
    superdesk.get_resource_service('ingest').delete(lookup={'_id': item_id})


@celery.task
def verify_ingest():
    logger.info(
        'VerifiedPixel: Checking for new ingested images for verification...'
    )
    items = superdesk.get_resource_service('ingest').get_from_mongo(
        req=ParsedRequest(),
        lookup={
            'type': 'picture',
            'verification': {'$exists': False}
        }
    )
    for item in items:
        process_item(item)
