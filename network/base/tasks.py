from datetime import timedelta
import json
import urllib2

from orbit import satellite

from django.conf import settings
from django.utils.timezone import now

from network.base.models import Satellite, Tle, Mode, Transmitter, Observation
from network.celery import app


@app.task
def update_all_tle():
    """Task to update all satellite TLEs"""
    satellites = Satellite.objects.exclude(manual_tle=True)

    for obj in satellites:
        try:
            sat = satellite(obj.norad_cat_id)
        except:
            continue

        # Get latest satellite TLE and check if it changed
        tle = sat.tle()
        try:
            latest_tle = obj.latest_tle.tle1
        except:
            pass
        if latest_tle == tle[1]:
            continue

        Tle.objects.create(tle0=tle[0], tle1=tle[1], tle2=tle[2], satellite=obj)


@app.task
def fetch_data():
    """Task to fetch all data from DB"""
    apiurl = settings.DB_API_ENDPOINT
    modes_url = "{0}modes".format(apiurl)
    satellites_url = "{0}satellites".format(apiurl)
    transmitters_url = "{0}transmitters".format(apiurl)

    try:
        modes = urllib2.urlopen(modes_url).read()
        satellites = urllib2.urlopen(satellites_url).read()
        transmitters = urllib2.urlopen(transmitters_url).read()
    except:
        raise Exception('API is unreachable')

    # Fetch Modes
    for mode in json.loads(modes):
        id = mode['id']
        try:
            existing_mode = Mode.objects.get(id=id)
            existing_mode.__dict__.update(mode)
            existing_mode.save()
        except Mode.DoesNotExist:
            Mode.objects.create(**mode)

    # Fetch Satellites
    for sat in json.loads(satellites):
        norad_cat_id = sat['norad_cat_id']
        try:
            existing_satellite = Satellite.objects.get(norad_cat_id=norad_cat_id)
            existing_satellite.__dict__.update(sat)
            existing_satellite.save()
        except Satellite.DoesNotExist:
            Satellite.objects.create(**sat)

    # Fetch Transmitters
    for transmitter in json.loads(transmitters):
        norad_cat_id = transmitter['norad_cat_id']
        uuid = transmitter['uuid']
        mode_id = transmitter['mode_id']

        try:
            sat = Satellite.objects.get(norad_cat_id=norad_cat_id)
        except Satellite.DoesNotExist:
            continue
        transmitter.pop('norad_cat_id')

        try:
            mode = Mode.objects.get(id=mode_id)
        except Mode.DoesNotExist:
            mode = None
        try:
            existing_transmitter = Transmitter.objects.get(uuid=uuid)
            existing_transmitter.__dict__.update(transmitter)
            existing_transmitter.satellite = sat
            existing_transmitter.save()
        except Transmitter.DoesNotExist:
            new_transmitter = Transmitter.objects.create(**transmitter)
            new_transmitter.satellite = sat
            new_transmitter.mode = mode
            new_transmitter.save()


@app.task
def clean_observations():
    """Task to clean up old observations that lack actual data."""
    if settings.ENVIRONMENT == 'stage':
        threshold = now() - timedelta(days=int(settings.OBSERVATION_OLD_RANGE))
        observations = Observation.objects.filter(end__lt=threshold)
        for obs in observations:
            if not obs.is_verified():
                obs.delete()
