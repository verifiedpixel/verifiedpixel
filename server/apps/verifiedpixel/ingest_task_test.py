from unittest import TestCase, skip
from apps.prepopulate.app_initialize import AppInitializeWithDataCommand
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
from .vpp_test import VPPTestCase

from pprint import pprint  # noqa @TODO: debug


class VerifiedPixelAppTest(TestCase, VPPTestCase):

    # maxDiff = None

    @classmethod
    def setUpClass(cls):
        """
        workaround for gridfs index problem,
        reuse the same app context for all the tests
        """
        setup(context=cls)

    @classmethod
    def tearDownClass(cls):
        """
        workaround for gridfs index problem,
        """
        cls.purge_index("archive")

    def setUp(self):
        setup(context=self)
        with self.app.app_context():
            AppInitializeWithDataCommand().run()
        self.expected_verification_results = []

    def upload_fixture_image(
        self, fixture_image_path, verification_result_path, headline='test'
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
                'headline': headline,
                'slugline': 'rebuild',
                'renditions': renditions,
                'type': 'picture'
            }]
            image_id = get_resource_service('ingest').post(data)
        with open(verification_result_path, 'r') as f:
            self.expected_verification_results.append(json.load(f))
        return image_id

    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_happy_day_png(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            verify_ingest()
            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertEqual(
                self.expected_verification_results[0],
                list(items)[0]['verification']
            )

    @activate_izitru_mock(
        {"response_file": './test/vpp/test2_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test2_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test2_gris_search_response.json'}
    )
    def test_happy_day_jpg(self):
        self.upload_fixture_image(
            './test/vpp/test2.jpg',
            './test/vpp/test2_verification_result.json'
        )
        with self.app.app_context():
            verify_ingest()
            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertEqual(
                self.expected_verification_results[0],
                list(items)[0]['verification']
            )

    @skip
    @activate_izitru_mock(
        {
            "status": 500,
            "response": {"foo": "bar"},
        }, {
            "status": 404,
            "response": {"foo": "bar"},
        },
        {"response_file": './test/vpp/test1_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_succeeded_izitru(self):
        self.fail("@TODO")

    @skip
    @activate_izitru_mock(
        {
            "status": 500,
            "response": {"foo": "bar"},
        }, {
            "status": 404,
            "response": {"foo": "bar"},
        }, {
            "status": 204,
            "response": {"foo": "bar"},
        },
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_failed_izitru(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            verify_ingest.apply_async(retry=True)
            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertNotIn(
                'izitru',
                list(items)[0]['verification']
            )
            self.assertEqual(
                self.expected_verification_results[0]['tineye'],
                list(items)[0]['verification']['tineye']
            )
            self.assertEqual(
                self.expected_verification_results[0]['gris'],
                list(items)[0]['verification']['gris']
            )
