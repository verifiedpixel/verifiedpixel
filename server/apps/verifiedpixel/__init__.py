import logging
import json
import zipfile
from flask import current_app as app
from eve.utils import ParsedRequest
from pytineye.api import TinEyeAPIRequest
from pytineye.exceptions import TinEyeAPIError  # noqa @TODO: retry
from io import BytesIO, StringIO

from superdesk.celery_app import celery
from superdesk import get_backend
from superdesk.resource import Resource
from superdesk import get_resource_service
from superdesk.services import BaseService
from superdesk.upload import url_for_media

from .ingest_task import verify_ingest  # noqa
from .ingest_task import get_original_image

# @TODO: for debug purpose
from pprint import pprint  # noqa


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


class VerifiedPixelZipService(BaseService):
    def on_created(self, doc):
        self_id = doc[0]['_id']
        items_ids = doc[0]['items']
        zip_items(self_id, items_ids)

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
def zip_items(result_id, items_ids):
    archive_service = get_resource_service('archive')
    vppzip_service = get_resource_service('verifiedpixel_zip')

    vppzip_service.patch(
        result_id,
        {'status': "processing"},
    )

    items = archive_service.get_from_mongo(req=ParsedRequest(),
                                           lookup={'_id': {'$in': items_ids}})
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
        zip_file_object.getvalue(), filename=str(items_ids),
        content_type='application/zip',
        resource=vppzip_service.datasource,
        metadata={}
    )
    uploaded_zip_url = url_for_media(uploaded_zip_id)
    vppzip_service.patch(
        result_id,
        {'status': "done", "result": uploaded_zip_url},
    )
