import calendar
from datetime import datetime, date, timedelta
from calendar import monthrange

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    UserProfile,
    Artist,
    Event,
    Ticket,
    Performance,
    Stage
)

from .serializers import (
    RegisterSerializer, UserSerializer, ArtistSerializer,
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    TicketSerializer, ProfileSerializer
)

from .permissions import IsOrganizerAndOwner


# ============================================
# AUTH ENDPOINTS
# ============================================

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


# ============================================
# EVENT API (DRF)
# ============================================

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


# ============================================
# PROFILE / TICKETS
# ============================================

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


# ============================================
# JSON CALENDAR API
# ============================================

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

    days = [{
        'date': datetime(year, month, day).date().isoformat(),
        'events': days_dict.get(datetime(year, month, day).date().isoformat(), [])
    } for day in range(1, last_day + 1)]

    return Response({
        'year': year,
        'month': month,
        'days': days
    })


# ============================================
# ARTIST API
# ============================================

class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]


# ============================================
# HTML TEMPLATE PAGES
# ============================================

def registration_page(request):
    return render(request, 'registration.html')

def login_page(request):
    return render(request, 'login.html')

def logout_page(request):
    return render(request, 'logout.html')

def profile_page(request):
    # Provide server-side context so the template can render profile data
    if request.user.is_authenticated:
        user = request.user
        profile = getattr(user, 'profile', None)
        tickets = Ticket.objects.filter(user=user).select_related('event')
        hosted_events = Event.objects.filter(host=user) if (profile and profile.is_organizer) else []

        context = {
            'username': user.username,
            'email': user.email,
            'is_organizer': profile.is_organizer if profile else False,
            'tickets': tickets,
            'hosted_events': hosted_events,
        }
    else:
        context = {}

    return render(request, 'profile.html', context)

def tickets_page(request):
    return render(request, 'tickets.html')


def map_image(request):
    """Development helper: serve the bundled map image placed in
    `festify/templates/events/map.png`. This avoids needing to move the
    image into STATIC during quick local development.
    """
    import os
    from django.http import FileResponse, Http404

    base = os.path.dirname(__file__)
    path = os.path.join(base, 'templates', 'events', 'map.png')
    if not os.path.exists(path):
        raise Http404("Map image not found")

    return FileResponse(open(path, 'rb'), content_type='image/png')


def map_page(request):
    """Render a dedicated HTML page that displays the festival map.

    We also pass simple hotspot positions (percent-based) for each Stage
    so the template can render clickable elements that redirect to the
    stage detail pages.
    """
    # Get all stages and assign them positions from a small predefined list.
    stages = list(Stage.objects.order_by('order'))

    # Percent-based positions tuned to the current map image layout.
    default_positions = [
        {'left': '59%', 'top': '25%'},  # first stage
        {'left': '28%', 'top': '39%'},  # second stage
        {'left': '50%', 'top': '61%'},  # third stage
    ]

    stage_positions = []
    for i, stage in enumerate(stages):
        pos = default_positions[i] if i < len(default_positions) else {'left': '50%', 'top': '50%'}
        stage_positions.append({
            'id': stage.id,
            'name': stage.name,
            'left': pos['left'],
            'top': pos['top'],
        })

    return render(request, 'events/map_page.html', {
        'stage_positions': stage_positions,
    })


def stage_detail(request, pk):
    stage = get_object_or_404(Stage, pk=pk)
    # Show upcoming performances for this stage across events
    performances = (
        Performance.objects
        .filter(stage=stage)
        .select_related('artist', 'event')
        .order_by('event__start_datetime', 'start_time')
    )

    return render(request, 'events/stage_detail.html', {
        'stage': stage,
        'performances': performances,
    })


# ============================================
# FESTIVAL HTML VIEWS (Stage + Performance)
# ============================================

def home(request):
    """Show the earliest performance TODAY for each stage."""
    today = date.today()

    events_today = Event.objects.filter(
        start_datetime__date__lte=today
    ).filter(
        Q(end_datetime__date__gte=today) | Q(end_datetime__isnull=True)
    )

    performances_today = (
        Performance.objects
        .filter(event__in=events_today)
        .select_related("artist", "stage", "event")
        .order_by("start_time")
    )

    earliest_by_stage = {}
    for perf in performances_today:
        stage = perf.stage
        current = earliest_by_stage.get(stage)
        if current is None or perf.start_time < current.start_time:
            earliest_by_stage[stage] = perf

    stages = Stage.objects.order_by("order")
    stage_cards = [{
        "stage": stage,
        "performance": earliest_by_stage.get(stage),
    } for stage in stages]

    return render(request, "events/home.html", {
        "today": today,
        "stage_cards": stage_cards,
    })


def month_calendar(request, year=None, month=None):
    today = date.today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    _, num_days = calendar.monthrange(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, num_days)

    events = Event.objects.filter(
        start_datetime__date__lte=last_day
    ).filter(
        Q(end_datetime__date__gte=first_day) | Q(end_datetime__isnull=True)
    )

    event_by_day = {}
    for evt in events:
        evt_start = evt.start_datetime.date()
        evt_end = evt.end_datetime.date() if evt.end_datetime else evt_start

        current = max(evt_start, first_day)
        final = min(evt_end, last_day)

        while current <= final:
            event_by_day.setdefault(current, []).append(evt)
            current += timedelta(days=1)

    cal = calendar.Calendar(firstweekday=0)
    raw_weeks = cal.monthdatescalendar(year, month)

    weeks = []
    for week in raw_weeks:
        rows = []
        for d in week:
            rows.append({
                "date": d,
                "in_month": d.month == month,
                "events": event_by_day.get(d, []),
            })
        weeks.append(rows)

    return render(request, "events/calendar.html", {
        "year": year,
        "month": month,
        "weeks": weeks,
        "prev_year": year if month > 1 else year - 1,
        "prev_month": month - 1 if month > 1 else 12,
        "next_year": year if month < 12 else year + 1,
        "next_month": month + 1 if month < 12 else 1,
        "month_name": calendar.month_name[month],
    })


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    performances = (
        event.performances
        .select_related("artist", "stage")
        .order_by("start_time", "stage__order")
    )

    return render(request, "events/event_detail.html", {
        "event": event,
        "performances": performances,
    })
