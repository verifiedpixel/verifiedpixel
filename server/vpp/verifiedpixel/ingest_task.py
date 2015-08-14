import hashlib
import time
from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
from requests import request
from PIL import Image
from io import BytesIO
from kombu.serialization import register
import dill

from pytineye.api import TinEyeAPIRequest, TinEyeAPIError

from apiclient.discovery import build as google_build
from apiclient.discovery import HttpError as GoogleHttpError

import superdesk
from superdesk.celery_app import celery

from .logging import error, warning, info


# @TODO: for debug purpose
from pprint import pprint  # noqa


register('dill', dill.dumps, dill.loads, content_type='application/x-binary-data', content_encoding='binary')


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
    pass


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


API_GETTERS = {
    'izitru': get_izitru_results,
    'tineye': get_tineye_results,
    'gris': get_gris_results,
}


@celery.task(max_retries=3, bind=True, serializer='dill')
def append_api_results_to_item(self, item, api_name, args):
    filename = item['slugline']
    item_id = item['_id']
    api_getter = API_GETTERS[api_name]
    info(
        "{api}: searching matches for {file}... ({tries} of {max})".format(
            api=api_name, file=filename, tries=self.request.retries, max=self.max_retries
        ))
    try:
        verification_result = api_getter(*args)
    except APIGracefulException as e:
        if self.request.retries < self.max_retries:
            warning("{api}: API exception raised during "
                    "verification of {file} (retrying):\n {exception}".format(
                        api=api_name, file=filename, exception=e))
            raise self.retry(exc=e, countdown=60)
        else:
            error("{api}: max retries exceeded on "
                  "verification of {file}:\n {exception}".format(
                      api=api_name, file=filename, exception=e))
            verification_result = {"status": "error", "message": repr(e)}
    else:
        info("{api}: matchs found for {file}.".format(
            api=api_name, file=filename))
    # record result to database
    ingest_service = superdesk.get_resource_service('ingest')
    ingest_service.patch(
        item_id, {'verification.%s' % api_name: verification_result}
    )
    updated_item = ingest_service.find_one(req=None, _id=item_id)
    if 'verification' in updated_item and len(updated_item['verification']) == len(API_GETTERS):
        # Auto fetch items to the 'Verified Imges' desk
        desk = superdesk.get_resource_service('desks').find_one(req=None, name='Verified Images')
        desk_id = str(desk['_id'])
        #info('=====================================DONE=================================')
        info('Fetching item {}: {} into desk: {}'.format(filename, item_id, desk_id))
        superdesk.get_resource_service('fetch').fetch([{'_id': item_id, 'desk': desk_id}])
        # Delete the ingest item
        ingest_service.delete(lookup={'_id': item_id})


def verify_ingest_task():
    info(
        'Checking for new ingested images for verification...'
    )
    items = superdesk.get_resource_service('ingest').get_from_mongo(
        req=ParsedRequest(),
        lookup={
            'type': 'picture',
            'verification': {'$exists': False}
        }
    )
    for item in items:
        filename = item['slugline']
        info(
            'found new ingested item: "{}"'.format(filename)
        )
        try:
            href, content = get_original_image(item)
        except ImageNotFoundException:
            return
        all_args = {
            'izitru': (filename, content,),
            'tineye': (content,),
            'gris': (href,),
        }
        for api_name in API_GETTERS:
            args = all_args[api_name]
            append_api_results_to_item.delay(item, api_name, args)
