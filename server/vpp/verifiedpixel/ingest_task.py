from bson.objectid import ObjectId
from gridfs import GridFS
from flask import current_app as app
from eve.utils import ParsedRequest
from kombu.serialization import register
import dill
from celery import chord, group
import random

import superdesk
from superdesk.celery_app import celery
from vpp.tasks import send_to

from .logging import error, warning, info, success
from .elastic import handle_elastic_write_problems_wrapper
from .exceptions import APIGracefulException, ImageNotFoundException
from .vpp_mock import (
    activate_izitru_mock, activate_tineye_mock, activate_incandescent_mock
)
from .incandescent import (
    get_incandescent_results, get_incandescent_results_callback
)
from .tineye import get_tineye_results
from .izitru import get_izitru_results


# @TODO: for debug purpose
from pprint import pprint  # noqa
from .logging import debug, print_task_exception   # noqa


register('dill', dill.dumps, dill.loads, content_type='application/x-binary-data', content_encoding='binary')


def get_original_image(item, resource):
    if 'renditions' in item:
        driver = app.data.mongo
        px = driver.current_mongo_prefix(resource)
        _fs = GridFS(driver.pymongo(prefix=px).db)
        for k, v in item['renditions'].items():
            if k == 'original':
                _file = _fs.get(ObjectId(v['media']))
                content = _file.read()
                href = v['href']
                return (href, content)
    raise ImageNotFoundException()


API_GETTERS = {
    'izitru': {"function": get_izitru_results, "args": ("filename", "content",)},
    'tineye': {"function": get_tineye_results, "args": ("content",)},
    # 'incandescent': {"function": get_incandescent_results, "args": ("href",)},
}


MOCKS = {
    'izitru': {
        'function': activate_izitru_mock,
        'fixtures': [
            {"response_file": "test/vpp/mock_izitru_1.json"},
            {"response_file": "test/vpp/mock_izitru_2.json"},
            {"response_file": "test/vpp/mock_izitru_3.json"},
            {"response_file": "test/vpp/mock_izitru_4.json"},
            {"response_file": "test/vpp/mock_izitru_5.json"},
            {"response": {'status': 'error', 'message': 'something gone wrong'}}
        ]
    },
    'tineye': {
        'function': activate_tineye_mock,
        'fixtures': [
            {"response_file": "test/vpp/mock_tineye_many.json"},
            {"response_file": "test/vpp/mock_tineye_zero.json"},
            {"response": {'status': 'error', 'message': 'something gone wrong'}}
        ]
    },
    'incandescent': {
        'function': activate_incandescent_mock,
        'fixtures': [
            {"response_file": './test/vpp/incandescent_add_response.json'},
        ]
    },
    'incandescent_callback': {
        'function': activate_incandescent_mock,
        'fixtures': [
            {"response_file": './test/vpp/incandescent_result_response.json'},
            {"response_file": './test/vpp/incandescent_result_response_710.json'},
            {"response_file": './test/vpp/incandescent_result_response_755.json'}
        ]
    },
}


def get_api_getter(api_name, api_getter=None):
    if not api_getter:
        api_getter = API_GETTERS[api_name]['function']
    if app.config['USE_VERIFICATION_MOCK']:  # pragma no cover
        mock = MOCKS[api_name]
        api_wrapper = mock['function'](random.choice(mock['fixtures']), eternal=True)
        api_getter = api_wrapper(api_getter)
    return api_getter


def write_results(api_name, item_id, verification_id, verification_stats, verification_results, resource):
    handle_elastic_write_problems_wrapper(
        lambda: superdesk.get_resource_service(resource).patch(
            item_id,
            {'verification.stats.{api}'.format(api=api_name): verification_stats}
        )
    )
    if verification_results:
        # @TODO: write date
        handle_elastic_write_problems_wrapper(
            lambda: superdesk.get_resource_service('verification_results').patch(
                verification_id,
                {api_name: verification_results}
            )
        )


