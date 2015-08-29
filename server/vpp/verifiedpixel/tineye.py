from pytineye.api import TinEyeAPIRequest, TinEyeAPIError

import superdesk
from .exceptions import APIGracefulException


# @TODO: for debug purpose
from pprint import pprint  # noqa
from .logging import debug  # noqa


def init_tineye(app):
    app.data.vpp_tineye_api = TinEyeAPIRequest(
        api_url=app.config['TINEYE_API_URL'],
        public_key=app.config['TINEYE_PUBLIC_KEY'],
        private_key=app.config['TINEYE_SECRET_KEY']
    )


def get_tineye_results(content):
    try:
        response = superdesk.app.data.vpp_tineye_api.search_data(content)
    except TinEyeAPIError as e:
        # @TODO: or e.message[0] == 'NO_SIGNATURE_ERROR' ?
        if e.code == 400:
            return {'total': None, 'results': {"status": "error", "message": repr(e.message)}}
        raise APIGracefulException(e)
    except KeyError as e:
        if e.args[0] == 'code':
            raise APIGracefulException(e)
    result = response.json_results
    if 'results' not in result or 'total_results' not in result['results']:
        raise APIGracefulException(result)
    return {'total': result['results']['total_results'], 'results': result}
