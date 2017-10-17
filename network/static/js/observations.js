$(document).ready(function() {
    'use strict';

    $('#satellite-filter').submit(function () {
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
        $('#satellite-filter').submit();
    });

    // Satellite Filters
    $('#satellite-selection').bind('keyup change', function() {
        $('#satellite-filter').submit();
    });
    if ($('#satellite-selection').val()) {

        $('#collapseFilters').show();
    }
});
