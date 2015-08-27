from superdesk import get_backend

from .ingest_task import init_tineye
from .zip_resource import (
    VerifiedPixelZipService, VerifiedPixelZipResource
)
from .verification_results_resource import (
    VerificationResultsService, VerificationResultsResource
)


def init_app(app):
    endpoint_name = 'verifiedpixel_zip'
    service = VerifiedPixelZipService(endpoint_name, backend=get_backend())
    VerifiedPixelZipResource(endpoint_name, app=app, service=service)

    endpoint_name = 'verification_results'
    service = VerificationResultsService(endpoint_name, backend=get_backend())
    VerificationResultsResource(endpoint_name, app=app, service=service)

    init_tineye(app)
