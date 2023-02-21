# URL's

from django.urls import path

from . import views

app_name = 'pubbyauth'

urlpatterns = [
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('profile', views.profile, name='profile'),
    #path('register', views.register_view, name='register'),
]