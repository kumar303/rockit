from django.conf.urls.defaults import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^start$', views.start, name='sync.start'),
    url(r'^finish$', views.finish, name='sync.finish'),
    url(r'^upload$', views.upload, name='sync.upload'),
    url(r'^checkfiles$', views.checkfiles, name='sync.checkfiles'),
    url(r'^$', views.index, name='sync.index'),
)
