import json
import pytest

from django.test import TestCase

from network.base.tests import (
    ObservationFactory,
    SatelliteFactory,
    TransmitterFactory,
    StationFactory
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
