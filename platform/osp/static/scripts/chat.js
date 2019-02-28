var chatAddress = "";

var connection;

var showingChatClients = false;
var showingChatProfileInfo = false;
var showingIgnoredChatMessages = false;
var chatAutoFocus = false;
var autoLogin = true;
var loadRecentMessages = true;

var userNicknames = [];

var ignoredUsers = [];

$( function () {
    initConnection();
    readChatSettings();

    $( "#chatClientListButton" ).click( function() {
        if ( showingChatClients ) {
            $( "#chat" ).removeClass( "showChatClients" );
            saveChatSetting( "streamChat_showChatClients", false );
        } else {
            $( "#chat" ).addClass( "showChatClients" );
            saveChatSetting( "streamChat_showChatClients", true );
        }

        showingChatClients = !showingChatClients;
    } );

	$( "#reconnectButton" ).click( function() {
		initConnection();
		$( "#reconnectLabel" ).css( "display", "none" );
	} );

    $( "#loginButton" ).click( function() {
        login();
        $( "#reconnectLabel" ).css( "display", "none" );
        $( "#loginButton" ).css( "display", "none" );
    } );

    $( "#sendMessageButton" ).click( sendCurrentMessage );
    $( "#messageTextArea" ).keydown( function ( event ) {
        if ( event.keyCode === 13 ) {
            sendCurrentMessage();
            event.preventDefault();
        }
    } );

    //you cannot use data-toggle dropdown and tooltip simultaneously
    if ( !( 'ontouchstart' in window ) ) {
        $( "#chatSettingsButton" ).tooltip({
            container: 'body',
            animation: false
        });
    }

    //do not let the settings dropdown to close
    $( '#chatSettingsDropdown' ).click( function( e ) {
        e.stopPropagation();
    } );

    $( "#showTimestampsCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );
        if ( isChecked ) {
            $( "#chatMessagesContainer" ).removeClass( "chatMessageTimestampHidden" );
        } else {
            $( "#chatMessagesContainer" ).addClass( "chatMessageTimestampHidden" );
        }

        saveChatSetting( "streamChat_showTimestamps", isChecked );
    });
    $( "#showTimestampsCheckbox" ).trigger( "change" );

    $( "#showChatViewerCountCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );
        if ( isChecked ) {
            $( "#chat" ).removeClass( "hiddenViewerCount" );
        } else {
            $( "#chat" ).addClass( "hiddenViewerCount" );
        }

        saveChatSetting( "streamChat_showViewerCount", isChecked );
    });
    $( "#showChatViewerCountCheckbox" ).trigger( "change" );

    $( "#showIgnoredChatMessagesCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );

        showingIgnoredChatMessages = isChecked;
        saveChatSetting( "streamChat_showIgnoredChatMessages", isChecked );
        showIgnoredMessages( isChecked );
    });
    $( "#showIgnoredChatMessagesCheckbox" ).trigger( "change" );

    $( "#chatAutoLoginCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );
        autoLogin = isChecked;
        saveChatSetting( "streamChat_autoLogin", isChecked );
    });
    $( "#chatAutoLoginCheckbox" ).trigger( "change" );

    $( "#chatLoadRecentMessagesCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );
        loadRecentMessages = isChecked;
        saveChatSetting( "streamChat_loadRecentMessages", isChecked );
    });
    $( "#chatLoadRecentMessagesCheckbox" ).trigger( "change" );

    $( "#chatAutoFocusCheckbox" ).change( function() {
        var isChecked = $( this ).is( ":checked" );
        saveChatSetting( "streamChat_chatAutoFocus", isChecked );
    });
    $( "#chatAutoFocusCheckbox" ).trigger( "change" );

    $( "#clearChatButton" ).click( function() {
        clearChat();
        $( "#chatSettingsButton" ).click();
    } );

    $( "#showStandaloneChatButton" ).click( function() {
        $( "#chatSettingsButton" ).click();
        window.open( "/" + roomName + "/chat/", "_blank", "menubar=0,status=0,location=0,titlebar=0,toolbar=0,resizable=1" );
    } );

    if ( !( 'ontouchstart' in window ) ) {
        $( "#chatProfileInfoSwitchButton" ).tooltip({
            animation: false,
            template: '<div class="tooltip chatProfileInfoTooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
        });
    }
    $( "#chatProfileInfoSwitchButton" ).click( function() {
        var chatProfileInfoSwitchGlyph = $( "#chatProfileInfoSwitchButton" ).find( ".glyphicon" );
        var chatProfileInfoSwitchButton = $( "#chatProfileInfoSwitchButton" );

        if ( showingChatProfileInfo ) {
            $( "#chat" ).removeClass( "showChatProfileInfo" );
            chatProfileInfoSwitchGlyph.removeClass( "glyphicon-comment" );
            chatProfileInfoSwitchGlyph.addClass( "glyphicon-info-sign" );
            chatProfileInfoSwitchButton.attr( "title", "О стримере" );
            if ( !( 'ontouchstart' in window ) ) {
                chatProfileInfoSwitchButton.tooltip( 'fixTitle' ).tooltip('show');
            }
        } else {
            $( "#chat" ).addClass( "showChatProfileInfo" );
            chatProfileInfoSwitchGlyph.removeClass( "glyphicon-info-sign" );
            chatProfileInfoSwitchGlyph.addClass( "glyphicon-comment" );
            chatProfileInfoSwitchButton.attr( "title", "Чат" );
            if ( !( 'ontouchstart' in window ) ) {
                chatProfileInfoSwitchButton.tooltip( 'fixTitle' ).tooltip('show');
            }
        }

        showingChatProfileInfo = !showingChatProfileInfo;
    } );

} );

