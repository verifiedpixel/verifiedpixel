from unittest import TestCase
from superdesk.tests import setup

from .ingest_task import get_tineye_results
from .exceptions import APIGracefulException

from .vpp_mock import activate_tineye_mock
from .vpp_test import VPPTestCase

from pprint import pprint  # noqa @TODO: debug


class TinEyeTest(TestCase, VPPTestCase):

    @classmethod
    def setUpClass(cls):
        setup(context=cls)
        with open('./test/vpp/test2.jpg', 'rb') as f:
            cls.mock_image = f.read()

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
            {'results': {'message': "['foobar']", 'status': 'error'}, 'total': None}
        )
