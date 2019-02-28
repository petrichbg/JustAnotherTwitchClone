const async = require( 'async' );
const cookieParser = require( 'cookie' );
const config = require( 'config' );
const http = require( 'http' );

const logger = require( './logger' );
const pidFile = require( './pidFile' );

let io;
let clients = {};
let clientMessages = {};

function startServer() {
    process.on( 'SIGINT', function () {
        pidFile.del();
        logger.close();
        process.exit( 0 );
    });

    process.on( 'SIGUSR2', function () {
        logger.close();
        logger.init();
    });

    process.on( 'uncaughtException', function ( err ) {
        logger.log( err.stack );
        logger.close();
        throw err;
    });

    logger.init();
    pidFile.init();

    setInterval( cleraOldClientMessages, 1000 * 60 );

    let port = config.get( 'port' );
    io = require( 'socket.io' ).listen( port );

    // executed on each connected socket 
    io.use( beforeClientConnection );
    io.sockets.on( 'connection', onClientConnection );

    logger.log( "Process PID is " + process.pid );
    logger.log( "Server is running on port " + port );
    // logger.log( "Service port is " + servicePort );    
}

startServer();

// INIT ENDS HERE

// service io
let sio = require( 'socket.io' ).listen( config.get( 'servicePort' ) );
sio.sockets.on( 'connection', function ( client ) {
	client.ip = stripIPV6( client.request.connection.remoteAddress );
    logger.log( client.ip + ': Connected to service port' );
    
    // TODO: move these ips to the config
    if ( client.ip !== "127.0.0.1" && client.ip !== "::ffff:127.0.0.1" && client.ip !== "213.128.7.74" && client.ip !== "::ffff:213.128.7.74" && client.ip !== "91.229.74.179" && client.ip !== "::ffff:91.229.74.179" ) {
        logger.log( client.ip + ': Refused connection to service port' );
        client.disconnect();
    }
    
    client.on( 'MASS_BROADCAST', function ( message ) {
        logger.log( client.ip + ' MASS_BROADCAST: ' + message );
        massBroadcast( message );
    } );
    
    client.on( 'CHANNEL_MESSAGE', function ( data ) {
        try {
            data = JSON.parse( data );
            let message = data.message;
            let room = data.room;

            if ( io.sockets.adapter.rooms[room] === undefined ) {
                logger.log( client.ip + " CHANNEL_MESSAGE: room " + room + " doesn't exist" );
                return;
            }
            
            let roomClients = Object.keys( io.sockets.adapter.rooms[room].sockets );
            for ( let i = 0 ; i < roomClients.length ; i++ ) {
                let roomClient = clients[roomClients[i]];
                if ( roomClient !== undefined ) {
                    roomClient.emit( 'SERVER_ERROR', message );
                }
            }
            
            logger.log( client.ip + ' CHANNEL_MESSAGE (' + room + '): ' + message );

        } catch ( err ) {
            logger.log( `ERROR: Failed to parse CHANNEL_MESSAGE, ${err.message}` );
        }
    } );

    client.on( 'BAN_NOTIFY', function( data ) {
        try { 
            data = JSON.parse( data );

            let nickname = data.nickname;
            let room = data.room;
            let ban_reason = data.reason || null;
            let expiry_date = data.expiry_date || null;

            let client = getClientInRoom( nickname, room );
            if ( client !== undefined ) {
                io.to( room ).emit( 'SERVER_BANNED', nickname );
                let ban_message = makeBanMessage( ban_reason, expiry_date );
                client.emit( 'SERVER_ERROR', ban_message );
            }
        } catch ( err ) {
            logger.log( `ERROR: Failed to parse BAN_NOTIFY, ${err.message}` );
        }
    } );

    client.on( 'UNBAN_NOTIFY', function( data ) {
        try {
            data = JSON.parse( data );

            let nickname = data.nickname;
            let room = data.room;

            let client = getClientInRoom( nickname, room );
            if ( client !== undefined ) {
                io.to( room ).emit( 'SERVER_UNBANNED', nickname );
                client.emit( 'SERVER_ERROR', 'Вы были разбанены' );
            }
        } catch ( err ) {
            logger.log( `ERROR: Failed to parse UNBAN_NOTIFY, ${err.message}` );
        }
    } );  

    client.on( 'OP_NOTIFY', function( data ) {
        try { 
            data = JSON.parse( data );

            let nickname = data.nickname;
            let room = data.room;

            let client = getClientInRoom( nickname, room );
            if ( client !== undefined ) {
                io.to( room ).emit( 'SERVER_MODERATOR', nickname );
                client.emit( 'SERVER_ERROR', 'Теперь вы являетесь модератором этого канала' );
            }
        } catch ( err ) {
            logger.log( `ERROR: Failed to parse OP_NOTIFY, ${err.message}` );
        }
    } ); 

    client.on( 'UNOP_NOTIFY', function( data ) {
        try {
            data = JSON.parse( data );

            let nickname = data.nickname;
            let room = data.room;

            let client = getClientInRoom( nickname, room );
            if ( client !== undefined ) {
                io.to( room ).emit( 'SERVER_NO_MODERATOR', nickname );
                client.emit( 'SERVER_ERROR', 'Вы больше не являетесь модератором этого канала' );
            }
        } catch ( err ) {
            logger.log( `ERROR: Failed to parse UNOP_NOTIFY, ${err.message}` );
        }
    } );           
} );

