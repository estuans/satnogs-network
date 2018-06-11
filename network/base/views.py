import urllib2
import ephem
import math
from operator import itemgetter
from datetime import datetime, timedelta

from django.db.models import Count
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import now, make_aware, utc
from django.utils.text import slugify
from django.views.generic import ListView

from rest_framework import serializers, viewsets
from network.base.models import (Station, Transmitter, Observation,
                                 Satellite, Antenna, Tle, Rig, StationStatusLog)
from network.users.models import User
from network.base.forms import StationForm, SatelliteFilterForm
from network.base.decorators import admin_required, ajax_required
from network.base.helpers import calculate_polar_data, resolve_overlaps
from network.base.perms import schedule_perms, delete_perms, vet_perms
from network.base.tasks import update_all_tle, fetch_data


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ('name', 'lat', 'lng', 'id')


class StationAllView(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.exclude(status=0)
    serializer_class = StationSerializer


@ajax_required
def satellite_position(request, sat_id):
    sat = get_object_or_404(Satellite, norad_cat_id=sat_id)
    try:
        satellite = ephem.readtle(
            str(sat.latest_tle.tle0),
            str(sat.latest_tle.tle1),
            str(sat.latest_tle.tle2)
        )
    except (ValueError, AttributeError):
        data = {}
    else:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        satellite.compute(now)
        data = {
            'lon': '{0}'.format(satellite.sublong),
            'lat': '{0}'.format(satellite.sublat)
        }
    return JsonResponse(data, safe=False)


def index(request):
    """View to render index page."""
    if request.user.is_authenticated():
        return redirect(reverse('users:view_user', kwargs={"username": request.user.username}))

    return render(request, 'base/home.html', {'mapbox_id': settings.MAPBOX_MAP_ID,
                                              'mapbox_token': settings.MAPBOX_TOKEN})


def custom_404(request):
    """Custom 404 error handler."""
    return HttpResponseNotFound(render(request, '404.html'))


def custom_500(request):
    """Custom 500 error handler."""
    return HttpResponseServerError(render(request, '500.html'))


def robots(request):
    data = render(request, 'robots.txt', {'environment': settings.ENVIRONMENT})
    response = HttpResponse(data,
                            content_type='text/plain; charset=utf-8')
    return response


@admin_required
def settings_site(request):
    """View to render settings page."""
    if request.method == 'POST':
        fetch_data.delay()
        update_all_tle.delay()
        messages.success(request, 'Data fetching task was triggered successfully!')
        return redirect(reverse('users:view_user', kwargs={"username": request.user.username}))
    return render(request, 'base/settings_site.html')


class ObservationListView(ListView):
    """
    Displays a list of observations with pagination
    """
    model = Observation
    context_object_name = "observations"
    paginate_by = settings.ITEMS_PER_PAGE
    template_name = 'base/observations.html'

    def get_queryset(self):
        """
        Optionally filter based on norad get argument
        Optionally filter based on future/good/bad/unvetted/failed
        """
        norad_cat_id = self.request.GET.get('norad', '')
        observer = self.request.GET.get('observer', '')
        station = self.request.GET.get('station', '')
        self.filtered = False

        bad = self.request.GET.get('bad', '1')
        if bad == '0':
            bad = False
        else:
            bad = True
        good = self.request.GET.get('good', '1')
        if good == '0':
            good = False
        else:
            good = True
        unvetted = self.request.GET.get('unvetted', '1')
        if unvetted == '0':
            unvetted = False
        else:
            unvetted = True
        future = self.request.GET.get('future', '1')
        if future == '0':
            future = False
        else:
            future = True
        failed = self.request.GET.get('failed', '1')
        if failed == '0':
            failed = False
        else:
            failed = True

        if False in (bad, good, unvetted, future, failed):
            self.filtered = True

        observations = Observation.objects.all()
        if not norad_cat_id == '':
            observations = observations.filter(
                satellite__norad_cat_id=norad_cat_id)
            self.filtered = True
        if not observer == '':
            observations = observations.filter(
                author=observer)
            self.filtered = True
        if not station == '':
            observations = observations.filter(
                ground_station_id=station)
            self.filtered = True

        if not bad:
            observations = observations.exclude(vetted_status='bad')
        if not good:
            observations = observations.exclude(vetted_status='good')
        if not failed:
            observations = observations.exclude(vetted_status='failed')
        if not unvetted:
            observations = observations.exclude(vetted_status='unknown',
                                                id__in=(o.id for
                                                        o in observations if o.is_past))
        if not future:
            observations = observations.exclude(id__in=(o.id for
                                                        o in observations if o.is_future))
        return observations

    def get_context_data(self, **kwargs):
        """
        Need to add a list of satellites to the context for the template
        """
        context = super(ObservationListView, self).get_context_data(**kwargs)
        context['satellites'] = Satellite.objects.all()
        context['authors'] = User.objects.all().order_by('first_name', 'last_name', 'username')
        context['stations'] = Station.objects.all().order_by('id')
        norad_cat_id = self.request.GET.get('norad', None)
        observer = self.request.GET.get('observer', None)
        station = self.request.GET.get('station', None)
        context['future'] = self.request.GET.get('future', '1')
        context['bad'] = self.request.GET.get('bad', '1')
        context['good'] = self.request.GET.get('good', '1')
        context['unvetted'] = self.request.GET.get('unvetted', '1')
        context['failed'] = self.request.GET.get('failed', '1')
        context['filtered'] = self.filtered
        if norad_cat_id is not None and norad_cat_id != '':
            context['norad'] = int(norad_cat_id)
        if observer is not None and observer != '':
            context['observer_id'] = int(observer)
        if station is not None and station != '':
            context['station_id'] = int(station)
        if 'scheduled' in self.request.session:
            context['scheduled'] = self.request.session['scheduled']
            try:
                del self.request.session['scheduled']
            except KeyError:
                pass
        context['can_schedule'] = schedule_perms(self.request.user)
        return context


@login_required
def observation_new(request):
    """View for new observation"""
    me = request.user

    can_schedule = schedule_perms(me)
    if not can_schedule:
        messages.error(request, 'You don\'t have permissions to schedule observations')
        return redirect(reverse('base:observations_list'))

    if request.method == 'POST':
        sat_id = request.POST.get('satellite')
        trans_id = request.POST.get('transmitter')
        try:
            start_time = datetime.strptime(request.POST.get('start-time'), '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(request.POST.get('end-time'), '%Y-%m-%d %H:%M')
        except ValueError:
            messages.error(request, 'Please use the datetime dialogs to submit valid values.')
            return redirect(reverse('base:observation_new'))

        if (end_time - start_time) > timedelta(minutes=settings.OBSERVATION_DATE_MAX_RANGE):
            messages.error(request, 'Please use the datetime dialogs to submit valid timeframe.')
            return redirect(reverse('base:observation_new'))

        if (start_time < datetime.now()):
            messages.error(request, 'Please schedule an observation that begins in the future')
            return redirect(reverse('base:observation_new'))

        start = make_aware(start_time, utc)
        end = make_aware(end_time, utc)
        sat = Satellite.objects.get(norad_cat_id=sat_id)
        trans = Transmitter.objects.get(uuid=trans_id)
        tle = Tle.objects.get(id=sat.latest_tle.id)

        sat_ephem = ephem.readtle(str(sat.latest_tle.tle0),
                                  str(sat.latest_tle.tle1),
                                  str(sat.latest_tle.tle2))
        observer = ephem.Observer()
        observer.date = str(start)

        total = int(request.POST.get('total'))

        scheduled = []

        for item in range(total):
            start = datetime.strptime(
                request.POST.get('{0}-starting_time'.format(item)), '%Y-%m-%d %H:%M:%S.%f'
            )
            end = datetime.strptime(
                request.POST.get('{}-ending_time'.format(item)), '%Y-%m-%d %H:%M:%S.%f'
            )
            station_id = request.POST.get('{}-station'.format(item))
            ground_station = Station.objects.get(id=station_id)
            observer.lon = str(ground_station.lng)
            observer.lat = str(ground_station.lat)
            observer.elevation = ground_station.alt
            tr, azr, tt, altt, ts, azs = observer.next_pass(sat_ephem)

            obs = Observation(satellite=sat, transmitter=trans, tle=tle, author=me,
                              start=make_aware(start, utc), end=make_aware(end, utc),
                              ground_station=ground_station,
                              rise_azimuth=format(math.degrees(azr), '.0f'),
                              max_altitude=format(math.degrees(altt), '.0f'),
                              set_azimuth=format(math.degrees(azs), '.0f'))
            obs.save()
            scheduled.append(obs.id)
            time_start_new = ephem.Date(ts).datetime() + timedelta(minutes=1)
            observer.date = time_start_new.strftime("%Y-%m-%d %H:%M:%S.%f")

        try:
            del request.session['scheduled']
        except KeyError:
            pass
        request.session['scheduled'] = scheduled

        # If it's a single observation redirect to that one
        if total == 1:
            messages.success(request, 'Observation was scheduled successfully.')
            return redirect(reverse('base:observation_view', kwargs={'id': scheduled[0]}))

        messages.success(request, 'Observations were scheduled successfully.')
        return redirect(reverse('base:observations_list'))

    satellites = Satellite.objects.filter(transmitters__alive=True) \
        .filter(status='alive').distinct()
    transmitters = Transmitter.objects.filter(alive=True)

    obs_filter = {}
    if request.method == 'GET':
        filter_form = SatelliteFilterForm(request.GET)
        if filter_form.is_valid():
            start_date = filter_form.cleaned_data['start_date']
            end_date = filter_form.cleaned_data['end_date']
            ground_station = filter_form.cleaned_data['ground_station']
            norad = filter_form.cleaned_data['norad']

            if start_date:
                start_date = datetime.strptime(start_date,
                                               '%Y/%m/%d %H:%M').strftime('%Y-%m-%d %H:%M')
            if end_date:
                end_date = (datetime.strptime(end_date, '%Y/%m/%d %H:%M') +
                            timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')
            obs_filter['exists'] = True
            obs_filter['norad'] = norad
            obs_filter['start_date'] = start_date
            obs_filter['end_date'] = end_date
            if ground_station:
                obs_filter['ground_station'] = ground_station
        else:
            obs_filter['exists'] = False

    return render(request, 'base/observation_new.html',
                  {'satellites': satellites,
                   'transmitters': transmitters, 'obs_filter': obs_filter,
                   'date_min_start': settings.OBSERVATION_DATE_MIN_START,
                   'date_min_end': settings.OBSERVATION_DATE_MIN_END,
                   'date_max_range': settings.OBSERVATION_DATE_MAX_RANGE})


@ajax_required
def prediction_windows(request, sat_id, transmitter, start_date, end_date,
                       station_id=None):
    try:
        sat = Satellite.objects.filter(transmitters__alive=True) \
            .filter(status='alive').distinct().get(norad_cat_id=sat_id)
    except Satellite.DoesNotExist:
        data = {
            'error': 'You should select a Satellite first.'
        }
        return JsonResponse(data, safe=False)

    try:
        satellite = ephem.readtle(
            str(sat.latest_tle.tle0),
            str(sat.latest_tle.tle1),
            str(sat.latest_tle.tle2)
        )
    except (ValueError, AttributeError):
        data = {
            'error': 'No TLEs for this satellite yet.'
        }
        return JsonResponse(data, safe=False)

    try:
        downlink = Transmitter.objects.get(uuid=transmitter).downlink_low
    except Transmitter.DoesNotExist:
        data = {
            'error': 'You should select a Transmitter first.'
        }
        return JsonResponse(data, safe=False)

    end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M')

    data = []

    stations = Station.objects.all()
    if station_id:
        stations = stations.filter(id=station_id)
    for station in stations:
        if not schedule_perms(request.user, station):
            continue

        # Skip if this station is not capable of receiving the frequency
        if not downlink:
            continue
        frequency_supported = False
        for gs_antenna in station.antenna.all():
            if (gs_antenna.frequency <= downlink <= gs_antenna.frequency_max):
                frequency_supported = True
        if not frequency_supported:
            continue

        observer = ephem.Observer()
        observer.lon = str(station.lng)
        observer.lat = str(station.lat)
        observer.elevation = station.alt
        observer.date = str(start_date)
        station_match = False
        keep_digging = True
        while keep_digging:
            try:
                tr, azr, tt, altt, ts, azs = observer.next_pass(satellite)
            except ValueError:
                data = {
                    'error': 'That satellite seems to stay always below your horizon.'
                }
                break

            # no match if the sat will not rise above the configured min horizon
            elevation = format(math.degrees(altt), '.0f')
            if float(elevation) >= station.horizon:
                if ephem.Date(tr).datetime() < end_date:
                    if ephem.Date(ts).datetime() > end_date:
                        ts = end_date
                        keep_digging = False
                    else:
                        time_start_new = ephem.Date(ts).datetime() + timedelta(minutes=1)
                        observer.date = time_start_new.strftime("%Y-%m-%d %H:%M:%S.%f")

                    # Adjust or discard window if overlaps exist
                    window_start = make_aware(ephem.Date(tr).datetime(), utc)
                    window_end = make_aware(ephem.Date(ts).datetime(), utc)

                    # Check if overlaps with existing scheduled observations
                    gs_data = Observation.objects.filter(ground_station=station)
                    window = resolve_overlaps(station, gs_data, window_start, window_end)

                    if window:
                        if not station_match:
                            station_windows = {
                                'id': station.id,
                                'name': station.name,
                                'window': []
                            }
                            station_match = True
                        window_start = window[0]
                        window_end = window[1]
                        station_windows['window'].append(
                            {
                                'start': window_start.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                'end': window_end.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                'az_start': azr
                            })
                        # In case our window was split in two
                        try:
                            window_start = window[2]
                            window_end = window[3]
                            station_windows['window'].append(
                                {
                                    'start': window_start.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                    'end': window_end.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                    'az_start': azr
                                })
                        except IndexError:
                            pass
                else:
                    # window start outside of window bounds
                    break
            else:
                # did not rise above user configured horizon
                break

        if station_match:
            data.append(station_windows)

    return JsonResponse(data, safe=False)


def observation_view(request, id):
    """View for single observation page."""
    observation = get_object_or_404(Observation, id=id)

    can_vet = vet_perms(request.user, observation)

    can_delete = delete_perms(request.user, observation)

    if settings.ENVIRONMENT == 'production':
        discuss_slug = 'https://community.libre.space/t/observation-{0}-{1}-{2}' \
            .format(observation.id, slugify(observation.satellite.name),
                    observation.satellite.norad_cat_id)
        discuss_url = ('https://community.libre.space/new-topic?title=Observation {0}: {1}'
                       ' ({2})&body=Regarding [Observation {3}](http://{4}{5}) ...'
                       '&category=observations') \
            .format(observation.id, observation.satellite.name,
                    observation.satellite.norad_cat_id, observation.id,
                    request.get_host(), request.path)
        has_comments = True
        apiurl = '{0}.json'.format(discuss_slug)
        try:
            urllib2.urlopen(apiurl).read()
        except urllib2.URLError:
            has_comments = False

        return render(request, 'base/observation_view.html',
                      {'observation': observation, 'has_comments': has_comments,
                       'discuss_url': discuss_url, 'discuss_slug': discuss_slug,
                       'can_vet': can_vet, 'can_delete': can_delete})

    return render(request, 'base/observation_view.html',
                  {'observation': observation, 'can_vet': can_vet,
                   'can_delete': can_delete})


@login_required
def observation_delete(request, id):
    """View for deleting observation."""
    observation = get_object_or_404(Observation, id=id)
    can_delete = delete_perms(request.user, observation)
    if can_delete:
        observation.delete()
        messages.success(request, 'Observation deleted successfully.')
    else:
        messages.error(request, 'Permission denied.')
    return redirect(reverse('base:observations_list'))


@login_required
def observation_vet(request, id, status):
    observation = get_object_or_404(Observation, id=id)
    can_vet = vet_perms(request.user, observation)
    if status in ['good', 'bad', 'failed', 'unknown'] and can_vet:
        observation.vetted_status = status
        observation.vetted_user = request.user
        observation.vetted_datetime = now()
        observation.save(update_fields=['vetted_status', 'vetted_user', 'vetted_datetime'])
        if not status == 'unknown':
            messages.success(request, 'Observation vetted successfully. [<a href="{0}">Undo</a>]'
                             .format(reverse('base:observation_vet',
                                             kwargs={'id': observation.id, 'status': 'unknown'})))
    else:
        messages.error(request, 'Permission denied.')
    return redirect(reverse('base:observation_view', kwargs={'id': observation.id}))


def stations_list(request):
    """View to render Stations page."""
    stations = Station.objects.annotate(total_obs=Count('observations'))
    form = StationForm()
    antennas = Antenna.objects.all()
    online = stations.filter(status=2).count()
    testing = stations.filter(status=1).count()

    return render(request, 'base/stations.html',
                  {'stations': stations, 'form': form, 'antennas': antennas,
                   'online': online, 'testing': testing,
                   'mapbox_id': settings.MAPBOX_MAP_ID, 'mapbox_token': settings.MAPBOX_TOKEN})


def station_view(request, id):
    """View for single station page."""
    station = get_object_or_404(Station, id=id)
    form = StationForm(instance=station)
    antennas = Antenna.objects.all()
    rigs = Rig.objects.all()
    unsupported_frequencies = request.GET.get('unsupported_frequencies', '0')

    can_schedule = schedule_perms(request.user, station)

    # Calculate uptime
    uptime = '-'
    try:
        latest = StationStatusLog.objects.filter(station=station)[0]
    except IndexError:
        latest = None
    if latest:
        if latest.status:
            try:
                offline = StationStatusLog.objects.filter(station=station, status=0)[0]
                uptime = latest.changed - offline.changed
            except IndexError:
                uptime = now() - latest.changed
            uptime = str(uptime).split('.')[0]

    if request.user.is_authenticated():
        if request.user == station.owner:
            wiki_help = ('<a href="{0}" target="_blank" class="wiki-help"><span class="glyphicon '
                         'glyphicon-question-sign" aria-hidden="true"></span>'
                         '</a>'.format(settings.WIKI_STATION_URL))
            if station.is_offline:
                messages.error(request, ('Your Station is offline. You should make '
                                         'sure it can successfully connect to the Network API. '
                                         '{0}'.format(wiki_help)))
            if station.is_testing:
                messages.warning(request, ('Your Station is in Testing mode. Once you are sure '
                                           'it returns good observations you can put it online. '
                                           '{0}'.format(wiki_help)))

    return render(request, 'base/station_view.html',
                  {'station': station, 'form': form, 'antennas': antennas,
                   'mapbox_id': settings.MAPBOX_MAP_ID,
                   'mapbox_token': settings.MAPBOX_TOKEN,
                   'rigs': rigs, 'can_schedule': can_schedule,
                   'unsupported_frequencies': unsupported_frequencies,
                   'uptime': uptime})


def station_log(request, id):
    """View for single station status log."""
    station = get_object_or_404(Station, id=id)
    station_log = StationStatusLog.objects.filter(station=station)

    return render(request, 'base/station_log.html',
                  {'station': station, 'station_log': station_log})


@ajax_required
def pass_predictions(request, id):
    """Endpoint for pass predictions"""
    station = get_object_or_404(Station, id=id)
    unsupported_frequencies = request.GET.get('unsupported_frequencies', '0')

    try:
        satellites = Satellite.objects.filter(transmitters__alive=True) \
            .filter(status='alive').distinct()
    except Satellite.DoesNotExist:
        pass  # we won't have any next passes to display

    # Load the station information and invoke ephem so we can
    # calculate upcoming passes for the station
    observer = ephem.Observer()
    observer.lon = str(station.lng)
    observer.lat = str(station.lat)
    observer.elevation = station.alt

    nextpasses = []
    passid = 0

    for satellite in satellites:
        # look for a match between transmitters from the satellite and
        # ground station antenna frequency capabilities
        if int(unsupported_frequencies) == 0:
            frequency_supported = False
            transmitters = Transmitter.objects.filter(satellite=satellite)
            for gs_antenna in station.antenna.all():
                for transmitter in transmitters:
                    if transmitter.downlink_low:
                        if (gs_antenna.frequency <=
                                transmitter.downlink_low <=
                                gs_antenna.frequency_max):
                            frequency_supported = True
            if not frequency_supported:
                continue

        observer.date = ephem.date(datetime.today())

        try:
            sat_ephem = ephem.readtle(str(satellite.latest_tle.tle0),
                                      str(satellite.latest_tle.tle1),
                                      str(satellite.latest_tle.tle2))
        except (ValueError, AttributeError):
            continue

        # Here we are going to iterate over each satellite to
        # find its appropriate passes within a given time constraint
        keep_digging = True
        while keep_digging:
            try:
                tr, azr, tt, altt, ts, azs = observer.next_pass(sat_ephem)
            except ValueError:
                break  # there will be sats in our list that fall below horizon, skip
            except TypeError:
                break  # if there happens to be a non-EarthSatellite object in the list
            except Exception:
                break

            if tr is None:
                break

            # using the angles module convert the sexagesimal degree into
            # something more easily read by a human
            try:
                elevation = format(math.degrees(altt), '.0f')
                azimuth_r = format(math.degrees(azr), '.0f')
                azimuth_s = format(math.degrees(azs), '.0f')
            except TypeError:
                break
            passid += 1

            # show only if >= configured horizon and in next 6 hours,
            # and not directly overhead (tr < ts see issue 199)
            if tr < ephem.date(datetime.today() +
                               timedelta(hours=settings.STATION_UPCOMING_END)):
                if (float(elevation) >= station.horizon and tr < ts):
                    valid = True
                    if tr < ephem.Date(datetime.now() +
                                       timedelta(minutes=settings.OBSERVATION_DATE_MIN_START)):
                        valid = False
                    polar_data = calculate_polar_data(observer,
                                                      sat_ephem,
                                                      tr.datetime(),
                                                      ts.datetime(), 10)
                    sat_pass = {'passid': passid,
                                'mytime': str(observer.date),
                                'name': str(satellite.name),
                                'id': str(satellite.id),
                                'success_rate': str(satellite.success_rate),
                                'unknown_rate': str(satellite.unknown_rate),
                                'bad_rate': str(satellite.bad_rate),
                                'data_count': str(satellite.data_count),
                                'good_count': str(satellite.good_count),
                                'bad_count': str(satellite.bad_count),
                                'unknown_count': str(satellite.unknown_count),
                                'norad_cat_id': str(satellite.norad_cat_id),
                                'tr': tr.datetime(),  # Rise time
                                'azr': azimuth_r,     # Rise Azimuth
                                'tt': tt.datetime(),  # Max altitude time
                                'altt': elevation,    # Max altitude
                                'ts': ts.datetime(),  # Set time
                                'azs': azimuth_s,     # Set azimuth
                                'valid': valid,
                                'polar_data': polar_data}
                    nextpasses.append(sat_pass)
                observer.date = ephem.Date(ts).datetime() + timedelta(minutes=1)
            else:
                keep_digging = False

    data = {
        'id': id,
        'nextpasses': sorted(nextpasses, key=itemgetter('tr'))
    }

    return JsonResponse(data, safe=False)


def station_edit(request, id=None):
    """Edit or add a single station."""
    station = None
    antennas = Antenna.objects.all()
    rigs = Rig.objects.all()
    if id:
        station = get_object_or_404(Station, id=id, owner=request.user)

    if request.method == 'POST':
        if station:
            form = StationForm(request.POST, request.FILES, instance=station)
        else:
            form = StationForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.save(commit=False)
            if not station:
                f.testing = True
            f.owner = request.user
            f.save()
            form.save_m2m()
            messages.success(request, 'Ground Station saved successfully.')
            return redirect(reverse('base:station_view', kwargs={'id': f.id}))
        else:
            messages.error(request, ('Your Ground Station submission has some '
                                     'errors. {0}').format(form.errors))
            return render(request, 'base/station_edit.html',
                          {'form': form, 'station': station, 'antennas': antennas, 'rigs': rigs})
    else:
        if station:
            form = StationForm(instance=station)
        else:
            form = StationForm()
        return render(request, 'base/station_edit.html',
                      {'form': form, 'station': station, 'antennas': antennas, 'rigs': rigs})


@login_required
def station_delete(request, id):
    """View for deleting a station."""
    me = request.user
    station = get_object_or_404(Station, id=id, owner=request.user)
    station.delete()
    messages.success(request, 'Ground Station deleted successfully.')
    return redirect(reverse('users:view_user', kwargs={'username': me}))


def satellite_view(request, id):
    try:
        sat = Satellite.objects.get(norad_cat_id=id)
    except Satellite.DoesNotExist:
        data = {
            'error': 'Unable to find that satellite.'
        }
        return JsonResponse(data, safe=False)

    data = {
        'id': id,
        'name': sat.name,
        'names': sat.names,
        'image': sat.image,
        'success_rate': sat.success_rate,
        'good_count': sat.good_count,
        'bad_count': sat.bad_count,
        'unknown_count': sat.unknown_count,
        'data_count': sat.data_count,
    }

    return JsonResponse(data, safe=False)
