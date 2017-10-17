/* global moment */

$(document).ready(function() {
    'use strict';

    $('#UTCModal').on('show.bs.modal', function () {
        var local = moment().format('HH:mm:ss');
        var utc = moment().utc().format('HH:mm:ss');
        $('#timezone-utc').text(utc);
        $('#timezone-local').text(local);
    });
});
