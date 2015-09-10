from superdesk.resource import Resource
from superdesk.services import BaseService

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


class VerificationResultsResource(Resource):
    '''
    VerifiedPixelZip schema
    '''
    schema = {
        'izitru': {'type': 'dict'},
        'tineye': {'type': 'dict'},
        'incandescent': {'type': 'dict'},
    }
    privileges = {
        'GET': 'verification_results',
        'POST': 'verification_results',
        'PATCH': 'verification_results',
        'DELETE': 'verification_results'
    }
