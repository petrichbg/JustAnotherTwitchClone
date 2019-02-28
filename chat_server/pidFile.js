const config = require( 'config' );
const fs = require( 'fs' );

let pidFilePath = null;

module.exports.init = function() {
    pidFilePath = config.get( 'pidFilePath' );
    if ( pidFilePath === null ) {
        return;
    }
    fs.writeFile( pidFilePath, process.pid, function ( error ) {
        if ( error ) {
            console.log( error );
            return;
        }
    } );
}

module.exports.del = function() {
    if ( pidFilePath === null ) {
        return;
    }

    // unlink deletes file
	fs.unlinkSync( pidFilePath, function ( error ) {
		if ( error ) {
			console.log( error );
			return;
		}
	} );
}