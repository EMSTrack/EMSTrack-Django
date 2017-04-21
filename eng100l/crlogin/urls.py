from django.conf.urls import url
from crlogin import views

urlpatterns = [
    #url(r'^login/', views.LoginPageView.as_view()),
    url(r'^about/', views.AboutPageView.as_view()),
    url(r'^login/', views.user_login, name='login_url'),
    url(r'^signup/', views.user_signup, name='signup_url'),
    url(r'^logout/', views.user_logout),
    url(r'^settings/', views.user_settings, name='settings_url'),
    
]
