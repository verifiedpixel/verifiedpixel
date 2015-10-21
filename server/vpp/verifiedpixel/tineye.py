from pytineye.api import TinEyeAPIRequest, TinEyeAPIError

import superdesk
from flask import current_app
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
        with superdesk.app.app_context():
            current_app.data.vpp_tineye_api = TinEyeAPIRequest(
                api_url=current_app.config['TINEYE_API_URL'],
                public_key=current_app.config['TINEYE_PUBLIC_KEY'],
                private_key=current_app.config['TINEYE_SECRET_KEY']
            )
            response = current_app.data.vpp_tineye_api.search_data(content)
    except TinEyeAPIError as e:
        # @TODO: or e.message[0] == 'NO_SIGNATURE_ERROR' ?
        if e.code == 400:
            return {
                'stats': {'total': None},
                'results': {"status": "error", "message": repr(e.message)}
            }
        raise APIGracefulException(e)
    except Exception as e:
        raise APIGracefulException(e)
    result = response.json_results
    for match in result['results']['matches']:
        match['earliest_crawl_date'] = min([
            backlink['crawl_date'] for backlink in match['backlinks']
        ])
    return {
        'stats': {'total': result['results']['total_results']},
        'results': result
    }
