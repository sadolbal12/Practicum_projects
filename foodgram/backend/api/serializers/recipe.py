from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.serializers.user import UserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag (только чтение)."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Cериализатор для модели Ingredient (только чтение)."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта (GET)."""

    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def get_author(self, obj):
        return UserSerializer(obj.author, context=self.context).data

    def get_ingredients(self, obj):
        return [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount,
            }
            for item in obj.ingredient_items.all()
        ]

    def get_image(self, obj):
        if not obj.image:
            return ''
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if not obj.image:
            return ''
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


def _parse_ingredient_id(raw_id):
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        raise serializers.ValidationError(
            'id ингредиента должен быть целым числом.',
        )


def _parse_ingredient_amount(raw_amount):
    try:
        return int(raw_amount)
    except (TypeError, ValueError):
        raise serializers.ValidationError(
            'amount ингредиента должен быть целым числом.',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор который принимает теги картинку и ингридиенты."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    ingredients = serializers.ListField(
        write_only=True, child=serializers.DictField(),
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'cooking_time', 'image', 'tags', 'ingredients',
        )

    def validate_ingredients(self, value):
        seen = set()
        normalized = []
        for item in value:
            if 'id' not in item or 'amount' not in item:
                raise serializers.ValidationError(
                    'Каждый ингредиент должен содержать "id" и "amount".',
                )
            ingredient_id = _parse_ingredient_id(item['id'])
            amount = _parse_ingredient_amount(item['amount'])
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                load_hint = 'Выполните load_ingredients_and_tags.'
                message = (
                    f'Ингредиент с id {ingredient_id} не найден. {load_hint}'
                )
                raise serializers.ValidationError(message)
            if amount <= 0:
                raise serializers.ValidationError(
                    'Количество должно быть положительным.',
                )
            if ingredient_id in seen:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.',
                )
            seen.add(ingredient_id)
            normalized.append({'id': ingredient_id, 'amount': amount})
        return normalized

    def validate(self, data):
        if not data.get('tags'):
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'},
            )
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'},
            )
        return data

    def _save_ingredients(self, recipe, ingredients_data):
        items = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(items)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.ingredient_items.all().delete()
            self._save_ingredients(instance, ingredients_data)
        return instance

    def validate_tags(self, value):
        ids = [tag.id for tag in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_image(self, value):
        if self.partial and not value:
            return value
        if not value:
            raise serializers.ValidationError('Поле image обязательно.')
        return value

    def to_representation(self, instance):
        from api.querysets import annotate_recipe_user_flags
        request = self.context.get('request')
        user = request.user if request else None
        queryset = annotate_recipe_user_flags(
            Recipe.objects.filter(pk=instance.pk), user,
        )
        annotated = queryset.first()
        return RecipeReadSerializer(annotated, context=self.context).data
