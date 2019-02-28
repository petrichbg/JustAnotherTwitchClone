$( function() {
    
    $( '#saveStreamDashboardButton' ).on( 'click', function( event ){
        event.preventDefault();
        
        var stream_description = $( "#id_stream_description" ).val();
        var stream_chat_motd = $( "#id_stream_chat_motd" ).val();
        var stream_hidden = $( "#id_stream_hidden" ).prop( 'checked' );
        
        $.ajax({
            url : '/' + roomName + '/dashboard/stream/',
            type : "POST",
            data : { 
                'stream_description': stream_description,
                'stream_chat_motd': stream_chat_motd,
                'stream_hidden': stream_hidden,
            }, 
            success: function() {
                $( '#saveStreamDashboardButton' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'bottom' } ).on( 'show.bs.popover', function () {
                    setTimeout( function () {
                        $('#saveStreamDashboardButton').popover('destroy');
                    }, 2000);
                });
                $( '#saveStreamDashboardButton' ).popover( 'show' );
            }
        });
    });
    
    $( "#dashboardHelperListAddButton" ).click( function() {
        var helperName = $( "#dashboardHelperListAddInput" ).val();
        if ( helperName.length <= 0 ) {
            return;
        }
        
        $.ajax({
            url : '/service/dashboardpermit/' + helperName + '/',
            type : "POST",
            dataType: "json",
            success: function( data ) {
                
                if ( !data['error'] ) {
                    $( '#dashboardHelperListButtonGroup' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'bottom' } ).on( 'show.bs.popover', function () {
                        setTimeout( function () {
                            $('#dashboardHelperListButtonGroup').popover('destroy');
                        }, 2000);
                    });
                    $( '#dashboardHelperListButtonGroup' ).popover( 'show' );
                    $( "#dashboardHelperListAddInput" ).val( "" );
                    var userListElement = $( data['html'] );
                    
                    userListElement.children( ".media-body" ).children( ".removeUserListElementButton" ).click( function() {
                        removeDashboardHelper( $( this ) );
                    } );
                    $( '#dashboardHelperList' ).append( userListElement );   
                    $( "#dashboardHelperListErrorMessageContainer" ).css( "display", "none" );
                } else {
                    $( "#dashboardHelperListErrorMessageContainer" ).css( "display", "block" );
                    $( "#dashboardHelperListErrorMessageContainer" ).text( data['error'] );
                }
            }
        });
    } );
    
    $( "#dashboardHelperList .removeUserListElementButton" ).click( function() {
        removeDashboardHelper( $( this ) );
    } );    
    
    $( "#opListAddButton" ).click( function() {
        var opName = $( "#opListAddInput" ).val();
        if ( opName.length <= 0 ) {
            return;
        }
        
        $.ajax({
            url : '/service/chatop/' + roomName + '/' + opName + '/',
            type : "POST",
            dataType: "json",
            success: function( data ) {
                if ( !data['error'] ) {
                    $( '#opListButtonGroup' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'bottom' } ).on( 'show.bs.popover', function () {
                        setTimeout( function () {
                            $( '#opListButtonGroup' ).popover('destroy');
                        }, 2000);
                    });
                    $( '#opListButtonGroup' ).popover( 'show' );
                    $( "#opListAddInput" ).val( "" );
                    var userListElement = $( data['html'] );
                    userListElement.children( ".media-body" ).children( ".removeUserListElementButton" ).click( function() {
                        removeModerator( $( this ) );
                    } );  
                    $( '#opList' ).append( userListElement );
                    $( "#opListErrorMessageContainer" ).css( "display", "none" );
                } else {
                    $( "#opListErrorMessageContainer" ).css( "display", "block" );
                    $( "#opListErrorMessageContainer" ).text( data['error'] );
                }
            }
        });
    } );
    
    $( "#opList .removeUserListElementButton" ).click( function() {
        removeModerator( $( this ) );
    } );
    
    $( "#banListAddButton" ).click( function() {
        var banName = $( "#banListAddInput" ).val();
        if ( banName.length <= 0 ) {
            return;
        }
        var banLength = $( "#banLength" ).val();
        var banLengthMeasurement = $( "#banLengthMeasurement" )[0].selectedIndex;
        var banReason = $( "#banReason" ).val();
        
        $.ajax({
            url : '/service/chatban/' + roomName + '/' + banName + '/',
            type : "POST",
            dataType: "json",
            data: { 
                ban_length: banLength,
                ban_length_measurement: banLengthMeasurement,
                ban_reason: banReason
            },
            success: function( data ) {
                if ( !data['error'] ) {
                    $( '#banListButtonGroup' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'bottom' } ).on( 'show.bs.popover', function () {
                        setTimeout( function () {
                            $( '#banListButtonGroup' ).popover('destroy');
                        }, 2000);
                    });
                    $( '#banListButtonGroup' ).popover( 'show' );
                    $( "#banListAddInput" ).val( "" );
                    $( "#banReason" ).val( "" );
                    var userListElement = $( data['html'] );
                    userListElement.find( ".removeBanElementButton" ).click( function() {
                        removeBan( $( this ) );
                    } );  
                    $( '#banList' ).prepend( userListElement );
                    $( "#banListErrorMessageContainer" ).css( "display", "none" );
                    userListElement.tooltip( {'animation': false, 'container': userListElement } );

                } else {
                    $( "#banListErrorMessageContainer" ).css( "display", "block" );
                    $( "#banListErrorMessageContainer" ).text( data['error'] );
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
    
    $( "#banList .removeBanElementButton" ).click( function() {
        removeBan( $( this ) );
    } );
    
    $( "#showStreamKeyButton" ).click( function() {
        $( "#streamKeyContainer" ).removeClass( "hidden" );
        $( "#showStreamKeyButton" ).addClass( "hidden" );
    } );
    
    $( "#resetStreamKeyButton" ).click( function() {
        $.ajax({
            url : '/service/updatestreamkey/' + roomName + '/',
            type : "POST",
            dataType: "json",
            success: function( data ) {
                if ( !data['error'] ) {
                    $( "#streamKey" ).val( data['stream_key'] );
                }
            }
        });
    } );
    
    
    $( "#resetStreamButton" ).click( function() {
        $.ajax({
            url : '/service/resetstream/' + roomName + '/',
            type : "POST",
            dataType: "json",
            success: function( data ) {
                if ( !data['error'] ) {
                    $( "#resetStreamButton" ).text( 'Успешно' );
                }
            }
        });
    } );
    
    $('[data-toggle="tooltip"]').tooltip( {'animation': false, 'container': 'body' } );
    $('[data-toggle="tooltipBanReason"]').each( function() {
        $( this ).tooltip( {'animation': false, 'container': $( this ) } );
    } );
    
    if ( $( "#player" ).length > 0 ) {
        jwplayer("player").setup({
            sources: [
                {
                    file: rtmpServerAddress + roomName
                }
            ],
            autostart: false,
            width: "100%",
            height: "100%",
            primary: "flash",
            skin: {
                name: "glow"
            }
        });
    }

    setInterval( updateStreamInfo, 20000 );
    updateStreamInfo();
} );

function updateStreamInfo() {
    $.ajax({
        url: '/api/streaminfo/' + roomName + '/',
        dataType: 'json',
        success: function ( data ) {
            $( "#viewerCount" ).text( data['viewers'] );
            $( "#chatClientViewerCount" ).text( data['viewers'] );
            $( "#followerCount" ).text( data['followers'] );
            
            var active = data['active'];
            if ( active ) {
                $( "#viewerCountContainer" ).removeClass( "hidden" );
                $( "#chatClientViewerCountContainer" ).removeClass( "hidden" );
                $( "#resetStreamButton" ).removeAttr( "disabled" );
                $( "#resetStreamSuccessLabel" ).css( "display", "none" );
            } else { 
                $( "#viewerCountContainer" ).addClass( "hidden" );
                $( "#chatClientViewerCountContainer" ).addClass( "hidden" );
                $( "#resetStreamButton" ).attr( "disabled", "disabled" );
            }
        }
    });
}

function removeDashboardHelper( helperElement ) {
    var helperName = $( helperElement ).prev().text().trim();  
    if ( helperName.length <= 0 ) {
        return;
    }
    
    var userListElement = $( helperElement ).parent().parent();
    
    $.ajax({
        url : '/service/dashboardforbid/' + helperName + '/',
        type : "POST",
        dataType: "json",
        success: function( data ) {
            if ( !data['error'] ) {
                $( '#dashboardHelperList' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'top' } ).on( 'show.bs.popover', function () {
                    setTimeout( function () {
                        $( '#dashboardHelperList' ).popover('destroy');
                    }, 2000);
                });
                $( '#dashboardHelperList' ).popover( 'show' );
                
                userListElement.remove();
            }
        }
    });
}

function removeModerator( moderatorElement ) {
    var opName = $( moderatorElement ).prev().text().trim();
    if ( opName.length <= 0 ) {
        return;
    }
    
    var userListElement = $( moderatorElement ).parent().parent();
    
    $.ajax({
        url : '/service/chatunop/' + roomName + '/' + opName + '/',
        type : "POST",
        dataType: "json",
        success: function( data ) {
            if ( !data['error'] ) {
                $( '#opList' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'top' } ).on( 'show.bs.popover', function () {
                    setTimeout( function () {
                        $('#opList').popover('destroy');
                    }, 2000);
                });
                $( '#opList' ).popover( 'show' );
                
                userListElement.remove();
            }
        }
    });
}

function removeBan( banElement ) {
    var banName = banElement.parents( "tr" ).children( "td" ).contents()[1].textContent;
    if ( banName.length <= 0 ) {
        return;
    }
     
    var userListElement = $( banElement ).parents( "tr" );
    
    $.ajax({
        url : '/service/chatunban/' + roomName + '/' + banName + '/',
        type : "POST",
        dataType: "json",
        success: function( data ) {
            if ( !data['error'] ) {
                $( '#banList' ).popover( { 'trigger': 'manual', 'content': 'Успешно', 'placement': 'top' } ).on( 'show.bs.popover', function () {
                    setTimeout( function () {
                        $('#banList').popover('destroy');
                    }, 2000);
                });
                $( '#banList' ).popover( 'show' );
                
                userListElement.remove();
            }
        }
    });   
}
