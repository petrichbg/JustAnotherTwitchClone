import sys
import json

argv = sys.argv
if ( len( argv ) <= 1 ):
	sys.exit()

from socketIO_client import SocketIO

servicePort = 8268
host = ""
message = sys.argv[1]

io = SocketIO( host, servicePort )

if len( argv ) >= 3:
	room = sys.argv[2]
	io.emit( "CHANNEL_MESSAGE", json.dumps( { 'message': message, 'room': room } ) )
else:
	io.emit( "MASS_BROADCAST", message )

print( 'Mass broadcast: ' + message )