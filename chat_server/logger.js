const config = require( 'config' );
const fs = require( 'fs' );
const moment = require( 'moment' );
const path = require( 'path' );

let logFile = null;

function generateLogName() {
    //with datestamp
    return "chat_log_" + moment().format( "YYYY_MM_DD-HH_mm_ss" ) + ".log";
}

module.exports.init = function() {
    let logPath = config.get( 'logPath' );

    if ( logPath === null ) {
        return;
    }

    let logName = generateLogName();
    let logMonthFolder = moment().format( "YYYY_MM" );
    let logMonthFolderPath = path.join( logPath, logMonthFolder );
    if ( !fs.existsSync( logMonthFolderPath ) ){
        fs.mkdirSync( logMonthFolderPath );
    }
	let logFullPath = path.join( logMonthFolderPath, logName );
    logFile = fs.createWriteStream( logFullPath, { 'flags': 'a' } );
}

module.exports.log = function( string ) {
    let logMessage = "[" + moment().format( "YYYY-MM-DD HH:mm:ss" ) + "] " + string;
	if ( logFile !== null ) {
		logFile.write( logMessage + "\n" );
	}
    console.log( logMessage );
}

module.exports.close = function() {
    if ( logFile !== null ) {
        logFile.close();
    }
}