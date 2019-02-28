from django.contrib import admin
from osp.models import UserData, UserFollow, UserChannelHelper, UserNameChange, ChatBan, ChatBanIP, ChatBanUser, ChatModerator, StreamPublishBan, StreamPublishUserBan, StreamPlayBan, UserNotification, UserFollowNotification
from osp.api import drop_from_streaming
from django import forms

# Register your models here.

def drop_from_streaming_action( modeladmin, request, queryset ):
	for client in queryset:
		drop_from_streaming( name = client.user.username )
drop_from_streaming.short_description = "Drop selected users from streaming"

class UserDataAdmin( admin.ModelAdmin ):
	search_fields = [ 'user_id__username', 'registration_ip', 'last_login_ip' ]
	readonly_fields = ( 'user', 'stream_key', 'registration_ip', 'last_login_ip', 'last_activity_date' )
	list_display = ( 'user', 'stream_description', 'registration_ip', 'last_login_ip', 'last_activity_date' )
	actions = [ drop_from_streaming_action ]

	def formfield_for_dbfield( self, db_field, **kwargs ):
		formfield = super( UserDataAdmin, self ).formfield_for_dbfield( db_field, **kwargs )
		if db_field.name == 'bio':
			formfield.widget = forms.Textarea( attrs=formfield.widget.attrs )
		return formfield

class UserFollowAdmin( admin.ModelAdmin ):
	raw_id_fields = ( 'user' , 'follow_user' )
	search_fields = [ 'user__username', 'follow_user__username' ]
	list_display = ( 'user', 'follow_user' )

class UserChannelHelperAdmin( admin.ModelAdmin ):
	raw_id_fields = ( 'channel_user' , 'helper_user' )
	search_fields = [ 'helper_user__username', 'channel_user__username' ]
	list_display = ( 'channel_user', 'helper_user' )

class UserNameChangeAdmin( admin.ModelAdmin ):
	readonly_fields = ( 'user', 'previous_username', 'new_username', 'change_date' )
	list_display = ( 'user', 'previous_username', 'new_username', 'change_date' )

class ChatModeratorAdmin( admin.ModelAdmin ):
	raw_id_fields = ( 'chat_user' , 'moderator_user' )
	search_fields = [ 'chat_user__username', 'moderator_user__username' ]
	list_display = ( 'chat_user', 'moderator_user' )

class ChatBanAdmin( admin.ModelAdmin ):
	raw_id_fields = ( 'chat_user' , 'banned_user' )
	search_fields = [ 'chat_user__username', 'banned_user__username' ]
	list_display = ( 'chat_user', 'banned_user', 'reason', 'expiry_date' )

class ChatBanIPAdmin( admin.ModelAdmin ):
	readonly_fields = ( 'issue_date', 'issued_by' )
	search_fields = [ 'banned_ip' ]
	list_display = ( 'banned_ip', 'reason', 'issued_by', 'issue_date', 'expiry_date' )

class ChatBanUserAdmin( admin.ModelAdmin ):
	raw_id_fields = ( 'user', )
	readonly_fields = ( 'issue_date', 'issued_by' )
	search_fields = [ 'user' ]
	list_display = ( 'user', 'reason', 'issued_by', 'issue_date', 'expiry_date' )

class StreamPublishBanAdmin( admin.ModelAdmin ):
	readonly_fields = ( 'issue_date', 'issued_by' )
	search_fields = [ 'banned_ip' ]
	list_display = ( 'banned_ip', 'reason', 'issued_by', 'issue_date', 'expiry_date' )

class StreamPublishUserBanAdmin( admin.ModelAdmin ):
	raw_id_fields = ( 'user', )
	readonly_fields = ( 'issue_date', 'issued_by' )
	search_fields = [ 'user' ]
	list_display = ( 'user', 'reason', 'issued_by', 'issue_date', 'expiry_date' )

class StreamPlayBanAdmin( admin.ModelAdmin ):
	readonly_fields = ( 'issue_date', 'issued_by' )
	search_fields = [ 'banned_ip' ]
	list_display = ( 'banned_ip', 'reason', 'issued_by', 'issue_date', 'expiry_date' )

class UserNotificationAdmin( admin.ModelAdmin ):
	search_fields = [ 'user_id__username' ]
	readonly_fields = ( 'user', 'issue_date', 'expiry_date', 'has_been_read' )
	list_display = [ 'user', 'text', 'issue_date' ]

class UserFollowNotificationAdmin( admin.ModelAdmin ):
	search_fields = [ 'user_id__username', 'follower_user__username' ]
	readonly_fields = ( 'user', 'issue_date', 'expiry_date', 'has_been_read', 'followed' )
	list_display = [ 'user', 'follower_user', 'followed', 'issue_date' ]

admin.site.register( UserData, UserDataAdmin )
admin.site.register( UserFollow, UserFollowAdmin )
admin.site.register( UserChannelHelper, UserChannelHelperAdmin )
admin.site.register( UserNameChange, UserNameChangeAdmin )
admin.site.register( ChatModerator, ChatModeratorAdmin )
admin.site.register( ChatBan, ChatBanAdmin )
admin.site.register( ChatBanIP, ChatBanIPAdmin )
admin.site.register( ChatBanUser, ChatBanUserAdmin )
admin.site.register( StreamPublishBan, StreamPublishBanAdmin )
admin.site.register( StreamPublishUserBan, StreamPublishUserBanAdmin )
admin.site.register( StreamPlayBan, StreamPlayBanAdmin )
admin.site.register( UserNotification, UserNotificationAdmin )
admin.site.register( UserFollowNotification, UserFollowNotificationAdmin )