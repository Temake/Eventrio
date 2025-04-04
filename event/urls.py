from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'events', views.EventViewSet, basename='event')


urlpatterns = [
    path('', include(router.urls)),
    path('logout/', views.logout, name='user-logout'),
    path('register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('public-events/', views.PublicEventListView.as_view(), name='public-events'),
    path('api/events/<int:id>/attendees/', views.AttendeeView.as_view(), name='attendee-list'),
    path('register-event/<str:registration_link>/', views.EventRegistrationView.as_view(), name='event-registration'),
]