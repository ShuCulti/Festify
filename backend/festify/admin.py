from django.contrib import admin
from .models import (
    UserProfile,
    Artist,
    Event,
    Ticket,
    Stage,
    Performance,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_organizer']
    list_filter = ['is_organizer']
    search_fields = ['user__username', 'user__email']


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['name', 'genre']
    search_fields = ['name', 'genre']


class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'host',
        'start_datetime',
        'location_name',
        'ticket_price',
        'capacity',
        'tickets_sold',
    ]
    list_filter = ['start_datetime']
    search_fields = ['title', 'location_name', 'host__username']
    filter_horizontal = ['artists']
    ordering = ('start_datetime',)
    inlines = [PerformanceInline]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'purchase_datetime']
    list_filter = ['purchase_datetime']
    search_fields = ['user__username', 'event__title']


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "order")
    ordering = ("order",)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("get_label", "artist", "stage", "event", "start_time", "end_time")
    list_filter = ("event", "stage", "artist")
    ordering = ("event__start_date", "start_time")

    def get_label(self, obj):
        return obj.title or obj.artist.name

    get_label.short_description = "Performance"