function saveChatSetting( settingName, settingValue ) {
    if ( typeof( Storage ) === "undefined" ) {
        return;
    }

    localStorage.setItem( settingName, settingValue );
}

function readChatSettings() {
    if ( typeof( Storage ) === "undefined" ) {
        return;
    }

    var showChatClients = localStorage.getItem( "streamChat_showChatClients" );
    if ( showChatClients === "true" ) {
        $( "#chat" ).addClass( "showChatClients" );
        showingChatClients = true;
    }

    var showTimestamps = localStorage.getItem( "streamChat_showTimestamps" );
    if ( showTimestamps === "true" ) {
        $( '#showTimestampsCheckbox' ).prop( 'checked', showTimestamps );
    }

    var showViewerCount = localStorage.getItem( "streamChat_showViewerCount" );
    if ( showViewerCount === "true" ) {
        $( '#showChatViewerCountCheckbox' ).prop( 'checked', showViewerCount );
    }

    var ignoredUsersString = localStorage.getItem( "streamChat_ignoredUsers" );
    if ( ignoredUsersString ) {
        ignoredUsers = ignoredUsersString.split( "," );
    }

    autoLogin = localStorage.getItem( "streamChat_autoLogin" );
    if ( autoLogin === "false" ) {
        $( '#chatAutoLoginCheckbox' ).prop( 'checked', false );
    }

    loadRecentMessages = localStorage.getItem( "streamChat_loadRecentMessages" );
    if ( loadRecentMessages === "false" ) {
        $( '#chatLoadRecentMessagesCheckbox' ).prop( 'checked', false );
    }

    var showIgnoredChatMessages = localStorage.getItem( "streamChat_showIgnoredChatMessages" );
    if ( showIgnoredChatMessages === "true" ) {
        $( '#showIgnoredChatMessagesCheckbox' ).prop( 'checked', showIgnoredChatMessages );
    }

    chatAutoFocus = localStorage.getItem( "streamChat_chatAutoFocus" );
    if ( chatAutoFocus === "true" ) {
        $( '#chatAutoFocusCheckbox' ).prop( 'checked', chatAutoFocus );
    }

}

