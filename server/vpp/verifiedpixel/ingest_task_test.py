from unittest import TestCase
from eve.utils import ParsedRequest

import superdesk
from superdesk import get_resource_service
from superdesk.tests import setup
from apps.prepopulate.app_initialize import AppInitializeWithDataCommand

from vpp.verifiedpixel.ingest_task import (
    APIGracefulException, append_api_results_to_item,
    get_tineye_results, get_izitru_results, get_gris_results,
    verify_ingest
)

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
        with open('./test/vpp/test2.jpg', 'rb') as f:
            cls.mock_image = f.read()

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
        self.mock_item = {"slugline": "test"}

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
            verify_ingest.apply()
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

    @activate_izitru_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_izitru500(self):
        with self.assertRaises(APIGracefulException):
            append_api_results_to_item(
                self.mock_item, 'izitru', get_izitru_results,
                (self.mock_item['slugline'], self.mock_image))

    @activate_izitru_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_izitru200(self):
        with self.assertRaises(APIGracefulException):
            append_api_results_to_item(
                self.mock_item, 'izitru',
                get_izitru_results, (self.mock_item['slugline'], self.mock_image))

    @activate_tineye_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_tineye500(self):
        with self.assertRaises(APIGracefulException):
            append_api_results_to_item(
                self.mock_item, 'tineye',
                get_tineye_results, (self.mock_image, ))

    @activate_tineye_mock({"status": 404, "response": {"foo": "bar"}, })
    def test_retry_failed_tineye404(self):
        with self.assertRaises(APIGracefulException):
            append_api_results_to_item(
                self.mock_item, 'tineye',
                get_tineye_results, (self.mock_image, ))

    @activate_tineye_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_tineye200(self):
        with self.assertRaises(APIGracefulException):
            append_api_results_to_item(
                self.mock_item, 'tineye',
                get_tineye_results, (self.mock_image, ))

    @activate_gris_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_gris(self):
        with self.assertRaises(APIGracefulException):
            append_api_results_to_item(
                self.mock_item, 'gris',
                get_gris_results, ('image.jpg.to', ))

    def test_image_not_found(self):
        with self.app.app_context():
            data = [{
                'headline': 'wrong ingest item',
                'slugline': 'test',
                'type': 'picture'
            }]
            get_resource_service('ingest').post(data)

            verify_ingest()
            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertEqual(
                0,
                len(list(items))
            )
