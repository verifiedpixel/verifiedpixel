from superdesk import get_backend

from .ingest_task import init_tineye
from .ingest_task import verify_ingest  # noqa
from .zip_resource import (
    VerifiedPixelZipService, VerifiedPixelZipResource
)


def init_app(app):
    endpoint_name = 'verifiedpixel_zip'
    service = VerifiedPixelZipService(endpoint_name, backend=get_backend())
    VerifiedPixelZipResource(endpoint_name, app=app, service=service)
    init_tineye(app)
