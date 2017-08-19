from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^myposts$', views.BlogIndexPrivate.as_view(), name="myposts"),
    url(r'^post/(?P<slug>\S+)$', views.BlogDetail.as_view(), name="post"),
    url(r'^post_new/$', views.post_new, name='post_new'),
    url(r'^$', views.BlogIndex.as_view(), name='home'),
]