// remove messages that are older than 1 hour
// and old remove messages if they exceed limit of 100 per room 
let MESSAGE_LIFETIME = 1000 * 60 * 60;
const MAX_MESSAGES_FOR_ROOM = 100;
function cleraOldClientMessages() {
    for ( let key in clientMessages ) {
        let roomMessages = clientMessages[key];

        let messagesToDelete = 0;
        for ( let message of roomMessages ) {
            let difference = new Date().valueOf() - message.timestamp;
            if ( difference >= MESSAGE_LIFETIME ) {
                messagesToDelete++;
            }

            if ( messagesToDelete > 0 ) {
                clientMessages[key].splice( 0, messagesToDelete );
            }
        }
        
        messagesToDelete = Math.max( 0, roomMessages.length - MAX_MESSAGES_FOR_ROOM );
        if ( messagesToDelete > 0 ) {
            clientMessages[key].splice( 0, messagesToDelete );
        }
    }
}

function beforeClientConnection( client, next ) {

    // HACK - allow to intercept all custom messages from the client
    // used to detect spam with custom messages
    // http://stackoverflow.com/questions/10405070/socket-io-client-respond-to-all-events-with-one-handler
    let onevent = client.onevent;
    client.onevent = function ( packet ) {
        let args = packet.data || [];
        onevent.call( this, packet );
        packet.data = [ "*" ].concat( args );
        onevent.call( this, packet );
    };

    client.messageCounter = ( function() {
        client.messagesLastSecond = 0;
        setInterval( function() { 
            client.messagesLastSecond = 0
        }, 1000 );        
    } )();
    client.messagesUntilSpam = 0;

    if ( client.request.headers['x-bot-stream-key'] !== undefined &&
         client.request.headers['x-bot-stream-room'] !== undefined &&
         client.request.headers['x-bot-name'] !== undefined ) {

        checkBotAuth( client, function ( err, result ) {
            if ( err ) {
                logger.log( `ERROR: Bot failed to auth` );
                logger.log( `ERROR: ${err.message}` );
                client.emit( 'SERVER_ERROR', err.message );
                client.authenticated = false;
            } else {
                if ( result.success ) {            
                    client.authenticated = true;
                    client.bot = true;
                    client.nickname = result.username;
                } else {
                    logger.log( `ERROR: Bot failed to auth` );
                    logger.log( `ERROR: ${err.message}` );
                    client.emit( 'SERVER_ERROR', err.message );
                    client.authenticated = false;               
                }        
            }
            
            //that was moved here recently with no idea on performance
            //if you put these out of checkAuth, you risk using undefined nickname
            clients[client.id] = client;
            next();            
        } );
    } else {
        checkAuth( client, function ( err, result ) {
            if ( err ) {
                logger.log( `ERROR: Failed to auth` );
                logger.log( `ERROR: ${err.message}` );
                client.authenticated = false;
            } else {
                if ( result.success ) {            
                    client.authenticated = true;
                    client.nickname = result.username;
                } else {
                    client.authenticated = false;
                }        
            }
            
            //that was moved here recently with no idea on performance
            //if you put these out of checkAuth, you risk using undefined nickname
            clients[client.id] = client;
            next();
        } );
    }
}

