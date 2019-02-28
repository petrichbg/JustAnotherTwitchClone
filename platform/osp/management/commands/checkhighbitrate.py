from django.core.management.base import BaseCommand
from osp.api import get_stream_list, drop_from_streaming

class Command( BaseCommand ):
	def handle( self, *args, **options ):
		for stream in get_stream_list( include_bitrate = True, include_hidden = True ):
			if ( stream['bitrate'] > 6000000 ):
				drop_from_streaming( stream['name'] )