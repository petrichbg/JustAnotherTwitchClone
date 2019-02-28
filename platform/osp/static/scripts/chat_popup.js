$( function() {
    setInterval( updateStreamInfo, 10000 );
    updateStreamInfo();
    
    $('[data-toggle="tooltip"]').tooltip( {'animation': false, 'container': 'body' } );
} );

function updateStreamInfo() {
    $.ajax({
        url: '/api/streaminfo/' + roomName + '/',
        dataType: 'json',
        success: function ( data ) {
            $( "#chatClientViewerCount" ).text( data['viewers'] );  
            var active = data['active'];
            if ( active ) {
                $( "#chatClientViewerCountContainer" ).removeClass( "hidden" );
            } else { 
                $( "#chatClientViewerCountContainer" ).addClass( "hidden" );
            }
        }
    });
}