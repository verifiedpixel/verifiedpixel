# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import superdesk
from superdesk.celery_app import celery
import logging

logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)

@celery.task
def verify_ingest():
    logger.info('VerifiedPixel: Checking for new ingested images for verification...')

    # TODO: lookup image items with no verification metadata
    lookup = {'type': 'picture'}
    items = superdesk.get_resource_service('ingest').get(req=None, lookup=lookup)
    for item in items:
        # TODO: make call to izitru
        # TODO: make call to google reverse image search 
        # TODO: make call to tineye
        logger.info('found {}'.format(item))
    else:
        logger.info('no ingest items found for {}'.format(lookup))
