from unittest import TestCase
from flask import current_app as app
from eve.utils import config, ParsedRequest
import json
import ntpath
import imghdr

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

    @classmethod
    def setUpClass(cls):
        """
        workaround for gridfs index problem,
        reuse the same app context for all the tests
        """
        setup(context=cls)

    def setUp(self):
        setup(context=self)

    def tearDown(self):
        pass

    def upload_fixture_image(
        self, fixture_image_path, verification_result_path
    ):
        with self.app.app_context():
            with open(fixture_image_path, mode='rb') as f:
                file_name = ntpath.basename(fixture_image_path)
                file_type = 'image'
                content_type = '%s/%s' % (file_type, imghdr.what(f))
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
        with open(verification_result_path, 'r') as f:
            self.verification_result = json.load(f)

    @activate_izitru_mock('./test/vpp/test1_izitru_response.json')
    @activate_tineye_mock('./test/vpp/test1_tineye_response.json')
    @activate_gris_mock([
        './test/vpp/gris_discovery_response.json',
        './test/vpp/test1_gris_search_response.json'
    ])
    def test_happy_day_image1(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
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

    @activate_izitru_mock('./test/vpp/test2_izitru_response.json')
    @activate_tineye_mock('./test/vpp/test2_tineye_response.json')
    @activate_gris_mock([
        './test/vpp/gris_discovery_response.json',
        './test/vpp/test2_gris_search_response.json'
    ])
    def test_happy_day_image2(self):
        self.upload_fixture_image(
            './test/vpp/test2.jpg',
            './test/vpp/test2_verification_result.json'
        )
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
