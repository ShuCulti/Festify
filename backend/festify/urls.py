from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'artists', views.ArtistViewSet, basename='artist')

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/tickets/', views.user_tickets, name='user-tickets'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('', include(router.urls)),
]
