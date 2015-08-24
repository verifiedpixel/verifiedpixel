from unittest import TestCase
from eve.utils import ParsedRequest

import superdesk
from superdesk import get_resource_service
from superdesk.tests import setup
from apps.prepopulate.app_initialize import AppInitializeWithDataCommand

from .ingest_task import (
    verify_ingest,
    get_tineye_results, get_izitru_results,
    get_incandescent_results
)
from .exceptions import APIGracefulException

from .vpp_mock import (
    activate_tineye_mock, activate_izitru_mock,
    activate_incandescent_mock
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
    @activate_incandescent_mock(
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"response_file": './test/vpp/incandescent_result_response.json'}
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
            verification_result = list(items)[0]['verification']
            self.assertVerificationResult(
                verification_result,
                self.expected_verification_results[0]
            )

    @activate_izitru_mock(
        {"response_file": './test/vpp/test2_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test2_tineye_response.json'}
    )
    @activate_incandescent_mock(
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"response_file": './test/vpp/incandescent_result_response.json'}
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
            verification_result = list(items)[0]['verification']
            self.assertVerificationResult(
                verification_result,
                self.expected_verification_results[0]
            )

    # Izitru

    @activate_izitru_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_izitru500(self):
        with self.assertRaises(APIGracefulException):
            get_izitru_results(self.mock_item['slugline'], self.mock_image)

    @activate_izitru_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_izitru200(self):
        with self.assertRaises(APIGracefulException):
            get_izitru_results(self.mock_item['slugline'], self.mock_image)

    # TinEye

    @activate_tineye_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_tineye500(self):
        with self.assertRaises(APIGracefulException):
            get_tineye_results(self.mock_image)

    @activate_tineye_mock({"status": 404, "response": {"foo": "bar"}, })
    def test_retry_failed_tineye404(self):
        with self.assertRaises(APIGracefulException):
            get_tineye_results(self.mock_image)

    @activate_tineye_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_tineye200(self):
        with self.assertRaises(APIGracefulException):
            get_tineye_results(self.mock_image)

    @activate_tineye_mock({"status": 400,
                           "response": {"code": 400, "messages": ['foobar']}, })
    def test_retry_futile_tineye400(self):
        self.assertEqual(
            get_tineye_results(self.mock_image),
            {"status": "error", "message": "['foobar']"}
        )

    # Incandescent

    @activate_incandescent_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_incandescent500(self):
        with self.assertRaises(APIGracefulException):
            get_incandescent_results('image.jpg.to')

    @activate_incandescent_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_incandescent200(self):
        with self.assertRaises(APIGracefulException):
            get_incandescent_results('image.jpg.to')

    # misc

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
