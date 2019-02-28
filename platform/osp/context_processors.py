from django.conf import settings
from django.db import connection
from datetime import datetime, timedelta
from ipware.ip import get_ip
from osp.models import UserNotification, UserFollowNotification

last_update_date = datetime(
	year = 2016,
	month = 12,
	day = 2,
	hour = 7
)

last_hotfix_update = datetime(
	year = 2017,
	month = 7,
	day = 28,
	hour = 8
)

hold_update_note_for_hours = 48
hold_hotifx_note_for_hours = 48

def update_hot( request ):
	if last_update_date + timedelta( hours = hold_update_note_for_hours ) >= datetime.now():
		return_value = "hot"
	else:
		return_value = ""

	return {
		'update_hot': return_value
	}

def hotfix_hot( request ):
	if last_hotfix_update + timedelta( hours = hold_hotifx_note_for_hours ) >= datetime.now():
		return_value = "hot"
	else:
		return_value = ""

	return {
		'hotfix_hot': return_value
	}

def notifications_hot( request ):
	return_value = ""

	if request.user.is_authenticated():
		if UserFollowNotification.objects.filter( user = request.user, has_been_read = False ).exists():
			return_value = "hot"

		elif UserNotification.objects.filter( user = request.user, has_been_read = False ).exists():
			return_value = "hot"

	return { 'notifications_hot': return_value }

def is_user_banned( request ):
	if request.user.is_authenticated():
		ip = get_ip( request )

		with connection.cursor() as cursor:
			query = """
			SELECT COUNT( * ) > 0 AS has_bans
			FROM (
				SELECT
					id
				FROM osp_stream_publish_ban
				WHERE banned_ip = '{1}' AND now() < expiry_date AND NOT lifted

				UNION

				SELECT
					id
				FROM osp_stream_publish_user_ban
				WHERE user_id = {0} AND now() < expiry_date AND NOT lifted

				UNION

				SELECT
					id
				FROM osp_stream_play_ban
				WHERE banned_ip = '{1}' AND now() < expiry_date AND NOT lifted

				UNION

				SELECT
					id
				FROM osp_chat_ban_ip
				WHERE banned_ip = '{1}' AND now() < expiry_date AND NOT lifted

				UNION

				SELECT
					id
				FROM osp_chat_ban_user
				WHERE user_id = {0} AND now() < expiry_date AND NOT lifted
			) t
			""".format( request.user.id, ip )

			cursor.execute( query )
			result = bool( cursor.fetchall()[0][0] )

			return { 'is_user_banned': result }

	return { 'is_user_banned': False }