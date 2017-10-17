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
        fields = ('id', 'start', 'end', 'ground_station', 'transmitter',
                  'norad_cat_id', 'payload', 'waterfall', 'demoddata', 'station_name',
                  'station_lat', 'station_lng')
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
        return obj.ground_station.name

    def get_station_lat(self, obj):
        return obj.ground_station.lat

    def get_station_lng(self, obj):
        return obj.ground_station.lng


class JobSerializer(serializers.ModelSerializer):
    frequency = serializers.SerializerMethodField()
    tle0 = serializers.SerializerMethodField()
    tle1 = serializers.SerializerMethodField()
    tle2 = serializers.SerializerMethodField()
    mode = serializers.SerializerMethodField()
    transmitter = serializers.SerializerMethodField()

    class Meta:
        model = Observation
        fields = ('id', 'start', 'end', 'ground_station', 'tle0', 'tle1', 'tle2',
                  'frequency', 'mode', 'transmitter')

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
        except:
            return ''


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ('uuid', 'name', 'alt', 'lat', 'lng', 'rig',
                  'active', 'antenna', 'id', 'apikey', 'description')

    apikey = serializers.CharField(read_only=True)
