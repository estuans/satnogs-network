import json
import urllib2

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from network.base.models import Mode, Satellite, Transmitter


class Command(BaseCommand):
    help = 'Provide DB API endpoint'

    def handle(self, *args, **options):
        apiurl = settings.DB_API_ENDPOINT
        modes_url = "{0}modes".format(apiurl)
        satellites_url = "{0}satellites".format(apiurl)
        transmitters_url = "{0}transmitters".format(apiurl)

        self.stdout.write("==Fetching from: {0}==".format(apiurl))
        try:
            modes = urllib2.urlopen(modes_url).read()
            satellites = urllib2.urlopen(satellites_url).read()
            transmitters = urllib2.urlopen(transmitters_url).read()
        except urllib2.URLError:
            raise CommandError('API is unreachable')

        # Fetch Modes
        for mode in json.loads(modes):
            id = mode['id']
            name = mode['name']
            try:
                existing_mode = Mode.objects.get(id=id)
                existing_mode.__dict__.update(mode)
                existing_mode.save()
                self.stdout.write('Mode {0} updated'.format(name))
            except Mode.DoesNotExist:
                Mode.objects.create(**mode)
                self.stdout.write('Mode {0} added'.format(name))

        # Fetch Satellites
        for satellite in json.loads(satellites):
            norad_cat_id = satellite['norad_cat_id']
            name = satellite['name']
            try:
                existing_satellite = Satellite.objects.get(norad_cat_id=norad_cat_id)
                existing_satellite.__dict__.update(satellite)
                existing_satellite.save()
                self.stdout.write('Satellite {0}-{1} updated'.format(norad_cat_id, name))
            except Satellite.DoesNotExist:
                Satellite.objects.create(**satellite)
                self.stdout.write('Satellite {0}-{1} added'.format(norad_cat_id, name))

        # Fetch Transmitters
        for transmitter in json.loads(transmitters):
            norad_cat_id = transmitter['norad_cat_id']
            uuid = transmitter['uuid']
            description = transmitter['description']
            mode_id = transmitter['mode_id']

            try:
                sat = Satellite.objects.get(norad_cat_id=norad_cat_id)
            except Satellite.DoesNotExist:
                self.stdout.write('Satellite {0} not present'.format(norad_cat_id))
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
                self.stdout.write('Transmitter {0}-{1} updated'.format(uuid, description))
            except Transmitter.DoesNotExist:
                new_transmitter = Transmitter.objects.create(**transmitter)
                new_transmitter.satellite = sat
                new_transmitter.mode = mode
                new_transmitter.save()
                self.stdout.write('Transmitter {0}-{1} created'.format(uuid, description))