function onClientConnection( client ) {
    client.ip = stripIPV6( client.request.connection.remoteAddress );
    if ( client.ip === undefined ) {
        client.ip = "IP_UNKNOWN";
    }
    logger.log( client.ip + ': Connected' );
    
    initClientHandlers( client );
}

function initClientHandlers( client ) {
    client.on( 'disconnect', onClientDisconnect( client ) );
    client.on( '*', checkIfClientTryingToDOS( client ) ); // '*' event is defined in beforeClientConnection
    client.on( 'CLIENT_ROOM_JOIN_REQUEST', onClientRoomJoinRequiest( client ) );
    client.on( 'CLIENT_ROOM_LOGIN_REQUEST', onClientLoginRequest( client ) );
    client.on( 'CLIENT_RECENT_MESSAGES_REQUEST', onClientRecentMessagesRequest( client ) );
    client.on( 'CLIENT_MESSAGE', onClientMessage( client ) );
}

function checkAuth( client, callback ) {
    let handshakeData = client.request;
    let sessionid;
    if ( handshakeData.headers.cookie !== undefined ) {
        sessionid = cookieParser.parse( handshakeData.headers.cookie ).sessionid;
    }

    if ( sessionid !== undefined ) {
        let query = `sessionid=${sessionid}`;
        let options = {
            host: config.get( 'streamHost' ),
            port: config.get( 'streamWebPort' ),
            path: config.get( 'streamWebURL' ) + '/service/auth/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': query.length
            }
        };

        let req = http.request( options, function ( res ) {
            res.setEncoding( 'utf8' );
            res.on( 'data', function ( data ) {
                try {
                    data = JSON.parse( data );
                    callback( null, data );
                } catch ( err ) {
                    callback( err );
                }
            });
        });

        req.on( 'error', function( err ) {
            logger.log( `ERROR: ${err.message}` );
        });
        
        req.write( query );
        req.end();
    } else {
        callback( null, { success: false } );
    }
    
    clients[client.id] = client;
}

function checkBotAuth( client, callback ) {
    let streamKey = client.request.headers['x-bot-stream-key'];
    let roomName = client.request.headers['x-bot-stream-room'];
    let botName = client.request.headers['x-bot-name'];

    let query = `stream_key=${streamKey}&room_name=${roomName}&bot_name=${botName}`;
    let options = {
        host: config.get( 'streamHost' ),
        port: config.get( 'streamWebPort' ),
        path: config.get( 'streamWebURL' ) + '/service/botauth/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': query.length
        }
    };

    let req = http.request( options, function ( res ) {
        res.setEncoding( 'utf8' );
        res.on( 'data', function ( data ) {
            try {
                data = JSON.parse( data );
                if ( data.success ) {
                    callback( null, data );
                } else {
                    callback( new Error( data.error ) );
                }
            } catch ( err ) {
                callback( err );
            }
        });
    });

    req.on( 'error', function( err ) {
        logger.log( `ERROR: ${err.message}` );
    });
    
    req.write( query );
    req.end();
}

function fillClientInfo( client, callback ) {
    let query = `room=${client.room}&username=${client.nickname}`;
    let options = {
        host: config.get( 'streamHost' ),
        port: config.get( 'streamWebPort' ),
        path: config.get( 'streamWebURL' ) + '/service/chatuserinfo/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': query.length
        }
    };

    let req = http.request( options, function ( res ) {
        res.setEncoding( 'utf8' );
        res.on( 'data', function ( data ) {
            try {
                data = JSON.parse( data );
            } catch ( err ) {
                logger.log( "ERROR: Failed to receive chat user info" );
                logger.log( `ERROR: ${err.message}` );
                callback( err );
            }
            
            client.owner = data.owner;
            client.moderator = data.moderator;
            client.banned = data.banned;
            client.ban_expiry_date = data.ban_expiry_date;
            client.ban_reason = data.ban_reason;
            callback( null, data );            
        });
    });
        
    req.on( 'error', function( err ) {
        logger.log( `ERROR: ${err.message}` );
    });

    req.write( query );
    req.end();
}

