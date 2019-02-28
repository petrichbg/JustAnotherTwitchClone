from django.core.management.base import BaseCommand
import urllib.request
import urllib.error
from django.conf import settings
import xml.etree.ElementTree as ET
from django.contrib.auth.models import User
from osp.models import UserData
from osp.api import get_follower_count
from osp.convenience import bleach_span
import json

class Command( BaseCommand ):
	def handle( self, *args, **options ):
		try:
			u = urllib.request.urlopen( settings.OSP_RTMP_SERVER_STAT_ADDRESS, timeout = 3 )
		except urllib.error.URLError:
			return None

		rtmp_info = ET.parse( u )
		u.close()

		if rtmp_info is not None:
			rtmp_info = rtmp_info.getroot()
		else:
			return []

		streams = []

		for stream in rtmp_info.findall( './/stream' ):
			#since all routing on RTMP side results in all meaningful stream names to be like 'http://NAME', I need to extract the NAME this way
			#I don't know how to achieve RTMP routing so we could get nice names instead of this or random values by default
			stream_name = stream.find( 'name' ).text.rsplit( '/', 1 )[1]

			active = stream.find( 'publishing' ) is not None
			if not active:
				continue

			try:
				user = User.objects.get( username = stream_name )
				user_data = UserData.objects.get( user_id = user.id )
			except User.DoesNotExist:
				continue

			hidden = user_data.stream_hidden

			#add clients who are not publishing (streamers) to set, to ensure that there are only unique clients.
			client_list = stream.findall( 'client' )
			ip_set = set()
			streamer_ip = None
			for client in client_list:
				publishing = client.find( 'publishing' )
				ip = client.find( 'address' ).text
				if publishing is None:
					ip_set.add( ip )
				else:
					streamer_ip = ip

			ip_set.discard( streamer_ip )

			name = stream_name
			description = user_data.stream_description
			viewers = len( ip_set )

			stream_info = {
				"name" : name,
				"description" : description,
				"hidden": hidden,
				"viewers" : viewers,
				"active" : active,
			}

			stream_info['followers'] = get_follower_count( name )

			stream_info['ip'] = streamer_ip

			stream_info['description'] = bleach_span( stream_info['description'] )

			streams.append( stream_info )

		file = open( settings.OSP_STREAM_LIST_PATH, 'w' )
		file.write( json.dumps( streams ) )
