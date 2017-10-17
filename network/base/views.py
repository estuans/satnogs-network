import urllib2
import ephem
import math
from operator import itemgetter
from datetime import datetime, timedelta
from StringIO import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import now, make_aware, utc
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from rest_framework import serializers, viewsets

from network.base.models import (Station, Transmitter, Observation,
                                 Satellite, Antenna, Tle, Rig)
from network.base.forms import StationForm, SatelliteFilterForm
from network.base.decorators import admin_required
from network.base.helpers import calculate_polar_data, resolve_overlaps


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ('name', 'lat', 'lng')


class StationAllView(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.filter(active=True)
    serializer_class = StationSerializer


def satellite_position(request, sat_id):
    sat = get_object_or_404(Satellite, norad_cat_id=sat_id)
    try:
        satellite = ephem.readtle(
            str(sat.latest_tle.tle0),
            str(sat.latest_tle.tle1),
            str(sat.latest_tle.tle2)
        )
    except:
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
    observations = Observation.objects.all()
    try:
        featured_station = Station.objects.filter(active=True).latest('featured_date')
    except Station.DoesNotExist:
        featured_station = None

    ctx = {
        'latest_observations': observations.filter(end__lt=now()).order_by('-id')[:10],
        'scheduled_observations': observations.filter(end__gte=now()),
        'featured_station': featured_station,
        'mapbox_id': settings.MAPBOX_MAP_ID,
        'mapbox_token': settings.MAPBOX_TOKEN
    }

    return render(request, 'base/home.html', ctx)


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
        if request.POST['fetch']:
            try:
                data_out = StringIO()
                tle_out = StringIO()
                call_command('fetch_data', stdout=data_out)
                call_command('update_all_tle', stdout=tle_out)
                request.session['settings_out'] = data_out.getvalue() + tle_out.getvalue()
            except:
                messages.error(request, 'fetch command failed.')
        return redirect(reverse('base:settings_site'))

    fetch_out = request.session.get('settings_out', False)
    if fetch_out:
        del request.session['settings_out']
        return render(request, 'base/settings_site.html', {'fetch_data': fetch_out})
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
        Optionally filter based on good/bad/unvetted
        """
        norad_cat_id = self.request.GET.get('norad', '')
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

        if norad_cat_id == '':
            observations = Observation.objects.all()
        else:
            observations = Observation.objects.filter(
                satellite__norad_cat_id=norad_cat_id)

        if not bad:
            observations = observations.exclude(vetted_status='no_data')
        if not good:
            observations = observations.exclude(vetted_status='verified')
        if not unvetted:
            observations = observations.exclude(vetted_status='unknown')
        return observations

    def get_context_data(self, **kwargs):
        """
        Need to add a list of satellites to the context for the template
        """
        context = super(ObservationListView, self).get_context_data(**kwargs)
        context['satellites'] = Satellite.objects.all()
        norad_cat_id = self.request.GET.get('norad', None)
        context['bad'] = self.request.GET.get('bad', '1')
        context['good'] = self.request.GET.get('good', '1')
        context['unvetted'] = self.request.GET.get('unvetted', '1')
        if norad_cat_id is not None and norad_cat_id != '':
            context['norad'] = int(norad_cat_id)
        if 'scheduled' in self.request.session:
            context['scheduled'] = self.request.session['scheduled']
            try:
                del self.request.session['scheduled']
            except KeyError:
                pass
        return context


@login_required
def observation_new(request):
    """View for new observation"""
    me = request.user
    if request.method == 'POST':
        sat_id = request.POST.get('satellite')
        trans_id = request.POST.get('transmitter')
        try:
            start_time = datetime.strptime(request.POST.get('start-time'), '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(request.POST.get('end-time'), '%Y-%m-%d %H:%M')
        except ValueError:
            messages.error(request, 'Please use the datetime dialogs to submit valid values.')
            return redirect(reverse('base:observation_new'))

        if (end_time - start_time) > timedelta(minutes=int(settings.DATE_MAX_RANGE)):
            messages.error(request, 'Please use the datetime dialogs to submit valid timeframe.')
            return redirect(reverse('base:observation_new'))

        start = make_aware(start_time, utc)
        end = make_aware(end_time, utc)
        sat = Satellite.objects.get(norad_cat_id=sat_id)
        trans = Transmitter.objects.get(id=trans_id)
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
                   'date_min_start': settings.DATE_MIN_START,
                   'date_min_end': settings.DATE_MIN_END,
                   'date_max_range': settings.DATE_MAX_RANGE})


def prediction_windows(request, sat_id, transmitter, start_date, end_date,
                       station_id=None):
    try:
        sat = Satellite.objects.filter(transmitters__alive=True) \
            .filter(status='alive').distinct().get(norad_cat_id=sat_id)
    except:
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
    except:
        data = {
            'error': 'No TLEs for this satellite yet.'
        }
        return JsonResponse(data, safe=False)

    try:
        downlink = Transmitter.objects.get(id=int(transmitter)).downlink_low
    except:
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
        if not station.online:
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
                        except:
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

    # This context flag will determine if vet buttons appeas for the observation.
    # That includes observer, station owner involved, staff.
    is_vetting_user = False
    if request.user.is_authenticated():
        if observation.author == request.user or request.user.is_staff:
            is_vetting_user = True
        if Station.objects.filter(owner=request.user). \
           filter(id=observation.ground_station.id).count():
            is_vetting_user = True

    # This context flag will determine if a delete button appears for the observation.
    # That includes observer, superusers and people with certain permission.
    is_deletable = False
    if request.user.is_authenticated():
        if observation.author == request.user and observation.is_deletable_before_start:
            is_deletable = True
        if request.user.has_perm('base.delete_observation') and observation.is_deletable_after_end:
            is_deletable = True
        if request.user.is_superuser:
            is_deletable = True

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
        except:
            has_comments = False

        return render(request, 'base/observation_view.html',
                      {'observation': observation, 'has_comments': has_comments,
                       'discuss_url': discuss_url, 'discuss_slug': discuss_slug,
                       'is_vetting_user': is_vetting_user, 'is_deletable': is_deletable})

    return render(request, 'base/observation_view.html',
                  {'observation': observation, 'is_vetting_user': is_vetting_user,
                   'is_deletable': is_deletable})


@login_required
def observation_delete(request, id):
    """View for deleting observation."""
    observation = get_object_or_404(Observation, id=id)
    is_deletable = False
    if observation.author == request.user and observation.is_deletable_before_start:
        is_deletable = True
    if request.user.has_perm('base.delete_observation') and observation.is_deletable_after_end:
        is_deletable = True
    if request.user.is_superuser:
        is_deletable = True
    if is_deletable:
        observation.delete()
        messages.success(request, 'Observation deleted successfully.')
    else:
        messages.error(request, 'Permission denied.')
    return redirect(reverse('base:observations_list'))


@login_required
def observation_verify(request, id):
    me = request.user
    observation = get_object_or_404(Observation, id=id)
    observation.vetted_status = 'verified'
    observation.vetted_user = me
    observation.vetted_datetime = datetime.today()
    observation.save(update_fields=['vetted_status', 'vetted_user', 'vetted_datetime'])
    return redirect(reverse('base:observation_view', kwargs={'id': observation.id}))


@login_required
def observation_mark_bad(request, id):
    me = request.user
    observation = get_object_or_404(Observation, id=id)
    observation.vetted_status = 'no_data'
    observation.vetted_user = me
    observation.vetted_datetime = datetime.today()
    observation.save(update_fields=['vetted_status', 'vetted_user', 'vetted_datetime'])
    return redirect(reverse('base:observation_view', kwargs={'id': observation.id}))


def stations_list(request):
    """View to render Stations page."""
    stations = Station.objects.all()
    form = StationForm()
    antennas = Antenna.objects.all()

    return render(request, 'base/stations.html',
                  {'stations': stations, 'form': form, 'antennas': antennas})


def station_view(request, id):
    """View for single station page."""
    station = get_object_or_404(Station, id=id)
    form = StationForm(instance=station)
    antennas = Antenna.objects.all()
    rigs = Rig.objects.all()
    unsupported_frequencies = request.GET.get('unsupported_frequencies', '0')

    try:
        satellites = Satellite.objects.filter(transmitters__alive=True) \
            .filter(status='alive').distinct()
    except:
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
            except:
                break
            passid += 1

            # show only if >= configured horizon and in next 6 hours,
            # and not directly overhead (tr < ts see issue 199)
            if tr < ephem.date(datetime.today() +
                               timedelta(hours=settings.STATION_UPCOMING_END)):
                if (float(elevation) >= station.horizon and tr < ts):
                    valid = True
                    if tr < ephem.Date(datetime.now() +
                                       timedelta(minutes=int(settings.DATE_MIN_START))):
                        valid = False
                    polar_data = calculate_polar_data(observer,
                                                      sat_ephem,
                                                      tr.datetime(),
                                                      ts.datetime(), 10)
                    sat_pass = {'passid': passid,
                                'mytime': str(observer.date),
                                'debug': observer.next_pass(sat_ephem),
                                'name': str(satellite.name),
                                'id': str(satellite.id),
                                'success_rate': str(satellite.success_rate),
                                'unknown_rate': str(satellite.unknown_rate),
                                'empty_rate': str(satellite.empty_rate),
                                'data_count': str(satellite.data_count),
                                'verified_count': str(satellite.verified_count),
                                'empty_count': str(satellite.empty_count),
                                'unknown_count': str(satellite.unknown_count),
                                'norad_cat_id': str(satellite.norad_cat_id),
                                'tr': tr.datetime(),  # Rise time
                                'azr': azimuth_r,     # Rise Azimuth
                                'tt': tt,             # Max altitude time
                                'altt': elevation,    # Max altitude
                                'ts': ts.datetime(),  # Set time
                                'azs': azimuth_s,     # Set azimuth
                                'valid': valid,
                                'polar_data': polar_data}
                    nextpasses.append(sat_pass)
                observer.date = ephem.Date(ts).datetime() + timedelta(minutes=1)
            else:
                keep_digging = False

    return render(request, 'base/station_view.html',
                  {'station': station, 'form': form, 'antennas': antennas,
                   'mapbox_id': settings.MAPBOX_MAP_ID,
                   'mapbox_token': settings.MAPBOX_TOKEN,
                   'nextpasses': sorted(nextpasses, key=itemgetter('tr')),
                   'rigs': rigs,
                   'unsupported_frequencies': unsupported_frequencies})


@require_POST
def station_edit(request):
    """Edit or add a single station."""
    if request.POST['id']:
        pk = request.POST.get('id')
        station = get_object_or_404(Station, id=pk, owner=request.user)
        form = StationForm(request.POST, request.FILES, instance=station)
    else:
        form = StationForm(request.POST, request.FILES)
    if form.is_valid():
        f = form.save(commit=False)
        f.owner = request.user
        f.save()
        form.save_m2m()
        if f.online:
            messages.success(request, 'Successfully saved Ground Station.')
        else:
            messages.success(request, ('Successfully saved Ground Station. It will appear online '
                                       'as soon as it connects with our API.'))

        return redirect(reverse('base:station_view', kwargs={'id': f.id}))
    else:
        messages.error(request, 'Your Station submission had some errors.{0}'.format(form.errors))
        return redirect(reverse('users:view_user', kwargs={'username': request.user.username}))


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
        sat = get_object_or_404(Satellite, norad_cat_id=id)
    except:
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
        'verified_count': sat.verified_count,
        'empty_count': sat.empty_count,
        'unknown_count': sat.unknown_count,
        'data_count': sat.data_count,
    }

    return JsonResponse(data, safe=False)
