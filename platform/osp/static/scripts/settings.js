var previewTimeout = null;
var lastBioText = "";

$( function() {
    $( "#id_bio" ).on( "input", function() {
        if ( previewTimeout !== null ) {
            clearTimeout( previewTimeout );
        }

        var bioText = $( "#id_bio" ).val().toString();
        if ( bioText === lastBioText ) {
            return;
        }
        
        previewTimeout = setTimeout( function() {
            lastBioText = bioText;
            loadPreview();
        }, 600 );
    } );

    var bio = $( "#id_bio" ).val().toString();
    if ( bio.length > 0 ) {
        loadPreview();
    }
} );

function loadPreview() {
    var bio = $( "#id_bio" ).val().toString();

    $.ajax({
        url : '/service/markdownpreview/',
        type : "POST",
        dataType: "json",
        data: {
            message: bio
        },
        success: function( data ) {
            if ( !data['error'] ) {
                $( "#bioPreview" ).html( data['html'] );
            }
        }
    });    
}