function initConnection( ) {
    $( "#chat" ).addClass( "showConnectionDialog" );
    $( "#connectionDialogWrapper" ).css( "visibility", "visible" );
    $( "#connectionDialogLabel" ).text( "Подключаемся..." );
    $( "#reconnectButton" ).css( "visibility", "hidden" );

    if ( !connection ) {
        connection = io.connect( chatAddress );
    } else {
        connection.io.connect();
		return;
    }

    connection.io.reconnection( false );
    connection.io.timeout( 3000 );

    connection.on( 'connect', function() {
        connection.emit( 'CLIENT_ROOM_JOIN_REQUEST', roomName ); // join the room
    } );

    connection.on( 'connect_error', function () {
        resetChat( "Ошибка соединения" );
    } );

    connection.on( 'disconnect', function () {
        resetChat( "Разрыв соединения" );
    } );

    connection.on( 'SERVER_ROOM_JOIN_SUCCESS', function ( authenticated ) {
        showInfoMessage( "Подключен к чату " + roomName );

        if ( authenticated ) {
            if ( autoLogin ) {
                login();
            } else {
                provideLogin();
            }
        } else {
            $( "#chat" ).removeClass( "showConnectionDialog" );
        }

        if ( loadRecentMessages ) {
            connection.emit( 'CLIENT_RECENT_MESSAGES_REQUEST', roomName );
        }
    } );

    connection.on( 'SERVER_LOGIN_SUCCESS', function ( nickname ) {
        enableChat( nickname );
    } );

    connection.on( 'SERVER_BANNED', function ( nickname ) {
        markAsBannedChatMember( nickname );
    } );

    connection.on( 'SERVER_MODERATOR', function ( nickname ) {
        markAsModeratorChatMember( nickname );
    } );

    connection.on( 'SERVER_NO_MODERATOR', function ( nickname ) {
        markAsNoModeratorChatMember( nickname );
    } );

    connection.on( 'SERVER_ERROR', function ( errorString ) {
        showError( errorString );
    } );

    connection.on( 'SERVER_UNBANNED', function( nickname ) {
        markAsUnbannedChatMember( nickname );
    } );

    connection.on( 'SERVER_CLIENTS_LIST', function( clients ) {
        while ( clients.length > 0 ) {
            appendChatMember( clients.shift() );
        }
    });

    connection.on( 'SERVER_CLIENT_CONNECTED', function ( nickname ) {
        appendChatMember( nickname );
    } );

    connection.on( 'SERVER_CLIENT_DISCONNECTED', function ( nickname ) {
        removeChatMember( nickname );
    } );

    connection.on( 'SERVER_CLIENT_MESSAGE', function ( sender ) {
        appendChatMessage( sender );
    } );

    connection.on( 'SERVER_RECENT_MESSAGES', function ( messages ) {
        for ( var i = messages.length - 1 ; i >= 0 ; i-- ) {
            prependChatMessage( messages[i] );
        }
        scrollToBottom();
    } );

    connection.on( 'SERVER_INFO_MESSAGE', function( message ) {
        showInfoMessage( message );
    } );
}

function login() {
    connection.emit( 'CLIENT_ROOM_LOGIN_REQUEST', roomName );
}

function sendCurrentMessage() {
    var message = $( "#messageTextArea" ).val().toString();
    if ( message.length <= 0 ) {
        return;
    }
    $( "#messageTextArea" ).val( "" );

    connection.emit( 'CLIENT_MESSAGE', message );
}

function enableChat( nickname ) {
    $( "#chat" ).removeClass( "showConnectionDialog" );
    $( "#connectionDialogWrapper" ).css( "display", "none" );
    $( "#chatMessagesContainer" ).css( "display", "block" );

    $( "#chat" ).addClass( "showChatInput" );

    $( "#chat" ).addClass( "showChatClientNickname" );
    $( "#chatNicknameLabel" ).text( nickname );

    var chatNicknameLabel = $( "#chatNicknameLabel" ).text();
    if ( chatNicknameLabel.toLowerCase() === roomName.toLowerCase() ) {
        $( "#chatNicknameLabel" ).addClass( "clientOwner" );
    }

    if ( chatAutoFocus === "true" ) {
        $( "#messageTextArea" ).focus();
    }
}

