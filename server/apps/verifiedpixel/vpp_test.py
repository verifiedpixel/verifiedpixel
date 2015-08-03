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

from pprint import pprint  # noqa @TODO: debug


class VerifiedPixelAppTest(TestCase):

    # maxDiff = None

    @classmethod
    def setUpClass(cls):
        """
        workaround for gridfs index problem,
        reuse the same app context for all the tests
        """
        setup(context=cls)

    def setUp(self):
        setup(context=self)
        with self.app.app_context():
            AppInitializeWithDataCommand().run()

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
                self.verification_result,
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
                self.verification_result,
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
            verify_ingest()
            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertNotIn(
                'izitru',
                list(items)[0]['verification']
            )
            self.assertEqual(
                self.verification_result['tineye'],
                list(items)[0]['verification']['tineye']
            )
            self.assertEqual(
                self.verification_result['gris'],
                list(items)[0]['verification']['gris']
            )

    @activate_izitru_mock(
        {"response_file": './test/vpp/test1_izitru_response.json'},
        {"response_file": './test/vpp/test2_izitru_response.json'}
    )
    @activate_tineye_mock(
        {"response_file": './test/vpp/test1_tineye_response.json'},
        {"response_file": './test/vpp/test2_tineye_response.json'}
    )
    @activate_gris_mock(
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test1_gris_search_response.json'},
        {"response_file": './test/vpp/gris_discovery_response.json'},
        {"response_file": './test/vpp/test2_gris_search_response.json'}
    )
    def test_zip_output(self):
        self.upload_fixture_image(
            './test/vpp/test.png',
            './test/vpp/test1_verification_result.json'
        )
        self.upload_fixture_image(
            './test/vpp/test2.jpg',
            './test/vpp/test2_verification_result.json'
        )
        with self.app.app_context():
            test_client = app.test_client()
            verify_ingest()
            lookup = {'type': 'picture'}
            items = superdesk.get_resource_service('archive').get(
                req=ParsedRequest(), lookup=lookup
            )
            self.assertEqual(len(list(items)), 2)
            item_ids = [item['_id'] for item in items]
            vppzip_service = get_resource_service('verifiedpixel_zip')
            zip_id = vppzip_service.post([{'items': item_ids}])[0]
            print(zip_id)
            zip_item = list(vppzip_service.get_from_mongo(
                req=ParsedRequest(), lookup={"_id": zip_id}
            ))[0]
            pprint(zip_item)
            response = test_client.get(zip_item['result'])
            # @TODO: finish the test
            with open('./test/vpp/output.zip', 'wb') as f:
                f.write(response.get_data())
