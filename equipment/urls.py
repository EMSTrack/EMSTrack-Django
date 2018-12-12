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

    url(r'^update_items/(?P<pk>[0-9]+)$',
        login_required(views.EquipmentUpdateView.as_view()),
        name='update-items'),

]