function disableChat() {
    $( "#chat" ).removeClass( "showChatInput" );
}

function provideLogin() {
	$( "#reconnectLabel" ).css( "display", "inline-block" );

    $( "#connectionDialogWrapper" ).css( "display", "table" );
    $( "#chat" ).addClass( "showConnectionDialog" );
    $( "#connectionDialogWrapper" ).css( "visibility", "visible" );
    $( "#connectionDialogLabel" ).text( "Автовход отключен" );
    $( "#reconnectButton" ).css( "display", "none" );
    $( "#loginButton" ).css( "display", "inline" );
    $( "#loginButton" ).css( "visibility", "visible" );
    $( "#loginButton" ).text( "Войти" );
}

function resetChat( error ) {
    userNicknames = [];

    disableChat();
    $( "#chat" ).removeClass( "showChatClientNickname" );
	$( "#reconnectLabel" ).css( "display", "inline-block" );
    $( "#chatClientsContainer" ).empty();

    $( "#connectionDialogWrapper" ).css( "display", "table" );
    if ( error ) {
        $( "#chat" ).addClass( "showConnectionDialog" );
        $( "#connectionDialogWrapper" ).css( "visibility", "visible" );
        $( "#connectionDialogLabel" ).text( error );
        $( "#loginButton" ).css( "display", "none" );
        $( "#reconnectButton" ).css( "display", "inline" );
        $( "#reconnectButton" ).css( "visibility", "visible" );
        $( "#reconnectButton" ).text( "Подключиться снова" );
    }
}

function clearChat() {
    $( "#chatMessagesContainer" ).empty();
}

function makeChatMessage( sender ) {
    var messageNickname = $( "<span class=chatMessageNickname>" + sender.nickname + "</span>" );
    if ( sender.owner ) {
        messageNickname.addClass( "clientOwner" );
    }
    if ( sender.moderator ) {
        messageNickname.addClass( "clientModerator" );
    }
    if ( sender.banned ) {
        messageNickname.addClass( "clientBanned" );
    }
    if ( sender.bot ) {
        messageNickname.addClass( "clientBot" );
    }

    var timeString;
    if ( sender.timestamp !== undefined ) {
        timeString = buildTimeString( new Date( sender.timestamp ) );
    } else {
        timeString = getCurrentTimeString();
    }

    // linkify destroys spaces needed for timestamp
    var timestampElement = $( "<span class=chatMessageTimestamp>" + timeString + " </span>" );
    var messageElement = $( "<li class=chatMessage>" + messageNickname.outerHTML() + "<span class=chatMessageText></span></li>" );
    messageElement.children( ".chatMessageText" ).text( ": " + sender.message ).linkify();
    messageElement.prepend( timestampElement );
    messageElement.find( ".linkified" ).attr( "target", "_blank" );
    messageElement.children( ".chatMessageNickname" ).click( function( e ) {
        if ( e.ctrlKey === true || e.button === 1 ) {
            window.open( '/' + sender.nickname + '/profile/', '_blank' );
            return;
        }
        showUserCard( $( this ) );
    } );
    messageElement.children( ".chatMessageNickname" ).mousedown( function( e ) {
        if ( e.button === 1 ) {
            e.preventDefault();
            window.open( '/' + sender.nickname + '/profile/', '_blank' );
        }
    } );

    var br = $( "<br/>" );

    if ( userIsIgnored( sender.nickname ) ) {
        if ( !showingIgnoredChatMessages ) {
            $( messageElement ).addClass( "chatMessageIgnored" );
            br.addClass( "chatMessageIgnored" );
        } else {
            $( messageElement ).addClass( "chatMessagePreviouslyIgnored" );
            br.addClass( "chatMessagePreviouslyIgnored" );
        }
    }

    return [ messageElement, br ];
}

