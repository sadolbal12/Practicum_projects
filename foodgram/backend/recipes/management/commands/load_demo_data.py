from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

DEMO_USERS = (
    {
        'username': 'admin',
        'email': 'admin@example.ru',
        'password': '12345',
        'first_name': 'Admin',
        'last_name': 'Foodgram',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'username': 'demo_chef',
        'email': 'chef@example.ru',
        'password': 'foodgram123',
        'first_name': 'Демо',
        'last_name': 'Повар',
    },
    {
        'username': 'demo_user',
        'email': 'user@example.ru',
        'password': 'foodgram123',
        'first_name': 'Демо',
        'last_name': 'Пользователь',
    },
)


class Command(BaseCommand):
    help = (
        'Создаёт или обновляет тестовых пользователей и суперпользователя '
        'для ревью (пароли перезаписываются при каждом запуске).'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for data in DEMO_USERS:
            password = data['password']
            user, created = User.objects.update_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_staff': data.get('is_staff', False),
                    'is_superuser': data.get('is_superuser', False),
                },
            )
            user.set_password(password)
            user.save()

            status_text = 'Создан' if created else 'Обновлён'
            role = ' (суперпользователь)' if user.is_superuser else ''
            email = user.email
            self.stdout.write(
                self.style.SUCCESS(
                    f'{status_text}: {email}{role}, пароль установлен'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Готово. Вход на сайте — по email и паролю из README.'
            )
        )
