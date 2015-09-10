from unittest import TestCase
from eve.utils import ParsedRequest

import superdesk
from superdesk import get_resource_service
from apps.prepopulate.app_initialize import AppInitializeWithDataCommand

from .ingest_task import verify_ingest

from .vpp_mock import (
    activate_tineye_mock, activate_izitru_mock,
    activate_incandescent_mock
)
from .vpp_test import VPPTestCase, setup

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
        self.expected_verification_stats = []
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
            './test/vpp/test1_verification_stats.json',
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
                self.expected_verification_stats[0],
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
            './test/vpp/test2_verification_stats.json',
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
                self.expected_verification_stats[0],
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
    def test_happy_day_jpg_remove(self):
        self.upload_fixture_image(
            './test/vpp/test2.jpg',
            './test/vpp/test2_verification_stats.json',
            './test/vpp/test2_verification_result.json'
        )
        with self.app.app_context():
            verify_ingest()
            item = list(superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup={'type': 'picture'}
            ))[0]
            verification_result = item['verification']
            results_id = verification_result['results']
            self.assertVerificationResult(
                verification_result,
                self.expected_verification_stats[0],
                self.expected_verification_results[0]
            )

            results = list(superdesk.get_resource_service('verification_results').get(
                req=ParsedRequest(), lookup={'_id': results_id}
            ))
            self.assertEqual(len(results), 1)

            superdesk.get_resource_service('archive').delete_action(
                {'_id': item['_id']}
            )

            verification_result = list(superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup={'_id': item['_id']}
            ))
            self.assertEqual(len(verification_result), 0)

            results = list(superdesk.get_resource_service('verification_results').get(
                req=ParsedRequest(), lookup={'_id': results_id}
            ))
            self.assertEqual(len(results), 0)

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
