from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^myposts$', views.BlogIndexPrivate.as_view(), name="myposts"),
    url(r'^post/(?P<slug>\S+)/edit$', views.post_edit, name='post_edit'),
    url(r'^post/(?P<slug>\S+)/delete$', views.post_delete, name='post_delete'),
    url(r'^post/(?P<slug>\S+)/changepostfb$', views.change_post_to_fb, name='change_post_to_fb'),
    url(r'^post/(?P<slug>\S+)$', views.BlogDetail.as_view(), name="post"),
    url(r'^post_new/$', views.post_new, name='post_new'),
    url(r'^$', views.BlogIndex.as_view(), name='home'),
]
