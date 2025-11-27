from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_organizer = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Artist(models.Model):
    # Keep your current fields
    name = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    # + add optional image_url so it also works with the other code
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    location_name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    artists = models.ManyToManyField(Artist, blank=True, related_name='events')
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField()
    tickets_sold = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def remaining_tickets(self):
        return self.capacity - self.tickets_sold


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    purchase_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


# === ADDED FROM THE OTHER FILE ===

class Stage(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class Performance(models.Model):
    """
    A specific artist on a specific stage at a specific time,
    as part of an EVENT.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="performances")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="performances")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="performances")

    title = models.CharField(max_length=200, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    description = models.TextField(blank=True)

    def __str__(self):
        label = self.title or self.artist.name
        # Your Event uses start_datetime instead of start_date
        date_str = self.event.start_datetime.date() if self.event.start_datetime else "?"
        return f"{label} - {self.stage} ({date_str} {self.start_time})"
