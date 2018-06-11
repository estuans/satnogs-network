from rest_framework import serializers

from network.base.models import Observation, Station, DemodData


class DemodDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemodData
        fields = ('payload_demod', )


class ObservationSerializer(serializers.ModelSerializer):
    transmitter = serializers.SerializerMethodField()
    norad_cat_id = serializers.SerializerMethodField()
    station_name = serializers.SerializerMethodField()
    station_lat = serializers.SerializerMethodField()
    station_lng = serializers.SerializerMethodField()
    demoddata = DemodDataSerializer(many=True)

    class Meta:
        model = Observation
        fields = ('id', 'start', 'end', 'ground_station', 'transmitter', 'norad_cat_id',
                  'payload', 'waterfall', 'demoddata', 'station_name', 'station_lat',
                  'station_lng', 'vetted_status', 'client_version', 'client_metadata')
        read_only_fields = ['id', 'start', 'end', 'observation', 'ground_station',
                            'transmitter', 'norad_cat_id', 'station_name',
                            'station_lat', 'station_lng']

    def update(self, instance, validated_data):
        validated_data.pop('demoddata')
        super(ObservationSerializer, self).update(instance, validated_data)
        return instance

    def get_transmitter(self, obj):
        try:
            return obj.transmitter.uuid
        except AttributeError:
            return ''

    def get_norad_cat_id(self, obj):
        return obj.satellite.norad_cat_id

    def get_station_name(self, obj):
        try:
            return obj.ground_station.name
        except AttributeError:
            return None

    def get_station_lat(self, obj):
        try:
            return obj.ground_station.lat
        except AttributeError:
            return None

    def get_station_lng(self, obj):
        try:
            return obj.ground_station.lng
        except AttributeError:
            return None


class StationSerializer(serializers.ModelSerializer):
    antenna = serializers.SerializerMethodField()
    altitude = serializers.SerializerMethodField()
    min_horizon = serializers.SerializerMethodField()
    observations = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = ('id', 'name', 'altitude', 'min_horizon', 'lat', 'lng',
                  'qthlocator', 'location', 'antenna', 'created', 'last_seen',
                  'status', 'observations', 'description')

    def get_altitude(self, obj):
        return obj.alt

    def get_min_horizon(self, obj):
        return obj.horizon

    def get_antenna(self, obj):
        def antenna_name(antenna):
            return (antenna.band + " " + antenna.get_antenna_type_display())
        try:
            return [antenna_name(ant) for ant in obj.antenna.all()]
        except AttributeError:
            return None

    def get_observations(self, obj):
        try:
            return obj.observations_count
        except AttributeError:
            return None

    def get_status(self, obj):
        try:
            return obj.get_status_display()
        except AttributeError:
            return None


class JobSerializer(serializers.ModelSerializer):
    frequency = serializers.SerializerMethodField()
    tle0 = serializers.SerializerMethodField()
    tle1 = serializers.SerializerMethodField()
    tle2 = serializers.SerializerMethodField()
    mode = serializers.SerializerMethodField()
    transmitter = serializers.SerializerMethodField()
    baud = serializers.SerializerMethodField()

    class Meta:
        model = Observation
        fields = ('id', 'start', 'end', 'ground_station', 'tle0', 'tle1', 'tle2',
                  'frequency', 'mode', 'transmitter', 'baud')

    def get_frequency(self, obj):
        return obj.transmitter.downlink_low

    def get_transmitter(self, obj):
        return obj.transmitter.uuid

    def get_tle0(self, obj):
        return obj.tle.tle0

    def get_tle1(self, obj):
        return obj.tle.tle1

    def get_tle2(self, obj):
        return obj.tle.tle2

    def get_mode(self, obj):
        try:
            return obj.transmitter.mode.name
        except AttributeError:
            return ''

    def get_baud(self, obj):
        return obj.transmitter.baud


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ('uuid', 'name', 'alt', 'lat', 'lng', 'rig',
                  'testing', 'antenna', 'id', 'apikey', 'description')

    apikey = serializers.CharField(read_only=True)
