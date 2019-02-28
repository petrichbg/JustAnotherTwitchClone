from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from osp import views

urlpatterns = patterns( '',
	url( r'^$', views.IndexView.as_view(), { 'sidebar': False } , name='index' ),
	url( r'^rules/$', views.RulesView.as_view(), name='rules' ),
	url( r'^help/$', views.HelpView.as_view(), name='help' ),
	url( r'^changelog/$', views.ChangeLogView.as_view(), name='changelog' ),
	url( r'^register/$', views.RegisterView.as_view(), name='register' ),
	url( r'^login/$', views.LoginView.as_view(), name='login' ),
	url( r'^logout/$', views.LogOutView, name='logout' ),
	url( r'^settings/$', login_required( views.SettingsView.as_view() ), name='settings' ),
	url( r'^notifications/$', login_required( views.NotificationsView.as_view() ), name='notifications' ),
	url( r'^users/$', views.UsersView.as_view(), name='users' ),
	url( r'^streams/$', views.StreamListView.as_view(), name='streams' ),
	url( r'^markdown/$', views.MarkdownView.as_view(), name='markdown' ),

	#api
	url( r'^api/$', views.api_intro, name='api_intro' ),
	url( r'^api/streamlist/$', views.api_stream_list, name='api_stream_list' ),
	url( r'^api/streamlist/follow/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_stream_list_follow, name='api_stream_list_follow' ),
	url( r'^api/streaminfo/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_stream_info, name='api_stream_info' ),
	url( r'^api/userinfo/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_user_info, name='api_user_info' ),
	url( r'^api/followlist/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_follow_list, name='api_follow_list' ),
	url( r'^api/followerlist/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_follower_list, name='api_follower_list' ),
	url( r'^api/isfollowing/(?P<username>[0-9a-zA-Z_-]+)/(?P<targetname>[0-9a-zA-Z_-]+)/$', views.api_is_following, name='api_is_following' ),
	url( r'^api/hide/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_hide_stream, name='api_hide_stream' ),
	url( r'^api/usercount/$', views.api_user_count, name='user_count' ),
	url( r'^api/activeusercount/$', views.api_active_user_count, name='active_user_count' ),
	url( r'^api/subscribercount/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_subscriber_count, name='subscriber_count' ),
	url( r'^api/banhistory/(?P<username>[0-9a-zA-Z_-]+)/$', views.api_ban_history, name='api_ban_history' ),

	#services with api potential
	url( r'^service/follow/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_follow, name='service_follow' ),
	url( r'^service/unfollow/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_unfollow, name='service_unfollow' ),
	url( r'^service/dashboardpermit/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_dashboard_permit, name='service_dashboard_permit' ),
	url( r'^service/dashboardforbid/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_dashboard_forbid, name='service_dashboard_forbid' ),
	url( r'^service/chatop/(?P<username>[0-9a-zA-Z_-]+)/(?P<targetname>[0-9a-zA-Z_-]+)/$', views.service_chat_op, name='service_chat_op' ),
	url( r'^service/chatunop/(?P<username>[0-9a-zA-Z_-]+)/(?P<targetname>[0-9a-zA-Z_-]+)/$', views.service_chat_unop, name='service_chat_unop' ),
	url( r'^service/chatban/(?P<username>[0-9a-zA-Z_-]+)/(?P<targetname>[0-9a-zA-Z_-]+)/$', views.service_chat_ban, name='service_chat_ban' ),
	url( r'^service/chatunban/(?P<username>[0-9a-zA-Z_-]+)/(?P<targetname>[0-9a-zA-Z_-]+)/$', views.service_chat_unban, name='service_chat_unban' ),
	url( r'^service/updatestreamkey/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_update_stream_key, name='service_update_stream_key' ),
	url( r'^service/resetstream/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_reset_stream, name='service_reset_stream' ),
	url( r'^service/userban/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_user_ban, name='service_user_ban' ),
	url( r'^service/userunban/(?P<username>[0-9a-zA-Z_-]+)/$', views.service_user_unban, name='service_user_unban' ),
	url( r'^service/auth/$', views.service_auth, name='auth' ),
	url( r'^service/botauth/$', views.service_bot_auth, name='bot_auth' ),
	url( r'^service/chatuserinfo/$', views.service_chat_user_info, name='service_chat_user_info' ),
	url( r'^service/chatusercard/$', views.service_chat_user_card, name='service_chat_user_card' ),
	url( r'^service/chatmotd/$', views.service_chat_motd, name='service_chat_motd' ),
	url( r'^service/rtmponpublish/$', views.service_rtmp_on_publish, name='service_rtmp_on_publish' ),
	url( r'^service/rtmponpublishdone/$', views.service_rtmp_on_publish_done, name='service_rtmp_on_publish_done' ),
	url( r'^service/rtmponplay/$', views.service_rtmp_on_play, name='service_rtmp_on_play' ),
	url( r'^service/rtmponplaydone/$', views.service_rtmp_on_play_done, name='service_rtmp_on_play_done' ),
	url( r'^service/removenotification/$', views.service_remove_notification, name='service_remove_notification' ),
	url( r'^service/markdownpreview/$', views.service_markdown_preview, name='service_markdown_preview' ),



	#must be the last!
	url( r'^(?P<username>[0-9a-zA-Z_-]+)/$', views.StreamView.as_view(), name='stream' ),
	url( r'^(?P<username>[0-9a-zA-Z_-]+)/profile/$', views.ProfileView.as_view(), name='profile' ),
	url( r'^(?P<username>[0-9a-zA-Z_-]+)/chat/$', views.ChatView.as_view(), name='stream_chat' ),

	#dashboard
	url( r'^(?P<username>[0-9a-zA-Z_-]+)/dashboard/stream/$', login_required( views.dashboard_stream ), name='dashboard_stream' ),
	url( r'^(?P<username>[0-9a-zA-Z_-]+)/dashboard/$', login_required( views.DashboardView.as_view() ), name='dashboard' ),

)
