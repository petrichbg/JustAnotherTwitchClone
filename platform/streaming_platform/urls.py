from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from osp import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'streaming_platform.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

	url( r'^admin/', include( admin.site.urls ) ),
	url( r'^', include( 'osp.urls', namespace='osp' ), name='osp' ),
    
)  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
