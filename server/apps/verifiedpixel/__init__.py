import logging
import hashlib
import time
import json
import zipfile
from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
from pytineye.api import TinEyeAPIRequest
from pytineye.exceptions import TinEyeAPIError  # noqa @TODO: retry
from requests import request
from PIL import Image
from io import BytesIO, StringIO
from apiclient.discovery import build

import superdesk
from superdesk.celery_app import celery
from superdesk import get_backend
from superdesk.resource import Resource
from superdesk import get_resource_service
from superdesk.services import BaseService
from superdesk.upload import url_for_media

# @TODO: for debug purpose
from pprint import pprint  # noqa


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


class VerifiedPixelZipService(BaseService):
    def on_created(self, doc):
        self_id = doc[0]['_id']
        item_ids = doc[0]['items']
        zip_items(self_id, item_ids)

    def on_delete(self, doc):
        # @TODO: delete file
        pass


class VerifiedPixelZipResource(Resource):
    '''
    VerifiedPixelZip schema
    '''
    schema = {
        'items': {
            'type': 'list',
            'schema': Resource.rel('fetch', False)
        },
        'result': {
            'type': 'string',
        },
        'status': {
            'type': 'string',
            'default': 'pending',
            'allowed': ['pending', 'processing', 'done', 'error'],
        },
    }
    privileges = {
        'GET': 'verifiedpixel_zip',
        'POST': 'verifiedpixel_zip',
        'DELETE': 'verifiedpixel_zip'
    }


def init_app(app):
    endpoint_name = 'verifiedpixel_zip'
    service = VerifiedPixelZipService(endpoint_name, backend=get_backend())
    VerifiedPixelZipResource(endpoint_name, app=app, service=service)

    app.data.tineye_api = TinEyeAPIRequest(
        api_url=app.config['TINEYE_API_URL'],
        public_key=app.config['TINEYE_PUBLIC_KEY'],
        private_key=app.config['TINEYE_SECRET_KEY']
    )


@celery.task
def zip_items(result_id, item_ids):
    archive_service = get_resource_service('archive')
    vppzip_service = get_resource_service('verifiedpixel_zip')

    vppzip_service.patch(
        result_id,
        {'status': "processing"},
    )

    items = archive_service.get_from_mongo(req=ParsedRequest(),
                                           lookup={'_id': {'$in': item_ids}})
    verification_data_object = StringIO()
    verification_data = {}
    zip_file_object = BytesIO()
    zip_file = zipfile.ZipFile(zip_file_object, mode='w')
    for item in items:
        item_id = item['_id']
        image = get_original_image(item)[1]
        zip_file.writestr(item_id, image)
        verification_data[item_id] = item['verification']
    json.dump(verification_data, verification_data_object)
    zip_file.writestr('verification.json', verification_data_object.getvalue())
    zip_file.close()

    uploaded_zip_id = app.media.put(
        zip_file_object.getvalue(), filename=str(item_ids),
        content_type='application/zip',
        resource=vppzip_service.datasource,
        metadata={}
    )
    uploaded_zip_url = url_for_media(uploaded_zip_id)
    vppzip_service.patch(
        result_id,
        {'status': "done", "result": uploaded_zip_url},
    )
    print('done:')
    print(result_id)


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
    response = superdesk.app.data.tineye_api.search_data(content)
    if response.total_results > 0:
        return response.json_results
    raise APIGracefulException(response)


def get_gris_results(href):
    service = build('customsearch', 'v1',
                    developerKey=superdesk.app.config['GRIS_API_KEY'])
    res = service.cse().list(
        q=href,
        searchType='image',
        cx=superdesk.app.config['GRIS_API_CX'],
    ).execute()
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
    # @TODO: mb check here also presence of some of the required fields
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
