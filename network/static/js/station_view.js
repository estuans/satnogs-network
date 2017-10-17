/* global L, URI */

$(document).ready(function() {
    'use strict';

    // Render Station success rate
    var success_rate = $('.gs.progress-bar-success').data('success-rate');
    var percentagerest = $('.gs.progress-bar-danger').data('percentagerest');
    $('.gs.progress-bar-success').css('width', success_rate + '%');
    $('.gs.progress-bar-danger').css('width', percentagerest + '%');

    // Reading data for station
    var station_info = $('#station-info').data();

    // Confirm station deletion
    var message = 'Do you really want to delete this Ground Station?';
    var actions = $('#station-delete');
    if (actions.length) {
        actions[0].addEventListener('click', function(e) {
            if (! confirm(message)) {
                e.preventDefault();
            }
        });
    }

    // Init the map
    var mapboxid = $('div#map-station').data('mapboxid');
    var mapboxtoken = $('div#map-station').data('mapboxtoken');

    L.mapbox.accessToken = mapboxtoken;
    L.mapbox.config.FORCE_HTTPS = true;
    var map = L.mapbox.map('map-station', mapboxid,{
        zoomControl: false
    }).setView([station_info.lat, station_info.lng], 6);

    // Add a marker
    L.mapbox.featureLayer({
        type: 'Feature',
        geometry: {
            type: 'Point',
            coordinates: [
                parseFloat(station_info.lng),
                parseFloat(station_info.lat)
            ]
        },
        properties: {
            title: station_info.name,
            'marker-size': 'large',
            'marker-color': '#666',
        }
    }).addTo(map);

    // Filters
    $('#antenna-filter').submit(function () {
        var the_form = $(this);

        the_form.find('input[type="checkbox"]').each( function () {
            var the_checkbox = $(this);


            if( the_checkbox.is(':checked') === true ) {
                the_checkbox.attr('value','1');
            } else {
                the_checkbox.prop('checked',true);
                // Check the checkbox but change it's value to 0
                the_checkbox.attr('value','0');
            }
        });
    });

    $('.filter-section input[type=checkbox]').change(function() {
        $('#antenna-filter').submit();
    });

    // Hightlight Data block
    var uri = new URI(location.href);
    var tab = uri.hash();
    $('ul.nav a[href="' + tab + '"]').tab('show');
});
