from unittest import TestCase

from .ingest_task import get_incandescent_results, get_incandescent_results_callback
from .exceptions import APIGracefulException

from .vpp_mock import activate_incandescent_mock
from .vpp_test import VPPTestCase, setup

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

    @activate_incandescent_mock(
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"status": 200, "response": {"status": 710, "foo": "bar"}}
    )
    def test_retry_failed_incandescent200_710(self):
        get_data = get_incandescent_results('image.jpg.to')
        with self.assertRaises(Exception):
            get_incandescent_results_callback(get_data)

    @activate_incandescent_mock(
        {"response_file": './test/vpp/incandescent_add_response.json'},
        {"status": 200, "response": {"code": 710, "foo": "bar"}}
    )
    def test_retry_failed_incandescent200_2(self):
        get_data = get_incandescent_results('image.jpg.to')
        with self.assertRaises(Exception):
            get_incandescent_results_callback(get_data)
