from elasticsearch.exceptions import ConnectionTimeout as ElasticConnectionTimeout
from elasticsearch.exceptions import SerializationError as ElasticSerializationError
from elasticsearch.exceptions import ConflictError as ElasticConflictError
from .logging import warning
from .logging import debug  # noqa


def handle_elastic_timeout_decorator(max_retries=3, retry_interval=30):
    retries_done = 0

    def wrap(f):
        def wrapped(self, *args, **kwargs):
            nonlocal retries_done
            try:
                return f(self, *args, **kwargs)
            except (ElasticConnectionTimeout, ElasticSerializationError) as e:
                warning("Can't connect to elasticsearch, retrying in "
                        "{interval}s:\n {exception}".format(
                            interval=retry_interval, exception=list(e.args)))
                retries_done += 1
                if retries_done < max_retries:
                    self.max_retries += 1
                    raise self.retry(exc=e, countdown=retry_interval)
                else:
                    raise(e)
        return wrapped
    return wrap


def handle_elastic_write_problems_wrapper(f):
    while True:
        try:
            return f()
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
