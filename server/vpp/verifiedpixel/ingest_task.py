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
from celery import chord, group
import json

from pytineye.api import TinEyeAPIRequest, TinEyeAPIError

import superdesk
from superdesk.celery_app import celery

from .logging import error, warning, info, success
from .elastic import handle_elastic_write_problems_wrapper
from .exceptions import APIGracefulException, ImageNotFoundException
from .incandescent import (
    get_incandescent_results, get_incandescent_results_callback
)


# @TODO: for debug purpose
from pprint import pprint  # noqa
from .logging import debug  # noqa


register('dill', dill.dumps, dill.loads, content_type='application/x-binary-data', content_encoding='binary')


def init_tineye(app):
    app.data.vpp_tineye_api = TinEyeAPIRequest(
        api_url=app.config['TINEYE_API_URL'],
        public_key=app.config['TINEYE_PUBLIC_KEY'],
        private_key=app.config['TINEYE_SECRET_KEY']
    )


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


def get_tineye_results(content):
    try:
        response = superdesk.app.data.vpp_tineye_api.search_data(content)
    except TinEyeAPIError as e:
        # @TODO: or e.message[0] == 'NO_SIGNATURE_ERROR' ?
        if e.code == 400:
            return {"status": "error", "message": repr(e.message)}
        raise APIGracefulException(e)
    except KeyError as e:
        if e.args[0] == 'code':
            raise APIGracefulException(e)
    else:
        return response.json_results


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
    'izitru': {"function": get_izitru_results, "args": ("filename", "content",)},
    'tineye': {"function": get_tineye_results, "args": ("content",)},
    #'incandescent': {"function": get_incandescent_results, "args": ("href",)},
}


def get_placeholder_api_getter(fixtures_list):  # pragma: no cover

    def create_eternal_fixture_generator():
        i = 0
        fixtures = [json.loads(x[1]) for x in prepare_sequence_from_args(fixtures_list)]
        max = len(fixtures)
        while True:
            yield fixtures[i]
            i = (i + 1) % max

    fixture_generator = create_eternal_fixture_generator()

    def api_getter(*args, **kwargs):
        return next(fixture_generator)

    return api_getter

MOCK_API_GETTERS = {
    'izitru': {"function": get_placeholder_api_getter([
        {"response_file": "test/vpp/mock_izitru_1.json"},
        {"response_file": "test/vpp/mock_izitru_3.json"},
        {"response_file": "test/vpp/mock_izitru_5.json"},
        {"response": {'status': 'error', 'message': 'something gone wrong'}}
    ]), "args": ("filename", "content",)},
    'tineye': {"function": get_placeholder_api_getter([
        {"response_file": "test/vpp/mock_tineye_many.json"},
        {"response_file": "test/vpp/mock_tineye_zero.json"},
        {"response": {'status': 'error', 'message': 'something gone wrong'}}
    ]), "args": ("content",)},
    'incandescent': {"function": get_placeholder_api_getter([
        {"response": {'status': 'error', 'message': 'mock not implemented yet'}}
    ]), "args": ("href",)},
}


def get_api_getters():
    if app.config['USE_VERIFICATION_MOCK']:
        return MOCK_API_GETTERS  # pragma: no cover
    else:
        return API_GETTERS


@celery.task(max_retries=3, bind=True, serializer='dill', name='vpp.append_api_result', ignore_result=False)
def append_api_results_to_item(self, item, api_name, args):
    filename = item['slugline']
    api_getter = get_api_getters()[api_name]['function']
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
            raise self.retry(exc=e, countdown=app.config['VERIFICATION_TASK_RETRY_INTERVAL'])
        else:
            error("{api}: max retries exceeded on "
                  "verification of {file}:\n {exception}".format(
                      api=api_name, file=filename, exception=e))
            verification_result = {"status": "error", "message": repr(e)}
    else:
        info("{api}: matchs found for {file}.".format(
            api=api_name, file=filename))
    # record result to database
    handle_elastic_write_problems_wrapper(
        lambda: superdesk.get_resource_service('ingest').patch(
            item['_id'],
            {'verification.{api}'.format(api=api_name): verification_result}
        )
    )


