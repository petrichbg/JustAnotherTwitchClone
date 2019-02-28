from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.views.decorators.csrf import csrf_exempt
from django.template.context_processors import csrf
from django.db import IntegrityError, connection
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.views.static import serve
from ipware.ip import get_ip
import user_agents
from osp.forms import RegisterForm, LoginForm, UserSettingsProfileForm, UserSettingsChangeNameForm, DashboardStreamForm
from osp.models import UserData, UserFollow, UserChannelHelper, UserNameChange, UserNotification, UserFollowNotification, ChatBan, ChatBanIP, ChatBanUser, ChatModerator, StreamPublishBan, StreamPublishUserBan, StreamPlayBan
from osp.api import get_stream_info, get_user_info, get_stream_list, get_stream_list_following, get_follow_list, get_follower_list, get_follower_count, is_following, get_user_list_element, get_user_ban_table_element, has_dashboard_access, generate_stream_key, drop_from_streaming, remove_expired_chat_bans, get_inactive_stream_info, hide_stream, send_message_to_chat_server
from osp.convenience import generate_page_title, parse_markdown, append_stream_log, symlink_forced
from datetime import datetime, timedelta

import json
import re
import os
import random
import urllib.request
import urllib.error

#omit the proxy
proxy_handler = urllib.request.ProxyHandler( {} )
opener = urllib.request.build_opener( proxy_handler )
urllib.request.install_opener( opener )

# Create your views here.
class IndexView( TemplateView ):
	template_name = 'index.html'

	def get_context_data( self, **kwargs ):
		context = super( IndexView, self ).get_context_data( **kwargs )
		context['navbar_main_active'] = "active"
		context['page_title'] = generate_page_title( "" )

		return context

class RulesView( TemplateView ):
	template_name = 'rules.html'

	def get_context_data( self, **kwargs ):
		context = super( RulesView, self ).get_context_data( **kwargs )
		context['navbar_rules_active'] = "active"
		context['page_title'] = generate_page_title( "Правила и замечания о ресурсе" )
		return context

class HelpView( TemplateView ):
	template_name = 'help.html'

	def get_context_data( self, **kwargs ):
		context = super( HelpView, self ).get_context_data( **kwargs )
		context['navbar_help_active'] = "active"
		context['page_title'] = generate_page_title( "Помощь" )
		return context

class ChangeLogView( TemplateView ):
	template_name = 'changelog.html'

	def get_context_data( self, **kwargs ):
		context = super( ChangeLogView, self ).get_context_data( **kwargs )
		context['navbar_changelog_active'] = "active"
		context['page_title'] = generate_page_title( "История изменений" )
		return context

