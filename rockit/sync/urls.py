from django.conf.urls.defaults import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^upload$', views.upload, name='sync.upload'),
    url(r'^checkfiles$', views.checkfiles, name='sync.checkfiles'),
    url(r'^$', views.index, name='sync.index'),
)
