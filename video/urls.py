from django.conf.urls import url

from login.decorator import login_required

from . import views

app_name = 'video'
urlpatterns = [

    url(r'^$',
        login_required(views.IndexView.as_view()),
        name="index"),

]
