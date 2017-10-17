$( document ).ready( function(){
    $('#fetchform').submit(function(){
        $('button[type=submit]', this).attr('disabled', 'disabled');
        $('button[type=submit]', this).text('fetching');
    });

    $('#fetch_log').click(function(){
        $('code').toggle();
        event.preventDefault();
    });
});