function prependChatMessage( sender ) {
    var messageElement = makeChatMessage( sender );

    $( "#chatMessagesContainer" ).prepend( messageElement[1] ); // <br>
    $( "#chatMessagesContainer" ).prepend( messageElement[0] ); // message

}

function appendChatMessage( sender ) {
    var haveToAutoScroll = shouldAutoScroll();

    var messageElement = makeChatMessage( sender );

    $( "#chatMessagesContainer" ).append( messageElement[0] ); // message
    $( "#chatMessagesContainer" ).append( messageElement[1] ); // <br>

    if ( haveToAutoScroll ) {
        scrollToBottom();
    }
}

function appendChatMember( chatMember ) {
    if ( chatMember !== undefined ) {
        if ( chatMember.nickname === undefined ) {
            return;
        }
        if ( userNicknames.indexOf( chatMember.nickname ) != -1 ) {
            return;
        }
        var chatClient = $( "<li class=chatClientNickname><span>" + chatMember.nickname + "</span></li>" );
        if ( chatMember.owner ) {
            chatClient.addClass( "clientOwner" );
        }
        if ( chatMember.moderator ) {
            chatClient.addClass( "clientModerator" );
        }
        if ( chatMember.banned ) {
            chatClient.addClass( "clientBanned" );
        }
        if ( chatMember.bot ) {
            chatClient.addClass( "clientBot" );
        }
        chatClient.click( function( e ) {
            if ( e.ctrlKey === true || e.button === 1 ) {
                window.open( '/' + chatMember.nickname + '/profile/', '_blank' );
                return;
            }
            showUserCard( $( this ) );
        } );
        chatClient.mousedown( function( e ) {
            if ( e.button === 1 ) {
                e.preventDefault();
                window.open( '/' + chatMember.nickname + '/profile/', '_blank' );
            }
        } );

        var chatClientContainer = $( "#chatClientsContainer" ).append( chatClient );
        if ( chatClient.width() > ( chatClientContainer.width() / 2 ) - 5 ) { //dumb magic numbers so it works for now, thanks to paddings etc
            chatClient.attr( "title", chatMember.nickname );
        }

        crossIfIgnored( chatMember.nickname );

        userNicknames.push( chatMember.nickname );
    }
}

function removeChatMember( nickname ) {
    $( ".chatClientNickname" ).each( function () {
        if ( $( this ).text() === nickname ) {
            $( this ).remove();
            userNicknames.splice( userNicknames.indexOf( nickname ), 1 );
        }
    } );
}

function markAsBannedChatMember( nickname ) {
    $( ".chatClientNickname" ).each( function () {
        if ( $( this ).text() === nickname ) {
            $( this ).addClass( "clientBanned" );
        }
    } );

    if ( $( "#chatNicknameLabel" ).text() === nickname ) {
        $( "#chatNicknameLabel" ).addClass( "clientBanned" );
        disableChat();
    }
}

function markAsUnbannedChatMember( nickname ) {
    $( ".chatClientNickname" ).each( function () {
        if ( $( this ).text() === nickname ) {
            $( this ).removeClass( "clientBanned" );
        }
    } );

    if ( $( "#chatNicknameLabel" ).text() === nickname ) {
        $( "#chatNicknameLabel" ).removeClass( "clientBanned" );
        enableChat();
    }
}

function markAsModeratorChatMember( nickname ) {
    $( ".chatClientNickname" ).each( function () {
        var chatClientNickname = $( this ).text();
        if ( chatClientNickname === nickname ) {
            $( this ).addClass( "clientModerator" );
        }
    } );

    if ( $( "#chatNicknameLabel" ).text() === nickname ) {
        $( "#chatNicknameLabel" ).addClass( "clientModerator" );
    }
}

