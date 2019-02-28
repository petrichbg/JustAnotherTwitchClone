from django.core.management.base import BaseCommand
from osp.models import ChatBanIP, ChatBanUser, StreamPublishBan, StreamPublishUserBan, StreamPlayBan
from osp.api import remove_expired_chat_bans
from datetime import datetime

class Command( BaseCommand ):
	def handle( self, *args, **options ):
		remove_expired_chat_bans()