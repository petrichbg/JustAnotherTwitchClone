from django.utils import timezone
from osp.models import UserData
from osp.views import views_not_updating_last_user_activity

class UpdateLastActivityMiddleware(object):
	def process_view( self, request, view_func, view_args, view_kwargs ):
		if view_func in views_not_updating_last_user_activity:
			return

		if request.user.is_authenticated():
			UserData.objects.filter( user_id = request.user.id ).update( last_activity_date = timezone.now() )