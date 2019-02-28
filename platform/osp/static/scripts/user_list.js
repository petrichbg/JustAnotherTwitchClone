function userListInit( elementID, options ) {
    var output = Mustache.render( "{{ fuck }}", options )
    $( elementID ).html( output );
}