function getRoomMOTD( roomName, callback ) {
    let data = `room=${roomName}`;
    let options = {
        host: config.get( 'streamHost' ),
        port: config.get( 'streamWebPort' ),
        path: config.get( 'streamWebURL' ) + '/service/chatmotd/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': data.length
        }
    };

    let req = http.request( options, function ( res ) {
        res.setEncoding( 'utf8' );
        res.on( 'data', function ( data ) {
            try {
                data = JSON.parse( data ); 
                callback( null, data );
            } catch ( err ) {
                logger.log( `ERROR: Failed to get chat MOTD` );
                logger.log( `ERROR: ${err.message}` );
                callback( err );                
            }
        });
    });

    req.on( 'error', function( err ) {
        logger.log( `ERROR: ${err.message}` );
    });

    req.write( data );
    req.end();
}

function checkIfClientTryingToDOS( client ) {
    return function() {
        // client.messagesLastSecond++;
        // if ( client.messagesLastSecond > 12 ) {
        //     logger.log( client.ip + ': POTENTIAL DOS ATTEMPT' );
        //     client.disconnect();
        // }
    }
}

function onClientDisconnect( client ) {
    return function() {
        logger.log( client.ip + ': Disconnected' );
        delete clients[client.id];

        let isStillInChatRoom = clientNicknameInRoom( client.nickname, client.room );
        if ( !isStillInChatRoom ) {
            io.to( client.room ).emit( 'SERVER_CLIENT_DISCONNECTED', client.nickname );
        }
    }
}

function onClientRoomJoinRequiest( client ) {
    return function( roomName ) {

        if ( typeof roomName !== 'string' ) {
            client.emit( 'SERVER_ERROR', 'Некорректное сообщение' );
            return;
        }
        
        // client issuing join request for the second time? 
        if ( client.room !== undefined ) {
            // don't do anything if he's already connected to this room
            if ( client.room === roomName ) {
                return;
            }
            // but disconnect from his current room if it's
            // different to the one he's switching to 
            client.leave( client.room );
        }

        // client got into the new room
        client.room = roomName;

        async.series( {
            emitMOTD: function( callback ) {
                getRoomMOTD( roomName, function( err, data ) {
                    if ( err ) {
                        callback( err );
                    } else {
                        if ( data.success ) {    
                            if ( data.chat_motd.length > 0 ) {
                                client.emit( 'SERVER_INFO_MESSAGE', data.chat_motd );
                            }
                        }
                        callback( null );
                    }
                } );
            },
            fillClientInfo: function( callback ) { // TODO: Move to login function
                fillClientInfo( client, function( err ) {
                    if ( err ) {
                        callback( err );
                    } else {
                        callback( null );
                    }
                } );                  
            },
            processJoin: function( callback ) {
                client.join( roomName );
                client.emit( 'SERVER_CLIENTS_LIST', getClientsInRoomForSend( roomName ) );
                client.emit( 'SERVER_ROOM_JOIN_SUCCESS', client.authenticated );
                logger.log( "[" + roomName + "] " + client.ip + ": Joined");

                callback( null );
            }
        }, function() {
        } ); 
    }
}

function onClientLoginRequest( client ) { 
    return function( roomName ) {
        if ( typeof roomName !== 'string' ) {
            client.emit( 'SERVER_ERROR', 'Некорректное сообщение' );
            return;
        }
    
        if ( client.authenticated ) {
            client.emit( 'SERVER_LOGIN_SUCCESS', client.nickname );
            logger.log( "[" + roomName + "] " + client.ip + " " + client.nickname + ": Logged in" );

            //the purpose of this variable is dumb
            let alreadyInChatRoom = clientNicknameInRoom( client.nickname, roomName );
            
            if ( !alreadyInChatRoom ) {
                io.to( client.room ).emit( 'SERVER_CLIENT_CONNECTED', getClientInfo( client ) );
            }
            client.loggedIn = true;
        } else {
            client.emit( 'SERVER_LOGIN_FAILURE', client.nickname );
            return;
        }
        
        if ( client.moderator ) {
            io.to( client.room ).emit( 'SERVER_MODERATOR', client.nickname );
        }
        
        if ( client.banned ) {
            let ban_message = makeBanMessage( client.ban_reason, client.ban_expiry_date );
            
            client.emit( 'SERVER_ERROR', ban_message );
            
            io.to( client.room ).emit( 'SERVER_BANNED', client.nickname );
        }         
    }
}

