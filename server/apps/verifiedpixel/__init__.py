from superdesk import get_backend
from superdesk.celery_app import celery

from .ingest_task import init_tineye
from .ingest_task import verify_ingest_task
from .zip_resource import (
    VerifiedPixelZipService, VerifiedPixelZipResource
)


@celery.task
def verify_ingest(*args, **kwargs):
    return verify_ingest_task(*args, **kwargs)


def init_app(app):
    endpoint_name = 'verifiedpixel_zip'
    service = VerifiedPixelZipService(endpoint_name, backend=get_backend())
    VerifiedPixelZipResource(endpoint_name, app=app, service=service)
    init_tineye(app)
