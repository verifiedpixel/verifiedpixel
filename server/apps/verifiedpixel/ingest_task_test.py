from unittest import TestCase
from apps.prepopulate.app_initialize import AppInitializeWithDataCommand
from eve.utils import ParsedRequest

import superdesk
from superdesk import get_resource_service
from superdesk.tests import setup

from apps.verifiedpixel import verify_ingest
from apps.verifiedpixel.ingest_task import APIGracefulException

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
        """
        @TODO: do we really need this test
        """
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            """
            @TODO: find a way to test it in a more sane way
            """
            with self.assertRaises(APIGracefulException):
                verify_ingest()
            with self.assertRaises(APIGracefulException):
                verify_ingest()
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
        {
            "status": 500,
            "response": {"foo": "bar"},
        }
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_failed_izitru500(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            with self.assertRaises(APIGracefulException):
                verify_ingest()

    @activate_izitru_mock(
        {
            "status": 200,
            "response": {"foo": "bar"},
        }
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_failed_izitru200(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            with self.assertRaises(APIGracefulException):
                verify_ingest()

    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'}
    )
    @activate_tineye_mock(
        {
            "status": 500,
            "response": {"foo": "bar"},
        }
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_failed_tineye500(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            with self.assertRaises(APIGracefulException):
                verify_ingest()

    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'}
    )
    @activate_tineye_mock(
        {
            "status": 404,
            "response": {"foo": "bar"},
        }
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_failed_tineye404(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            with self.assertRaises(APIGracefulException):
                verify_ingest()

    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'}
    )
    @activate_tineye_mock(
        {
            "status": 200,
            "response": {"foo": "bar"},
        }
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'}
    )
    def test_retry_failed_tineye200(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            with self.assertRaises(APIGracefulException):
                verify_ingest()

    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'}
    )
    @activate_gris_mock(
        {
            "status": 500,
            "response": {"foo": "bar"},
        }
    )
    def test_retry_failed_gris(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        with self.app.app_context():
            with self.assertRaises(APIGracefulException):
                verify_ingest()

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
