from django.contrib import admin
from .models import UserProfile, Artist, Event, Ticket

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_organizer']
    list_filter = ['is_organizer']
    search_fields = ['user__username', 'user__email']

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['name', 'genre']
    search_fields = ['name', 'genre']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'start_datetime', 'location_name', 'ticket_price', 'capacity', 'tickets_sold']
    list_filter = ['start_datetime']
    search_fields = ['title', 'location_name', 'host__username']
    filter_horizontal = ['artists']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'purchase_datetime']
    list_filter = ['purchase_datetime']
    search_fields = ['user__username', 'event__title']