function markAsNoModeratorChatMember( nickname ) {
    $( ".chatClientNickname" ).each( function () {
        var chatClientNickname = $( this ).text();
        if ( chatClientNickname === nickname ) {
            $( this ).removeClass( "clientModerator" );
        }
    } );

    if ( $( "#chatNicknameLabel" ).text() === nickname ) {
        $( "#chatNicknameLabel" ).removeClass( "clientModerator" );
    }
}

function showError( errorString ) {
    var haveToAutoScroll = shouldAutoScroll();

    var messageElement = $( "<li class=chatMessage><span class=chatMessageError></span></li>" );
    messageElement.children( ".chatMessageError" ).text( errorString );
    $( "#chatMessagesContainer" ).append( messageElement );
    $( "#chatMessagesContainer" ).append( "<br>" );

    if ( haveToAutoScroll ) {
        scrollToBottom();
    }
}

function showInfoMessage( infoString ) {
    var haveToAutoScroll = shouldAutoScroll();

    // linkify destroys spaces needed for timestamp
    var timestampElement = $( "<span class=chatMessageTimestamp>" + getCurrentTimeString() + " </span>" );
    var messageElement = $( "<li class=chatMessage><span class=chatMessageInfo></span></li>" );
    messageElement.children( ".chatMessageInfo" ).text( infoString ).linkify();
    messageElement.prepend( timestampElement );
    messageElement.find( ".linkified" ).attr( "target", "_blank" );
    $( "#chatMessagesContainer" ).append( messageElement );
    $( "#chatMessagesContainer" ).append( "<br>" );

    if ( haveToAutoScroll ) {
        scrollToBottom();
    }
}

