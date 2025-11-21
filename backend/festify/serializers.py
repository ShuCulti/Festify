from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Artist, Event, Ticket

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['is_organizer']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    is_organizer = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'is_organizer']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        is_organizer = validated_data.pop('is_organizer', False)
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user, is_organizer=is_organizer)
        return user

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['id', 'name', 'genre', 'description']

class EventListSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(many=True, read_only=True)
    remaining_tickets = serializers.ReadOnlyField()
    host_username = serializers.CharField(source='host.username', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_datetime', 'end_datetime',
            'location_name', 'address', 'latitude', 'longitude', 'image',
            'artists', 'ticket_price', 'capacity', 'tickets_sold',
            'remaining_tickets', 'host_username', 'created_at'
        ]

class EventDetailSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(many=True, read_only=True)
    remaining_tickets = serializers.ReadOnlyField()
    host = UserSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'host', 'title', 'description', 'start_datetime', 'end_datetime',
            'location_name', 'address', 'latitude', 'longitude', 'image',
            'artists', 'ticket_price', 'capacity', 'tickets_sold',
            'remaining_tickets', 'created_at', 'updated_at'
        ]

class EventCreateUpdateSerializer(serializers.ModelSerializer):
    artist_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_datetime', 'end_datetime',
            'location_name', 'address', 'latitude', 'longitude', 'image',
            'ticket_price', 'capacity', 'artist_ids'
        ]

    def create(self, validated_data):
        artist_ids = validated_data.pop('artist_ids', [])
        event = Event.objects.create(**validated_data)
        if artist_ids:
            artists = Artist.objects.filter(id__in=artist_ids)
            event.artists.set(artists)
        return event

    def update(self, instance, validated_data):
        artist_ids = validated_data.pop('artist_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if artist_ids is not None:
            artists = Artist.objects.filter(id__in=artist_ids)
            instance.artists.set(artists)
        return instance

class TicketSerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'user', 'event', 'purchase_datetime']

class ProfileSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    is_organizer = serializers.BooleanField()
    tickets = TicketSerializer(many=True)
    hosted_events = EventListSerializer(many=True)
