/*global L*/

$(document).ready(function() {
    'use strict';

    // Render Station success rate
    var success_rate = $('.progress-bar-success').data('success-rate');
    var percentagerest = $('.progress-bar-danger').data('percentagerest');
    $('.progress-bar-success').css('width', success_rate + '%');
    $('.progress-bar-danger').css('width', percentagerest + '%');

    var mapboxid = $('div#map').data('mapboxid');
    var mapboxtoken = $('div#map').data('mapboxtoken');
    var stations = $('div#map').data('stations');

    L.mapbox.accessToken = mapboxtoken;
    L.mapbox.config.FORCE_HTTPS = true;
    var map = L.mapbox.map('map', mapboxid, {
        zoomControl: false
    }).setView([40, 0], 3);
    L.mapbox.featureLayer().addTo(map);

    $.ajax({
        url: stations
    }).done(function(data) {
        data.forEach(function(m) {
            L.mapbox.featureLayer({
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [
                        parseFloat(m.lng),
                        parseFloat(m.lat)
                    ]
                },
                properties: {
                    title: m.name,
                    'marker-size': 'large',
                    'marker-color': '#666',
                }
            }).addTo(map);
        });
    });
});
