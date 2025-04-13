
from django.contrib import admin
from django.urls import path,include
from rest_framework import urls
from rest_framework.authtoken import views
from .views import Homeroute
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',Homeroute,name="HomePage"),
    path('login', views.ObtainAuthToken.as_view(), name='obtain_auth_token'),
    path('api/', include('event.urls')),
   

]
