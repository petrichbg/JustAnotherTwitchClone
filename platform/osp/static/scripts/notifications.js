function removeNotification( button ) {

    var id = $( button ).data( "id" );
    var notificationType = $( button ).data( "notification-type" );

    $.ajax({
        url : '/service/removenotification/',
        type: 'POST',
        dataType: "json",
        data: {
            id: id,
            notificationType: notificationType
        },
        success: function( data ) {
            if ( !data['error'] ) {
                $( button ).parent().parent().parent().remove();
            }

            if ( $( "#notifications" ).children().length === 0 ) {
                $( "#notificationsLabel" ).toggleClass( "hidden" );
                $( "#noNotificationsLabel" ).toggleClass( "hidden" );
            }
        }
    });

}