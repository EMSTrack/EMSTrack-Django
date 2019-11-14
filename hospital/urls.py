from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'hospital'
urlpatterns = [

    url(r'^list/$',
        login_required(views.HospitalListView.as_view()),
        name="list"),

    url(r'^create/$',
        login_required(views.HospitalCreateView.as_view()),
        name="create"),
    
    url(r'^detail/(?P<pk>[0-9]+)$',
        login_required(views.HospitalDetailView.as_view()),
        name="detail"),

    url(r'^update/(?P<pk>[0-9]+)$',
        login_required(views.HospitalUpdateView.as_view()),
        name="update"),

    url(r'^export/$',
        staff_member_required(views.HospitalExportView.as_view()),
        name='export-hospital'),

    url(r'^import/$',
        staff_member_required(views.HospitalImportView.as_view()),
        name='import-hospital'),

    url(r'^process_import/$',
        staff_member_required(views.HospitalProcessImportView.as_view()),
        name='process-import-hospital'),

]
