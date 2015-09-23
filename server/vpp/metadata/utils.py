# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from datetime import datetime
from uuid import uuid4
from flask import current_app as app
from .item import GUID_TAG, GUID_NEWSML, GUID_FIELD


item_url = 'regex("[\w,.:_-]+")'

extra_response_fields = [GUID_FIELD, 'headline', 'firstcreated', 'versioncreated', 'archived']

aggregations = {
    'type': {'terms': {'field': 'type'}},
    'desk': {'terms': {'field': 'task.desk'}},
    'stage': {'terms': {'field': 'task.stage'}},
    'category': {'terms': {'field': 'anpa_category.name'}},
    'source': {'terms': {'field': 'source'}},
    'state': {'terms': {'field': 'state'}},
    'urgency': {'terms': {'field': 'urgency'}},
    'day': {'date_range': {'field': 'firstcreated', 'format': 'dd-MM-yyy HH:mm:ss', 'ranges': [{'from': 'now-24H'}]}},
    'week': {'date_range': {'field': 'firstcreated', 'format': 'dd-MM-yyy HH:mm:ss', 'ranges': [{'from': 'now-1w'}]}},
    'month': {'date_range': {'field': 'firstcreated', 'format': 'dd-MM-yyy HH:mm:ss', 'ranges': [{'from': 'now-1M'}]}},
    'make': {'terms': {'field': 'filemeta.Make'}},
    'capture_location': {'terms': {'field': 'verification.stats.izitru.location'}},
    'izitru': {'terms': {'field': 'verification.stats.izitru.verdict'}},
    'original_source': {'terms': {'field': 'original_source'}},
    'vpp_tag': {'terms': {'field': 'vpp_tag'}},
}


def generate_guid(**hints):
    """
    Generate a GUID based on given hints
    param: hints: hints used for generating the guid
    """
    newsml_guid_format = 'urn:newsml:%(domain)s:%(timestamp)s:%(identifier)s'
    tag_guid_format = 'tag:%(domain)s:%(year)d:%(identifier)s'

    if not hints.get('id'):
        hints['id'] = str(uuid4())

    t = datetime.today()

    if hints['type'].lower() == GUID_TAG:
        return tag_guid_format % {'domain': app.config['SERVER_DOMAIN'], 'year': t.year, 'identifier': hints['id']}
    elif hints['type'].lower() == GUID_NEWSML:
        return newsml_guid_format % {'domain': app.config['SERVER_DOMAIN'],
                                     'timestamp': t.isoformat(),
                                     'identifier': hints['id']}
    return None
