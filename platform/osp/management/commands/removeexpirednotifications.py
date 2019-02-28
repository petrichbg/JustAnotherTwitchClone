from django.core.management.base import BaseCommand
from osp.models import UserNotification, UserFollowNotification
from datetime import datetime

class Command( BaseCommand ):
	def handle( self, *args, **options ):
		UserNotification.objects.filter( expiry_date__lt = datetime.now() ).delete()
		UserFollowNotification.objects.filter( expiry_date__lt = datetime.now() ).delete()