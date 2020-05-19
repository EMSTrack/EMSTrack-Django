from django.conf.urls import url
#from django.contrib.auth.decorators import login_required
from login.decorator import guest_login_required

from . import views

app_name = 'guest'
urlpatterns = [

    url(r'^$',
        guest_login_required(views.IndexView.as_view()),
        name="index"),

]
