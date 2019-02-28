$( function() {
    $( '.nav-tabs a' ).on( 'shown.bs.tab', function ( e ) {
        window.location.hash = e.target.hash;
        $( "html" ).scrollTop( 0 );
    });

    var url = document.location.toString();
    if ( url.match( '#' ) ) {
        $( '.nav-tabs a[href="#' + url.split( '#' )[1] + '"]' ).tab( 'show' );
    } 
} );