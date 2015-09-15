from unittest import TestCase, skip
from apps.prepopulate.app_initialize import AppInitializeWithDataCommand
from flask import current_app as app
from eve.utils import ParsedRequest
from io import BytesIO
import json
import zipfile

import superdesk
from superdesk import get_resource_service

from vpp.verifiedpixel.ingest_task import verify_ingest

from .vpp_mock import (
    activate_tineye_mock, activate_izitru_mock,
    activate_incandescent_mock
)
from .vpp_test import VPPTestCase, setup

from pprint import pprint  # noqa @TODO: debug


class VerifiedPixelZipResourceTest(TestCase, VPPTestCase):

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
        self.expected_verification_stats = []

    @skip
    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'},
        {"response_file": './test/vpp/test2_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'},
        {"response_file": './test/vpp/test2_tineye_response.json'}
    )
    @activate_incandescent_mock(
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"response_file": './test/vpp/incandescent_result_response.json'},
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"response_file": './test/vpp/incandescent_result_response.json'}
    )
    def test_zip_output(self):
        image_paths = [
            './test/vpp/test.png',
            './test/vpp/test2.jpg'
        ]
        self.upload_fixture_image(
            image_paths[0],
            './test/vpp/test1_verification_stats.json',
            './test/vpp/test1_verification_result.json',
            '0',
        )
        self.upload_fixture_image(
            image_paths[1],
            './test/vpp/test2_verification_stats.json',
            './test/vpp/test2_verification_result.json',
            '1',
        )
        with self.app.app_context():
            test_client = app.test_client()
            verify_ingest()
            lookup = {'type': 'picture',
                      'verification': {'$exists': True}}
            verified_items = list(superdesk.get_resource_service('archive').get_from_mongo(
                req=ParsedRequest(), lookup=lookup
            ))
            verified_items_ids = {int(item['headline']): item['_id']
                                  for item in verified_items}
            self.assertEqual(len(verified_items_ids), 2, "Items weren't verified.")

            vppzip_service = get_resource_service('verifiedpixel_zip')
            zipped_item_id = vppzip_service.post([
                {'items': list(verified_items_ids.values())}
            ])[0]
            zipped_item = list(vppzip_service.get_from_mongo(
                req=ParsedRequest(), lookup={"_id": zipped_item_id}
            ))[0]
            response = test_client.get(zipped_item['result'])
            zip_file = zipfile.ZipFile(BytesIO(response.get_data()))
            self.assertEqual(
                sorted(zip_file.namelist()),
                sorted(list(verified_items_ids.values()) + ['verification.json']),
                "Filelist in zip not match.")
            verification_dict = json.loads(
                zip_file.read('verification.json').decode()
            )
            for img_id, item_id in verified_items_ids.items():
                self.assertVerificationResult(
                    verification_dict[item_id],
                    self.expected_verification_stats[img_id],
                    self.expected_verification_results[img_id]
                )
                with open(image_paths[img_id], 'rb') as f:
                    self.assertEqual(
                        zip_file.read(item_id),
                        f.read(),
                        "Image in zip not match."
                    )

    @skip
    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'},
        {"response_file": './test/vpp/test2_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'},
        {"response_file": './test/vpp/test2_tineye_response.json'}
    )
    @activate_incandescent_mock(
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"response_file": './test/vpp/incandescent_result_response.json'},
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"response_file": './test/vpp/incandescent_result_response.json'}
    )
    def test_zip_output_delete(self):
        image_paths = [
            './test/vpp/test.png',
            './test/vpp/test2.jpg'
        ]
        self.upload_fixture_image(
            image_paths[0],
            './test/vpp/test1_verification_stats.json',
            './test/vpp/test1_verification_result.json',
            '0',
        )
        self.upload_fixture_image(
            image_paths[1],
            './test/vpp/test2_verification_stats.json',
            './test/vpp/test2_verification_result.json',
            '1',
        )
        with self.app.app_context():
            verify_ingest()
            lookup = {'type': 'picture',
                      'verification': {'$exists': True}}
            verified_items = list(superdesk.get_resource_service('archive').get_from_mongo(
                req=ParsedRequest(), lookup=lookup
            ))
            verified_items_ids = {int(item['headline']): item['_id']
                                  for item in verified_items}
            self.assertEqual(len(verified_items_ids), 2, "Items weren't verified.")

            vppzip_service = get_resource_service('verifiedpixel_zip')
            zipped_item_id = vppzip_service.post([
                {'items': list(verified_items_ids.values())}
            ])[0]
            zipped_item = list(vppzip_service.get_from_mongo(
                req=ParsedRequest(), lookup={"_id": zipped_item_id}
            ))[0]
            vppzip_service.delete_action({'_id': zipped_item_id})

            self.assertEqual(
                len(list(vppzip_service.get_from_mongo(
                    req=ParsedRequest(), lookup={"_id": zipped_item_id}
                ))),
                0
            )
            self.assertIsNone(
                self.app.media.get(
                    zipped_item['result_id'],
                    resource=vppzip_service.datasource,
                )
            )
