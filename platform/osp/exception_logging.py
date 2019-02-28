from django.conf import settings
from datetime import datetime
import sys, traceback
import codecs

class ExceptionLoggingMiddleware( object ):
	def process_exception( self, request, exception ):
		if settings.OSP_EXCEPTION_LOG is not None:
			exc_log = codecs.open( settings.OSP_EXCEPTION_LOG, "a+", 'utf-8' )
			exc_log.write( "=======================[{0}]=======================\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ) ) )
			exc_log.write( "Reason: {0}\n".format( str( exception ) ) )
			traceback.print_exc( file = exc_log )
			exc_log.write( "\n\n" )
			exc_log.close()