function showUserCard( userElement ) {
    var username = $( userElement ).text();
    if ( username.length <= 0 ) {
        return;
    }

    var isBot = userElement.hasClass( "clientBot" );
    console.log( isBot );

    $.ajax({
        url : '/service/chatusercard/',
        type : "POST",
        data: {
            "room": roomName,
            "username": username,
            "is_bot": isBot
        },
        success: function( data ) {
            if ( data !== 0 ) {
                var userCard = $( data );
                var userCardWidth = userCard.width();
                var userCardHeight = userCard.height();
                var windowWidth = $( window ).width();
                var windowHeight= $( window ).height();

                var topPos = userElement.offset().top;
                if ( topPos + userCardHeight > windowHeight - 4 ) {
                    topPos += windowHeight - ( topPos + userCardHeight ) - 4;
                }

                var leftPos = userElement.offset().left;
                if ( leftPos + userCardWidth > windowWidth - 4 ) {
                    leftPos += windowWidth - ( leftPos + userCardWidth ) - 4;
                }

                $( "#chat" ).append( userCard );
                $( userCard ).css({
                    top: topPos + "px",
                    left: leftPos + "px"
                });

                $( userCard ).draggable( { handle: ".chatUserCardUser" } );

                if ( !( 'ontouchstart' in window ) ) {
                    $( '[data-toggle="tooltipChatUserCard"]' ).tooltip( {'animation': false, 'container': userCard } );
                }

                $( userCard ).find( ".chatUserCardCloseButton" ).click( function() {
                    $( userCard ).remove();
                } );

                if ( userIsIgnored( username ) ) {
                    var ignoreIcon = $( userCard ).find( ".chatUserCardIgnoreButton span" );
                    ignoreIcon.removeClass( "glyphicon-volume-off" );
                    ignoreIcon.addClass( "glyphicon-volume-up" );
                    var ignoreButton = $( userCard ).find( ".chatUserCardIgnoreButton" ).attr( "title", "Перестать игнорировать" );
                    if ( !( 'ontouchstart' in window ) ) {
                        ignoreButton.tooltip( 'fixTitle' );
                    }
                }
                $( userCard ).find( ".chatUserCardIgnoreButton" ).click( function() {
                    var ignoreIcon = $( userCard ).find( ".chatUserCardIgnoreButton span" );
                    if ( userIsIgnored( username ) ) {
                        unignoreUser( username );
                        ignoreIcon.removeClass( "glyphicon-volume-up" );
                        ignoreIcon.addClass( "glyphicon-volume-off" );
                        $( userCard ).find( ".chatUserCardIgnoreButton" ).attr( "title", "Игнорировать" ).tooltip( 'fixTitle' );
                        if ( !( 'ontouchstart' in window ) ) {
                            ignoreButton.tooltip( 'fixTitle' );
                        }
                    } else {
                        ignoreUser( username );
                        ignoreIcon.removeClass( "glyphicon-volume-off" );
                        ignoreIcon.addClass( "glyphicon-volume-up" );
                        $( userCard ).find( ".chatUserCardIgnoreButton" ).attr( "title", "Перестать игнорировать" ).tooltip( 'fixTitle' );
                        if ( !( 'ontouchstart' in window ) ) {
                            ignoreButton.tooltip( 'fixTitle' );
                        }
                    }

                    crossIfIgnored( username );
                } );

                $( userCard ).find( ".chatUserCardBanButton" ).click( function() {
                    var isBanned = $( this ).find( ".glyphicon-heart" ).length > 0; //lame
                    if ( isBanned ) {
                        $.ajax({
                            url : '/service/chatunban/' + roomName + '/' + username + '/',
                            type : "POST",
                            dataType: "json",
                            success: function( data ) {
                                if ( !data['error'] ) {
                                    $( userCard ).find( ".chatUserCardUsername" ).removeClass( "clientBanned" );
                                    var banIcon = $( userCard ).find( ".chatUserCardBanButton span" );
                                    banIcon.removeClass( "glyphicon-heart" );
                                    banIcon.addClass( "glyphicon-fire" );
                                    var banButton = $( userCard ).find( ".chatUserCardBanButton" ).attr( "title", "Забанить" );
                                    var banConfirmButton = $( userCard ).find( ".chatUserCardBanConfirmButton" ).attr( "title", "Забанить" );
                                    if ( !( 'ontouchstart' in window ) ) {
                                        banButton.tooltip( 'fixTitle' ).tooltip( 'show' );
                                        banConfirmButton.tooltip( 'fixTitle' );
                                    }

                                    showInfoMessage( "Пользователь " + username + " был разбанен" );
                                }
                            }
                        });
                    } else {
                        $( userCard ).find( ".chatUserCardMainControls" ).addClass( "hidden" );
                        $( userCard ).find( ".chatUserCardBanControls" ).removeClass( "hidden" );
                        $( userCard ).find( ".chatUserCardCloseBanControlsButton" ).removeClass( "hidden" );
                    }
                } );

                $( userCard ).find( ".chatUserCardCloseBanControlsButton" ).click( function() {
                    $( userCard ).find( ".chatUserCardBanControls" ).addClass( "hidden" );
                    $( userCard ).find( ".chatUserCardCloseBanControlsButton" ).addClass( "hidden" );
                    $( userCard ).find( ".chatUserCardMainControls" ).removeClass( "hidden" );
                } );

                $( userCard ).find( ".chatUserCardBanConfirmButton" ).click( function() {
                    var banLength = $( userCard ).find( ".chatUserCardBanLength" ).val();
                    var banLengthMeasurement = $( userCard ).find( ".chatUserCardBanLengthMeasurement" )[0].selectedIndex;
                    var banReason = $( userCard ).find( ".chatUserCardBanReason" ).val();

                    $.ajax({
                        url : '/service/chatban/' + roomName + '/' + username + '/',
                        type : "POST",
                        dataType: "json",
                        data: {
                            ban_length: banLength,
                            ban_length_measurement: banLengthMeasurement,
                            ban_reason: banReason
                        },
                        success: function( data ) {
                            if ( !data['error'] ) {
                                $( userCard ).find( ".chatUserCardUsername" ).addClass( "clientBanned" );
                                var banIcon = $( userCard ).find( ".chatUserCardBanButton span" );
                                banIcon.removeClass( "glyphicon-fire" );
                                banIcon.addClass( "glyphicon-heart" );
                                var banButton = $( userCard ).find( ".chatUserCardBanButton" ).attr( "title", "Разбанить" );
                                if ( !( 'ontouchstart' in window ) ) {
                                    banButton.tooltip( 'fixTitle' );
                                }

                                showInfoMessage( "Пользователь " + username + " был забанен" );
                            } else {
                                showError( data['error'] );
                            }
                        }
                    });
                    $( userCard ).find( ".chatUserCardBanControls" ).addClass( "hidden" );
                    $( userCard ).find( ".chatUserCardCloseBanControlsButton" ).addClass( "hidden" );
                    $( userCard ).find( ".chatUserCardMainControls" ).removeClass( "hidden" );
                } );

                $( userCard ).find( ".chatUserCardBanLengthMeasurement" ).change( function() {
                    var index = $( this )[0].selectedIndex;
                    if ( index == 5 ) { // permanent
                        $( userCard ).find( ".chatUserCardBanLength" ).attr( "disabled", "" );
                        $( userCard ).find( ".chatUserCardBanLength" ).val( "" );
                    } else {
                        $( userCard ).find( ".chatUserCardBanLength" ).removeAttr( "disabled" );
                    }
                } );
            }
        }
    });
}

