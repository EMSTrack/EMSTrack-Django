from django.conf.urls import url

from login.decorator import login_required

from . import views

app_name = 'dashboard'
urlpatterns = [
    url(r'^$',
        login_required(views.DashboardView.as_view()),
        name="index"),
]
