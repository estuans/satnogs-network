from optparse import make_option
from orbit import satellite

from django.core.management.base import BaseCommand, CommandError

from network.base.models import Satellite


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--delete',
                    action='store_true',
                    dest='delete',
                    default=False,
                    help='Delete Satellite'),
    )
    args = '<Satellite Identifiers>'
    help = 'Updates/Inserts TLEs for certain Satellites'

    def handle(self, *args, **options):
        for item in args:
            if options['delete']:
                try:
                    Satellite.objects.get(norad_cat_id=item).delete()
                    self.stdout.write('Satellite {}: deleted'.format(item))
                    continue
                except Satellite.DoesNotExist:
                    raise CommandError('Satellite with Identifier {} does not exist'.format(item))

            try:
                sat = satellite(item)
            except IndexError:
                raise CommandError('Satellite with Identifier {} does not exist'.format(item))

            try:
                obj = Satellite.objects.get(norad_cat_id=item)
            except Satellite.DoesNotExist:
                obj = Satellite(norad_cat_id=item)

            obj.name = sat.name()
            tle = sat.tle()
            obj.tle0 = tle[0]
            obj.tle1 = tle[1]
            obj.tle2 = tle[2]
            obj.save()

            self.stdout.write('fetched data for {}: {}'.format(obj.norad_cat_id, obj.name))
