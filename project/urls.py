from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from .views import TestingView

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'asd/asd/.*', TestingView.as_view()),
    url(r'^admin/', include(admin.site.urls)),
)
