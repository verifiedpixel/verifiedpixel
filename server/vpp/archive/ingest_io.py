# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from superdesk.celery_app import update_key, set_key
from superdesk.resource import Resource
from superdesk.services import BaseService
from eve.defaults import resolve_default_values
from eve.methods.common import resolve_document_etag
from flask import current_app as app

from vpp.metadata.item import metadata_schema
from vpp.metadata.utils import extra_response_fields, item_url, aggregations


STATE_INGESTED = 'ingested'
SOURCE = 'ingest'


class IngestResource(Resource):
    schema = {
        'archived': {
            'type': 'datetime'
        }
    }
    schema.update(metadata_schema)
    extra_response_fields = extra_response_fields
    item_url = item_url
    datasource = {
        'search_backend': 'elastic',
        'aggregations': aggregations
    }


class IngestService(BaseService):

    def post_in_mongo(self, docs, **kwargs):
        for doc in docs:
            resolve_default_values(doc, app.config['DOMAIN'][self.datasource]['defaults'])
        self.on_create(docs)
        resolve_document_etag(docs, self.datasource)
        ids = self.backend.create_in_mongo(self.datasource, docs, **kwargs)
        self.on_created(docs)
        return ids

    def put_in_mongo(self, id, document):
        resolve_default_values(document, app.config['DOMAIN'][self.datasource]['defaults'])
        original = self.find_one(req=None, _id=id)
        self.on_replace(document, original)
        resolve_document_etag(document, self.datasource)
        res = self.backend.replace_in_mongo(self.datasource, id, document, original)
        self.on_replaced(document, original)
        return res

    def set_ingest_provider_sequence(self, item, provider):
        """
        Sets the value of ingest_provider_sequence in item.
        :param item: object to which ingest_provider_sequence to be set
        :param provider: ingest_provider object, used to build the key name of sequence
        """
        sequence_key_name = "{provider_type}_{provider_id}_ingest_seq".format(provider_type=provider.get('type'),
                                                                              provider_id=str(provider.get('_id')))
        sequence_number = update_key(sequence_key_name, flag=True)
        item['ingest_provider_sequence'] = str(sequence_number)

        if sequence_number == app.config['MAX_VALUE_OF_INGEST_SEQUENCE']:
            set_key(sequence_key_name)
