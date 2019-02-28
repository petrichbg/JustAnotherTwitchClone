$( function() {
    if ( typeof( Storage ) === "undefined" ) {
        return;
    }

    var isDark = localStorage.getItem( "streamView_dark" );
    if ( isDark === "true" ) {
        $( "body" ).addClass( "dark" );
    }

    $( "#darkModeButton" ).click( function() {
        var isDark = $( "body" ).hasClass( "dark" );
        $( "body" ).toggleClass( "dark" );
        saveStreamSetting( "streamView_dark", !isDark );
    } );
    
} );

function saveStreamSetting( settingName, settingValue ) {
    if ( typeof( Storage ) === "undefined" ) {
        return;
    }
    
    localStorage.setItem( settingName, settingValue );
}