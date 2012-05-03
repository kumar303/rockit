from django.conf.urls.defaults import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^upload$', views.upload, name='sync.upload'),
    url(r'^songs$', views.songs, name='sync.songs'),
    url(r'^$', views.index, name='sync.index'),
)
