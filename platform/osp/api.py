import xml.etree.ElementTree as ET
import hashlib
import time
import urllib.request
import urllib.error
import json
from ipware.ip import get_ip
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from osp.models import UserData, UserFollow, UserChannelHelper, ChatModerator, ChatBan

#omit the proxy
proxy_handler = urllib.request.ProxyHandler( {} )
opener = urllib.request.build_opener( proxy_handler )
urllib.request.install_opener( opener )

def get_stream_list( specific_stream_name = None, include_followers = True, include_ip = False, include_hidden = False, include_bitrate = False ):
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

		if specific_stream_name is not None and stream_name != specific_stream_name:
			continue

		active = stream.find( 'publishing' ) is not None
		if not active:
			continue

		try:
			user_data = UserData.objects.only( 'stream_description', 'stream_hidden' ).get( user__username = stream_name )
		except User.DoesNotExist:
			continue
		except UserData.DoesNotExist:
			continue

		hidden = user_data.stream_hidden
		if hidden and not include_hidden:
			continue

		# no incoming bytes
		broken = int( stream.find( 'bw_in' ).text ) == 0 and int( stream.find( 'time' ).text ) > 20000

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
			"broken": broken
		}

		if include_followers:
			stream_info['followers'] = get_follower_count( username = stream_name )

		if include_ip:
			stream_info['ip'] = streamer_ip

		if include_bitrate:
			stream_info['bitrate'] = int( stream.find( 'bw_video' ).text )

		streams.append( stream_info )

	return streams


def get_stream_info( stream_name ):
	stream_info = get_stream_list( specific_stream_name = stream_name, include_hidden = True )
	if len( stream_info ) <= 0:
		return get_inactive_stream_info( stream_name )

	# get_stream_info_object always returns an array,
	# but in this case it always has one stream_info
	# and has to be converted to an object
	return stream_info[0]

def get_inactive_stream_info( stream_name ):
	try:
		user_data = UserData.objects.only( 'stream_description', 'stream_hidden' ).get( user__username = stream_name )
	except UserData.DoesNotExist:
		return {}

	name = stream_name
	description = user_data.stream_description
	hidden = user_data.stream_hidden
	viewers = 0
	active = False
	followers = get_follower_count( username = stream_name )

	stream_info = {
		"name" : name,
		"description" : description,
		"hidden": hidden,
		"viewers" : viewers,
		"active" : active,
		"followers": followers,
		"broken": False
	}

	return stream_info

def get_user_info( username ):
	try:
		user_data = UserData.objects.get( user__username = username )
	except UserData.DoesNotExist:
		return {}

	name = username
	avatar = user_data.avatar
	profile = reverse( 'osp:profile', args = [name] )
	user_object = {
		"name" : name,
		"avatar" : avatar.url,
		"profile" : profile
	}

	return user_object

def get_stream_list_following( username, include_ip = False, include_followers = False ):
	follow_list = []
	for follow in get_follow_list( username ):
		follow_list.append( follow['name'] )

	streams = get_stream_list( include_followers = False, include_ip = include_ip )
	for stream in list( streams ):
		if stream['name'] not in follow_list:
			streams.remove( stream )

	return streams

def get_follow_list( username ):
	follow_list = []
	try:
		user = User.objects.get( username = username )
	except User.DoesNotExist:
		return follow_list

	user_follow = UserFollow.objects.filter( user_id = user.id )

	for follow in user_follow:
		follow_user = User.objects.get( id = follow.follow_user_id )
		follow_list.append( get_user_info( follow_user.username ) )

	return follow_list

def get_follower_list( username ):
	follower_list = []
	try:
		user = User.objects.get( username = username )
	except User.DoesNotExist:
		return follower_list

	user_follow = UserFollow.objects.filter( follow_user_id = user.id )

	for follow in user_follow:
		follower_user = User.objects.get( id = follow.follow_user_id )
		follower_list.append( get_user_info( follower_user.username ) )

	return follower_list

def get_follower_count( username = None, only_active_followers = True, user_id = None ):
	if user_id is not None:
		return UserFollow.objects.filter( follow_user = user_id ).count()

	if username is not None:
		if only_active_followers:
			follows = User.objects.filter(
				userfollow__follow_user__username = username,
				userdata__last_activity_date__gt = datetime.now() - timedelta( days = settings.OSP_DAYS_UNTIL_USER_CONSIDERED_INACTIVE )
			).count()
			return follows
		else:
			return UserFollow.objects.filter( follow_user__username = username ).count()

	return 0

