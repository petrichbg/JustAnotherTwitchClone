from django.db import models
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import now, timedelta
from PIL import Image
import os
from osp.convenience import format_file_as_uuid

#not dry enough
def avatar_path( instance, filename ):
	return format_file_as_uuid( instance, filename, 'avatar/' )

# Create your models here.

class UserData( models.Model ):
	user = models.OneToOneField( User )
	bio = models.CharField( max_length = 10000, blank = True )
	stream_chat_motd = models.CharField( max_length = 255, blank = True )
	stream_description = models.CharField( max_length = 140, blank = True )
	stream_hidden = models.BooleanField( default = True )
	stream_key = models.CharField( max_length = 100, default = "BLANK" )
	avatar = models.ImageField( default = "./avatar/default_avatar.png", upload_to = avatar_path, storage = FileSystemStorage( ) )
	receive_follow_notifications = models.BooleanField( default = True )
	show_subscriptions_on_top = models.BooleanField( default = True )
	last_activity_date = models.DateTimeField( auto_now = True )
	registration_ip = models.GenericIPAddressField( protocol = 'IPv4', null = True )
	last_login_ip = models.GenericIPAddressField( protocol = 'IPv4', null = True )

	class Meta:
		db_table = "osp_user_data"
		verbose_name = "User Data"
		verbose_name_plural = "User Data"

	def save(self, *args, **kwargs):
		super(UserData, self).save(*args, **kwargs)
		if self.avatar:
			image = Image.open( os.path.join( self.avatar.storage.location, self.avatar.name ) )
			size = ( 64, 64 )
			image.thumbnail( size, Image.ANTIALIAS )
			image.save( os.path.join( self.avatar.storage.location, self.avatar.name ) )

	def __getattribute__( self, name ):
		attr = models.Model.__getattribute__( self, name )
		if name == "stream_description" and len( attr ) == 0:
			return "Безымянный стрим"
		return attr

	def __str__( self ):
		return self.user.username

#those are shamelessy stolen from stackoverflow
#delete old avatar files
@receiver(models.signals.post_delete, sender=UserData)
def auto_delete_file_on_delete(sender, instance, **kwargs):
	if instance.avatar:
		if os.path.isfile(instance.avatar.path):
			if not "default_avatar.png" in instance.avatar.path:
				os.remove(instance.avatar.path)

@receiver(models.signals.pre_save, sender=UserData)
def auto_delete_file_on_change(sender, instance, **kwargs):
	if not instance.pk:
		return False

	try:
		old_file = UserData.objects.get(pk=instance.pk).avatar
	except UserData.DoesNotExist:
		return False

	new_file = instance.avatar
	if not old_file == new_file and not "default_avatar.png" in old_file.name:
		if os.path.isfile(old_file.path):
			os.remove(old_file.path)

class UserFollow( models.Model ):
	user = models.ForeignKey( User )
	follow_user = models.ForeignKey( User, related_name = "user_follow_follow_user" )

	class Meta:
		db_table = "osp_user_follow"
		unique_together = ( "user", "follow_user" )
		verbose_name = "User's Follower"
		verbose_name_plural = "Users' Followers"

	def __str__( self ):
		return "UserFollow: {0} <-- {1}".format( self.follow_user.username, self.user.username )

def default_user_follow_notification_expiry_date():
    return now() + timedelta( days = 7 )

class UserFollowNotification( models.Model ):
	user = models.ForeignKey( User )
	follower_user = models.ForeignKey( User, related_name = "user_follow_notification_follower_user" )
	followed = models.BooleanField()
	issue_date = models.DateTimeField( auto_now_add = True )
	expiry_date = models.DateTimeField( default = default_user_follow_notification_expiry_date )
	has_been_read = models.BooleanField( default = False )

	class Meta:
		db_table = "osp_user_follow_notification"
		verbose_name = "User's Follow Notifications"
		verbose_name_plural = "Users' Follow Notifications"

	def __str__( self ):
		return "UserFollowNotification: {0} <-- {1}".format( self.user.username, self.follower_user.username )

def default_user_notification_expiry_date():
    return now() + timedelta( days = 31 )

class UserNotification( models.Model ):
	user = models.ForeignKey( User )
	text = models.CharField( max_length = 10000 )
	issue_date = models.DateTimeField( auto_now_add = True )
	expiry_date = models.DateTimeField( default = default_user_notification_expiry_date )
	has_been_read = models.BooleanField( default = False )

	class Meta:
		db_table = "osp_user_notification"
		verbose_name = "User's Notifications"
		verbose_name_plural = "Users' Notifications"

	def __str__( self ):
		return "UserNotification: {0}".format( self.user.username )

class UserChannelHelper( models.Model ):
	channel_user = models.ForeignKey( User, related_name = "chat_helper_channel_user" )
	helper_user = models.ForeignKey( User )

	class Meta:
		db_table = "osp_user_channel_helper"
		unique_together = ( "channel_user", "helper_user" )
		verbose_name = "User's Channel Helper"
		verbose_name_plural = "Users' Channel Helpers"

	def __str__( self ):
		return "UserChannelHelper: {0} <-- {1}".format( self.channel_user.username, self.helper_user.username )