@celery.task(max_retries=3, bind=True, serializer='dill', name='vpp.append_incandescent_result', ignore_result=False)
def append_incandescent_results_to_item(self, item, href):
    api_name = 'incandescent'

    filename = item['slugline']
    info(
        "{api}: searching matches for {file}... ({tries} of {max})".format(
            api=api_name, file=filename, tries=self.request.retries, max=self.max_retries
        ))
    try:
        get_data = get_incandescent_results(href)
    except APIGracefulException as e:
        if self.request.retries < self.max_retries:
            warning("{api}: API exception raised during "
                    "verification of {file} (retrying):\n {exception}".format(
                        api=api_name, file=filename, exception=e))
            raise self.retry(exc=e, countdown=app.config['VERIFICATION_TASK_RETRY_INTERVAL'])
        else:
            error("{api}: max retries exceeded on "
                  "verification of {file}:\n {exception}".format(
                      api=api_name, file=filename, exception=e))
            verification_result = {"status": "error", "message": repr(e)}
            return verification_result
    else:
        info("{api}: waiting for matches for {file}.".format(
            api=api_name, file=filename))
        return get_data


@celery.task(
    max_retries=20, countdown=5, bind=True, serializer='dill',
    name='vpp.append_incandescent_result_callback', ignore_result=False
)
def append_incandescent_results_to_item_callback(self, get_data, item_id, filename):

    api_name = 'incandescent'

    try:
        verification_result = get_incandescent_results_callback(get_data)
    except APIGracefulException as e:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            error("{api}: timeout exceeded on "
                  "verification of {file}:\n {exception}".format(
                      api=api_name, file=filename, exception=e))
            verification_result = {"status": "error", "message": repr(e)}
    else:
        info("{api}: matchs found for {file}.".format(
            api=api_name, file=filename))
    # record result to database
    handle_elastic_write_problems_wrapper(
        lambda: superdesk.get_resource_service('ingest').patch(
            item_id,
            {'verification.{api}'.format(api=api_name): verification_result}
        )
    )


@celery.task(bind=True, name='vpp.finalize_verification')
def finalize_verification(self, *args, item_id, desk_id):
    success('Fetching item: {} into desk "Verified Images".'.format(item_id))
    handle_elastic_write_problems_wrapper(
        # Auto fetch items to the 'Verified Images' desk
        lambda: superdesk.get_resource_service('fetch').fetch(
            [{'_id': item_id, 'desk': desk_id}]
        )
    )
    handle_elastic_write_problems_wrapper(
        # Delete the ingest item
        lambda: superdesk.get_resource_service('ingest').delete(
            lookup={'_id': item_id}
        )
    )


@celery.task(bind=True, name='vpp.verify_ingest')
def verify_ingest(self):
    info(
        'Checking for new ingested images for verification...'
    )
    try:
        items = superdesk.get_resource_service('ingest').get_from_mongo(
            req=ParsedRequest(),
            lookup={
                'type': 'picture',
                'verification': {'$exists': False}
            }
        )
        desk = superdesk.get_resource_service('desks').find_one(req=ParsedRequest(), name='Verified Images')
        desk_id = str(desk['_id'])
    except Exception as e:
        error("Raised from verify_ingest task, aborting:")
        error(e)
        raise(e)
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
            "filename": filename,
            "content": content,
            "href": href
        }
        chord(
            group(
                group(
                    (append_api_results_to_item.subtask(
                        args=(
                            item, api_name,
                            [all_args[arg_name] for arg_name in data['args']]
                        )
                    ))
                    for api_name, data in get_api_getters().items()
                ),
                chord(
                    append_incandescent_results_to_item.subtask(
                        kwargs={
                            "item": item,
                            "href": href,
                        }
                    ),
                    append_incandescent_results_to_item_callback.subtask(
                        kwargs={
                            "filename": all_args['filename'],
                            "item_id": item['_id'],
                        }
                    )
                )
            ),
            finalize_verification.subtask(
                kwargs={"item_id": item['_id'], "desk_id": desk_id},
                immutable=True
            )
        ).delay()
