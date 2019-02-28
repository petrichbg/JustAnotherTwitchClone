var username;

$( function() {
    username = window.location.pathname.split( '/' )[1];

    $( "#banButton" ).click( function() {
        var banContext = $( "#banContext" )[0].selectedIndex;
        var banTarget = $("#banTarget .active").data( "value" );
        var banLength = $( "#banLength" ).val();
        var banLengthMeasurement = $( "#banLengthMeasurement" )[0].selectedIndex;
        var banReason = $( "#banReason" ).val();

        $.ajax({
            url : '/service/userban/' + username + '/',
            type : "POST",
            dataType: "json",
            data: {
                ban_context: banContext,
                ban_target: banTarget,
                ban_length: banLength,
                ban_length_measurement: banLengthMeasurement,
                ban_reason: banReason
            },
            success: function( data ) {
                if ( !data['error'] ) {
                    $( "#banLength" ).val( "" );
                    $( "#banReason" ).val( "" );
                    $( "#banListErrorMessageContainer" ).addClass( "hidden" );
                    $( "#bansTable" ).prepend( data['html'] );

                    $( "#collapseBanPanel" ).collapse( 'hide' );
                } else {
                    $( "#banErrorMessageContainer" ).removeClass( "hidden" );
                    $( "#banErrorMessageContainer" ).text( data['error'] );
                }
            }
        });
    } );
    
    $( "#banLengthMeasurement" ).change( function() {
        var index = $( this )[0].selectedIndex;
        if ( index == 5 ) { // permanent
            $( "#banLength" ).attr( "disabled", "" );
            $( "#banLength" ).val( "" );
        } else {
            $( "#banLength" ).removeAttr( "disabled" );
        }
    } );    
} );

function liftBan( button ) {
    if ( !confirm( "Вы точно хотите преждевременно снять этот бан?" ) ) {
        return;
    }

    var banId = $( button ).data( "id" );
    var banContext = $( button ).data( "context" );
    var banByIP = $( button ).data( "ban-by-ip" );

    $.ajax({
        url : '/service/userunban/' + username + '/',
        type : "POST",
        dataType: "json",
        data: {
            ban_id: banId,
            ban_context: banContext,
            ban_by_ip: banByIP
        },
        success: function( data ) {
            if ( !data['error'] ) {
                $( button ).parent().parent().addClass( "lifted" );
                $( button ).remove();
            } else {
                $( "#banErrorMessageContainer" ).removeClass( "hidden" );
                $( "#banErrorMessageContainer" ).text( data['error'] );
            }
        }
    });
}