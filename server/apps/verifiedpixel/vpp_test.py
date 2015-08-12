from flask import current_app as app
from eve.utils import config
import json
import ntpath
import imghdr

from superdesk import get_resource_service
from superdesk.media.renditions import generate_renditions
from superdesk.upload import url_for_media


class VPPTestCase:

    def upload_fixture_image(
        self, fixture_image_path, verification_result_path, headline='test'
    ):
        with self.app.app_context():
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
                'slugline': 'rebuild',
                'renditions': renditions,
                'type': 'picture'
            }]
            image_id = get_resource_service('ingest').post(data)
        with open(verification_result_path, 'r') as f:
            self.expected_verification_results.append(json.load(f))
        return image_id

    @classmethod
    def purge_index(cls, resource_name):
        """
        workaround for gridfs index problem,
        """
        with cls.app.app_context():
            connection = cls.app.data.mongo.pymongo(
                resource=resource_name
            ).cx
            connection._purge_index(
                cls.app.config['MONGO_DBNAME']
            )
