from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'report'
urlpatterns = [

    url(r'^list/$',
        login_required(views.ReportListView.as_view()),
        name="list"),

]
