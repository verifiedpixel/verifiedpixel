from time import sleep
from elasticsearch.exceptions import ConnectionTimeout as ElasticConnectionTimeout
from elasticsearch.exceptions import SerializationError as ElasticSerializationError
from elasticsearch.exceptions import ConflictError as ElasticConflictError
from elasticsearch.exceptions import TransportError as ElasticTransportError
from urllib3.exceptions import ProtocolError
from http.client import BadStatusLine

from .logging import warning
from .logging import debug  # noqa


def handle_elastic_timeout_wrapper(f):
    retry_interval = 0.5  # s
    max_retry = 60

    def retry(e):
        nonlocal retry_interval
        warning("Can't connect to elasticsearch, retrying in "
                "{interval} s: {exception}".format(
                    interval=retry_interval, exception=str(e.__class__).split("'")[1]))
        sleep(retry_interval)
        retry_interval *= 2
        if retry_interval > max_retry:
            raise(e)

    while True:
        try:
            return f()
        except (
            ElasticConnectionTimeout, ElasticSerializationError,
            ElasticTransportError
        ) as e:
            retry(e)
        except (ProtocolError, BadStatusLine) as e:
            retry(e)
            print(list(e.args))
        else:
            break


handle_elastic_read_problems_wrapper = handle_elastic_timeout_wrapper


def handle_elastic_write_problems_wrapper(f):
    while True:
        try:
            return handle_elastic_timeout_wrapper(f)
        except ElasticConflictError:
            warning("restarting transaction because of Elastic ConflictError")
            pass
        except Exception as e:
            if not e.__repr__().startswith('OriginalChangedError'):
                raise(e)
            else:
                warning("restarting transaction because of Eve OriginalChangedError")
        else:
            break