def is_following( username, targetname ):
	try:
		user_follow = UserFollow.objects.get( user__username = username, follow_user__username = targetname )
	except UserFollow.DoesNotExist:
		return False

	return True

# TODO: get rid of these dumb things, we're not supposed to bash database here.
# already fetched data should be going directly to the template

#functions below are related to services but I decided not to make separate file
#dashboard_link argument is dumb and pollutes the template
def get_user_list_element( username, delete_allowed = False, show_ban_date = False, ban_date = None, dashboard_link = False, tooltip = None ):
	try:
		user = User.objects.get( username = username )
		user_data = UserData.objects.get( user_id = user.id )
	except User.DoesNotExist:
		return {}

	if ban_date is not None:
		ban_date = ban_date.strftime( "%Y-%m-%d %H:%M:%S" )
	else:
		ban_date = "Вечно"

	return render_to_string( 'user_list_element.html', { 'user': user_data, 'delete_allowed': delete_allowed, 'show_ban_date': show_ban_date, 'ban_date': ban_date, 'dashboard_link': dashboard_link, 'tooltip': tooltip } )

def get_user_ban_table_element( ban ):
	try:
		user_data = UserData.objects.get( user_id = ban.banned_user_id )
	except UserData.DoesNotExist:
		return {}

	if ban.expiry_date is not None:
		ban.expiry_date = ban.expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )

	return render_to_string( 'user_ban_table_element.html', { 'user': user_data, 'ban': ban } )

def has_dashboard_access( username, targetname ):
	try:
		user = User.objects.get( username = username )
		user_id = user.id
		target_id = User.objects.get( username = targetname ).id
	except User.DoesNotExist:
		return False

	if user.is_superuser:
		return True

	if user_id == target_id:
		return True

	try:
		user_channel_helper = UserChannelHelper.objects.get( channel_user_id = target_id, helper_user_id = user_id )
		return True
	except UserChannelHelper.DoesNotExist:
		pass

	try:
		user_chat_moderator = ChatModerator.objects.get( chat_user_id = target_id, moderator_user_id = user_id )
		return True
	except ChatModerator.DoesNotExist:
		pass

	return False

def generate_stream_key( username ):
	try:
		user = User.objects.get( username = username )
		user_data = UserData.objects.get( user_id = user.id )

		info = "cacti:" + user.username + str( time.time() )
		info = info.encode('utf-8')

		sha1hash = hashlib.sha1()
		sha1hash.update( info )

		user_data.stream_key = sha1hash.hexdigest()
		user_data.save()

		return sha1hash.hexdigest()

	except User.DoesNotExist:
		pass

def remove_expired_chat_bans( user_id = None, chat_user_id = None ):
	if user_id is not None:
		chat_bans = ChatBan.objects.filter( banned_user = user_id )
	elif chat_user_id is not None:
		chat_bans = ChatBan.objects.filter( chat_user_id = chat_user_id )
	else:
		chat_bans = ChatBan.objects

	chat_bans = chat_bans.filter( expiry_date__lt = datetime.now() )

	for chat_ban in chat_bans:
		send_message_to_chat_server( 'UNBAN_NOTIFY', json.dumps( {
			"nickname": chat_ban.banned_user.username,
			"room": chat_ban.chat_user.username
		} ) )
		chat_ban.delete()

#RTMP control does not accept URLencoded name
def drop_from_streaming( name = None, ip = None ):
	if name is not None:
		try:
			url = settings.OSP_RTMP_SERVER_CONTROL_ADDRESS + "drop/publisher?app=live&name=%s" % 'http://' + name
			urllib.request.urlopen( url )
			return
		except urllib.error.HTTPError:
			pass

	if ip is not None:
		try:
			url = settings.OSP_RTMP_SERVER_CONTROL_ADDRESS + "drop/publisher?app=live&addr=%s" % ip
			urllib.request.urlopen( url )
			return
		except urllib.error.HTTPError:
			pass

def hide_stream( request, username ):
	ip = get_ip( request )
	if not ip in settings.OSP_IP_ALLOWED_TO_QUICK_HIDE_STREAMS:
		return False

	try:
		user = User.objects.get( username = username )
		user_data = UserData.objects.get( user_id = user.id )

		user_data.stream_hidden = True
		user_data.save()

		return True

	except User.DoesNotExist:
		return False

# I don't like the fact that it has to be a new connection each time
from socketIO_client import SocketIO
servicePort = 8268
host = ""

def send_message_to_chat_server( header, message ):
	try:
		io = SocketIO( host, servicePort, wait_for_connection = False )
		io.emit( header, message )
	except:
		pass
