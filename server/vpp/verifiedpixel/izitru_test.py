from unittest import TestCase
from superdesk.tests import setup

from .ingest_task import (
    get_izitru_results,
)
from .exceptions import APIGracefulException

from .vpp_mock import activate_izitru_mock
from .vpp_test import VPPTestCase

from pprint import pprint  # noqa @TODO: debug


class IzitruTest(TestCase, VPPTestCase):

    @classmethod
    def setUpClass(cls):
        setup(context=cls)
        with open('./test/vpp/test2.jpg', 'rb') as f:
            cls.mock_image = f.read()
        cls.mock_item = {"slugline": "test"}

    @activate_izitru_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_izitru500(self):
        with self.assertRaises(APIGracefulException):
            get_izitru_results(self.mock_item['slugline'], self.mock_image)

    @activate_izitru_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_izitru200(self):
        with self.assertRaises(APIGracefulException):
            get_izitru_results(self.mock_item['slugline'], self.mock_image)
