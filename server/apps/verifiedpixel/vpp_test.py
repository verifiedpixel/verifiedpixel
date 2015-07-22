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
from .vpp_mock import setup_vpp_mock, teardown_vpp_mock

from pprint import pprint  # noqa @TODO: debug


class VerifiedPixelAppTest(TestCase):

    maxDiff = None

    def setUp(self):
        setup(context=self)
        #setup_vpp_mock(self)

    def tearDown(self):
        teardown_vpp_mock(self)

    def upload_fixture_image(self):
        fixture_image_path = './test.png'
        file_name = 'test.png'
        content_type = 'image/png'
        file_type = 'image'
        with self.app.app_context():
            with open(fixture_image_path, mode='rb') as f:
                file_id = app.media.put(f, filename=file_name,
                                        content_type=content_type,
                                        resource=get_resource_service('ingest').datasource,
                                        metadata={})
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

    def test_pass(self):
        self.upload_fixture_image()
        with self.app.app_context():
            verify_ingest()  # noqa

            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('ingest').get(
                req=ParsedRequest(), lookup=lookup
            )

            if True:
                with open('ingest_item_verification.json', 'w') as f:
                    json.dump(list(items)[0]['verification'], f)

            verification_result = list(items)[0]['verification']
            self.assertEqual(
                self.verification_result['izitru'],
                verification_result['izitru']
            )

            #self.assertEqual(
                #self.verification_result,
                #list(items)[0]['verification']
            #)

            print(verification_result['tineye']['code'])
