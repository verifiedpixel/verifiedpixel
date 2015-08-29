from unittest import TestCase
from superdesk.tests import setup

from .ingest_task import get_incandescent_results
from .exceptions import APIGracefulException

from .vpp_mock import activate_incandescent_mock
from .vpp_test import VPPTestCase

from pprint import pprint  # noqa @TODO: debug


class IncandescenTest(TestCase, VPPTestCase):

    @classmethod
    def setUpClass(cls):
        setup(context=cls)

    @activate_incandescent_mock({"status": 500, "response": {"foo": "bar"}, })
    def test_retry_failed_incandescent500(self):
        with self.assertRaises(APIGracefulException):
            get_incandescent_results('image.jpg.to')

    @activate_incandescent_mock({"status": 200, "response": {"foo": "bar"}, })
    def test_retry_failed_incandescent200(self):
        with self.assertRaises(APIGracefulException):
            get_incandescent_results('image.jpg.to')
