import json
import pytest

from django.test import TestCase

from rest_framework.utils.encoders import JSONEncoder

from network.base.tests import (
    ObservationFactory,
    SatelliteFactory,
    TransmitterFactory,
    StationFactory,
    AntennaFactory
)


@pytest.mark.django_db(transaction=True)
class JobViewApiTest(TestCase):
    """
    Tests the Job View API
    """
    observation = None
    satellites = []
    transmitters = []
    stations = []

    def setUp(self):
        for x in xrange(1, 10):
            self.satellites.append(SatelliteFactory())
        for x in xrange(1, 10):
            self.transmitters.append(TransmitterFactory())
        for x in xrange(1, 10):
            self.stations.append(StationFactory())
        self.observation = ObservationFactory()

    def test_job_view_api(self):
        response = self.client.get('/api/jobs/')
        response_json = json.loads(response.content)
        self.assertEqual(response_json, [])


@pytest.mark.django_db(transaction=True)
class SettingsViewApiTest(TestCase):
    """
    Tests the Job View API
    """
    station = None

    def setUp(self):
        self.station = StationFactory()
        self.station.uuid = 'test'
        self.station.save()

    def test_list(self):
        response = self.client.get('/api/settings/')
        self.assertEqual(response.status_code, 404)

    def test_retrieve(self):
        response = self.client.get('/api/settings/%s/' % self.station.uuid)
        self.assertContains(response, self.station.name)


@pytest.mark.django_db(transaction=True)
class StationViewApiTest(TestCase):
    """
    Tests the Station View API
    """
    station = None

    def setUp(self):
        self.antenna = AntennaFactory()
        self.encoder = JSONEncoder()
        self.station = StationFactory.create(antennas=[self.antenna])

    def test_station_view_api(self):

        ants = self.station.antenna.all()
        ser_ants = [" ".join([ant.band, ant.get_antenna_type_display()]) for ant in ants]

        station_serialized = {
            u'altitude': self.station.alt,
            u'antenna': ser_ants,
            u'created': self.encoder.default(self.station.created),
            u'description': self.station.description,
            u'id': self.station.id,
            u'last_seen': self.encoder.default(self.station.last_seen),
            u'lat': self.station.lat,
            u'lng': self.station.lng,
            u'location': self.station.location,
            u'min_horizon': self.station.horizon,
            u'name': self.station.name,
            u'observations': 0,
            u'qthlocator': self.station.qthlocator,
            u'status': self.station.get_status_display()}

        response = self.client.get('/api/stations/')
        response_json = json.loads(response.content)
        self.assertEqual(response_json, [station_serialized])
