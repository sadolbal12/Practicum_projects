import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient, Tag

TAGS = (
    {'name': 'Завтрак', 'slug': 'breakfast'},
    {'name': 'Обед', 'slug': 'lunch'},
    {'name': 'Ужин', 'slug': 'dinner'},
)


class Command(BaseCommand):
    help = 'Загружает ингредиенты и теги.'

    def handle(self, *args, **kwargs):
        self.load_ingredients()
        self.load_tags()

    def load_ingredients(self):
        file_path = settings.BASE_DIR / 'data' / 'ingredients.json'
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        before_count = Ingredient.objects.count()
        ingredients = []
        for item in data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            if not name or not measurement_unit:
                raise CommandError(
                    'Каждый ингредиент должен содержать ключи '
                    '"name" и "measurement_unit".',
                )
            ingredients.append(
                Ingredient(name=name, measurement_unit=measurement_unit),
            )
        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
        added = Ingredient.objects.count() - before_count
        total_count = Ingredient.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Добавлено ингредиентов: {added}, всего в базе: {total_count}'
            )
        )

    def load_tags(self):
        created_count = 0
        for tag in TAGS:
            slug = tag.get('slug')
            name = tag.get('name')
            if not slug or not name:
                raise CommandError(
                    'Каждый тег должен содержать ключи "name" и "slug".',
                )
            _tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name},
            )
            if created:
                created_count += 1
        self.stdout.write(
            self.style.SUCCESS(f'Загружено {created_count} тегов')
        )
