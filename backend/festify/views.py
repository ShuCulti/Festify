from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from datetime import datetime, timedelta
from calendar import monthrange
from .models import UserProfile, Artist, Event, Ticket
from .serializers import (
    RegisterSerializer, UserSerializer, ArtistSerializer,
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    TicketSerializer, ProfileSerializer
)
from .permissions import IsOrganizerAndOwner

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username_or_email = request.data.get('username')
    password = request.data.get('password')

    if not username_or_email or not password:
        return Response(
            {'error': 'Username/email and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = None
    if '@' in username_or_email:
        try:
            user_obj = User.objects.get(email=username_or_email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
    else:
        user = authenticate(username=username_or_email, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(
        {'error': 'Invalid credentials'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventCreateUpdateSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizerAndOwner()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = Event.objects.all().order_by('start_datetime')

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location_name__icontains=search)
            )

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_datetime__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_datetime__lte=end_date)

        upcoming = self.request.query_params.get('upcoming')
        if upcoming:
            queryset = queryset.filter(start_datetime__gte=datetime.now())

        return queryset

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def buy(self, request, pk=None):
        event = self.get_object()
        user = request.user

        if Ticket.objects.filter(user=user, event=event).exists():
            return Response(
                {'error': 'You already have a ticket for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if event.tickets_sold >= event.capacity:
            return Response(
                {'error': 'Event is sold out'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket = Ticket.objects.create(user=user, event=event)
        event.tickets_sold += 1
        event.save()

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    profile = user.profile

    tickets = Ticket.objects.filter(user=user).select_related('event')
    hosted_events = Event.objects.filter(host=user) if profile.is_organizer else []

    data = {
        'username': user.username,
        'email': user.email,
        'is_organizer': profile.is_organizer,
        'tickets': TicketSerializer(tickets, many=True).data,
        'hosted_events': EventListSerializer(hosted_events, many=True).data if hosted_events else []
    }

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tickets(request):
    tickets = Ticket.objects.filter(user=request.user).select_related('event')
    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def calendar_view(request):
    year = int(request.query_params.get('year', datetime.now().year))
    month = int(request.query_params.get('month', datetime.now().month))

    start_date = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    events = Event.objects.filter(
        start_datetime__gte=start_date,
        start_datetime__lte=end_date
    ).order_by('start_datetime')

    days_dict = {}
    for event in events:
        date_key = event.start_datetime.date().isoformat()
        if date_key not in days_dict:
            days_dict[date_key] = []
        days_dict[date_key].append(EventListSerializer(event).data)

    days = []
    for day in range(1, last_day + 1):
        date_key = datetime(year, month, day).date().isoformat()
        days.append({
            'date': date_key,
            'events': days_dict.get(date_key, [])
        })

    return Response({
        'year': year,
        'month': month,
        'days': days
    })

class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

def registration_page(request):
    return render(request, 'registration.html')

def login_page(request):
    return render(request, 'login.html')

def logout_page(request):
    return render(request, 'logout.html')

def profile_page(request):
    return render(request, 'profile.html')

def tickets_page(request):
    return render(request, 'tickets.html')
