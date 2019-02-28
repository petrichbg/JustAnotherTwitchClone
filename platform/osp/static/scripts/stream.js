var usingLegacyPlayer = false;
var autoPlay = false;
var showingPlayerSettings = false;
var isMobile = false;
var streamSettings;

$( function() {
    streamSettings = readStreamSettings();

    isMobile = $( "#player" ).hasClass( "isMobile" );

    if ( streamSettings.enableFullscreen ) {
        setFullscreen( true );
    }

    $( "#toggleSidebarButton" ).click( function() {
        if ( $( "body" ).hasClass( "chatCollapsed" ) ) {
            $( "body" ).removeClass( "chatCollapsed" );
            $( "#toggleSidebarButton" ).attr( "data-original-title", "Скрыть чат" );
            $( "#toggleSidebarButton span" ).removeClass( "glyphicon-triangle-left" ).addClass( "glyphicon-triangle-right" );            
        } else {
            $( "body" ).addClass( "chatCollapsed" );
            $( "#toggleSidebarButton" ).attr( "data-original-title", "Раскрыть чат" );
            $( "#toggleSidebarButton span" ).removeClass( "glyphicon-triangle-right" ).addClass( "glyphicon-triangle-left" );            
        }
        
        sidebarEnabled = !sidebarEnabled;
    } );    

    $( "#fullscreenButton" ).click( function() {
        setFullscreen( true )
    } );
    
    $( "#disableFullscreenButton" ).click( function() {
        setFullscreen( false )
    } );

    $( '#followButton' ).click( function() { 
        follow( roomName );
    });

    $( '#playerSettingsButton' ).click( function() {
        if ( !showingPlayerSettings ) {
            $( "#playerSettingsButton" ).addClass( "active" );
            $( "#playerSettings" ).removeClass( "invisible" );
        } else {
            $( "#playerSettingsButton" ).removeClass( "active" );
            $( "#playerSettings" ).addClass( "invisible" );
            $( this ).blur();
        }

        showingPlayerSettings = !showingPlayerSettings;
    } );

    $( '#playerKeepAspectRatio' ).change( function() {
        saveStreamSetting( "streamView_playerFit", "false" );
        initializePlayer();
    } );

    $( '#playerFit' ).change( function() {
        saveStreamSetting( "streamView_playerFit", "true" );
        initializePlayer();
    } );
    if ( streamSettings.stretching === "exactfit" ) {
        $( '#playerFit' ).click();
    }

    $( "#autoPlayCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );
        saveChatSetting( "streamView_autoPlay", isChecked );
    });
    
    if ( streamSettings.autoPlay === "true" ) {
        $( '#autoPlayCheckbox' ).parent().addClass( 'active' );
    }
    
    $( '#saveStreamSettingsButton' ).on( 'click', function( event ){
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
                updateStreamInfo();
                $('#streamSettings').modal('hide');
            }
        });
    });

    if ( !( 'ontouchstart' in window ) ) {
        $('[data-toggle="tooltip"]').tooltip( {'animation': false, 'container': 'body' } );
    }
    
    initializePlayer();

    setInterval( updateStreamInfo, 20000 );
    updateStreamInfo();
} );

function initializePlayer() {
    if ( isMobile ) {
        // TODO: disable default controls and make them custom on all mobile browsers
        //initializeMobilePlayer();
    } else {
        initializeJWPlayer();
    }    
}

function initializeJWPlayer() {
    streamSettings = readStreamSettings();

    var settings = {
        sources: [
            {
                file: rtmpServerAddress + roomName
            }
        ],
        autostart: streamSettings.autoPlay,
        width: "100%",
        height: "100%",
        primary: "flash",
        stretching: streamSettings.stretching
    };

    if ( !usingLegacyPlayer ) {
        settings.skin = {
            name: "glow"
        };
    }

    jwplayer( "player" ).setup( settings );
}

function setFullscreen( enabled ) {
    if ( enabled ) {
        $( "body" ).addClass( "fullscreen" );
        saveStreamSetting( "streamView_enableFullscreen", true )
    } else {
        $( "body" ).removeClass( "fullscreen" );
        saveStreamSetting( "streamView_enableFullscreen", false )
    }
}

function saveStreamSetting( settingName, settingValue ) {
    if ( typeof( Storage ) === "undefined" ) {
        return;
    }
    
    localStorage.setItem( settingName, settingValue );
}

function readStreamSettings() {
    if ( typeof( Storage ) === "undefined" ) {
        return {
            enableFullscreen: false,
            stretching: "uniform",
            autoPlay: false
        }
    }
    
    var enableFullscreen = localStorage.getItem( "streamView_enableFullscreen" );
    var playerFit = localStorage.getItem( "streamView_playerFit" );
    var autoPlay = localStorage.getItem( "streamView_autoPlay" );

    return {
        enableFullscreen: enableFullscreen === "true",
        stretching: playerFit === "true" ? "exactfit" : "uniform",
        autoPlay: autoPlay
    }
}

function updateStreamInfo() {
    $.ajax({
        url: '/api/streaminfo/' + roomName + "/",
        dataType: 'json',
        success: function ( data ) {
            var description = data['description'];
            if ( description !== undefined ) {
                $( "#descriptionLabel" ).text( description );
                $( "#descriptionLabel" ).attr( "title", description );
            } else {
                $( "#descriptionLabel" ).text( "Безымянный стрим" );
            }
            
            $( "#viewerCount" ).text( data['viewers'] );
            $( "#chatClientViewerCount" ).text( data['viewers'] );
            $( "#followerCount" ).text( data['followers'] );
            
            var active = data['active'];
            if ( active ) {
                $( "#streamOfflineLabel" ).addClass( "hidden" );
                $( "#viewerCountContainer" ).removeClass( "hidden" );
                $( "#chatClientViewerCountContainer" ).removeClass( "hidden" );
            } else { 
                $( "#streamOfflineLabel" ).removeClass( "hidden" );
                $( "#viewerCountContainer" ).addClass( "hidden" );
                $( "#chatClientViewerCountContainer" ).addClass( "hidden" );
            }
        }
    });
}

function haveToResetPlayer() {
    return !( navigator.userAgent.indexOf( "Firefox" ) > 0 );
}