function onClientRecentMessagesRequest( client ) {
    return function( room ) {
        if ( typeof room !== 'string' ) {
            client.emit( 'SERVER_ERROR', 'Некорректное сообщение' );
            return;
        }

        if ( clientMessages[room] !== undefined ) {
            client.emit( 'SERVER_RECENT_MESSAGES', clientMessages[room] );
        }
    }
}

function onClientMessage( client ) {
    return function ( message ) {

        if ( typeof message !== 'string' ) {
            client.emit( 'SERVER_ERROR', 'Некорректное сообщение' );
            return;
        }

        if ( !client.nickname ) { //huh
            logger.log( client.ip + ": Tried to send a message without login" );
            return;
        }

        async.series( {
            auth: function( callback ) {
                // bots are authenticated on connection
                if ( client.bot ) {
                    checkBotAuth( client, function ( err ) {
                        if ( err ) {
                            client.emit( 'SERVER_ERROR', err.message );
                            logger.log( "[" + client.room + "] " + client.ip + " " + client.nickname + ": Bot tried to send a message without authentication" );
                            removeClientFromAllRooms( client );
                            client.disconnect();
                            return callback( err );
                        }

                        callback( null );
                    } ); 
                } else {
                    checkAuth( client, function ( err, result ) {
                        if ( err ) {
                            return callback( err );
                        }

                        if ( !result.success ) {            
                            client.authenticated = false;
                            logger.log( "[" + client.room + "] " + client.ip + " " + client.nickname + ": Tried to send a message without session" );
                            client.emit( 'SERVER_ERROR', "Для участия в чате необходимо войти на сайт" );
                            removeClientFromAllRooms( client );
                        }

                        callback( null );
                    } ); 
                }               
            },
            fillClientInfo: function( callback ) {
                if ( !client.authenticated ) {
                    return callback( null );
                } 

                fillClientInfo( client, function( err ) {
                    if ( err ) {
                        callback( err );
                    } else {
                        callback( null );
                    }
                } );                
            },
            checkMessage: function( callback ) {
                if ( !client.authenticated ) {
                    return callback( null );
                }

                if ( client.banned ) {
                    let ban_message = makeBanMessage( client.ban_reason, client.ban_expiry_date ); 
                    
                    client.emit( 'SERVER_ERROR', ban_message );
                    io.to( client.room ).emit( 'SERVER_BANNED', client.nickname );
                    
                    return callback( null );
                }
                
                if ( message.length > 255 ) {
                    client.emit( 'SERVER_ERROR', "Длина сообщения превышает 255 символов" );
                    logger.log( "[" + client.room + "] " + client.ip + " " + client.nickname + ": Message is too large" );
                    
                    return callback( null );
                }

                // let spamTimeout;
                // if ( client.messagesUntilSpam > 3 ) {
                //     spamTimeout = 2000;
                // } else {
                //     spamTimeout = 4500;
                // }

                // setTimeout( function () {
                //     client.messagesUntilSpam--;
                // }, spamTimeout );

                // client.messagesUntilSpam++;
                // if ( client.messagesUntilSpam > 3 ) { //huh
                //     client.emit( 'SERVER_ERROR', "Хватит флудить" );
                    
                //     return callback( null );
                // }

                //trim-check
                if ( message.trim().length === 0 ) {
                    return callback( null );
                }

                if ( !Array.isArray( clientMessages[client.room] ) ) {
                    clientMessages[client.room] = [];
                }

                clientMessages[client.room].push( {
                    nickname: client.nickname,
                    message: message,
                    owner: client.owner,
                    moderator: client.moderator,
                    banned: client.banned,
                    bot: client.bot,
                    timestamp: new Date().valueOf()
                } ); 
                     
                logger.log( "[" + client.room + "] " + client.ip + " " + client.nickname + ": " + message );

                io.to( client.room ).emit( 'SERVER_CLIENT_MESSAGE', {
                    nickname: client.nickname,
                    message: message,
                    owner: client.owner,
                    moderator: client.moderator,
                    bot: client.bot,
                    banned: client.banned
                } );
            }
        }, function() {
        } )
        
    }
}

