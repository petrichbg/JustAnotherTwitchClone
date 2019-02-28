var lastTab = null;

$( function() {
    $( '.nav-tabs a' ).on( 'shown.bs.tab', function ( e ) {
        window.location.hash = e.target.hash;
        $( "html" ).scrollTop( 0 );
        if ( lastTab !== null ) {
            lastTab.toggleClass( "active" );
        }
        lastTab = $( "#tabs [href='" + e.target.hash + "']" );
        lastTab.toggleClass( "active" );
    });

    var url = document.location.toString();
    if ( url.match( '#' ) ) {
        $( '.nav-tabs a[href="#' + url.split( '#' )[1] + '"]' ).tab( 'show' );
    } 
} );