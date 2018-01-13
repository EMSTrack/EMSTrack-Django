from django.conf.urls import url, include

from django.contrib.auth.decorators import login_required, permission_required

from . import views

urlpatterns = [

    url(r'list/',
        login_required(views.HospitalListView.as_view()),
        name="hospital_list"),

    url(r'create/',
        login_required(views.HospitalCreateView.as_view()),
        name="hospital_create"),
    
    url(r'detail/<int:pk>/',
        login_required(views.HospitalDetailView.as_view()),
        name="hospital_detail"),

    url(r'update/<int:pk>/',
        login_required(views.HospitalUpdateView.as_view()),
        name="hospital_update"),
    
]
