import hashlib
import time
from requests import request
from PIL import Image
from io import BytesIO
from flask import current_app

import superdesk

from .exceptions import APIGracefulException


# @TODO: for debug purpose
from pprint import pprint  # noqa
from .logging import debug  # noqa


def get_izitru_results(filename, content):
    with superdesk.app.app_context():
        config = current_app.config
    izitru_security_data = int(time.time())
    m = hashlib.md5()
    m.update(str(izitru_security_data).encode())
    m.update(config['IZITRU_PRIVATE_KEY'].encode())
    izitru_security_hash = m.hexdigest()

    upfile = content
    img = Image.open(BytesIO(content))
    if img.format != 'JPEG':
        exif = img.info.get('exif', b"")
        converted_image = BytesIO()
        img.save(converted_image, 'JPEG', exif=exif)
        upfile = converted_image.getvalue()
        converted_image.close()
    # img.close()

    data = {
        'activationKey': config['IZITRU_ACTIVATION_KEY'],
        'securityData': izitru_security_data,
        'securityHash': izitru_security_hash,
        'exactMatch': 'true',
        'nearMatch': 'false',
        'storeImage': 'true',
    }
    files = {'upFile': (filename, upfile, 'image/jpeg', {'Expires': '0'})}
    response = request('POST', config['IZITRU_API_URL'], data=data, files=files)
    if response.status_code != 200:
        raise APIGracefulException(response)
    result = response.json()
    if 'verdict' not in result or 'EXIF' not in result:
        raise APIGracefulException(result)
    return {
        'stats': {
            'verdict': result['verdict'],
            'location': result['EXIF']['captureLocation']
        },
        'results': result
    }
