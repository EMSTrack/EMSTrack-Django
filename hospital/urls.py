from django.conf.urls import url, include
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

    # Admin

    url(r'^equipment/list$',
        staff_member_required(views.HospitalEquipmentAdminListView.as_view()),
        name='equipment_list'),

    url(r'^equipment/create$',
        staff_member_required(views.HospitalEquipmentAdminCreateView.as_view()),
        name='equipment_create'),

    url(r'^equipment/detail/(?P<pk>[0-9]+)$',
        staff_member_required(views.HospitalEquipmentAdminDetailView.as_view()),
        name='equipment_detail'),

    url(r'^equipment/update/(?P<pk>[0-9]+)$',
        staff_member_required(views.HospitalEquipmentAdminUpdateView.as_view()),
        name='equipment_update'),

]
