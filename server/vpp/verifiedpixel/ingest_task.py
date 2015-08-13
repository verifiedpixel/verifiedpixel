import logging
import hashlib
import time
from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
from requests import request
from PIL import Image
from io import BytesIO
import dill

from pytineye.api import TinEyeAPIRequest, TinEyeAPIError

from apiclient.discovery import build as google_build
from apiclient.discovery import HttpError as GoogleHttpError

import superdesk
from superdesk.celery_app import celery


# @TODO: for debug purpose
from pprint import pprint  # noqa


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


def init_tineye(app):
    app.data.tineye_api = TinEyeAPIRequest(
        api_url=app.config['TINEYE_API_URL'],
        public_key=app.config['TINEYE_PUBLIC_KEY'],
        private_key=app.config['TINEYE_SECRET_KEY']
    )


class ImageNotFoundException(Exception):
    pass


def get_original_image(item):
    if 'renditions' in item:
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
    try:
        response = superdesk.app.data.tineye_api.search_data(content)
    except TinEyeAPIError as e:
        raise APIGracefulException(e)
    except KeyError as e:
        if e.args[0] == 'code':
            raise APIGracefulException(e)
    else:
        return response.json_results


def get_gris_results(href):
    try:
        service = google_build('customsearch', 'v1',
                               developerKey=superdesk.app.config['GRIS_API_KEY'])
        res = service.cse().list(
            q=href,
            searchType='image',
            cx=superdesk.app.config['GRIS_API_CX'],
        ).execute()
    except GoogleHttpError as e:
        raise APIGracefulException(e)
    return res


def get_izitru_results(filename, content):
    izitru_security_data = int(time.time())
    m = hashlib.md5()
    m.update(str(izitru_security_data).encode())
    m.update(superdesk.app.config['IZITRU_PRIVATE_KEY'].encode())
    izitru_security_hash = m.hexdigest()

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
        'activationKey': superdesk.app.config['IZITRU_ACTIVATION_KEY'],
        'securityData': izitru_security_data,
        'securityHash': izitru_security_hash,
        'exactMatch': 'true',
        'nearMatch': 'false',
        'storeImage': 'true',
    }
    files = {'upFile': (filename, upfile, 'image/jpeg', {'Expires': '0'})}
    response = request('POST', superdesk.app.config['IZITRU_API_URL'], data=data, files=files)
    if response.status_code != 200:
        raise APIGracefulException(response)
    result = response.json()
    if 'verdict' not in result:
        raise APIGracefulException(result)
    return result


@celery.task(max_retries=3, bind=True)
def append_api_results_to_item(self, item, api_name, serialized_api_getter, args):
    api_getter = dill.loads(serialized_api_getter)
    filename = item['slugline']
    logger.info(
        "VerifiedPixel: {api}: searching matches for {file}...".format(
            api=api_name, file=filename
        ))
    try:
        verification_result = api_getter(*args)
    except APIGracefulException as e:
        logger.warning(
            "VerifiedPixel: {api}: API exception raised during "
            "verification of {file}:\n {exception}".format(
                api=api_name, file=filename, exception=e
            ))
        self.retry(exc=e, countdown=60)
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
        serialized_api_getter = dill.dumps(api_getter)
        append_api_results_to_item.delay(
            item, api_name, serialized_api_getter, args
        )

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
        process_item.delay(item)
