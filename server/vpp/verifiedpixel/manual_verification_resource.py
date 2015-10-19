from eve.utils import ParsedRequest

import superdesk
from superdesk.resource import Resource
from superdesk.services import BaseService
from superdesk.celery_app import celery

from .ingest_task import verify_items

from .logging import error, info
from .logging import debug, print_task_exception   # noqa


class ManualVerificationService(BaseService):

    def on_created(self, docs):
        for doc in docs:
            verify_manually.delay(
                temp_id=doc['_id'],
                item_id=doc['item_id'],
                provider=doc['provider']
            )


class ManualVerificationResource(Resource):
    schema = {
        'item_id': {'type': 'string'},
        'provider': {'type': 'string'},
    }
    privileges = {
        'GET': 'archive',
        'POST': 'archive',
        'PATCH': 'archive',
        'DELETE': 'archive'
    }


@celery.task(bind=True, name='vpp.verify_manually')
@print_task_exception
def verify_manually(self, temp_id, item_id, provider):
    info(
        'Manual verification for {}...'.format(item_id)
    )
    try:
        desk = superdesk.get_resource_service('desks').find_one(req=ParsedRequest(), name='Verified Images')
        desk_id = str(desk['_id'])
    except Exception as e:
        error("Raised from verify_ingest task, aborting:")
        error(e)
        raise(e)
    else:
        item = superdesk.get_resource_service('archive').find_one(
            req=ParsedRequest(), _id=item_id)
        verify_items(
            [item], 'archive', desk_id,
            verification_providers=[provider]
        )
        superdesk.get_resource_service('manual_verification').delete(
            lookup={'_id': temp_id}
        )
