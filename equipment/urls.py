from django.conf.urls import url, include
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'equipment'
urlpatterns = [

    # Equipment, with staff permission

    url(r'^list$',
        staff_member_required(views.EquipmentAdminListView.as_view()),
        name='list'),

    url(r'^create$',
        staff_member_required(views.EquipmentAdminCreateView.as_view()),
        name='create'),

    url(r'^detail/(?P<pk>[0-9]+)$',
        staff_member_required(views.EquipmentAdminDetailView.as_view()),
        name='detail'),

    url(r'^update/(?P<pk>[0-9]+)$',
        staff_member_required(views.EquipmentAdminUpdateView.as_view()),
        name='update'),

    # Equipment sets

    url(r'^set/list$',
        staff_member_required(views.EquipmentSetAdminListView.as_view()),
        name='list-set'),

    url(r'^set/create$',
        staff_member_required(views.EquipmentSetAdminCreateView.as_view()),
        name='create-set'),

    url(r'^set/detail/(?P<pk>[0-9]+)$',
        staff_member_required(views.EquipmentSetAdminDetailView.as_view()),
        name='detail-set'),

    url(r'^set/update/(?P<pk>[0-9]+)$',
        staff_member_required(views.EquipmentSetAdminUpdateView.as_view()),
        name='update-set'),

    # Equipment holder

    url(r'^holder/update/(?P<pk>[0-9]+)$',
        login_required(views.EquipmentHolderUpdateView.as_view()),
        name='update-holder'),

]
