from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# This is the namespace used in templates: {% url 'events:home' %}
app_name = "events"

router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'artists', views.ArtistViewSet, basename='artist')

urlpatterns = [
    # HTML pages (Stage + Performance views)
    path("", views.home, name="home"),
    path("calendar/", views.month_calendar, name="calendar"),
    path("calendar/<int:year>/<int:month>/", views.month_calendar, name="calendar_month"),
    path("event/<int:pk>/", views.event_detail, name="event_detail"),

    # Auth API
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", views.logout, name="logout"),

    # Profile / tickets API
    path("profile/", views.profile, name="profile"),
    path("profile/tickets/", views.user_tickets, name="user-tickets"),

    # DRF API under /api/
    path("api/auth/register/", views.register, name="register-api"),
    path("api/auth/login/", views.login, name="login-api"),
    path("api/auth/logout/", views.logout, name="logout-api"),
    path("api/profile/", views.profile, name="profile-api"),
    path("api/profile/tickets/", views.user_tickets, name="user-tickets-api"),
    path("api/", include(router.urls)),

    # Static HTML pages for frontend
    path("register/", views.registration_page, name="registration-page"),
    path("login/", views.login_page, name="login-page"),
    path("logout/", views.logout_page, name="logout-page"),
    path("profile-page/", views.profile_page, name="profile-page"),
    path("tickets-page/", views.tickets_page, name="tickets-page"),
]
