# Festify Backend Setup

## Installation

```bash
pip install -r requirements.txt
```

## Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py create_default_admin
```

## Run Server

```bash
python manage.py runserver
```

## Default Admin Account

- Username: `festify@admin`
- Password: `123456`
- Admin URL: `http://localhost:8000/admin/`

## API Endpoints

### Authentication
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`

### Profile
- `GET /api/profile/`
- `GET /api/profile/tickets/`

### Events
- `GET /api/events/`
- `GET /api/events/<id>/`
- `POST /api/events/`
- `PUT /api/events/<id>/`
- `PATCH /api/events/<id>/`
- `DELETE /api/events/<id>/`
- `POST /api/events/<id>/buy/`

### Artists
- `GET /api/artists/`
- `GET /api/artists/<id>/`
- `POST /api/artists/`
- `PUT /api/artists/<id>/`
- `PATCH /api/artists/<id>/`
- `DELETE /api/artists/<id>/`

### Calendar
- `GET /api/calendar/?year=2025&month=7`