class UserNameChange( models.Model ):
	user = models.ForeignKey( User )
	previous_username = models.CharField( max_length = 30, blank = False )
	new_username = models.CharField( max_length = 30, blank = False )
	change_date = models.DateField( auto_now_add = True )

	class Meta:
		db_table = "osp_user_name_change"
		verbose_name = "User's Name Change"
		verbose_name_plural = "Users' Name Changes"

	def __str__( self ):
		return "UserNameChange: {0} --> {1} on {2}".format( self.previous_username, self.new_username, self.change_date )

class ChatBan( models.Model ):
	chat_user = models.ForeignKey( User, related_name = "chat_ban_chat_user" )
	banned_user = models.ForeignKey( User )
	reason = models.CharField( max_length = 300, blank = True )
	#null expiry_date means permaban
	expiry_date = models.DateTimeField( blank = True, null = True, default = None )

	class Meta:
		db_table = "osp_chat_ban"
		verbose_name = "Chat Ban"
		verbose_name_plural = "Chat Bans"
		unique_together = ( "chat_user", "banned_user" )

	def __str__( self ):
		return "ChatBan: {0} <-- {1}".format( self.chat_user.username, self.banned_user.username )

class ChatBanIP( models.Model ):
	banned_ip = models.GenericIPAddressField( protocol = 'IPv4' )
	reason = models.CharField( max_length = 300, blank = True )
	issued_by = models.ForeignKey( User, null = True, related_name = "stream_chat_ban_ip_issued_by" )
	issue_date = models.DateTimeField( default = now )
	#null expiry_date means permaban
	expiry_date = models.DateTimeField( blank = True, null = True, default = None )
	lifted = models.BooleanField( default = False )

	class Meta:
		db_table = "osp_chat_ban_ip"
		verbose_name = 'Chat IP Ban'
		verbose_name_plural = 'Chat IP Bans'

	def __str__( self ):
		return self.banned_ip

class ChatBanUser( models.Model ):
	user = models.ForeignKey( User )
	reason = models.CharField( max_length = 300, blank = True )
	issued_by = models.ForeignKey( User, null = True, related_name = "stream_chat_ban_user_issued_by" )
	issue_date = models.DateTimeField( default = now )
	#null expiry_date means permaban
	expiry_date = models.DateTimeField( blank = True, null = True, default = None )
	lifted = models.BooleanField( default = False )

	class Meta:
		db_table = "osp_chat_ban_user"
		verbose_name = 'Chat User Ban'
		verbose_name_plural = 'Chat User Bans'

	def __str__( self ):
		return "ChatBanUser: {0}".format( self.user )

class ChatModerator( models.Model ):
	chat_user = models.ForeignKey( User, related_name = "chat_moderator_chat_user" )
	moderator_user = models.ForeignKey( User )

	class Meta:
		db_table = "osp_chat_moderator"
		verbose_name = "Chat Moderator"
		verbose_name_plural = "Chat Moderators"
		unique_together = ( "chat_user", "moderator_user" )

	def __str__( self ):
		return "ChatModerator: {0} <-- {1}".format( self.chat_user.username, self.moderator_user.username )

#sick import
from osp.api import drop_from_streaming
class StreamPublishBan( models.Model ):
	banned_ip = models.GenericIPAddressField( protocol = 'IPv4' )
	reason = models.CharField( max_length = 300, blank = True )
	issued_by = models.ForeignKey( User, null = True, related_name = "stream_publish_ban_issued_by" )
	issue_date = models.DateTimeField( default = now )
	#null expiry_date means permaban
	expiry_date = models.DateTimeField( blank = True, null = True, default = None )
	lifted = models.BooleanField( default = False )
	def save( self, *args, **kwargs ):
		super( StreamPublishBan, self ).save( *args, **kwargs )
		drop_from_streaming( ip = self.banned_ip )

	class Meta:
		db_table = "osp_stream_publish_ban"
		verbose_name = "Stream Publish IP Ban"
		verbose_name_plural = "Stream Publish IP Bans"

	def __str__( self ):
		return self.banned_ip

class StreamPublishUserBan( models.Model ):
	user = models.ForeignKey( User )
	reason = models.CharField( max_length = 300, blank = True )
	issued_by = models.ForeignKey( User, null = True, related_name = "stream_publish_user_ban_issued_by" )
	issue_date = models.DateTimeField( default = now )
	#null expiry_date means permaban
	expiry_date = models.DateTimeField( blank = True, null = True, default = None )
	lifted = models.BooleanField( default = False )
	def save( self, *args, **kwargs ):
		super( StreamPublishUserBan, self ).save( *args, **kwargs )
		drop_from_streaming( name = self.user.username )

	class Meta:
		db_table = "osp_stream_publish_user_ban"
		verbose_name = "Stream Publish User Ban"
		verbose_name_plural = "Stream Publish User Bans"

	def __str__( self ):
		return self.user.username

class StreamPlayBan( models.Model ):
	banned_ip = models.GenericIPAddressField( protocol = 'IPv4' )
	reason = models.CharField( max_length = 300, blank = True )
	issued_by = models.ForeignKey( User, null = True, related_name = "stream_play_ban_issued_by" )
	issue_date = models.DateTimeField( default = now )
	#null expiry_date means permaban
	expiry_date = models.DateTimeField( blank = True, null = True, default = None )
	lifted = models.BooleanField( default = False )

	class Meta:
		db_table = "osp_stream_play_ban"
		verbose_name = "Stream Play IP Ban"
		verbose_name_plural = "Stream Play IP Bans"

	def __str__( self ):
		return self.banned_ip