function ignoreUser( username ) {
    if ( !userIsIgnored( username ) ) {
        ignoredUsers.push( username );
        saveIgnoredUsers();
        showInfoMessage( "Пользователь " + username + " теперь игнорируется" );
    }
}

function unignoreUser( username ) {
    var index = ignoredUsers.indexOf( username );
    if ( index === -1 ) {
        return;
    }

    ignoredUsers.splice( index, 1 );
    saveIgnoredUsers();
    showInfoMessage( "Пользователь " + username + " больше не игнорируется" );
}

function userIsIgnored( username ) {
    return ignoredUsers.indexOf( username ) !== -1;
}

function saveIgnoredUsers() {
    saveChatSetting( "streamChat_ignoredUsers", ignoredUsers.toString() );
}

function crossIfIgnored( username ) {
    var isIgnored = userIsIgnored( username );
    $( ".chatClientNickname" ).each( function () {
        if ( $( this ).text() === username ) {
            if ( isIgnored ) {
                $( this ).css( "text-decoration", "line-through" );
            } else {
                $( this ).css( "text-decoration", "" );
            }
        }
    } );
}

function showIgnoredMessages( show ) {
    $( "#chatMessagesContainer" ).children().each( function () {
        if ( show ) {
            if ( $( this ).hasClass( "chatMessageIgnored" ) ) {
                $( this ).removeClass( "chatMessageIgnored" );
                $( this ).addClass( "chatMessagePreviouslyIgnored" );
            }
        } else {
            if ( $( this ).hasClass( "chatMessagePreviouslyIgnored" ) ) {
                $( this ).removeClass( "chatMessagePreviouslyIgnored" );
                $( this ).addClass( "chatMessageIgnored" );
            }
        }
    } );
}

function getCurrentTimeString() {
    var date = new Date();
    return buildTimeString( date );
}

function buildTimeString( date ) {
    var hours = date.getHours();
    if ( hours < 10 ) {
        hours = "0" + hours;
    }
    var minutes = date.getMinutes();
    if ( minutes < 10 ) {
        minutes = "0" + minutes;
    }

    var currentTimeString = hours + ":" + minutes;
    return currentTimeString;
}

function shouldAutoScroll() {
    var container = $( "#chatMessagesContainer" );
    var difference = container[0].scrollHeight - ( container[0].scrollTop + container.height() );

    return difference < 30;
}

function scrollToBottom() {
    var container = $( "#chatMessagesContainer" );
    container.scrollTop( container[0].scrollHeight );
}

jQuery.fn.outerHTML = function(s) {
    return s
        ? this.before(s).remove()
        : jQuery("<p>").append(this.eq(0).clone()).html();
};
