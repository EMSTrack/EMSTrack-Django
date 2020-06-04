from django.conf.urls import url

from login.decorator import guest_login_required

from . import views

app_name = 'guest'
urlpatterns = [

    url(r'^video/(?P<sender_info>.+)$',
        views.VideoView.as_view(),
        name="video"
    ),

    url(r'^redirect$',
        views.RedirectView.as_view(),
        name="redirect"
    ),


    url(r'^$',
        guest_login_required(views.IndexView.as_view()),
        name="index"),

]
