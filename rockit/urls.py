from django.conf import settings
from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from django.contrib.admin import site as admin_site
# from funfactory.admin import site as admin_site

import rockit.music.urls
import rockit.sync.urls


admin.autodiscover()


urlpatterns = patterns('',
    (r'music/', include(rockit.music.urls)),
    (r'sync/', include(rockit.sync.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin_site.urls)),
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