class UsersView( TemplateView ):
	template_name = 'users.html'
	template_name_chunk = 'users_chunk.html'

	def get( self, request, *args, **kwargs ):
		if request.is_ajax():
			context = self.get_context_data( **kwargs )
			return render( request, self.template_name_chunk, context )

		return render( request, self.template_name, self.get_context_data( **kwargs ) )

	def get_context_data( self, **kwargs ):
		context = super( UsersView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Пользователи" )
		page = self.request.GET.get( 'page' )
		username_filter = self.request.GET.get( 'username' )
		show_active_users_string = self.request.GET.get( 'showActiveUsers' )
		show_active_users = show_active_users_string == "true"
		if page is None:
			page = 1
		else:
			page = int( page )

		if show_active_users:
			active_users_filter = "d.last_activity_date > '{0}'".format(
				( datetime.now() - timedelta( days = settings.OSP_DAYS_UNTIL_USER_CONSIDERED_INACTIVE ) ).strftime( "%Y-%m-%d %H:%M:%S" )
			)
			inner_active_users_filter = "WHERE " + active_users_filter
			outer_active_users_filter = "AND " + active_users_filter
		else:
			inner_active_users_filter = ""
			outer_active_users_filter = ""

		# This should be django querySet instead, or made with some kind of SQL query builder.
		# Formatting query with WHERE clauses is not fun.
		with connection.cursor() as cursor:
			query = '''
				SELECT
					u.username,
					COALESCE( f.count, 0 ) AS count,
					d.avatar
				FROM osp_user_data d

				INNER JOIN auth_user u ON d.user_id = u.id

				LEFT JOIN (
					SELECT follow_user_id, COUNT( follow_user_id ) as count FROM osp_user_follow f
					INNER JOIN osp_user_data d ON f.user_id = d.user_id
					{0}
					GROUP BY follow_user_id
				) f ON u.id = f.follow_user_id

				WHERE u.username LIKE '%{1}%' {2}

				ORDER BY count DESC

				LIMIT {3}, 30
			'''.format(
				inner_active_users_filter,
				username_filter,
				outer_active_users_filter,
				( page - 1 ) * 30
			)

			cursor.execute( query )
			users = list( cursor.fetchall() )

		stream_list = get_stream_list()
		for i in range( 0, len( users ) ):
			username = users[i][0]
			streaming = any( stream['name'] == username for stream in stream_list )
			stream_description = ""
			if streaming:
				stream_info = [ stream for stream in stream_list if stream['name'] == username ][0]
				streaming = stream_info['active'] and not stream_info['hidden']
				stream_description = stream_info['description']
			subscriber_count = users[i][1]
			avatar = "/pic/" + users[i][2]

			users[i] = {
				"username": username,
				"streaming": streaming,
				"stream_description": stream_description,
				"subscriber_count": subscriber_count,
				"avatar": avatar
			}

		context['navbar_users_active'] = "active"
		context['users'] = users
		context['has_next_page'] = True
		if len( users ) > 0:
			context['next_page'] = str( page + 1 )
			context['has_next_page'] = True
		else:
			context['next_page'] = ""
			context['has_next_page'] = False

		next_page_link_additions = ""
		if username_filter is not None:
			next_page_link_additions = next_page_link_additions + "&username="+username_filter
		if show_active_users:
			next_page_link_additions = next_page_link_additions + "&showActiveUsers=true"

		context['next_page_link_additions'] = next_page_link_additions

		return context

class StreamListView( TemplateView ):
	template_name = 'streams.html'
	template_name_chunk = 'streams_chunk.html'

	advice_list = [
		""
	]

	def get( self, request, *args, **kwargs ):
		if request.is_ajax():
			context = self.get_context_data( **kwargs )
			return render( request, self.template_name_chunk, context )

		return render( request, self.template_name, self.get_context_data( **kwargs ) )

	def get_context_data( self, **kwargs ):
		context = super( StreamListView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Стримы" )

		page = self.request.GET.get( 'page' )
		if page is None:
			page = 1

		stream_list = get_stream_list( include_ip = self.request.user.is_staff, include_followers = False )
		stream_list_follows = []

		# first show streams of people you're subscribed to, then other streams
		if self.request.user.is_authenticated():
			try:
				show_subscriptions_on_top = UserData.objects.get( user = self.request.user ).show_subscriptions_on_top
				if show_subscriptions_on_top:
					followings = UserFollow.objects.filter( user__username = self.request.user.username ).values_list( 'follow_user__username', flat = True )

					for i in range( len( stream_list ) - 1, -1, -1 ):
						stream = stream_list[i]
						if stream['name'] in followings:
							stream_list_follows.append( stream )
							stream_list.remove( stream )
			except UserData.DoesNotExist:
				pass

		#sort by viewers descending
		stream_list.sort( key = lambda x: x['viewers'], reverse = True )
		stream_list_follows.sort( key = lambda x: x['viewers'], reverse = True )

		stream_list = stream_list_follows + stream_list

		stream_list_paginator = Paginator( stream_list, 20 )
		context['stream_preview_location'] = settings.OSP_RTMP_SERVER_STREAM_PREVIEW_ADDRESS
		context['streams'] = stream_list_paginator.page( page )
		context['has_next_page'] = True
		try:
			context['next_page'] = stream_list_paginator.page( page ).next_page_number()
		except InvalidPage:
			context['has_next_page'] = False

		context['navbar_streams_active'] = "active"

		context['advice'] = random.choice( self.advice_list )

		ip = get_ip( self.request )
		if ip in settings.OSP_IP_ALLOWED_TO_QUICK_HIDE_STREAMS:
			context['admin_quick_hide'] = True

		return context

class DashboardView( TemplateView ):
	template_name = 'dashboard.html'
	def get_context_data( self, **kwargs ):
		context = super( DashboardView, self ).get_context_data( **kwargs )

		try:
			user = User.objects.get( username = kwargs[ 'username' ] )
			context['page_title'] = generate_page_title( "Панель - " + user.username )
			user_data = UserData.objects.get( user_id = user.id )
		except User.DoesNotExist:
			raise Http404( "Пользователя не существует" )

		if not has_dashboard_access( self.request.user.username, user.username ):
			raise PermissionDenied()

		if self.request.user.username == user.username:
			context['chat_moderation'] = True
		else:
			try:
				ChatModerator.objects.get( chat_user_id = user.id, moderator_user_id = self.request.user.id )
				context['chat_moderation'] = True
				context['active_tab_pane'] = "chatbansettings"
			except ChatModerator.DoesNotExist:
				pass

		if self.request.user.username == user.username or self.request.user.is_staff:
			context['chat'] = True
			context['stream_moderation'] = True
			context['active_tab_pane'] = "stream"
		else:
			try:
				UserChannelHelper.objects.get( channel_user_id = user.id, helper_user_id = self.request.user.id )
				context['chat'] = True
				context['stream_moderation'] = True
				context['active_tab_pane'] = "stream"
			except UserChannelHelper.DoesNotExist:
				pass

		context['home_dashboard'] = self.request.user.username == user.username
		context['user_bio'] = parse_markdown( user_data.bio )
		context['dashboard_stream_form'] = DashboardStreamForm(
			initial = {
				'stream_description': user_data.stream_description,
				'stream_chat_motd': user_data.stream_chat_motd,
				'stream_hidden': user_data.stream_hidden
			}
		)

		context['navbar_user_dashboard_active'] = 'active'

		dashboard_helper_list_html = []
		dashboard_helper_list = UserChannelHelper.objects.filter( channel_user_id = user.id )
		for dashboard_helper in dashboard_helper_list:
			dashboard_helper_name = User.objects.get( id = dashboard_helper.helper_user_id ).username
			dashboard_helper_list_html.append( get_user_list_element( dashboard_helper_name, delete_allowed = True ) )
		context['dashboard_helper_list'] = dashboard_helper_list_html

		available_dashboard_list_html = []
		available_dashboard_basic_list = UserChannelHelper.objects.filter( helper_user_id = user.id ).values_list( 'channel_user', flat = True )
		available_dashboard_moderation_list = ChatModerator.objects.filter( moderator_user_id = user.id ).values_list( 'chat_user', flat = True )
		available_dashboard_list = list( available_dashboard_basic_list ) + list( set( available_dashboard_moderation_list ) - set( available_dashboard_basic_list ) )
		for available_dashboard_id in available_dashboard_list:
			available_dashboard_name = User.objects.get( id = available_dashboard_id ).username
			available_dashboard_list_html.append( get_user_list_element( available_dashboard_name, delete_allowed = False, dashboard_link = True ) )
		context['available_dashboard_list'] = available_dashboard_list_html

		op_list_html = []
		op_list = ChatModerator.objects.filter( chat_user_id = user.id )
		for op in op_list:
			op_name = User.objects.get( id = op.moderator_user_id ).username
			op_list_html.append( get_user_list_element( op_name, delete_allowed = True ) )
		context['op_list'] = op_list_html

		remove_expired_chat_bans( chat_user_id = user.id )
		ban_list_html = []
		ban_list = ChatBan.objects.filter( chat_user_id = user.id )
		for ban in ban_list:
			ban_list_html.append( get_user_ban_table_element( ban ) )
		context['ban_list'] = ban_list_html

		context['stream_key'] = user_data.stream_key
		context['rtmp_server_address'] = settings.OSP_RTMP_SERVER_STREAM_APP_ADDRESS
		context['room_name'] = user.username

		return context

def dashboard_stream( request, username ):
	user = User.objects.get( username = username )
	user_data = UserData.objects.get( user_id = user.id )

	if not has_dashboard_access( request.user.username, username ):
		raise PermissionDenied()

	if request.method == 'POST':
		dashboard_stream_form = DashboardStreamForm( request.POST, instance = user_data )
		if dashboard_stream_form.is_valid():
			dashboard_stream_form.save( commit = False )
			dashboard_stream_form.user = request.user
			dashboard_stream_form.save()

			return HttpResponse()

	raise PermissionDenied()

class ChatView( TemplateView ):
	template_name = 'chat_popup.html'

	def get_context_data( self, **kwargs ):
		context = super( ChatView, self ).get_context_data( **kwargs )
		try:
			user = User.objects.get( username = kwargs[ 'username' ] )
			context['page_title'] = generate_page_title( "Чат - " + user.username )
			user_data = UserData.objects.get( user_id = user.id )
		except User.DoesNotExist:
			raise Http404( "Пользователя не существует" )

		context['chat'] = True
		context['hide_navbar'] = True
		context['room_name'] = user.username
		context['user_bio'] = parse_markdown( user_data.bio )

		remove_expired_chat_bans( chat_user_id = user.id )

		return context

class StreamView( TemplateView ):
	template_name = 'stream.html'

	def get_context_data( self, **kwargs ):
		context = super( StreamView, self ).get_context_data( **kwargs )
		try:
			user = User.objects.only( 'id', 'username' ).get( username = kwargs[ 'username' ] )
			context['page_title'] = generate_page_title( "Стрим - " + user.username )
			user_data = UserData.objects.get( user_id = user.id )
		except User.DoesNotExist:
			raise Http404( "Пользователя не существует" )

		context['chat'] = True
		context['username'] = user.username
		context['following'] = is_following( self.request.user.username, user.username )
		context['avatar_url'] = user_data.avatar.url
		context['user_bio'] = parse_markdown( user_data.bio )

		context['rtmp_server_address'] = settings.OSP_RTMP_SERVER_STREAM_APP_ADDRESS
		context['room_name'] = user.username

		context['dashboard_stream_form'] = DashboardStreamForm(
			initial = {
				'stream_description': user_data.stream_description,
				'stream_chat_motd': user_data.stream_chat_motd,
				'stream_hidden': user_data.stream_hidden
			}
		)

		context['using_legacy_player'] = settings.OSP_USE_LEGACY_PLAYER

		if self.request.user.username == user.username:
			context['navbar_user_profile_active'] = 'active'

		context['stream_settings_access'] = False
		if self.request.user.username == user.username or self.request.user.is_staff:
			context['stream_settings_access'] = True
		else:
			try:
				UserChannelHelper.objects.get( channel_user_id = user.id, helper_user_id = self.request.user.id )
				context['stream_settings_access'] = True
			except UserChannelHelper.DoesNotExist:
				pass

		remove_expired_chat_bans( user_id = self.request.user.id )

		if settings.OSP_PROVIDE_MOBILE_PLAYER:
			user_agent = user_agents.parse( self.request.META['HTTP_USER_AGENT'] )
			context['use_mobile_player'] = user_agent.is_mobile or user_agent.is_tablet

		return context

#horrible mess
class ProfileView( TemplateView ):
	template_name = 'profile.html'
	template_name_chunk = 'user_list_grid_chunk.html'

	PAGE_SIZE = 40

	def get( self, request, *args, **kwargs ):
		if request.is_ajax():
			page = request.GET.get( 'page' )
			list_type = request.GET.get( 'list' )
			username = kwargs[ 'username' ]

			if list_type == 'subscribed_to':
				subscribed_to_list_html = []
				subscribed_to_list = UserData.objects.filter(
					user__in = UserFollow.objects.filter( user__username = username ).values( 'follow_user' )
				).select_related()
				subscribed_to_list_paginator = Paginator( subscribed_to_list, self.PAGE_SIZE )
				subscribed_to_list_page = subscribed_to_list_paginator.page( page )
				for subscription in subscribed_to_list_page:
					subscribed_to_has_next_page = True
					subscribed_to_list_html.append(
						render_to_string( 'user_list_grid_element.html', {
							'user': subscription
						} )
					)
				try:
					subscribed_to_list_page_number = subscribed_to_list_paginator.page( page ).next_page_number()
				except InvalidPage:
					subscribed_to_has_next_page = False
					subscribed_to_list_page_number = -1

				return render( request, self.template_name_chunk, {
					'user_list_elements': subscribed_to_list_html,
					'has_next_page': subscribed_to_has_next_page,
					'next_page_link_additions': str( subscribed_to_list_page_number ) + "&list=subscribed_to"
				} )
			elif list_type == 'subscriber':
				show_active_users_string = self.request.GET.get( 'showActiveUsers' )
				show_active_users = show_active_users_string == "true"

				subscriber_list_html = []

				if show_active_users:
					show_active_users_string = "&showActiveUsers=true"
					subscriber_list = UserData.objects.filter(
						user__in = UserFollow.objects.filter( follow_user__username = username ).values( 'user' ),
						last_activity_date__gt = datetime.now() - timedelta( days = settings.OSP_DAYS_UNTIL_USER_CONSIDERED_INACTIVE )
					).select_related()
				else:
					show_active_users_string = ""
					subscriber_list = UserData.objects.filter(
						user__in = UserFollow.objects.filter( follow_user__username = username ).values( 'user' )
					).select_related()

				subscriber_list_paginator = Paginator( subscriber_list, self.PAGE_SIZE )
				subscriber_list_page = subscriber_list_paginator.page( page )
				for subscriber in subscriber_list_page:
					subscriber_list_html.append(
						render_to_string( 'user_list_grid_element.html', {
							'user': subscriber
						} )
					)
				subscriber_has_next_page = True
				try:
					subscriber_list_page_number = subscriber_list_paginator.page( page ).next_page_number()
				except InvalidPage:
					subscriber_has_next_page = False
					subscriber_list_page_number = -1

				return render( request, self.template_name_chunk, {
					'user_list_elements': subscriber_list_html,
					'has_next_page': subscriber_has_next_page,
					'next_page_link_additions': str( subscriber_list_page_number ) + "&list=subscriber" + show_active_users_string
				} )

		return render( request, self.template_name, self.get_context_data( **kwargs ) )

	def get_context_data( self, **kwargs ):
		context = super( ProfileView, self ).get_context_data( **kwargs )
		username = kwargs[ 'username' ]

		try:
			user_data = UserData.objects.select_related().get( user__username = username )
			context['page_title'] = generate_page_title( "Профиль - " + user_data.user.username )
		except User.DoesNotExist:
			raise Http404("Пользователя не существует")

		page = self.request.GET.get( 'page' )
		if page is None:
			page = 1

		stream_info = get_stream_info( user_data.user.username )

		context['username'] = user_data.user.username
		context['bio'] = parse_markdown( user_data.bio )
		context['avatar_url'] = user_data.avatar.url
		context['streaming'] = stream_info['active'] and not stream_info['hidden']
		context['can_follow'] = self.request.user.is_authenticated() and self.request.user.id != user_data.user.id
		if context['can_follow']:
			context['following'] = is_following( self.request.user.username, user_data.user.username )
		context['register_date'] = user_data.user.date_joined
		context['last_activity_date'] = user_data.last_activity_date
		context['registration_ip'] = user_data.registration_ip
		context['last_login_ip'] = user_data.last_login_ip

		subscribed_to_list_html = []
		subscribed_to_list = UserData.objects.filter(
			user__in = UserFollow.objects.filter( user = user_data.user.id ).values( 'follow_user' )
		).select_related()
		subscribed_to_list_paginator = Paginator( subscribed_to_list, self.PAGE_SIZE )
		subscribed_to_list_page = subscribed_to_list_paginator.page( page )
		context['subscribed_to_has_next_page'] = True
		try:
			context['subscribed_to_next_page'] = subscribed_to_list_paginator.page( page ).next_page_number()
		except InvalidPage:
			context['subscribed_to_has_next_page'] = False
		for subscription in subscribed_to_list_page:
			subscribed_to_list_html.append(
				render_to_string( 'user_list_grid_element.html', {
					'user': subscription
				} )
			)
		context['subscribed_to_list'] = subscribed_to_list_html
		context['subscribed_to_list_title'] = "Подписка ({0})".format( len( subscribed_to_list ) )

		subscriber_list_html = []
		subscriber_list = UserData.objects.filter(
			user__in = UserFollow.objects.filter( follow_user = user_data.user.id ).values( 'user' ),
			last_activity_date__gt = datetime.now() - timedelta( days = settings.OSP_DAYS_UNTIL_USER_CONSIDERED_INACTIVE )
		).select_related()
		subscriber_list_paginator = Paginator( subscriber_list, self.PAGE_SIZE )
		subscriber_list_page = subscriber_list_paginator.page( page )
		context['subscriber_has_next_page'] = True
		try:
			context['subscriber_next_page'] = subscriber_list_paginator.page( page ).next_page_number()
		except InvalidPage:
			context['subscriber_has_next_page'] = False
		for subscriber in subscriber_list_page:
			subscriber_list_html.append(
				render_to_string( 'user_list_grid_element.html', {
					'user': subscriber
				} )
			)
		context['subscriber_list'] = subscriber_list_html
		context['subscriber_list_title'] = "Подписчики ({0})".format( len( subscriber_list ) )

		context['active_tab_pane'] = "profile"
		context['name_changes'] = UserNameChange.objects.filter( user_id = user_data.user.id ).values_list( 'previous_username', flat = True )

		if self.request.user.username == user_data.user.username:
			context['navbar_user_profile_active'] = 'active'
		return context

class SettingsView( TemplateView ):
	template_name = 'settings.html'
	DAYS_FOR_NEW_NAME_CHANGE = 365

	def get_context_data( self, **kwargs ):
		context = super( SettingsView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Настройки" )

		user = self.request.user
		user_data = UserData.objects.get( user_id = user.id )
		context['user_settings_profile_form'] = UserSettingsProfileForm(
			initial = {
				'bio': user_data.bio,
				'show_subscriptions_on_top': user_data.show_subscriptions_on_top,
				'receive_follow_notifications': user_data.receive_follow_notifications
			}
		)

		context['user_settings_password_form'] = UserSettingsPasswordForm( user = self.request.user )
		context['user_settings_delete_yourself_form'] = UserSettingsDeleteYourselfForm( user = self.request.user )

		context['user_settings_change_name_form'] = UserSettingsChangeNameForm( user = self.request.user )
		context['user_settings_change_name_form_available'] = True
		user_name_changes = UserNameChange.objects.filter( user = self.request.user ).order_by( '-change_date' )
		if len( user_name_changes ) > 0:
			current_date = datetime.now().date()
			last_name_change_date = user_name_changes[0].change_date

			days_passed = (current_date - last_name_change_date).days
			if days_passed < self.DAYS_FOR_NEW_NAME_CHANGE:
				context['user_settings_change_name_form_available'] = False
				context['user_settings_change_name_form_not_available_until'] = ( last_name_change_date + timedelta( days = self.DAYS_FOR_NEW_NAME_CHANGE ) ).strftime( '%Y/%m/%d' )

		context['navbar_user_settings_active'] = "active"
		context['active_tab_pane'] = "profile"
		context['avatar_url'] = user_data.avatar.url
		return context

	def post( self, request, *args, **kwargs ):
		user = self.request.user
		user_data = UserData.objects.get( user_id = user.id )

		user_settings_profile_form = UserSettingsProfileForm( initial = {
			'bio': user_data.bio,
			'show_subscriptions_on_top': user_data.show_subscriptions_on_top,
			'receive_follow_notifications': user_data.receive_follow_notifications
		} )
		user_settings_profile_form_success = False

		user_settings_password_form = UserSettingsPasswordForm( user = request.user )
		user_settings_password_form_success = False
		user_settings_delete_yourself_form = UserSettingsDeleteYourselfForm( user = request.user )

		user_settings_change_name_form = UserSettingsChangeNameForm( user = request.user )
		user_settings_change_name_form_success = False
		user_settings_change_name_form_available = True
		user_settings_change_name_form_not_available_until = None

		active_tab_pane = "profile"

		if 'user_settings_profile_form' in request.POST:
			user_settings_profile_form = UserSettingsProfileForm( request.POST, request.FILES, instance = user_data )

			if user_settings_profile_form.is_valid():
				user_settings_profile_form.save( commit = False )
				user_settings_profile_form.user = request.user
				user_settings_profile_form.save()

				if 'remove_avatar' in request.POST:
					user_data.avatar = "./avatar/default_avatar.png"
					user_data.save()

				user_settings_profile_form_success = True

			user_settings_profile_form = UserSettingsProfileForm(
				initial = { 'bio': user_data.bio }
			)

			active_tab_pane = "profile"

		elif 'user_settings_password_form' in request.POST:
			user_settings_password_form = UserSettingsPasswordForm( user = request.user, data = request.POST )
			if user_settings_password_form.is_valid():
				user_settings_password_form.save()
				update_session_auth_hash( request, user_settings_password_form.user )
				user_settings_password_form_success = True

			active_tab_pane = "password"

		elif 'user_settings_delete_yourself_form' in request.POST:
			user_settings_delete_yourself_form = UserSettingsDeleteYourselfForm( user = request.user, data = request.POST )
			if user_settings_delete_yourself_form.is_valid():
				user = request.user;
				user_data = UserData.objects.get( user_id = user.id )
				user_data.delete()
				user.delete()
				return HttpResponseRedirect( reverse( 'osp:index' ) )
			active_tab_pane = "delete_yourself"

		elif 'user_settings_change_name_form' in request.POST:
			user_settings_change_name_form = UserSettingsChangeNameForm( user = request.user, data = request.POST )
			if user_settings_change_name_form.is_valid():
				user = request.user
				new_username = user_settings_change_name_form.cleaned_data['new_username']

				name_change = UserNameChange( user = user, previous_username = user.username, new_username = new_username )
				name_change.save()

				user.username = new_username
				user.save()

				user_settings_change_name_form_available = False
				user_settings_change_name_form_not_available_until = ( datetime.now().date() + timedelta( days = self.DAYS_FOR_NEW_NAME_CHANGE ) ).strftime( '%Y/%m/%d' )

				user_settings_change_name_form_success = True

			active_tab_pane = "change_name"

		#dumb and not DRY enough
		return render( request, self.template_name, {
			'user_settings_profile_form': user_settings_profile_form,
			'user_settings_profile_form_success': user_settings_profile_form_success,

			'user_settings_password_form': user_settings_password_form,
			'user_settings_password_form_success': user_settings_password_form_success,
			'user_settings_delete_yourself_form': user_settings_delete_yourself_form,

			'user_settings_change_name_form': user_settings_change_name_form,
			'user_settings_change_name_form_success': user_settings_change_name_form_success,
			'user_settings_change_name_form_available': user_settings_change_name_form_available,
			'user_settings_change_name_form_not_available_until': user_settings_change_name_form_not_available_until,

			'avatar_url': user_data.avatar.url,
			'active_tab_pane': active_tab_pane,
			'navbar_user_settings_active': 'active',
			'page_title': generate_page_title( "Настройки" )
		} )

class NotificationsView( TemplateView ):
	template_name = 'notifications.html'

	def get_context_data( self, **kwargs ):
		context = super( NotificationsView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Оповещения" )
		context['navbar_user_notifications_active'] = "active"

		user_notifications = UserNotification.objects.filter( user = self.request.user ).order_by( '-id' )
		for user_notification in user_notifications:
			is_new = user_notification.has_been_read == False

			user_notification.has_been_read = True
			user_notification.save()

			user_notification.text = parse_markdown( user_notification.text )
			user_notification.is_new = is_new
		context['user_notifications'] = user_notifications

		user_follow_notifications = UserFollowNotification.objects.filter( user = self.request.user ).order_by( '-id' )
		for user_follow_notification in user_follow_notifications:
			is_new = user_follow_notification.has_been_read == False

			user_follow_notification.has_been_read = True
			user_follow_notification.save()

			user_follow_notification.is_new = is_new
		context['user_follow_notifications'] = user_follow_notifications

		context['notifications_exist'] = len( user_notifications ) > 0 or len( user_follow_notifications ) > 0

		return context

	def post( self, request, *args, **kwargs ):
		if request.user.is_staff:
			ban_context = int( request.POST.get( 'banContext' ) )
			notification = request.POST.get( 'notification' )
			username = request.POST.get( 'username' )

			if ban_context == 0: # everyone
				user_ids = User.objects.all().values_list( 'id', flat = True )
				notifications = []
				for user_id in user_ids:
					notifications.append( UserNotification( user_id = user_id, text = notification ) )

				UserNotification.objects.bulk_create( notifications )
				return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )

			elif ban_context == 1: # specific user
				try:
					user = User.objects.get( username = username )

					user_notification = UserNotification( user = user, text = notification )
					user_notification.save()
					return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )
				except User.DoesNotExist:
					return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		raise PermissionDenied()

class MarkdownView( TemplateView ):
	template_name = 'markdown.html'
	def get_context_data( self, **kwargs ):
		context = super( MarkdownView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Примеры использования разметки" )
		context['navbar_markdown_active'] = "active"
		return context

class RegisterView( TemplateView ):
	template_name = 'register.html'
	def get_context_data( self, **kwargs ):
		context = super( RegisterView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Регистрация" )
		context['register_form'] = RegisterForm()
		context['navbar_register_active'] = "active"
		return context

	def post( self, request, *args, **kwargs ):
		register_form = RegisterForm( request.POST )
		if register_form.is_valid():
			# User registration is held here
			registered_user = register_form.save()
			registered_user.set_password( registered_user.password )
			registered_user.save()

			user_data = UserData(
				user = registered_user,
				registration_ip = get_ip( request ),
				last_login_ip = get_ip( request )
			)
			user_data.save()
			generate_stream_key( registered_user.username )

			registered_user = authenticate( username = request.POST['username'], password = request.POST['password'] )
			login( request, registered_user )
			return HttpResponseRedirect( reverse( 'osp:index' ) )

		return render( request, self.template_name, { 'register_form': register_form } )

class LoginView( TemplateView ):
	template_name = 'login.html'

	def get_context_data( self, **kwargs ):
		context = super( LoginView, self ).get_context_data( **kwargs )
		context['page_title'] = generate_page_title( "Вход" )
		context['login_form'] = LoginForm()
		context['navbar_login_active'] = "active"
		return context

	def post( self, request, *args, **kwargs ):
		login_form = LoginForm( request.POST )
		authentication_error = None
		if login_form.is_valid():
			username = request.POST[ 'username' ]
			password = request.POST[ 'password' ]

			user = authenticate( username = username, password = password )

			if user:
				if user.is_active:
					user_data = UserData.objects.get( user_id = user.id )
					user_data.last_login_ip = get_ip( request )
					user_data.save()
					login( request, user )

					return HttpResponseRedirect( reverse( 'osp:index' ) )
				else:
					raise PermissionDenied()
			else:
				authentication_error = "Введены неверные имя пользователя или пароль"
		return render( request, self.template_name, { 'login_form': login_form, 'authentication_error': authentication_error, 'navbar_login_active': 'active' } )

def LogOutView( request ):
	views_requiring_login = [ 'dashboard', 'settings' ]

	next = request.GET['next'];
	url_name = resolve( next ).url_name

	logout( request )
	if url_name in views_requiring_login:
		return HttpResponseRedirect( reverse( 'osp:index' ) )
	else:
		return HttpResponseRedirect( next )

def api_intro( request ):
	return HttpResponse( "Hi", content_type='application/json' )

def api_stream_info( request, username ):
	response = HttpResponse( json.dumps( get_stream_info( username ) ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_stream_list( request ):
	response = HttpResponse( json.dumps( get_stream_list( include_followers = False ) ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_stream_list_follow( request, username ):
	response = HttpResponse( json.dumps( get_stream_list_following( username ) ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_user_info( request, username ):
	response = HttpResponse( json.dumps( get_user_info( username ) ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_follow_list( request, username ):
	response = HttpResponse( json.dumps( get_follow_list( username ) ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_follower_list( request, username ):
	response = HttpResponse( json.dumps( get_follower_list( username ) ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_is_following( request, username, targetname ):
	response = HttpResponse( is_following( username, targetname ) )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_hide_stream( request, username ):
	response = HttpResponse( hide_stream( request, username ) )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_user_count( request ):
	user_count = UserData.objects.count()
	response = HttpResponse( json.dumps( { 'user_count': user_count } ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_active_user_count( request ):
	user_count = UserData.objects.filter( last_activity_date__gt = datetime.now() - timedelta( days = settings.OSP_DAYS_UNTIL_USER_CONSIDERED_INACTIVE ) ).count()
	response = HttpResponse( json.dumps( { 'user_count': user_count } ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_subscriber_count( request, username ):
	active = request.GET.get( 'active' ) == "true"
	subscriber_count = get_follower_count( username = username, only_active_followers = active )

	response = HttpResponse( json.dumps( { 'subscriber_count': subscriber_count } ), content_type='application/json' )
	response["Cache-Control"] = "no-cache, no-store, must-revalidate"
	return response

def api_ban_history( request, username ):
	try:
		user_data = UserData.objects.get( user__username = username )
	except:
		raise Http404()

	bans = []

	with connection.cursor() as cursor:
		query = """
			SELECT
				t.id,
				0 AS context,
				reason,
				issue_date,
				u.username AS issued_by,
				expiry_date,
				banned_ip,
				now() < expiry_date OR expiry_date IS NULL AS active,
				lifted
			FROM osp_stream_publish_ban t
			LEFT JOIN auth_user u ON issued_by_id = u.id
			WHERE banned_ip = '{0}' OR banned_ip = '{1}'

			UNION

			SELECT
				t.id,
				0 AS context,
				reason,
				issue_date,
				u.username AS issued_by,
				expiry_date,
				NULL AS banned_ip,
				now() < expiry_date OR expiry_date IS NULL AS active,
				lifted
			FROM osp_stream_publish_user_ban t
			LEFT JOIN auth_user u ON issued_by_id = u.id
			WHERE user_id = '{2}'

			UNION

			SELECT
				t.id,
				1 AS context,
				reason,
				issue_date,
				u.username AS issued_by,
				expiry_date,
				banned_ip,
				now() < expiry_date OR expiry_date IS NULL AS active,
				lifted
			FROM osp_stream_play_ban t
			LEFT JOIN auth_user u ON issued_by_id = u.id
			WHERE banned_ip = '{0}' OR banned_ip = '{1}'

			UNION

			SELECT
				t.id,
				2 AS context,
				reason,
				issue_date,
				u.username AS issued_by,
				expiry_date,
				banned_ip,
				now() < expiry_date OR expiry_date IS NULL AS active,
				lifted
			FROM osp_chat_ban_ip t
			LEFT JOIN auth_user u ON issued_by_id = u.id
			WHERE banned_ip = '{0}' OR banned_ip = '{1}'

			UNION

			SELECT
				t.id,
				2 AS context,
				reason,
				issue_date,
				u.username AS issued_by,
				expiry_date,
				NULL AS banned_ip,
				now() < expiry_date OR expiry_date IS NULL AS active,
				lifted
			FROM osp_chat_ban_user t
			LEFT JOIN auth_user u ON issued_by_id = u.id
			WHERE user_id = '{2}'

			ORDER BY issue_date DESC
		""".format( user_data.registration_ip, user_data.last_login_ip, user_data.user_id )

		cursor.execute( query )
		bans = cursor.fetchall()

		response = "";
		for ban in bans:
			context = ban[1]
			if context == 0:
				context_string = "На вещание"
			elif context == 1:
				context_string = "На просмотр"
			elif context == 2:
				context_string = "На все чаты"

			expiry_date = ban[5]
			if expiry_date is None:
				expiry_date = "-"
			else:
				expiry_date = expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )

			response += render_to_string( 'ban_chunk.html', {
				"id": ban[0],
				"context": ban[1],
				"context_string": context_string,
				"reason": ban[2],
				"issue_date": ban[3].strftime( "%Y-%m-%d %H:%M:%S" ),
				"issued_by": ban[4],
				"expiry_date": expiry_date,
				"banned_ip": ban[6],
				"active": bool( ban[7] ),
				"lifted": bool( ban[8] ),
				"allowed_to_lift": request.user.is_staff
			} )

		return HttpResponse( response )

def service_follow( request, username ):
	if request.method == 'POST':
		user = request.user
		try:
			target = User.objects.only( 'id', 'username' ).get( username = username )
			target_should_be_notified = UserData.objects.only( 'receive_follow_notifications' ).get( user = target ).receive_follow_notifications
			if target.username == user.username:
				return HttpResponse( "You cannot follow yourself" )
		except User.DoesNotExist:
			return HttpResponse( "User does not exist" )

		try:
			user_follow = UserFollow( user_id = user.id, follow_user_id = target.id )
			user_follow.save()
		except IntegrityError:
			return HttpResponse( "You already follow this user" )

		if target_should_be_notified:
			# prevent notification spam
			recent_unfollows = UserFollowNotification.objects.filter(
				issue_date__gt = datetime.now() - timedelta( hours = 1 ),
				user = target,
				follower_user = user,
				followed = False
			)
			if recent_unfollows.exists():
				for recent_unfollow in recent_unfollows:
					recent_unfollow.delete()
			else:
				notification = UserFollowNotification( user = target, follower_user = user, followed = True )
				notification.save()

		return HttpResponse( 1 )

	raise PermissionDenied()

def service_unfollow( request, username ):
	if request.method == 'POST':
		user = request.user
		try:
			target = User.objects.only( 'id', 'username' ).get( username = username )
			target_should_be_notified = UserData.objects.only( 'receive_follow_notifications' ).get( user = target ).receive_follow_notifications
			if target.username == user.username:
				return HttpResponse( "You cannot unfollow yourself" )
		except User.DoesNotExist:
			return HttpResponse( "User does not exist" )

		try:
			user_follow = UserFollow.objects.get( user_id = user.id, follow_user_id = target.id )
			user_follow.delete()
		except UserFollow.DoesNotExist:
			return HttpResponse( "You ain't following this user" )

		if target_should_be_notified:
			# prevent notification spam
			recent_follows = UserFollowNotification.objects.filter(
				issue_date__gt = datetime.now() - timedelta( hours = 1 ),
				user = target,
				follower_user = user,
				followed = True
			)
			if recent_follows.exists():
				for recent_follow in recent_follows:
					recent_follow.delete()
			else:
				notification = UserFollowNotification( user = target, follower_user = user, followed = False )
				notification.save()

		return HttpResponse( 1 )

	raise PermissionDenied()

def service_dashboard_permit( request, username ):
	if request.method == 'POST':
		user = request.user
		try:
			target = User.objects.only( 'id', 'username' ).get( username = username )
			if target.username == user.username:
				return HttpResponse( json.dumps( { "error": "У владельца канала уже есть доступ к своей панели" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		try:
			user_channel_helper = UserChannelHelper( channel_user_id = user.id, helper_user_id = target.id )
			user_channel_helper.save()
		except IntegrityError:
			return HttpResponse( json.dumps( { "error": "Вы уже дали доступ к панели этому пользователю" } ), content_type='application/json' )

		return HttpResponse( json.dumps( { "html": get_user_list_element( username, delete_allowed = True ) } ), content_type='application/json' )

	raise PermissionDenied()

def service_dashboard_forbid( request, username ):
	if request.method == 'POST':
		user = request.user
		try:
			target = User.objects.only( 'id', 'username' ).get( username = username )
			if target.username == user.username:
				return HttpResponse( json.dumps( { "error": "Вы не можете запретить владельцу канала открывать свою собственную панель" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		try:
			user_channel_helper = UserChannelHelper.objects.get( channel_user_id = user.id, helper_user_id = target.id )
			user_channel_helper.delete()
		except UserChannelHelper.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Пользователь уже не имеет доступа к вашей панели" } ), content_type='application/json' )

		return HttpResponse( 1 )

	raise PermissionDenied()

def service_chat_op( request, username, targetname ):
	if request.method == 'POST':
		try:
			user = User.objects.only( 'id', 'username' ).get( username = username )
			if user != request.user:
				return HttpResponse( json.dumps( { "error": "Отсутствуют права для выполнения данного действия" } ), content_type='application/json' )
			target = User.objects.only( 'id', 'username' ).get( username = targetname )
			if target.username == user.username:
				return HttpResponse( json.dumps( { "error": "Владелец чата уже является модератором собственного чата" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		try:
			chat_moderator = ChatModerator( chat_user_id = user.id, moderator_user_id = target.id )
			chat_moderator.save()
		except IntegrityError:
			return HttpResponse( json.dumps( { "error": "Пользователь уже является модератором" } ), content_type='application/json' )

		send_message_to_chat_server( 'OP_NOTIFY', json.dumps( {
			"nickname": targetname,
			"room": username
		} ) )
		return HttpResponse( json.dumps( { "html": get_user_list_element( targetname, delete_allowed = True ) } ), content_type='application/json' )

	raise PermissionDenied()

def service_chat_unop( request, username, targetname ):
	if request.method == 'POST':
		try:
			user = User.objects.only( 'id', 'username' ).get( username = username )
			if user != request.user:
				return HttpResponse( json.dumps( { "error": "Отсутствуют права для выполнения данного действия" } ), content_type='application/json' )
			target = User.objects.only( 'id', 'username' ).get( username = targetname )
			if target.username == user.username:
				return HttpResponse( json.dumps( { "error": "Вы не можете снять у владельца права модератора с его собственного чата" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		try:
			chat_moderator = ChatModerator.objects.get( chat_user_id = user.id, moderator_user_id = target.id )
			chat_moderator.delete()
		except ChatModerator.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Пользователь уже не является модератором" } ) )

		send_message_to_chat_server( 'UNOP_NOTIFY', json.dumps( {
			"nickname": targetname,
			"room": username
		} ) )
		return HttpResponse( 1 )

	raise PermissionDenied()

@csrf_exempt # hnnnnnng
def service_chat_ban( request, username, targetname ):
	if request.method == 'POST':
		try:
			user = User.objects.only( 'id', 'username' ).get( username = username )

			stream_key = request.POST.get( 'stream_key' )
			if stream_key is not None:
				user_data = UserData.objects.filter( stream_key = stream_key )
				if user_data.exists():
					stream_key_username = user_data[0].user.username
					if username != stream_key_username:
						return HttpResponse( json.dumps( { "error": "Неверный ключ" } ), content_type='application/json' )
				else:
					return HttpResponse( json.dumps( { "error": "Неверный ключ" } ), content_type='application/json' )
			else:
				if user != request.user and not ChatModerator.objects.filter( chat_user_id = user.id, moderator_user_id = request.user.id ).exists():
					return HttpResponse( json.dumps( { "error": "Отсутствуют права для выполнения данного действия" } ), content_type='application/json' )

			target = User.objects.only( 'id', 'username' ).get( username = targetname )
			if target.username == user.username:
				return HttpResponse( json.dumps( { "error": "Вы не можете забанить владельца от его собственного чата" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		# checking
		ban_reason = request.POST['ban_reason'].strip()
		if len( ban_reason ) > 255:
			return HttpResponse( json.dumps( { "error": "Величина причины бана не должна превышать 255 символов" } ), content_type='application/json' )

		try:
			ban_length_measurement = int( request.POST['ban_length_measurement'] )
		except:
			return HttpResponse( json.dumps( { "error": "Неверно введены единицы измерения длительности бана" } ), content_type='application/json' )
		if ban_length_measurement < 0 or ban_length_measurement > 5:
			return HttpResponse( json.dumps( { "error": "Неверно введены единицы измерения длительности бана" } ), content_type='application/json' )

		if ban_length_measurement != 5:
			try:
				ban_length = int( request.POST['ban_length'] )
			except:
				return HttpResponse( json.dumps( { "error": "Неверно задана длительность бана" } ) )
		else:
			ban_length = None

		# finally the ban itself

		try:
			ban_expiry_date = None
			if ban_length_measurement == 0: # mins
				ban_expiry_date = datetime.now() + timedelta( minutes = ban_length )
			elif ban_length_measurement == 1: # hours
				ban_expiry_date = datetime.now() + timedelta( hours = ban_length )
			elif ban_length_measurement == 2: # days
				ban_expiry_date = datetime.now() + timedelta( days = ban_length )
			elif ban_length_measurement == 3: # weeks
				ban_expiry_date = datetime.now() + timedelta( weeks = ban_length )
			elif ban_length_measurement == 4: # months
				ban_expiry_date = datetime.now() + timedelta( days = ban_length * 31 )

			chat_ban = ChatBan(
				chat_user_id = user.id,
				banned_user_id = target.id,
				reason = ban_reason,
				expiry_date = ban_expiry_date
			)
			chat_ban.save()
		except IntegrityError:
			return HttpResponse( json.dumps( { "error": "Пользователь уже забанен" } ), content_type='application/json' )

		if ban_expiry_date is not None:
			ban_expiry_date = ban_expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )

		send_message_to_chat_server( 'BAN_NOTIFY', json.dumps( {
			"nickname": targetname,
			"room": username,
			"reason": ban_reason,
			"expiry_date": ban_expiry_date
		} ) )
		return HttpResponse( json.dumps( { "html": get_user_ban_table_element( chat_ban ) } ) )

	raise PermissionDenied()

def service_chat_unban( request, username, targetname ):
	if request.method == 'POST':
		try:
			user = User.objects.only( 'id', 'username' ).get( username = username )
			if user != request.user and not ChatModerator.objects.filter( chat_user_id = user.id, moderator_user_id = request.user.id ).exists():
				return HttpResponse( json.dumps( { "error": "Отсутствуют права для выполнения данного действия" } ), content_type='application/json' )
			target = User.objects.only( 'id', 'username' ).get( username = targetname )
			if target.username == user.username:
				return HttpResponse( json.dumps( { "error": "Вы не можете разбанить владельца от его собственного чата" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		try:
			chat_ban = ChatBan.objects.get( chat_user_id = user.id, banned_user_id = target.id )
			chat_ban.delete()
		except ChatBan.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Пользователь уже не находится в бане" } ), content_type='application/json' )

		send_message_to_chat_server( 'UNBAN_NOTIFY', json.dumps( {
			"nickname": targetname,
			"room": username,
		} ) )
		return HttpResponse( 1 )

	raise PermissionDenied()

def service_update_stream_key( request, username ):
	if request.method == 'POST':
		try:
			user = User.objects.only( 'id' ).get( username = username )
			if user != request.user:
				return HttpResponse( json.dumps( { "error": "Отсутствуют права для выполнения данного действия" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		return HttpResponse( json.dumps( { "stream_key": generate_stream_key( username ) } ), content_type='application/json' )

	raise PermissionDenied()

def service_reset_stream( request, username ):
	if request.method == 'POST':
		try:
			user = User.objects.only( 'id' ).get( username = username )
			if user != request.user:
				return HttpResponse( json.dumps( { "error": "Отсутствуют права для выполнения данного действия" } ), content_type='application/json' )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		drop_from_streaming( username )
		return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )

	raise PermissionDenied()

def service_user_ban( request, username ):
	if request.method == 'POST' and request.user.is_staff:

		# checking
		ban_reason = request.POST['ban_reason'].strip()
		if len( ban_reason ) > 300:
			return HttpResponse( json.dumps( { "error": "Величина причины бана не должна превышать 300 символов" } ), content_type='application/json' )

		try:
			ban_context = int( request.POST['ban_context'] )
			ban_target = int( request.POST['ban_target'] )
		except:
			return HttpResponse( json.dumps( { "error": "Неверно задан контекст бана" } ), content_type='application/json' )
		if ban_context < 0 or ban_context > 2:
			return HttpResponse( json.dumps( { "error": "Неверно задан контекст бана" } ), content_type='application/json' )

		try:
			ban_length_measurement = int( request.POST['ban_length_measurement'] )
		except:
			return HttpResponse( json.dumps( { "error": "Неверно введены единицы измерения длительности бана" } ), content_type='application/json' )
		if ban_length_measurement < 0 or ban_length_measurement > 5:
			return HttpResponse( json.dumps( { "error": "Неверно введены единицы измерения длительности бана" } ), content_type='application/json' )

		if ban_length_measurement != 5:
			try:
				ban_length = int( request.POST['ban_length'] )
			except:
				return HttpResponse( json.dumps( { "error": "Неверно задана длительность бана" } ) )
		else:
			ban_length = None

		# finally the ban itself
		try:
			target = User.objects.only( 'id', 'username' ).get( username = username )
			target_ip = UserData.objects.only( 'registration_ip', 'last_login_ip' ).get( user = target )
		except User.DoesNotExist:
			return HttpResponse( json.dumps( { "error": "Данного пользователя не существует" } ), content_type='application/json' )

		ban_expiry_date = None
		if ban_length_measurement == 0: # mins
			ban_expiry_date = datetime.now() + timedelta( minutes = ban_length )
		elif ban_length_measurement == 1: # hours
			ban_expiry_date = datetime.now() + timedelta( hours = ban_length )
		elif ban_length_measurement == 2: # days
			ban_expiry_date = datetime.now() + timedelta( days = ban_length )
		elif ban_length_measurement == 3: # weeks
			ban_expiry_date = datetime.now() + timedelta( weeks = ban_length )
		elif ban_length_measurement == 4: # months
			ban_expiry_date = datetime.now() + timedelta( days = ban_length * 31 )

		if ban_target == 1: # registration ip
			ip = target_ip.registration_ip
		elif ban_target == 2: # last activity ip
			ip = target_ip.last_login_ip
		else:
			ip = None

		if ban_context == 0: # publish ban
			ban_context_string = "На вещание"
			if ban_target == 0: # user ban
				publish_ban = StreamPublishUserBan(
					user = target,
					reason = ban_reason,
					issued_by = request.user,
					expiry_date = ban_expiry_date
				)
			else:
				publish_ban = StreamPublishBan(
					banned_ip = ip,
					reason = ban_reason,
					issued_by = request.user,
					expiry_date = ban_expiry_date
				)
			publish_ban.save()
			ban_id = publish_ban.id
			issue_date = publish_ban.issue_date
			issued_by = publish_ban.issued_by.username

		elif ban_context == 1: # play ban
			if ban_target == 0:
				return HttpResponse( json.dumps( { "error": "Баны на просмотр возможны только по IP" } ), content_type='application/json' )

			ban_context_string = "На просмотр"
			play_ban = StreamPlayBan(
				banned_ip = ip,
				reason = ban_reason,
				issued_by = request.user,
				expiry_date = ban_expiry_date
			)
			play_ban.save()
			ban_id = play_ban.id
			issue_date = play_ban.issue_date
			issued_by = play_ban.issued_by.username

		elif ban_context == 2: # chat ban
			ban_context_string = "На все чаты"
			if ban_target == 0: # user ban
				chat_ban = ChatBanUser(
					user = target,
					reason = ban_reason,
					issued_by = request.user,
					expiry_date = ban_expiry_date
				)
			else:
				chat_ban = ChatBanIP(
					banned_ip = ip,
					reason = ban_reason,
					issued_by = request.user,
					expiry_date = ban_expiry_date
				)
			chat_ban.save()
			ban_id = chat_ban.id
			issue_date = chat_ban.issue_date
			issued_by = chat_ban.issued_by.username

		if ban_expiry_date is not None:
			ban_expiry_date = ban_expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )
		else:
			ban_expiry_date = "-"

		issue_date = issue_date.strftime( "%Y-%m-%d %H:%M:%S" )

		return HttpResponse( json.dumps( {
			"html": render_to_string( 'ban_chunk.html', {
				"id": ban_id,
				"context": ban_context,
				"context_string": ban_context_string,
				"reason": ban_reason,
				"issue_date": issue_date,
				"issued_by": issued_by,
				"expiry_date": ban_expiry_date,
				"banned_ip": ip,
				"active": True,
				"lifted": False,
				"allowed_to_lift": request.user.is_staff
			} )
		} ), content_type='application/json' )

	raise PermissionDenied()

def service_user_unban( request, username ):
	if request.method == 'POST' and request.user.is_staff:

		# checking
		try:
			ban_id = int( request.POST['ban_id'] )
			ban_context = int( request.POST['ban_context'] )
			ban_by_ip = bool( int( request.POST['ban_by_ip'] ) )
		except:
			return HttpResponse( json.dumps( { "error": "Неверно введены параметры для снятия бана" } ), content_type='application/json' )

		if ban_context < 0 or ban_context > 2:
			return HttpResponse( json.dumps( { "error": "Неверно задан контекст бана" } ), content_type='application/json' )

		if ban_context == 0: # publish ban
			if not ban_by_ip:
				publish_ban = StreamPublishUserBan.objects.filter( id = ban_id ).update( lifted = True )
			else:
				publish_ban = StreamPublishBan.objects.filter( id = ban_id ).update( lifted = True )

			return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )

		elif ban_context == 1: # play ban
			play_ban = StreamPlayBan.objects.filter( id = ban_id ).update( lifted = True )
			return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )

		elif ban_context == 2: # chat ban
			if not ban_by_ip:
				chat_ban = ChatBanUser.objects.filter( id = ban_id ).update( lifted = True )
			else:
				chat_ban = ChatBanIP.objects.filter( id = ban_id ).update( lifted = True )

			return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )

		return HttpResponse( json.dumps( { "success": False } ), content_type='application/json' )

	raise PermissionDenied()

@csrf_exempt
def service_auth( request ):
	try:
		session = Session.objects.get( session_key=request.POST.get( 'sessionid' ) )
		user_id = session.get_decoded().get( '_auth_user_id' )
		user = User.objects.get( id=user_id )

		return HttpResponse( json.dumps( { "success": True, "username": user.username } ), content_type='application/json' )
	except Exception:
		raise PermissionDenied()

@csrf_exempt
def service_bot_auth( request ):
	try:
		stream_key = request.POST['stream_key'];
		bot_name = request.POST['bot_name'];
		room_name = request.POST['room_name'];

		room_exists = User.objects.filter( username = room_name ).exists()
		if not room_exists:
			return HttpResponse( json.dumps( { "success": False, "error": "Room doesn't exist" } ), content_type='application/json' )

		duplicate_username = User.objects.filter( username = bot_name ).exists()
		if duplicate_username:
			return HttpResponse( json.dumps( { "success": False, "error": "Username {0} is already taken, change your bot name".format( bot_name ) } ), content_type='application/json' )

		bot_name_is_correct = len( bot_name ) >= 3 and re.search( r"^[A-Za-z][A-Za-z0-9]*(?:[_-][A-Za-z0-9]+)*$", bot_name )
		if not bot_name_is_correct:
			return HttpResponse( json.dumps( { "success": False, "error": "Invalid bot name" } ), content_type='application/json' )

		stream_key_is_valid = UserData.objects.filter( user__username = room_name, stream_key = stream_key ).exists()
		if not stream_key_is_valid:
			return HttpResponse( json.dumps( { "success": False, "error": "Invalid stream key" } ), content_type='application/json' )

		return HttpResponse( json.dumps( { "success": True, "username": bot_name } ), content_type='application/json' )
	except Exception:
		raise PermissionDenied()

#for now, this is only for node.js chat. so it's reading POST
@csrf_exempt
def service_chat_user_info( request ):
	user_info = {
		"success": False,
		"owner": False,
		"moderator": False,
		"banned": False,
		"ban_expiry_date": None,
		"ban_reason": None
	}
	try:
		room = request.POST.get( 'room' )
		username = request.POST.get( 'username' )

		chat_user = User.objects.only( 'id' ).get( username = room )
		target_user = User.objects.only( 'id' ).get( username = username )

		user_info['success'] = True

		try:
			chat_ban = ChatBan.objects.get( chat_user_id = chat_user.id, banned_user_id = target_user.id )
			user_info['banned'] = True
			ban_expiry_date = chat_ban.expiry_date
			if ban_expiry_date is not None:
				user_info['ban_expiry_date'] = ban_expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )
			user_info['ban_reason'] = chat_ban.reason
			return HttpResponse( json.dumps( user_info ), content_type='application/json' )
		except ChatBan.DoesNotExist:
			pass

		try:
			target_user_data = UserData.objects.get( user_id = target_user.id )
			registration_ip = target_user_data.registration_ip
			last_login_ip = target_user_data.last_login_ip

			chat_ip_bans = ChatBanIP.objects.filter( Q( banned_ip = registration_ip ) | Q( banned_ip = last_login_ip ), Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), lifted = False ).order_by( '-issue_date' )
			if chat_ip_bans.exists():
				user_info['banned'] = True
				if chat_ip_bans[0].expiry_date is not None:
					user_info['ban_expiry_date'] = chat_ip_bans[0].expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )
				user_info['ban_reason'] = chat_ip_bans[0].reason

				return HttpResponse( json.dumps( user_info ), content_type='application/json' )

			chat_user_bans = ChatBanUser.objects.filter( Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), user = target_user, lifted = False ).order_by( '-issue_date' )
			if chat_user_bans.exists():
				user_info['banned'] = True
				if chat_user_bans[0].expiry_date is not None:
					user_info['ban_expiry_date'] = chat_user_bans[0].expiry_date.strftime( "%Y-%m-%d %H:%M:%S" )
				user_info['ban_reason'] = chat_user_bans[0].reason

				return HttpResponse( json.dumps( user_info ), content_type='application/json' )

		except UserData.DoesNotExist:
			pass

		if chat_user.id == target_user.id:
			user_info['owner'] = True
			return HttpResponse( json.dumps( user_info ), content_type='application/json' )

		try:
			chat_moderator = ChatModerator.objects.get( chat_user_id = chat_user.id, moderator_user_id = target_user.id )
			user_info['moderator'] = True
			return HttpResponse( json.dumps( user_info ), content_type='application/json' )
		except ChatModerator.DoesNotExist:
			pass

		return HttpResponse( json.dumps( user_info ), content_type='application/json' )
	except Exception:
		return HttpResponse( json.dumps( user_info ), content_type='application/json' )

#not DRY enough
@csrf_exempt
def service_chat_user_card( request ):
	user_card = {
		"nickname": "",
		"avatar_url": "",
		"owner": False,
		"moderator": False,
		"banned": False,
		"bot": False,
		"show_moderation": False
	}
	try:
		room = request.POST.get( 'room' )
		username = request.POST.get( 'username' )
		is_bot = request.POST.get( 'is_bot' ) == "true"

		if not is_bot:
			chat_user = User.objects.only( 'id' ).get( username = room )
			target_user = User.objects.only( 'id' ).get( username = username )
			request_user = request.user

			target_user_data = UserData.objects.only( 'avatar', 'registration_ip', 'last_login_ip' ).get( user_id = target_user.id )

			registration_ip = target_user_data.registration_ip
			last_login_ip = target_user_data.last_login_ip

			user_card['nickname'] = target_user.username
			user_card['avatar_url'] = target_user_data.avatar.url
			if chat_user.id == target_user.id:
				user_card['owner'] = True

			if not user_card['owner']:
				try:
					chat_moderator = ChatModerator.objects.get( chat_user_id = chat_user.id, moderator_user_id = target_user.id )
					user_card['moderator'] = True
				except ChatModerator.DoesNotExist:
					pass

				try:
					chat_ban = ChatBan.objects.get( chat_user_id = chat_user.id, banned_user_id = target_user.id )
					user_card['banned'] = True
				except ChatBan.DoesNotExist:
					pass

				chat_bans = ChatBanUser.objects.filter( Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), user = target_user, lifted = False )
				if chat_bans.exists():
					user_card['banned'] = True

				chat_ip_bans = ChatBanIP.objects.filter( Q( banned_ip = registration_ip ) | Q( banned_ip = last_login_ip ), Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), lifted = False )
				if chat_ip_bans.exists():
					user_card['banned'] = True

			request_user_can_moderate = False
			if chat_user.id == request_user.id:
				request_user_can_moderate = True
			if not request_user_can_moderate:
				try:
					request_user_moderator = ChatModerator.objects.get( chat_user_id = chat_user.id, moderator_user_id = request_user.id )
					request_user_can_moderate = True
				except ChatModerator.DoesNotExist:
					pass

			if not target_user.id == request_user.id and target_user.id != chat_user.id and not user_card['moderator'] and request_user_can_moderate:
				user_card['show_moderation'] = True

			user_card['can_ignore'] = True

			if request_user.is_authenticated() and request_user.id == target_user.id:
				user_card['can_ignore'] = False

		else:
			user_card['bot'] = True
			user_card['nickname'] = username
			user_card['can_ignore'] = True

	except Exception:
		raise PermissionDenied()

	return HttpResponse( render_to_string( 'chat_user_card.html', user_card ) )

@csrf_exempt
def service_chat_motd( request ):
	chat_motd = {
		"success": False,
		"chat_motd": ""
	}

	try:
		room = request.POST.get( 'room' )
		chat_owner = User.objects.get( username = room )

		chat_motd['success'] = True

		chat_owner_data = UserData.objects.get( user_id = chat_owner.id )
		chat_motd['chat_motd'] = chat_owner_data.stream_chat_motd

		return HttpResponse( json.dumps( chat_motd ), content_type='application/json' )

	except Exception:
		return HttpResponse( json.dumps( chat_motd ), content_type='application/json' )

@csrf_exempt
def service_markdown_preview( request ):
	if request.method == 'POST':
		return HttpResponse( json.dumps( { "html": parse_markdown( request.POST.get( 'message' ) ) } ), content_type='application/json' )

	raise PermissionDenied()

def service_remove_notification( request ):
	if request.method == 'POST':
		notification_id = request.POST.get( 'id' )
		notification_type = int( request.POST.get( 'notificationType' ) )

		if notification_type == 0:
			try:
				notification = UserNotification.objects.get( id = notification_id )
				if notification.user != request.user:
					return HttpResponse( json.dumps( { "error": "Вы не можете удалить чужое оповещение" } ), content_type='application/json' )

				notification.delete()
				return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )
			except UserNotification.DoesNotExist:
				pass

		elif notification_type == 1:
			try:
				notification = UserFollowNotification.objects.get( id = notification_id )
				if notification.user != request.user:
					return HttpResponse( json.dumps( { "error": "Вы не можете удалить чужое оповещение" } ), content_type='application/json' )

				notification.delete()
				return HttpResponse( json.dumps( { "success": True } ), content_type='application/json' )
			except UserFollowNotification.DoesNotExist:
				pass

	raise PermissionDenied()

@csrf_exempt
def service_rtmp_on_publish( request ):
	if request.method == 'POST':
		publish_log = None
		if settings.OSP_PUBLISH_LOG_DIRECTORY is not None:
			publish_log = append_stream_log( settings.OSP_PUBLISH_LOG_DIRECTORY, settings.OSP_PUBLISH_LOG_NAME )

		stream_key = request.POST.get( 'name' )
		ip = request.POST.get( 'addr' )

		if publish_log:
			publish_log.write( "[{0}] ({1}) {2}: Connection attempt\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), stream_key, ip ) )

		try:
			user_data = UserData.objects.get( stream_key = stream_key )
			user = User.objects.only( 'id', 'username' ).get( id = user_data.user_id )
		except UserData.DoesNotExist:
			if publish_log:
				publish_log.write( "[{0}] ({1}) {2}: Rejected - stream key does not exist\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), stream_key, ip ) )
				publish_log.close()
			raise PermissionDenied()

		if StreamPublishBan.objects.filter( Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), banned_ip = ip, lifted = False ).exists():
			if publish_log:
				publish_log.write( "[{0}] ({1} - {2}) {3}: Rejected - banned ip\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
				publish_log.close()
			raise PermissionDenied()

		if StreamPublishUserBan.objects.filter( Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), user_id = user.id, lifted = False ).exists():
			if publish_log:
				publish_log.write( "[{0}] ({1} - {2}) {3}: Rejected - user is banned\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
				publish_log.close()
			raise PermissionDenied()

		if publish_log:
			publish_log.write( "[{0}] ({1} - {2}) {3}: Connected\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
			publish_log.close()

		# these symlinks mask stream keys and are used to play HLS streams
		source = os.path.join( settings.OSP_HLS_STREAM_PATH, stream_key )
		if not os.path.isdir( source ):
			os.mkdir( source )
		destination = os.path.join( settings.OSP_HLS_STREAM_LINK_PATH, user.username )
		if not os.path.isdir( settings.OSP_HLS_STREAM_LINK_PATH ):
			os.mkdir( settings.OSP_HLS_STREAM_LINK_PATH )
		symlink_forced( source, destination )

		return HttpResponseRedirect( "//" + user.username )

	raise PermissionDenied()

@csrf_exempt
def service_rtmp_on_publish_done( request ):
	if request.method == 'POST':
		publish_log = None
		if settings.OSP_PUBLISH_LOG_DIRECTORY is not None:
			publish_log = append_stream_log( settings.OSP_PUBLISH_LOG_DIRECTORY, settings.OSP_PUBLISH_LOG_NAME )

		stream_key = request.POST.get( 'name' )
		ip = request.POST.get( 'addr' )

		try:
			user_data = UserData.objects.only( 'user_id', 'stream_description' ).get( stream_key = stream_key )
			user = User.objects.only( 'id', 'username' ).get( id = user_data.user_id )
		except UserData.DoesNotExist:
			raise PermissionDenied()

		if publish_log:
			publish_log.write( "[{0}] ({1} - {2}) {3}: Disconnected\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
			publish_log.close()

		return HttpResponse( 200 )

	raise PermissionDenied()

@csrf_exempt
def service_rtmp_on_play( request ):
	if request.method == 'POST':
		play_log = None
		if settings.OSP_PLAY_LOG_DIRECTORY is not None:
			play_log = append_stream_log( settings.OSP_PLAY_LOG_DIRECTORY, settings.OSP_PLAY_LOG_NAME )

		stream_name = request.POST.get( 'name' )
		ip = request.POST.get( 'addr' )

		if play_log:
			play_log.write( "[{0}] ({1}) {2}: Connection attempt\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), stream_name, ip ) )

		try:
			user = User.objects.only( 'id', 'username' ).get( username = stream_name )
			user_data = UserData.objects.only( 'stream_description' ).get( user_id = user.id )
		except User.DoesNotExist:
			if play_log:
				play_log.write( "[{0}] ({1}) {2}: Rejected - stream name does not exist\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), stream_name, ip ) )
				play_log.close()
			raise PermissionDenied()

		if StreamPlayBan.objects.filter( Q( expiry_date__gt = datetime.now() ) | Q( expiry_date = None ), banned_ip = ip, lifted = False ).exists():
			if play_log:
				play_log.write( "[{0}] ({1} - {2}) {3}: Rejected - banned ip\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
				play_log.close()
			raise PermissionDenied()

		if play_log:
			play_log.write( "[{0}] ({1} - {2}) {3}: Connected\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
			play_log.close()

		# if there's no incoming stream - drop the streamer from nginx
		broken = get_stream_info( stream_name )['broken']
		if broken:
			drop_from_streaming( name = stream_name )

		return HttpResponseRedirect( "//" + user.username )

	raise PermissionDenied()

@csrf_exempt
def service_rtmp_on_play_done( request ):
	if request.method == 'POST':
		play_log = None
		if settings.OSP_PLAY_LOG_DIRECTORY is not None:
			play_log = append_stream_log( settings.OSP_PLAY_LOG_DIRECTORY, settings.OSP_PLAY_LOG_NAME )

		stream_name = request.POST.get( 'name' )
		ip = request.POST.get( 'addr' )

		try:
			user = User.objects.only( 'id' ).get( username = stream_name )
			user_data = UserData.objects.only( 'stream_description' ).get( user_id = user.id )
		except User.DoesNotExist:
			raise PermissionDenied()

		if play_log:
			play_log.write( "[{0}] ({1} - {2}) {3}: Disconnected\n".format( datetime.now().strftime( "%Y-%m-%d %H:%M:%S" ), user.username, user_data.stream_description, ip ) )
			play_log.close()

		return HttpResponse( 200 )

	raise PermissionDenied()

views_not_updating_last_user_activity = [
	api_intro,
	api_stream_list,
	api_stream_list_follow,
	api_stream_info,
	api_user_info,
	api_follow_list,
	api_follower_list,
	api_is_following,
	api_hide_stream,

	serve,

	service_chat_user_card
]