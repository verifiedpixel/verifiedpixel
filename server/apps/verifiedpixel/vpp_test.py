from unittest import TestCase
from flask import current_app as app
from eve.utils import config, ParsedRequest
import json

import superdesk
from superdesk import get_resource_service
from superdesk.tests import setup
from superdesk.media.renditions import generate_renditions
from superdesk.upload import url_for_media

from apps.verifiedpixel import verify_ingest

from .vpp_mock import (
    activate_tineye_mock, activate_izitru_mock, activate_gris_mock
)

from pprint import pprint  # noqa @TODO: debug


class VerifiedPixelAppTest(TestCase):

    maxDiff = None

    def setUp(self):
        setup(context=self)

    def tearDown(self):
        pass

    def upload_fixture_image(self):
        fixture_image_path = './test/vpp/test.png'
        file_name = 'test.png'
        content_type = 'image/png'
        file_type = 'image'
        with self.app.app_context():
            with open(fixture_image_path, mode='rb') as f:
                file_id = app.media.put(
                    f, filename=file_name,
                    content_type=content_type,
                    resource=get_resource_service('ingest').datasource,
                    metadata={}
                )
                inserted = [file_id]
                renditions = generate_renditions(
                    f, file_id, inserted, file_type, content_type,
                    rendition_config=config.RENDITIONS['picture'],
                    url_for_media=url_for_media
                )
            data = [{
                'headline': 'test',
                'slugline': 'rebuild',
                'renditions': renditions,
                'type': 'picture'
            }]
            get_resource_service('ingest').post(data)
        with open('./ingest_item_verification.json', 'r') as f:
            self.verification_result = json.load(f)

    @activate_izitru_mock('./test/vpp/izitru_response.json')
    @activate_tineye_mock('./test/vpp/tineye_response.json')
    @activate_gris_mock([
        './test/vpp/gris_discovery_response.json',
        './test/vpp/gris_search_response.json'
    ])
    def test_pass(self):
        self.upload_fixture_image()
        with self.app.app_context():
            verify_ingest()

            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('ingest').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertEqual(
                self.verification_result,
                list(items)[0]['verification']
            )
