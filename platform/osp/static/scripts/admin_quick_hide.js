$( function () {
    initializeQuickHideButtonHandler( $( ".quickHideStreamButton" ) );
    if ( $('#streamList a.jscroll-next:last' ).length ) {
        $('#streamList').jscroll({
            debug: true,
            loadingHtml: '<div>...</div>',
            padding: 20,
            nextSelector: 'a.jscroll-next:last',
            callback: function() {
                initializeQuickHideButtonHandler( $( ".jscroll-added" ).last().find( ".quickHideStreamButton" ) );
            }
        });
    }
});

function initializeQuickHideButtonHandler( button ) {
    $( button ).on( 'click', function( event ) {
        var streamName = $( this ).attr( "value" );
        var streamElement = $( this ).parents( ".stream" );

        $.ajax({
            url : '/api/hide/' + streamName + '/',
            type : "POST",
            success: function( data ) {
                if ( data === "True" ) {
                    streamElement.remove();
                }
            }
        });
    });
}