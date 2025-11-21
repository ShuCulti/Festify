from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from festify.models import UserProfile

class Command(BaseCommand):
    help = 'Creates default admin user if it does not exist'

    def handle(self, *args, **options):
        username = 'festify@admin'
        email = 'festify@admin'
        password = '123456'

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            UserProfile.objects.get_or_create(user=user, defaults={'is_organizer': True})
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user {username} already exists'))
