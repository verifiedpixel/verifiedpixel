import json
import zipfile
from flask import current_app as app
from eve.utils import ParsedRequest
from io import BytesIO, StringIO

from superdesk.celery_app import celery
from superdesk.resource import Resource
from superdesk import get_resource_service
from superdesk.services import BaseService
from superdesk.upload import url_for_media

from .ingest_task import get_original_image

# @TODO: for debug purpose
from pprint import pprint  # noqa
from .logging import debug


class VerificationResultsService(BaseService):
    def on_created(self, docs):
        for doc in docs:
            self_id = doc['_id']
            debug(self_id)
            debug(doc)
            # items_ids = doc['items']
            # zip_items(self_id, items_ids)

    def on_delete(self, doc):
        pass
        # app.media.delete(doc['result_id'])


class VerificationResultsResource(Resource):
    '''
    VerifiedPixelZip schema
    '''
    schema = {
        'izitru': {'type': 'dict'},
        'tineye': {'type': 'dict'},
        'incandescent_google': {'type': 'list'},
        'incandescent_bing': {'type': 'list'},
        'incandescent_baidu': {'type': 'list'},
        'incandescent_yandex': {'type': 'list'},
        'incandescent_other': {'type': 'list'},
    }
    privileges = {
        'GET': 'verification_results',
        'POST': 'verification_results',
        'PATCH': 'verification_results',
        'DELETE': 'verification_results'
    }


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
    vppzip_service.patch(result_id, {
        "status": "done",
        "result": uploaded_zip_url,
        "result_id": uploaded_zip_id
    })
