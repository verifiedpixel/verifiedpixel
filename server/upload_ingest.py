#!/usr/bin/env python3
# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014, 2015 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

"""Ingest Uploader"""

from flask.ext.script import Manager
from app import get_app
from eve.utils import config
import ntpath
import imghdr
import sys
import os

from superdesk import get_resource_service
from superdesk.media.renditions import generate_renditions
from superdesk.upload import url_for_media

app = get_app()
manager = Manager(app)


def upload_fixture_image(fixture_image_path, headline='test'):
    with app.app_context():
        with open(fixture_image_path, mode='rb') as f:
            file_name = ntpath.basename(fixture_image_path)
            file_type = 'image'
            content_type = '%s/%s' % (file_type, imghdr.what(f))
            file_id = app.media.put(
                f, filename=file_name,
                content_type=content_type,
                resource=get_resource_service('ingest').datasource,
                metadata={}
            )
            inserted = [file_id]
            renditions = generate_renditions(
                f, file_id, inserted, file_type, content_type,
                rendition_config=config.RENDITIONS['picture'],
                url_for_media=url_for_media
            )
        data = [{
            'headline': headline,
            'slugline': headline,
            'renditions': renditions,
            'type': 'picture'
        }]
        image_id = get_resource_service('ingest').post(data)
    return image_id


if __name__ == '__main__':
    for image_path in sys.argv[1:]:
        upload_fixture_image(image_path, os.path.split(image_path)[-1])
