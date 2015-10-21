from superdesk import get_backend

from .tineye import init_tineye
from .zip_resource import (
    VerifiedPixelZipService, VerifiedPixelZipResource
)
from .verification_results_resource import (
    VerificationResultsService, VerificationResultsResource
)
from .manual_verification_resource import (
    ManualVerificationService, ManualVerificationResource
)


def init_app(app):

    init_tineye(app)

    endpoint_name = 'verifiedpixel_zip'
    service = VerifiedPixelZipService(endpoint_name, backend=get_backend())
    VerifiedPixelZipResource(endpoint_name, app=app, service=service)

    endpoint_name = 'verification_results'
    service = VerificationResultsService(endpoint_name, backend=get_backend())
    VerificationResultsResource(endpoint_name, app=app, service=service)

    endpoint_name = 'manual_verification'
    service = ManualVerificationService(endpoint_name, backend=get_backend())
    ManualVerificationResource(endpoint_name, app=app, service=service)
