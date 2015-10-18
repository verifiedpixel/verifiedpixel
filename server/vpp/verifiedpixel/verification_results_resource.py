from superdesk.resource import Resource
from superdesk.services import BaseService


class VerificationResultsService(BaseService):
    pass


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