@celery.task(max_retries=3, bind=True, serializer='dill', name='vpp.append_api_result', ignore_result=False)
def append_api_results_to_item(self, item, api_name, args, verification_id, resource):
    filename = item.get('slugline', "(no headline)")
    info(
        "{api}: searching matches for {file}... ({tries} of {max})".format(
            api=api_name, file=filename, tries=self.request.retries, max=self.max_retries
        ))
    try:
        results_object = get_api_getter(api_name)(*args)
    except APIGracefulException as e:
        if self.request.retries < self.max_retries:
            warning("{api}: API exception raised during "
                    "verification of {file} (retrying):\n {exception}".format(
                        api=api_name, file=filename, exception=e))
            raise self.retry(
                exc=e, countdown=app.config['VERIFICATION_TASK_RETRY_INTERVAL'])
        else:
            error("{api}: max retries exceeded on "
                  "verification of {file}:\n {exception}".format(
                      api=api_name, file=filename, exception=e
                  ))
            verification_results = {"status": "error", "message": repr(e)}
            verification_stats = {"total": None}
    else:
        info("{api}: matchs found for {file}.".format(
            api=api_name, file=filename
        ))
        verification_results = results_object['results']
        verification_stats = results_object['stats']
    write_results(api_name,
                  item['_id'], verification_id,
                  verification_stats, verification_results,
                  resource=resource
                  )


@celery.task(max_retries=3, bind=True, serializer='dill', name='vpp.append_incandescent_result', ignore_result=False)
def append_incandescent_results_to_item(self, item, href):
    api_name = 'incandescent'
    filename = item.get('slugline', "(no headline)")
    info(
        "{api}: searching matches for {file}... ({tries} of {max})".format(
            api=api_name, file=filename, tries=self.request.retries, max=self.max_retries
        ))
    try:
        get_data = get_api_getter(api_name, get_incandescent_results)(href)
    except APIGracefulException as e:
        if self.request.retries < self.max_retries:
            warning("{api}: API exception raised during "
                    "verification of {file} (retrying):\n {exception}".format(
                        api=api_name, file=filename, exception=e))
            raise self.retry(exc=e, countdown=app.config['VERIFICATION_TASK_RETRY_INTERVAL'])
        else:
            error("{api}: max retries exceeded on "
                  "verification of {file}:\n {exception}".format(
                      api=api_name, file=filename, exception=e))
            verification_result = {"status": "error", "message": repr(e)}
            return verification_result
    else:
        info("{api}: waiting for matches for {file}.".format(
            api=api_name, file=filename))
        return get_data


@celery.task(
    max_retries=20, countdown=15, bind=True,
    name='vpp.append_incandescent_result_callback', ignore_result=False
)
def append_incandescent_results_to_item_callback(self, get_data, item_id, filename, verification_id, resource):
    api_name = 'incandescent'

    if 'status' in get_data:
        error("{api}: API exception raised on "
              "verification of {file}:\n {exception}".format(
                  api=api_name, file=filename, exception=get_data))
        verification_results = get_data
        verification_stats = {}
    else:
        try:
            results_object = get_api_getter(
                'incandescent_callback', get_incandescent_results_callback
            )(get_data)
            verification_stats = results_object['stats']
            verification_results = results_object['results']
        except APIGracefulException as e:
            if self.request.retries < self.max_retries:
                info("{api}: result is not ready for {file}, retrying... ({num} of {max})".format(
                    api=api_name, file=filename, num=self.request.retries, max=self.max_retries))
                raise self.retry(exc=e, countdown=self.countdown)
            else:
                error("{api}: timeout exceeded on "
                      "verification of {file}:\n {exception}".format(
                          api=api_name, file=filename, exception=e))
                verification_results = {"status": "error", "message": repr(e)}
                verification_stats = {}
        else:
            info("{api}: matchs found for {file}.".format(
                api=api_name, file=filename))
    # record result to database
    write_results(
        api_name,
        item_id, verification_id,
        verification_stats, verification_results,
        resource=resource
    )


