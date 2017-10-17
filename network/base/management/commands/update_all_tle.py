from orbit import satellite

from django.core.management.base import BaseCommand

from network.base.models import Satellite, Tle


class Command(BaseCommand):
    help = 'Update TLEs for existing Satellites'

    def handle(self, *args, **options):

        satellites = Satellite.objects.exclude(manual_tle=True)

        self.stdout.write("==Fetching TLEs==")

        for obj in satellites:
            try:
                sat = satellite(obj.norad_cat_id)
            except:
                self.stdout.write(('{0} - {1}: TLE not found [error]')
                                  .format(obj.name, obj.norad_cat_id))
                continue

            obj.name = sat.name()
            obj.save()

            # Get latest satellite TLE and check if it changed
            tle = sat.tle()
            try:
                latest_tle = obj.latest_tle.tle1
            except:
                pass
            if latest_tle == tle[1]:
                self.stdout.write(('{0} - {1}: TLE already exists [defer]')
                                  .format(obj.name, obj.norad_cat_id))
                continue

            Tle.objects.create(tle0=tle[0], tle1=tle[1], tle2=tle[2], satellite=obj)
            self.stdout.write(('{0} - {1}: new TLE found [updated]')
                              .format(obj.name, obj.norad_cat_id))
