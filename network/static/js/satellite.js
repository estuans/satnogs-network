$(document).ready(function() {
    'use strict';

    $('#SatelliteModal').on('show.bs.modal', function (event) {
        var satlink = $(event.relatedTarget);
        var modal = $(this);

        $.ajax({
            url: '/satellites/' + satlink.data('id') + '/'
        })
            .done(function( data ) {
                modal.find('.satellite-title').text(data.name);
                modal.find('.satellite-names').text(data.names);
                modal.find('#SatelliteModalTitle').text(data.name);
                modal.find('.satellite-id').text(satlink.data('id'));
                modal.find('#db-link').attr('href', 'https://db.satnogs.org/satellite/' + satlink.data('id'));
                modal.find('#new-obs-link').attr('href', '/observations/new/?norad=' + satlink.data('id'));
                modal.find('#old-obs-link').attr('href', '/observations/?norad=' + satlink.data('id'));
                modal.find('.satellite-success').text(data.success_rate + '% success on ' + data.data_count + ' observations');
                modal.find('.satellite-good').text(data.good_count);
                modal.find('.satellite-unknown').text(data.unknown_count);
                modal.find('.satellite-bad').text(data.bad_count);
                if (data.image) {
                    modal.find('.satellite-img-full').attr('src', data.image);
                } else {
                    modal.find('.satellite-img-full').attr('src', '/static/img/sat.png');
                }

            });
    });
});
