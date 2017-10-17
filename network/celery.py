from __future__ import absolute_import

import os

from celery import Celery

import dotenv

dotenv.read_dotenv('.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'network.settings')

from django.conf import settings  # noqa

RUN_DAILY = 60 * 60 * 24
RUN_HOURLY = 60 * 60

app = Celery('network')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from network.base.tasks import update_all_tle, fetch_data, clean_observations

    sender.add_periodic_task(RUN_HOURLY, update_all_tle.s(),
                             name='update-all-tle')

    sender.add_periodic_task(RUN_HOURLY, fetch_data.s(),
                             name='fetch-data')

    sender.add_periodic_task(RUN_DAILY, clean_observations.s(),
                             name='clean-observations')


if settings.ENVIRONMENT == 'production' or settings.ENVIRONMENT == 'stage':
    from opbeat.contrib.django.models import client, logger, register_handlers
    from opbeat.contrib.celery import register_signal

    try:
        register_signal(client)
    except Exception as e:
        logger.exception('Failed installing celery hook: {0}'.format(e))

    register_handlers()
