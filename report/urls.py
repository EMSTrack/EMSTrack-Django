from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'report'
urlpatterns = [

    url(r'^$',
        login_required(views.ReportIndexView.as_view()),
        name="index"),

    url(r'^vehicle-mileage$',
        login_required(views.VehicleMileageReportView.as_view()),
        name="vehicle-mileage"),

    url(r'^vehicle-status$',
        login_required(views.VehicleStatusReportView.as_view()),
        name="vehicle-status"),

]