function getClientsList() {
    let clientsList = [];
    for ( let i = 0 ; i < Object.keys( clients ).length ; i++ ) {
        clientsList.push( {
            "ip": clients[ Object.keys( clients )[i] ].ip, 
            "authenticated": clients[ Object.keys( clients )[i] ].authenticated,
            "sessionid": clients[ Object.keys( clients )[i] ].sessionid,
            "nickname": clients[ Object.keys( clients )[i] ].nickname,
            "room": clients[ Object.keys( clients )[i] ].room,
        });
    }

    return clientsList;
}

function printClients() {
    console.log( getClientsList() );
}

// TODO: Related to sio, may be gone
function massBroadcast( message ) {
    for ( let i = 0 ; i < Object.keys( clients ).length ; i++ ) {
        let client = clients[ Object.keys( clients )[i] ];
        client.emit( 'SERVER_ERROR', message );
    }
}

function getClientInRoom( nickname, roomName ) {
    if ( io.sockets.adapter.rooms[roomName] === undefined ) {
        return undefined;
    }

    let roomClients = Object.keys( io.sockets.adapter.rooms[roomName].sockets );

    for ( let i = 0 ; i < roomClients.length ; i++ ) {
        let client = clients[roomClients[i]];

        if ( client !== undefined ) {
            if ( client.nickname !== undefined && client.loggedIn === true && client.nickname == nickname ) {
                return client;
            }
        } 
    }

    return undefined;
}

function clientNicknameInRoom( clientNickname, roomName ) {
    if ( io.sockets.adapter.rooms[roomName] === undefined ) {
        return false;
    }

    let roomClients = Object.keys( io.sockets.adapter.rooms[roomName].sockets );

    let clientNames = [];
    for ( let i = 0 ; i < roomClients.length ; i++ ) {
        let client = clients[roomClients[i]];
        if ( client !== undefined ) {
            if ( client.nickname !== undefined && client.loggedIn === true ) {
                clientNames.push( client.nickname );
            }
        } 
    }

    return clientNames.indexOf( clientNickname ) != -1;
}

function getClientsInRoomForSend( roomName ) {
    if ( io.sockets.adapter.rooms[roomName] === undefined ) {
        return;
    }
    
    let roomClients = Object.keys( io.sockets.adapter.rooms[roomName].sockets );
    
    let clientNames = [];
    for ( let i = 0 ; i < roomClients.length ; i++ ) {
        let client = clients[roomClients[i]];
        if ( client !== undefined ) {
            if ( client.nickname !== undefined && client.loggedIn === true ) {
                clientNames.push( getClientInfo( client ) );
            }
        }
    }
    
    let flags = {};
    let clientNamesSet = clientNames.filter( function( entry ) {
        if ( flags[ entry.nickname ] ) {
            return false;
        }
        flags[ entry.nickname ] = true;
        return true;
    });

    return clientNamesSet;
}

function getClientInfo( client ) {
    return {
        nickname: client.nickname,
        owner: client.owner,
        moderator: client.moderator,
        banned: client.banned,
        bot: client.bot
    };
}

function removeClientFromAllRooms( client ) {
    let roomList = io.sockets.adapter.rooms;
    for ( let i = 0 ; i < Object.keys( roomList ).length ; i++ ) {
        let roomName = Object.keys( roomList )[i];
        if ( clientNicknameInRoom( client.nickname, roomName ) ) {
            io.to( roomName ).emit( 'SERVER_CLIENT_DISCONNECTED', client.nickname );
        }
    }
}

function makeBanMessage( banReason, expiryDate ) {
    let banMessage = "Вы забанены";
    if ( expiryDate !== null ) {
        banMessage += " до " + expiryDate;
    } else {
        banMessage += " на неопределенный срок";
    }
    
    if ( banReason !== null ) {
        if ( banReason.length > 0 ) {
            banMessage += " - " + banReason;
        } else {
            banMessage += " - причина не указана";
        }
    } else {
        banMessage += " - причина не указана";
    }

    return banMessage;
}

function stripIPV6( ipv6String ) {
    if ( typeof ipv6String !== 'string' ) {
        return ipv6String;
    }
    var substringToRemove = "::ffff:";
    if ( ipv6String.indexOf( substringToRemove ) !== -1 ) {
        return ipv6String.replace( substringToRemove, "" );
    } else {
        return ipv6String;
    }
};