import logging
import zipfile
from flask import current_app as app
from flask import json
from eve.utils import ParsedRequest
from io import BytesIO, StringIO
from pymongo import MongoClient
import uuid

from superdesk.celery_app import celery
from superdesk.resource import Resource
from superdesk import get_resource_service
from superdesk.services import BaseService
from superdesk.upload import url_for_media
from superdesk.notification import push_notification

from .ingest_task import get_original_image

# @TODO: for debug purpose
from pprint import pprint  # noqa
from .logging import debug, print_task_exception  # noqa


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


class VerifiedPixelZipService(BaseService):
    def on_create(self, docs):
        for doc in docs:
            doc['vpp_id'] = str(uuid.uuid1())

    def on_created(self, docs):
        for doc in docs:
            items_ids = doc['items']
            vpp_id = doc['vpp_id']
            zip_items.delay(vpp_id, items_ids)

    def on_delete(self, doc):
        app.media.delete(doc['result_id'])


class VerifiedPixelZipResource(Resource):
    '''
    VerifiedPixelZip schema
    '''
    schema = {
        'items': {
            'type': 'list',
            # 'schema': Resource.rel('fetch', False)
            'schema': {
                'type': 'string',
            }
        },
        'result_id': {
            'type': 'string',
        },
        'result': {
            'type': 'string',
        },
        'status': {
            'type': 'string',
            'default': 'pending',
            'allowed': ['pending', 'processing', 'done', 'error'],
        },
        'vpp_id': {
            'type': 'string',
        }
    }
    privileges = {
        'GET': 'verifiedpixel_zip',
        # 'POST': 'verifiedpixel_zip',
        'POST': 'archive',
        # 'PATCH': 'verifiedpixel_zip',
        'PATCH': 'archive',
        'DELETE': 'verifiedpixel_zip'
    }


@celery.task
@print_task_exception
def zip_items(vpp_id, items_ids):
    mongo = app.extensions['pymongo']['MONGO'][1]
    transaction_result = mongo.verifiedpixel_zip.update(
        {"vpp_id": vpp_id},
        {"$set": {'status': "processing"}}
    )
    if transaction_result['n'] != 1:
        raise Exception(transaction_result)

    archive_service = get_resource_service('archive')
    vppzip_service = get_resource_service('verifiedpixel_zip')
    results_service = get_resource_service('verification_results')

    items = list(archive_service.get_from_mongo(
        req=ParsedRequest(), lookup={'_id': {'$in': items_ids}}))
    verification_ids = [item['verification']['results'] for item in items]
    verification_results = {
        result['_id']: result for result in
        list(results_service.get_from_mongo(
            req=ParsedRequest(), lookup={'_id': {'$in': verification_ids}})
        )
    }
    verification_data_object = StringIO()
    verification_data = {}
    zip_file_object = BytesIO()
    zip_file = zipfile.ZipFile(zip_file_object, mode='w')
    for item in items:
        item_id = item['_id']
        image = get_original_image(item, 'archive')[1]
        zip_file.writestr(item_id, image)
        item['verification']['results'] = verification_results[
            item['verification']['results']
        ]
        for field in ['_id', '_etag', '_created', '_updated']:
            del item['verification']['results'][field]
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

    transaction_result = mongo.verifiedpixel_zip.update(
        {"vpp_id": vpp_id},
        {
            "$set": {
                "status": "done",
                "result": uploaded_zip_url,
                "result_id": uploaded_zip_id
            },
        }
    )
    if transaction_result['n'] != 1:
        raise Exception(transaction_result)

    raw_id = str(
        list(mongo.verifiedpixel_zip.find({"vpp_id": vpp_id}))[0]['_id']
    )

    push_notification(
        'verifiedpixel_zip:ready',
        id=raw_id,
        url=uploaded_zip_url
    )
