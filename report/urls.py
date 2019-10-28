from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'report'
urlpatterns = [

    url(r'^$',
        login_required(views.ReportIndexView.as_view()),
        name="index"),

    url(r'^vehicle$',
        login_required(views.VehicleReportView.as_view()),
        name="vehicle"),

]
