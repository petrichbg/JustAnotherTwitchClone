var username;
var previewTimeout = null;
var lastNotificationText = "";

$( function() {
    username = window.location.pathname.split( '/' )[1];

    $( "#postNotificationButton" ).click( function() {
        var banContext = $( "#notificationTarget .active" ).data( "value" );
        var notification = $( "#notificationTextArea" ).val().toString();
        var username = $( "#notificationTargetUsername" ).val();

        $.ajax({
            url : '',
            type : "POST",
            dataType: "json",
            data: {
                banContext: banContext,
                notification: notification,
                username: username
            },
            success: function( data ) {
                if ( !data['error'] ) {
                    $( "#notificationTextArea" ).val( "" );
                    $( "#notificationTargetUsername" ).val( "" );
                    $( "#notificationPreview" ).html( "" );

                    $( "#postNotificationErrorContainer" ).addClass( "hidden" );
                    // $( "#bansTable" ).prepend( data['html'] );

                    $( "#collapsePostNotificationPanel" ).collapse( 'hide' );
                    $( '#postNotificationLabel' ).text( "ОПОВЕЩЕНИЕ ОТПРАВЛЕНО" );
                    setTimeout( function () {
                        $('#postNotificationLabel').text( "ОПОВЕСТИТЬ" );
                    }, 2000);
                } else {
                    $( "#postNotificationErrorContainer" ).removeClass( "hidden" );
                    $( "#postNotificationErrorContainer" ).text( data['error'] );
                }
            }
        });
    } );

    $( "#notificationTextArea" ).on( "input", function() {
        if ( previewTimeout !== null ) {
            clearTimeout( previewTimeout );
        }

        var notificationText = $( "#notificationTextArea" ).val().toString();
        if ( notificationText === lastNotificationText ) {
            return;
        }
        
        previewTimeout = setTimeout( function() {
            lastNotificationText = notificationText;
            loadPreview();
        }, 600 );
    } );

    var notificationText = $( "#notificationTextArea" ).val().toString();
    if ( notificationText.length > 0 ) {
        loadPreview();
    }
} );

function loadPreview() {
    var notification = $( "#notificationTextArea" ).val().toString();

    $.ajax({
        url : '/service/markdownpreview/',
        type : "POST",
        dataType: "json",
        data: {
            message: notification
        },
        success: function( data ) {
            if ( !data['error'] ) {
                $( "#notificationPreview" ).html( data['html'] );
            }
        }
    });    
}