@celery.task(bind=True, name='vpp.finalize_verification', ignore_result=False)
@print_task_exception
def finalize_verification(self, *args, item_id, desk_id, resource):
    if resource == 'ingest':
        handle_elastic_write_problems_wrapper(
            # Auto fetch items to the 'Verified Images' desk
            lambda: superdesk.get_resource_service('fetch').fetch(
                [{'_id': item_id, 'desk': desk_id}]
            )
        )
        handle_elastic_write_problems_wrapper(
            # Delete the ingest item
            lambda: superdesk.get_resource_service('ingest').delete(
                lookup={'_id': item_id}
            )
        )
    elif resource == 'archive':
        item = superdesk.get_resource_service('archive').find_one(
            req=ParsedRequest(), _id=item_id)
        send_to(item, desk_id=desk_id)
        superdesk.get_resource_service('archive').patch(
            item_id,
            {'task': item['task']}
        )

    success('Fetching item: {} into desk "Verified Images".'.format(item_id))


@celery.task(ignore_result=False, name='vpp.wait_for_results')
def wait_for_results(*args, **kwargs):
    return


def verify_items(items, resource, desk_id, verification_providers=None):
    for item in items:

        incandescent_enabled = True
        common_api_getters = API_GETTERS
        if verification_providers:
            incandescent_enabled = False
            if 'incandescent' in verification_providers:
                incandescent_enabled = True
                verification_providers.remove('incandescent')
            common_api_getters = {name: API_GETTERS[name] for name in verification_providers}

        verification_id = item.get('verification', {}).get('results', None)
        if not verification_id:
            verification_id = handle_elastic_write_problems_wrapper(
                lambda: superdesk.get_resource_service('verification_results').post([{}])
            )[0]
            handle_elastic_write_problems_wrapper(
                lambda: superdesk.get_resource_service(resource).patch(
                    item['_id'],
                    {'verification.results': verification_id}
                )
            )

        filename = item.get('slugline', "(no headline)")
        info(
            'found new item for verification: "{}"'.format(filename)
        )
        try:
            href, content = get_original_image(item, resource)
        except ImageNotFoundException:
            return
        all_args = {
            "filename": filename,
            "content": content,
            "href": href
        }

        common_tasks = (
            chord([
                append_api_results_to_item.subtask(
                    args=(
                        item, api_name,
                        [all_args[arg_name] for arg_name in data['args']]
                    ),
                    kwargs={
                        'verification_id': verification_id,
                        'resource': resource,
                    }
                )
                for api_name, data in common_api_getters.items()
            ],
                wait_for_results.subtask()
            )
        )
        if not incandescent_enabled:
            verification_tasks = common_tasks
        else:
            incandescent_tasks = (
                append_incandescent_results_to_item.subtask(
                    kwargs={
                        "item": item,
                        "href": all_args['href'],
                    }
                ) | append_incandescent_results_to_item_callback.subtask(
                    kwargs={
                        "filename": all_args['filename'],
                        "item_id": item['_id'],
                        'verification_id': verification_id,
                        'resource': resource,
                    }
                )
            )
            verification_tasks = group(common_tasks, incandescent_tasks)

        chord(
            verification_tasks,
            finalize_verification.subtask(
                kwargs={
                    "item_id": item['_id'],
                    "desk_id": desk_id,
                    "resource": resource,
                },
                immutable=True
            )
        ).delay()


@celery.task(bind=True, name='vpp.verify_ingest')
@print_task_exception
def verify_ingest(self):
    info(
        'Checking for new ingested images for verification...'
    )
    try:
        ingest_items = superdesk.get_resource_service('ingest').get_from_mongo(
            req=ParsedRequest(),
            lookup={
                'type': 'picture',
                'verification': {'$exists': False}
            }
        )
        archive_items = superdesk.get_resource_service('archive').get_from_mongo(
            req=ParsedRequest(),
            lookup={
                'type': 'picture',
                'verification': {'$exists': False}
            }
        )
        desk = superdesk.get_resource_service('desks').find_one(req=ParsedRequest(), name='Verified Images')
        desk_id = str(desk['_id'])
    except Exception as e:
        error("Raised from verify_ingest task, aborting:")
        error(e)
        raise(e)
    else:
        verify_items(ingest_items, 'ingest', desk_id)
        verify_items(archive_items, 'archive', desk_id)
